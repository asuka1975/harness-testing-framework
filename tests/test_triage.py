"""トリアージ待ち行列（plan.md 第6節 F3: サンプル一件を流せる）。"""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

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
    items,
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


def test_confidence_at_the_threshold_is_not_queued(tmp_path: Path) -> None:
    run, _ = _run(tmp_path)
    added = enqueue(tmp_path / "queue.jsonl", run, review_below=0.55)
    assert [i.reason for i in added] == ["unknown"]


def test_classifier_error_label_must_be_an_option(tmp_path: Path) -> None:
    run, _ = _run(tmp_path)
    queue = tmp_path / "queue.jsonl"
    added = enqueue(queue, run, review_below=0.6)
    record = tmp_path / "decisions.jsonl"
    with pytest.raises(TriageInvalid, match="選択肢"):
        decide(queue, record, Decision(added[0].item, "classifier_error", "nonsense", "", "人手"))
    decide(
        queue,
        record,
        Decision(added[0].item, "classifier_error", "unknown", "本当は unknown", "人手"),
    )


def test_items_of_different_runs_with_the_same_seed_do_not_collide(tmp_path: Path) -> None:
    first, _ = _run(tmp_path / "a")
    second = RunRecord(
        first.seed, first.status, [*first.events[:-1], {**first.events[-1], "extra": 1}], {}
    )
    queue = tmp_path / "queue.jsonl"
    assert len(enqueue(queue, first, review_below=0.6)) == 2
    assert first.run_id != second.run_id
    assert len(enqueue(queue, second, review_below=0.6)) == 2
    assert len(enqueue(queue, first, review_below=0.6)) == 0


def _item_row(i: int) -> dict[str, object]:
    return {
        "item": f"{i:016x}-{i}",
        "run": i,
        "seq": i,
        "scope": "stage",
        "target": "s1",
        "visit": 1,
        "options": ["goal", "unknown"],
        "choice": "goal",
        "confidence": 0.5,
        "outcome": "goal",
        "state": "0" * 64,
        "reason": "low_confidence",
    }


def _lines(rows: Sequence[dict[str, object]]) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def test_queue_reads_follow_appends_and_rewrites(tmp_path: Path) -> None:
    """読み込みは、追記された行だけを読み足しても、書き換えられたファイルを読み直しても正しい。"""
    queue = tmp_path / "queue.jsonl"
    queue.write_text(_lines([_item_row(0), _item_row(1)]), encoding="utf-8")
    assert [i.run for i in items(queue)] == [0, 1]
    with queue.open("a", encoding="utf-8") as f:
        f.write(_lines([_item_row(2)]))
    assert [i.run for i in items(queue)] == [0, 1, 2]
    # 同じ長さ以上で中身の違うファイルに書き換える
    queue.write_text(_lines([_item_row(7), _item_row(8), _item_row(9)]), encoding="utf-8")
    assert [i.run for i in items(queue)] == [7, 8, 9]
    queue.write_text(_lines([_item_row(5)]), encoding="utf-8")
    assert [i.run for i in items(queue)] == [5]
    with queue.open("a", encoding="utf-8") as f:
        f.write('{"item": "broken"}\n')
    with pytest.raises(TriageInvalid, match=r"queue.jsonl:2"):
        items(queue)


def test_deciding_many_items_does_not_revalidate_the_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """判定を一件ずつ記録しても、待ち行列の各行の形式の検査は一度だけ（項目の数の二乗にならない）。"""
    queue, record = tmp_path / "queue.jsonl", tmp_path / "record.jsonl"
    queue.write_text(_lines([_item_row(i) for i in range(50)]), encoding="utf-8")
    calls = {"n": 0}
    original = Draft202012Validator.iter_errors

    def counting(self: Draft202012Validator, instance: object) -> object:
        calls["n"] += 1
        return original(self, instance)

    monkeypatch.setattr(Draft202012Validator, "iter_errors", counting)
    for item in items(queue):
        decide(queue, record, Decision(item.item, "label", "goal", "", "tester"))
    assert open_items(queue, record) == []
    # 待ち行列の 50 行と、判定の 50 行（記録の時と、読み戻す時）
    assert calls["n"] <= 50 + 50 * 2
