"""偽ステージ本体によるランナー検証のランナー（遷移の決定論テスト）と、契約適合テスト。"""

from harness_testing_framework.runtime.recorder import ReplayOnly
from harness_testing_framework.testing.harness.fakes import (
    AbortOperator,
    AutoUser,
    ConformanceRegistry,
    MarkerClassifier,
    ScriptedBody,
    ScriptedClassifier,
    ScriptedOperator,
    ScriptedUser,
    Unreachable,
    evaluation_target,
    marked_class,
)
from harness_testing_framework.testing.harness.scenario import (
    Expectation,
    Scenario,
    ScenarioInvalid,
    ScenarioResult,
    load_scenario,
    run_scenario,
    verify,
)
from harness_testing_framework.testing.harness.trace import (
    TRANSITION_KINDS,
    summarize,
    transition_coverage,
)

__all__ = [
    "TRANSITION_KINDS",
    "AbortOperator",
    "AutoUser",
    "ConformanceRegistry",
    "Expectation",
    "MarkerClassifier",
    "ReplayOnly",
    "Scenario",
    "ScenarioInvalid",
    "ScenarioResult",
    "ScriptedBody",
    "ScriptedClassifier",
    "ScriptedOperator",
    "ScriptedUser",
    "Unreachable",
    "evaluation_target",
    "load_scenario",
    "marked_class",
    "run_scenario",
    "summarize",
    "transition_coverage",
    "verify",
]
