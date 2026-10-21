"""シナリオ（contract/conformance/scenario.schema.json）を読み、ランタイムで実行して要約する。"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from harness_testing_framework.contract import JSONValue, MetricRegistry, load_contract_schema
from harness_testing_framework.runtime.checkpoint import BlobStore, Snapshot
from harness_testing_framework.runtime.loader import load_workflow
from harness_testing_framework.runtime.recorder import Passthrough, Recorder, Recording, ReplayOnly
from harness_testing_framework.runtime.runner import (
    RunResult,
    RunState,
    Runtime,
    decision_from_json,
)
from harness_testing_framework.testing.harness.fakes import (
    ConformanceRegistry,
    ScriptedBody,
    ScriptedClassifier,
    ScriptedOperator,
    ScriptedUser,
    Unreachable,
)
from harness_testing_framework.testing.harness.trace import summarize


class ScenarioInvalid(ValueError):
    """シナリオがスキーマに適合しない。"""


@dataclass(frozen=True)
class Expectation:
    status: str
    trace: list[str]
    memory: Mapping[str, JSONValue] | None = None
    annotations: int | None = None


@dataclass(frozen=True)
class Scenario:
    path: Path
    name: str
    description: str
    workflow: Path
    metrics: str | None
    seed: int
    threshold: float
    inputs: Mapping[str, str]
    visits: Mapping[str, Mapping[str, Any]]
    gates: Mapping[str, Mapping[str, Any]]
    operator: Sequence[Mapping[str, Any]]
    user: Sequence[Mapping[str, Any]]
    expect: Expectation


def load_scenario(path: Path) -> Scenario:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = list(
        Draft202012Validator(load_contract_schema("scenario.schema.json")).iter_errors(doc)
    )
    if errors:
        raise ScenarioInvalid(f"{path}: " + "; ".join(e.message for e in errors))
    expect = doc["expect"]
    return Scenario(
        path=path,
        name=doc["scenario"],
        description=doc["description"],
        workflow=(path.parent / doc["workflow"]).resolve(),
        metrics=doc.get("metrics"),
        seed=doc.get("seed", 0),
        threshold=doc.get("threshold", 0.5),
        inputs=doc.get("inputs", {}),
        visits=doc["visits"],
        gates=doc.get("gates", {}),
        operator=doc.get("operator", []),
        user=doc.get("user", []),
        expect=Expectation(
            expect["status"], expect["trace"], expect.get("memory"), expect.get("annotations")
        ),
    )


@dataclass(frozen=True)
class ScenarioResult:
    status: str
    summary: list[str]
    trace: list[dict[str, JSONValue]]
    snapshots: list[Snapshot]
    final_snapshot: Snapshot
    state: RunState
    resumes: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def run_scenario(
    scenario: Scenario,
    workdir: Path,
    *,
    registry: MetricRegistry | None = None,
    fixtures: Path | None = None,
    record: Path | None = None,
    replay: Path | None = None,
    max_resumes: int = 50,
) -> ScenarioResult:
    """シナリオを参照ランタイムで実行する（README.md の手順）。

    record を与えると外からの値をそこに記録し、replay を与えると記録だけから再生する。
    再生では、偽の分類器・運用者・ユーザー・指標の代わりに、呼ばれたら失敗するものを束縛する。
    """
    if scenario.metrics == "conformance":
        registry = ConformanceRegistry()
    if registry is None:
        raise ValueError(f"{scenario.name}: 指標レジストリが要る")
    workflow = load_workflow(scenario.workflow, registry.names())
    user = ScriptedUser(scenario.user)
    operator = ScriptedOperator(scenario.operator)
    classifier = ScriptedClassifier(
        {k: v["classify"] for k, v in scenario.visits.items() if "classify" in v}, scenario.gates
    )
    recorder: Recorder = Passthrough()
    if record is not None:
        recorder = Recording(record)
    if replay is not None:
        recorder = ReplayOnly(replay)
    body = ScriptedBody(scenario.visits, fixtures)
    store = BlobStore(workdir / "store")

    def new_runtime() -> Runtime:
        if replay is not None:
            unreachable = Unreachable(registry.names())
            return Runtime(
                workflow,
                {s.id: body for s in workflow.stages},
                registry=unreachable,
                classifier=unreachable,
                operator=unreachable,
                user_io=unreachable,
                store=store,
                workdir=workdir,
                threshold=scenario.threshold,
                recorder=recorder,
            )
        return Runtime(
            workflow,
            {s.id: body for s in workflow.stages},
            registry=registry,
            classifier=classifier,
            operator=operator,
            user_io=user,
            store=store,
            workdir=workdir,
            threshold=scenario.threshold,
            recorder=recorder,
        )

    inputs = {p: c.encode("utf-8") for p, c in scenario.inputs.items()}
    result = new_runtime().start(scenario.seed, inputs)
    events, snapshot_ids = list(result.events), list(result.snapshots)
    resumes = 0
    while result.status in ("suspended", "awaiting_operator") and resumes < max_resumes:
        resume = _resumer(result, user, operator, replay is not None)
        if resume is None:
            break
        # 保存した状態から、新しく組み立てたランタイムで再開する
        state = RunState.from_json(result.state.to_json())
        result = resume(new_runtime(), state)
        events += result.events
        snapshot_ids += result.snapshots
        resumes += 1
    return ScenarioResult(
        status=result.status,
        summary=summarize(events),
        trace=events,
        snapshots=[store.get_snapshot(i) for i in snapshot_ids],
        final_snapshot=store.get_snapshot(result.state.current),
        state=result.state,
        resumes=resumes,
    )


def _resumer(
    result: RunResult, user: ScriptedUser, operator: ScriptedOperator, replaying: bool
) -> Callable[[Runtime, RunState], RunResult] | None:
    """中断なら次の回答で、escalate 待ちなら次の選択で再開する手続き。台本が尽きたら None。"""
    if result.status == "suspended":
        entry = None if replaying else user.next_entry()
        if not replaying and (entry is None or entry.get("defer")):
            return None
        answer = "" if entry is None else str(entry["answer"])
        return lambda runtime, state: runtime.resume(state, answer=answer)
    entry = {"kind": "abort"} if replaying else operator.next_entry()
    if entry is None or entry["kind"] == "defer":
        return None
    decision = decision_from_json(entry)
    return lambda runtime, state: runtime.resume(state, decision=decision)
