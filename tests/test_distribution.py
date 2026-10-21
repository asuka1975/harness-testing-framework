"""分布テストのランナーの判定（plan.md 第6節 F3）。合成の実行の集まりで確かめる。"""

import math
from pathlib import Path

import pytest

from harness_testing_framework.testing.stages import (
    ExpectationsInvalid,
    RunRecord,
    RunSet,
    evaluate_expectations,
    load_expectations,
    wilson_interval,
)


def _run(outcomes: list[tuple[str, int, str]], status: str = "completed") -> RunRecord:
    events: list[dict[str, object]] = []
    for target, visit, outcome in outcomes:
        events.append(
            {
                "event": "evaluation",
                "scope": "stage",
                "stage": target,
                "phase": "p",
                "visit": visit,
                "outcome": outcome,
            }
        )
    events.append({"event": "run_end", "status": status})
    return RunRecord(seed=0, status=status, events=events, representatives={})


def _expectations(tmp_path: Path, criteria: str) -> Path:
    path = tmp_path / "e.yaml"
    path.write_text(
        "expectations: t\ndescription: d\nworkflow: w.yaml\nruns: 10\nseed: 0\ncriteria:\n"
        + criteria,
        encoding="utf-8",
    )
    return path


def test_wilson_interval_known_values() -> None:
    low, high = wilson_interval(8, 10, z=1.96)
    # z = 1.96 での Wilson の区間。手計算では
    # 中心 (8 + 1.9208) / 13.8416、幅 1.96 * sqrt(1.6 + 0.9604) / 13.8416
    center = (8 + 1.96**2 / 2) / (10 + 1.96**2)
    half = 1.96 * math.sqrt(8 * 2 / 10 + 1.96**2 / 4) / (10 + 1.96**2)
    assert math.isclose(low, center - half) and math.isclose(high, center + half)
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_outcome_rate_counts_matching_evaluations(tmp_path: Path) -> None:
    runs = RunSet(
        [
            _run([("a", 1, "x"), ("a", 2, "goal")]),
            _run([("a", 1, "goal")]),
            _run([("a", 1, "x"), ("a", 2, "x")], status="aborted"),
            _run([("b", 1, "x")]),
        ]
    )
    e = load_expectations(
        _expectations(
            tmp_path,
            "  - {kind: outcome_rate, target: a, visit: 1, outcome: x, min: 0.6, max: 0.7}\n"
            "  - {kind: outcome_rate, target: a, from_visit: 2, outcome: x, min: 0.5, max: 0.5}\n"
            "  - {kind: status_rate, status: completed, min: 0.75, max: 0.75}\n"
            "  - {kind: mean_visits, target: a, min: 1.25, max: 1.25}\n"
            "  - {kind: outcome_rate, target: c, visit: 1, outcome: x, min: 0, max: 1}\n",
        )
    )
    results = evaluate_expectations(e, runs).results
    assert [r.passed for r in results] == [True, True, True, True, False]
    assert (results[0].count, results[0].n) == (2, 3)
    assert results[4].n == 0 and "判定できない" in results[4].note


def test_band_edges_are_inclusive_and_outside_fails(tmp_path: Path) -> None:
    runs = RunSet([_run([("a", 1, "x")]), _run([("a", 1, "goal")])])
    inside = _expectations(
        tmp_path, "  - {kind: outcome_rate, target: a, visit: 1, outcome: x, min: 0.5, max: 0.5}\n"
    )
    assert evaluate_expectations(load_expectations(inside), runs).passed
    outside = _expectations(
        tmp_path, "  - {kind: outcome_rate, target: a, visit: 1, outcome: x, min: 0.51, max: 1}\n"
    )
    assert not evaluate_expectations(load_expectations(outside), runs).passed


def test_invalid_expectations_are_rejected(tmp_path: Path) -> None:
    bad = _expectations(
        tmp_path, "  - {kind: outcome_rate, target: a, outcome: x, min: 0.9, max: 0.1}\n"
    )
    with pytest.raises(ExpectationsInvalid):
        load_expectations(bad)
    worse = _expectations(tmp_path, "  - {kind: nonsense, min: 0, max: 1}\n")
    with pytest.raises(ExpectationsInvalid):
        load_expectations(worse)


def test_runs_can_be_scaled_by_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _expectations(tmp_path, "  - {kind: status_rate, status: completed, min: 0, max: 1}\n")
    monkeypatch.setenv("HTF_RUNS", "37")
    assert load_expectations(path).runs == 37
