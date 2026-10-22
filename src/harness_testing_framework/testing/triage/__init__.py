"""トリアージ待ち行列。unknown と確信度の低い評価を集め、人の判定を記録する。

待ち行列と判定の記録は JSON Lines のファイル（慣例として reports/triage/）。状態文書は置き場にあり、各項目は
その SHA-256 を持つ。分類体系の変更（新しいクラス、記述の改訂）は提案として記録するだけで、ワークフロー定義は
変えない（記述の改訂は人間の承認を経る）。
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.testing.stages.runs import RunRecord

VERDICTS = (
    "label",
    "not_a_problem",
    "classifier_error",
    "new_class_proposal",
    "description_revision_proposal",
)
PROPOSALS = ("new_class_proposal", "description_revision_proposal")


class TriageInvalid(ValueError):
    """待ち行列か判定が形式に適合しない、または項目と食い違う。"""


@dataclass(frozen=True)
class TriageItem:
    """待ち行列の一項目。

    item は `<実行の id>-<評価の seq>` で、分類器の検証のコーパスの項目の id と同じ形。state は状態文書の
    SHA-256 で、内容は置き場（BlobStore.get）で読める。reason は unknown か low_confidence。
    """

    item: str
    run: int
    seq: int
    scope: str
    target: str
    visit: int
    options: list[str]
    choice: str | None
    confidence: float
    outcome: str
    state: str
    reason: str


@dataclass(frozen=True)
class Decision:
    item: str
    verdict: str
    label: str | None
    note: str
    by: str

    @property
    def proposal(self) -> bool:
        return self.verdict in PROPOSALS


@cache
def _validator(schema: str) -> Draft202012Validator:
    return Draft202012Validator(load_contract_schema(schema))


# 読んだファイルごとの、検査済みの先頭部分（バイト数、その SHA-256、行の数、行の内容）。待ち行列と判定の記録は
# 追記で育つので、先頭が前に読んだ時のままなら、追記された行だけを検査して読み足す（判定を一件ずつ記録しても、
# 項目の数の二乗の検査にならない）。先頭が変わっていれば全体を読み直す
_seen: dict[tuple[Path, str], tuple[int, str, int, list[dict[str, Any]]]] = {}


def _read(path: Path, schema: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = path.read_bytes()
    key = (path.resolve(), schema)
    rows: list[dict[str, Any]] = []
    start = lines = 0
    if key in _seen:
        size, digest, seen_lines, seen_rows = _seen[key]
        if len(data) >= size and hashlib.sha256(data[:size]).hexdigest() == digest:
            rows, start, lines = list(seen_rows), size, seen_lines
    validator = _validator(schema)
    for chunk in data[start:].splitlines(keepends=True):
        lines += 1
        line = chunk.decode("utf-8")
        if line.strip():
            row = json.loads(line)
            errors = list(validator.iter_errors(row))
            if errors:
                raise TriageInvalid(f"{path}:{lines}: " + "; ".join(e.message for e in errors))
            rows.append(row)
    # 改行で終わっていない最後の行（書きかけかもしれない）は覚えず、次に読む時にもう一度検査する
    if data.endswith(b"\n") or not data:
        _seen[key] = (len(data), hashlib.sha256(data).hexdigest(), lines, list(rows))
    return rows


def _append(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def items(queue: Path) -> list[TriageItem]:
    """待ち行列の全項目（形式を検査する）。"""
    return [TriageItem(**r) for r in _read(queue, "triage_item.schema.json")]


def enqueue(queue: Path, run: RunRecord, *, review_below: float) -> list[TriageItem]:
    """実行記録の評価のうち、結果が unknown のものと、確信度が review_below 未満のものを待ち行列に足す。
    すでにある項目は足さない。足した項目を返す。"""
    known = {i.item for i in items(queue)}
    added: list[TriageItem] = []
    for e in run.evaluations():
        classification = e["classification"]
        if not isinstance(classification, Mapping) or "state" not in classification:
            continue
        confidence = float(classification["confidence"])
        if e["outcome"] == "unknown":
            reason = "unknown"
        elif confidence < review_below:
            reason = "low_confidence"
        else:
            continue
        target = str(e["stage"] if e["scope"] == "stage" else e["phase"])
        item = TriageItem(
            item=f"{run.run_id}-{e['seq']}",
            run=run.seed,
            seq=int(e["seq"]),
            scope=str(e["scope"]),
            target=target,
            visit=int(e["visit"]),
            options=[str(o) for o in classification["options"]],
            choice=classification["choice"],
            confidence=confidence,
            outcome=str(e["outcome"]),
            state=str(classification["state"]),
            reason=reason,
        )
        if item.item not in known:
            added.append(item)
            known.add(item.item)
    _append(queue, [asdict(i) for i in added])
    return added


def decisions(record: Path) -> list[Decision]:
    """判定の記録の全行（形式を検査する）。"""
    return [
        Decision(r["item"], r["verdict"], r["label"], r["note"], r["by"])
        for r in _read(record, "triage_decision.schema.json")
    ]


def decide(queue: Path, record: Path, decision: Decision) -> None:
    """項目への判定を記録する。label はその評価の選択肢のどれか。分類体系の変更は提案として残す。"""
    if decision.verdict not in VERDICTS:
        raise TriageInvalid(f"判定 {decision.verdict} は {VERDICTS} のどれでもない")
    by_item = {i.item: i for i in items(queue)}
    if decision.item not in by_item:
        raise TriageInvalid(f"待ち行列に項目 {decision.item} が無い")
    options = by_item[decision.item].options
    if decision.verdict == "label" and decision.label not in options:
        raise TriageInvalid(f"ラベル {decision.label} が項目の選択肢 {options} に無い")
    if decision.label is not None and decision.label not in options:
        raise TriageInvalid(f"正しいクラス {decision.label} が項目の選択肢 {options} に無い")
    row = {**asdict(decision), "proposal": decision.proposal}
    _append(record, [row])


def open_items(queue: Path, record: Path | None = None) -> list[TriageItem]:
    """判定のまだ無い項目。"""
    decided = {d.item for d in decisions(record)} if record is not None else set()
    return [i for i in items(queue) if i.item not in decided]


__all__ = [
    "PROPOSALS",
    "VERDICTS",
    "Decision",
    "TriageInvalid",
    "TriageItem",
    "decide",
    "decisions",
    "enqueue",
    "items",
    "open_items",
]
