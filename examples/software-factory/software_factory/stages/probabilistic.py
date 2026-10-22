"""software-factory の確率的な偽ステージ本体。

分布の設計値は tests/stochastic.yaml にある。本体は文脈の種だけを乱数の源にして変種を選び、フィクスチャを作業領域に
写し、変種の記憶を書く。成果物の先頭にある印 `[[class <ステージ>=<クラス>]]` を MarkerClassifier が読む。

- intake は、依頼者（ペルソナのユーザーシミュレータ）に決まった三つの質問と、持ち帰った問い（記憶 intake_questions）を
  尋ね、回答で intake.md の「## 質問と回答」を書く。ペルソナは実行の種から選ぶ
- release は、carry を受けたか（記憶 missing_notes が空でない一覧か）で分布を選ぶ
- unit_test の変種 defect は、repo/src/ の実装の系統（tests/stochastic.yaml の families）でクラスとフィクスチャが分かれる
"""

import random
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from harness_testing_framework.contract import Classifier, Question, StageContext, UserIO
from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.harness import AbortOperator, MarkerClassifier
from harness_testing_framework.testing.stages import (
    Expectations,
    RunRecord,
    RunSet,
    record_run,
    run_many,
    runs_from_environment,
)
from software_factory.metrics import REGISTRY
from software_factory.personas import QUESTIONS, PersonaUser, persona_for
from software_factory.stages.deterministic import FIXTURES, ROOT, WORKFLOW, inputs

TABLE: dict[str, Any] = yaml.safe_load((ROOT / "tests" / "stochastic.yaml").read_text("utf-8"))
INPUTS = inputs()
CODE_STAGES = ("implement", "unit_test")
DISCOUNT = "repo/src/shopcart/discount.py"


def fixture_dir(stage: str, name: str) -> Path:
    """変種のフィクスチャのディレクトリ。コードを含むものは .code/ の下。"""
    return (FIXTURES / ".code" if stage in CODE_STAGES else FIXTURES) / stage / name


def condition(stage: str, visit: int, carried: bool) -> str:
    """分布の鍵。release は carry を受けたか、ほかは訪問の回数で決める。"""
    if stage == "release":
        return "with_carry" if carried else "without_carry"
    return "first" if visit == 1 else "again"


def choose_variant(profile: str, stage: str, key: str, seed: int) -> str:
    """種だけから変種を一つ選ぶ。"""
    dist: dict[str, float] = TABLE["profiles"][profile][stage][key]
    names = sorted(dist)
    return random.Random(seed).choices(names, weights=[dist[n] for n in names])[0]


def implementation_family(workspace: Path) -> str:
    """作業領域の repo/src/shopcart/discount.py が goal の実装のどの変種か。その系統を返す。"""
    path = workspace / DISCOUNT
    data = path.read_bytes() if path.exists() else None
    families: dict[str, str] = TABLE["families"]
    for variant, family in families.items():
        if (fixture_dir("implement", variant) / DISCOUNT).read_bytes() == data:
            return family
    raise LookupError(f"{DISCOUNT} が goal の実装のどの変種にも当たらない")


def resolve(stage: str, variant: str, workspace: Path) -> tuple[str, dict[str, Any]]:
    """変種から、写すフィクスチャの名前と、クラスと記憶の仕様。"""
    spec: dict[str, Any] = TABLE["variants"][stage][variant]
    if "by_family" in spec:
        resolved: dict[str, Any] = spec["by_family"][implementation_family(workspace)]
        return str(resolved["fixture"]), resolved
    return variant, spec


class StochasticBody:
    def __init__(self, profile: str) -> None:
        self.profile = profile

    def __call__(self, context: StageContext) -> None:
        stage = context.stage_id
        carried = stage == "release" and bool(context.read_memory("missing_notes"))
        variant = choose_variant(
            self.profile, stage, condition(stage, context.visit, carried), context.seed
        )
        name, spec = resolve(stage, variant, context.workspace)
        shutil.copytree(fixture_dir(stage, name), context.workspace, dirs_exist_ok=True)
        for key, value in spec.get("memory", {}).items():
            context.write_memory(key, value)


class IntakeBody(StochasticBody):
    """依頼者に尋ね、変種の intake.md の「## 質問と回答」を回答で書き換える。"""

    def __call__(self, context: StageContext) -> None:
        user = context.user_io
        if user is None:
            raise RuntimeError("intake にユーザー入出力が無い")
        carried = context.read_memory("intake_questions")
        extra = [q for q in carried if isinstance(q, str)] if isinstance(carried, list) else []
        questions = [*QUESTIONS, *extra]
        qa = "".join(f"- Q: {q}\n  A: {user.ask(Question(q))}\n" for q in questions)
        variant = choose_variant(
            self.profile, "intake", condition("intake", context.visit, False), context.seed
        )
        template = (fixture_dir("intake", variant) / "intake.md").read_text("utf-8")
        text = re.sub(
            r"(^## 質問と回答\n)(.*?)(?=^## |\Z)",
            lambda m: f"{m.group(1)}{qa}\n",
            template,
            flags=re.M | re.S,
        )
        (context.workspace / "intake.md").write_text(text, "utf-8")


WORKFLOW_MODEL = load_workflow(WORKFLOW, REGISTRY.names())


def runtime(
    profile: str,
    workdir: Path,
    *,
    seed: int = 0,
    store: BlobStore | None = None,
    classifier: Classifier | None = None,
    user: UserIO | None = None,
    threshold: float = 0.5,
) -> Runtime:
    """確率的な偽の本体、印を読む分類器、中止する運用者、種から選んだペルソナで組み立てる。"""
    bodies = {
        s.id: IntakeBody(profile) if s.id == "intake" else StochasticBody(profile)
        for s in WORKFLOW_MODEL.stages
    }
    return Runtime(
        WORKFLOW_MODEL,
        bodies,
        registry=REGISTRY,
        classifier=classifier if classifier is not None else MarkerClassifier(),
        operator=AbortOperator(),
        user_io=user if user is not None else PersonaUser(persona_for(seed)),
        store=store if store is not None else BlobStore(workdir / "store"),
        workdir=workdir,
        threshold=threshold,
    )


def run_set(
    profile: str,
    runs: int,
    seed: int,
    workdir: Path,
    *,
    classifier: Classifier | None = None,
    threshold: float = 0.5,
) -> tuple[RunSet, BlobStore]:
    """種 seed から runs 回実行する。ペルソナを種から選ぶので、実行ごとにランタイムを組み立て、置き場は共有する。"""
    store = BlobStore(workdir / "store")

    def one(s: int) -> RunRecord:
        built = runtime(
            profile, workdir, seed=s, store=store, classifier=classifier, threshold=threshold
        )
        return record_run(built, s, INPUTS)

    return run_many(runs, seed, one), store


def run_expectations(expectations: Expectations, workdir: Path) -> RunSet:
    """expectations の bindings.profile の本体で、expectations の回数（HTF_RUNS で増やせる）と種で実行する。"""
    count = runs_from_environment(expectations.runs)
    runs, _ = run_set(str(expectations.bindings["profile"]), count, expectations.seed, workdir)
    return runs
