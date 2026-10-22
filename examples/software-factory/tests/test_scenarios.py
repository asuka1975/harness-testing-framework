"""software-factory の遷移の決定論テスト。

- 遷移の六種をすべて通す（フェーズ境界越えは五通り）
- escalate の四つの選択が動く
- 指標は実在のツール（pytest、coverage、ruff、compileall）で測り、その値で選択肢から goal が外れることも確かめる
- 記録再生で同一のスナップショットが得られる
- シナリオの inputs は、確率的な実行と同じフィクスチャ（依頼と変更前のコードベース）である。シナリオはフィクスチャを
  `{from: パス}` で参照する
- コミットしたシナリオの YAML は、software_factory/scenarios.py が作るものと一致する
  （遷移の列を変えた時と、ok のフィクスチャのファイルを足し引きした時は `python -m software_factory.scenarios` で作り直す）
- 要求の取り込みのペルソナ（ユーザーシミュレータ）を、台本の user の代わりに束縛しても、シナリオの期待どおりに動く
"""

from pathlib import Path

import pytest
from software_factory.personas import CAP, FLOOR, PERSONAS, QUESTIONS, Persona, PersonaUser
from software_factory.scenarios import GENERATED
from software_factory.stages.deterministic import SCENARIOS, inputs, run

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
    """フェーズ境界を越える辺（design、implement、acceptance、review の各辺）と、運用者による越境を通す。"""
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
        ("acceptance", "implement"),
        ("review", "implement"),
        ("review", "design"),
        ("release", "implement"),
    }


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
    assert answering.asked == [CAP, FLOOR]

    deferring = PersonaUser(persona, defer_first=True)
    result = run(SCENARIOS / "happy_path_user_suspend.yaml", tmp_path / "b", user=deferring)
    assert result.problems == []
    assert result.resumes == 1
    assert deferring.asked == list(QUESTIONS)


def test_committed_scenarios_match_the_generator() -> None:
    assert sorted(GENERATED) == [p.name for p in PATHS]
    for path in PATHS:
        assert path.read_text("utf-8") == GENERATED[path.name], path.name
