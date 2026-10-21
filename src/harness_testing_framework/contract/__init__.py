"""ハーネス契約の Python 束縛。

言語に依存しない契約の文書は、リポジトリ最上位の contract/contract.md にある。
節の番号はその文書の節を指す。
"""

import json
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, Protocol

type JSONValue = bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None

CONTRACT_VERSION = "0.1"

# 正はリポジトリ最上位の contract/ にあり、ここにはその複製を同梱する（一致はテストで保証する）
SCHEMA_FILES = (
    "snapshot.schema.json",
    "trace.schema.json",
    "scenario.schema.json",
    "expectations.schema.json",
)


def load_contract_schema(name: str) -> dict[str, Any]:
    """同梱した契約の JSON Schema（SCHEMA_FILES のいずれか）を読む。"""
    if name not in SCHEMA_FILES:
        raise KeyError(name)
    schema: dict[str, Any] = json.loads(files(__package__).joinpath(name).read_text("utf-8"))
    return schema


# --- 7.3 ユーザー入出力 ---


@dataclass(frozen=True)
class Question:
    text: str
    choices: tuple[str, ...] = ()


class AwaitingAnswer(Exception):
    """回答がまだ無いことの合図（3.3）。ランタイムは実行を中断状態にする。"""

    def __init__(self, question: Question) -> None:
        super().__init__(question.text)
        self.question = question


class UserIO(Protocol):
    def ask(self, question: Question) -> str:
        """回答の文を返す。回答がまだ無ければ AwaitingAnswer を送出する。"""
        ...


# --- 7.4 LLM クライアント ---


class LLMClient(Protocol):
    def complete(self, request: JSONValue) -> JSONValue: ...


# --- 7.1 ステージ本体 ---


class StageContext(Protocol):
    @property
    def stage_id(self) -> str: ...

    @property
    def visit(self) -> int:
        """この実行でこのステージに入った回数（1 から）。"""
        ...

    @property
    def workspace(self) -> Path: ...

    @property
    def seed(self) -> int:
        """実行の種、ステージの id、訪問の回数から決定論的に導いた整数。"""
        ...

    def read_memory(self, name: str) -> JSONValue:
        """memory_in に宣言した記憶を読む。値が無ければ None。"""
        ...

    def write_memory(self, name: str, value: JSONValue) -> None:
        """memory_out に宣言した記憶を書く。"""
        ...

    @property
    def user_io(self) -> UserIO:
        """awaits_user を宣言したステージだけが使える。"""
        ...

    @property
    def llm(self) -> LLMClient:
        """recorder を経由した LLM クライアント。"""
        ...


class StageBody(Protocol):
    def __call__(self, context: StageContext) -> None: ...


# --- 7.2 指標レジストリ ---


class SnapshotView(Protocol):
    """読み取り専用のスナップショット。"""

    def exists(self, path: str) -> bool: ...

    def read_bytes(self, path: str) -> bytes: ...

    def read_text(self, path: str) -> str: ...

    def list_files(self, prefix: str = "") -> Sequence[str]:
        """prefix で始まるファイルのパスを辞書順に返す。"""
        ...

    def memory(self, name: str) -> JSONValue: ...

    def baseline(self) -> "SnapshotView | None":
        """比べる基準のスナップショット。ステージの指標ならそのステージの開始時、
        フェーズの指標ならフェーズの最初のステージの直近の開始時。"""
        ...


class MetricError(Exception):
    """指標を測定できない。評価ではその指標を未達とする。"""


class MetricRegistry(Protocol):
    def names(self) -> Collection[str]: ...

    def measure(self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float:
        """値を測る。測定できなければ MetricError を送出する。"""
        ...


# --- 7.5 分類器 ---


@dataclass(frozen=True)
class Option:
    id: str
    description: str


@dataclass(frozen=True)
class Classification:
    choice: str | None
    confidence: float


class Classifier(Protocol):
    def classify(self, state: str, options: Sequence[Option]) -> Classification: ...


# --- 7.6 運用者 ---

type EscalationReason = Literal["max_exceeded", "unknown", "stage_error", "contract_violation"]


@dataclass(frozen=True)
class Edge:
    stage: str
    state: str
    target: str


@dataclass(frozen=True)
class Escalation:
    reason: EscalationReason
    stage: str
    outcome: str | None
    edge: Edge | None
    count: int | None
    message: str = ""


@dataclass(frozen=True)
class Rerun:
    pass


@dataclass(frozen=True)
class RollbackTo:
    stage: str
    carry: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContinueAsGoal:
    note: str
    by: str = ""


@dataclass(frozen=True)
class Abort:
    pass


type Decision = Rerun | RollbackTo | ContinueAsGoal | Abort


class AwaitingDecision(Exception):
    """運用者の選択がまだ無いことの合図（3.4）。ランタイムは実行を escalate 待ちで保存する。"""


class Operator(Protocol):
    def decide(self, escalation: Escalation) -> Decision: ...


__all__ = [
    "CONTRACT_VERSION",
    "Abort",
    "AwaitingAnswer",
    "AwaitingDecision",
    "Classification",
    "Classifier",
    "ContinueAsGoal",
    "Decision",
    "Edge",
    "Escalation",
    "EscalationReason",
    "JSONValue",
    "LLMClient",
    "MetricError",
    "MetricRegistry",
    "Operator",
    "Option",
    "Question",
    "Rerun",
    "RollbackTo",
    "SnapshotView",
    "StageBody",
    "StageContext",
    "UserIO",
    "load_contract_schema",
]
