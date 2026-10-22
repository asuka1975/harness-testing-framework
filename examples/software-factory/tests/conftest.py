"""software-factory のテストの設定。

多数の実行の集まりは、分布テスト、独立性検証、マルコフ合成の実測、分類器の検証で共有する（一つ作るのに十数秒かかる）。

tests/fixtures/ の下のコードベースのフィクスチャ（意図的に失敗するテストや、lint に反するコードを含む）は、リポジトリの
検査（ruff、mypy、pytest の収集）から外れる（adopting.md 第11節）ので、ここでは外さない。
"""

from pathlib import Path

import pytest
from software_factory.design import design_model
from software_factory.stages.probabilistic import WORKFLOW_MODEL, run_set

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.e2e import Prediction, synthesize
from harness_testing_framework.testing.stages import (
    RunSet,
    load_expectations,
    runs_from_environment,
)

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


@pytest.fixture(scope="session")
def design_prediction() -> Prediction:
    """設計値の MarkovModel の厳密な予測。分布テストの基準の根拠（E[n]）と、マルコフ合成の比較に使う。"""
    return synthesize(design_model("markov"), WORKFLOW_MODEL)
