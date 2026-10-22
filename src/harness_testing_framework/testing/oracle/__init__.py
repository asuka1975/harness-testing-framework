"""分類器の検証（オラクル）。コーパス形式とラベル形式、一致率（Cohen の κ）・較正（ECE）・再実行一致のレポート。

コーパスの各項目は、分類器が見た状態文書と選択肢（実行記録と置き場から作れる）。ラベルは人手で付けた正しいクラス。
分類器の判定の閾値は、このレポートの較正の結果から決める。
"""

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from harness_testing_framework.contract import (
    Classification,
    Classifier,
    Option,
    load_contract_schema,
)
from harness_testing_framework.runtime.checkpoint import BlobStore
from harness_testing_framework.runtime.model import Workflow
from harness_testing_framework.runtime.oracle import safe_classify
from harness_testing_framework.testing.harness.fakes import marked_class
from harness_testing_framework.testing.stages.runs import RunSet


class CorpusInvalid(ValueError):
    """コーパスかラベルが形式に適合しない、または互いに食い違う。"""


@dataclass(frozen=True)
class CorpusItem:
    """コーパスの一項目。

    item は `<実行の id>-<評価の seq>` で、トリアージの項目の id と同じ形（突き合わせられる）。scope は stage か
    phase、target はステージかフェーズの id、options は選択肢、state は分類器が見た状態文書、source は出どころ
    （実行の種、seq、分類器の選択）。
    """

    item: str
    scope: str
    target: str
    options: tuple[Option, ...]
    state: str
    source: Mapping[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "item": self.item,
            "scope": self.scope,
            "target": self.target,
            "options": [{"id": o.id, "description": o.description} for o in self.options],
            "state": self.state,
        }
        if self.source:
            out["source"] = dict(self.source)
        return out


@dataclass(frozen=True)
class Label:
    """人手のラベル。item はコーパスの項目の id、label はその項目の選択肢のどれか、labeler は付けた人。"""

    item: str
    label: str
    labeler: str


def _read_jsonl(path: Path, schema_name: str) -> list[dict[str, Any]]:
    validator = Draft202012Validator(load_contract_schema(schema_name))
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        errors = list(validator.iter_errors(row))
        if errors:
            raise CorpusInvalid(f"{path}:{n}: " + "; ".join(e.message for e in errors))
        rows.append(row)
    return rows


def _write_jsonl(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )


def load_corpus(path: Path) -> list[CorpusItem]:
    return [
        CorpusItem(
            r["item"],
            r["scope"],
            r["target"],
            tuple(Option(o["id"], o["description"]) for o in r["options"]),
            r["state"],
            r.get("source", {}),
        )
        for r in _read_jsonl(path, "corpus_item.schema.json")
    ]


def save_corpus(items: Sequence[CorpusItem], path: Path) -> None:
    _write_jsonl([i.to_json() for i in items], path)


def load_labels(path: Path) -> list[Label]:
    return [
        Label(r["item"], r["label"], r["labeler"]) for r in _read_jsonl(path, "label.schema.json")
    ]


def save_labels(labels: Sequence[Label], path: Path) -> None:
    _write_jsonl([{"item": x.item, "label": x.label, "labeler": x.labeler} for x in labels], path)


def build_corpus(
    runs: RunSet, store: BlobStore, workflow: Workflow, *, unique_states: bool = False
) -> list[CorpusItem]:
    """実行記録の各評価から、分類器が見た状態文書と選択肢の項目を作る。状態文書は置き場から読む。

    unique_states が真なら、状態文書と選択肢の組ごとに最初の項目だけを残す。偽の本体のように同じ成果物が
    繰り返し出る実行では、同じ状態文書が何度も入り、項目の数の重みが状態文書の出現の回数で偏る。
    """
    items: list[CorpusItem] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for run in runs.runs:
        for e in run.evaluations():
            classification = e["classification"]
            if not isinstance(classification, Mapping) or "state" not in classification:
                continue
            stage = workflow.stage(str(e["stage"]))
            if e["scope"] == "stage":
                goal_text, target = stage.goal.qualitative, stage.id
            else:
                phase = workflow.phase(stage.phase)
                goal_text, target = phase.goal.qualitative, phase.id
            descriptions = {"goal": goal_text, **{s.id: s.description for s in stage.end_states}}
            options = tuple(Option(o, descriptions[o]) for o in classification["options"])
            key = (str(classification["state"]), tuple(o.id for o in options))
            if unique_states and key in seen:
                continue
            seen.add(key)
            state = store.get(str(classification["state"])).decode("utf-8")
            item = f"{run.run_id}-{e['seq']}"
            source = {"run": run.seed, "seq": e["seq"], "choice": classification["choice"]}
            items.append(CorpusItem(item, str(e["scope"]), target, options, state, source))
    return items


def cohen_kappa(pairs: Sequence[tuple[str | None, str | None]]) -> float:
    """(人手のラベル, 分類器の選択) の組から Cohen の κ。偶然の一致が 1 なら、一致率が 1 のとき 1。"""
    n = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / n
    left = Counter(a for a, _ in pairs)
    right = Counter(b for _, b in pairs)
    chance = sum(left[k] * right.get(k, 0) for k in left) / (n * n)
    if chance == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - chance) / (1 - chance)


@dataclass(frozen=True)
class CalibrationBin:
    low: float
    high: float
    n: int
    accuracy: float
    confidence: float


def expected_calibration_error(
    records: Sequence[tuple[float, bool]], bins: int = 10
) -> tuple[float, list[CalibrationBin]]:
    """(確信度, 正解か) の組の ECE。確信度を [0, 1] の等幅の bins 個の区間に分け（最後の区間は 1 を含む）、
    区間ごとの |正解率 - 平均の確信度| を件数で重みづけて足す。"""
    groups: list[list[tuple[float, bool]]] = [[] for _ in range(bins)]
    for confidence, correct in records:
        index = min(int(round(confidence * bins, 9)), bins - 1)
        groups[index].append((confidence, correct))
    table: list[CalibrationBin] = []
    ece = 0.0
    for i, group in enumerate(groups):
        low, high = i / bins, (i + 1) / bins
        if not group:
            table.append(CalibrationBin(low, high, 0, 0.0, 0.0))
            continue
        accuracy = sum(1 for _, c in group if c) / len(group)
        confidence = sum(c for c, _ in group) / len(group)
        ece += len(group) / len(records) * abs(accuracy - confidence)
        table.append(CalibrationBin(low, high, len(group), accuracy, confidence))
    return ece, table


@dataclass(frozen=True)
class TargetSummary:
    n: int
    kappa: float
    accuracy: float
    ece: float | None


@dataclass(frozen=True)
class OracleReport:
    """分類器の検証の結果。

    ECE は答えた項目だけで計算する（答え無しを確信度 0 の不正解として入れると、答え無しが多いほど ECE が下がるため）。
    答えた割合は coverage に、答え無しの件数は unanswered に出す。κ と混同行列は、答え無しを独立のカテゴリとして数える。
    by_target の鍵は `stage:<ステージの id>` か `phase:<フェーズの id>`。
    """

    n: int
    kappa: float
    accuracy: float
    confusion: dict[tuple[str, str | None], int]
    ece: float | None
    bins: list[CalibrationBin]
    rerun_agreement: float
    unanswered: int
    coverage: float
    by_target: dict[str, TargetSummary]

    def lines(self) -> list[str]:
        ece = (
            f"ECE {self.ece:.3f}（等幅 {len(self.bins)} 区間）"
            if self.ece is not None
            else "ECE なし（答えた項目が無い）"
        )
        out = [
            f"件数 {self.n}、一致率 {self.accuracy:.3f}、Cohen の κ {self.kappa:.3f}、{ece}",
            f"再実行の一致率 {self.rerun_agreement:.3f}、答え無し {self.unanswered} 件（答えた割合 {self.coverage:.3f}。ECE は答えた項目だけ）",
        ]
        out += [
            f"混同 {label} → {choice}: {n}"
            for (label, choice), n in sorted(self.confusion.items(), key=str)
        ]
        out += [
            f"区間 [{b.low:.1f}, {b.high:.1f}): {b.n} 件、正解率 {b.accuracy:.3f}、平均の確信度 {b.confidence:.3f}"
            for b in self.bins
            if b.n
        ]
        return out


def oracle_report(
    classifier: Classifier,
    corpus: Sequence[CorpusItem],
    labels: Sequence[Label],
    *,
    bins: int = 10,
    reruns: int = 2,
) -> OracleReport:
    """ラベルの付いた各項目を分類器にかけ、κ、混同行列、ECE、再実行の一致率を求める。

    同じ項目を reruns 回分類し、すべて同じ選択だった項目の割合を再実行の一致率とする。κ と ECE は一回目の結果で計算する。
    分類器の出力はランタイムと同じく「答え無し」に正規化する（例外、範囲外や有限でない確信度、選択肢に無い id）。
    答え無しは κ と混同行列では独立のカテゴリとして数え、ECE には入れない。
    """
    if not labels:
        raise CorpusInvalid("ラベルが一つも無い")
    by_item = {i.item: i for i in corpus}
    pairs: list[tuple[str, str | None]] = []
    records: list[tuple[float, bool]] = []
    targets: list[str] = []
    agree = 0
    for label in labels:
        if label.item not in by_item:
            raise CorpusInvalid(f"ラベルの項目 {label.item} がコーパスに無い")
        item = by_item[label.item]
        if label.label not in {o.id for o in item.options}:
            raise CorpusInvalid(f"ラベル {label.label} が項目 {label.item} の選択肢に無い")
        results = [
            safe_classify(classifier, item.state, item.options) for _ in range(max(1, reruns))
        ]
        first = results[0]
        pairs.append((label.label, first.choice))
        records.append((first.confidence, first.choice == label.label))
        targets.append(f"{item.scope}:{item.target}")
        agree += all(r.choice == first.choice for r in results)
    n = len(pairs)
    answered = [r for r, (_, choice) in zip(records, pairs, strict=True) if choice is not None]
    ece: float | None = None
    table: list[CalibrationBin] = []
    if answered:
        ece, table = expected_calibration_error(answered, bins)
    by_target: dict[str, TargetSummary] = {}
    for target in sorted(set(targets)):
        idx = [i for i, t in enumerate(targets) if t == target]
        sub_pairs = [pairs[i] for i in idx]
        sub_answered = [records[i] for i in idx if pairs[i][1] is not None]
        sub_ece = expected_calibration_error(sub_answered, bins)[0] if sub_answered else None
        accuracy = sum(1 for a, b in sub_pairs if a == b) / len(idx)
        by_target[target] = TargetSummary(len(idx), cohen_kappa(sub_pairs), accuracy, sub_ece)
    return OracleReport(
        n=n,
        kappa=cohen_kappa(pairs),
        accuracy=sum(1 for a, b in pairs if a == b) / n,
        confusion=dict(Counter(pairs)),
        ece=ece,
        bins=table,
        rerun_agreement=agree / n,
        unanswered=sum(1 for _, b in pairs if b is None),
        coverage=len(answered) / n,
        by_target=by_target,
    )


class ConfusionClassifier:
    """既知の混同行列を持つ偽の分類器。

    状態文書の印 `[[class <対象>=<真のクラス>]]` から真のクラスを読み、rows[真のクラス] の (選ぶクラス, 確信度) を
    真のクラスごとに、初めて見た順に巡って割り当てる。同じ状態文書には同じ答えを返す（決定論的）。
    配分は違う状態文書の数で巡るので、真のクラスごとの違う状態文書の数が rows の長さの倍数で、コーパスに同じ
    状態文書が重ならない（build_corpus の unique_states）なら、混同行列は配分どおりになる。
    """

    def __init__(self, rows: Mapping[str, Sequence[tuple[str | None, float]]]) -> None:
        self._rows = rows
        self._cursor: Counter[str] = Counter()
        self._answers: dict[str, Classification] = {}

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        key = hashlib.sha256(state.encode()).hexdigest()
        if key in self._answers:
            return self._answers[key]
        truth = marked_class(state)
        if truth is None or truth not in self._rows:
            answer = Classification(None, 0.0)
        else:
            row = self._rows[truth]
            choice, confidence = row[self._cursor[truth] % len(row)]
            self._cursor[truth] += 1
            answer = Classification(choice, confidence)
        self._answers[key] = answer
        return answer


class FlakyClassifier:
    """再実行で答えが揺れる偽の分類器。

    同じ状態文書を二回目以降に分類する時、初めて見た順で every 件に一件の項目だけ、選択肢の中の別のクラスを返す。
    再実行の一致率は 1 - 1/every になる。一回目の答えは基の分類器のもの。
    「二回目」は再実行に限らない。コーパスに同じ状態文書が二度あれば、一回目の分類の中でも二度目は揺れる。
    重なりの無いコーパス（build_corpus の unique_states）で使う。
    """

    def __init__(self, base: Classifier, every: int) -> None:
        self._base = base
        self._every = every
        self._first: dict[str, Classification] = {}
        self._order: dict[str, int] = {}

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        key = hashlib.sha256(state.encode()).hexdigest()
        if key not in self._first:
            self._order[key] = len(self._order)
            self._first[key] = self._base.classify(state, options)
            return self._first[key]
        first = self._first[key]
        if self._order[key] % self._every != 0:
            return first
        others = [o.id for o in options if o.id != first.choice]
        return Classification(others[0] if others else None, first.confidence)


__all__ = [
    "CalibrationBin",
    "ConfusionClassifier",
    "CorpusInvalid",
    "CorpusItem",
    "FlakyClassifier",
    "Label",
    "OracleReport",
    "TargetSummary",
    "build_corpus",
    "cohen_kappa",
    "expected_calibration_error",
    "load_corpus",
    "load_labels",
    "oracle_report",
    "save_corpus",
    "save_labels",
]
