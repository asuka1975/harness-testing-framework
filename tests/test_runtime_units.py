"""参照ランタイムの、シナリオでは通らない契約の強制と境界（契約 第8節、2.2、2.4）。"""

import contextlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from harness_testing_framework.contract import (
    Abort,
    AwaitingAnswer,
    Classification,
    ContinueAsGoal,
    JSONValue,
    Option,
    Question,
    RollbackTo,
    SnapshotView,
    StageContext,
)
from harness_testing_framework.runtime import (
    BlobStore,
    OperatorDecisionInvalid,
    Passthrough,
    Recording,
    ReplayOnly,
    Runtime,
    Snapshot,
    WorkflowInvalid,
    load_workflow,
)
from harness_testing_framework.runtime.model import Criterion
from harness_testing_framework.runtime.oracle import satisfies, state_document
from harness_testing_framework.runtime.runner import RunState
from harness_testing_framework.testing.harness import (
    ConformanceRegistry,
    ScriptedClassifier,
    evaluation_target,
)

ROOT = Path(__file__).resolve().parents[1]
BASIC = ROOT / "contract/conformance/workflows/basic.yaml"


class Goal:
    """どの評価にも、選択肢に goal があれば goal を、なければ答え無しを返す分類器。"""

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        return (
            Classification("goal", 1.0)
            if any(o.id == "goal" for o in options)
            else Classification(None, 0)
        )


class AbortAll:
    def __init__(self) -> None:
        self.seen: list[str] = []

    def decide(self, escalation: object) -> Abort:
        self.seen.append(str(escalation))
        return Abort()


def _ok(context: StageContext) -> None:
    n = context.stage_id[-1]
    (context.workspace / f"s{n}.txt").write_text(n)
    (context.workspace / f"s{n}.flag").write_text("true")
    if n == "2":
        (context.workspace / "gate1.flag").write_text("true")
    if n == "3":
        (context.workspace / "gate2.num").write_text("0")


def _runtime(tmp_path: Path, bodies: Mapping[str, object], **kw: object) -> Runtime:
    workflow = load_workflow(BASIC, ConformanceRegistry().names())
    return Runtime(
        workflow,
        {s.id: bodies.get(s.id, _ok) for s in workflow.stages},  # type: ignore[misc]
        registry=kw.pop("registry", ConformanceRegistry()),  # type: ignore[arg-type]
        classifier=Goal(),
        operator=kw.pop("operator", AbortAll()),  # type: ignore[arg-type]
        store=BlobStore(tmp_path / "store"),
        workdir=tmp_path,
        **kw,  # type: ignore[arg-type]
    )


def _errors(result_events: list[dict[str, JSONValue]]) -> list[JSONValue]:
    return [e["error"] for e in result_events if e["event"] == "stage_end" and e["error"]]


def test_happy_path_with_python_bodies(tmp_path: Path) -> None:
    result = _runtime(tmp_path, {}).start(0, {"in.txt": b"x"})
    assert result.status == "completed"


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        (lambda c: c.read_memory("m33"), "memory_in に無い m33"),
        (lambda c: c.write_memory("m99", 1), "memory_out に無い m99"),
        (lambda c: c.user_io.ask(Question("?")), "awaits_user"),
    ],
)
def test_contract_violations_in_context(body: object, fragment: str, tmp_path: Path) -> None:
    result = _runtime(tmp_path, {"s2": body}).start(0, {"in.txt": b"x"})
    errors = _errors(result.events)
    assert result.status == "aborted"
    assert errors and isinstance(errors[0], dict)
    assert errors[0]["kind"] == "contract_violation"
    assert fragment in str(errors[0]["message"])


def test_violation_is_reported_even_if_body_swallows_it(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        with contextlib.suppress(Exception):
            c.write_memory("m99", 1)
        _ok(c)

    errors = _errors(_runtime(tmp_path, {"s2": body}).start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and errors[0]["kind"] == "contract_violation"


def test_unbound_body_and_unbound_llm_are_stage_errors(tmp_path: Path) -> None:
    workflow = load_workflow(BASIC, ConformanceRegistry().names())
    runtime = Runtime(
        workflow,
        {},
        registry=ConformanceRegistry(),
        classifier=Goal(),
        operator=AbortAll(),
        store=BlobStore(tmp_path / "store"),
        workdir=tmp_path,
    )
    errors = _errors(runtime.start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and "束縛されていない" in str(errors[0]["message"])

    def uses_llm(c: StageContext) -> None:
        c.llm.complete({"prompt": "x"})

    errors = _errors(_runtime(tmp_path / "b", {"s1": uses_llm}).start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and errors[0]["kind"] == "stage_error"


def test_llm_calls_go_through_recorder(tmp_path: Path) -> None:
    class Echo:
        def __init__(self) -> None:
            self.calls = 0

        def complete(self, request: JSONValue) -> JSONValue:
            self.calls += 1
            return {"echo": request}

    seen: list[JSONValue] = []

    def body(c: StageContext) -> None:
        seen.append(c.llm.complete({"prompt": c.stage_id}))
        _ok(c)

    echo = Echo()
    _runtime(
        tmp_path / "a", {"s1": body}, llm=echo, recorder=Recording(tmp_path / "rec.jsonl")
    ).start(0, {"in.txt": b"x"})
    _runtime(tmp_path / "b", {"s1": body}, recorder=ReplayOnly(tmp_path / "rec.jsonl")).start(
        0, {"in.txt": b"x"}
    )
    assert echo.calls == 1
    assert seen == [{"echo": {"prompt": "s1"}}] * 2


def test_seed_depends_on_stage_and_visit(tmp_path: Path) -> None:
    seeds: list[int] = []

    def body(c: StageContext) -> None:
        seeds.append(c.seed)
        _ok(c)

    _runtime(tmp_path / "a", {"s1": body}).start(3, {"in.txt": b"x"})
    _runtime(tmp_path / "b", {"s1": body}).start(3, {"in.txt": b"x"})
    _runtime(tmp_path / "c", {"s1": body}).start(4, {"in.txt": b"x"})
    assert seeds[0] == seeds[1] != seeds[2]


@pytest.mark.parametrize(
    "decision",
    [RollbackTo("s3"), RollbackTo("s1", ("m99",))],
)
def test_invalid_operator_rollback_is_rejected(decision: RollbackTo, tmp_path: Path) -> None:
    class Op:
        def decide(self, escalation: object) -> RollbackTo:
            return decision

    def unknown(c: StageContext) -> None:
        (c.workspace / "s2.txt").write_text("x")

    result = _runtime(tmp_path, {"s2": unknown}, operator=Op()).start(0, {"in.txt": b"x"})
    assert result.status == "awaiting_operator"
    kinds = [e["event"] for e in result.events]
    assert kinds[-3:] == ["warning", "escalation", "run_end"]
    assert result.events[-2]["decision"] is None
    assert OperatorDecisionInvalid.__name__ in str(result.events[-3]["message"])


def test_resume_requires_the_right_input(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {})
    with pytest.raises(ValueError):
        runtime.resume(RunState(seed=0, status="suspended"))
    with pytest.raises(ValueError):
        runtime.resume(RunState(seed=0, status="awaiting_operator"))
    with pytest.raises(ValueError):
        runtime.resume(RunState(seed=0, status="completed"))


def test_loader_rejects_invalid_workflow() -> None:
    bad = ROOT / "schema/examples/invalid-spec/rollback_forward/rollback_to_later_stage.yaml"
    with pytest.raises(WorkflowInvalid, match="rollback_forward"):
        load_workflow(bad, ["output_exists", "defect_count"])


def test_non_numeric_metric_value_is_unmet(tmp_path: Path) -> None:
    class Weird(ConformanceRegistry):
        def measure(
            self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]
        ) -> bool | float:
            return "yes"  # type: ignore[return-value]

    result = _runtime(tmp_path, {}, registry=Weird()).start(0, {"in.txt": b"x"})
    evaluation = next(e for e in result.events if e["event"] == "evaluation")
    assert isinstance(evaluation["metrics"], dict)
    flag = evaluation["metrics"]["flag"]
    assert isinstance(flag, dict) and flag["passed"] is False and "error" in flag


@pytest.mark.parametrize(
    ("criterion", "value", "expected"),
    [
        (Criterion("m", "", True, None, None, {}), True, True),
        (Criterion("m", "", True, None, None, {}), 1, False),
        (Criterion("m", "", 1, None, None, {}), 1.0, True),
        (Criterion("m", "", 1, None, None, {}), True, False),
        (Criterion("m", "", None, 0, 1, {}), 0.5, True),
        (Criterion("m", "", None, 0, None, {}), -1, False),
        (Criterion("m", "", None, None, 1, {}), True, False),
    ],
)
def test_satisfies(criterion: Criterion, value: bool | float, expected: bool) -> None:
    assert satisfies(criterion, value) is expected


def test_state_document_projection(tmp_path: Path) -> None:
    store = BlobStore(tmp_path)
    files = {
        "a.txt": store.put("本文".encode()),
        "bin": store.put(b"\xff\xfe"),
        "out/x.txt": store.put(b"x"),
    }
    snapshot = Snapshot(files=files, memory={"m": {"k": 1}})
    paths = ["a.txt", "bin", "missing.txt", "out/", "empty/", "a.txt"]
    doc = state_document("# 評価: stage s visit 2", paths, ["m"], snapshot, store, 10_000)
    assert evaluation_target(doc) == ("stage", "s", 2)
    assert doc.count("## ファイル a.txt") == 1
    assert "文字として読めない: 2 バイト" in doc
    assert "## ファイル missing.txt\n（無い）" in doc
    assert "## ファイル out/x.txt\nx" in doc
    assert "## ファイル empty/\n（無い）" in doc
    assert '## 記憶 m\n{"k": 1}' in doc
    short = state_document("# 評価: stage s visit 2", paths, ["m"], snapshot, store, 60)
    assert len(short) <= 60 and "切り詰めた" in short


def test_out_of_scope_memory_value_must_be_json(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        c.write_memory("m21", {1, 2})  # type: ignore[arg-type]

    errors = _errors(_runtime(tmp_path, {"s2": body}).start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and errors[0]["kind"] == "stage_error"


# --- F2 の検証の指摘（中-1〜中-4、中-7、低-1〜低-5、低-8、低-10、低-12） ---


class Deferring:
    def ask(self, question: Question) -> str:
        raise AwaitingAnswer(question)


def test_suspend_saves_the_pending_question(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        c.user_io.ask(Question("読者は誰か", ("A", "B")))

    result = _runtime(tmp_path, {"s1": body}, user_io=Deferring()).start(0, {"in.txt": b"x"})
    assert result.status == "suspended"
    assert result.state.pending == {
        "kind": "user",
        "question": {"text": "読者は誰か", "choices": ["A", "B"]},
    }


def test_record_keys_include_the_run_seed(tmp_path: Path) -> None:
    rec = tmp_path / "rec.jsonl"
    _runtime(tmp_path / "a", {}, recorder=Recording(rec)).start(1, {"in.txt": b"x"})
    with pytest.raises(ReplayOnly.Missing):
        _runtime(tmp_path / "b", {}, recorder=ReplayOnly(rec)).start(999, {"in.txt": b"x"})


class Counter:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, request: JSONValue) -> JSONValue:
        self.calls += 1
        return self.calls


class AnswerLater:
    def __init__(self) -> None:
        self.asked = 0

    def ask(self, question: Question) -> str:
        self.asked += 1
        raise AwaitingAnswer(question)


@pytest.mark.parametrize("record", [False, True])
def test_llm_responses_are_replayed_after_resume(record: bool, tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        first = c.llm.complete({"prompt": "下書き"})
        answer = c.user_io.ask(Question("よいか"))
        (c.workspace / "s1.txt").write_text(f"{first} {answer}")
        (c.workspace / "s1.flag").write_text("true")

    llm = Counter()
    recorder = Recording(tmp_path / "rec.jsonl") if record else Passthrough()
    runtime = _runtime(tmp_path, {"s1": body}, llm=llm, user_io=AnswerLater(), recorder=recorder)
    suspended = runtime.start(0, {"in.txt": b"x"})
    state = RunState.from_json(suspended.state.to_json())
    resumed = runtime.resume(state, answer="はい")
    assert resumed.status == "completed"
    assert llm.calls == 1
    final = runtime.store.get_snapshot(resumed.state.current)
    assert runtime.store.get(final.files["s1.txt"]) == "1 はい".encode()
    if record:
        lines = (tmp_path / "rec.jsonl").read_text(encoding="utf-8").splitlines()
        kinds = [json.loads(json.loads(line)["key"])[0] for line in lines]
        assert kinds.count("llm") == 1


def test_swallowed_suspension_still_suspends(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        with contextlib.suppress(AwaitingAnswer):
            c.user_io.ask(Question("?"))
        _ok(c)

    result = _runtime(tmp_path, {"s1": body}, user_io=Deferring()).start(0, {"in.txt": b"x"})
    assert result.status == "suspended"


def test_swallowed_replay_miss_still_stops(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        with contextlib.suppress(Exception):
            c.llm.complete({"prompt": "x"})
        _ok(c)

    # LLM を呼ばない実行を記録し、LLM を呼ぶ本体で再生する。足りないのは LLM の呼び出しだけ
    rec = tmp_path / "rec.jsonl"
    _runtime(tmp_path / "a", {}, recorder=Recording(rec)).start(0, {"in.txt": b"x"})
    runtime = _runtime(tmp_path / "b", {"s1": body}, recorder=ReplayOnly(rec))
    with pytest.raises(ReplayOnly.Missing):
        runtime.start(0, {"in.txt": b"x"})


def test_context_has_no_public_bypass(tmp_path: Path) -> None:
    seen: list[list[str]] = []

    def body(c: StageContext) -> None:
        seen.append([n for n in dir(c) if not n.startswith("_")])
        _ok(c)

    _runtime(tmp_path, {"s1": body}).start(0, {"in.txt": b"x"})
    assert "ask" not in seen[0] and "complete" not in seen[0]


def test_suspension_from_stage_without_awaits_user_is_a_violation(tmp_path: Path) -> None:
    def body(c: StageContext) -> None:
        raise AwaitingAnswer(Question("?"))

    errors = _errors(_runtime(tmp_path, {"s2": body}).start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and errors[0]["kind"] == "contract_violation"


class BadConfidence:
    def __init__(self, confidence: float) -> None:
        self.confidence = confidence

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        return Classification("goal", self.confidence)


class Crashing:
    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        raise RuntimeError("分類器が落ちた")


@pytest.mark.parametrize(
    "classifier", [BadConfidence(float("nan")), BadConfidence(1.5), Crashing()]
)
def test_invalid_classifier_output_is_no_answer(classifier: object, tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, {})
    runtime.classifier = classifier  # type: ignore[assignment]
    result = runtime.start(0, {"in.txt": b"x"})
    evaluation = next(e for e in result.events if e["event"] == "evaluation")
    assert evaluation["outcome"] == "unknown"
    assert evaluation["classification"] == {
        "options": ["goal", "unknown"],
        "choice": None,
        "confidence": 0.0,
    }


def test_metric_crash_is_a_measurement_failure(tmp_path: Path) -> None:
    class Crash(ConformanceRegistry):
        def measure(
            self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]
        ) -> bool | float:
            raise ZeroDivisionError("壊れた指標")

    result = _runtime(tmp_path, {}, registry=Crash()).start(0, {"in.txt": b"x"})
    evaluation = next(e for e in result.events if e["event"] == "evaluation")
    assert isinstance(evaluation["metrics"], dict)
    flag = evaluation["metrics"]["flag"]
    assert (
        isinstance(flag, dict)
        and flag["passed"] is False
        and "ZeroDivisionError" in str(flag["error"])
    )


def test_symlink_in_workspace_is_a_violation(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("秘密")

    def body(c: StageContext) -> None:
        _ok(c)
        (c.workspace / "s1.txt").unlink()
        (c.workspace / "s1.txt").symlink_to(outside)

    errors = _errors(_runtime(tmp_path / "w", {"s1": body}).start(0, {"in.txt": b"x"}).events)
    assert isinstance(errors[0], dict) and errors[0]["kind"] == "contract_violation"
    assert "記号リンク" in str(errors[0]["message"])


def test_seeds_differ_by_stage_and_visit_within_a_run(tmp_path: Path) -> None:
    seeds: dict[str, int] = {}

    def body(c: StageContext) -> None:
        seeds[f"{c.stage_id}#{c.visit}"] = c.seed
        _ok(c)

    class Op:
        def decide(self, escalation: object) -> object:
            from harness_testing_framework.contract import Rerun

            return Rerun() if len(seeds) < 3 else Abort()

    class OnceUnknown:
        def classify(self, state: str, options: Sequence[Option]) -> Classification:
            if state.startswith("# 評価: stage s1 visit 1"):
                return Classification(None, 0)
            return Goal().classify(state, options)

    runtime = _runtime(tmp_path, {"s1": body, "s2": body}, operator=Op())
    runtime.classifier = OnceUnknown()
    runtime.start(5, {"in.txt": b"x"})
    assert {"s1#1", "s1#2", "s2#1"} <= set(seeds)
    assert len({seeds["s1#1"], seeds["s1#2"], seeds["s2#1"]}) == 3


def test_body_reads_carried_memory(tmp_path: Path) -> None:
    def s1(c: StageContext) -> None:
        (c.workspace / "s1.txt").write_text(str(c.read_memory("m21")))
        (c.workspace / "s1.flag").write_text("true")

    def s2(c: StageContext) -> None:
        c.write_memory("m21", "直す点")
        _ok(c)

    classifier = ScriptedClassifier(
        {
            "s1#1": {"choice": "goal", "confidence": 1},
            "s2#1": {"choice": "e2_back", "confidence": 1},
            "s1#2": {"choice": "goal", "confidence": 1},
        },
        {},
    )
    runtime = _runtime(tmp_path, {"s1": s1, "s2": s2})
    runtime.classifier = classifier
    result = runtime.start(0, {"in.txt": b"x"})
    starts = [e for e in result.events if e["event"] == "stage_start" and e["stage"] == "s2"]
    second = runtime.store.get_snapshot(str(starts[1]["snapshot"]))
    assert runtime.store.get(second.files["s1.txt"]) == "直す点".encode()


def test_continue_as_goal_records_who(tmp_path: Path) -> None:
    class Op:
        def __init__(self, by: str) -> None:
            self.by = by

        def decide(self, escalation: object) -> ContinueAsGoal:
            return ContinueAsGoal("許容", self.by)

    def unknown(c: StageContext) -> None:
        (c.workspace / "s1.txt").write_text("x")

    for by, expected in [("", "operator"), ("田中", "田中")]:
        runtime = _runtime(tmp_path / (by or "anon"), {"s1": unknown}, operator=Op(by))
        result = runtime.start(0, {"in.txt": b"x"})
        final = runtime.store.get_snapshot(result.state.current)
        assert final.annotations[0].by == expected


def test_evaluation_inputs(tmp_path: Path) -> None:
    calls: list[tuple[str, list[str]]] = []

    class Spy:
        def classify(self, state: str, options: Sequence[Option]) -> Classification:
            calls.append((state, [o.id for o in options]))
            return Goal().classify(state, options)

    def s3(c: StageContext) -> None:
        c.write_memory("m33", "出力の記憶")
        _ok(c)

    runtime = _runtime(tmp_path, {"s3": s3})
    runtime.classifier = Spy()
    runtime.start(0, {"in.txt": b"x"})
    by_header = {state.splitlines()[0]: (state, options) for state, options in calls}
    stage3, options3 = by_header["# 評価: stage s3 visit 1"]
    assert options3 == ["goal", "e3_back", "e3_retry", "unknown"]
    assert "## ファイル s2.txt" in stage3 and "## ファイル s1.txt" not in stage3
    assert '## 記憶 m33\n"出力の記憶"' in stage3
    assert "## 記憶 m32" in stage3
    gate1, options_gate1 = by_header["# 評価: phase p1 visit 1"]
    assert options_gate1 == ["goal", "e2_back", "unknown"]
    assert "## ファイル in.txt" in gate1 and "## ファイル s1.txt" in gate1
    assert "## ファイル gate1.flag" in gate1 and "## ファイル s3.txt" not in gate1


def test_metric_view_has_the_stage_start_as_baseline(tmp_path: Path) -> None:
    seen: dict[str, object] = {}

    class Changed(ConformanceRegistry):
        def measure(
            self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]
        ) -> bool | float:
            base = view.baseline()
            key = "phase" if args.get("path") in ("gate1.flag", "gate2.num") else "stage"
            if base is not None:
                changed = [p for p in view.list_files() if not base.exists(p)]
                seen.setdefault(f"{key}:{args.get('path')}", changed)
            return super().measure(name, view, args)

    _runtime(tmp_path, {}, registry=Changed()).start(0, {"in.txt": b"x"})
    assert seen["stage:s2.flag"] == ["gate1.flag", "s2.flag", "s2.txt"]
    assert seen["phase:gate1.flag"] == ["gate1.flag", "s1.flag", "s1.txt", "s2.flag", "s2.txt"]
