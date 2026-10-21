"""toy-minimal の定義の完了条件（plan.md 第6節 F1）。

- 3〜4 ステージで、ロールバック、carry、フェーズ境界越え、ユーザー待ちを含む
- 整合性検査器を違反も警告も無く通る（指標レジストリは玩具の実装）
- 遷移の六種（決定 追加の論点 B）のそれぞれが、定義の上で起こりうる
"""

from pathlib import Path
from typing import Any

from toy_minimal.metrics import REGISTRY

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.spec import check_workflow_file

WORKFLOW = Path(__file__).resolve().parents[1] / "workflow.yaml"
DOC: Any = load_workflow_document(WORKFLOW)
PHASES = DOC["workflow"]["phases"]
STAGES = [(p["id"], s) for p in PHASES for s in p["stages"]]
PHASE_OF = {s["id"]: pid for pid, s in STAGES}
EDGES = [(s, rb) for _, s in STAGES for rb in s["rollback"]]


def test_passes_checker_without_warnings() -> None:
    assert check_workflow_file(WORKFLOW, REGISTRY.names()) == []


def test_size() -> None:
    assert 3 <= len(STAGES) <= 4
    assert len(PHASES) >= 2


def transition_coverage() -> dict[str, bool]:
    """遷移の六種のそれぞれが、この定義の上で起こりうるか。"""
    return {
        "next": len(STAGES) >= 2,
        "rollback": bool(EDGES),
        "max 超過": all("max" in rb for _, rb in EDGES) and bool(EDGES),
        "unknown": all(any(e["id"] == "unknown" for e in s["end_state"]) for _, s in STAGES),
        "中断と再開": any(s.get("awaits_user") for _, s in STAGES),
        "フェーズ境界越え": any(PHASE_OF[s["id"]] != PHASE_OF[rb["stage"]] for s, rb in EDGES),
    }


def test_every_transition_kind_is_possible() -> None:
    coverage = transition_coverage()
    assert len(coverage) == 6
    assert all(coverage.values()), coverage


def test_has_carry() -> None:
    assert any(rb.get("carry") for _, rb in EDGES)


def test_every_phase_has_a_gate() -> None:
    for phase in PHASES:
        assert phase["goal"]["qualitative"]
        assert phase["goal"]["quantitative"]
