"""tests/stochastic.yaml の設計値から、分布テストの基準の根拠になる量を計算する。

- design_model: (ステージ, 訪問の区分) ごとのクラスの分布の、設計どおりの MarkovModel（ゲートは常に goal）
- simulate: 設計値とワークフロー定義の辺（戻り先と max）から、運用者が escalate に中止で答える実行を多数標本し、
  訪問ごとの評価の回数の期待値を見積もる。synthesize はステージごとの全訪問の合計しか出さないので、visit や
  from_visit で絞った基準の分母の期待値 E[n] はこちらで出す（adopting-gaps.md）。status と訪問の回数の平均は
  synthesize の厳密な値と一致するはずで、test_e2e.py が確かめる

確率的な偽の本体のクラスの分布は (ステージ, 訪問の区分) だけで決まる（release の carry の有無は訪問の区分と一致する）ので、
この標本は遷移規則を辿るだけでよい。
"""

import random
from collections import Counter
from dataclasses import dataclass
from typing import Any

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.e2e import MarkovModel
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


@dataclass(frozen=True)
class Simulated:
    """標本の数と、(ステージ, 訪問, クラス) ごとの評価の回数、最後の状態の回数、ステージごとの訪問の回数。"""

    samples: int
    evaluations: Counter[tuple[str, int, str]]
    status: Counter[str]
    visits: Counter[str]

    def per_run(self, stage: str, outcome: str | None = None, *, visit: int = 0) -> float:
        """一回の実行あたりの、条件に合う評価の回数の期待値。visit が負なら -visit 以降。"""
        total = sum(
            n
            for (s, v, o), n in self.evaluations.items()
            if s == stage
            and (outcome is None or o == outcome)
            and (visit == 0 or (v == visit if visit > 0 else v >= -visit))
        )
        return total / self.samples


def simulate(profile: str = "markov", samples: int = 200_000, seed: int = 0) -> Simulated:
    rng = random.Random(seed)
    dists = {
        (s, b): sorted(class_distribution(profile, s, b).items()) for s in ORDER for b in (1, 2)
    }
    evaluations: Counter[tuple[str, int, str]] = Counter()
    status: Counter[str] = Counter()
    visits: Counter[str] = Counter()
    for _ in range(samples):
        seen: Counter[str] = Counter()
        counts: Counter[tuple[str, str]] = Counter()
        stage = ORDER[0]
        while True:
            seen[stage] += 1
            visits[stage] += 1
            classes, weights = zip(*dists[(stage, min(seen[stage], 2))], strict=True)
            outcome = rng.choices(classes, weights=weights)[0]
            evaluations[(stage, seen[stage], outcome)] += 1
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
    return Simulated(samples, evaluations, status, visits)
