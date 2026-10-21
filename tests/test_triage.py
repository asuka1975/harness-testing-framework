"""トリアージ待ち行列（plan.md 第6節 F3: サンプル一件を流せる）。"""

from collections.abc import Sequence
from pathlib import Path

import pytest

from harness_testing_framework.contract import Classification, Option, StageContext
from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.harness import AbortOperator, ConformanceRegistry
from harness_testing_framework.testing.stages import RunRecord, record_run
from harness_testing_framework.testing.triage import (
    Decision,
    TriageInvalid,
    decide,
    decisions,
    enqueue,
    open_items,
)

ROOT = Path(__file__).resolve().parents[1]


class LowThenUnknown:
    """s1 は確信度 0.55 で goal、s2 は答え無し。"""

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        if state.startswith("# 評価: stage s1"):
            return Classification("goal", 0.55)
        return Classification(None, 0.0)


def _write(context: StageContext) -> None:
    n = context.stage_id[-1]
    (context.workspace / f"s{n}.txt").write_text(n)
    (context.workspace / f"s{n}.flag").write_text("true")


def _run(tmp_path: Path) -> tuple[RunRecord, BlobStore]:
    workflow = load_workflow(
        ROOT / "contract/conformance/workflows/basic.yaml", ConformanceRegistry().names()
    )
    store = BlobStore(tmp_path / "store")
    runtime = Runtime(
        workflow,
        {s.id: _write for s in workflow.stages},
        registry=ConformanceRegistry(),
        classifier=LowThenUnknown(),
        operator=AbortOperator(),
        store=store,
        workdir=tmp_path,
    )
    return record_run(runtime, 7, {"in.txt": b"x"}), store


def test_one_sample_flows_through_the_queue(tmp_path: Path) -> None:
    run, store = _run(tmp_path)
    queue = tmp_path / "triage" / "queue.jsonl"
    added = enqueue(queue, run, review_below=0.6)
    assert [(i.target, i.reason) for i in added] == [("s1", "low_confidence"), ("s2", "unknown")]
    assert store.get(added[1].state).decode("utf-8").startswith("# 評価: stage s2 visit 1")
    assert enqueue(queue, run, review_below=0.6) == []
    assert len(open_items(queue)) == 2

    record = tmp_path / "triage" / "decisions.jsonl"
    decide(
        queue,
        record,
        Decision(added[1].item, "label", "e2_back", "直すべき点が m21 にある", "人手"),
    )
    decide(queue, record, Decision(added[0].item, "not_a_problem", None, "goal で正しい", "人手"))
    assert open_items(queue, record) == []
    assert [d.verdict for d in decisions(record)] == ["label", "not_a_problem"]


def test_invalid_decisions_are_rejected(tmp_path: Path) -> None:
    run, _ = _run(tmp_path)
    queue = tmp_path / "queue.jsonl"
    added = enqueue(queue, run, review_below=0.6)
    record = tmp_path / "decisions.jsonl"
    with pytest.raises(TriageInvalid, match="選択肢"):
        decide(queue, record, Decision(added[1].item, "label", "nonsense", "", "人手"))
    with pytest.raises(TriageInvalid, match="項目"):
        decide(queue, record, Decision("no-such-item", "label", "goal", "", "人手"))
    with pytest.raises(TriageInvalid, match="判定"):
        decide(queue, record, Decision(added[1].item, "delete_class", None, "", "人手"))


def test_taxonomy_changes_are_proposals_only(tmp_path: Path) -> None:
    run, _ = _run(tmp_path)
    queue = tmp_path / "queue.jsonl"
    added = enqueue(queue, run, review_below=0.6)
    record = tmp_path / "decisions.jsonl"
    decide(
        queue,
        record,
        Decision(
            added[1].item,
            "new_class_proposal",
            None,
            "どの end_state にも当たらない状態がある",
            "人手",
        ),
    )
    [d] = decisions(record)
    assert d.verdict == "new_class_proposal" and d.proposal
