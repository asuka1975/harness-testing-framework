"""toy-minimal の確率的な偽ステージ本体と分布テスト（plan.md 第6節 F3）。

- 本体は種だけを乱数の源にする（同じ種で同じ結果）
- 変種の選び方の経験分布が、設計値（tests/stochastic.yaml）に近い
- 正しい expectations が通り、ずらした expectations の基準はすべて落ちる
"""

import math
from pathlib import Path

import pytest
from toy_minimal.stages.probabilistic import TABLE, choose_variant, run_set

from harness_testing_framework.testing.stages import (
    RunSet,
    evaluate_expectations,
    load_expectations,
)

EXPECTATIONS = Path(__file__).parent / "expectations"


def test_table_distributions_sum_to_one() -> None:
    def walk(node: object) -> list[dict[str, float]]:
        if isinstance(node, dict) and all(isinstance(v, int | float) for v in node.values()):
            return [node]
        return [d for v in (node.values() if isinstance(node, dict) else []) for d in walk(v)]

    for dist in walk(TABLE["profiles"]):
        assert math.isclose(sum(dist.values()), 1.0), dist


def test_choice_depends_only_on_the_seed() -> None:
    for seed in range(50):
        a = choose_variant("markov", "review_note", 1, seed, "")
        b = choose_variant("markov", "review_note", 1, seed, "")
        assert a == b


@pytest.mark.parametrize(
    ("profile", "stage", "visit", "note", "path"),
    [
        ("markov", "plan_outline", 1, "", ["plan_outline", "first"]),
        ("markov", "plan_outline", 2, "", ["plan_outline", "again"]),
        ("markov", "write_note", 1, "", ["write_note", "first"]),
        ("divergent", "review_note", 1, "抽象的な説明", ["review_note", "after_ok_b", "first"]),
        ("divergent", "review_note", 1, "具体的", ["review_note", "after_ok", "first"]),
    ],
)
def test_empirical_choice_matches_design(
    profile: str, stage: str, visit: int, note: str, path: list[str]
) -> None:
    design: object = TABLE["profiles"][profile]
    for key in path:
        assert isinstance(design, dict)
        design = design[key]
    assert isinstance(design, dict)
    n = 4000
    counts: dict[str, int] = {}
    for seed in range(n):
        variant = choose_variant(profile, stage, visit, seed * 7919 + 13, note)
        counts[variant] = counts.get(variant, 0) + 1
    for variant, p in design.items():
        se = math.sqrt(p * (1 - p) / n)
        assert abs(counts.get(variant, 0) / n - p) <= 4 * se + 1e-9, (variant, counts)


@pytest.fixture(scope="module")
def markov_runs(tmp_path_factory: pytest.TempPathFactory) -> RunSet:
    expectations = load_expectations(EXPECTATIONS / "markov.yaml")
    return run_set(expectations, tmp_path_factory.mktemp("markov"))


def test_correct_expectations_pass(markov_runs: RunSet) -> None:
    report = evaluate_expectations(load_expectations(EXPECTATIONS / "markov.yaml"), markov_runs)
    assert report.passed, report.lines()


def test_every_shifted_criterion_fails(markov_runs: RunSet) -> None:
    report = evaluate_expectations(
        load_expectations(EXPECTATIONS / "markov_shifted.yaml"), markov_runs
    )
    assert not any(r.passed for r in report.results), report.lines()


def test_every_variant_writes_every_memory_out_item() -> None:
    """memory_out の記憶は訪問のたびに書く（問題が無ければ空の一覧）。書かないと、持ち帰った前の値が
    状態文書に残り、問いが解けていても同じ end_state に分類されうる（adopting.md 第2.1節）。"""
    from toy_minimal.metrics import REGISTRY

    from harness_testing_framework.runtime import load_workflow

    workflow = load_workflow(Path(__file__).parents[1] / "workflow.yaml", REGISTRY.names())
    for stage in workflow.stages:
        for name, spec in TABLE["variants"][stage.id].items():
            assert set(spec.get("memory", {})) == set(stage.memory_out), (stage.id, name)
