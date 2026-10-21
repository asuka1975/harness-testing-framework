"""分類器の検証（オラクル）のレポート（plan.md 第2節「分類器の検証」、第6節 F3）。

既知の混同行列を持つ偽の分類器に対して、既知の κ と ECE と再実行の一致率を再現する。期待値は下の配分から手で計算した。
"""

from pathlib import Path

import pytest

from harness_testing_framework.contract import Classification, Option
from harness_testing_framework.testing.oracle import (
    ConfusionClassifier,
    CorpusInvalid,
    CorpusItem,
    FlakyClassifier,
    Label,
    cohen_kappa,
    expected_calibration_error,
    load_corpus,
    load_labels,
    oracle_report,
    save_corpus,
    save_labels,
)

OPTIONS = (
    Option("goal", "目的を達した"),
    Option("x", "直すべき点がある"),
    Option("unknown", "どちらでもない"),
)
# 真のクラスごとの件数と、偽の分類器の配分（周期ごとに (選ぶクラス, 確信度) を順に返す）
COUNTS = {"goal": 50, "x": 30, "unknown": 20}
ROWS = {
    "goal": [("goal", 0.9)] * 9 + [("x", 0.6)],  # 45 件正解、5 件 x
    "x": [("x", 0.8)] * 4 + [("goal", 0.6)],  # 24 件正解、6 件 goal
    "unknown": [("unknown", 0.7)] * 4 + [("goal", 0.6)],  # 16 件正解、4 件 goal
}


def _corpus() -> tuple[list[CorpusItem], list[Label]]:
    items, labels = [], []
    # 真のクラスを交互に並べても、偽の分類器の配分はクラスごとに数える
    order = [c for i in range(50) for c in ("goal", "x", "unknown") if i < COUNTS[c]]
    for n, true in enumerate(order, 1):
        state = f"# 評価: stage a visit 1\n[[class a={true}]]\n項目 {n}"
        items.append(CorpusItem(f"i{n}", "stage", "a", OPTIONS, state))
        labels.append(Label(f"i{n}", true, "人手"))
    return items, labels


def test_known_kappa_and_confusion() -> None:
    items, labels = _corpus()
    report = oracle_report(ConfusionClassifier(ROWS), items, labels, reruns=1)
    assert report.n == 100
    assert report.confusion == {
        ("goal", "goal"): 45,
        ("goal", "x"): 5,
        ("x", "x"): 24,
        ("x", "goal"): 6,
        ("unknown", "unknown"): 16,
        ("unknown", "goal"): 4,
    }
    po = (45 + 24 + 16) / 100
    pe = (50 * 55 + 30 * 29 + 20 * 16) / 100**2
    assert report.kappa == pytest.approx((po - pe) / (1 - pe))
    assert report.accuracy == pytest.approx(0.85)


def test_known_ece_with_ten_equal_width_bins() -> None:
    items, labels = _corpus()
    report = oracle_report(ConfusionClassifier(ROWS), items, labels, reruns=1)
    # 確信度 0.9 の 45 件は全問正解、0.8 の 24 件と 0.7 の 16 件も正解、0.6 の 15 件は全問不正解
    expected = 0.45 * 0.1 + 0.24 * 0.2 + 0.16 * 0.3 + 0.15 * 0.6
    assert report.ece == pytest.approx(expected)
    populated = [b for b in report.bins if b.n]
    assert [(b.low, b.n) for b in populated] == [(0.6, 15), (0.7, 16), (0.8, 24), (0.9, 45)]


def test_known_rerun_agreement() -> None:
    items, labels = _corpus()
    stable = oracle_report(ConfusionClassifier(ROWS), items, labels, reruns=3)
    assert stable.rerun_agreement == pytest.approx(1.0)
    flaky = oracle_report(
        FlakyClassifier(ConfusionClassifier(ROWS), every=4), items, labels, reruns=2
    )
    assert flaky.rerun_agreement == pytest.approx(0.75)


def test_kappa_and_ece_edge_cases() -> None:
    assert cohen_kappa([("a", "a"), ("b", "b")]) == pytest.approx(1.0)
    assert cohen_kappa([("a", "a"), ("a", "a")]) == pytest.approx(1.0)  # 偶然の一致が 1 のとき
    ece, bins = expected_calibration_error([(1.0, True), (0.0, False)], bins=10)
    assert ece == pytest.approx(0.0)
    assert bins[-1].n == 1 and bins[0].n == 1


def test_unanswered_is_its_own_category_and_excluded_from_ece() -> None:
    items, labels = _corpus()
    report = oracle_report(
        ConfusionClassifier({**ROWS, "x": [(None, 0.0)]}), items, labels, reruns=1
    )
    assert report.confusion[("x", None)] == 30
    assert report.unanswered == 30
    assert report.coverage == pytest.approx(0.7)
    # 答えた 70 件だけで: 0.9 の 45 件は正解、0.7 の 16 件は正解、0.6 の 9 件は不正解
    assert report.ece == pytest.approx((45 * 0.1 + 16 * 0.3 + 9 * 0.6) / 70)


class Misbehaving:
    def __init__(self, result: object) -> None:
        self.result = result

    def classify(self, state: str, options: object) -> Classification:
        if isinstance(self.result, Exception):
            raise self.result
        assert isinstance(self.result, Classification)
        return self.result


@pytest.mark.parametrize(
    "result",
    [
        Classification("goal", -0.3),
        Classification("goal", 1.5),
        Classification("goal", float("nan")),
        Classification("nonsense", 0.9),
        RuntimeError("落ちた"),
    ],
)
def test_invalid_classifier_output_is_no_answer(result: object) -> None:
    items, labels = _corpus()
    report = oracle_report(Misbehaving(result), items[:5], labels[:5], reruns=1)
    assert report.unanswered == 5
    assert report.coverage == 0.0


def test_breakdown_by_target() -> None:
    items, labels = _corpus()
    report = oracle_report(ConfusionClassifier(ROWS), items, labels, reruns=1)
    assert set(report.by_target) == {"stage:a"}
    assert report.by_target["stage:a"].kappa == pytest.approx(report.kappa)
    assert report.by_target["stage:a"].n == 100


def test_empty_labels_are_rejected() -> None:
    items, _ = _corpus()
    with pytest.raises(CorpusInvalid, match="ラベル"):
        oracle_report(ConfusionClassifier(ROWS), items, [])


def test_corpus_and_labels_round_trip(tmp_path: Path) -> None:
    items, labels = _corpus()
    save_corpus(items[:3], tmp_path / "corpus.jsonl")
    save_labels(labels[:3], tmp_path / "labels.jsonl")
    assert load_corpus(tmp_path / "corpus.jsonl") == items[:3]
    assert load_labels(tmp_path / "labels.jsonl") == labels[:3]


def test_labels_must_refer_to_items_and_options(tmp_path: Path) -> None:
    items, _ = _corpus()
    with pytest.raises(CorpusInvalid, match="選択肢"):
        oracle_report(ConfusionClassifier(ROWS), items[:1], [Label("i1", "nonsense", "人手")])
    with pytest.raises(CorpusInvalid, match="項目"):
        oracle_report(ConfusionClassifier(ROWS), items[:1], [Label("i999", "goal", "人手")])
    (tmp_path / "bad.jsonl").write_text('{"item": "i1"}\n', encoding="utf-8")
    with pytest.raises(CorpusInvalid):
        load_labels(tmp_path / "bad.jsonl")


def test_breakdown_differs_by_target() -> None:
    items, labels = _corpus()
    # 前半 50 件を対象 b に付け替える（b は goal の項目が多い）
    moved = [
        CorpusItem(
            i.item,
            i.scope,
            "b",
            i.options,
            i.state.replace("stage a", "stage b").replace("class a=", "class b="),
        )
        if n < 50
        else i
        for n, i in enumerate(items)
    ]
    report = oracle_report(ConfusionClassifier(ROWS), moved, labels, reruns=1)
    assert set(report.by_target) == {"stage:a", "stage:b"}
    a, b = report.by_target["stage:a"], report.by_target["stage:b"]
    assert a.n + b.n == 100
    assert (a.kappa, a.ece) != (b.kappa, b.ece)
    for summary in (a, b):
        assert summary.kappa != pytest.approx(report.kappa) or summary.ece != pytest.approx(
            report.ece
        )


def test_no_answered_items_gives_no_ece() -> None:
    items, labels = _corpus()
    report = oracle_report(
        ConfusionClassifier({k: [(None, 0.0)] for k in ROWS}), items, labels, reruns=1
    )
    assert report.coverage == 0.0
    assert report.ece is None
    assert any("ECE なし" in line for line in report.lines())
