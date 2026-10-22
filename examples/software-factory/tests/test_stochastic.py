"""software-factory の確率的な偽ステージ本体と分布テスト。

- 本体は種だけを乱数の源にする（同じ種で同じ実行）
- 変種の選び方の経験分布が、設計値（tests/stochastic.yaml）に近い
- release の分布は carry を受けたかで変わり、それは訪問の区分と一致する
- 本体は契約を守る（多数の実行で、契約違反、本体の例外、範囲外のファイルの警告が一度も無い）
- 本体は訪問のたびに memory_out のすべての記憶を書く（tests/stochastic.yaml のすべての変種と、すべてのシナリオの訪問）
- 分布テストに使う実行の集まりに、指標の測定の失敗が一度も無く、印が goal の評価ではいつも goal が選択肢にある
  （ツールの異常終了などで goal が選択肢から外れると、印の goal が黙って unknown になり、分布が狂う）
- 正しい expectations（ゲートがいつも goal の markov.yaml と、assurance のゲートを実行の種で揺らす markov_gated.yaml）が
  通り、ずらした expectations（markov_shifted.yaml、markov_gated_shifted.yaml）の基準はすべて落ちる
- 正しい expectations の各基準は、設計値を中に含み、幅が設計値の両側に標準誤差の 3 倍以上 5 倍以下ある（0 と 1 で切る側を
  除く）。外れる側の期待件数が 10 に届かない基準は、二項分布の裾の確率が 0.1% 以下。標準誤差の分母 E[n] と訪問の回数の
  分散は、設計値の MarkovModel の synthesize の evaluations と visits_variance から厳密に出す
"""

import math
from pathlib import Path
from typing import Any

import pytest
from software_factory.design import expected_count
from software_factory.stages.deterministic import SCENARIOS
from software_factory.stages.probabilistic import (
    TABLE,
    WORKFLOW_MODEL,
    choose_variant,
    run_set,
    runtime,
)

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.e2e import Prediction
from harness_testing_framework.testing.harness import load_scenario, marked_class
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
        lower, upper = c["min"] != 0.0, not (c["kind"] == "outcome_rate" and c["max"] == 1.0)
        assert not lower or 3 * se <= p - c["min"] <= 5 * se, (c, p, se)
        assert not upper or 3 * se <= c["max"] - p <= 5 * se, (c, p, se)
        if c["kind"] == "outcome_rate" and runs * n * min(p, 1 - p) < 10:
            # 二項分布が歪む基準: 正規近似ではなく、裾の確率で誤って落ちる確率を確かめる（adopting.md 第12節）
            assert _outside(round(runs * n), p, c["min"], c["max"]) <= 0.001, c
            checked.add("binomial")
        checked.add(c["kind"])
    assert {"outcome_rate", "status_rate", "mean_visits"} <= checked


def _outside(n: int, p: float, low: float, high: float) -> float:
    """二項分布 B(n, p) の割合 X/n が [low, high] の外に出る確率。"""
    return sum(
        math.comb(n, k) * p**k * (1 - p) ** (n - k)
        for k in range(n + 1)
        if not low <= k / n <= high
    )


@pytest.mark.parametrize("name", ["markov_gated_shifted.yaml"])
def test_every_shifted_gated_criterion_fails(
    name: str, gated_runs: tuple[RunSet, BlobStore]
) -> None:
    report = evaluate_expectations(load_expectations(EXPECTATIONS / name), gated_runs[0])
    assert not any(r.passed for r in report.results), report.lines()


def test_every_shifted_criterion_fails(markov: tuple[RunSet, BlobStore]) -> None:
    report = evaluate_expectations(
        load_expectations(EXPECTATIONS / "markov_shifted.yaml"), markov[0]
    )
    assert not any(r.passed for r in report.results), report.lines()


@pytest.mark.parametrize("name", ["markov", "gated"])
def test_bodies_keep_the_contract(
    name: str, markov_runs: tuple[RunSet, BlobStore], gated_runs: tuple[RunSet, BlobStore]
) -> None:
    """契約違反（宣言外のパスや記憶）、本体の例外、範囲外のファイルを捨てた警告が、どの実行にも無い。"""
    runs = (markov_runs if name == "markov" else gated_runs)[0]
    for run in runs.runs:
        for event in run.events:
            assert event["event"] != "warning", (run.seed, event)
            if event["event"] == "stage_end":
                assert event["error"] is None, (run.seed, event)


@pytest.mark.parametrize("name", ["markov", "gated"])
def test_metrics_never_fail_to_measure_and_goal_marks_keep_goal(
    name: str, markov_runs: tuple[RunSet, BlobStore], gated_runs: tuple[RunSet, BlobStore]
) -> None:
    """分布テストに使う実行の集まりで、指標の測定の失敗（ツールの異常終了を含む）が一度も無く、印が goal の評価
    （tests/stochastic.yaml の metrics_fail が空の変種）ではいつも goal が選択肢にある。"""
    runs, store = markov_runs if name == "markov" else gated_runs
    goal_marked = 0
    for run in runs.runs:
        for event in run.evaluations():
            metrics: Any = event["metrics"]
            errors = {k: v["error"] for k, v in metrics.items() if "error" in v}
            assert errors == {}, (run.seed, event["seq"], errors)
            classification: Any = event["classification"]
            if event["scope"] != "stage" or classification is None:
                continue
            state = store.get(str(classification["state"])).decode("utf-8")
            if marked_class(state) == "goal":
                goal_marked += 1
                assert "goal" in classification["options"], (run.seed, event["seq"], metrics)
    assert goal_marked > 1000


@pytest.mark.parametrize("name", ["markov", "gated"])
def test_bodies_write_memory_out_on_every_visit(
    name: str, markov_runs: tuple[RunSet, BlobStore], gated_runs: tuple[RunSet, BlobStore]
) -> None:
    """本体が訪問のたびに memory_out を書くことを、本体の振る舞いで確かめる。印が goal のステージの評価では、その訪問の
    終了時スナップショットの memory_out の記憶が、goal の変種の値（tests/stochastic.yaml の ok）と等しい。本体が書かなけれ
    ば、持ち帰った前の値や前の訪問の値が残り、違う値になる。"""
    runs, store = markov_runs if name == "markov" else gated_runs
    memory_out = {s.id: s.memory_out for s in WORKFLOW_MODEL.stages}
    checked = 0
    for run in runs.runs:
        ended: dict[str, str] = {}
        for event in run.events:
            if event["event"] == "stage_end":
                ended[str(event["stage"])] = str(event["snapshot"])
                continue
            classification: Any = event.get("classification")
            if event["event"] != "evaluation" or event["scope"] != "stage" or not classification:
                continue
            stage = str(event["stage"])
            if marked_class(store.get(str(classification["state"])).decode("utf-8")) != "goal":
                continue
            memory = store.get_snapshot(ended[stage]).memory
            expected = TABLE["variants"][stage]["ok"].get("memory", {})
            for item in memory_out[stage]:
                assert memory.get(item) == expected[item], (run.seed, stage, item, memory.get(item))
            checked += 1
    assert checked > 1000


def test_every_body_writes_every_memory_out_item() -> None:
    """memory_out の記憶は訪問のたびに書く（問題が無ければ空の一覧）。書かないと、持ち帰った前の値が状態文書に残り、
    問いが解けていても同じ end_state に分類されうる（adopting.md 第2.1節）。確率的な本体の変種と、シナリオの台本の
    すべての訪問（例外で終わるものを除く）を確かめる。"""
    memory_out = {s.id: set(s.memory_out) for s in WORKFLOW_MODEL.stages}
    for stage, variants in TABLE["variants"].items():
        for name, spec in variants.items():
            specs = spec["by_family"].values() if "by_family" in spec else [spec]
            for one in specs:
                assert set(one.get("memory", {})) == memory_out[stage], (stage, name)
    for path in sorted(SCENARIOS.glob("*.yaml")):
        for key, visit in load_scenario(path).visits.items():
            stage = key.split("#")[0]
            if "raise" not in visit:
                assert set(visit.get("memory", {})) == memory_out[stage], (path.name, key)


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
