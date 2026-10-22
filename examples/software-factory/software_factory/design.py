"""tests/stochastic.yaml の設計値から、分布テストの基準の根拠になる量を計算する。

- design_model: (ステージ, 訪問の区分) ごとのクラスの分布の、設計どおりの MarkovModel（ゲートは常に goal）
- expected_count: その MarkovModel に synthesize をかけた予測から、一回の実行あたりの、条件（visit か from_visit、結果）に
  合うステージの評価の回数の期待値。基準の分母の期待値 E[n] と、その中の結果の割合の根拠
- simulate: 訪問の回数の、一回の実行の中での標準偏差を見積もる標本。synthesize は訪問の回数の期待値しか出さないので、
  mean_visits の基準の幅のためだけに、設計値とワークフロー定義の辺（戻り先と max）を辿って運用者が escalate に中止で
  答える実行を標本する（adopting-gaps.md）。標本の最後の状態と訪問の回数の平均が synthesize の厳密な値と一致することを
  test_e2e.py が確かめる

確率的な偽の本体のクラスの分布は (ステージ, 訪問の区分) だけで決まる（release の carry の有無は訪問の区分と一致する）ので、
この標本は遷移規則を辿るだけでよい。
"""

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Any

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.e2e import MarkovModel, Prediction
from software_factory.stages.deterministic import WORKFLOW
from software_factory.stages.probabilistic import TABLE

DOC: Any = load_workflow_document(WORKFLOW)
STAGES: list[dict[str, Any]] = [s for p in DOC["workflow"]["phases"] for s in p["stages"]]
ORDER = [s["id"] for s in STAGES]
PHASES = [p["id"] for p in DOC["workflow"]["phases"]]
EDGES = {(s["id"], rb["state"]): (rb["stage"], rb["max"]) for s in STAGES for rb in s["rollback"]}
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


def design_model(profile: str = "markov") -> MarkovModel:
    stage = {(s, b): class_distribution(profile, s, b) for s in ORDER for b in (1, 2)}
    gate = {(p, b): {"goal": 1.0} for p in PHASES for b in (1, 2)}
    return MarkovModel(stage, gate, cap=2)


def expected_count(
    prediction: Prediction,
    stage: str,
    outcome: str | None = None,
    *,
    visit: int = 0,
    from_visit: int = 0,
) -> float:
    """一回の実行あたりの、ステージ stage の評価（visit ならその訪問、from_visit ならその訪問以降）の回数の期待値。
    outcome を与えると、そのうち結果が outcome のもの。訪問の区分は design_model の cap（2）で頭打ちにしてある。"""
    if (visit > 0) == (from_visit > 0):
        raise ValueError("visit か from_visit のどちらか一つを与える")

    def matches(bucket: int) -> bool:
        return bucket == visit if visit > 0 else bucket >= from_visit

    if outcome is None:
        return sum(
            n
            for (scope, target, bucket), n in prediction.evaluations.items()
            if scope == "stage" and target == stage and matches(bucket)
        )
    return sum(
        n
        for (scope, target, bucket, result), n in prediction.visit_outcomes.items()
        if scope == "stage" and target == stage and result == outcome and matches(bucket)
    )


@dataclass(frozen=True)
class Simulated:
    """標本の数と、最後の状態の回数、ステージごとの訪問の回数の和と二乗の和。"""

    samples: int
    status: Counter[str]
    visits: Counter[str]
    squares: Counter[str]

    def visit_sd(self, stage: str) -> float:
        """一回の実行の中での、ステージの訪問の回数の標準偏差。"""
        mean = self.visits[stage] / self.samples
        return math.sqrt(self.squares[stage] / self.samples - mean * mean)


def simulate(profile: str = "markov", samples: int = 200_000, seed: int = 0) -> Simulated:
    rng = random.Random(seed)
    dists = {
        (s, b): sorted(class_distribution(profile, s, b).items()) for s in ORDER for b in (1, 2)
    }
    status: Counter[str] = Counter()
    visits: Counter[str] = Counter()
    squares: Counter[str] = Counter()
    for _ in range(samples):
        seen: Counter[str] = Counter()
        counts: Counter[tuple[str, str]] = Counter()
        stage = ORDER[0]
        while True:
            seen[stage] += 1
            classes, weights = zip(*dists[(stage, min(seen[stage], 2))], strict=True)
            outcome = rng.choices(classes, weights=weights)[0]
            if outcome == "goal":
                i = ORDER.index(stage) + 1
                if i == len(ORDER):
                    status["completed"] += 1
                    break
                stage = ORDER[i]
                continue
            edge = EDGES.get((stage, outcome))
            if edge is None or counts[(stage, outcome)] >= edge[1]:
                status["aborted"] += 1
                break
            counts[(stage, outcome)] += 1
            stage = edge[0]
        for name, n in seen.items():
            visits[name] += n
            squares[name] += n * n
    return Simulated(samples, status, visits, squares)
