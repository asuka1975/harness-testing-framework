"""E2E のカバレッジ計画（誘発と注入）。

各ステージの各クラス（goal、end_state、unknown）を一度は踏む（plan.md 第2節）。踏み方は二つ。

- 誘発（induce）: その状態を実際に表す成果物を本体に書かせ、分類もそれに合わせる。ハーネスが状態ごとに台本を与える
- 注入（inject）: 誘発の台本が無い状態は、goal の成果物のまま分類の結果だけをその状態にする

計画の各項目は、決定論テストと同じシナリオで、参照ランタイムで実行する。
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness_testing_framework.contract import MetricRegistry
from harness_testing_framework.runtime.model import Workflow
from harness_testing_framework.testing.harness.scenario import Expectation, Scenario, run_scenario

GOAL = {"choice": "goal", "confidence": 0.9}


@dataclass(frozen=True, order=True)
class Target:
    stage: str
    outcome: str


def coverage_targets(workflow: Workflow) -> list[Target]:
    """踏むべき (ステージ, クラス)。goal、unknown 以外の end_state、unknown の順。"""
    targets: list[Target] = []
    for stage in workflow.stages:
        targets.append(Target(stage.id, "goal"))
        targets += [Target(stage.id, e.id) for e in stage.end_states if e.id != "unknown"]
        targets.append(Target(stage.id, "unknown"))
    return targets


@dataclass(frozen=True)
class CoverageItem:
    targets: tuple[Target, ...]
    method: str
    scenario: Scenario

    @property
    def target(self) -> Target:
        return self.targets[0]


def _visits_bound(workflow: Workflow) -> int:
    return 2 + sum(rb.max for s in workflow.stages for rb in s.rollbacks.values())


def plan_coverage(
    workflow: Workflow,
    workflow_path: Path,
    *,
    goal: Mapping[str, Mapping[str, Any]],
    induce: Mapping[tuple[str, str], Mapping[str, Any]],
    inputs: Mapping[str, str],
    seed: int = 0,
) -> list[CoverageItem]:
    """カバレッジ計画を作る。goal はステージごとの goal の台本、induce は (ステージ, クラス) ごとの誘発の台本。

    最初の項目は全ステージが goal の実行（全ステージの goal を踏む）。続く各項目は、対象のステージの
    最初の訪問だけを対象のクラスにし、ほかの訪問は goal にする。escalate には中止で答える。
    """
    bound = _visits_bound(workflow)

    def base_visits() -> dict[str, dict[str, Any]]:
        return {
            f"{s.id}#{v}": {**goal[s.id], "classify": GOAL}
            for s in workflow.stages
            for v in range(1, bound + 1)
        }

    gates = {f"{p.id}#{v}": GOAL for p in workflow.phases for v in range(1, bound + 1)}
    common: dict[str, Any] = {
        "path": workflow_path,
        "workflow": workflow_path,
        "metrics": None,
        "seed": seed,
        "threshold": 0.5,
        "inputs": inputs,
        "gates": gates,
        "operator": [{"kind": "abort"}] * bound,
        "user": [{"answer": "カバレッジ計画の回答"}] * (10 * bound),
        "expect": Expectation(status="completed", trace=[]),
    }
    items = [
        CoverageItem(
            tuple(Target(s.id, "goal") for s in workflow.stages),
            "induce",
            Scenario(
                name="coverage-goal",
                description="全ステージが goal",
                visits=base_visits(),
                **common,
            ),
        )
    ]
    for target in coverage_targets(workflow):
        if target.outcome == "goal":
            continue
        visits = base_visits()
        classify = {"choice": target.outcome, "confidence": 0.9}
        key = f"{target.stage}#1"
        if (target.stage, target.outcome) in induce:
            method = "induce"
            visits[key] = {**induce[(target.stage, target.outcome)], "classify": classify}
        else:
            method = "inject"
            visits[key] = {**goal[target.stage], "classify": classify}
        name = f"coverage-{target.stage}-{target.outcome}"
        scenario = Scenario(
            name=name, description=f"{target} を{method}で踏む", visits=visits, **common
        )
        items.append(CoverageItem((target,), method, scenario))
    return items


@dataclass(frozen=True)
class CoverageReport:
    covered: list[Target]
    missing: list[Target]
    reached: dict[Target, bool]


def run_coverage(
    plan: list[CoverageItem],
    workdir: Path,
    *,
    registry: MetricRegistry,
    fixtures: Path | None = None,
) -> CoverageReport:
    """計画の各項目を実行し、踏んだ (ステージ, クラス) を集める。"""
    covered: set[Target] = set()
    reached: dict[Target, bool] = {}
    wanted: list[Target] = []
    for i, item in enumerate(plan):
        result = run_scenario(item.scenario, workdir / str(i), registry=registry, fixtures=fixtures)
        seen = {
            Target(str(e["stage"]), str(e["outcome"]))
            for e in result.trace
            if e["event"] == "evaluation" and e["scope"] == "stage"
        }
        covered |= seen
        for target in item.targets:
            reached[target] = target in seen
            wanted.append(target)
    return CoverageReport(
        sorted(covered), sorted(t for t in set(wanted) if t not in covered), reached
    )
