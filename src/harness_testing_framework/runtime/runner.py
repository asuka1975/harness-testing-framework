"""参照ランタイムの実行。遷移規則は契約 第3節、実行記録の並びは契約 3.4.1。"""

import hashlib
import json
import shutil
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from harness_testing_framework.contract import (
    Abort,
    AwaitingAnswer,
    AwaitingDecision,
    Classifier,
    ContinueAsGoal,
    Decision,
    Edge,
    Escalation,
    JSONValue,
    LLMClient,
    MetricRegistry,
    Operator,
    Question,
    Rerun,
    RollbackTo,
    StageBody,
    UserIO,
)
from harness_testing_framework.runtime.checkpoint import (
    Annotation,
    BlobStore,
    Snapshot,
    SnapshotReader,
    capture,
    initial_snapshot,
    materialize,
    restore_overlay,
)
from harness_testing_framework.runtime.model import Rollback, Stage, Workflow
from harness_testing_framework.runtime.oracle import (
    GOAL,
    UNKNOWN,
    MetricResult,
    classify,
    measure,
    options,
    state_document,
)
from harness_testing_framework.runtime.recorder import Passthrough, Recorder, ReplayOnly

type Event = dict[str, JSONValue]


class StageFailure(Exception):
    """本体の例外か契約違反。評価をせずに escalate する（契約 2.1）。"""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


class ContractViolation(Exception):
    """本体が契約に反する操作をした（契約 第8節）。"""


class OperatorDecisionInvalid(ValueError):
    """運用者の選択が契約 3.4 の条件を満たさない。"""


@dataclass
class RunState:
    """保存して別のプロセスで再開できる、実行の状態。

    current は最後のスナップショットの id。status が suspended なら pending は
    {"kind": "user", "question": {"text": 質問の文, "choices": [選択肢, ...]}}、awaiting_operator なら
    {"kind": "operator", "escalation": escalate の状況}。ほかの属性はランタイムの内部の状態で、読み書きしない。
    """

    seed: int
    status: str = "running"
    stage: str = ""
    visit: int = 0
    visits: dict[str, int] = field(default_factory=dict)
    starts: dict[str, str] = field(default_factory=dict)
    current: str = ""
    counts: dict[str, int] = field(default_factory=dict)
    answers: list[str] = field(default_factory=list)
    responses: list[JSONValue] = field(default_factory=list)
    pending: dict[str, Any] | None = None
    escalations: int = 0
    seq: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @staticmethod
    def from_json(text: str) -> "RunState":
        return RunState(**json.loads(text))


@dataclass(frozen=True)
class RunResult:
    """start か resume の一区切りの結果。events と snapshots はその区切りの分。"""

    status: str
    state: RunState
    events: list[Event]
    snapshots: list[str]


def derive_seed(seed: int, stage_id: str, visit: int) -> int:
    digest = hashlib.sha256(f"{seed}:{stage_id}:{visit}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def decision_to_json(decision: Decision) -> dict[str, JSONValue]:
    match decision:
        case Rerun():
            return {"kind": "rerun"}
        case RollbackTo(stage=stage, carry=carry):
            return {"kind": "rollback", "stage": stage, "carry": list(carry)}
        case ContinueAsGoal(note=note):
            return {"kind": "continue_as_goal", "note": note}
        case Abort():
            return {"kind": "abort"}
    raise TypeError(decision)


def decision_from_json(doc: Mapping[str, Any]) -> Decision:
    kind = doc["kind"]
    if kind == "rerun":
        return Rerun()
    if kind == "rollback":
        return RollbackTo(doc["stage"], tuple(doc.get("carry", [])))
    if kind == "continue_as_goal":
        return ContinueAsGoal(doc["note"], doc.get("by", ""))
    if kind == "abort":
        return Abort()
    raise ValueError(kind)


class _Context:
    """ステージ本体に渡す一回の実行の文脈（契約 7.1）。"""

    def __init__(self, runtime: "Runtime", state: RunState, stage: Stage, workspace: Path) -> None:
        self._runtime = runtime
        self._state = state
        self._stage = stage
        self._workspace = workspace
        self._memory = dict(runtime.store.get_snapshot(state.starts[stage.id]).memory)
        self.written: dict[str, JSONValue] = {}
        self.violations: list[str] = []
        # 本体が握りつぶしても、ランタイムが中断と再生の失敗を見落とさないように覚えておく
        self.awaiting: Question | None = None
        self.missing: ReplayOnly.Missing | None = None
        self._questions = 0
        self._llm_calls = 0

    @property
    def stage_id(self) -> str:
        return self._stage.id

    @property
    def visit(self) -> int:
        return self._state.visit

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def seed(self) -> int:
        return derive_seed(self._state.seed, self._stage.id, self._state.visit)

    def _violate(self, message: str) -> ContractViolation:
        self.violations.append(message)
        return ContractViolation(message)

    def read_memory(self, name: str) -> JSONValue:
        if name not in self._stage.memory_in:
            raise self._violate(f"{self._stage.id} が memory_in に無い {name} を読んだ")
        return self._memory.get(name)

    def write_memory(self, name: str, value: JSONValue) -> None:
        if name not in self._stage.memory_out:
            raise self._violate(f"{self._stage.id} が memory_out に無い {name} を書いた")
        json.dumps(value)
        self.written[name] = value

    @property
    def user_io(self) -> UserIO:
        if not self._stage.awaits_user:
            raise self._violate(f"{self._stage.id} は awaits_user を宣言していない")
        return _RecordedUserIO(self)

    @property
    def llm(self) -> LLMClient:
        return _RecordedLLM(self)

    def _call(self, kind: str, key: list[str | int], request: JSONValue, live: Any) -> JSONValue:
        try:
            return self._runtime.recorder.call(kind, key, request, live)
        except ReplayOnly.Missing as missing:
            self.missing = missing
            raise

    def _ask(self, question: Question) -> str:
        state, runtime = self._state, self._runtime
        index = self._questions
        self._questions += 1
        if index < len(state.answers):
            return state.answers[index]
        if state.pending and "answer" in state.pending:
            answer = str(state.pending["answer"])
            state.pending = None
            state.answers.append(answer)
            return answer

        def live() -> JSONValue:
            if runtime.user_io is None:
                raise RuntimeError("ユーザー入出力が束縛されていない")
            try:
                return {"answer": runtime.user_io.ask(question)}
            except AwaitingAnswer:
                return {"defer": True}

        request: JSONValue = {"text": question.text, "choices": list(question.choices)}
        key = _key(state.seed, self._stage.id, state.visit, index)
        response = self._call("user", key, request, live)
        assert isinstance(response, dict)
        if response.get("defer"):
            self.awaiting = question
            raise AwaitingAnswer(question)
        answer = str(response["answer"])
        state.answers.append(answer)
        return answer

    def _complete(self, request: JSONValue) -> JSONValue:
        runtime, state = self._runtime, self._state
        index = self._llm_calls
        self._llm_calls += 1
        # 中断から再開した訪問では、それまでの応答を再生する（外へ二度出さない）
        if index < len(state.responses):
            return state.responses[index]

        def live() -> JSONValue:
            if runtime.llm is None:
                raise RuntimeError("LLM クライアントが束縛されていない")
            return runtime.llm.complete(request)

        key = _key(state.seed, self._stage.id, state.visit, index)
        response = self._call("llm", key, request, live)
        state.responses.append(response)
        return response


class _RecordedUserIO:
    def __init__(self, context: _Context) -> None:
        self._context = context

    def ask(self, question: Question) -> str:
        return self._context._ask(question)


class _RecordedLLM:
    def __init__(self, context: _Context) -> None:
        self._context = context

    def complete(self, request: JSONValue) -> JSONValue:
        return self._context._complete(request)


class Runtime:
    """参照ランタイム。ワークフロー定義から遷移とゲートを駆動する。"""

    def __init__(
        self,
        workflow: Workflow,
        bodies: Mapping[str, StageBody],
        *,
        registry: MetricRegistry,
        classifier: Classifier,
        operator: Operator,
        store: BlobStore,
        workdir: Path,
        user_io: UserIO | None = None,
        llm: LLMClient | None = None,
        threshold: float = 0.5,
        recorder: Recorder | None = None,
        state_limit: int = 20000,
    ) -> None:
        self.workflow = workflow
        self.bodies = dict(bodies)
        self.registry = registry
        self.classifier = classifier
        self.operator = operator
        self.store = store
        self.workdir = workdir
        self.user_io = user_io
        self.llm = llm
        self.threshold = threshold
        self.recorder: Recorder = recorder or Passthrough()
        self.state_limit = state_limit
        self._events: list[Event] = []
        self._snapshots: list[str] = []

    # --- 入口 ---

    def start(self, seed: int, inputs: Mapping[str, bytes]) -> RunResult:
        """種 seed と、ワークフローの inputs のファイル（パスから内容）で実行を始める。"""
        self._events, self._snapshots = [], []
        state = RunState(seed=seed)
        self._emit(state, {"event": "run_start", "workflow": self.workflow.name, "seed": seed})
        self._enter(state, self.workflow.stages[0], initial_snapshot(self.store, inputs))
        self._loop(state)
        return self._result(state)

    def resume(
        self, state: RunState, *, answer: str | None = None, decision: Decision | None = None
    ) -> RunResult:
        """中断（suspended）した実行を answer で、escalate 待ち（awaiting_operator）の実行を decision で
        再開する。state は同じ置き場を使うランタイムで保存したもの。"""
        self._events, self._snapshots = [], []
        # 再開で受け取る回答と選択も外からの値なので、記録再生を通す
        if state.status == "suspended":
            if answer is None:
                raise ValueError("中断からの再開には回答が要る")
            given = answer
            response = self.recorder.call(
                "resume_answer",
                _key(state.seed, state.stage, state.visit, len(state.answers)),
                {},
                lambda: {"answer": given},
            )
            assert isinstance(response, dict)
            state.pending = {"kind": "user", "answer": str(response["answer"])}
            state.status = "running"
            self._transition(state, "resume", state.stage, state.stage)
        elif state.status == "awaiting_operator":
            if decision is None or state.pending is None:
                raise ValueError("escalate 待ちからの再開には選択が要る")
            escalation = state.pending["escalation"]
            chosen = decision
            response = self.recorder.call(
                "resume_decision",
                _key(state.seed, str(escalation["stage"]), state.escalations),
                escalation,
                lambda: decision_to_json(chosen),
            )
            assert isinstance(response, dict)
            state.pending = None
            state.status = "running"
            self._apply(state, escalation, decision_from_json(response))
        else:
            raise ValueError(f"状態 {state.status} の実行は再開できない")
        self._loop(state)
        return self._result(state)

    def snapshot(self, snapshot_id: str) -> Snapshot:
        """スナップショットを id で読む。最後のものの id は result.state.current。"""
        return self.store.get_snapshot(snapshot_id)

    # --- 実行記録 ---

    def _emit(self, state: RunState, event: Event) -> None:
        self._events.append({"seq": state.seq, **event})
        state.seq += 1

    def _transition(
        self,
        state: RunState,
        kind: str,
        source: str,
        target: str | None,
        edge: Event | None = None,
        count: int | None = None,
        crosses_phase: bool = False,
    ) -> None:
        self._emit(
            state,
            {
                "event": "transition",
                "kind": kind,
                "from": source,
                "to": target,
                "edge": edge,
                "count": count,
                "crosses_phase": crosses_phase,
            },
        )

    def _end(self, state: RunState, status: str) -> None:
        state.status = status
        self._emit(state, {"event": "run_end", "status": status})

    def _result(self, state: RunState) -> RunResult:
        return RunResult(state.status, state, self._events, self._snapshots)

    # --- 遷移 ---

    def _loop(self, state: RunState) -> None:
        while state.status == "running":
            self._step(state)

    def _enter(self, state: RunState, stage: Stage, start: Snapshot) -> None:
        self.store.put_snapshot(start)
        state.visits[stage.id] = state.visits.get(stage.id, 0) + 1
        state.stage, state.visit = stage.id, state.visits[stage.id]
        state.starts[stage.id] = start.id
        state.current = start.id
        state.answers, state.responses = [], []

    def _step(self, state: RunState) -> None:
        stage = self.workflow.stage(state.stage)
        start = self.store.get_snapshot(state.starts[stage.id])
        base: Event = {"stage": stage.id, "visit": state.visit}
        self._emit(state, {"event": "stage_start", **base, "snapshot": start.id})
        self._snapshots.append(start.id)
        try:
            end, discarded = self._run_body(state, stage, start)
        except AwaitingAnswer as waiting:
            question = {"text": waiting.question.text, "choices": list(waiting.question.choices)}
            state.pending = {"kind": "user", "question": question}
            self._transition(state, "suspend", stage.id, None)
            self._end(state, "suspended")
            return
        except StageFailure as failure:
            error: Event = {"kind": failure.kind, "message": failure.message}
            self._emit(state, {"event": "stage_end", **base, "snapshot": start.id, "error": error})
            self._snapshots.append(start.id)
            state.current = start.id
            self._escalate(state, stage, failure.kind, None, None, "stage", failure.message)
            return
        self.store.put_snapshot(end)
        state.current, state.answers, state.responses = end.id, [], []
        self._emit(state, {"event": "stage_end", **base, "snapshot": end.id, "error": None})
        self._snapshots.append(end.id)
        for path in discarded:
            self._emit(state, {"event": "warning", "message": f"範囲外のファイル {path} を捨てた"})
        self._after(state, stage, self._evaluate(state, stage, end, gate=False), "stage")

    def _after(self, state: RunState, stage: Stage, outcome: str, origin: str) -> None:
        if outcome == GOAL:
            if origin == "gate":
                self._pass_gate(state, stage)
            elif self.workflow.is_last_in_phase(stage.id):
                current = self.store.get_snapshot(state.current)
                self._after(state, stage, self._evaluate(state, stage, current, gate=True), "gate")
            else:
                self._next(state, stage)
        elif outcome == UNKNOWN:
            self._escalate(state, stage, "unknown", None, None, origin)
        else:
            self._take_edge(state, stage, stage.rollbacks[outcome], origin)

    def _pass_gate(self, state: RunState, stage: Stage) -> None:
        current = self.store.get_snapshot(state.current)
        passed = current.with_gate(stage.phase, self.workflow.phase_order)
        state.current = self.store.put_snapshot(passed)
        self._transition(state, "gate_pass", stage.id, None)
        self._next(state, stage)

    def _next(self, state: RunState, stage: Stage) -> None:
        following = self.workflow.next_stage(stage.id)
        if following is None:
            self._transition(state, "complete", stage.id, None)
            self._end(state, "completed")
            return
        crosses = following.phase != stage.phase
        self._transition(state, "next", stage.id, following.id, crosses_phase=crosses)
        self._enter(state, following, self.store.get_snapshot(state.current))

    @staticmethod
    def _edge(rollback: Rollback) -> Event:
        return {"stage": rollback.stage, "state": rollback.state, "target": rollback.target}

    def _take_edge(self, state: RunState, stage: Stage, rollback: Rollback, origin: str) -> None:
        key = f"{rollback.stage}/{rollback.state}"
        count = state.counts.get(key, 0)
        edge = self._edge(rollback)
        if count >= rollback.max:
            self._escalate(state, stage, "max_exceeded", edge, count, origin)
            return
        state.counts[key] = count + 1
        target = self.workflow.stage(rollback.target)
        self._rollback(state, stage, target, rollback.carry, edge, count + 1)

    def _rollback(
        self,
        state: RunState,
        stage: Stage,
        target: Stage,
        carry: tuple[str, ...],
        edge: Event | None,
        count: int | None,
    ) -> None:
        start = self.store.get_snapshot(state.starts[target.id])
        restored, missing = restore_overlay(start, self.store.get_snapshot(state.current), carry)
        crosses = target.phase != stage.phase
        self._transition(state, "rollback", stage.id, target.id, edge, count, crosses)
        for name in missing:
            message = f"carry の {name} が現在の記憶に無いので重ねなかった"
            self._emit(state, {"event": "warning", "message": message})
        self._enter(state, target, restored)

    # --- 評価 ---

    def _evaluate(self, state: RunState, stage: Stage, snapshot: Snapshot, gate: bool) -> str:
        if gate:
            phase = self.workflow.phase(stage.phase)
            goal, scope, target = phase.goal, "phase", phase.id
            paths: list[str] = []
            for sid in phase.stages:
                s = self.workflow.stage(sid)
                paths += [p for p in (*s.reads, *s.writes) if p not in paths]
        else:
            goal, scope, target = stage.goal, "stage", stage.id
            paths = list(dict.fromkeys((*stage.reads, *stage.writes)))
        key = _key(state.seed, scope, target, state.visit)
        first = self.workflow.phase(stage.phase).stages[0] if gate else stage.id
        baseline = self.store.get_snapshot(state.starts[first])
        view = SnapshotReader(snapshot, self.store, baseline)
        metrics = measure(goal, self.registry, view, self.recorder, key)
        include_goal = all(m.passed for m in metrics.values())
        choices = options(goal, stage.end_states, include_goal)
        header = f"# 評価: {scope} {target} visit {state.visit}"
        document = state_document(
            header, paths, stage.memory_out, snapshot, self.store, self.state_limit
        )
        outcome, result = classify(
            self.classifier, document, choices, self.threshold, self.recorder, key
        )
        # 分類器が見た状態文書を残す（オラクルのコーパスとトリアージが読む。契約 2.4・第6節）
        state_id = self.store.put(document.encode("utf-8"))
        self._emit(
            state,
            {
                "event": "evaluation",
                "scope": scope,
                "stage": stage.id,
                "phase": stage.phase,
                "visit": state.visit,
                "metrics": {name: _metric_json(m) for name, m in metrics.items()},
                "classification": {
                    "options": [o.id for o in choices],
                    "choice": result.choice,
                    "confidence": result.confidence,
                    "state": state_id,
                },
                "outcome": outcome,
            },
        )
        return outcome

    # --- escalate ---

    def _escalate(
        self,
        state: RunState,
        stage: Stage,
        reason: str,
        edge: Event | None,
        count: int | None,
        origin: str,
        message: str = "",
    ) -> None:
        self._transition(state, "escalate", stage.id, None, edge, count)
        escalation: dict[str, JSONValue] = {
            "stage": stage.id,
            "reason": reason,
            "edge": edge,
            "count": count,
            "origin": origin,
            "message": message,
        }
        state.escalations += 1
        response = self.recorder.call(
            "operator",
            _key(state.seed, stage.id, state.escalations),
            escalation,
            lambda: self._live_decision(escalation),
        )
        assert isinstance(response, dict)
        if response.get("defer"):
            event: Event = {
                "event": "escalation",
                "stage": stage.id,
                "reason": reason,
                "edge": edge,
                "decision": None,
            }
            self._emit(state, event)
            state.pending = {"kind": "operator", "escalation": escalation}
            self._end(state, "awaiting_operator")
            return
        self._apply(state, escalation, decision_from_json(response))

    def _live_decision(self, escalation: Mapping[str, Any]) -> JSONValue:
        edge = escalation["edge"]
        request = Escalation(
            reason=escalation["reason"],
            stage=escalation["stage"],
            outcome=None,
            edge=Edge(**edge) if edge else None,
            count=escalation["count"],
            message=escalation["message"],
        )
        try:
            decision = self.operator.decide(request)
        except AwaitingDecision:
            return {"defer": True}
        out = decision_to_json(decision)
        if isinstance(decision, ContinueAsGoal) and decision.by:
            out["by"] = decision.by
        return out

    def _invalid(self, stage: Stage, decision: Decision) -> str | None:
        if isinstance(decision, RollbackTo):
            if decision.stage not in {s.id for s in self.workflow.stages}:
                return f"ステージ {decision.stage} が無い"
            target = self.workflow.stage(decision.stage)
            if target.position > stage.position:
                return f"{decision.stage} は {stage.id} より後ろ"
            if not set(decision.carry) <= set(target.memory_in):
                return f"carry {list(decision.carry)} が {decision.stage} の memory_in に無い"
        return None

    def _apply(self, state: RunState, escalation: Mapping[str, Any], decision: Decision) -> None:
        stage = self.workflow.stage(escalation["stage"])
        problem = self._invalid(stage, decision)
        if problem is not None:
            # 契約 3.4: 条件を満たさない選択は拒み、escalate 待ちに戻す
            message = f"{OperatorDecisionInvalid.__name__}: {problem}"
            self._emit(state, {"event": "warning", "message": message})
            event: Event = {
                "event": "escalation",
                "stage": stage.id,
                "reason": escalation["reason"],
                "edge": escalation["edge"],
                "decision": None,
            }
            self._emit(state, event)
            state.pending = {"kind": "operator", "escalation": dict(escalation)}
            self._end(state, "awaiting_operator")
            return
        self._emit(
            state,
            {
                "event": "escalation",
                "stage": stage.id,
                "reason": escalation["reason"],
                "edge": escalation["edge"],
                "decision": decision_to_json(decision),
            },
        )
        match decision:
            case Rerun():
                self._enter(state, stage, self.store.get_snapshot(state.starts[stage.id]))
            case RollbackTo(stage=target_id, carry=carry):
                self._rollback(state, stage, self.workflow.stage(target_id), carry, None, None)
            case ContinueAsGoal(note=note, by=by):
                current = self.store.get_snapshot(state.current)
                annotation = Annotation("forced_goal", stage.id, note, by or "operator")
                annotated = current.with_annotation(annotation)
                state.current = self.store.put_snapshot(annotated)
                self._after(state, stage, GOAL, escalation["origin"])
            case Abort():
                self._transition(state, "abort", stage.id, None)
                self._end(state, "aborted")

    # --- 本体 ---

    def _run_body(
        self, state: RunState, stage: Stage, start: Snapshot
    ) -> tuple[Snapshot, tuple[str, ...]]:
        body = self.bodies.get(stage.id)
        if body is None:
            raise StageFailure("stage_error", f"{stage.id} の本体が束縛されていない")
        workspace = self.workdir / "workspaces" / f"{state.seq}-{stage.id}-{state.visit}"
        materialize(start, self.store, workspace)
        try:
            context = _Context(self, state, stage, workspace)
            try:
                body(context)
            except AwaitingAnswer as waiting:
                if not stage.awaits_user:
                    message = f"{stage.id} は awaits_user を宣言していないのに中断の合図を送った"
                    raise StageFailure("contract_violation", message) from waiting
                raise
            except ReplayOnly.Missing:
                raise
            except ContractViolation as e:
                raise StageFailure("contract_violation", str(e)) from e
            except Exception as e:
                # 合図を別の例外に包み直しても、握りつぶした場合と同じに扱う
                if context.missing is None and context.awaiting is None:
                    raise StageFailure("stage_error", f"{type(e).__name__}: {e}") from e
            if context.missing is not None:
                raise context.missing
            if context.awaiting is not None:
                raise AwaitingAnswer(context.awaiting)
            if context.violations:
                raise StageFailure("contract_violation", "; ".join(context.violations))
            memory = {**start.memory, **context.written}
            captured = capture(workspace, self.workflow, stage, start, self.store, memory)
            if captured.violations:
                raise StageFailure("contract_violation", "; ".join(captured.violations))
            return captured.snapshot, captured.discarded
        finally:
            shutil.rmtree(workspace, ignore_errors=True)


def _key(*parts: str | int) -> list[str | int]:
    return list(parts)


def _metric_json(result: MetricResult) -> JSONValue:
    return result.to_json()
