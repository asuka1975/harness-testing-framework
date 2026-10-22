"""expectations（分布テストの基準）の読み込みと判定。

判定の規則: 観測した割合（または平均）が [min, max] に入れば通る。報告には
Wilson の 95% 区間とその幅を添え、実行の回数が基準の幅に対して足りるかを人が見られるようにする。
分母（条件に合う評価の数、または実行の数）が min_samples（既定 30）未満の基準は判定できず、通らない。
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.testing.stages.runs import RunSet, runs_from_environment

Z95 = 1.959963984540054


class ExpectationsInvalid(ValueError):
    """expectations が形式に適合しない、または基準が矛盾する。"""


@dataclass(frozen=True)
class Expectations:
    path: Path
    name: str
    description: str
    workflow: Path
    runs: int
    seed: int
    bindings: dict[str, Any]
    criteria: list[dict[str, Any]]


def load_expectations(path: Path) -> Expectations:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = load_contract_schema("expectations.schema.json")
    errors = list(Draft202012Validator(schema).iter_errors(doc))
    if errors:
        raise ExpectationsInvalid(f"{path}: " + "; ".join(e.message for e in errors))
    for criterion in doc["criteria"]:
        if criterion["min"] > criterion["max"]:
            raise ExpectationsInvalid(f"{path}: min が max より大きい: {criterion}")
    return Expectations(
        path=path,
        name=doc["expectations"],
        description=doc["description"],
        workflow=(path.parent / doc["workflow"]).resolve(),
        runs=runs_from_environment(doc["runs"]),
        seed=doc["seed"],
        bindings=doc.get("bindings", {}),
        criteria=doc["criteria"],
    )


def wilson_interval(count: int, n: int, z: float = Z95) -> tuple[float, float]:
    """二項の割合の Wilson の区間。n が 0 なら [0, 1]。"""
    if n == 0:
        return 0.0, 1.0
    p = count / n
    denominator = n + z * z
    center = (count + z * z / 2) / denominator
    half = z * math.sqrt(n * p * (1 - p) + z * z / 4) / denominator
    return max(0.0, center - half), min(1.0, center + half)


@dataclass(frozen=True)
class CriterionResult:
    criterion: dict[str, Any]
    observed: float | None
    count: int
    n: int
    low: float
    high: float
    passed: bool
    note: str = ""

    def line(self) -> str:
        c = self.criterion
        target = c.get("target", c.get("status", ""))
        if "visit" in c:
            target += f" 訪問 {c['visit']}"
        if "from_visit" in c:
            target += f" 訪問 {c['from_visit']} 以降"
        if "outcome" in c:
            target += f" = {c['outcome']}"
        band = f"[{c['min']}, {c['max']}]"
        mark = "PASS" if self.passed else "FAIL"
        if self.observed is None or self.note:
            return f"{mark} {c['kind']} {target} {band}: {self.note}"
        interval = f"95% 区間 [{self.low:.3f}, {self.high:.3f}]（幅 {self.high - self.low:.3f}）"
        observed = f"観測 {self.observed:.3f}（{self.count}/{self.n}）"
        return f"{mark} {c['kind']} {target} {band}: {observed}、{interval}"


@dataclass(frozen=True)
class ExpectationReport:
    expectations: Expectations
    results: list[CriterionResult]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def lines(self) -> list[str]:
        return [r.line() for r in self.results]


def _visit_matches(criterion: dict[str, Any], visit: int) -> bool:
    if "visit" in criterion:
        return visit == int(criterion["visit"])
    if "from_visit" in criterion:
        return visit >= int(criterion["from_visit"])
    return True


MIN_SAMPLES = 30


def _judge(criterion: dict[str, Any], runs: RunSet) -> CriterionResult:
    result = _measure(criterion, runs)
    needed = int(criterion.get("min_samples", MIN_SAMPLES))
    if result.observed is not None and result.n < needed:
        note = f"件数 {result.n} が min_samples {needed} 未満で判定できない"
        return CriterionResult(
            criterion, result.observed, result.count, result.n, result.low, result.high, False, note
        )
    return result


def _measure(criterion: dict[str, Any], runs: RunSet) -> CriterionResult:
    kind = criterion["kind"]
    lo, hi = criterion["min"], criterion["max"]
    if kind == "mean_visits":
        values = [r.visits(criterion["target"]) for r in runs.runs]
        if not values:
            return CriterionResult(criterion, None, 0, 0, 0, 0, False, "実行が無く判定できない")
        mean = sum(values) / len(values)
        sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
        half = Z95 * sd / math.sqrt(len(values))
        passed = lo <= mean <= hi
        return CriterionResult(
            criterion, mean, sum(values), len(values), mean - half, mean + half, passed
        )
    if kind == "status_rate":
        n = len(runs.runs)
        count = sum(1 for r in runs.runs if r.status == criterion["status"])
    else:
        scope = criterion.get("scope", "stage")
        matching = [
            e
            for r in runs.runs
            for e in r.evaluations()
            if e["scope"] == scope
            and (e["stage"] if scope == "stage" else e["phase"]) == criterion["target"]
            and _visit_matches(criterion, int(e["visit"]))
        ]
        n = len(matching)
        count = sum(1 for e in matching if e["outcome"] == criterion["outcome"])
    if n == 0:
        return CriterionResult(
            criterion, None, 0, 0, 0, 1, False, "条件に合う評価が無く判定できない"
        )
    low, high = wilson_interval(count, n)
    observed = count / n
    return CriterionResult(criterion, observed, count, n, low, high, lo <= observed <= hi)


def evaluate_expectations(expectations: Expectations, runs: RunSet) -> ExpectationReport:
    """各基準を判定する。"""
    return ExpectationReport(expectations, [_judge(c, runs) for c in expectations.criteria])
