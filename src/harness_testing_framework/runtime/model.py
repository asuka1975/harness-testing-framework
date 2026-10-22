"""ワークフロー定義の実行用のモデル。検査を通った定義から作る不変の値。"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from harness_testing_framework.contract import JSONValue


def covered_by(path: str, entries: Sequence[str]) -> bool:
    """ファイル path が成果物の宣言 entries のどれかに当たるか。

    / で終わる宣言はディレクトリ全体を表す。
    """
    return any(path == e or (e.endswith("/") and path.startswith(e)) for e in entries)


@dataclass(frozen=True)
class Criterion:
    """goal の quantitative の一項目。"""

    name: str
    description: str
    equals: bool | float | None
    min: float | None
    max: float | None
    args: Mapping[str, JSONValue]


@dataclass(frozen=True)
class Goal:
    """ステージかフェーズの goal。qualitative は記述、criteria は quantitative の各指標の基準。"""

    qualitative: str
    criteria: tuple[Criterion, ...]


@dataclass(frozen=True)
class EndState:
    """end_state の一項目（unknown を含む）。id と、分類器に渡す記述。"""

    id: str
    description: str


@dataclass(frozen=True)
class Rollback:
    """rollback の一項目。ステージ stage の end_state state から target へ、記憶 carry を持って戻る。max 回まで。"""

    stage: str
    state: str
    target: str
    carry: tuple[str, ...]
    max: int


@dataclass(frozen=True)
class Stage:
    id: str
    name: str
    description: str
    phase: str
    position: int
    awaits_user: bool
    reads: tuple[str, ...]
    writes: tuple[str, ...]
    memory_in: tuple[str, ...]
    memory_out: tuple[str, ...]
    goal: Goal
    end_states: tuple[EndState, ...]
    rollbacks: Mapping[str, Rollback] = field(default_factory=dict)


@dataclass(frozen=True)
class Phase:
    """フェーズ。stages はそのフェーズのステージの id（順に）。goal はゲートの基準。"""

    id: str
    name: str
    description: str
    goal: Goal
    stages: tuple[str, ...]


@dataclass(frozen=True)
class Workflow:
    name: str
    description: str
    inputs: tuple[str, ...]
    phases: tuple[Phase, ...]
    stages: tuple[Stage, ...]

    def stage(self, stage_id: str) -> Stage:
        for s in self.stages:
            if s.id == stage_id:
                return s
        raise KeyError(stage_id)

    def phase(self, phase_id: str) -> Phase:
        for p in self.phases:
            if p.id == phase_id:
                return p
        raise KeyError(phase_id)

    def next_stage(self, stage_id: str) -> Stage | None:
        position = self.stage(stage_id).position
        return self.stages[position + 1] if position + 1 < len(self.stages) else None

    def is_last_in_phase(self, stage_id: str) -> bool:
        stage = self.stage(stage_id)
        return self.phase(stage.phase).stages[-1] == stage_id

    @property
    def scope(self) -> tuple[str, ...]:
        """スナップショットが持つ範囲（inputs と全ステージの writes）。"""
        entries = list(self.inputs)
        for s in self.stages:
            entries += [w for w in s.writes if w not in entries]
        return tuple(entries)

    @property
    def phase_order(self) -> tuple[str, ...]:
        return tuple(p.id for p in self.phases)


def _goal(doc: Mapping[str, Any]) -> Goal:
    criteria = tuple(
        Criterion(
            name=name,
            description=c["description"],
            equals=c.get("equals"),
            min=c.get("min"),
            max=c.get("max"),
            args=MappingProxyType(dict(c.get("args", {}))),
        )
        for name, c in doc["quantitative"].items()
    )
    return Goal(doc["qualitative"], criteria)


def build_workflow(doc: Mapping[str, Any]) -> Workflow:
    """検査を通ったワークフロー定義の文書からモデルを作る。"""
    w = doc["workflow"]
    phases: list[Phase] = []
    stages: list[Stage] = []
    for p in w["phases"]:
        for s in p["stages"]:
            art = s["artifacts"]
            rollbacks = {
                rb["state"]: Rollback(
                    stage=s["id"],
                    state=rb["state"],
                    target=rb["stage"],
                    carry=tuple(rb.get("carry", [])),
                    max=rb["max"],
                )
                for rb in s["rollback"]
            }
            stages.append(
                Stage(
                    id=s["id"],
                    name=s["name"],
                    description=s["description"],
                    phase=p["id"],
                    position=len(stages),
                    awaits_user=bool(s.get("awaits_user", False)),
                    reads=tuple(art.get("reads", [])),
                    writes=tuple(art.get("writes", [])),
                    memory_in=tuple(art.get("memory_in", [])),
                    memory_out=tuple(art.get("memory_out", [])),
                    goal=_goal(s["goal"]),
                    end_states=tuple(EndState(e["id"], e["description"]) for e in s["end_state"]),
                    rollbacks=MappingProxyType(rollbacks),
                )
            )
        phases.append(
            Phase(
                id=p["id"],
                name=p["name"],
                description=p["description"],
                goal=_goal(p["goal"]),
                stages=tuple(s["id"] for s in p["stages"]),
            )
        )
    return Workflow(
        name=w["name"],
        description=w["description"],
        inputs=tuple(w.get("inputs", [])),
        phases=tuple(phases),
        stages=tuple(stages),
    )
