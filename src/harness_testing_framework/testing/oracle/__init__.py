"""分類器の検証（オラクル）。コーパス形式とラベル形式、一致率（Cohen の κ）・較正（ECE）・再実行一致のレポート。

コーパスの各項目は、分類器が見た状態文書と選択肢（実行記録と置き場から作れる）。ラベルは人手で付けた正しいクラス。
分類器の判定の閾値は、このレポートの較正の結果から決める（plan.md 第2節）。
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
from harness_testing_framework.testing.harness.fakes import _MARKER, evaluation_target
from harness_testing_framework.testing.stages.runs import RunSet


class CorpusInvalid(ValueError):
    """コーパスかラベルが形式に適合しない、または互いに食い違う。"""


@dataclass(frozen=True)
class CorpusItem:
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


def build_corpus(runs: RunSet, store: BlobStore, workflow: Workflow) -> list[CorpusItem]:
    """実行記録の各評価から、分類器が見た状態文書と選択肢の項目を作る。状態文書は置き場から読む。"""
    items: list[CorpusItem] = []
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
            state = store.get(str(classification["state"])).decode("utf-8")
            item = f"{run.seed}-{e['seq']}"
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
class OracleReport:
    n: int
    kappa: float
    accuracy: float
    confusion: dict[tuple[str, str | None], int]
    ece: float
    bins: list[CalibrationBin]
    rerun_agreement: float
    unanswered: int

    def lines(self) -> list[str]:
        out = [
            f"件数 {self.n}、一致率 {self.accuracy:.3f}、Cohen の κ {self.kappa:.3f}、ECE {self.ece:.3f}（等幅 {len(self.bins)} 区間）",
            f"再実行の一致率 {self.rerun_agreement:.3f}、答え無し {self.unanswered} 件",
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
    答え無しは独立のカテゴリとして数え、確信度 0 の不正解として較正に入れる。
    """
    by_item = {i.item: i for i in corpus}
    pairs: list[tuple[str, str | None]] = []
    records: list[tuple[float, bool]] = []
    agree = 0
    for label in labels:
        if label.item not in by_item:
            raise CorpusInvalid(f"ラベルの項目 {label.item} がコーパスに無い")
        item = by_item[label.item]
        if label.label not in {o.id for o in item.options}:
            raise CorpusInvalid(f"ラベル {label.label} が項目 {label.item} の選択肢に無い")
        results = [classifier.classify(item.state, item.options) for _ in range(max(1, reruns))]
        first = results[0]
        choice = first.choice if first.choice in {o.id for o in item.options} else None
        confidence = first.confidence if choice is not None else 0.0
        pairs.append((label.label, choice))
        records.append((confidence, choice == label.label))
        agree += all(r.choice == first.choice for r in results)
    n = len(pairs)
    ece, table = expected_calibration_error(records, bins)
    return OracleReport(
        n=n,
        kappa=cohen_kappa(pairs),
        accuracy=sum(1 for a, b in pairs if a == b) / n,
        confusion=dict(Counter(pairs)),
        ece=ece,
        bins=table,
        rerun_agreement=agree / n,
        unanswered=sum(1 for _, b in pairs if b is None),
    )


class ConfusionClassifier:
    """既知の混同行列を持つ偽の分類器。

    状態文書の印 `[[class <対象>=<真のクラス>]]` から真のクラスを読み、rows[真のクラス] の (選ぶクラス, 確信度) を
    真のクラスごとに、初めて見た順に巡って割り当てる。同じ状態文書には同じ答えを返す（決定論的）。
    真のクラスごとの件数が rows の長さの倍数なら、混同行列は配分どおりになる。
    """

    def __init__(self, rows: Mapping[str, Sequence[tuple[str | None, float]]]) -> None:
        self._rows = rows
        self._cursor: Counter[str] = Counter()
        self._answers: dict[str, Classification] = {}

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        key = hashlib.sha256(state.encode()).hexdigest()
        if key in self._answers:
            return self._answers[key]
        target = evaluation_target(state)
        truth = next((c for t, c in _MARKER.findall(state) if target and t == target[1]), None)
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
    "build_corpus",
    "cohen_kappa",
    "expected_calibration_error",
    "load_corpus",
    "load_labels",
    "oracle_report",
    "save_corpus",
    "save_labels",
]
