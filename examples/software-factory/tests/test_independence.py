"""software-factory の独立性検証。

- divergent: implement の goal というクラスの中で、実装の変種（ok は REQ-1 を誤る、ok_fixed は正しい）によって
  unit_test の分布が分かれる（変種 defect のテストが、実在の pytest で ok では落ち ok_fixed では通る）。
  独立性検証は stage:implement=goal で違反を検出する
- markov: goal の実装の二つの変種（ok と ok_b）は同じ系統なので違反を出さない（p 値が 0.001 以上）
- どちらでも、intake の goal のペルソナごとの代表（回答が違う intake.md）は下流を変えない（p 値が 0.001 以上）
- assurance のゲートを成果物によらず実行の種で揺らす実行（RandomGateClassifier）では、ゲートが下流を変えても代表には
  よらないので、違反を出さない
"""

import pytest
from software_factory.design import family_wise_violations

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.stages import RunSet, independence

type Verdicts = dict[tuple[str, int, int], tuple[str, dict[str, int], float | None]]


@pytest.fixture(scope="module")
def verdicts(
    markov_runs: tuple[RunSet, BlobStore], divergent_runs: tuple[RunSet, BlobStore]
) -> dict[str, Verdicts]:
    """実行の集まりは tests/conftest.py で共有する（markov は分布テストと同じもの）。"""
    out: dict[str, Verdicts] = {}
    for profile, (runs, _) in (("markov", markov_runs), ("divergent", divergent_runs)):
        out[profile] = {
            (r.state, r.visit, r.next_visit): (r.verdict, r.groups, r.p_value)
            for r in independence(runs)
        }
    return out


def test_divergent_body_is_detected(verdicts: dict[str, Verdicts]) -> None:
    verdict, groups, _ = verdicts["divergent"][("stage:implement=goal", 1, 1)]
    assert verdict == "violated"
    assert len(groups) == 2, groups


def test_markov_body_is_not_flagged(verdicts: dict[str, Verdicts]) -> None:
    """仕込んだ所（stage:implement=goal、訪問 1 → 1）で、markov は判定でき、p 値が 0.001 以上。補正の無い alpha 0.01 の
    not_detected を求めると、この一つの検定でも正しい本体が種や回数（HTF_RUNS）によって約 1% の確率で落ちる。divergent の
    検出は p = 0.0005 程度なので、0.001 で確かめても検出の確かめには響かない（tests/README.md）。"""
    _, groups, p_value = verdicts["markov"][("stage:implement=goal", 1, 1)]
    assert p_value is not None and p_value >= 0.001, p_value
    assert len(groups) == 2, groups


def test_markov_body_has_no_family_wise_violation(markov_runs: tuple[RunSet, BlobStore]) -> None:
    """仕込んでいない状態にも違いが無いこと。検定は状態ごとに alpha 0.01 で補正が無いので、全状態を alpha 0.01 で
    確かめると、正しい本体でも種や回数（HTF_RUNS）によって数 % の確率で落ちる。全状態を見る時は、判定できた検定の数で
    alpha を割る（Bonferroni）。"""
    assert family_wise_violations(independence(markov_runs[0])) == []


@pytest.mark.parametrize("profile", ["markov", "divergent"])
def test_persona_representatives_do_not_change_downstream(
    verdicts: dict[str, Verdicts], profile: str
) -> None:
    """ペルソナごとの intake.md（三つの代表）で下流が変わらない。仕込んでいない違いの確かめなので、上と同じく p 値が
    0.001 以上であることで確かめる。"""
    _, groups, p_value = verdicts[profile][("stage:intake=goal", 1, 1)]
    assert p_value is not None and p_value >= 0.001, p_value
    assert len(groups) == 3, groups


def test_random_gate_is_not_flagged(gated_runs: tuple[RunSet, BlobStore]) -> None:
    """ゲートを揺らしても、どの状態にも違いが無い（判定できた検定の数で alpha を割って確かめる）。"""
    results = independence(gated_runs[0])
    assert family_wise_violations(results) == []
    assert "not_detected" in {r.verdict for r in results}
