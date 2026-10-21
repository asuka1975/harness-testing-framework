"""遷移行列の推定と独立性検証（plan.md 第2節「組み合わせテストはしない」、第6節 F3）。合成の実行で確かめる。"""

from typing import Any

import pytest

from harness_testing_framework.testing.stages import (
    RunRecord,
    RunSet,
    chi_square,
    independence,
    transition_matrix,
    transitions,
)


def _run(steps: list[tuple[str, str, str | None]], status: str = "completed") -> RunRecord:
    """steps: (ステージ, 結果, 代表)。順に評価が起き、最後に run_end。"""
    events: list[dict[str, Any]] = []
    reps: dict[int, str] = {}
    for i, (stage, outcome, rep) in enumerate(steps):
        events.append(
            {
                "seq": i,
                "event": "evaluation",
                "scope": "stage",
                "stage": stage,
                "phase": "p",
                "visit": 1,
                "outcome": outcome,
            }
        )
        if rep is not None:
            reps[i] = rep
    events.append({"seq": len(steps), "event": "run_end", "status": status})
    return RunRecord(seed=0, status=status, events=events, representatives=reps)


def test_transitions_follow_the_next_evaluation_or_the_end() -> None:
    runs = RunSet([_run([("a", "goal", "r1"), ("b", "x", "q"), ("a", "goal", "r2")], "aborted")])
    got = [(t.state, t.representative, t.next) for t in transitions(runs)]
    assert got == [
        ("stage:a=goal", "r1", "stage:b=x"),
        ("stage:b=x", "q", "stage:a=goal"),
        ("stage:a=goal", "r2", "end:aborted"),
    ]


def test_transition_matrix_counts_and_probabilities() -> None:
    runs = RunSet(
        [_run([("a", "goal", None), ("b", "goal", None)])] * 3
        + [_run([("a", "goal", None), ("b", "x", None)])]
    )
    matrix = transition_matrix(runs)
    assert matrix["stage:a=goal"] == {"stage:b=goal": 0.75, "stage:b=x": 0.25}
    assert matrix["stage:b=goal"] == {"end:completed": 1.0}


def test_chi_square_known_value() -> None:
    # 2×2 の表 [[10, 20], [30, 40]]。期待度数 [[12, 18], [28, 42]] から手で計算した値
    expected = 4 / 12 + 4 / 18 + 4 / 28 + 4 / 42
    assert chi_square([[10, 20], [30, 40]]) == pytest.approx(expected)


def _two_groups(counts_a: dict[str, int], counts_b: dict[str, int]) -> RunSet:
    runs = []
    for rep, counts in (("A", counts_a), ("B", counts_b)):
        for nxt, n in counts.items():
            runs += [_run([("a", "goal", rep), ("b", nxt, None)])] * n
    return RunSet(runs)


def test_independent_when_downstream_distributions_agree() -> None:
    runs = _two_groups({"goal": 40, "x": 10}, {"goal": 40, "x": 10})
    [result] = [r for r in independence(runs) if r.state == "stage:a=goal"]
    assert result.verdict == "independent"
    assert result.p_value is not None and result.p_value > 0.5
    assert result.groups == {"A": 50, "B": 50}


def test_violated_when_downstream_distributions_differ() -> None:
    runs = _two_groups({"goal": 45, "x": 5}, {"goal": 20, "x": 30})
    [result] = [r for r in independence(runs) if r.state == "stage:a=goal"]
    assert result.verdict == "violated"
    assert result.p_value is not None and result.p_value < 0.01


def test_undetermined_with_one_representative_or_small_groups() -> None:
    one = RunSet([_run([("a", "goal", "A"), ("b", "goal", None)])] * 30)
    assert [r.verdict for r in independence(one) if r.state == "stage:a=goal"] == ["undetermined"]
    small = _two_groups({"goal": 5}, {"x": 5})
    [result] = [r for r in independence(small, min_group=10) if r.state == "stage:a=goal"]
    assert result.verdict == "undetermined"
    assert "代表" in result.note


def test_permutation_p_value_is_deterministic() -> None:
    runs = _two_groups({"goal": 30, "x": 20}, {"goal": 22, "x": 28})
    first = [r.p_value for r in independence(runs, seed=3)]
    assert first == [r.p_value for r in independence(runs, seed=3)]
