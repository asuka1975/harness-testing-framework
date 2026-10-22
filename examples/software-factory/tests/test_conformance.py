"""契約適合テスト。

このハーネスは参照ランタイムを使う。adopting.md 第9節は、自前のランタイムを用意する場合に contract/conformance/scenarios/
のすべてのシナリオを通すとするが、このハーネスが束縛して使うランタイムについても同じシナリオを通す
（adopting-gaps.md）。シナリオは合成のワークフローと契約適合テストの指標レジストリ（metrics: conformance）を使い、
ハーネスの指標や本体は使わない。ハーネスの本体が契約を守ること（宣言外のパスや記憶を変えない）は、test_stochastic.py の
多数の実行で確かめる。
"""

from pathlib import Path

import pytest
from software_factory.stages.deterministic import ROOT

from harness_testing_framework.testing.harness import load_scenario, run_scenario

CONFORMANCE = ROOT.parents[1] / "contract" / "conformance" / "scenarios"
PATHS = sorted(CONFORMANCE.glob("*.yaml"))


def test_the_conformance_suite_is_present() -> None:
    assert len(PATHS) >= 20


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_conformance_scenario(path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(path)
    result = run_scenario(scenario, tmp_path)
    assert result.problems == []
    assert result.summary == scenario.expect.trace
    assert result.status == scenario.expect.status
