"""評価（契約 2.2）と状態文書の投影（契約 2.4）。"""

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass

from harness_testing_framework.contract import (
    Classification,
    Classifier,
    JSONValue,
    MetricError,
    MetricRegistry,
    Option,
)
from harness_testing_framework.runtime.checkpoint import BlobStore, Snapshot, SnapshotReader
from harness_testing_framework.runtime.model import Criterion, EndState, Goal
from harness_testing_framework.runtime.recorder import Key, Recorder

GOAL = "goal"
UNKNOWN = "unknown"


def satisfies(criterion: Criterion, value: bool | float) -> bool:
    """測った値が基準を満たすか。比較はフレームワークが行う（決定 #2）。"""
    if criterion.equals is not None:
        if isinstance(criterion.equals, bool) or isinstance(value, bool):
            return isinstance(value, bool) and value is criterion.equals
        return float(value) == float(criterion.equals)
    if isinstance(value, bool):
        return False
    low = criterion.min if criterion.min is not None else float("-inf")
    high = criterion.max if criterion.max is not None else float("inf")
    return low <= value <= high


@dataclass(frozen=True)
class MetricResult:
    value: bool | float | None
    passed: bool
    error: str | None = None

    def to_json(self) -> dict[str, JSONValue]:
        out: dict[str, JSONValue] = {"value": self.value, "passed": self.passed}
        if self.error is not None:
            out["error"] = self.error
        return out


def measure(
    goal: Goal,
    registry: MetricRegistry,
    view: SnapshotReader,
    recorder: Recorder,
    key: Key,
) -> dict[str, MetricResult]:
    """goal の各指標を測って基準と比べる。測定の失敗は未達（D-1）。"""
    results: dict[str, MetricResult] = {}
    for criterion in goal.criteria:

        def live(c: Criterion = criterion) -> JSONValue:
            try:
                return {"value": registry.measure(c.name, view, c.args)}
            except MetricError as e:
                return {"error": str(e)}
            except Exception as e:
                # 指標の実装の不具合も、測定の失敗として未達にする
                return {"error": f"{type(e).__name__}: {e}"}

        request: JSONValue = {"name": criterion.name, "args": dict(criterion.args)}
        response = recorder.call("metric", [*key, criterion.name], request, live)
        assert isinstance(response, dict)
        if "error" in response:
            results[criterion.name] = MetricResult(None, False, str(response["error"]))
            continue
        value = response["value"]
        if not isinstance(value, bool | int | float):
            results[criterion.name] = MetricResult(
                None, False, f"値が真偽値でも数でもない: {value!r}"
            )
            continue
        results[criterion.name] = MetricResult(value, satisfies(criterion, value))
    return results


def _file_section(path: str, view: SnapshotReader, snapshot: Snapshot, store: BlobStore) -> str:
    data = view.read_bytes(path)
    try:
        return f"## ファイル {path}\n{data.decode('utf-8')}"
    except UnicodeDecodeError:
        digest = snapshot.files[path]
        return f"## ファイル {path}\n（文字として読めない: {len(data)} バイト、sha256 {digest}）"


def state_document(
    header: str,
    paths: Sequence[str],
    memory_names: Sequence[str],
    snapshot: Snapshot,
    store: BlobStore,
    limit: int,
) -> str:
    """状態文書（契約 2.4）。見出し行、宣言された成果物の内容、memory_out の値をこの順に並べる。"""
    view = SnapshotReader(snapshot, store)
    sections = [header]
    seen: set[str] = set()
    for entry in paths:
        files = view.list_files(entry) if entry.endswith("/") else [entry]
        if entry.endswith("/") and not files:
            sections.append(f"## ファイル {entry}\n（無い）")
        for path in files:
            if path in seen:
                continue
            seen.add(path)
            if view.exists(path):
                sections.append(_file_section(path, view, snapshot, store))
            else:
                sections.append(f"## ファイル {path}\n（無い）")
    for name in memory_names:
        value = json.dumps(snapshot.memory.get(name), ensure_ascii=False, sort_keys=True)
        sections.append(f"## 記憶 {name}\n{value}")
    document = "\n\n".join(sections)
    if len(document) > limit:
        notice = f"\n\n（ここで切り詰めた。元の長さ {len(document)} 文字）"
        document = document[: max(0, limit - len(notice))] + notice
    return document


def options(goal: Goal, end_states: Sequence[EndState], include_goal: bool) -> list[Option]:
    """分類の選択肢（契約 2.2）。指標をすべて満たした時だけ goal を含める。"""
    head = [Option(GOAL, goal.qualitative)] if include_goal else []
    return head + [Option(e.id, e.description) for e in end_states]


@dataclass(frozen=True)
class Evaluation:
    outcome: str
    metrics: dict[str, MetricResult]
    options: tuple[str, ...]
    classification: Classification | None


def classify(
    classifier: Classifier,
    document: str,
    choices: Sequence[Option],
    threshold: float,
    recorder: Recorder,
    key: Key,
) -> tuple[str, Classification]:
    """分類器に選ばせ、結果を評価の結果に写す。閾値未満と選択肢外は unknown。"""

    def live() -> JSONValue:
        # 分類器の例外と、0〜1 の有限の数でない確信度は「答え無し」（契約 2.2）
        try:
            c = classifier.classify(document, choices)
            confidence = float(c.confidence)
        except Exception:
            return {"choice": None, "confidence": 0.0}
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            return {"choice": None, "confidence": 0.0}
        return {"choice": c.choice, "confidence": confidence}

    request: JSONValue = {
        "state": document,
        "options": [{"id": o.id, "description": o.description} for o in choices],
    }
    response = recorder.call("classify", key, request, live)
    assert isinstance(response, dict)
    choice = response["choice"]
    confidence = response["confidence"]
    assert choice is None or isinstance(choice, str)
    assert isinstance(confidence, int | float)
    result = Classification(choice, float(confidence))
    ids = {o.id for o in choices}
    if result.choice is None or result.choice not in ids or result.confidence < threshold:
        return UNKNOWN, result
    return result.choice, result
