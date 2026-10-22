"""契約適合テスト。

このハーネスは参照ランタイムを使うので、契約適合テストを自分で通す必要は無い（adopting.md 第9節、契約 第10節。判定の対象は
ランタイムの実装で、参照ランタイムはフレームワークの側で通してある）。ここでは、このハーネスが束縛する版の参照ランタイムに、
パッケージに同梱したシナリオ一式（conformance_scenarios()。pip で入れた環境でも同じ場所から読める）をかけて、版の取り違えが
無いことを安く確かめるだけにする。シナリオは合成のワークフローと契約適合テストの指標レジストリ（metrics: conformance）を使い、
ハーネスの指標や本体は使わない。

ハーネスの側が守ること（宣言外のパスや記憶を変えない、範囲外のファイルを作らない）は、ランタイムが実行のたびに検査する。
多数の実行に契約違反、本体の例外、範囲外のファイルの警告が一度も無いことを test_stochastic.py で確かめる。
"""

from pathlib import Path

import pytest

from harness_testing_framework.testing.harness import (
    conformance_scenarios,
    load_scenario,
    run_scenario,
)

PATHS = conformance_scenarios()


def test_the_conformance_suite_is_present() -> None:
    assert len(PATHS) >= 20


@pytest.mark.parametrize("path", PATHS, ids=[p.stem for p in PATHS])
def test_conformance_scenario(path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(path)
    result = run_scenario(scenario, tmp_path)
    assert result.problems == []
    assert result.summary == scenario.expect.trace
    assert result.status == scenario.expect.status
