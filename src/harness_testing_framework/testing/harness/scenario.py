"""シナリオ（contract/conformance/scenario.schema.json）を読み、ランタイムで実行して要約する。"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from harness_testing_framework.contract import (
    JSONValue,
    MetricRegistry,
    UserIO,
    load_contract_schema,
)
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
    starts: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    options: Mapping[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Scenario:
    """読み込んだシナリオ（形は scenario.schema.json）。ファイルの参照は内容の文字列に置き換えてある。

    凍結した dataclass なので、一部を変えた写しは `dataclasses.replace(scenario, inputs=...)` で作れる。
    """

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


def conformance_dir() -> Path:
    """パッケージに同梱した契約適合テスト一式（contract/conformance/ の写し。README.md、workflows/、
    scenarios/、files/、manifests.json）のディレクトリ。シナリオの形式は load_contract_schema で読む。"""
    path = Path(str(files("harness_testing_framework.contract") / "conformance"))
    if not path.is_dir():
        raise FileNotFoundError(f"契約適合テスト一式がファイルとして読めない: {path}")
    return path


def conformance_scenarios() -> list[Path]:
    """同梱した契約適合テストのシナリオのファイル（名前の順）。"""
    return sorted((conformance_dir() / "scenarios").glob("*.yaml"))


def _contents(path: Path, files: Mapping[str, Any]) -> dict[str, str]:
    """ファイルの内容の対応を読む。{from: パス} はシナリオのファイルからの相対パスで、鍵が / で終わるなら
    そのディレクトリの下のすべてのファイルを、鍵の下の相対パスに置く（README.md）。"""
    out: dict[str, str] = {}
    for key, value in files.items():
        if isinstance(value, str):
            out[key] = value
            continue
        source = path.parent / value["from"]
        if key.endswith("/") != value["from"].endswith("/"):
            raise ScenarioInvalid(
                f"{path}: {key} の from {value['from']} は、どちらも / で終わるか、どちらも終わらない"
            )
        if key.endswith("/"):
            if not source.is_dir():
                raise ScenarioInvalid(f"{path}: {key} の from {value['from']} がディレクトリでない")
            for file in sorted(f for f in source.rglob("*") if f.is_file()):
                out[key + file.relative_to(source).as_posix()] = file.read_text(encoding="utf-8")
        elif source.is_file():
            out[key] = source.read_text(encoding="utf-8")
        else:
            raise ScenarioInvalid(f"{path}: {key} の from {value['from']} がファイルでない")
    return out


def load_scenario(path: Path) -> Scenario:
    """シナリオを読む。ファイルの参照（{from: パス}）は、ここで内容の文字列に置き換える。"""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = list(
        Draft202012Validator(load_contract_schema("scenario.schema.json")).iter_errors(doc)
    )
    if errors:
        raise ScenarioInvalid(f"{path}: " + "; ".join(e.message for e in errors))
    expect = doc["expect"]
    starts = {
        key: {**start, "files": _contents(path, start["files"])}
        for key, start in expect.get("starts", {}).items()
    }
    return Scenario(
        path=path,
        name=doc["scenario"],
        description=doc["description"],
        workflow=(path.parent / doc["workflow"]).resolve(),
        metrics=doc.get("metrics"),
        seed=doc.get("seed", 0),
        threshold=doc.get("threshold", 0.5),
        inputs=_contents(path, doc.get("inputs", {})),
        visits=doc["visits"],
        gates=doc.get("gates", {}),
        operator=doc.get("operator", []),
        user=doc.get("user", []),
        expect=Expectation(
            status=expect["status"],
            trace=expect["trace"],
            memory=expect.get("memory"),
            annotations=expect.get("annotations"),
            starts=starts,
            options=expect.get("options", {}),
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
    problems: list[str] = field(default_factory=list)
    """シナリオの期待との食い違い（verify の結果）。空なら期待どおり。"""


def run_scenario(
    scenario: Scenario,
    workdir: Path,
    *,
    registry: MetricRegistry | None = None,
    fixtures: Path | None = None,
    record: Path | None = None,
    replay: Path | None = None,
    max_resumes: int = 50,
    user: UserIO | None = None,
) -> ScenarioResult:
    """シナリオを参照ランタイムで実行する（README.md の手順）。

    record を与えると外からの値をそこに記録し、replay を与えると記録だけから再生する。
    再生では、偽の分類器・運用者・ユーザー・指標の代わりに、呼ばれたら失敗するものを束縛する。
    user を与えると、シナリオの user の台本の代わりにそれ（ユーザーシミュレータなど）に尋ねる。それが回答を
    保留して中断した時の再開の回答には、シナリオの user の台本を順に使う。
    """
    if scenario.metrics == "conformance":
        registry = ConformanceRegistry()
    if registry is None:
        raise ValueError(f"{scenario.name}: 指標レジストリが要る")
    workflow = load_workflow(scenario.workflow, registry.names())
    script = ScriptedUser(scenario.user)
    user_io: UserIO = script if user is None else user
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
            user_io=user_io,
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
        resume = _resumer(result, script, operator, replay is not None)
        if resume is None:
            break
        # 保存した状態から、新しく組み立てたランタイムで再開する
        state = RunState.from_json(result.state.to_json())
        result = resume(new_runtime(), state)
        events += result.events
        snapshot_ids += result.snapshots
        resumes += 1
    outcome = ScenarioResult(
        status=result.status,
        summary=summarize(events),
        trace=events,
        snapshots=[store.get_snapshot(i) for i in snapshot_ids],
        final_snapshot=store.get_snapshot(result.state.current),
        state=result.state,
        resumes=resumes,
    )
    outcome.problems.extend(verify(scenario, outcome, store))
    return outcome


def verify(scenario: Scenario, result: ScenarioResult, store: BlobStore) -> list[str]:
    """結果をシナリオの期待と比べ、食い違いを一行ずつ返す（README.md の手順 5）。"""
    expect = scenario.expect
    problems: list[str] = []
    if result.summary != expect.trace:
        problems.append(f"trace: {result.summary} != {expect.trace}")
    if result.status != expect.status:
        problems.append(f"status: {result.status} != {expect.status}")
    starts = {
        f"{e['stage']}#{e['visit']}": str(e["snapshot"])
        for e in result.trace
        if e["event"] == "stage_start"
    }
    for key, want in expect.starts.items():
        if key not in starts:
            problems.append(f"starts {key}: 訪問が無い")
            continue
        snapshot = store.get_snapshot(starts[key])
        files = {p: store.get(d).decode("utf-8") for p, d in snapshot.files.items()}
        got = {"files": files, "memory": dict(snapshot.memory), "gates": list(snapshot.gates)}
        for part in ("files", "memory", "gates"):
            if got[part] != want[part]:
                problems.append(f"starts {key} {part}: {got[part]} != {want[part]}")
    evaluations: dict[str, JSONValue] = {}
    for e in result.trace:
        if e["event"] == "evaluation" and isinstance(e["classification"], dict):
            target = e["stage"] if e["scope"] == "stage" else e["phase"]
            evaluations[f"{e['scope']}:{target}#{e['visit']}"] = e["classification"]["options"]
    for key, want_options in expect.options.items():
        if evaluations.get(key) != want_options:
            problems.append(f"options {key}: {evaluations.get(key)} != {want_options}")
    for name, value in (expect.memory or {}).items():
        if result.final_snapshot.memory.get(name) != value:
            problems.append(f"memory {name}: {result.final_snapshot.memory.get(name)} != {value}")
    if (
        expect.annotations is not None
        and len(result.final_snapshot.annotations) != expect.annotations
    ):
        problems.append(
            f"annotations: {len(result.final_snapshot.annotations)} != {expect.annotations}"
        )
    return problems


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
