"""遷移行列の推定と独立性検証（plan.md 第2節「組み合わせテストはしない」、第6節 F3）。合成の実行で確かめる。"""

import random
from pathlib import Path
from typing import Any

import pytest

from harness_testing_framework.contract import StageContext
from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.harness import (
    AbortOperator,
    ConformanceRegistry,
    MarkerClassifier,
)
from harness_testing_framework.testing.stages import (
    RunRecord,
    RunSet,
    chi_square,
    entries,
    entry_dependence,
    independence,
    record_run,
    run_many,
    transition_matrix,
    transitions,
)

ROOT = Path(__file__).resolve().parents[1]


def _run(steps: list[tuple[Any, ...]], status: str = "completed") -> RunRecord:
    """steps: (ステージ, 結果, 代表[, 訪問[, スコープ]])。順に評価が起き、最後に run_end。
    スコープが phase の評価は、ステージの欄をフェーズの id として扱う。"""
    events: list[dict[str, Any]] = []
    reps: dict[int, str] = {}
    for i, step in enumerate(steps):
        stage, outcome, rep = step[:3]
        visit = step[3] if len(step) > 3 else 1
        scope = step[4] if len(step) > 4 else "stage"
        events.append(
            {
                "seq": i,
                "event": "evaluation",
                "scope": scope,
                "stage": stage,
                "phase": stage if scope == "phase" else "p",
                "visit": visit,
                "outcome": outcome,
            }
        )
        if rep is not None:
            reps[i] = rep
    events.append({"seq": len(steps), "event": "run_end", "status": status})
    return RunRecord(seed=0, status=status, events=events, representatives=reps)


def test_transitions_follow_the_next_evaluation_or_the_end() -> None:
    runs = RunSet([_run([("a", "goal", "r1"), ("b", "x", "q"), ("a", "goal", "r2")], "aborted")])
    got = [(t.state, t.representative, t.next) for t in transitions(runs)]
    assert got == [
        ("stage:a=goal", "r1", "stage:b=x"),
        ("stage:b=x", "q", "stage:a=goal"),
        ("stage:a=goal", "r2", "end:aborted"),
    ]


def test_transition_matrix_counts_and_probabilities() -> None:
    runs = RunSet(
        [_run([("a", "goal", None), ("b", "goal", None)])] * 3
        + [_run([("a", "goal", None), ("b", "x", None)])]
    )
    matrix = transition_matrix(runs)
    assert matrix["stage:a=goal"] == {"stage:b=goal": 0.75, "stage:b=x": 0.25}
    assert matrix["stage:b=goal"] == {"end:completed": 1.0}


def test_chi_square_known_value() -> None:
    # 2×2 の表 [[10, 20], [30, 40]]。期待度数 [[12, 18], [28, 42]] から手で計算した値
    expected = 4 / 12 + 4 / 18 + 4 / 28 + 4 / 42
    assert chi_square([[10, 20], [30, 40]]) == pytest.approx(expected)


def _two_groups(counts_a: dict[str, int], counts_b: dict[str, int]) -> RunSet:
    runs = []
    for rep, counts in (("A", counts_a), ("B", counts_b)):
        for nxt, n in counts.items():
            runs += [_run([("a", "goal", rep), ("b", nxt, None)])] * n
    return RunSet(runs)


def test_independent_when_downstream_distributions_agree() -> None:
    runs = _two_groups({"goal": 40, "x": 10}, {"goal": 40, "x": 10})
    [result] = [r for r in independence(runs) if r.state == "stage:a=goal"]
    assert result.verdict == "not_detected"
    assert result.p_value is not None and result.p_value > 0.5
    assert result.groups == {"A": 50, "B": 50}


def test_violated_when_downstream_distributions_differ() -> None:
    runs = _two_groups({"goal": 45, "x": 5}, {"goal": 20, "x": 30})
    [result] = [r for r in independence(runs) if r.state == "stage:a=goal"]
    assert result.verdict == "violated"
    assert result.p_value is not None and result.p_value < 0.01


def test_undetermined_with_one_representative_or_small_groups() -> None:
    one = RunSet([_run([("a", "goal", "A"), ("b", "goal", None)])] * 30)
    assert [r.verdict for r in independence(one) if r.state == "stage:a=goal"] == ["undetermined"]
    small = _two_groups({"goal": 5}, {"x": 5})
    [result] = [r for r in independence(small, min_group=10) if r.state == "stage:a=goal"]
    assert result.verdict == "undetermined"
    assert "代表" in result.note


def test_permutation_p_value_is_deterministic() -> None:
    runs = _two_groups({"goal": 30, "x": 20}, {"goal": 22, "x": 28})
    first = [r.p_value for r in independence(runs, seed=3)]
    assert first == [r.p_value for r in independence(runs, seed=3)]


def test_next_state_passes_through_gate_evaluations() -> None:
    runs = RunSet([_run([("a", "goal", "r"), ("g", "goal", None, 1, "phase"), ("b", "x", None)])])
    got = [(t.state, t.next) for t in transitions(runs)]
    assert got[0] == ("stage:a=goal", "phase:g=goal > stage:b=x")
    assert got[1] == ("phase:g=goal", "stage:b=x")


def test_difference_after_a_gate_is_detected() -> None:
    """フェーズの最終ステージの goal でも、ゲートの先の次のステージの違いを検出する。"""
    runs: list[RunRecord] = []
    for rep, counts in (("A", {"goal": 45, "x": 5}), ("B", {"goal": 15, "x": 35})):
        for nxt, n in counts.items():
            runs += [
                _run([("a", "goal", rep), ("g", "goal", None, 1, "phase"), ("b", nxt, None)])
            ] * n
    [result] = [r for r in independence(RunSet(runs)) if r.state == "stage:a=goal"]
    assert result.verdict == "violated"


def test_strata_by_visit_bucket() -> None:
    """訪問の区分が違うと下流が違っても、区分の中で揃っていれば違反にしない（マルコフの仮定と揃える）。"""
    runs: list[RunRecord] = []
    for visit, rep, counts in ((1, "A", {"goal": 40, "x": 10}), (2, "B", {"goal": 10, "x": 40})):
        for nxt, n in counts.items():
            runs += [_run([("a", "goal", rep, visit), ("b", nxt, None)])] * n
    results = [r for r in independence(RunSet(runs)) if r.state == "stage:a=goal"]
    assert sorted(r.visit for r in results) == [1, 2]
    assert all(r.verdict != "violated" for r in results)


def test_p_value_is_never_below_one_over_permutations_plus_one() -> None:
    runs = _two_groups({"goal": 10}, {"x": 10})
    [result] = [r for r in independence(runs, permutations=9) if r.state == "stage:a=goal"]
    assert result.p_value == pytest.approx(1 / 10)


def test_permutation_p_value_matches_exact_hypergeometric() -> None:
    """周辺度数が対称な 2×2 では、カイ二乗の順序は |a - 5| の順序と同じなので、厳密な p 値は超幾何分布から出る。"""
    from math import comb

    runs = _two_groups({"goal": 8, "x": 2}, {"goal": 2, "x": 8})
    [result] = [
        r for r in independence(runs, permutations=20000, min_group=10) if r.state == "stage:a=goal"
    ]
    exact = 2 * sum(comb(10, k) * comb(10, 10 - k) for k in (8, 9, 10)) / comb(20, 10)
    assert result.p_value is not None
    assert abs(result.p_value - exact) < 4 * (exact * (1 - exact) / 20000) ** 0.5


def test_strata_include_the_next_stage_visit() -> None:
    """代表が「どこから戻ってきたか」で変わり、次のステージの訪問の区分と結びつく場合、訪問の区分の違いを
    クラスの粗さと取り違えない。代表 A の後は次が訪問 1、代表 B の後は次が訪問 2 で、それぞれ下流の分布が違う。"""
    runs: list[RunRecord] = []
    for rep, next_visit, counts in (
        ("A", 1, {"goal": 40, "x": 10}),
        ("B", 2, {"goal": 10, "x": 40}),
    ):
        for nxt, n in counts.items():
            runs += [_run([("a", "goal", rep, 1), ("b", nxt, None, next_visit)])] * n
    results = [r for r in independence(RunSet(runs)) if r.state == "stage:a=goal"]
    assert sorted((r.visit, r.next_visit) for r in results) == [(1, 1), (1, 2)]
    assert all(r.verdict == "undetermined" for r in results)


def _workflow_runs(tmp_path: Path, carry_matters: bool) -> RunSet:
    """s2 の結果が、s3 から e3_back で戻った（記憶 m32 を受けた）かで変わる本体（carry_matters）と、変わらない本体。

    s2 の訪問 2 以降には、s1 からの next（s2 の e2_back の後）と、s3 からの rollback の二つの入り方がある。
    """
    workflow = load_workflow(
        ROOT / "contract/conformance/workflows/basic.yaml", ConformanceRegistry().names()
    )

    def body(context: StageContext) -> None:
        rng = random.Random(context.seed)
        n = context.stage_id[-1]
        (context.workspace / f"s{n}.flag").write_text("true")
        if n == "1":
            (context.workspace / "s1.txt").write_text("[[class s1=goal]]")
        elif n == "2":
            carried = context.read_memory("m32") is not None
            p_goal = 0.9 if carried and carry_matters else 0.5
            cls = "goal" if rng.random() < p_goal else "e2_back"
            (context.workspace / "s2.txt").write_text(f"[[class s2={cls}]]")
            (context.workspace / "gate1.flag").write_text("true")
            context.write_memory("m21", "直すところ")
        else:
            cls = "e3_back" if context.visit == 1 and rng.random() < 0.5 else "goal"
            (context.workspace / "s3.txt").write_text(f"[[class s3={cls}]]")
            (context.workspace / "gate2.num").write_text("0")
            context.write_memory("m32", "直すところ")

    runtime = Runtime(
        workflow,
        {s.id: body for s in workflow.stages},
        registry=ConformanceRegistry(),
        classifier=MarkerClassifier(),
        operator=AbortOperator(),
        store=BlobStore(tmp_path / "store"),
        workdir=tmp_path,
    )
    return run_many(400, 0, lambda seed: record_run(runtime, seed, {"in.txt": b"x"}))


@pytest.fixture(scope="module")
def carry_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[bool, RunSet]:
    return {m: _workflow_runs(tmp_path_factory.mktemp(f"carry-{m}"), m) for m in (True, False)}


def test_entries_name_how_each_visit_was_entered(carry_runs: dict[bool, RunSet]) -> None:
    runs = carry_runs[False]
    seen = {(e.stage, e.entry) for e in entries(runs)}
    assert ("s1", "start") in seen
    assert ("s2", "next:s1") in seen
    assert ("s2", "rollback:s3=e3_back") in seen
    assert ("s1", "rollback:s2=e2_back") in seen
    assert all(e.visit >= 1 for e in entries(runs))


def test_entry_dependence_detects_carry_dependent_bodies(carry_runs: dict[bool, RunSet]) -> None:
    """訪問 2 以降の結果が入り方で違うかの検定。carry で振る舞いが変わる本体を検出し、変わらない本体では
    違反を出さない。"""
    dependent = {(r.stage, r.visit): r for r in entry_dependence(carry_runs[True])}
    plain = {(r.stage, r.visit): r for r in entry_dependence(carry_runs[False])}
    assert dependent[("s2", 2)].verdict == "violated"
    assert set(dependent[("s2", 2)].groups) == {"next:s1", "rollback:s3=e3_back"}
    assert plain[("s2", 2)].verdict == "not_detected"
    assert all(r.visit >= 2 for r in plain.values())
