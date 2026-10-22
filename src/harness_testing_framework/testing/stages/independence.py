"""遷移行列の推定と独立性検証。

状態は評価の結果（`stage:<id>=<結果>` か `phase:<id>=<結果>`）。次の状態は、同じ実行の中で続くゲートの評価
（あれば `>` でつなぐ）と、その次のステージの評価の結果。ステージの評価が続かなければ実行の最後の状態（`end:<状態>`）。
ゲートの評価を飛ばさずにつなぐのは、フェーズの最終ステージの goal の後に、次のフェーズの最初のステージの分布の
違いが見えるようにするため。

独立性検証: クラスは下流の振る舞いに関する同値類なので、同じクラスに属する代表どうしで、
次の状態の分布が揃うはず。代表はステージが書いた成果物の内容のハッシュ。代表ごとの次の状態の分割表の
カイ二乗統計量を、代表の札を入れ替える並べ替え検定（種を固定）で判定する。並べ替え検定は小さい期待度数でも
近似に頼らない。マルコフ合成と同じく、評価の訪問の番号を cap でまとめた区分ごとに分けて検定する（訪問によって
成果物と下流が変わるのは、クラスの粗さではない）。次のステージの評価の訪問の区分も層に含める（代表が「どこから
戻ってきたか」で変わり、次のステージの訪問と結びつく場合に、訪問による下流の違いを取り違えない）。

判定 not_detected は「この件数では違いを検出しなかった」の意味で、揃うことの証明ではない。状態ごとに独立に検定し、
多重性の補正はしない（違反の疑いは人がトリアージで確かめる）。
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
    visit: int
    representative: str | None
    next: str
    next_visit: int = 0
    """次のステージの評価の訪問の回数（ステージの評価が続かなければ 0）。"""


def _state(event: dict[str, object] | object) -> str:
    assert isinstance(event, dict)
    target = event["stage"] if event["scope"] == "stage" else event["phase"]
    return f"{event['scope']}:{target}={event['outcome']}"


def transitions(runs: RunSet) -> list[Transition]:
    """全実行の、評価から次の状態への遷移。次の状態は、続くゲートの評価を `>` でつなぎ、その次のステージの評価
    （ステージの評価が続かなければ実行の終わり `end:<状態>`）までを含む。"""
    out: list[Transition] = []
    for index, run in enumerate(runs.runs):
        evaluations = [dict(e) for e in run.evaluations()]
        for i, e in enumerate(evaluations):
            chain: list[str] = []
            next_visit = 0
            for later in evaluations[i + 1 :]:
                chain.append(_state(later))
                if later["scope"] == "stage":
                    next_visit = int(str(later["visit"]))
                    break
            else:
                chain.append(f"end:{run.status}")
            seq = int(str(e["seq"]))
            representative = run.representatives.get(seq) if e["scope"] == "stage" else None
            visit = int(str(e["visit"]))
            out.append(
                Transition(
                    index, seq, _state(e), visit, representative, " > ".join(chain), next_visit
                )
            )
    return out


def transition_counts(runs: RunSet) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for t in transitions(runs):
        counts[t.state][t.next] += 1
    return dict(counts)


def transition_matrix(runs: RunSet) -> dict[str, dict[str, float]]:
    """状態ごとの、次の状態（transitions の定義。ゲートをつないで次のステージの評価まで）の経験分布。"""
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


def _permutation_test(
    kept: Sequence[tuple[str, str]], groups: Sequence[str], permutations: int, seed: int
) -> tuple[float, float]:
    """群の札を入れ替える並べ替え検定。カイ二乗統計量と p 値。"""
    columns = sorted({value for _, value in kept})
    observed = chi_square(_table(kept, groups, columns))
    rng = random.Random(seed)
    labels = [g for g, _ in kept]
    values = [v for _, v in kept]
    exceed = 0
    for _ in range(permutations):
        rng.shuffle(labels)
        if chi_square(_table(list(zip(labels, values, strict=True)), groups, columns)) >= (
            observed - 1e-12
        ):
            exceed += 1
    return observed, (1 + exceed) / (1 + permutations)


@dataclass(frozen=True)
class IndependenceResult:
    state: str
    visit: int
    next_visit: int
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
    cap: int = 2,
) -> list[IndependenceResult]:
    """ステージの評価の結果ごとに、代表どうしで次の状態の分布が揃うかを検定する。

    判定は not_detected（違いを検出しなかった）、violated（p 値が alpha 未満）、undetermined（件数が min_group
    以上の代表が二つ未満）。状態と、訪問の区分（cap 以上は一つ）の組ごとに検定する。
    """
    by_state: dict[tuple[str, int, int], list[tuple[str, str]]] = defaultdict(list)
    for t in transitions(runs):
        if t.representative is not None:
            key = (t.state, min(t.visit, cap), min(t.next_visit, cap))
            by_state[key].append((t.representative, t.next))
    results: list[IndependenceResult] = []
    for state, bucket, next_bucket in sorted(by_state):
        samples = by_state[(state, bucket, next_bucket)]
        sizes = Counter(rep for rep, _ in samples)
        groups = sorted(rep for rep, n in sizes.items() if n >= min_group)
        if len(groups) < 2:
            note = f"{min_group} 件以上の代表が二つ未満（代表ごとの件数 {dict(sizes)}）"
            results.append(
                IndependenceResult(
                    state, bucket, next_bucket, dict(sizes), None, None, "undetermined", note
                )
            )
            continue
        kept = [(rep, nxt) for rep, nxt in samples if rep in groups]
        observed, p_value = _permutation_test(kept, groups, permutations, seed)
        verdict = "violated" if p_value < alpha else "not_detected"
        results.append(
            IndependenceResult(
                state,
                bucket,
                next_bucket,
                {g: sizes[g] for g in groups},
                observed,
                p_value,
                verdict,
            )
        )
    return results


@dataclass(frozen=True)
class Entry:
    """ステージの一回の訪問と、その入り方と評価の結果。

    entry は `start`（実行の最初）、`next:<前のステージ>`、`rollback:<元ステージ>=<end_state>`（ゲートの不合格を
    含む）、`operator_rollback:<escalate したステージ>`、`rerun`（運用者の再実行）。outcome はその訪問のステージの
    評価の結果（評価の前に終わった訪問は None）。
    """

    run: int
    stage: str
    visit: int
    entry: str
    outcome: str | None


def entries(runs: RunSet) -> list[Entry]:
    """全実行の、ステージの訪問ごとの入り方と評価の結果。中断からの再開は同じ訪問の続きで、入り方を変えない。"""
    out: list[Entry] = []
    for run in runs.runs:
        entry = "start"
        found: dict[tuple[str, int], int] = {}
        visits: list[Entry] = []
        for e in run.events:
            kind = e["event"]
            if kind == "transition" and e["kind"] == "next":
                entry = f"next:{e['from']}"
            elif kind == "transition" and e["kind"] == "rollback":
                edge = e["edge"]
                entry = (
                    f"rollback:{edge['stage']}={edge['state']}"
                    if isinstance(edge, dict)
                    else f"operator_rollback:{e['from']}"
                )
            elif kind == "escalation" and isinstance(e["decision"], dict):
                if e["decision"]["kind"] == "rerun":
                    entry = "rerun"
            elif kind == "stage_start":
                key = (str(e["stage"]), int(e["visit"]))
                if key not in found:
                    found[key] = len(visits)
                    visits.append(Entry(run.seed, key[0], key[1], entry, None))
            elif kind == "evaluation" and e["scope"] == "stage":
                key = (str(e["stage"]), int(e["visit"]))
                if key in found:
                    index = found[key]
                    visits[index] = Entry(
                        run.seed, key[0], key[1], visits[index].entry, str(e["outcome"])
                    )
        out += visits
    return out


@dataclass(frozen=True)
class EntryDependenceResult:
    stage: str
    visit: int
    """訪問の区分（min(訪問, cap)）。"""
    groups: dict[str, int]
    statistic: float | None
    p_value: float | None
    verdict: str
    note: str = ""


def entry_dependence(
    runs: RunSet,
    *,
    from_visit: int = 2,
    alpha: float = 0.01,
    permutations: int = 2000,
    seed: int = 0,
    min_group: int = 10,
    cap: int = 2,
) -> list[EntryDependenceResult]:
    """ステージの from_visit 回目以降の訪問の評価の結果が、入り方（Entry.entry）で違うかを検定する。

    マルコフ合成は、クラスの分布が (ステージ, 訪問の区分) だけで決まると仮定する。入り方（どの辺から戻ったか、
    carry を受けたか）で結果が違えば、その仮定は崩れている。予測と実測が合っていても、集計した量では違いが
    打ち消し合うことがあるので、入り方が複数あるステージはこれで確かめる。ステージと訪問の区分（cap 以上は一つ）の
    組ごとに、入り方の札を入れ替える並べ替え検定で判定する。判定の意味は independence と同じ。
    """
    by_key: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)
    for e in entries(runs):
        if e.visit >= from_visit and e.outcome is not None:
            by_key[(e.stage, min(e.visit, cap))].append((e.entry, e.outcome))
    results: list[EntryDependenceResult] = []
    for stage, bucket in sorted(by_key):
        samples = by_key[(stage, bucket)]
        sizes = Counter(entry for entry, _ in samples)
        groups = sorted(entry for entry, n in sizes.items() if n >= min_group)
        if len(groups) < 2:
            note = f"{min_group} 件以上の入り方が二つ未満（入り方ごとの件数 {dict(sizes)}）"
            results.append(
                EntryDependenceResult(stage, bucket, dict(sizes), None, None, "undetermined", note)
            )
            continue
        kept = [(entry, outcome) for entry, outcome in samples if entry in groups]
        observed, p_value = _permutation_test(kept, groups, permutations, seed)
        verdict = "violated" if p_value < alpha else "not_detected"
        results.append(
            EntryDependenceResult(
                stage, bucket, {g: sizes[g] for g in groups}, observed, p_value, verdict
            )
        )
    return results
