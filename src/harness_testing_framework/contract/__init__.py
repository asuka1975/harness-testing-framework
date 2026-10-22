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
    "corpus_item.schema.json",
    "label.schema.json",
    "triage_item.schema.json",
    "triage_decision.schema.json",
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
    """ユーザーへの質問。text は質問の文、choices は選択肢（自由回答なら空）。"""

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
    """ステージ本体に渡す文脈。ここにある属性と操作だけを使う（ほかの名前はランタイムの内部のもの）。"""

    @property
    def stage_id(self) -> str:
        """このステージの id。"""
        ...

    @property
    def visit(self) -> int:
        """この実行でこのステージに入った回数（1 から）。"""
        ...

    @property
    def workspace(self) -> Path:
        """作業領域。ランタイムが訪問ごとに開始時スナップショットから作り、訪問の後に消す。"""
        ...

    @property
    def seed(self) -> int:
        """実行の種、ステージの id、訪問の回数から SHA-256 で導いた整数。

        確率的な振る舞いの唯一の乱数の源。`random.Random(seed)` にそのまま渡してよい。訪問ごとの種は
        ハッシュから導くので、互いに独立な一様の種とみなせる。
        """
        ...

    def read_memory(self, name: str) -> JSONValue:
        """memory_in に宣言した記憶を読む。値がまだ無ければ（carry で受け取っていなければ）None。

        宣言の無い名前を読むのは契約違反。
        """
        ...

    def write_memory(self, name: str, value: JSONValue) -> None:
        """memory_out に宣言した記憶を書く。宣言の無い名前を書くのは契約違反。"""
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
        """値を測る。測定できなければ MetricError を送出する。

        args はワークフロー定義の基準の args で、読み取り専用の Mapping（dict とは限らない。必要なら dict(args)
        で写す）。同じスナップショットと args には同じ値を返す。そのため、費用の高い測定の結果は、読むファイルの
        内容のハッシュと args を鍵にして覚えてよい。
        """
        ...


# --- 7.5 分類器 ---


@dataclass(frozen=True)
class Option:
    """分類の選択肢。id は goal か end_state の id、description はワークフロー定義の記述そのもの。"""

    id: str
    description: str


@dataclass(frozen=True)
class Classification:
    """分類の結果。choice は選んだ選択肢の id（答えられなければ None）、confidence は 0〜1 の確信度。"""

    choice: str | None
    confidence: float


class Classifier(Protocol):
    def classify(self, state: str, options: Sequence[Option]) -> Classification: ...


# --- 7.6 運用者 ---

type EscalationReason = Literal["max_exceeded", "unknown", "stage_error", "contract_violation"]


@dataclass(frozen=True)
class Edge:
    """rollback の辺。ステージ stage の end_state state から、ステージ target へ戻る。"""

    stage: str
    state: str
    target: str


@dataclass(frozen=True)
class Escalation:
    """escalate の状況。stage は escalate したステージ、outcome は評価の結果（評価の前の escalate なら None）。

    edge と count は、max を超えた辺と、それを通った回数（max 超過の時だけ）。message は補足（本体の例外や
    契約違反の内容など）。
    """

    reason: EscalationReason
    stage: str
    outcome: str | None
    edge: Edge | None
    count: int | None
    message: str = ""


@dataclass(frozen=True)
class Rerun:
    """再実行。escalate したステージを、その直近の開始時スナップショットから新しい訪問として実行し直す。"""


@dataclass(frozen=True)
class RollbackTo:
    """指定ステージへのロールバック。stage は escalate したステージ自身か、それより前のステージ。

    carry は持ち帰る記憶の名前で、戻り先の memory_in にあるものに限る。
    """

    stage: str
    carry: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContinueAsGoal:
    """goal 到達扱いで続行。note は注記（なぜ）、by は誰が（空ならランタイムが operator と書く）。

    成果物はそのまま後のステージとゲートに渡る。後のゲートの指標は免れないので、成果物が実際に基準を
    満たしていなければ、後のゲートで goal が選択肢から外れ、もう一度 escalate しうる。
    """

    note: str
    by: str = ""


@dataclass(frozen=True)
class Abort:
    """中止。実行を中止状態で終え、最後のスナップショットを残す。"""


type Decision = Rerun | RollbackTo | ContinueAsGoal | Abort


class AwaitingDecision(Exception):
    """運用者の選択がまだ無いことの合図（3.4）。ランタイムは実行を escalate 待ちで保存する。"""


class Operator(Protocol):
    def decide(self, escalation: Escalation) -> Decision: ...


__all__ = [
    "CONTRACT_VERSION",
    "SCHEMA_FILES",
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
