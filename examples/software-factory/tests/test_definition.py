"""software-factory のワークフロー定義の性質。

- 4 フェーズ以上、8 ステージ以上。ソフトウェア開発の各段（取り込み、要件分析、設計、タスク分割、実装、単体テスト、検証、
  レビュー、リリース）を持つ
- 整合性検査器を違反も警告も無く通る（指標レジストリは実在のツールで測る実装）
- フェーズ境界を越えるロールバック、carry、ユーザー回答待ちを含み、遷移の六種のそれぞれが定義の上で起こりうる
- 全ステージに unknown があり、unknown 以外の end_state はそれぞれ一つの戻り先を持つ
- carry する記憶は、その end_state の記述が証拠として名指す（記述が観測できる条件として書かれていることの一部）
"""

from pathlib import Path
from typing import Any

from software_factory.metrics import REGISTRY

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


def test_size_and_stages() -> None:
    assert len(PHASES) >= 4
    assert len(STAGES) >= 8
    assert [s["id"] for _, s in STAGES] == [
        "intake",
        "analyze",
        "design",
        "plan_tasks",
        "implement",
        "unit_test",
        "acceptance",
        "review",
        "release",
    ]


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


def test_crossing_rollbacks_carry_and_user_wait() -> None:
    crossing = [
        (s["id"], rb["stage"]) for s, rb in EDGES if PHASE_OF[s["id"]] != PHASE_OF[rb["stage"]]
    ]
    assert len(crossing) >= 5, crossing
    assert all(rb.get("carry") for _, rb in EDGES)
    assert [s["id"] for _, s in STAGES if s.get("awaits_user")] == ["intake"]


def test_every_class_has_a_target_and_unknown_has_none() -> None:
    for _, stage in STAGES:
        ids = [e["id"] for e in stage["end_state"]]
        assert ids[-1] == "unknown"
        targets = [rb["state"] for rb in stage["rollback"]]
        assert sorted(targets) == sorted(i for i in ids if i != "unknown"), stage["id"]


def test_end_states_name_the_carried_memory_as_evidence() -> None:
    for stage, rb in EDGES:
        description = next(e["description"] for e in stage["end_state"] if e["id"] == rb["state"])
        for item in rb["carry"]:
            assert f"記憶 {item}" in description, (stage["id"], rb["state"], item)


def test_every_phase_has_a_gate() -> None:
    for phase in PHASES:
        assert phase["goal"]["qualitative"]
        assert phase["goal"]["quantitative"]


def test_release_is_reentered_only_through_its_own_carry() -> None:
    """release に戻る辺は release 自身からの一本だけ。release の分布は carry の有無で決まり、運用者が中止で答える実行では
    それが訪問の区分と一致する（マルコフ合成の前提。tests/stochastic.yaml、test_stochastic.py）。"""
    into_release = [(s["id"], rb) for s, rb in EDGES if rb["stage"] == "release"]
    assert [(source, rb["carry"]) for source, rb in into_release] == [
        ("release", ["missing_notes"])
    ]
    release = next(s for _, s in STAGES if s["id"] == "release")
    assert all(rb["stage"] == "release" for rb in release["rollback"])
    assert [s["id"] for _, s in STAGES][-1] == "release"
