"""toy-minimal の独立性検証（plan.md 第6節 F3 の完了条件）。

- クラス内で下流の分布を意図的に変えた偽ステージ本体（divergent）を検出する
- 揃っているもの（markov）では違反を出さない
"""

from pathlib import Path

import pytest
from toy_minimal.stages.probabilistic import INPUTS, runtime

from harness_testing_framework.testing.stages import (
    RunSet,
    independence,
    record_run,
    run_many,
    runs_from_environment,
)

RUNS = runs_from_environment(300)


def _runs(profile: str, workdir: Path) -> RunSet:
    built = runtime(profile, workdir)
    return run_many(RUNS, 20000, lambda seed: record_run(built, seed, INPUTS))


@pytest.fixture(scope="module")
def verdicts(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[tuple[str, int, int], str]]:
    out: dict[str, dict[tuple[str, int, int], str]] = {}
    for profile in ("markov", "divergent"):
        runs = _runs(profile, tmp_path_factory.mktemp(profile))
        out[profile] = {(r.state, r.visit, r.next_visit): r.verdict for r in independence(runs)}
    return out


def test_divergent_body_is_detected(verdicts: dict[str, dict[tuple[str, int, int], str]]) -> None:
    assert verdicts["divergent"][("stage:write_note=goal", 1, 1)] == "violated"


def test_markov_body_is_not_flagged(verdicts: dict[str, dict[tuple[str, int, int], str]]) -> None:
    assert verdicts["markov"][("stage:write_note=goal", 1, 1)] == "not_detected"
    assert "violated" not in verdicts["markov"].values()
