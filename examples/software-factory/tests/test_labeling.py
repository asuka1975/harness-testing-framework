"""人がラベルを付ける材料（docs/human-labeling.md）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

- 材料のコーパス（docs/human-labeling.corpus.jsonl）と human-labeling.md は、試しの実行から作り直したものと一致する
  （フィクスチャ、ペルソナ、記述を変えたら `python -m software_factory.labeling write` で作り直す）
- 材料は、往復 10 で代表を変えた所（記述がその内容を証拠に使う対象の訪問 1）の、(対象, 印, 上流の違い) の組をすべて含む
- human-labeling.md に印は無く、各項目に印を除いた状態文書、選択肢（id と記述）、「ラベル:」の行がある。`write` が作る形では
  「ラベル:」は空で、人が埋めた後も、「ラベル:」を空にすれば作り直したものと一致する（人がラベルを付けても検査は落ちない）
- 埋めた「ラベル:」から contract/formats/label.schema.json の形の JSON Lines を作り、`oracle_report(MarkerClassifier(), ...)`
  で印と比べられる。印どおりのラベルなら κ 1 で食い違いが無く、違うラベルはその項目を挙げる
- ラベルのファイルが無ければ、比べるコマンドはそのことを報告する（テストをスキップしない）。受け取ったラベルのファイルが
  あれば、コーパスの項目と選択肢に合い、human-labeling.md の「ラベル:」と同じであることを確かめる
"""

import json
import re
from collections import Counter
from pathlib import Path

import jsonschema
import pytest
from software_factory import labeling
from software_factory.personas import PERSONAS

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.testing.harness import marked_class
from harness_testing_framework.testing.oracle import CorpusItem, load_corpus, load_labels

NAMES = [p.name for p in PERSONAS]
# 対象ごとの (印, 上流の違い) の組。上流の違いは、intake.md を読む対象ではペルソナ、unit_test では実装の変種
SLOTS: dict[tuple[str, str], set[tuple[str | None, str]]] = {
    ("stage", "intake"): {("goal", "vague_founder"), ("unknown", "vague_founder")},
    ("stage", "analyze"): {(m, p) for m in ("goal", "needs_unclear") for p in NAMES}
    | {("unknown", "vague_founder")},
    ("phase", "discovery"): {(None, p) for p in NAMES},
    ("stage", "design"): {("goal", ""), ("requirements_gap", ""), ("unknown", "")},
    ("stage", "unit_test"): {("tests_insufficient", v) for v in ("ok", "ok_b", "ok_fixed")},
    ("stage", "acceptance"): {
        (m, p)
        for m in ("goal", "requirement_unmet", "requirement_misread", "unknown")
        for p in NAMES
    },
}


@pytest.fixture(scope="module")
def committed() -> list[CorpusItem]:
    return load_corpus(labeling.CORPUS)


def test_material_is_regenerated_from_the_trial_runs(
    committed: list[CorpusItem], tmp_path: Path
) -> None:
    items = labeling.trial_items(tmp_path)
    assert items == committed
    # 人が「ラベル:」を埋めた後も、それを空にすれば作り直したものと一致する
    assert labeling.blank_labels(labeling.MATERIAL.read_text("utf-8")) == labeling.render(items)


def test_material_covers_every_slot_once(committed: list[CorpusItem]) -> None:
    slots: dict[tuple[str, str], set[tuple[str | None, str]]] = {}
    for item in committed:
        assert labeling.visit_of(item) == 1, item.item
        slot = (marked_class(item.state), labeling.upstream(item))
        assert slot not in slots.get((item.scope, item.target), set()), item.item
        slots.setdefault((item.scope, item.target), set()).add(slot)
    assert slots == SLOTS
    assert len(committed) == sum(len(s) for s in SLOTS.values()) == 30
    assert len({item.item for item in committed}) == len(committed)


def test_material_hides_the_marks_and_leaves_every_label_blank(
    committed: list[CorpusItem],
) -> None:
    """`write` が作る形では、印が無く、各項目の「ラベル:」は空。コミットした材料も、項目ごとに「ラベル:」の行が一つある
    （人が埋めていてもよい）。"""
    text = labeling.render(committed)
    assert "[[class" not in text
    assert "[[class" not in labeling.MATERIAL.read_text("utf-8")
    sections = labeling.sections(text)
    assert [item_id for item_id, _ in sections] == [item.item for item in committed]
    for (_, body), item in zip(sections, committed, strict=True):
        assert labeling.unmarked_state(item) in body
        for option in item.options:
            assert f"- `{option.id}`: {option.description}" in body
        assert re.search(r"^ラベル:$", body, re.M), item.item
    _, empty, errors = labeling.parse_labels(labeling.MATERIAL.read_text("utf-8"), committed, "人")
    assert errors == []
    assert len(empty) <= len(committed)
    # 読み方: 印を探さず選択肢の記述だけで選び、迷ったら unknown と理由
    head = text.split("\n## 項目 ", 1)[0]
    assert "選択肢の記述だけ" in head and "unknown" in head and "理由" in head


def _filled(text: str, committed: list[CorpusItem], wrong: str | None = None) -> str:
    """印どおりのラベル（ゲートは goal）を「ラベル:」に書いた材料。wrong の項目だけは unknown と理由を書く。"""
    choice = {item.item: marked_class(item.state) or "goal" for item in committed}
    out = []
    for part in re.split(r"(?=^## 項目 )", text, flags=re.M):
        match = re.match(r"## 項目 \d+: `([^`]+)`", part)
        if match:
            item_id = match[1]
            label = "unknown（迷った）" if item_id == wrong else str(choice[item_id])
            part = re.sub(r"^ラベル:$", f"ラベル: {label}", part, flags=re.M)
        out.append(part)
    return "".join(out)


def test_filled_labels_compare_with_the_marks(
    committed: list[CorpusItem], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material, labels = tmp_path / "human-labeling.md", tmp_path / "human-labels.jsonl"
    text = labeling.render(committed)  # write が作る形（「ラベル:」が空）
    material.write_text(_filled(text, committed), "utf-8")
    assert labeling.blank_labels(material.read_text("utf-8")) == text
    args = ["--material", str(material), "--out", str(labels)]
    assert labeling.main(["labels", "--labeler", "人", *args]) == 0
    validator = jsonschema.Draft202012Validator(load_contract_schema("label.schema.json"))
    lines = labels.read_text("utf-8").splitlines()
    assert len(lines) == len(committed)
    for line in lines:
        validator.validate(json.loads(line))
    assert {label.labeler for label in load_labels(labels)} == {"人"}
    capsys.readouterr()
    assert labeling.main(["compare", "--labels", str(labels)]) == 0
    out = capsys.readouterr().out
    assert "kappa 1.000" in out and "食い違い: 0 件" in out

    # 一項目だけ印と違うラベル（unknown と理由）にすると、その項目を挙げる
    wrong = next(item for item in committed if marked_class(item.state) == "goal")
    material.write_text(_filled(text, committed, wrong=wrong.item), "utf-8")
    assert labeling.main(["labels", "--labeler", "人", *args]) == 0
    capsys.readouterr()
    assert labeling.main(["compare", "--labels", str(labels)]) == 0
    out = capsys.readouterr().out
    assert "食い違い: 1 件" in out and wrong.item in out


def test_labels_outside_the_options_are_rejected(
    committed: list[CorpusItem], tmp_path: Path
) -> None:
    material, labels = tmp_path / "human-labeling.md", tmp_path / "human-labels.jsonl"
    text = labeling.render(committed)  # write が作る形（「ラベル:」が空）
    material.write_text(text.replace("ラベル:\n", "ラベル: no_such_class\n", 1), "utf-8")
    args = ["--material", str(material), "--out", str(labels)]
    assert labeling.main(["labels", "--labeler", "人", *args]) != 0
    assert not labels.exists()


def test_compare_reports_a_missing_label_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert labeling.main(["compare", "--labels", str(tmp_path / "none.jsonl")]) == 1
    assert "ラベルのファイルが無い" in capsys.readouterr().out


def test_received_labels_fit_the_corpus(committed: list[CorpusItem]) -> None:
    """人から受け取ったラベル（docs/human-labels.jsonl）があれば、項目と選択肢に合い、human-labeling.md の「ラベル:」と
    同じ。無ければ、比べるコマンドは無いことを報告する（人がラベルを付けるまで、このリポジトリには無い）。"""
    if not labeling.LABELS.exists():
        assert labeling.main(["compare"]) == 1
        return
    options = {item.item: {o.id for o in item.options} for item in committed}
    labels = load_labels(labeling.LABELS)
    assert Counter(label.item for label in labels).most_common(1)[0][1] == 1
    for label in labels:
        assert label.label in options[label.item], label
    found, _, errors = labeling.parse_labels(labeling.MATERIAL.read_text("utf-8"), committed, "人")
    assert errors == []
    assert {(x.item, x.label) for x in found} == {(x.item, x.label) for x in labels}
