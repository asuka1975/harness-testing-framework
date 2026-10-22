"""software-factory の確率的な偽ステージ本体と分布テスト。

- 本体は種だけを乱数の源にする（同じ種で同じ実行）
- 変種の選び方の経験分布が、設計値（tests/stochastic.yaml）に近い
- release の分布は carry を受けたかで変わり、それは訪問の区分と一致する
- 本体は契約を守る（多数の実行で、契約違反、本体の例外、範囲外のファイルの警告が一度も無い）
- 正しい expectations（ゲートがいつも goal の markov.yaml と、assurance のゲートを実行の種で揺らす markov_gated.yaml）が
  通り、ずらした expectations の基準はすべて落ちる
- 正しい expectations の各基準は、設計値を中に含み、幅が設計値の両側に標準誤差の 3 倍以上ある（0 と 1 で切る側を除く）。
  標準誤差の分母 E[n] と訪問の回数の分散は、設計値の MarkovModel の synthesize の evaluations と visits_variance から
  厳密に出す
"""

import math
from pathlib import Path

import pytest
from software_factory.design import expected_count
from software_factory.stages.probabilistic import TABLE, choose_variant, run_set, runtime

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.e2e import Prediction
from harness_testing_framework.testing.stages import (
    RunSet,
    evaluate_expectations,
    load_expectations,
)

EXPECTATIONS = Path(__file__).parent / "expectations"


def test_table_distributions_sum_to_one() -> None:
    for profile in TABLE["profiles"].values():
        for stage, keys in profile.items():
            for key, dist in keys.items():
                assert math.isclose(sum(dist.values()), 1.0), (stage, key, dist)
                assert set(dist) <= set(TABLE["variants"][stage]), (stage, key)


def test_choice_depends_only_on_the_seed() -> None:
    for seed in range(50):
        a = choose_variant("markov", "implement", "first", seed)
        assert a == choose_variant("markov", "implement", "first", seed)


@pytest.mark.parametrize(
    ("profile", "stage", "key"),
    [
        ("markov", "analyze", "first"),
        ("markov", "implement", "first"),
        ("markov", "implement", "again"),
        ("divergent", "implement", "first"),
        ("markov", "unit_test", "first"),
        ("markov", "release", "without_carry"),
        ("markov", "release", "with_carry"),
    ],
)
def test_empirical_choice_matches_design(profile: str, stage: str, key: str) -> None:
    design: dict[str, float] = TABLE["profiles"][profile][stage][key]
    n = 4000
    counts: dict[str, int] = {}
    for seed in range(n):
        variant = choose_variant(profile, stage, key, seed * 7919 + 13)
        counts[variant] = counts.get(variant, 0) + 1
    for variant, p in design.items():
        se = math.sqrt(p * (1 - p) / n)
        assert abs(counts.get(variant, 0) / n - p) <= 4 * se + 1e-9, (variant, counts)


@pytest.fixture
def markov(markov_runs: tuple[RunSet, BlobStore]) -> tuple[RunSet, BlobStore]:
    """expectations/markov.yaml の回数と種での実行（tests/conftest.py で共有）。"""
    return markov_runs


def test_correct_expectations_pass(markov: tuple[RunSet, BlobStore]) -> None:
    report = evaluate_expectations(load_expectations(EXPECTATIONS / "markov.yaml"), markov[0])
    assert report.passed, report.lines()


def test_gated_expectations_pass(gated_runs: tuple[RunSet, BlobStore]) -> None:
    report = evaluate_expectations(
        load_expectations(EXPECTATIONS / "markov_gated.yaml"), gated_runs[0]
    )
    assert report.passed, report.lines()


@pytest.mark.parametrize("name", ["markov.yaml", "markov_gated.yaml"])
def test_correct_expectations_follow_the_design(
    name: str, design_prediction: Prediction, gated_prediction: Prediction
) -> None:
    expectations = load_expectations(EXPECTATIONS / name)
    prediction = gated_prediction if "gates" in expectations.bindings else design_prediction
    runs = expectations.runs
    checked: set[str] = set()
    for c in expectations.criteria:
        if c["kind"] == "outcome_rate":
            window = {
                "scope": c.get("scope", "stage"),
                "visit": c.get("visit", 0),
                "from_visit": c.get("from_visit", 0),
            }
            n = expected_count(prediction, c["target"], **window)
            p = expected_count(prediction, c["target"], c["outcome"], **window) / n
            se = math.sqrt(p * (1 - p) / (runs * n))
        elif c["kind"] == "status_rate":
            p = prediction.status[c["status"]]
            se = math.sqrt(p * (1 - p) / runs)
        else:
            p = prediction.mean_visits[c["target"]]
            se = math.sqrt(prediction.visits_variance[c["target"]] / runs)
        assert c["min"] <= p <= c["max"], c
        assert c["min"] == 0.0 or p - c["min"] >= 3 * se, (c, p, se)
        assert (c["kind"] == "outcome_rate" and c["max"] == 1.0) or c["max"] - p >= 3 * se, c
        checked.add(c["kind"])
    assert checked == {"outcome_rate", "status_rate", "mean_visits"}


def test_every_shifted_criterion_fails(markov: tuple[RunSet, BlobStore]) -> None:
    report = evaluate_expectations(
        load_expectations(EXPECTATIONS / "markov_shifted.yaml"), markov[0]
    )
    assert not any(r.passed for r in report.results), report.lines()


def test_bodies_keep_the_contract(markov: tuple[RunSet, BlobStore]) -> None:
    """契約違反（宣言外のパスや記憶）、本体の例外、範囲外のファイルを捨てた警告が、どの実行にも無い。"""
    for run in markov[0].runs:
        for event in run.events:
            assert event["event"] != "warning", (run.seed, event)
            if event["event"] == "stage_end":
                assert event["error"] is None, (run.seed, event)


def test_release_distribution_follows_the_carry(
    markov: tuple[RunSet, BlobStore], tmp_path: Path
) -> None:
    """release の訪問 1 は carry を持たず、訪問 2 以降はいつも空でない missing_notes を持って始まる。"""
    reader = runtime("markov", tmp_path, store=markov[1])
    seen = {1: 0, 2: 0}
    for run in markov[0].runs:
        for event in run.events:
            if event["event"] == "stage_start" and event["stage"] == "release":
                carried = reader.snapshot(str(event["snapshot"])).memory.get("missing_notes")
                visit = int(str(event["visit"]))
                seen[min(visit, 2)] += 1
                assert bool(carried) == (visit >= 2), (run.seed, visit, carried)
    assert seen[1] >= 100 and seen[2] >= 30, seen


def test_same_seed_gives_the_same_run(tmp_path: Path) -> None:
    a, _ = run_set("divergent", 5, 123, tmp_path / "a")
    b, _ = run_set("divergent", 5, 123, tmp_path / "b")
    assert [r.events for r in a.runs] == [r.events for r in b.runs]
