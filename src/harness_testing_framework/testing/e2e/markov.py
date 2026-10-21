"""マルコフ合成。

各ステージのクラスの分布が (ステージ, 訪問の番号) だけで決まると仮定したモデルから、ワークフローの遷移規則
（next、rollback と max、フェーズゲート、unknown）をたどって、実行全体の分布を厳密に計算する。訪問の番号は
cap 以上を一つにまとめる。escalate の後は方針に従う（いまは中止だけ）。

予測と実測の一致は、モデルの仮定が成り立つ本体に対して、合成の計算が正しいことの確認になる。仮定そのもの
（マルコフ性）が実際のハーネスで成り立つかは、実 LLM を伴う方法の検証の問題（plan.md 第1節）。
"""

import math
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cache

from harness_testing_framework.runtime.model import Workflow
from harness_testing_framework.testing.stages.runs import RunSet

type Dist = Mapping[str, float]


class ModelIncomplete(ValueError):
    """モデルに、到達しうる (ステージ, 訪問) の分布が無い。"""


@dataclass(frozen=True)
class MarkovModel:
    stage: Mapping[tuple[str, int], Dist]
    gate: Mapping[tuple[str, int], Dist]
    cap: int

    def _lookup(self, table: Mapping[tuple[str, int], Dist], key: str, visit: int) -> Dist:
        for bucket in range(min(visit, self.cap), 0, -1):
            if (key, bucket) in table:
                return table[(key, bucket)]
        raise ModelIncomplete(f"{key} の訪問 {visit} の分布が無い")

    def stage_distribution(self, stage: str, visit: int) -> Dist:
        return self._lookup(self.stage, stage, visit)

    def gate_distribution(self, phase: str, visit: int) -> Dist:
        return self._lookup(self.gate, phase, visit)


def estimate_model(runs: RunSet, cap: int = 2) -> MarkovModel:
    """実行記録の評価から、(ステージ, 訪問の区分) ごとのクラスの経験分布を推定する。"""
    counts: dict[tuple[str, str, int], Counter[str]] = defaultdict(Counter)
    for run in runs.runs:
        for e in run.evaluations():
            target = str(e["stage"] if e["scope"] == "stage" else e["phase"])
            counts[(str(e["scope"]), target, min(int(e["visit"]), cap))][str(e["outcome"])] += 1
    stage: dict[tuple[str, int], dict[str, float]] = {}
    gate: dict[tuple[str, int], dict[str, float]] = {}
    for (scope, target, bucket), counter in counts.items():
        total = sum(counter.values())
        dist = {k: v / total for k, v in sorted(counter.items())}
        (stage if scope == "stage" else gate)[(target, bucket)] = dist
    return MarkovModel(stage, gate, cap)


@dataclass(frozen=True)
class Prediction:
    status: dict[str, float]
    mean_visits: dict[str, float]
    outcomes: dict[tuple[str, str], float] = field(default_factory=dict)


@dataclass(frozen=True)
class _Sum:
    status: tuple[tuple[str, float], ...]
    visits: tuple[float, ...]
    outcomes: tuple[tuple[tuple[str, str], float], ...]


def synthesize(model: MarkovModel, workflow: Workflow, policy: str = "abort") -> Prediction:
    """モデルとワークフローから、最後の状態の分布、ステージごとの訪問の回数の期待値、
    ステージの評価の結果ごとの回数の期待値を計算する。"""
    if policy != "abort":
        raise ValueError(f"escalate の後の方針 {policy} は扱えない（中止だけ）")
    stages = [s.id for s in workflow.stages]
    edges = [(s.id, rb.state) for s in workflow.stages for rb in s.rollbacks.values()]

    def add(into: dict[str, float], key: str, value: float) -> None:
        into[key] = into.get(key, 0.0) + value

    def combine(parts: list[tuple[float, _Sum]]) -> _Sum:
        status: dict[str, float] = {}
        visits = [0.0] * len(stages)
        outcomes: dict[tuple[str, str], float] = {}
        for p, part in parts:
            for k, v in part.status:
                add(status, k, p * v)
            for i, v in enumerate(part.visits):
                visits[i] += p * v
            for k2, v in part.outcomes:
                outcomes[k2] = outcomes.get(k2, 0.0) + p * v
        return _Sum(tuple(sorted(status.items())), tuple(visits), tuple(sorted(outcomes.items())))

    def terminal(status: str) -> _Sum:
        return _Sum(((status, 1.0),), tuple([0.0] * len(stages)), ())

    @cache
    def enter(stage_id: str, visits: tuple[int, ...], counts: tuple[int, ...]) -> _Sum:
        position = stages.index(stage_id)
        visit = visits[position] + 1
        now = (*visits[:position], visit, *visits[position + 1 :])
        parts = []
        for outcome, p in model.stage_distribution(stage_id, visit).items():
            after = settle(stage_id, outcome, now, counts, "stage", visit)
            here = _Sum(
                (),
                tuple(1.0 if i == position else 0.0 for i in range(len(stages))),
                (((stage_id, outcome), 1.0),),
            )
            parts.append((p, combine([(1.0, after), (1.0, here)])))
        return combine(parts)

    def settle(
        stage_id: str,
        outcome: str,
        visits: tuple[int, ...],
        counts: tuple[int, ...],
        origin: str,
        visit: int,
    ) -> _Sum:
        stage = workflow.stage(stage_id)
        if outcome == "goal":
            if origin == "stage" and workflow.is_last_in_phase(stage_id):
                gate = model.gate_distribution(stage.phase, visit)
                return combine(
                    [
                        (q, settle(stage_id, g, visits, counts, "gate", visit))
                        for g, q in gate.items()
                    ]
                )
            following = workflow.next_stage(stage_id)
            return (
                terminal("completed") if following is None else enter(following.id, visits, counts)
            )
        if outcome == "unknown":
            return terminal("aborted")
        rollback = stage.rollbacks[outcome]
        index = edges.index((stage_id, outcome))
        if counts[index] >= rollback.max:
            return terminal("aborted")
        more = (*counts[:index], counts[index] + 1, *counts[index + 1 :])
        return enter(rollback.target, visits, more)

    total = enter(stages[0], tuple([0] * len(stages)), tuple([0] * len(edges)))
    status = dict(total.status)
    for s in ("completed", "aborted"):
        status.setdefault(s, 0.0)
    return Prediction(status, dict(zip(stages, total.visits, strict=True)), dict(total.outcomes))


@dataclass(frozen=True)
class Comparison:
    quantity: str
    predicted: float
    measured: float
    se: float
    within: bool

    def line(self) -> str:
        mark = "一致" if self.within else "不一致"
        return f"{mark} {self.quantity}: 予測 {self.predicted:.4f}、実測 {self.measured:.4f}（標準誤差 {self.se:.4f}）"


def _compare(
    quantity: str, predicted: float, values: list[float], k: float, binomial: bool
) -> Comparison:
    n = len(values)
    measured = sum(values) / n
    if binomial:
        se = math.sqrt(predicted * (1 - predicted) / n)
    else:
        sd = math.sqrt(sum((v - measured) ** 2 for v in values) / max(1, n - 1))
        se = sd / math.sqrt(n)
    within = abs(measured - predicted) <= k * se + 1e-9
    return Comparison(quantity, predicted, measured, se, within)


def compare_prediction(prediction: Prediction, runs: RunSet, k: float = 4.0) -> list[Comparison]:
    """予測と実測を比べる。差が標準誤差の k 倍以内なら一致とする。"""
    out: list[Comparison] = []
    for status, p in sorted(prediction.status.items()):
        values = [1.0 if r.status == status else 0.0 for r in runs.runs]
        out.append(_compare(f"status:{status}", p, values, k, binomial=True))
    for stage, mean in prediction.mean_visits.items():
        values = [float(r.visits(stage)) for r in runs.runs]
        out.append(_compare(f"visits:{stage}", mean, values, k, binomial=False))
    for (stage, outcome), mean in sorted(prediction.outcomes.items()):
        values = [
            float(
                sum(
                    1
                    for e in r.evaluations()
                    if e["scope"] == "stage" and e["stage"] == stage and e["outcome"] == outcome
                )
            )
            for r in runs.runs
        ]
        out.append(_compare(f"outcome:{stage}={outcome}", mean, values, k, binomial=False))
    return out
