"""決定論テストと契約適合テストの偽物（contract/conformance/README.md）。"""

import random
import re
import shutil
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

from harness_testing_framework.contract import (
    AwaitingAnswer,
    AwaitingDecision,
    Classification,
    Classifier,
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
        answers = [context.user_io.ask(Question(text)) for text in script.get("ask", [])]
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
        if "answers_to" in script:
            (context.workspace / script["answers_to"]).write_text("\n".join(answers), "utf-8")
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


_MARKER = re.compile(r"\[\[class ([a-z][a-z0-9_-]*)=([a-z][a-z0-9_-]*)\]\]")


def marked_class(state: str) -> str | None:
    """状態文書の見出し行が示す評価の対象について、印 `[[class <対象>=<クラス>]]` が示すクラス（最後の印）。"""
    target = evaluation_target(state)
    if target is None:
        return None
    marked = [cls for tid, cls in _MARKER.findall(state) if tid == target[1]]
    return marked[-1] if marked else None


class MarkerClassifier:
    """成果物に埋めた印 `[[class <対象の id>=<クラス>]]` を読む偽の分類器。

    確率的な偽の本体と組む。

    状態文書の見出し行から評価の対象を読み、その対象の印が示すクラスを返す。印が無ければ、
    goal が選択肢にあれば goal（フェーズゲートの既定）、なければ答え無し。印は成果物の先頭に置く
    （状態文書の長さの上限で切り詰められないように）。
    """

    def __init__(self, confidence: float = 0.9) -> None:
        self.confidence = confidence

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        ids = {o.id for o in options}
        if evaluation_target(state) is None:
            return Classification(None, 0.0)
        choice = marked_class(state) or ("goal" if "goal" in ids else None)
        if choice not in ids:
            return Classification(None, 0.0)
        return Classification(choice, self.confidence)


class RandomGateClassifier:
    """フェーズゲートの答えを、成果物によらない乱数で決める偽の分類器。ステージの評価は base に任せる。

    gates はフェーズの id からクラスの分布（クラスから確率）。そのフェーズのゲートを評価するたびに、種 seed の
    乱数で分布からクラスを一つ引き、選択肢にあれば確信度 confidence で返す。選択肢に無いクラスを引いた時と、
    gates に無いフェーズは base に任せる。分類器は種を受け取らないので、実行ごとに、その実行の種で組み立てて
    束縛する（ランタイムを実行ごとに組み立てる）。

    ゲートの答えがクラスの中の代表（成果物）によらないので、独立性検証は違反を出さず、マルコフ合成はゲートの
    分布をそのまま扱える。成果物の印でゲートを落とすと、その成果物は「goal の中で下流が違う代表」になる。
    """

    def __init__(
        self,
        base: Classifier,
        seed: int,
        gates: Mapping[str, Mapping[str, float]],
        confidence: float = 0.9,
    ) -> None:
        self._base = base
        self._random = random.Random(seed)
        self._gates = gates
        self._confidence = confidence

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        target = evaluation_target(state)
        if target is None or target[0] != "phase" or target[1] not in self._gates:
            return self._base.classify(state, options)
        dist = self._gates[target[1]]
        r, acc, choice = self._random.random(), 0.0, None
        for cls, p in dist.items():
            acc += p
            if r < acc:
                choice = cls
                break
        if choice is None or choice not in {o.id for o in options}:
            return self._base.classify(state, options)
        return Classification(choice, self._confidence)


class AbortOperator:
    """escalate にはいつも中止で答える運用者（分布テストとマルコフ合成の既定の方針）。"""

    def decide(self, escalation: Escalation) -> Decision:
        from harness_testing_framework.contract import Abort

        return Abort()


class AutoUser:
    """いつも同じ回答をその場で返すユーザー。"""

    def __init__(self, answer: str = "自動の回答") -> None:
        self.answer = answer

    def ask(self, question: Question) -> str:
        return self.answer
