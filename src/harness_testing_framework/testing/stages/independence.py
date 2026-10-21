"""遷移行列の推定と独立性検証。

状態は評価の結果（`stage:<id>=<結果>` か `phase:<id>=<結果>`）。次の状態は、同じ実行の中の次の評価の結果か、
評価が続かなければ実行の最後の状態（`end:<状態>`）。

独立性検証（plan.md 第2節）: クラスは下流の振る舞いに関する同値類なので、同じクラスに属する代表どうしで、
次の状態の分布が揃うはず。代表はステージが書いた成果物の内容のハッシュ。代表ごとの次の状態の分割表の
カイ二乗統計量を、代表の札を入れ替える並べ替え検定（種を固定）で判定する。並べ替え検定は小さい期待度数でも
近似に頼らない。
"""

import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from harness_testing_framework.testing.stages.runs import RunSet


@dataclass(frozen=True)
class Transition:
    run: int
    seq: int
    state: str
    representative: str | None
    next: str


def _state(event: dict[str, object] | object) -> str:
    assert isinstance(event, dict)
    target = event["stage"] if event["scope"] == "stage" else event["phase"]
    return f"{event['scope']}:{target}={event['outcome']}"


def transitions(runs: RunSet) -> list[Transition]:
    """全実行の、評価から次の評価（または実行の終わり）への遷移。"""
    out: list[Transition] = []
    for index, run in enumerate(runs.runs):
        evaluations = [dict(e) for e in run.evaluations()]
        for i, e in enumerate(evaluations):
            following = (
                _state(evaluations[i + 1]) if i + 1 < len(evaluations) else f"end:{run.status}"
            )
            seq = int(str(e["seq"]))
            representative = run.representatives.get(seq) if e["scope"] == "stage" else None
            out.append(Transition(index, seq, _state(e), representative, following))
    return out


def transition_counts(runs: RunSet) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for t in transitions(runs):
        counts[t.state][t.next] += 1
    return dict(counts)


def transition_matrix(runs: RunSet) -> dict[str, dict[str, float]]:
    """状態ごとの、次の状態の経験分布。"""
    matrix: dict[str, dict[str, float]] = {}
    for state, counter in transition_counts(runs).items():
        total = sum(counter.values())
        matrix[state] = {nxt: n / total for nxt, n in sorted(counter.items())}
    return matrix


def chi_square(table: Sequence[Sequence[int]]) -> float:
    """分割表のピアソンのカイ二乗統計量（期待度数が 0 の列は除く）。"""
    rows = [sum(r) for r in table]
    cols = [sum(c) for c in zip(*table, strict=True)]
    total = sum(rows)
    statistic = 0.0
    for i, row in enumerate(table):
        for j, observed in enumerate(row):
            expected = rows[i] * cols[j] / total
            if expected > 0:
                statistic += (observed - expected) ** 2 / expected
    return statistic


def _table(
    samples: Sequence[tuple[str, str]], groups: Sequence[str], columns: Sequence[str]
) -> list[list[int]]:
    counts = Counter(samples)
    return [[counts[(g, c)] for c in columns] for g in groups]


@dataclass(frozen=True)
class IndependenceResult:
    state: str
    groups: dict[str, int]
    statistic: float | None
    p_value: float | None
    verdict: str
    note: str = ""


def independence(
    runs: RunSet,
    *,
    alpha: float = 0.01,
    permutations: int = 2000,
    seed: int = 0,
    min_group: int = 10,
) -> list[IndependenceResult]:
    """ステージの評価の結果ごとに、代表どうしで次の状態の分布が揃うかを検定する。

    判定は independent（揃う）、violated（p 値が alpha 未満）、undetermined（samples が min_group 以上の
    代表が二つ未満）。
    """
    by_state: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for t in transitions(runs):
        if t.representative is not None:
            by_state[t.state].append((t.representative, t.next))
    results: list[IndependenceResult] = []
    for state in sorted(by_state):
        samples = by_state[state]
        sizes = Counter(rep for rep, _ in samples)
        groups = sorted(rep for rep, n in sizes.items() if n >= min_group)
        if len(groups) < 2:
            note = f"{min_group} 件以上の代表が二つ未満（代表ごとの件数 {dict(sizes)}）"
            results.append(IndependenceResult(state, dict(sizes), None, None, "undetermined", note))
            continue
        kept = [(rep, nxt) for rep, nxt in samples if rep in groups]
        columns = sorted({nxt for _, nxt in kept})
        observed = chi_square(_table(kept, groups, columns))
        rng = random.Random(seed)
        labels = [rep for rep, _ in kept]
        nexts = [nxt for _, nxt in kept]
        exceed = 0
        for _ in range(permutations):
            rng.shuffle(labels)
            if (
                chi_square(_table(list(zip(labels, nexts, strict=True)), groups, columns))
                >= observed - 1e-12
            ):
                exceed += 1
        p_value = (1 + exceed) / (1 + permutations)
        verdict = "violated" if p_value < alpha else "independent"
        results.append(
            IndependenceResult(state, {g: sizes[g] for g in groups}, observed, p_value, verdict)
        )
    return results
