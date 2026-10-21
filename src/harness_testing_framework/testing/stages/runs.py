"""多数の実行の記録（分布テスト、独立性検証、マルコフ合成の入力）。"""

import os
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from harness_testing_framework.runtime.checkpoint import canonical_json, sha256
from harness_testing_framework.runtime.model import covered_by
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


def record_run(runtime: Runtime, seed: int, inputs: Mapping[str, bytes]) -> RunRecord:
    """ランタイムで一回実行し、代表のハッシュを添えて記録する。

    中断や escalate 待ちで止まった実行は、その状態のまま記録する（運用者とユーザーは、
    その場で答える偽物を束縛しておく）。
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
            written = {p: d for p, d in snapshot.files.items() if covered_by(p, stage.writes)}
            representatives[int(str(event["seq"]))] = sha256(canonical_json(written))
    return RunRecord(seed, result.status, result.events, representatives)


def run_many(runs: int, seed: int, run_one: Callable[[int], RunRecord]) -> RunSet:
    """種 seed, seed + 1, ... で runs 回実行する。"""
    return RunSet([run_one(seed + i) for i in range(runs)])


def runs_from_environment(default: int) -> int:
    """実行の回数。環境変数 HTF_RUNS があればそれを使う（CI では小さく、人は大きくできる）。"""
    value = os.environ.get("HTF_RUNS")
    return int(value) if value else default
