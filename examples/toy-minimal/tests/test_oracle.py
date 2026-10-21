"""toy-minimal の実行記録から分類器の検証のコーパスを作る（状態文書は置き場から読む）。

印を読む偽の分類器は、印を正解のラベルとしたとき全問正解（κ = 1）で、確信度 0.9 なので ECE は 0.1。
"""

import re
from pathlib import Path

import pytest
from toy_minimal.stages.probabilistic import INPUTS, runtime

from harness_testing_framework.testing.harness import MarkerClassifier
from harness_testing_framework.testing.oracle import Label, build_corpus, oracle_report
from harness_testing_framework.testing.stages import record_run, run_many


def test_corpus_from_runs_and_marker_labels(tmp_path: Path) -> None:
    built = runtime("markov", tmp_path)
    runs = run_many(30, 50000, lambda seed: record_run(built, seed, INPUTS))
    corpus = build_corpus(runs, built.store, built.workflow)
    stage_items = [i for i in corpus if i.scope == "stage"]
    assert stage_items and all(i.state.startswith("# 評価: stage") for i in stage_items)
    assert all(i.options[0].description for i in corpus)
    labels = [
        Label(i.item, i.state.split(f"[[class {i.target}=", 1)[1].split("]]", 1)[0], "印")
        for i in stage_items
    ]
    report = oracle_report(MarkerClassifier(confidence=0.9), stage_items, labels, reruns=2)
    assert report.kappa == pytest.approx(1.0)
    assert report.ece == pytest.approx(0.1)
    assert report.rerun_agreement == pytest.approx(1.0)


def test_corpus_ids_use_the_run_id_not_the_seed(tmp_path: Path) -> None:
    built = runtime("markov", tmp_path)
    runs = run_many(5, 1, lambda s: record_run(built, s, INPUTS))
    corpus = build_corpus(runs, built.store, built.workflow)
    run_ids = {r.run_id for r in runs.runs}
    assert corpus
    assert all(re.fullmatch(r"[0-9a-f]{16}-\d+", i.item) for i in corpus)
    assert {i.item.split("-")[0] for i in corpus} <= run_ids
