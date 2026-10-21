"""決定論テストと契約適合テストの偽物（contract/conformance/README.md）。"""

import re
import shutil
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

from harness_testing_framework.contract import (
    AwaitingAnswer,
    AwaitingDecision,
    Classification,
    Decision,
    Escalation,
    JSONValue,
    MetricError,
    Option,
    Question,
    SnapshotView,
    StageContext,
)
from harness_testing_framework.runtime.runner import decision_from_json

_HEADER = re.compile(r"\A# 評価: (stage|phase) (\S+) visit (\d+)$", re.M)


def evaluation_target(state: str) -> tuple[str, str, int] | None:
    """状態文書の見出し行（契約 2.4）から、評価の対象（scope、id、訪問の回数）を読む。"""
    m = _HEADER.match(state)
    return (m.group(1), m.group(2), int(m.group(3))) if m else None


def _classification(entry: Mapping[str, Any]) -> Classification:
    return Classification(entry["choice"], float(entry["confidence"]))


class ScriptedClassifier:
    """台本どおりに分類する。台本に無いか、選んだ id が選択肢に無ければ「答え無し」。"""

    def __init__(
        self, stages: Mapping[str, Mapping[str, Any]], gates: Mapping[str, Mapping[str, Any]]
    ) -> None:
        self._stages = {k: _classification(v) for k, v in stages.items()}
        self._gates = {k: _classification(v) for k, v in gates.items()}

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        target = evaluation_target(state)
        if target is None:
            return Classification(None, 0.0)
        scope, target_id, visit = target
        table = self._stages if scope == "stage" else self._gates
        result = table.get(f"{target_id}#{visit}")
        if result is None or result.choice not in {o.id for o in options}:
            return Classification(None, 0.0)
        return result


class _Script:
    def __init__(self, entries: Sequence[Mapping[str, Any]]) -> None:
        self._entries = list(entries)
        self._index = 0

    def next_entry(self) -> Mapping[str, Any] | None:
        if self._index >= len(self._entries):
            return None
        entry = self._entries[self._index]
        self._index += 1
        return entry


class ScriptedOperator(_Script):
    """運用者の台本。{"kind": "defer"} は選択の保留。"""

    def decide(self, escalation: Escalation) -> Decision:
        entry = self.next_entry()
        if entry is None:
            raise LookupError(f"運用者の台本が尽きた: {escalation}")
        if entry["kind"] == "defer":
            raise AwaitingDecision()
        return decision_from_json(entry)


class ScriptedUser(_Script):
    """ユーザーの台本。{"defer": true} は回答の保留。"""

    def ask(self, question: Question) -> str:
        entry = self.next_entry()
        if entry is None:
            raise LookupError(f"ユーザーの台本が尽きた: {question.text}")
        if entry.get("defer"):
            raise AwaitingAnswer(question)
        return str(entry["answer"])


class ScriptedBody:
    """訪問ごとの台本どおりに作業領域と記憶を変える偽のステージ本体。全ステージで共有できる。"""

    def __init__(
        self, visits: Mapping[str, Mapping[str, Any]], fixtures: Path | None = None
    ) -> None:
        self._visits = visits
        self._fixtures = fixtures

    def __call__(self, context: StageContext) -> None:
        key = f"{context.stage_id}#{context.visit}"
        script = self._visits.get(key)
        if script is None:
            raise LookupError(f"台本に無い訪問 {key}")
        for text in script.get("ask", []):
            context.user_io.ask(Question(text))
        if "fixture" in script:
            if self._fixtures is None:
                raise LookupError("フィクスチャの置き場が与えられていない")
            shutil.copytree(
                self._fixtures / script["fixture"], context.workspace, dirs_exist_ok=True
            )
        for path, content in script.get("files", {}).items():
            target = context.workspace / path
            if content is None:
                target.unlink(missing_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
        for name, value in script.get("memory", {}).items():
            context.write_memory(name, value)
        if script.get("raise") == "stage_error":
            raise RuntimeError(f"台本による例外 {key}")


class ConformanceRegistry:
    """契約適合テストの指標レジストリ（flag と number）。"""

    def names(self) -> Collection[str]:
        return ("flag", "number")

    def measure(self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float:
        path = args.get("path")
        if not isinstance(path, str):
            raise MetricError("args.path が無い")
        if name == "flag":
            return view.exists(path) and view.read_text(path).strip() == "true"
        if name == "number":
            try:
                return float(view.read_text(path))
            except (FileNotFoundError, ValueError) as e:
                raise MetricError(f"{path} を数として読めない: {e}") from e
        raise MetricError(f"指標 {name} は無い")


class Unreachable:
    """再生の検査で外の代わりに束縛する。呼ばれたら失敗する。"""

    class Called(AssertionError):
        pass

    def __init__(self, names: Collection[str] = ()) -> None:
        self._names = names

    def names(self) -> Collection[str]:
        return self._names

    def measure(self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float:
        raise Unreachable.Called(f"measure {name}")

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        raise Unreachable.Called("classify")

    def decide(self, escalation: Escalation) -> Decision:
        raise Unreachable.Called("decide")

    def ask(self, question: Question) -> str:
        raise Unreachable.Called("ask")
