"""software-factory のワークフロー定義の性質。

- 4 フェーズ以上、8 ステージ以上。ソフトウェア開発の各段（取り込み、要件分析、設計、タスク分割、実装、単体テスト、検証、
  レビュー、リリース）を持つ
- 整合性検査器を違反も警告も無く通る（指標レジストリは実在のツールで測る実装）
- フェーズ境界を越えるロールバック、carry、ユーザー回答待ちを含み、遷移の六種のそれぞれが定義の上で起こりうる
- 全ステージに unknown があり、unknown 以外の end_state はそれぞれ一つの戻り先を持つ
- carry する記憶は、その end_state の記述が証拠として名指す（記述が観測できる条件として書かれていることの一部）
- unit_test のテストの不足と不備は、一つの end_state（tests_insufficient）と一つの記憶（coverage_gaps）で扱う（往復 11 で
  人間の決定により、往復 10 の tests_defective の分割を取り消した）。代表の test_report.md は、印のクラスの記述が証拠と
  する節だけが埋まっている
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


def test_unit_test_keeps_one_class_for_missing_and_wrong_tests() -> None:
    """unit_test のテストの不足（足りない）と不備（誤っている）は、どちらも tests_insufficient で unit_test 自身に戻り、記憶
    coverage_gaps 一つで持ち帰る。戻り先が同じで、分けて数えたいだけのクラスは分けない（adopting.md 第13節）。往復 10 で
    足した tests_defective は、人間の決定（docs/review-findings.md の G）で取り消し、unit_test と construction のゲートの
    記述を往復 10 の前（人間が承認した文）に戻した。テスト自身の誤り（準備、呼び出し、import）で失敗するテストは、どの
    end_state にも当たらず unknown になる（前と同じ）。"""
    unit_test = next(s for _, s in STAGES if s["id"] == "unit_test")
    ids = [e["id"] for e in unit_test["end_state"]]
    assert ids == ["impl_defect", "tests_insufficient", "unknown"]
    edges = {rb["state"]: rb for rb in unit_test["rollback"]}
    assert edges["tests_insufficient"] == {
        "state": "tests_insufficient",
        "stage": "unit_test",
        "carry": ["coverage_gaps"],
        "max": 2,
    }
    assert unit_test["artifacts"]["memory_in"] == ["coverage_gaps"]
    assert unit_test["artifacts"]["memory_out"] == ["failing_tests", "coverage_gaps"]
    description = {e["id"]: e["description"] for e in unit_test["end_state"]}
    assert description["impl_defect"].endswith("tests_insufficient に優先する。")
    assert "requirements.md の要件に反する期待を持つテスト" in description["tests_insufficient"]
    assert "テスト自身の誤り" not in unit_test["description"] + "".join(description.values())
    assert "「## テスト」「## 失敗」「## 未網羅」の節" in unit_test["description"]
    assert "「## 失敗」と「## 未網羅」が空である" in unit_test["goal"]["qualitative"]
    construction = next(p for p in PHASES if p["id"] == "construction")
    assert "問い、失敗、未網羅が無い" in construction["goal"]["qualitative"]
    assert "不備" not in construction["goal"]["qualitative"]


REPORT_SECTIONS = ["## テスト", "## 失敗", "## 未網羅"]
# 印のクラスごとに、test_report.md の空でない節（「（なし）」でない節）。記述が証拠とする節だけが埋まる
FILLED = {
    "goal": set(),
    "impl_defect": {"## 失敗"},
    "tests_insufficient": {"## 未網羅"},
}


def test_unit_test_reports_fill_the_section_their_class_names() -> None:
    """unit_test の全フィクスチャの test_report.md が三つの節を持ち、印のクラスの記述が証拠とする節だけが埋まっている。
    確率 0 の変種 defective（要件に反する期待を持つテスト）は tests_insufficient の代表で、不備を「## 未網羅」に書く。"""
    reports = sorted(
        (WORKFLOW.parent / "tests" / "fixtures" / "unit_test").glob("*/test_report.md")
    )
    seen: set[str] = set()
    for path in reports:
        text = path.read_text("utf-8")
        mark = text.splitlines()[0].removeprefix("[[class unit_test=").removesuffix("]]")
        headings = [line for line in text.splitlines() if line.startswith("## ")]
        assert headings == REPORT_SECTIONS, path
        if mark == "unknown":
            continue
        bodies = dict(zip(headings, text.split("\n## ")[1:], strict=True))
        filled = {h for h in REPORT_SECTIONS[1:] if "（なし）" not in bodies[h].split("\n", 1)[1]}
        assert filled == FILLED[mark], (path, filled)
        seen.add(mark)
    assert seen == set(FILLED)


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
