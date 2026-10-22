"""software-factory のトリアージの一周。

1. 印を読む偽の分類器で実行する。review とその assurance のゲートの評価だけ確信度を 0.6 にする（閾値 0.5 は越えるので
   遷移は変わらない）。unknown と確信度 0.7 未満の評価を待ち行列に足す
2. 人の代わりに、置き場の状態文書を読んで判定する。確信度が低いだけの評価には印のクラスでラベルを付ける（最初のゲートの
   評価だけは、正しいが確信度の低すぎる分類器の誤りとする）。unknown には、分類体系の変更の提案（新しいクラス、記述の修正）
   か「問題なし」を付ける
3. 判定の無い項目が無くなり、提案はワークフロー定義を変えない
4. ラベルを付けた項目を分類器の検証のコーパスに足し、オラクルのレポートを出す
"""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

import jsonschema
import pytest
from software_factory.stages.deterministic import ROOT, WORKFLOW
from software_factory.stages.probabilistic import WORKFLOW_MODEL, run_set

from harness_testing_framework.contract import Classification, Option
from harness_testing_framework.testing.harness import (
    MarkerClassifier,
    evaluation_target,
    marked_class,
)
from harness_testing_framework.testing.oracle import Label, build_corpus, oracle_report
from harness_testing_framework.testing.triage import (
    PROPOSALS,
    Decision,
    TriageInvalid,
    decide,
    decisions,
    enqueue,
    items,
    open_items,
)

FORMATS = ROOT.parents[1] / "contract" / "formats"


class Hesitant:
    """印を読む偽の分類器。review と assurance のゲートの評価だけ、確信度 0.6 で答える。"""

    def __init__(self) -> None:
        self.sure, self.unsure = MarkerClassifier(confidence=0.9), MarkerClassifier(confidence=0.6)

    def classify(self, state: str, options: Sequence[Option]) -> Classification:
        target = evaluation_target(state)
        unsure = target is not None and target[1] in ("review", "assurance")
        return (self.unsure if unsure else self.sure).classify(state, options)


CLASSIFIER = Hesitant()


def test_one_round_of_triage(tmp_path: Path) -> None:
    before = hashlib.sha256(WORKFLOW.read_bytes()).hexdigest()
    runs, store = run_set("markov", 24, 80000, tmp_path / "runs", classifier=CLASSIFIER)
    queue, record = tmp_path / "triage" / "queue.jsonl", tmp_path / "triage" / "decisions.jsonl"

    added = [item for run in runs.runs for item in enqueue(queue, run, review_below=0.7)]
    assert added and items(queue) == added
    assert {i.reason for i in added} == {"unknown", "low_confidence"}
    assert all(i.outcome == "unknown" or i.target in ("review", "assurance") for i in added)
    # 同じ実行を二度足しても重ならない
    assert [i for run in runs.runs for i in enqueue(queue, run, review_below=0.7)] == []

    # unknown の一つ目には新しいクラス、二つ目には記述の修正を提案し、残りは「人に戻して正しい」とする
    proposals = list(PROPOSALS)
    calibration_noted = False
    for item in open_items(queue, record):
        state = store.get(item.state).decode("utf-8")
        if item.outcome != "unknown" and item.scope == "phase" and not calibration_noted:
            calibration_noted = True
            note = "分類は正しいが確信度が 0.7 に届かない。分類器の較正を見直す"
            decide(queue, record, Decision(item.item, "classifier_error", None, note, "triager"))
        elif item.outcome != "unknown":
            label = marked_class(state) if item.scope == "stage" else "goal"
            decide(queue, record, Decision(item.item, "label", label, "印を確かめた", "triager"))
        elif proposals:
            note = (
                f"{item.target} の unknown の成果物に共通する状態を、分類体系に足すことを提案する"
            )
            decide(queue, record, Decision(item.item, proposals.pop(0), None, note, "triager"))
        else:
            decide(
                queue,
                record,
                Decision(item.item, "not_a_problem", None, "人に戻して正しい", "triager"),
            )

    assert open_items(queue, record) == []
    recorded = decisions(record)
    assert len(recorded) == len(added)
    lines = [json.loads(line) for line in record.read_text("utf-8").splitlines()]
    assert {d["verdict"] for d in lines if d["proposal"]} == set(PROPOSALS)
    assert {d["verdict"] for d in lines} == {
        "label",
        "classifier_error",
        *PROPOSALS,
        "not_a_problem",
    }
    for name, path in (("triage_item", queue), ("triage_decision", record)):
        schema = json.loads((FORMATS / f"{name}.schema.json").read_text("utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for line in path.read_text("utf-8").splitlines():
            validator.validate(json.loads(line))
    # 提案は記録されるだけで、ワークフロー定義は変わらない
    assert hashlib.sha256(WORKFLOW.read_bytes()).hexdigest() == before

    # ラベルを付けた項目を、分類器の検証のコーパスに足す
    labels = [
        Label(d.item, d.label, d.by)
        for d in recorded
        if d.verdict == "label" and d.label is not None
    ]
    corpus = [
        i for i in build_corpus(runs, store, WORKFLOW_MODEL) if i.item in {x.item for x in labels}
    ]
    assert {i.item for i in corpus} == {x.item for x in labels}
    report = oracle_report(CLASSIFIER, corpus, labels)
    assert report.kappa == pytest.approx(1.0)
    assert report.ece == pytest.approx(0.4)


def test_a_label_outside_the_options_is_rejected(tmp_path: Path) -> None:
    runs, _ = run_set("markov", 3, 80000, tmp_path / "runs", classifier=CLASSIFIER)
    queue, record = tmp_path / "queue.jsonl", tmp_path / "decisions.jsonl"
    enqueue(queue, runs.runs[0], review_below=0.7)
    item = items(queue)[0]
    with pytest.raises(TriageInvalid):
        decide(queue, record, Decision(item.item, "label", "no_such_class", "誤り", "triager"))
    assert open_items(queue, record) == items(queue)
