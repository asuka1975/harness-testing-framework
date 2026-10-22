"""software-factory の遷移の決定論テスト。

- 遷移の六種をすべて通す（フェーズ境界越えは、定義の上の六本の辺のすべてと、運用者による越境）
- 定義の上のロールバックの辺 12 本をすべて通す（自分自身への辺と、plan_tasks → design を含む）。どの辺についても、戻った直後の
  訪問の開始時スナップショットを expect.starts で確かめ、carry する記憶が空でない値で届く
- escalate の四つの選択が動く
- 指標は実在のツール（pytest、coverage、ruff、compileall）で測り、その値で選択肢から goal が外れることも確かめる
- 記録再生で同一のスナップショットが得られる
- シナリオの inputs は、確率的な実行と同じフィクスチャ（依頼と変更前のコードベース）である。シナリオはフィクスチャを
  `{from: パス}` で参照する
- コミットしたシナリオの YAML は、software_factory/scenarios.py が作るものと一致する
  （遷移の列を変えた時と、ok のフィクスチャのファイルを足し引きした時は `python -m software_factory.scenarios` で作り直す）
- 要求の取り込みのペルソナ（ユーザーシミュレータ）を、台本の user の代わりに束縛しても、シナリオの期待どおりに動く
"""

import re
from pathlib import Path
from typing import Any

import pytest
from software_factory.personas import AFTER, PERSONAS, QUESTIONS, REUSE, Persona, PersonaUser
from software_factory.scenarios import GENERATED
from software_factory.stages.deterministic import SCENARIOS, WORKFLOW, inputs, run

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.harness import (
    TRANSITION_KINDS,
    load_scenario,
    transition_coverage,
)

PATHS = sorted(SCENARIOS.glob("*.yaml"))


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_scenario(path: Path, tmp_path: Path) -> None:
    result = run(path, tmp_path)
    assert result.problems == []
    assert result.summary == load_scenario(path).expect.trace


def test_all_six_transition_kinds(tmp_path: Path) -> None:
    covered: set[str] = set()
    for i, path in enumerate(PATHS):
        covered |= transition_coverage(run(path, tmp_path / str(i)).trace)
    assert covered == set(TRANSITION_KINDS)


def test_all_four_escalation_decisions(tmp_path: Path) -> None:
    decisions: set[str] = set()
    for i, path in enumerate(PATHS):
        for event in run(path, tmp_path / str(i)).trace:
            if event["event"] == "escalation" and isinstance(event["decision"], dict):
                decisions.add(str(event["decision"]["kind"]))
    assert decisions == {"rerun", "rollback", "continue_as_goal", "abort"}


def test_crossing_rollbacks_from_every_later_phase(tmp_path: Path) -> None:
    """フェーズ境界を越える定義の上の六本の辺（design → analyze、implement → plan_tasks、acceptance → analyze と
    implement、review → design と implement）と、運用者による越境（release → implement）を通す。"""
    crossings: set[tuple[str, str]] = set()
    for i, path in enumerate(PATHS):
        for event in run(path, tmp_path / str(i)).trace:
            if (
                event["event"] == "transition"
                and event["kind"] == "rollback"
                and event["crosses_phase"]
            ):
                crossings.add((str(event["from"]), str(event["to"])))
    assert crossings >= {
        ("design", "analyze"),
        ("implement", "plan_tasks"),
        ("acceptance", "analyze"),
        ("acceptance", "implement"),
        ("review", "implement"),
        ("review", "design"),
        ("release", "implement"),
    }


def test_every_rollback_edge_is_taken(tmp_path: Path) -> None:
    """定義の上のすべてのロールバックの辺（12 本。自分自身への辺と、同じフェーズの中の plan_tasks → design を含む）を、
    どれかのシナリオが通る。持ち帰る記憶が戻り先の開始時スナップショットに届くことは、下の
    test_every_rollback_edge_has_its_carry_checked_at_the_next_start が確かめる。"""
    doc: Any = load_workflow_document(WORKFLOW)
    edges = {
        (stage["id"], rb["stage"], rb["state"])
        for phase in doc["workflow"]["phases"]
        for stage in phase["stages"]
        for rb in stage["rollback"]
    }
    taken: set[tuple[str, str, str]] = set()
    for i, path in enumerate(PATHS):
        for line in run(path, tmp_path / str(i)).summary:
            match = re.fullmatch(r"rollback (\S+) -> (\S+) \[(\S+) \d+\]( crossing)?", line)
            if match:
                taken.add((match[1], match[2], match[3]))
    assert len(edges) == 12
    assert taken == edges, edges - taken


def test_every_rollback_edge_has_its_carry_checked_at_the_next_start() -> None:
    """定義の上のすべてのロールバックの辺について、どれかのシナリオが、その辺で戻った直後の戻り先の訪問の開始時スナップ
    ショットを expect.starts に持ち、carry するすべての記憶を空でない値で期待する。シナリオが期待どおりに動くこと（実行
    記録の要約と開始時スナップショットの一致）は test_scenario が確かめるので、ここでは期待の側だけを読む。"""
    doc: Any = load_workflow_document(WORKFLOW)
    carry = {
        (stage["id"], rb["stage"], rb["state"]): rb["carry"]
        for phase in doc["workflow"]["phases"]
        for stage in phase["stages"]
        for rb in stage["rollback"]
    }
    checked: set[tuple[str, str, str]] = set()
    for path in PATHS:
        expect = load_scenario(path).expect
        lines = expect.trace
        for i, line in enumerate(lines):
            match = re.fullmatch(r"rollback (\S+) -> (\S+) \[(\S+) \d+\]( crossing)?", line)
            if not match:
                continue
            edge = (match[1], match[2], match[3])
            start = next(x for x in lines[i + 1 :] if x.startswith(f"start {edge[1]}#"))
            visit = start.removeprefix("start ")
            if visit not in expect.starts:
                continue
            memory = expect.starts[visit].get("memory", {})
            if all(memory.get(item) for item in carry[edge]):
                checked.add(edge)
    assert checked == set(carry), set(carry) - checked


@pytest.mark.parametrize("name", ["happy_path_user_suspend", "construction_rollbacks"])
def test_replay_gives_identical_snapshots(name: str, tmp_path: Path) -> None:
    path = SCENARIOS / f"{name}.yaml"
    recorded = run(path, tmp_path / "a", record=tmp_path / "rec.jsonl")
    replayed = run(path, tmp_path / "b", replay=tmp_path / "rec.jsonl")
    assert recorded.problems == [] and replayed.problems == []
    assert [s.id for s in replayed.snapshots] == [s.id for s in recorded.snapshots]
    assert replayed.final_snapshot.id == recorded.final_snapshot.id


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_scenario_inputs_are_the_shared_fixtures(path: Path) -> None:
    scenario = load_scenario(path)
    assert {k: v.encode() for k, v in scenario.inputs.items()} == inputs()


@pytest.mark.parametrize("persona", PERSONAS, ids=[p.name for p in PERSONAS])
def test_personas_can_stand_in_for_the_scripted_user(persona: Persona, tmp_path: Path) -> None:
    """持ち帰った問いをペルソナに尋ねる。ペルソナが最初の質問で回答を保留すると中断し、再開の回答は台本の user から取る。"""
    answering = PersonaUser(persona)
    result = run(SCENARIOS / "needs_unclear_asks_again.yaml", tmp_path / "a", user=answering)
    assert result.problems == []
    assert answering.asked == [AFTER, REUSE]

    deferring = PersonaUser(persona, defer_first=True)
    result = run(SCENARIOS / "happy_path_user_suspend.yaml", tmp_path / "b", user=deferring)
    assert result.problems == []
    assert result.resumes == 1
    assert deferring.asked == list(QUESTIONS)


def test_committed_scenarios_match_the_generator() -> None:
    assert sorted(GENERATED) == [p.name for p in PATHS]
    for path in PATHS:
        assert path.read_text("utf-8") == GENERATED[path.name], path.name
