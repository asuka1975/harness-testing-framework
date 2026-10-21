"""toy-minimal の決定論テスト（plan.md 第6節 F2 の完了条件）。

- toy-minimal で遷移の六種をすべて通す
- escalate の四つの選択肢が動く
- 記録再生で同一のスナップショットが得られる
"""

from pathlib import Path

import pytest
from toy_minimal.stages.deterministic import SCENARIOS, run

from harness_testing_framework.testing.harness import (
    TRANSITION_KINDS,
    load_scenario,
    transition_coverage,
)

PATHS = sorted(SCENARIOS.glob("*.yaml"))


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_scenario(path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(path)
    result = run(path, tmp_path)
    assert result.summary == scenario.expect.trace
    assert result.status == scenario.expect.status
    for name, value in (scenario.expect.memory or {}).items():
        assert result.final_snapshot.memory.get(name) == value, name
    if scenario.expect.annotations is not None:
        assert len(result.final_snapshot.annotations) == scenario.expect.annotations


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


@pytest.mark.parametrize("name", ["review_and_outline_rollbacks", "happy_with_user"])
def test_replay_gives_identical_snapshots(name: str, tmp_path: Path) -> None:
    path = SCENARIOS / f"{name}.yaml"
    recorded = run(path, tmp_path / "a", record=tmp_path / "rec.jsonl")
    replayed = run(path, tmp_path / "b", replay=tmp_path / "rec.jsonl")
    assert [s.id for s in replayed.snapshots] == [s.id for s in recorded.snapshots]
    assert replayed.final_snapshot.id == recorded.final_snapshot.id
