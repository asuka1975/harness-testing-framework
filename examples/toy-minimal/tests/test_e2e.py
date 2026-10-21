"""toy-minimal の E2E（plan.md 第6節 F3 の完了条件）。

- E2E のカバレッジ計画が、全 (stage, end_state) を踏む（誘発と注入の両方を使う）
- マルコフ合成の予測が実測と一致する

markov の本体は、クラスの分布が (ステージ, 訪問) だけで決まるように作ってある。予測と実測の一致は
合成の仕組みが正しく計算していることの確認で、マルコフ性という方法そのものの検証ではない（plan.md 第1節）。
"""

from pathlib import Path
from typing import Any

from toy_minimal.metrics import REGISTRY
from toy_minimal.stages.probabilistic import INPUTS, ROOT, runtime

from harness_testing_framework.testing.e2e import (
    compare_prediction,
    coverage_targets,
    estimate_model,
    plan_coverage,
    run_coverage,
    synthesize,
)
from harness_testing_framework.testing.stages import record_run, run_many

FIXTURES = ROOT / "tests" / "fixtures"
GOAL = {
    stage: {"fixture": f"{stage}/ok"}
    for stage in ("ask_topic", "plan_outline", "write_note", "review_note")
}
INDUCE: dict[tuple[str, str], dict[str, Any]] = {
    ("plan_outline", "topic_unclear"): {
        "fixture": "plan_outline/unclear",
        "memory": {"topic_questions": ["読者は"]},
    },
    ("plan_outline", "unknown"): {"fixture": "plan_outline/unknown"},
    ("write_note", "outline_unfit"): {
        "fixture": "write_note/gaps",
        "memory": {"outline_gaps": ["例"]},
    },
    ("write_note", "unknown"): {"fixture": "write_note/unknown"},
    ("review_note", "findings_blocking"): {
        "fixture": "review_note/blocking",
        "memory": {"review_findings": ["例"]},
    },
    ("review_note", "unknown"): {"fixture": "review_note/unknown"},
    # ask_topic の unknown は誘発の手段を用意せず、注入で踏む
}


def test_coverage_plan_reaches_every_stage_class(tmp_path: Path) -> None:
    workflow = runtime("markov", tmp_path / "w").workflow
    plan = plan_coverage(
        workflow, ROOT / "workflow.yaml", goal=GOAL, induce=INDUCE, inputs={"brief.txt": "依頼"}
    )
    report = run_coverage(plan, tmp_path, registry=REGISTRY, fixtures=FIXTURES)
    assert report.missing == []
    assert set(report.covered) == set(coverage_targets(workflow))
    methods = {item.method for item in plan}
    assert methods == {"induce", "inject"}
    assert all(report.reached[item.target] for item in plan)


def test_markov_prediction_matches_measurement(tmp_path: Path) -> None:
    built = runtime("markov", tmp_path / "a")
    estimation = run_many(400, 30000, lambda seed: record_run(built, seed, INPUTS))
    prediction = synthesize(estimate_model(estimation, cap=2), built.workflow)
    other = runtime("markov", tmp_path / "b")
    measurement = run_many(400, 40000, lambda seed: record_run(other, seed, INPUTS))
    comparisons = compare_prediction(prediction, measurement)
    checked = [c for c in comparisons if c.quantity.startswith(("status:", "visits:"))]
    assert checked
    assert all(c.within for c in checked), [c.line() for c in checked if not c.within]
