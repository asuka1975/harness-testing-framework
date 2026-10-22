"""software-factory の独立性検証。

- divergent: implement の goal というクラスの中で、実装の変種（ok は REQ-1 を誤る、ok_fixed は正しい）によって
  unit_test の分布が分かれる（変種 defect のテストが、実在の pytest で ok では落ち ok_fixed では通る）。
  独立性検証は stage:implement=goal で違反を検出する
- markov: goal の実装の二つの変種（ok と ok_b）は同じ系統なので違反を出さない
- どちらでも、intake の goal のペルソナごとの代表（回答が違う intake.md）は下流を変えない
- assurance のゲートを成果物によらず実行の種で揺らす実行（RandomGateClassifier）では、ゲートが下流を変えても代表には
  よらないので、違反を出さない
"""

import pytest

from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.stages import RunSet, independence

type Verdicts = dict[tuple[str, int, int], tuple[str, dict[str, int]]]


@pytest.fixture(scope="module")
def verdicts(
    markov_runs: tuple[RunSet, BlobStore], divergent_runs: tuple[RunSet, BlobStore]
) -> dict[str, Verdicts]:
    """実行の集まりは tests/conftest.py で共有する（markov は分布テストと同じもの）。"""
    out: dict[str, Verdicts] = {}
    for profile, (runs, _) in (("markov", markov_runs), ("divergent", divergent_runs)):
        out[profile] = {
            (r.state, r.visit, r.next_visit): (r.verdict, r.groups) for r in independence(runs)
        }
    return out


def test_divergent_body_is_detected(verdicts: dict[str, Verdicts]) -> None:
    verdict, groups = verdicts["divergent"][("stage:implement=goal", 1, 1)]
    assert verdict == "violated"
    assert len(groups) == 2, groups


def test_markov_body_is_not_flagged(verdicts: dict[str, Verdicts]) -> None:
    verdict, groups = verdicts["markov"][("stage:implement=goal", 1, 1)]
    assert verdict == "not_detected"
    assert len(groups) == 2, groups
    assert "violated" not in {v for v, _ in verdicts["markov"].values()}


@pytest.mark.parametrize("profile", ["markov", "divergent"])
def test_persona_representatives_do_not_change_downstream(
    verdicts: dict[str, Verdicts], profile: str
) -> None:
    verdict, groups = verdicts[profile][("stage:intake=goal", 1, 1)]
    assert verdict == "not_detected"
    assert len(groups) == 3, groups


def test_random_gate_is_not_flagged(gated_runs: tuple[RunSet, BlobStore]) -> None:
    verdicts = {r.verdict for r in independence(gated_runs[0])}
    assert "violated" not in verdicts
    assert "not_detected" in verdicts
