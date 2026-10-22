"""software-factory の決定論的な偽ステージ本体。

本体は訪問ごとの台本（tests/scenarios/ のシナリオ）に従い、tests/fixtures/ に用意した成果物を作業領域に写し、
記憶を書く。台本の解釈はフレームワークの ScriptedBody が行い、ここでは指標レジストリ（実在のツールで測る）と
フィクスチャの置き場を束縛する。
"""

from pathlib import Path

from harness_testing_framework.contract import UserIO
from harness_testing_framework.testing.harness import ScenarioResult, load_scenario, run_scenario
from software_factory.metrics import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "workflow.yaml"
FIXTURES = ROOT / "tests" / "fixtures"
SCENARIOS = ROOT / "tests" / "scenarios"
INPUTS = FIXTURES / "inputs"


def inputs() -> dict[str, bytes]:
    """ワークフローの inputs: 依頼（feature_request.md）と、変更前のコードベース（repo/）。tests/fixtures/inputs/ の写し。"""
    return {
        str(path.relative_to(INPUTS)): path.read_bytes()
        for path in sorted(INPUTS.rglob("*"))
        if path.is_file()
    }


def run(
    scenario_path: Path,
    workdir: Path,
    *,
    record: Path | None = None,
    replay: Path | None = None,
    user: UserIO | None = None,
) -> ScenarioResult:
    """シナリオを、実在のツールで測る指標レジストリとフィクスチャで実行する。

    user を与えると、台本の user の代わりにそのユーザーシミュレータ（ペルソナ）に尋ねる。
    """
    return run_scenario(
        load_scenario(scenario_path),
        workdir,
        registry=REGISTRY,
        fixtures=FIXTURES,
        record=record,
        replay=replay,
        user=user,
    )
