"""toy-minimal の確率的な偽ステージ本体（plan.md 第6節 F3）。

分布の設計値は tests/stochastic.yaml にある。本体は文脈の種だけを乱数の源にして変種を選び、
tests/fixtures/<ステージ>/<変種>/ を作業領域に写し、変種の記憶を書く。成果物の先頭にある印
`[[class <ステージ>=<クラス>]]` を MarkerClassifier が読む。
"""

import random
import shutil
from pathlib import Path
from typing import Any

import yaml

from harness_testing_framework.contract import StageContext
from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.harness import AbortOperator, AutoUser, MarkerClassifier
from harness_testing_framework.testing.stages import Expectations, RunSet, record_run, run_many
from toy_minimal.metrics import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
TABLE: dict[str, Any] = yaml.safe_load((ROOT / "tests" / "stochastic.yaml").read_text("utf-8"))
INPUTS = {
    "brief.txt": "新入社員向けに、勉強会の議事録の書き方を短いノートにまとめてほしい。".encode()
}


def _distribution(profile: str, stage: str, visit: int, note: str) -> dict[str, float]:
    table = TABLE["profiles"][profile][stage]
    if "after_ok" in table:
        # 査読は note.md の中身（write_note の変種）で分布が分かれる
        table = table["after_ok_b" if "抽象的な説明" in note else "after_ok"]
    dist: dict[str, float] = table["first" if visit == 1 else "again"]
    return dist


def choose_variant(profile: str, stage: str, visit: int, seed: int, note: str) -> str:
    """種だけから変種を一つ選ぶ。"""
    dist = _distribution(profile, stage, visit, note)
    names = sorted(dist)
    return random.Random(seed).choices(names, weights=[dist[n] for n in names])[0]


class StochasticBody:
    def __init__(self, profile: str) -> None:
        self.profile = profile

    def __call__(self, context: StageContext) -> None:
        note_path = context.workspace / "note.md"
        note = note_path.read_text("utf-8") if note_path.exists() else ""
        variant = choose_variant(self.profile, context.stage_id, context.visit, context.seed, note)
        shutil.copytree(
            FIXTURES / context.stage_id / variant, context.workspace, dirs_exist_ok=True
        )
        spec = TABLE["variants"][context.stage_id][variant]
        for name, value in spec.get("memory", {}).items():
            context.write_memory(name, value)


def runtime(profile: str, workdir: Path, threshold: float = 0.5) -> Runtime:
    """確率的な偽の本体、印を読む分類器、中止する運用者、その場で答えるユーザーで組み立てる。"""
    workflow = load_workflow(ROOT / "workflow.yaml", REGISTRY.names())
    body = StochasticBody(profile)
    return Runtime(
        workflow,
        {s.id: body for s in workflow.stages},
        registry=REGISTRY,
        classifier=MarkerClassifier(),
        operator=AbortOperator(),
        user_io=AutoUser(),
        store=BlobStore(workdir / "store"),
        workdir=workdir,
        threshold=threshold,
    )


def run_set(expectations: Expectations, workdir: Path) -> RunSet:
    """expectations の bindings.profile の本体で、expectations の回数と種で実行する。"""
    built = runtime(str(expectations.bindings["profile"]), workdir)
    return run_many(
        expectations.runs, expectations.seed, lambda seed: record_run(built, seed, INPUTS)
    )
