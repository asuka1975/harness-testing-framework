"""software-factory のテストの設定。

多数の実行の集まりは、分布テスト、独立性検証、マルコフ合成の実測、分類器の検証で共有する（一つ作るのに十数秒かかる）。

- markov_runs: expectations/markov.yaml の実行（ゲートはいつも goal）
- gated_runs: expectations/markov_gated.yaml の実行（assurance のゲートを、成果物によらず実行の種で揺らす）
- divergent_runs: 独立性検証が違反を検出するはずの本体の実行

tests/fixtures/ の下のコードベースのフィクスチャ（意図的に失敗するテストや、lint に反するコードを含む）は、リポジトリの
検査（ruff、mypy、pytest の収集）から外れる（adopting.md 第11節）ので、ここでは外さない。
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from software_factory.design import design_model
from software_factory.stages.probabilistic import WORKFLOW_MODEL, run_expectations, run_set

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.e2e import Prediction, synthesize
from harness_testing_framework.testing.stages import (
    RunSet,
    load_expectations,
    runs_from_environment,
)

EXPECTATIONS = Path(__file__).parent / "expectations"


def gates_of(name: str) -> Mapping[str, Mapping[str, float]] | None:
    """expectations の bindings にあるゲートの分布（RandomGateClassifier に与えるもの）。"""
    gates: Any = load_expectations(EXPECTATIONS / name).bindings.get("gates")
    if gates is None:
        return None
    return {str(p): {str(k): float(v) for k, v in d.items()} for p, d in gates.items()}


@pytest.fixture(scope="session")
def markov_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[RunSet, BlobStore]:
    """expectations/markov.yaml の回数と種での、markov の本体の実行。"""
    expectations = load_expectations(EXPECTATIONS / "markov.yaml")
    return run_expectations(expectations, tmp_path_factory.mktemp("markov"))


@pytest.fixture(scope="session")
def gated_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[RunSet, BlobStore]:
    """expectations/markov_gated.yaml の回数と種での、markov の本体とゲートの分布の実行。"""
    expectations = load_expectations(EXPECTATIONS / "markov_gated.yaml")
    return run_expectations(expectations, tmp_path_factory.mktemp("gated"))


@pytest.fixture(scope="session")
def divergent_runs(tmp_path_factory: pytest.TempPathFactory) -> tuple[RunSet, BlobStore]:
    """divergent の本体の実行（独立性検証）。"""
    return run_set(
        "divergent", runs_from_environment(400), 30000, tmp_path_factory.mktemp("divergent")
    )


@pytest.fixture(scope="session")
def design_prediction() -> Prediction:
    """設計値の MarkovModel の厳密な予測。分布テストの基準の根拠（E[n]、訪問の回数の分散）と、マルコフ合成の比較に使う。"""
    return synthesize(design_model("markov"), WORKFLOW_MODEL)


@pytest.fixture(scope="session")
def gated_prediction() -> Prediction:
    """ゲートの分布を足した設計値の MarkovModel の厳密な予測（expectations/markov_gated.yaml の根拠）。"""
    return synthesize(design_model("markov", gates_of("markov_gated.yaml")), WORKFLOW_MODEL)
