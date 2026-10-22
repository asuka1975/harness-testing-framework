"""software-factory の分類器の検証（オラクル）。

実行記録から分類器が見た状態文書のコーパスを作り（状態文書は置き場から読む）、成果物の印を人手のラベルの代わりにする。
偽の本体はフィクスチャを写すので、違う実行が同じ状態文書を生む。コーパスは build_corpus の unique_states で状態文書ごとに
一項目にする（同じ文書を二度分類すると、FlakyClassifier はそれを再実行として扱い、一回目の答えから揺らす）。ゲートの
状態文書には印が無いので、ステージの項目に絞る。

- 印を読む偽の分類器（確信度 0.9）は全問正解（κ = 1）で、ECE は 0.1、再実行の一致率は 1
- 既知の混同行列を持つ偽の分類器（ConfusionClassifier）のレポートが、混同行列から独立に計算した κ、混同行列、ECE、
  答え無しの件数と一致する。選択肢に無いクラスを選ぶ行は答え無しになる（ランタイムと同じ正規化）
- 揺れる偽の分類器（FlakyClassifier、4 件に 1 件）の再実行の一致率はおよそ 0.75 で、一回目の答えは基の分類器のもの
- コーパスとラベルは contract/formats の形式の JSON Lines で読み書きできる
"""

import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import jsonschema
import pytest
from software_factory.stages.probabilistic import WORKFLOW_MODEL

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.runtime import BlobStore
from harness_testing_framework.testing.harness import MarkerClassifier, marked_class
from harness_testing_framework.testing.oracle import (
    ConfusionClassifier,
    CorpusItem,
    FlakyClassifier,
    Label,
    build_corpus,
    load_corpus,
    load_labels,
    oracle_report,
    save_corpus,
    save_labels,
)
from harness_testing_framework.testing.stages import RunSet

# 真のクラス → (選ぶクラス, 確信度) の列。真のクラスごとに、初めて見た状態文書の順に巡って割り当てられる
ROWS: dict[str, list[tuple[str | None, float]]] = {
    "goal": [("goal", 0.93), ("goal", 0.83), ("goal", 0.73), ("unknown", 0.63)],
    "unknown": [("unknown", 0.87), ("goal", 0.57)],
    # design_flaw は analyze の選択肢に無いので、答え無しになる
    "needs_unclear": [("needs_unclear", 0.91), ("design_flaw", 0.52)],
}
END_STATES = {e.id for s in WORKFLOW_MODEL.stages for e in s.end_states} - {"unknown"}
for state in sorted(END_STATES - set(ROWS)):
    ROWS[state] = [(state, 0.88), (state, 0.78), ("unknown", 0.67)]


@pytest.fixture(scope="module")
def labeled(markov_runs: tuple[RunSet, BlobStore]) -> tuple[list[CorpusItem], list[Label]]:
    """分布テストと同じ実行の集まり（tests/conftest.py で共有）の、最初の 60 回からコーパスを作る。"""
    runs, store = RunSet(markov_runs[0].runs[:60]), markov_runs[1]
    unique = build_corpus(runs, store, WORKFLOW_MODEL, unique_states=True)
    corpus = [item for item in unique if item.scope == "stage"]
    assert len({item.state for item in corpus}) == len(corpus)
    labels = []
    for item in corpus:
        label = marked_class(item.state)
        assert label is not None, item.item
        labels.append(Label(item.item, label, "成果物の印"))
    return corpus, labels


def test_corpus_items_are_the_documents_the_classifier_saw(
    labeled: tuple[list[CorpusItem], list[Label]],
) -> None:
    corpus, _ = labeled
    assert {i.target for i in corpus} == {s.id for s in WORKFLOW_MODEL.stages}
    for item in corpus:
        assert item.state.startswith(f"# 評価: stage {item.target} visit ")
        assert item.options[-1].id == "unknown"
        assert all(o.description for o in item.options)


def test_marker_classifier_is_perfect(labeled: tuple[list[CorpusItem], list[Label]]) -> None:
    corpus, labels = labeled
    report = oracle_report(MarkerClassifier(confidence=0.9), corpus, labels, reruns=2)
    assert report.n == len(corpus)
    assert report.kappa == pytest.approx(1.0)
    assert report.ece == pytest.approx(0.1)
    assert report.rerun_agreement == pytest.approx(1.0)
    assert report.coverage == pytest.approx(1.0)
    assert set(report.by_target) == {f"stage:{s.id}" for s in WORKFLOW_MODEL.stages}


def _expected(
    corpus: Sequence[CorpusItem], labels: Sequence[Label]
) -> tuple[list[tuple[str, str | None]], list[tuple[float, bool]]]:
    """ROWS の配分から、(ラベル, 選択) の組と、答えた項目の (確信度, 正解か) を独立に組み立てる。"""
    truth = {label.item: label.label for label in labels}
    assigned: dict[str, tuple[str | None, float]] = {}
    seen: Counter[str] = Counter()
    pairs: list[tuple[str, str | None]] = []
    records: list[tuple[float, bool]] = []
    for item in corpus:
        cls = truth[item.item]
        if item.state not in assigned:
            row = ROWS[cls]
            assigned[item.state] = row[seen[cls] % len(row)]
            seen[cls] += 1
        choice, confidence = assigned[item.state]
        if choice not in {o.id for o in item.options}:
            choice = None
        pairs.append((cls, choice))
        if choice is not None:
            records.append((confidence, choice == cls))
    return pairs, records


def _kappa(pairs: Sequence[tuple[str, str | None]]) -> float:
    n = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    chance = sum(left[k] * right[k] for k in left) / (n * n)
    return (observed - chance) / (1 - chance)


def _ece(records: Sequence[tuple[float, bool]], bins: int = 10) -> float:
    groups: dict[int, list[tuple[float, bool]]] = {}
    for confidence, correct in records:
        groups.setdefault(min(int(confidence * bins), bins - 1), []).append((confidence, correct))
    return sum(
        len(g) / len(records) * abs(sum(c for _, c in g) / len(g) - sum(p for p, _ in g) / len(g))
        for g in groups.values()
    )


def test_confusion_classifier_report_matches_the_design(
    labeled: tuple[list[CorpusItem], list[Label]],
) -> None:
    corpus, labels = labeled
    pairs, records = _expected(corpus, labels)
    report = oracle_report(ConfusionClassifier(ROWS), corpus, labels, reruns=2)
    assert report.confusion == dict(Counter(pairs))
    assert report.kappa == pytest.approx(_kappa(pairs))
    assert report.accuracy == pytest.approx(sum(1 for a, b in pairs if a == b) / len(pairs))
    assert report.unanswered == sum(1 for _, b in pairs if b is None) > 0
    assert report.coverage == pytest.approx(len(records) / len(pairs))
    assert report.ece == pytest.approx(_ece(records))
    assert report.rerun_agreement == pytest.approx(1.0)
    assert 0.0 < report.kappa < 1.0


def test_flaky_classifier_disagrees_on_reruns(
    labeled: tuple[list[CorpusItem], list[Label]],
) -> None:
    corpus, labels = labeled
    report = oracle_report(FlakyClassifier(MarkerClassifier(confidence=0.9), 4), corpus, labels)
    assert report.kappa == pytest.approx(1.0)
    assert report.rerun_agreement == pytest.approx(0.75, abs=0.05)


def test_corpus_and_labels_round_trip_in_the_contract_formats(
    labeled: tuple[list[CorpusItem], list[Label]], tmp_path: Path
) -> None:
    corpus, labels = labeled
    save_corpus(corpus, tmp_path / "corpus.jsonl")
    save_labels(labels, tmp_path / "labels.jsonl")
    for name, schema in (("corpus", "corpus_item"), ("labels", "label")):
        validator = jsonschema.Draft202012Validator(load_contract_schema(f"{schema}.schema.json"))
        for line in (tmp_path / f"{name}.jsonl").read_text("utf-8").splitlines():
            validator.validate(json.loads(line))
    assert load_corpus(tmp_path / "corpus.jsonl") == corpus
    assert load_labels(tmp_path / "labels.jsonl") == labels
