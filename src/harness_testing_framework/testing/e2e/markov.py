"""マルコフ合成。

各ステージのクラスの分布が (ステージ, 訪問の番号) だけで決まると仮定したモデルから、ワークフローの遷移規則
（next、rollback と max、フェーズゲート、unknown）をたどって、実行全体の分布を厳密に計算する。訪問の番号は
cap 以上を一つにまとめる。escalate の後は方針に従う（いまは中止だけ）。

予測と実測の一致は、モデルの仮定が成り立つ本体に対して、合成の計算が正しいことの確認になる。仮定そのもの
（マルコフ性）が実際のハーネスで成り立つかは、実 LLM を伴う方法の検証の問題で、偽の本体では確かめられない。
"""

import math
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field

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
    """合成の結果。

    - status: 最後の状態（completed / aborted）の確率
    - mean_visits: ステージごとの訪問の回数の期待値
    - outcomes: (ステージ, 結果) ごとのステージの評価の回数の期待値
    - evaluations: (scope, 対象, 訪問の区分) ごとの評価の回数の期待値。scope は stage か phase（ゲート）で、
      区分は min(訪問の番号, cap)。ゲートの訪問はフェーズの最終ステージの訪問の番号。visit や from_visit で
      絞った分布テストの基準の分母の期待値 E[n] になる（区分が cap より小さい訪問は、その訪問ちょうど）
    - visit_outcomes: (scope, 対象, 訪問の区分, 結果) ごとの評価の回数の期待値
    - visits_variance: ステージごとの、一回の実行の中での訪問の回数の分散。mean_visits の基準の幅は、
      N 回の実行なら標準誤差 sqrt(visits_variance / N) から出せる
    """

    status: dict[str, float]
    mean_visits: dict[str, float]
    outcomes: dict[tuple[str, str], float] = field(default_factory=dict)
    evaluations: dict[tuple[str, str, int], float] = field(default_factory=dict)
    visit_outcomes: dict[tuple[str, str, int, str], float] = field(default_factory=dict)
    visits_variance: dict[str, float] = field(default_factory=dict)


type _Node = tuple[int, tuple[int, ...], tuple[int, ...]]


def synthesize(model: MarkovModel, workflow: Workflow, policy: str = "abort") -> Prediction:
    """モデルとワークフローから、最後の状態の分布と、訪問と評価の回数の期待値、訪問の回数の分散を
    厳密に計算する（Prediction）。

    状態（いまのステージ、ステージごとの訪問の番号、辺ごとの戻りの回数）の確率を、遷移規則に沿って前へ
    流す。戻りのたびに回数の和が増え、戻りが無ければステージの位置が進むので、状態は (回数の和, 位置) の
    順に一度ずつ処理すれば足りる。訪問の番号は cap で頭打ちにして持つ（分布は min(訪問, cap) だけで決まる）。
    訪問の回数の二次の積率は、同じ状態を逆の順にたどって求める。
    """
    if policy != "abort":
        raise ValueError(f"escalate の後の方針 {policy} は扱えない（中止だけ）")
    stages = [s.id for s in workflow.stages]
    edges = [(s.id, rb.state) for s in workflow.stages for rb in s.rollbacks.values()]
    status = {"completed": 0.0, "aborted": 0.0}
    visits_mean = dict.fromkeys(stages, 0.0)
    visit_outcomes: dict[tuple[str, str, int, str], float] = defaultdict(float)
    # (回数の和, 位置) → {(訪問の番号の組, 戻りの回数の組): 確率}
    pending: dict[tuple[int, int], dict[tuple[tuple[int, ...], tuple[int, ...]], float]] = (
        defaultdict(lambda: defaultdict(float))
    )
    # 処理した状態の順と、各状態からの分かれ（条件つきの確率と、次の状態か最後の状態）
    order: list[_Node] = []
    branches: dict[_Node, list[tuple[float, _Node | str]]] = {}

    def following(stage_id: str, visits: tuple[int, ...], counts: tuple[int, ...]) -> _Node | str:
        after = workflow.next_stage(stage_id)
        return "completed" if after is None else (stages.index(after.id), visits, counts)

    def returning(
        stage_id: str, outcome: str, visits: tuple[int, ...], counts: tuple[int, ...]
    ) -> _Node | str:
        if outcome == "unknown":
            return "aborted"
        rollback = workflow.stage(stage_id).rollbacks[outcome]
        index = edges.index((stage_id, outcome))
        if counts[index] >= rollback.max:
            return "aborted"
        more = (*counts[:index], counts[index] + 1, *counts[index + 1 :])
        return (stages.index(rollback.target), visits, more)

    pending[(0, 0)][(tuple([0] * len(stages)), tuple([0] * len(edges)))] = 1.0
    for total in range(sum(rb.max for s in workflow.stages for rb in s.rollbacks.values()) + 1):
        for position, stage_id in enumerate(stages):
            stage = workflow.stage(stage_id)
            for (visits, counts), mass in pending.pop((total, position), {}).items():
                node = (position, visits, counts)
                order.append(node)
                visit = min(visits[position] + 1, model.cap)
                now = (*visits[:position], visit, *visits[position + 1 :])
                visits_mean[stage_id] += mass
                out: list[tuple[float, _Node | str]] = []
                for outcome, p in model.stage_distribution(stage_id, visit).items():
                    visit_outcomes[("stage", stage_id, visit, outcome)] += mass * p
                    if outcome != "goal":
                        out.append((p, returning(stage_id, outcome, now, counts)))
                    elif not workflow.is_last_in_phase(stage_id):
                        out.append((p, following(stage_id, now, counts)))
                    else:
                        for g, q in model.gate_distribution(stage.phase, visit).items():
                            visit_outcomes[("phase", stage.phase, visit, g)] += mass * p * q
                            if g == "goal":
                                out.append((p * q, following(stage_id, now, counts)))
                            else:
                                out.append((p * q, returning(stage_id, g, now, counts)))
                branches[node] = out
                for probability, target in out:
                    if isinstance(target, str):
                        status[target] += mass * probability
                    else:
                        t_position, t_visits, t_counts = target
                        pending[(sum(t_counts), t_position)][(t_visits, t_counts)] += (
                            mass * probability
                        )
    assert not pending, "処理されない状態が残った"
    # 逆の順に、各状態から先の訪問の回数 N の E[N] と E[N^2] をステージごとに求める。
    # その状態のステージでは N = 1 + N'（N' は分かれた先の回数）なので E[N^2] = 1 + 2E[N'] + E[N'^2]
    first: dict[_Node, list[float]] = {}
    second: dict[_Node, list[float]] = {}
    zero = [0.0] * len(stages)
    for node in reversed(order):
        e1, e2 = zero, zero
        for probability, target in branches[node]:
            if not isinstance(target, str):
                e1 = [x + probability * y for x, y in zip(e1, first[target], strict=True)]
                e2 = [x + probability * y for x, y in zip(e2, second[target], strict=True)]
        e1, e2 = list(e1), list(e2)
        here = node[0]
        e2[here] += 1 + 2 * e1[here]
        e1[here] += 1
        first[node], second[node] = e1, e2
    root = order[0]
    variance = {s: max(0.0, second[root][i] - first[root][i] ** 2) for i, s in enumerate(stages)}
    outcomes: dict[tuple[str, str], float] = defaultdict(float)
    evaluations: dict[tuple[str, str, int], float] = defaultdict(float)
    for (scope, target_id, bucket, outcome), v in visit_outcomes.items():
        if scope == "stage":
            outcomes[(target_id, outcome)] += v
        evaluations[(scope, target_id, bucket)] += v
    return Prediction(
        status,
        visits_mean,
        dict(sorted(outcomes.items())),
        dict(sorted(evaluations.items())),
        dict(sorted(visit_outcomes.items())),
        variance,
    )


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
