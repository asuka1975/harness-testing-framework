"""契約適合テスト（contract/conformance/）を参照ランタイムで通す。

plan.md 第6節 F2 の完了条件の一部。

- 各シナリオの実行記録の要約、最後の状態、記憶、注記の数が期待どおり
- 実行記録の各出来事が contract/trace.schema.json に適合し、seq が通し番号
- スナップショットのマニフェストが contract/snapshot.schema.json に適合する
- シナリオ全体で遷移の六種（契約 3.5）をすべて通す
- 記録してから再生すると、外部を一度も呼ばずに同じスナップショットの列になる
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from harness_testing_framework.testing.harness import (
    TRANSITION_KINDS,
    ReplayOnly,
    load_scenario,
    run_scenario,
    transition_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "contract/conformance"
SCENARIOS = sorted((CONFORMANCE / "scenarios").glob("*.yaml"))
TRACE_SCHEMA = json.loads((ROOT / "contract/trace.schema.json").read_text(encoding="utf-8"))
SNAPSHOT_SCHEMA = json.loads((ROOT / "contract/snapshot.schema.json").read_text(encoding="utf-8"))
SCENARIO_SCHEMA = json.loads((CONFORMANCE / "scenario.schema.json").read_text(encoding="utf-8"))


def _ids(paths: list[Path]) -> list[str]:
    return [p.stem for p in paths]


def test_scenario_schema_conforms_to_metaschema() -> None:
    Draft202012Validator.check_schema(SCENARIO_SCHEMA)


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids(SCENARIOS))
def test_scenario_file_is_valid(path: Path) -> None:
    doc: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(SCENARIO_SCHEMA).iter_errors(doc))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids(SCENARIOS))
def test_reference_runtime_passes_scenario(path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(path)
    result = run_scenario(scenario, tmp_path)
    assert result.problems == []

    trace_validator = Draft202012Validator(TRACE_SCHEMA)
    for event in result.trace:
        errors = list(trace_validator.iter_errors(event))
        assert not errors, (event, [e.message for e in errors])
    assert [e["seq"] for e in result.trace] == list(range(len(result.trace)))

    snapshot_validator = Draft202012Validator(SNAPSHOT_SCHEMA)
    for snapshot in result.snapshots:
        assert not list(snapshot_validator.iter_errors(snapshot.manifest()))


def test_scenarios_cover_every_transition_kind(tmp_path: Path) -> None:
    covered: set[str] = set()
    for i, path in enumerate(SCENARIOS):
        result = run_scenario(load_scenario(path), tmp_path / str(i))
        covered |= transition_coverage(result.trace)
    assert covered == set(TRANSITION_KINDS)


@pytest.mark.parametrize(
    "name",
    [
        "resume_replays_answers",
        "phase_crossing_rollback",
        "max_exceeded_continue_as_goal",
        "operator_defers",
        "suspend_after_rollback",
    ],
)
def test_replay_reproduces_snapshots_without_external_calls(name: str, tmp_path: Path) -> None:
    scenario = load_scenario(CONFORMANCE / f"scenarios/{name}.yaml")
    recorded = run_scenario(scenario, tmp_path / "record", record=tmp_path / "rec.jsonl")
    replayed = run_scenario(scenario, tmp_path / "replay", replay=tmp_path / "rec.jsonl")
    assert [s.id for s in replayed.snapshots] == [s.id for s in recorded.snapshots]
    assert replayed.trace == recorded.trace
    assert replayed.problems == recorded.problems == []


def test_replay_with_missing_record_fails_loudly(tmp_path: Path) -> None:
    scenario = load_scenario(CONFORMANCE / "scenarios/rollback_with_carry.yaml")
    run_scenario(scenario, tmp_path / "record", record=tmp_path / "rec.jsonl")
    lines = (tmp_path / "rec.jsonl").read_text(encoding="utf-8").splitlines()
    (tmp_path / "short.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ReplayOnly.Missing):
        run_scenario(scenario, tmp_path / "replay", replay=tmp_path / "short.jsonl")
