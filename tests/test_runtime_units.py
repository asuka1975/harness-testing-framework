"""参照ランタイムの、シナリオでは通らない契約の強制と境界（契約 第8節、2.2、2.4）。"""

import contextlib
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from harness_testing_framework.contract import (
    Abort,
    Classification,
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
from harness_testing_framework.testing.harness import ConformanceRegistry, evaluation_target

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

    with pytest.raises(OperatorDecisionInvalid):
        _runtime(tmp_path, {"s2": unknown}, operator=Op()).start(0, {"in.txt": b"x"})


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
