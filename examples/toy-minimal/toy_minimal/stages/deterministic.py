"""toy-minimal の決定論的な偽ステージ本体。

本体は訪問ごとの台本（tests/scenarios/ のシナリオ）に従い、tests/fixtures/ に用意した成果物を
作業領域に写し、記憶を書く。台本の解釈はフレームワークの ScriptedBody が行い、ここでは
玩具のフィクスチャの置き場と指標レジストリを束縛する。
"""

from pathlib import Path

from harness_testing_framework.testing.harness import ScenarioResult, load_scenario, run_scenario
from toy_minimal.metrics import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
SCENARIOS = ROOT / "tests" / "scenarios"


def run(
    scenario_path: Path,
    workdir: Path,
    *,
    record: Path | None = None,
    replay: Path | None = None,
) -> ScenarioResult:
    """玩具のシナリオを、玩具の指標レジストリとフィクスチャで実行する。"""
    return run_scenario(
        load_scenario(scenario_path),
        workdir,
        registry=REGISTRY,
        fixtures=FIXTURES,
        record=record,
        replay=replay,
    )
