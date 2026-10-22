"""E2E のカバレッジ計画とマルコフ合成（plan.md 第6節 F3）。手で計算できる合成のモデルで確かめる。"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from harness_testing_framework.contract import Question, StageContext
from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.e2e import (
    MarkovModel,
    ModelIncomplete,
    Target,
    compare_prediction,
    coverage_targets,
    estimate_model,
    plan_coverage,
    run_coverage,
    synthesize,
)
from harness_testing_framework.testing.harness import (
    AbortOperator,
    ConformanceRegistry,
    MarkerClassifier,
    RandomGateClassifier,
)
from harness_testing_framework.testing.stages import (
    RunRecord,
    RunSet,
    independence,
    record_run,
    run_many,
)

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = load_workflow(
    ROOT / "contract/conformance/workflows/basic.yaml", ConformanceRegistry().names()
)


def test_coverage_targets_are_every_stage_class() -> None:
    assert coverage_targets(WORKFLOW) == [
        Target("s1", "goal"),
        Target("s1", "unknown"),
        Target("s2", "goal"),
        Target("s2", "e2_back"),
        Target("s2", "unknown"),
        Target("s3", "goal"),
        Target("s3", "e3_back"),
        Target("s3", "e3_retry"),
        Target("s3", "unknown"),
    ]


def test_synthesis_with_stage_rollbacks_matches_hand_calculation() -> None:
    # s2 は毎回 1/2 で e2_back（max 2）。三回目の e2_back で escalate し、中止になる
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"goal": 0.5, "e2_back": 0.5},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    p = synthesize(model, WORKFLOW)
    assert p.status["completed"] == pytest.approx(1 - 0.5**3)
    assert p.status["aborted"] == pytest.approx(0.5**3)
    assert p.mean_visits["s1"] == pytest.approx(1.75)
    assert p.mean_visits["s2"] == pytest.approx(1.75)
    assert p.mean_visits["s3"] == pytest.approx(0.875)
    assert p.outcomes[("s2", "e2_back")] == pytest.approx(0.5 + 0.25 + 0.125)


def test_synthesis_with_gate_rollbacks_and_unknown_matches_hand_calculation() -> None:
    # 一回の試みは s1 が 0.9 で goal（0.1 で unknown → 中止）、p1 のゲートが 0.5 で通る。
    # ゲートの不合格は s2 の e2_back の辺で s1 へ戻る（max 2）
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 0.9, "unknown": 0.1},
            ("s2", 1): {"goal": 1.0},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 0.5, "e2_back": 0.5}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    p = synthesize(model, WORKFLOW)
    fail = 0.9 * 0.5
    assert p.status["completed"] == pytest.approx(fail * (1 + fail + fail**2))
    assert p.mean_visits["s1"] == pytest.approx(1 + fail + fail**2)
    assert p.mean_visits["s2"] == pytest.approx(0.9 * (1 + fail + fail**2))
    assert p.status["completed"] + p.status["aborted"] == pytest.approx(1.0)


def test_visit_buckets_use_the_last_bucket_for_later_visits() -> None:
    # 訪問 2 以降は e2_back が起きない。s2 の訪問は高々 2
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"e2_back": 1.0},
            ("s2", 2): {"goal": 1.0},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=2,
    )
    p = synthesize(model, WORKFLOW)
    assert p.status["completed"] == pytest.approx(1.0)
    assert p.mean_visits["s2"] == pytest.approx(2.0)


def test_only_abort_policy_is_supported() -> None:
    model = MarkovModel(stage={("s1", 1): {"goal": 1.0}}, gate={}, cap=1)
    with pytest.raises(ValueError, match="方針"):
        synthesize(model, WORKFLOW, policy="rerun")


def _run(evals: list[tuple[str, str, str, int, str]], status: str) -> RunRecord:
    events = [
        {
            "seq": i,
            "event": "evaluation",
            "scope": scope,
            "stage": stage,
            "phase": phase,
            "visit": visit,
            "outcome": outcome,
        }
        for i, (scope, stage, phase, visit, outcome) in enumerate(evals)
    ]
    events += [
        {"seq": len(evals), "event": "stage_start", "stage": stage, "visit": visit}
        for _, stage, _, visit, _ in evals
    ]
    return RunRecord(seed=0, status=status, events=events)


def test_estimate_model_and_compare() -> None:
    runs = RunSet(
        [
            _run(
                [
                    ("stage", "s1", "p1", 1, "goal"),
                    ("stage", "s2", "p1", 1, "e2_back"),
                    ("stage", "s1", "p1", 2, "goal"),
                ],
                "aborted",
            ),
            _run(
                [
                    ("stage", "s1", "p1", 1, "goal"),
                    ("stage", "s2", "p1", 1, "goal"),
                    ("phase", "s2", "p1", 1, "goal"),
                    ("stage", "s3", "p2", 1, "goal"),
                    ("phase", "s3", "p2", 1, "goal"),
                ],
                "completed",
            ),
        ]
    )
    model = estimate_model(runs, cap=2)
    assert model.stage[("s1", 1)] == {"goal": 1.0}
    assert model.stage[("s2", 1)] == {"e2_back": 0.5, "goal": 0.5}
    assert model.stage[("s1", 2)] == {"goal": 1.0}
    assert model.gate[("p1", 1)] == {"goal": 1.0}
    comparisons = compare_prediction(synthesize(model, WORKFLOW), runs)
    names = {c.quantity for c in comparisons}
    assert {"status:completed", "visits:s1"} <= names


def test_missing_distribution_is_reported() -> None:
    model = MarkovModel(stage={("s1", 1): {"goal": 1.0}}, gate={}, cap=1)
    with pytest.raises(ModelIncomplete, match="s2"):
        synthesize(model, WORKFLOW)


def test_compare_prediction_reports_a_mismatch() -> None:
    """予測と食い違う実測（全実行が s2 を一回で通って完了）に対して、不一致を出す。"""
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"goal": 0.5, "e2_back": 0.5},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    runs = RunSet(
        [
            _run(
                [
                    ("stage", "s1", "p1", 1, "goal"),
                    ("stage", "s2", "p1", 1, "goal"),
                    ("phase", "s2", "p1", 1, "goal"),
                    ("stage", "s3", "p2", 1, "goal"),
                    ("phase", "s3", "p2", 1, "goal"),
                ],
                "completed",
            )
        ]
        * 400
    )
    comparisons = {c.quantity: c for c in compare_prediction(synthesize(model, WORKFLOW), runs)}
    assert not comparisons["visits:s2"].within
    assert not comparisons["status:completed"].within
    assert "不一致" in comparisons["visits:s2"].line()


def test_visit_buckets_beyond_two() -> None:
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"e2_back": 1.0},
            ("s2", 2): {"e2_back": 1.0},
            ("s2", 3): {"goal": 1.0},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=3,
    )
    p = synthesize(model, WORKFLOW)
    assert p.status["completed"] == pytest.approx(1.0)
    assert p.mean_visits["s2"] == pytest.approx(3.0)


def test_missing_bucket_falls_back_to_the_lower_one() -> None:
    """観測の無い区分は、下の区分の分布を使う（文書に書いた規則）。"""
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"goal": 0.5, "e2_back": 0.5},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=3,
    )
    assert synthesize(model, WORKFLOW).status["completed"] == pytest.approx(1 - 0.5**3)


def test_estimate_model_respects_cap() -> None:
    runs = RunSet(
        [
            _run(
                [
                    ("stage", "s2", "p1", 1, "goal"),
                    ("stage", "s2", "p1", 2, "e2_back"),
                    ("stage", "s2", "p1", 3, "goal"),
                ],
                "completed",
            ),
        ]
    )
    assert set(estimate_model(runs, cap=1).stage) == {("s2", 1)}
    assert estimate_model(runs, cap=1).stage[("s2", 1)] == pytest.approx(
        {"goal": 2 / 3, "e2_back": 1 / 3}
    )
    assert set(estimate_model(runs, cap=3).stage) == {("s2", 1), ("s2", 2), ("s2", 3)}


def test_synthesis_gives_expected_evaluations_per_visit_bucket() -> None:
    """訪問の区分ごとの評価の回数の期待値（visit や from_visit で絞った基準の分母 E[n]）。手計算と比べる。"""
    half = {"goal": 0.5, "e2_back": 0.5}
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): half,
            ("s2", 2): half,
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=2,
    )
    p = synthesize(model, WORKFLOW)
    # s2 の訪問 1 は必ず、訪問 2 は 1/2、訪問 3 は 1/4（区分 2 に入る）。s1 も同じ
    assert p.evaluations[("stage", "s2", 1)] == pytest.approx(1.0)
    assert p.evaluations[("stage", "s2", 2)] == pytest.approx(0.75)
    assert p.evaluations[("stage", "s1", 2)] == pytest.approx(0.75)
    assert p.visit_outcomes[("stage", "s2", 1, "e2_back")] == pytest.approx(0.5)
    assert p.visit_outcomes[("stage", "s2", 2, "goal")] == pytest.approx(0.25 + 0.125)
    # ゲートの訪問は最終ステージの訪問の回数。p1 は s2 が goal の時だけ評価する
    assert p.evaluations[("phase", "p1", 1)] == pytest.approx(0.5)
    assert p.evaluations[("phase", "p1", 2)] == pytest.approx(0.375)
    assert p.evaluations[("phase", "p2", 1)] == pytest.approx(0.875)
    assert ("phase", "p2", 2) not in p.evaluations


def test_per_visit_expectations_add_up_to_the_totals() -> None:
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 0.9, "unknown": 0.1},
            ("s2", 1): {"goal": 0.6, "e2_back": 0.4},
            ("s2", 2): {"goal": 0.8, "e2_back": 0.2},
            ("s3", 1): {"goal": 0.5, "e3_back": 0.3, "e3_retry": 0.2},
            ("s3", 3): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 0.7, "e2_back": 0.3}, ("p2", 1): {"goal": 1.0}},
        cap=3,
    )
    p = synthesize(model, WORKFLOW)
    for stage, mean in p.mean_visits.items():
        total = sum(v for (s, t, _), v in p.evaluations.items() if s == "stage" and t == stage)
        assert total == pytest.approx(mean)
    for (stage, outcome), mean in p.outcomes.items():
        total = sum(
            v
            for (s, t, _, o), v in p.visit_outcomes.items()
            if s == "stage" and t == stage and o == outcome
        )
        assert total == pytest.approx(mean)
    assert {b for (_, _, b) in p.evaluations} <= {1, 2, 3}


class _Simulator:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def ask(self, question: Question) -> str:
        self.asked.append(question.text)
        return "シミュレータの回答"


def test_coverage_runs_can_bind_a_user_simulator(tmp_path: Path) -> None:
    """run_coverage に user を与えると、awaits_user のステージの goal の台本が尋ねる先になる。"""
    goal: dict[str, dict[str, Any]] = {
        "s1": {
            "files": {"s1.txt": "s1", "s1.flag": "true"},
            "ask": ["主題は何か"],
            "answers_to": "s1.txt",
        },
        "s2": {"files": {"s2.txt": "s2", "s2.flag": "true", "gate1.flag": "true"}},
        "s3": {"files": {"s3.txt": "s3", "s3.flag": "true", "gate2.num": "0"}},
    }
    path = ROOT / "contract/conformance/workflows/basic.yaml"
    plan = plan_coverage(WORKFLOW, path, goal=goal, induce={}, inputs={"in.txt": "依頼"})
    simulator = _Simulator()
    report = run_coverage(plan, tmp_path, registry=ConformanceRegistry(), user=simulator)
    assert report.missing == []
    # s1 の最初の訪問は、どの項目でも尋ねる
    assert len(simulator.asked) >= len(plan)


def test_synthesis_gives_the_variance_of_visit_counts() -> None:
    """一回の実行の中での訪問の回数の分散（mean_visits の基準の幅の根拠）。手計算と比べる。"""
    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 1.0},
            ("s2", 1): {"goal": 0.5, "e2_back": 0.5},
            ("s3", 1): {"goal": 1.0},
        },
        gate={("p1", 1): {"goal": 1.0}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    p = synthesize(model, WORKFLOW)
    # s2 の訪問の回数は 1, 2, 3 がそれぞれ 1/2, 1/4, 1/4（三回目の e2_back で中止）
    mean = 0.5 * 1 + 0.25 * 2 + 0.25 * 3
    assert p.mean_visits["s2"] == pytest.approx(mean)
    assert p.visits_variance["s2"] == pytest.approx(0.5 * 1 + 0.25 * 4 + 0.25 * 9 - mean**2)
    # s3 は 0 回か 1 回（ベルヌーイ）
    assert p.visits_variance["s3"] == pytest.approx(0.875 * 0.125)
    assert p.visits_variance["s1"] == pytest.approx(p.visits_variance["s2"])


def test_visit_variance_matches_runs_simulated_from_the_model() -> None:
    """ゲートの戻りと unknown を含むモデルで、分散を厳密な列挙と標本で比べる。"""
    import random

    model = MarkovModel(
        stage={
            ("s1", 1): {"goal": 0.9, "unknown": 0.1},
            ("s2", 1): {"goal": 0.6, "e2_back": 0.4},
            ("s3", 1): {"goal": 0.5, "e3_back": 0.3, "e3_retry": 0.2},
        },
        gate={("p1", 1): {"goal": 0.7, "e2_back": 0.3}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    p = synthesize(model, WORKFLOW)
    rng = random.Random(0)
    maxes = {(s.id, rb.state): rb.max for s in WORKFLOW.stages for rb in s.rollbacks.values()}

    def draw(dist: Mapping[str, float]) -> str:
        r, acc = rng.random(), 0.0
        for k, v in dist.items():
            acc += v
            if r < acc:
                return k
        return k

    samples: dict[str, list[int]] = {s.id: [] for s in WORKFLOW.stages}
    for _ in range(40000):
        visits = dict.fromkeys(samples, 0)
        counts: dict[tuple[str, str], int] = {}
        stage: str | None = "s1"
        while stage is not None:
            visits[stage] += 1
            outcome = draw(model.stage_distribution(stage, 1))
            if outcome == "goal" and WORKFLOW.is_last_in_phase(stage):
                outcome = draw(model.gate_distribution(WORKFLOW.stage(stage).phase, 1))
            if outcome == "goal":
                following = WORKFLOW.next_stage(stage)
                stage = None if following is None else following.id
            elif outcome == "unknown" or counts.get((stage, outcome), 0) >= maxes[(stage, outcome)]:
                stage = None
            else:
                counts[(stage, outcome)] = counts.get((stage, outcome), 0) + 1
                stage = WORKFLOW.stage(stage).rollbacks[outcome].target
        for s, v in visits.items():
            samples[s].append(v)
    for s, values in samples.items():
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        assert p.mean_visits[s] == pytest.approx(mean, abs=0.03)
        assert p.visits_variance[s] == pytest.approx(variance, rel=0.05, abs=0.01)


def _goal_body(context: StageContext) -> None:
    n = context.stage_id[-1]
    (context.workspace / f"s{n}.txt").write_text(n)
    (context.workspace / f"s{n}.flag").write_text("true")
    if n == "2":
        (context.workspace / "gate1.flag").write_text("true")
        context.write_memory("m21", "直すところ")
    if n == "3":
        (context.workspace / "gate2.num").write_text("0")


def test_random_gate_classifier_shakes_gates_independently_of_artifacts(tmp_path: Path) -> None:
    """ゲートの答えを実行ごとの乱数で決める偽の分類器。ゲートの分布はクラスの中の代表によらないので、
    独立性検証は違反を出さず、ゲートの分布を持つマルコフ合成が実測と合う。"""
    store = BlobStore(tmp_path / "store")

    def run_one(seed: int) -> RunRecord:
        runtime = Runtime(
            WORKFLOW,
            {s.id: _goal_body for s in WORKFLOW.stages},
            registry=ConformanceRegistry(),
            classifier=RandomGateClassifier(
                MarkerClassifier(), seed, {"p1": {"goal": 0.5, "e2_back": 0.5}}
            ),
            operator=AbortOperator(),
            store=store,
            workdir=tmp_path,
        )
        return record_run(runtime, seed, {"in.txt": b"x"})

    runs = run_many(400, 0, run_one)
    gates = [
        e["outcome"]
        for r in runs.runs
        for e in r.evaluations()
        if e["scope"] == "phase" and e["phase"] == "p1"
    ]
    share = gates.count("e2_back") / len(gates)
    assert abs(share - 0.5) < 4 * (0.25 / len(gates)) ** 0.5
    # 同じ種では同じ実行
    assert run_one(7).events == run_one(7).events
    model = MarkovModel(
        stage={(s.id, 1): {"goal": 1.0} for s in WORKFLOW.stages},
        gate={("p1", 1): {"goal": 0.5, "e2_back": 0.5}, ("p2", 1): {"goal": 1.0}},
        cap=1,
    )
    prediction = synthesize(model, WORKFLOW)
    assert prediction.status["completed"] == pytest.approx(1 - 0.5**3)
    assert all(c.within for c in compare_prediction(prediction, runs)), [
        c.line() for c in compare_prediction(prediction, runs) if not c.within
    ]
    assert "violated" not in {r.verdict for r in independence(runs)}
