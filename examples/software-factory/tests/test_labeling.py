"""人がラベルを付ける材料（docs/human-labeling.md）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

- 材料のコーパス（docs/human-labeling.corpus.jsonl）と human-labeling.md は、試しの実行から作り直したものと一致する
  （フィクスチャ、ペルソナ、記述を変えたら `python -m software_factory.labeling write` で作り直す）
- 材料は、往復 10 で代表を変えた所の、手引き第15.1節の目安で選んだ (対象, 訪問の区分, 印, 上流の違い) の組をすべて一つずつ
  含む。訪問 2 以降を見るのは、memory_in を持つステージと、そのステージを含むフェーズのゲート（workflow.yaml の memory_in
  から決まる）だけ。そのうち、見出しのほかは訪問 1 と同じ状態文書は渡さない（design、plan_tasks、architecture のゲートは
  訪問 2 以降がすべてそう）。組の中では短い状態文書を選び、それで intake.md を読む対象の訪問 2 以降の項目は、持ち帰った
  問いの回答を含む（往復 12 の「回答を含むものを先に」を外しても変わらない）
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
from typing import Any

import jsonschema
import pytest
import yaml
from software_factory import labeling
from software_factory.personas import PERSONAS
from software_factory.stages.deterministic import ROOT

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.testing.harness import marked_class
from harness_testing_framework.testing.oracle import CorpusItem, load_corpus, load_labels

NAMES = [p.name for p in PERSONAS]
WORKFLOW_DOC: dict[str, Any] = yaml.safe_load((ROOT / "workflow.yaml").read_text("utf-8"))
# intake.md を読む対象（訪問 2 以降の intake.md に持ち帰った問いの回答が入る）の (印, 上流の違い) の組
_READS_INTAKE: dict[tuple[str, str], set[tuple[str | None, str]]] = {
    ("stage", "intake"): {("goal", "vague_founder"), ("unknown", "vague_founder")},
    ("stage", "analyze"): {(m, p) for m in ("goal", "needs_unclear") for p in NAMES}
    | {("unknown", "vague_founder")},
    ("phase", "discovery"): {(None, p) for p in NAMES},
}
# 持ち帰った記憶を受け取るが、訪問 2 以降の状態文書が、見出しのほかは訪問 1 と同じになる対象（偽の本体は入り直しても同じ
# 代表を写し、上流も変わらない）の (印, 上流の違い) の組。試しの実行は、markov の訪問 2 以降に出るクラスをすべて置く
_REPEATED: dict[tuple[str, str], set[tuple[str | None, str]]] = {
    ("stage", "design"): {("goal", ""), ("requirements_gap", ""), ("unknown", "")},
    ("stage", "plan_tasks"): {("goal", ""), ("unknown", "")},
    ("phase", "architecture"): {(None, "")},
}
# 対象と訪問の区分（訪問 2 以降か）ごとの (印, 上流の違い) の組。上流の違いは、intake.md を読む対象ではペルソナ、unit_test
# では実装の変種。review（往復 13 で足した。memory_in が無いので訪問 1 だけ）には上流の違いが無い
SLOTS: dict[tuple[str, str, bool], set[tuple[str | None, str]]] = {
    **{(s, t, again): slots for (s, t), slots in _READS_INTAKE.items() for again in (False, True)},
    **{(s, t, False): slots for (s, t), slots in _REPEATED.items()},
    ("stage", "unit_test", False): {("tests_insufficient", v) for v in ("ok", "ok_b", "ok_fixed")},
    ("stage", "acceptance", False): {
        (m, p)
        for m in ("goal", "requirement_unmet", "requirement_misread", "unknown")
        for p in NAMES
    },
    ("stage", "review", False): {
        (m, "") for m in ("goal", "changes_requested", "design_flaw", "unknown")
    },
}


@pytest.fixture(scope="module")
def committed() -> list[CorpusItem]:
    return load_corpus(labeling.CORPUS)


@pytest.fixture(scope="module")
def trial(tmp_path_factory: pytest.TempPathFactory) -> list[CorpusItem]:
    return labeling.trial_corpus(tmp_path_factory.mktemp("labeling"))


def test_material_is_regenerated_from_the_trial_runs(
    committed: list[CorpusItem], trial: list[CorpusItem]
) -> None:
    items = labeling.select(trial)
    assert items == committed
    # 人が「ラベル:」を埋めた後も、それを空にすれば作り直したものと一致する
    assert labeling.blank_labels(labeling.MATERIAL.read_text("utf-8")) == labeling.render(items)


def test_material_covers_every_slot_once(committed: list[CorpusItem]) -> None:
    slots: dict[tuple[str, str, bool], set[tuple[str | None, str]]] = {}
    for item in committed:
        key = (item.scope, item.target, labeling.again(item))
        slot = (marked_class(item.state), labeling.upstream(item))
        assert slot not in slots.get(key, set()), item.item
        slots.setdefault(key, set()).add(slot)
        # 訪問 2 以降の intake.md を読む対象の項目は、応答（持ち帰った問いの回答）の入った状態文書
        if labeling.again(item) and item.target in ("intake", "analyze", "discovery"):
            assert labeling.responded(item), item.item
    assert slots == SLOTS
    assert len(committed) == sum(len(s) for s in SLOTS.values()) == 49
    assert len({item.item for item in committed}) == len(committed)


def test_later_visits_without_a_response_repeat_the_first_visit(trial: list[CorpusItem]) -> None:
    """訪問 2 以降も見る対象のうち design、plan_tasks、architecture のゲートは、試しの実行でどのクラスの訪問 2 以降も出て、
    その状態文書は見出しのほかは訪問 1 の項目と同じ（記述の当てはまり方が同じなので、訪問 1 の項目で代える）。intake.md を
    読む対象では、各組に、訪問 1 と違う（持ち帰った問いの回答を含む）訪問 2 以降の状態文書がある。"""
    repeated = labeling.same_as_first(trial)
    later = [i for i in trial if labeling.again(i) and labeling.wanted(i)]
    for target, slots in _REPEATED.items():
        items = [i for i in later if (i.scope, i.target) == target]
        assert {(marked_class(i.state), labeling.upstream(i)) for i in items} == slots, target
        assert all(i.item in repeated for i in items), target
    for target in _READS_INTAKE:
        assert any(
            i.item not in repeated and labeling.responded(i)
            for i in later
            if (i.scope, i.target) == target
        ), target


def test_later_visits_are_passed_only_for_targets_that_receive_carried_memory() -> None:
    """訪問 2 以降も渡す対象は、workflow.yaml で memory_in を持つステージと、そういうステージを持つフェーズのゲート。"""
    memory_in: dict[str, bool] = {}
    phases: dict[str, list[str]] = {}
    for phase in WORKFLOW_DOC["workflow"]["phases"]:
        phases[phase["id"]] = [stage["id"] for stage in phase["stages"]]
        for stage in phase["stages"]:
            memory_in[stage["id"]] = bool(stage["artifacts"].get("memory_in"))
    expected = {
        (scope, target)
        for scope, target in labeling.EVIDENCE
        if (memory_in[target] if scope == "stage" else any(memory_in[s] for s in phases[target]))
    }
    passed_again = labeling.AGAIN
    assert passed_again == expected
    assert ("stage", "acceptance") not in passed_again
    assert ("stage", "review") not in passed_again
    # unit_test も受け取るが、変えた代表 defective は確率 0 で、試しの実行もシナリオも訪問 1 にしか写さない（訪問 2 以降の
    # 項目は無い）。design、plan_tasks、architecture の訪問 2 以降は訪問 1 と同じ状態文書（上のテスト）
    assert passed_again == set(_READS_INTAKE) | set(_REPEATED) | {("stage", "unit_test")}
    assert {(s, t) for s, t, again in SLOTS if again} == set(_READS_INTAKE)


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
