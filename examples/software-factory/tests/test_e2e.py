"""software-factory の E2E のカバレッジ計画とマルコフ合成。

- カバレッジ計画が全 (ステージ, クラス) を踏む。誘発（その状態を表す成果物を書かせる。実在の指標がその成果物を測る）と、
  注入（分類の結果だけを変える）の両方を使う
- 設計値の MarkovModel の厳密な予測（synthesize）と、設計値の標本（design.simulate。mean_visits の幅の根拠）が一致する
- 推定したモデルの予測と、設計値のモデルの予測が、別の種の実行の実測と一致する

markov の本体は、クラスの分布が (ステージ, 訪問) だけで決まるように作ってある（release は carry の有無で決まり、
それは訪問の区分と一致する）。予測と実測の一致は合成の仕組みの確認で、マルコフ性という方法そのものの検証ではない。
"""

from pathlib import Path
from typing import Any

import pytest
from software_factory.design import simulate
from software_factory.metrics import REGISTRY
from software_factory.personas import PERSONAS, QUESTIONS, PersonaUser
from software_factory.stages.deterministic import FIXTURES, WORKFLOW, inputs
from software_factory.stages.probabilistic import TABLE, WORKFLOW_MODEL, run_set

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.e2e import (
    Prediction,
    compare_prediction,
    coverage_targets,
    estimate_model,
    plan_coverage,
    run_coverage,
    synthesize,
)
from harness_testing_framework.testing.stages import RunSet, runs_from_environment


def _script(stage: str, variant: str, family: str = "rounds_total") -> dict[str, Any]:
    """変種の台本: そのフィクスチャを写し、変種の記憶を書く。"""
    spec = TABLE["variants"][stage][variant]
    if "by_family" in spec:
        spec = spec["by_family"][family]
        return {"fixture": f"{stage}/{spec['fixture']}", "memory": spec["memory"]}
    return {"fixture": f"{stage}/{variant}", "memory": spec.get("memory", {})}


# intake の goal の台本は、依頼者（ペルソナ）に決まった三つの質問を尋ねる
GOAL = {s.id: _script(s.id, "ok") for s in WORKFLOW_MODEL.stages}
GOAL["intake"] = {**GOAL["intake"], "ask": list(QUESTIONS)}
# (ステージ, クラス) → 誘発に使う変種。intake と review の unknown は誘発の手段を用意せず、注入で踏む
INDUCED = {
    ("analyze", "needs_unclear"): "unclear",
    ("analyze", "unknown"): "unknown",
    ("design", "requirements_gap"): "gap",
    ("design", "unknown"): "unknown",
    ("plan_tasks", "design_incomplete"): "incomplete",
    ("plan_tasks", "unknown"): "unknown",
    ("implement", "task_unclear"): "unclear",
    ("implement", "quality_violation"): "lint",
    ("implement", "unknown"): "unknown",
    ("unit_test", "impl_defect"): "defect",
    ("unit_test", "tests_insufficient"): "thin",
    ("unit_test", "unknown"): "unknown",
    ("acceptance", "requirement_misread"): "misread",
    ("acceptance", "requirement_unmet"): "unmet",
    ("acceptance", "unknown"): "unknown",
    ("review", "design_flaw"): "design_flaw",
    ("review", "changes_requested"): "changes",
    ("release", "notes_incomplete"): "incomplete",
    ("release", "unknown"): "unknown",
}
INDUCE = {target: _script(target[0], variant) for target, variant in INDUCED.items()}


def test_coverage_plan_reaches_every_stage_class(tmp_path: Path) -> None:
    """全 (ステージ, クラス) を踏む。intake の質問には、ペルソナのユーザーシミュレータが答える。"""
    files = {path: data.decode("utf-8") for path, data in inputs().items()}
    plan = plan_coverage(WORKFLOW_MODEL, WORKFLOW, goal=GOAL, induce=INDUCE, inputs=files)
    user = PersonaUser(PERSONAS[1])
    report = run_coverage(plan, tmp_path, registry=REGISTRY, fixtures=FIXTURES, user=user)
    assert report.missing == []
    assert set(report.covered) == set(coverage_targets(WORKFLOW_MODEL))
    assert {item.method for item in plan} == {"induce", "inject"}
    assert all(report.reached[item.target] for item in plan)
    assert set(user.asked) == set(QUESTIONS)
    assert len(user.asked) >= len(QUESTIONS) * len(plan)


def test_design_samples_match_exact_synthesis(design_prediction: Prediction) -> None:
    """design.simulate（mean_visits の基準の幅に使う、訪問の回数の標準偏差の根拠）の最後の状態と訪問の回数の平均が、
    synthesize の厳密な値と一致する。"""
    prediction = design_prediction
    sim = simulate("markov", 100_000, 1)
    for status, p in prediction.status.items():
        se = (p * (1 - p) / sim.samples) ** 0.5
        assert abs(sim.status[status] / sim.samples - p) <= 4 * se + 1e-9, status
    for stage, mean in prediction.mean_visits.items():
        assert abs(sim.visits[stage] / sim.samples - mean) <= 0.02, stage


RUNS = runs_from_environment(400)


@pytest.fixture
def measurement(markov_runs: tuple[RunSet, BlobStore]) -> RunSet:
    """実測は、分布テストと同じ実行の集まり（tests/conftest.py で共有）。推定には別の種の実行を使う。"""
    return markov_runs[0]


def test_estimated_prediction_matches_measurement(measurement: RunSet, tmp_path: Path) -> None:
    """推定したモデルの予測が、別の種の実行の実測と一致する（状態、訪問の回数、評価の結果ごとの回数）。"""
    estimation, _ = run_set("markov", RUNS, 40000, tmp_path)
    prediction = synthesize(estimate_model(estimation, cap=2), WORKFLOW_MODEL)
    comparisons = compare_prediction(prediction, measurement)
    assert {c.quantity.split(":")[0] for c in comparisons} == {"status", "visits", "outcome"}
    assert all(c.within for c in comparisons), [c.line() for c in comparisons if not c.within]


def test_design_prediction_matches_measurement(
    design_prediction: Prediction, measurement: RunSet
) -> None:
    """設計値から作ったモデルの厳密な予測と、実行の実測が一致する（推定の誤差を含まない比較）。"""
    comparisons = compare_prediction(design_prediction, measurement)
    assert all(c.within for c in comparisons), [c.line() for c in comparisons if not c.within]
