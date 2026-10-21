"""多数の実行の記録（分布テスト、独立性検証、マルコフ合成の入力）。"""

import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from harness_testing_framework.runtime.checkpoint import BlobStore, Snapshot, canonical_json, sha256
from harness_testing_framework.runtime.model import Stage, covered_by
from harness_testing_framework.runtime.runner import Runtime

type Event = Mapping[str, Any]


@dataclass(frozen=True)
class RunRecord:
    """一回の実行の記録。

    representatives は、ステージの評価の seq から、その評価の直前にステージが書いた
    成果物（writes に当たるファイル）の内容のハッシュへの対応。同じクラスの中の
    「代表」を見分けるのに使う（独立性検証）。
    """

    seed: int
    status: str
    events: Sequence[Event]
    representatives: Mapping[int, str] = field(default_factory=dict)

    @property
    def run_id(self) -> str:
        """実行の一意な id（実行記録の内容のハッシュの先頭 16 桁）。同じ種でも設定が違えば違う。"""
        return sha256(canonical_json([dict(e) for e in self.events]))[:16]

    def evaluations(self) -> Iterator[Event]:
        return (e for e in self.events if e["event"] == "evaluation")

    def visits(self, stage: str) -> int:
        """このステージを訪れた回数（訪問の番号の最大）。"""
        numbers = [
            int(e["visit"])
            for e in self.events
            if e["event"] in ("stage_start", "evaluation")
            and e.get("stage") == stage
            and e.get("scope", "stage") == "stage"
        ]
        return max(numbers, default=0)


@dataclass(frozen=True)
class RunSet:
    runs: Sequence[RunRecord]

    def __len__(self) -> int:
        return len(self.runs)


def writes_hash(stage: Stage, snapshot: Snapshot, store: BlobStore) -> str:
    """既定の代表の鍵: ステージが書いた成果物（writes に当たるファイル）の内容のハッシュ。"""
    written = {p: d for p, d in snapshot.files.items() if covered_by(p, stage.writes)}
    return sha256(canonical_json(written))


def record_run(
    runtime: Runtime,
    seed: int,
    inputs: Mapping[str, bytes],
    *,
    representative: Callable[[Stage, Snapshot, BlobStore], str] = writes_hash,
) -> RunRecord:
    """ランタイムで一回実行し、評価ごとに代表の鍵を添えて記録する。

    代表の鍵は、同じクラスの中の違う成果物を見分ける。既定は書いた成果物のハッシュで、偽の本体のように同じ
    成果物が繰り返し出る時に向く。LLM の出力のように毎回違う成果物では、意味の近いものを同じ鍵にまとめる関数を与える。
    中断や escalate 待ちで止まった実行は、その状態のまま記録する（運用者とユーザーは、その場で答える偽物を束縛しておく）。
    """
    result = runtime.start(seed, inputs)
    representatives: dict[int, str] = {}
    last_end: dict[str, str] = {}
    for event in result.events:
        if event["event"] == "stage_end" and event["error"] is None:
            last_end[str(event["stage"])] = str(event["snapshot"])
        if event["event"] == "evaluation" and event["scope"] == "stage":
            stage = runtime.workflow.stage(str(event["stage"]))
            snapshot = runtime.store.get_snapshot(last_end[stage.id])
            representatives[int(str(event["seq"]))] = representative(stage, snapshot, runtime.store)
    return RunRecord(seed, result.status, result.events, representatives)


def run_many(runs: int, seed: int, run_one: Callable[[int], RunRecord]) -> RunSet:
    """種 seed, seed + 1, ... で runs 回実行する。"""
    return RunSet([run_one(seed + i) for i in range(runs)])


def runs_from_environment(default: int) -> int:
    """実行の回数。環境変数 HTF_RUNS が default より大きければそれを使う。

    基準の幅は default の回数から決めてあるので、環境変数で回数を減らすことはできない（減らすと正しい基準が落ち、
    ずれた基準が通りやすくなる）。正の整数でない値は誤り。
    """
    value = os.environ.get("HTF_RUNS")
    if not value:
        return default
    runs = int(value)
    if runs <= 0:
        raise ValueError(f"HTF_RUNS は正の整数: {value}")
    return max(default, runs)
