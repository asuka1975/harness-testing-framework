"""software-factory のテストの設定。

- tests/fixtures/.code/ の下のコードベースのフィクスチャには test_*.py があり、意図的に失敗するテストを含む。
  それらはステージ本体が作業領域に写し、指標が一時ディレクトリで走らせるもので、このテストの対象ではないので収集しない
- 多数の実行の集まりは、分布テスト、独立性検証、マルコフ合成の実測、分類器の検証で共有する（一つ作るのに十数秒かかる）
"""

from pathlib import Path

import pytest
from software_factory.stages.probabilistic import run_set

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.stages import (
    RunSet,
    load_expectations,
    runs_from_environment,
)

collect_ignore = ["fixtures"]

EXPECTATIONS = Path(__file__).parent / "expectations"


@pytest.fixture(scope="session")
def markov_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[RunSet, BlobStore]:
    """expectations/markov.yaml の回数と種での、markov の本体の実行。"""
    expectations = load_expectations(EXPECTATIONS / "markov.yaml")
    runs = runs_from_environment(expectations.runs)
    return run_set("markov", runs, expectations.seed, tmp_path_factory.mktemp("markov"))


@pytest.fixture(scope="session")
def divergent_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[RunSet, BlobStore]:
    """divergent の本体の実行（独立性検証）。"""
    return run_set(
        "divergent", runs_from_environment(400), 30000, tmp_path_factory.mktemp("divergent")
    )
