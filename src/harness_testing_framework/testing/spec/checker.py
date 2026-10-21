"""ワークフロー定義の整合性検査。

スキーマ（構造）を検査し、通れば意味の性質を検査する。end_state の記述の良し悪し
（成果物から観測できるか、互いに排他か）と優先順は検査しない。人間のレビューで見る。
"""

from collections.abc import Collection, Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from harness_testing_framework.schema import (
    WorkflowDocumentError,
    load_workflow_document,
    load_workflow_schema,
)

UNKNOWN = "unknown"


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


# 違反の符号 → (重大度, 説明)
CODES: dict[str, tuple[Severity, str]] = {
    "document": (Severity.ERROR, "YAML の文書として読めない"),
    "schema": (Severity.ERROR, "スキーマに適合しない"),
    "rollback_max": (Severity.ERROR, "rollback の max が無いか、1 以上の整数でない"),
    "duplicate_id": (Severity.ERROR, "id が重複している"),
    "unresolved_reference": (Severity.ERROR, "rollback の参照先が無い"),
    "unresolved_read": (Severity.ERROR, "読む成果物を inputs も前のステージも書かない"),
    "rollback_bijection": (
        Severity.ERROR,
        "unknown を除く end_state と rollback が一対一に対応しない",
    ),
    "rollback_forward": (Severity.ERROR, "戻り先がそのステージより前に無い"),
    "carry_undeclared": (
        Severity.ERROR,
        "carry の項目が元の memory_out か戻り先の memory_in に無い",
    ),
    "memory_unsupplied": (
        Severity.ERROR,
        "memory_in の項目を carry も前のステージも生成しない",
    ),
    "memory_unused": (
        Severity.WARNING,
        "memory_out の項目を carry も後のステージも消費しない",
    ),
    "metric_unregistered": (Severity.ERROR, "指標が指標レジストリに無い"),
    "metric_range": (Severity.ERROR, "指標の min が max より大きい"),
    "unknown_missing": (Severity.ERROR, "end_state に unknown が無い"),
}


@dataclass(frozen=True, order=True)
class Violation:
    location: str
    code: str
    message: str

    @property
    def severity(self) -> Severity:
        return CODES[self.code][0]


def _v(location: str, code: str, detail: str) -> Violation:
    assert code in CODES, code
    return Violation(location, code, f"{CODES[code][1]}: {detail}")


def _path(parts: Collection[Any]) -> str:
    return ".".join(str(p) for p in parts)


def _schema_violation(error: ValidationError) -> Violation:
    parts = list(error.absolute_path)
    location = _path(parts)
    in_rollback_item = len(parts) >= 2 and parts[-2] == "rollback"
    missing_max = error.validator == "required" and in_rollback_item
    missing_max = missing_max and isinstance(error.instance, dict) and "max" not in error.instance
    bad_max = len(parts) >= 3 and parts[-1] == "max" and parts[-3] == "rollback"
    if missing_max or bad_max:
        return _v(location, "rollback_max", error.message)
    return _v(location, "schema", error.message)


@dataclass(frozen=True)
class _Stage:
    position: int
    location: str
    doc: dict[str, Any]

    @property
    def id(self) -> str:
        stage_id: str = self.doc["id"]
        return stage_id

    def artifacts(self, key: str) -> list[str]:
        values: list[str] = self.doc["artifacts"].get(key, [])
        return values


def _covers(written: str, read: str) -> bool:
    """written を書いたことで read が読めるようになるか。/ で終わるものはディレクトリ。"""
    if written == read:
        return True
    if written.endswith("/") and read.startswith(written):
        return True
    return read.endswith("/") and written.startswith(read)


def _check_metrics(
    goal: dict[str, Any], location: str, metrics: Collection[str]
) -> Iterator[Violation]:
    for name, criterion in goal["quantitative"].items():
        where = f"{location}.goal.quantitative.{name}"
        if name not in metrics:
            yield _v(where, "metric_unregistered", name)
        low, high = criterion.get("min"), criterion.get("max")
        if low is not None and high is not None and low > high:
            yield _v(where, "metric_range", f"min={low} max={high}")


def _duplicates(items: list[tuple[str, str]], what: str) -> Iterator[Violation]:
    seen: dict[str, str] = {}
    for location, item_id in items:
        if item_id in seen:
            yield _v(location, "duplicate_id", f"{what} {item_id!r} は {seen[item_id]} にもある")
        else:
            seen[item_id] = location


def _check_semantics(doc: dict[str, Any], metrics: Collection[str]) -> Iterator[Violation]:
    workflow = doc["workflow"]
    stages: list[_Stage] = []
    phase_ids: list[tuple[str, str]] = []
    for pi, phase in enumerate(workflow["phases"]):
        phase_location = f"workflow.phases.{pi}"
        phase_ids.append((phase_location, phase["id"]))
        yield from _check_metrics(phase["goal"], phase_location, metrics)
        for si, stage in enumerate(phase["stages"]):
            stages.append(_Stage(len(stages), f"{phase_location}.stages.{si}", stage))

    duplicates = [
        *_duplicates(phase_ids, "フェーズ"),
        *_duplicates([(s.location, s.id) for s in stages], "ステージ"),
        *(
            v
            for s in stages
            for v in _duplicates(
                [
                    (f"{s.location}.end_state.{i}", e["id"])
                    for i, e in enumerate(s.doc["end_state"])
                ],
                f"ステージ {s.id} の end_state",
            )
        ),
    ]
    if duplicates:
        # 重複した id があると参照の解決が曖昧になるので、ここで打ち切る
        yield from duplicates
        return

    by_id = {s.id: s for s in stages}

    # 成果物の流れ: 読むものは inputs か前のステージの writes にある
    available: list[str] = list(workflow.get("inputs", []))
    for s in stages:
        for i, read in enumerate(s.artifacts("reads")):
            if not any(_covers(w, read) for w in available):
                yield _v(
                    f"{s.location}.artifacts.reads.{i}", "unresolved_read", f"{s.id} が {read}"
                )
        available += s.artifacts("writes")

    # 各ステージの end_state と rollback
    carried_to: dict[str, set[str]] = {s.id: set() for s in stages}
    carried_from: dict[str, set[str]] = {s.id: set() for s in stages}
    # 戻り先が解決できない rollback の carry は、どのステージへ運ばれるはずだったか分からない
    carried_to_unresolved: set[str] = set()
    for s in stages:
        end_states = [e["id"] for e in s.doc["end_state"]]
        if UNKNOWN not in end_states:
            yield _v(f"{s.location}.end_state", "unknown_missing", s.id)
        rollbacks = s.doc["rollback"]
        unresolved_state = False
        for ri, rb in enumerate(rollbacks):
            where = f"{s.location}.rollback.{ri}"
            if rb["state"] not in end_states:
                unresolved_state = True
                yield _v(
                    where, "unresolved_reference", f"{s.id} の end_state に {rb['state']!r} が無い"
                )
            target = by_id.get(rb["stage"])
            carried_from[s.id].update(rb.get("carry", []))
            if target is None:
                yield _v(where, "unresolved_reference", f"ステージ {rb['stage']!r} が無い")
                carried_to_unresolved.update(rb.get("carry", []))
                continue
            if target.position >= s.position:
                yield _v(where, "rollback_forward", f"{s.id} → {target.id}")
            for item in rb.get("carry", []):
                if item not in s.artifacts("memory_out"):
                    yield _v(where, "carry_undeclared", f"{item} が {s.id} の memory_out に無い")
                if item not in target.artifacts("memory_in"):
                    yield _v(
                        where, "carry_undeclared", f"{item} が {target.id} の memory_in に無い"
                    )
                carried_to[target.id].add(item)
        if not unresolved_state:
            yield from _check_bijection(s, end_states, rollbacks)

    # 記憶の生成と消費
    for s in stages:
        earlier = {m for t in stages[: s.position] for m in t.artifacts("memory_out")}
        later = {m for t in stages[s.position + 1 :] for m in t.artifacts("memory_in")}
        for i, item in enumerate(s.artifacts("memory_in")):
            supplied = carried_to[s.id] | carried_to_unresolved | earlier
            if item not in supplied:
                yield _v(
                    f"{s.location}.artifacts.memory_in.{i}",
                    "memory_unsupplied",
                    f"{s.id} の {item}",
                )
        for i, item in enumerate(s.artifacts("memory_out")):
            if item not in carried_from[s.id] and item not in later:
                yield _v(
                    f"{s.location}.artifacts.memory_out.{i}", "memory_unused", f"{s.id} の {item}"
                )

        yield from _check_metrics(s.doc["goal"], s.location, metrics)


def _check_bijection(s: _Stage, end_states: list[str], rollbacks: list[Any]) -> Iterator[Violation]:
    counts = {e: 0 for e in end_states}
    for ri, rb in enumerate(rollbacks):
        counts[rb["state"]] += 1
        if rb["state"] == UNKNOWN:
            yield _v(
                f"{s.location}.rollback.{ri}",
                "rollback_bijection",
                f"{s.id} の unknown に rollback がある",
            )
    for ei, e in enumerate(end_states):
        if e == UNKNOWN:
            continue
        if counts[e] != 1:
            yield _v(
                f"{s.location}.end_state.{ei}",
                "rollback_bijection",
                f"{s.id} の {e} に rollback が {counts[e]} 個ある",
            )


def check_workflow(doc: Any, metrics: Collection[str]) -> list[Violation]:
    """ワークフロー定義を検査する。metrics は指標レジストリにある指標名。"""
    validator = Draft202012Validator(load_workflow_schema())
    schema_errors = [_schema_violation(e) for e in validator.iter_errors(doc)]
    if schema_errors:
        return sorted(schema_errors)
    return sorted(_check_semantics(doc, metrics))


def check_workflow_file(path: Path, metrics: Collection[str]) -> list[Violation]:
    """ワークフロー定義のファイルを読んで検査する。"""
    try:
        doc = load_workflow_document(path)
    except WorkflowDocumentError as e:
        return [_v(str(path), "document", str(e))]
    return check_workflow(doc, metrics)
