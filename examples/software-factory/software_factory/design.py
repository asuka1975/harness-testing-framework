"""tests/stochastic.yaml の設計値から、分布テストの基準の根拠になる量を計算する。

- design_model: (ステージ, 訪問の区分) ごとのクラスの分布の、設計どおりの MarkovModel。ゲートの分布は、
  RandomGateClassifier に与えるもの（gates）をそのまま書き、無いフェーズは常に goal
- expected_count: その MarkovModel に synthesize をかけた予測から、一回の実行あたりの、条件（scope、visit か from_visit、
  結果）に合う評価の回数の期待値。基準の分母の期待値 E[n] と、その中の結果の割合の根拠。mean_visits の基準の幅は、
  同じ予測の visits_variance（一回の実行の中での訪問の回数の分散）から出す
"""

from collections.abc import Mapping, Sequence
from typing import Any

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.e2e import MarkovModel, Prediction
from harness_testing_framework.testing.stages import EntryDependenceResult, IndependenceResult
from software_factory.stages.deterministic import WORKFLOW
from software_factory.stages.probabilistic import TABLE

DOC: Any = load_workflow_document(WORKFLOW)
STAGES: list[dict[str, Any]] = [s for p in DOC["workflow"]["phases"] for s in p["stages"]]
ORDER = [s["id"] for s in STAGES]
PHASES = [p["id"] for p in DOC["workflow"]["phases"]]
KEYS = {1: "first", 2: "again"}
RELEASE_KEYS = {1: "without_carry", 2: "with_carry"}


def class_distribution(profile: str, stage: str, bucket: int) -> dict[str, float]:
    """(ステージ, 訪問の区分) のクラスの分布。変種 defect は、goal の実装の系統が一つの時だけ決まる。"""
    key = (RELEASE_KEYS if stage == "release" else KEYS)[bucket]
    variants: dict[str, Any] = TABLE["variants"][stage]
    goal_impls = [
        v
        for v in TABLE["profiles"][profile]["implement"]["first"]
        if TABLE["variants"]["implement"][v]["class"] == "goal"
    ]
    families = {TABLE["families"][v] for v in goal_impls}
    dist: dict[str, float] = {}
    for variant, p in TABLE["profiles"][profile][stage][key].items():
        spec = variants[variant]
        if "by_family" in spec:
            if len(families) != 1:
                raise ValueError(
                    f"{profile} の {stage} の {variant} のクラスは実装の変種で分かれる"
                )
            (family,) = families
            spec = spec["by_family"][family]
        dist[spec["class"]] = dist.get(spec["class"], 0.0) + float(p)
    return dist


def design_model(
    profile: str = "markov", gates: Mapping[str, Mapping[str, float]] | None = None
) -> MarkovModel:
    """gates はフェーズの id からゲートのクラスの分布（RandomGateClassifier に与えるもの）。無いフェーズは常に goal。"""
    stage = {(s, b): class_distribution(profile, s, b) for s in ORDER for b in (1, 2)}
    gate = {(p, b): dict((gates or {}).get(p, {"goal": 1.0})) for p in PHASES for b in (1, 2)}
    return MarkovModel(stage, gate, cap=2)


def expected_count(
    prediction: Prediction,
    target: str,
    outcome: str | None = None,
    *,
    scope: str = "stage",
    visit: int = 0,
    from_visit: int = 0,
) -> float:
    """一回の実行あたりの、target（scope が stage ならステージ、phase ならフェーズのゲート）の評価のうち、visit なら
    その訪問、from_visit ならその訪問以降のものの回数の期待値。outcome を与えると、そのうち結果が outcome のもの。
    ゲートの訪問はフェーズの最終ステージの訪問。訪問の区分は design_model の cap（2）で頭打ちにしてある。"""
    if (visit > 0) == (from_visit > 0):
        raise ValueError("visit か from_visit のどちらか一つを与える")

    def matches(kind: str, name: str, bucket: int) -> bool:
        window = bucket == visit if visit > 0 else bucket >= from_visit
        return kind == scope and name == target and window

    if outcome is None:
        return sum(n for (k, t, b), n in prediction.evaluations.items() if matches(k, t, b))
    return sum(
        n
        for (k, t, b, result), n in prediction.visit_outcomes.items()
        if result == outcome and matches(k, t, b)
    )


def family_wise_violations(
    results: Sequence[IndependenceResult | EntryDependenceResult],
) -> list[str]:
    """判定できた検定のうち、p 値が alpha 0.01 を検定の数で割った値を下回るもの（多重性を見込んだ判定）。"""
    determined = [r for r in results if r.p_value is not None]
    return [
        f"{r.state if isinstance(r, IndependenceResult) else r.stage} {r.visit} p={r.p_value}"
        for r in determined
        if r.p_value is not None and r.p_value < 0.01 / len(determined)
    ]
