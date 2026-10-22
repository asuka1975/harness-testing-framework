"""人がラベルを付ける材料（docs/human-labeling.md）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

- 材料のコーパス（docs/human-labeling.corpus.jsonl）と human-labeling.md は、試しの実行（と、シナリオだけが写す代表の
  シナリオ）から作り直したものと一致する（フィクスチャ、ペルソナ、記述を変えたら
  `uv run python -m software_factory.labeling write` で作り直す）
- 材料は、往復 10 で代表を変えた所の、手引き第15.1節の目安で選んだ (対象, 訪問の区分, 印, 上流の違い) の組をすべて一つずつ
  含む。訪問 2 以降を見るのは、memory_in を持つステージと、そのステージを含むフェーズのゲート（workflow.yaml の memory_in
  から決まる）だけ。そのうち、見出しのほかは訪問 1 と同じ状態文書は渡さない（design、plan_tasks、architecture のゲート、
  implement は訪問 2 以降がすべてそう）。上流の違いは、intake.md を読む対象では (ペルソナ, 持ち帰った問いの回答の有無)、
  unit_test では goal の実装の変種。シナリオだけが写す代表（plan_tasks/incomplete）は、シナリオで分類器が見る状態文書を
  （run_scenario の結果の置き場から）項目にする
- 人に渡す human-labeling.md は、印（分類器の選択、代表のクラス）、選んだ規則、組ごとの数、項目の id を、どの形でも含まない。
  材料の文は、項目の (scope, 対象, 選択肢, 印を除いた状態文書) と、どの項目が同じ実行のものか、だけで決まる（印のクラス、
  項目の id、出どころ、渡す順を変えても同じ文になる）。項目は通し番号で示し、番号と id の対応はコーパスの側（source の
  number と並び）に持つ。同じ実行の項目は続けて並べない
- 見せ方: 選択肢の記述と、対象の項目の過半（二つ以上）で同じ区切りは、対象の節の頭に一度だけ示す。項目の状態文書は、
  共通の区切りを見出しだけ（「（共通）」）にした形で、共通の区切りを戻すと印を除いた状態文書（印だけの行を落とし、区切りの
  間の空行を一つにしたもの）に戻る
- 埋めた「ラベル:」から contract/formats/label.schema.json の形の JSON Lines を作り、`oracle_report(MarkerClassifier(), ...)`
  で印と比べられる。全角のコロンも読む。読めない行と選択肢に無い id は、項目の番号を添えた誤り（終了コード 2）。「ラベル:」の
  後が空で次の行に文がある時は警告する
- ラベルのファイルが無ければ、比べるコマンドはそのことを報告する（テストをスキップしない）。受け取ったラベルのファイルが
  あれば、コーパスの項目と選択肢に合い、human-labeling.md の「ラベル:」と同じであることを確かめる
- 代表の前提（手引き第12節）: acceptance の requirement_unmet の代表の「Discount.apply が支払額を切り捨てている」は ok と
  ok_b でだけ成り立つので、材料の acceptance は主経路の実装（ok、ok_b）の後だけ。review の changes_requested の代表の
  指摘は、review に届くどの単体テストの代表でも成り立つ
"""

import hashlib
import itertools
import json
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

import jsonschema
import pytest
import yaml
from software_factory import labeling
from software_factory.personas import PERSONAS
from software_factory.stages.deterministic import FIXTURES, ROOT, SCENARIOS, run
from software_factory.stages.probabilistic import TABLE

from harness_testing_framework.contract import load_contract_schema
from harness_testing_framework.testing.harness import marked_class, unmarked
from harness_testing_framework.testing.oracle import CorpusItem, load_corpus, load_labels

NAMES = [p.name for p in PERSONAS]
C = labeling.CARRIED
WORKFLOW_DOC: dict[str, Any] = yaml.safe_load((ROOT / "workflow.yaml").read_text("utf-8"))
# intake.md を読む対象の訪問 1 の (印, 上流の違い) の組。訪問 2 以降は、同じ組に持ち帰った問いの回答が入ったもの
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
    ("stage", "implement"): {
        ("goal", ""),
        ("quality_violation", ""),
        ("task_unclear", ""),
        ("unknown", ""),
    },
}
# 対象と訪問の区分（訪問 2 以降か）ごとの (印, 上流の違い) の組。上流の違いは、intake.md を読む対象では (ペルソナ, 持ち帰った
# 問いの回答の有無)（回答があれば末尾に labeling.CARRIED）、unit_test では実装の変種。plan_tasks の design_incomplete は
# シナリオだけが写す代表。review と implement には上流の違いが無い
SLOTS: dict[tuple[str, str, bool], set[tuple[str | None, str]]] = {
    **{(s, t, False): slots for (s, t), slots in _READS_INTAKE.items()},
    **{(s, t, True): {(m, p + C) for m, p in slots} for (s, t), slots in _READS_INTAKE.items()},
    **{(s, t, False): slots for (s, t), slots in _REPEATED.items()},
    ("stage", "plan_tasks", False): _REPEATED[("stage", "plan_tasks")]
    | {("design_incomplete", "")},
    ("stage", "unit_test", False): {("tests_insufficient", v) for v in ("ok", "ok_b", "ok_fixed")},
    ("stage", "acceptance", False): {
        (m, p + c)
        for m in ("goal", "requirement_unmet", "requirement_misread", "unknown")
        for p in NAMES
        for c in ("", C)
    },
    ("stage", "review", False): {
        (m, "") for m in ("goal", "changes_requested", "design_flaw", "unknown")
    },
}
# 人に渡す文に書かないもの（選んだ規則と組ごとの数を述べる語）
RULE_WORDS = (
    "まとめ方",
    "ごとに一つ",
    "上流の違い",
    "ペルソナ",
    "組ごと",
    "項目の数",
    "合わせて",
    "印でまとめ",
)


@pytest.fixture(scope="module")
def committed() -> list[CorpusItem]:
    return load_corpus(labeling.CORPUS)


@pytest.fixture(scope="module")
def trial(tmp_path_factory: pytest.TempPathFactory) -> list[CorpusItem]:
    return labeling.trial_corpus(tmp_path_factory.mktemp("labeling"))


@pytest.fixture(scope="module")
def material() -> str:
    return labeling.MATERIAL.read_text("utf-8")


def _run_of(item: CorpusItem) -> str:
    return item.item.rsplit("-", 1)[0]


def _outside_fences(text: str) -> str:
    """材料の文のうち、状態文書と共通の区切りの囲み（~~~~~~text … ~~~~~~）の外。"""
    out, inside = [], False
    for line in text.split("\n"):
        if line in (f"{labeling.FENCE}text", labeling.FENCE):
            inside = line != labeling.FENCE
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def test_material_is_regenerated_from_the_trial_runs(
    committed: list[CorpusItem], trial: list[CorpusItem], material: str
) -> None:
    items = labeling.select(trial)
    assert items == committed
    # 人が「ラベル:」を埋めた後も、それを空にすれば作り直したものと一致する
    assert labeling.blank_labels(material) == labeling.render(items)


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
    assert len(committed) == sum(len(s) for s in SLOTS.values()) == 66
    assert len({item.item for item in committed}) == len(committed)


def test_later_visits_without_a_response_repeat_the_first_visit(trial: list[CorpusItem]) -> None:
    """訪問 2 以降も見る対象のうち design、plan_tasks、architecture のゲート、implement は、試しの実行でどのクラスの
    訪問 2 以降も出て、その状態文書は見出しのほかは訪問 1 の項目と同じ（記述の当てはまり方が同じなので、訪問 1 の項目で
    代える）。intake.md を読む対象では、各組に、訪問 1 と違う（持ち帰った問いの回答を含む）訪問 2 以降の状態文書がある。"""
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
    # 項目は無い）。design、plan_tasks、architecture、implement の訪問 2 以降は訪問 1 と同じ状態文書（上のテスト）
    assert passed_again == set(_READS_INTAKE) | set(_REPEATED) | {("stage", "unit_test")}
    assert {(s, t) for s, t, again in SLOTS if again} == set(_READS_INTAKE)


def test_scenario_only_representative_is_the_state_the_classifier_sees(
    committed: list[CorpusItem], tmp_path: Path
) -> None:
    """plan_tasks/incomplete（シナリオ plan_tasks_design_incomplete_rollback だけが写す）の項目の状態文書は、そのシナリオを
    run_scenario で走らせた時に分類器が見た状態文書（実行記録の evaluation の classification.state の SHA-256 を、結果の
    置き場 store から読んだもの。手引き第15.1節）そのもの。scenario_corpus の各項目も、実行記録の評価ごとにその読み方で
    読んだ状態文書と同じ（往復 15 で、ランタイムを組み立て直す回避を結果の store に置き換えた。コミットした材料は往復 14 の
    回避で作ったもので、test_material_is_regenerated_from_the_trial_runs が、置き換えた後も材料の文が変わらないことを確かめる）。"""
    name, (scope, target, text) = next(iter(labeling.SCENARIO_ONLY.items()))
    items = [i for i in committed if i.source.get("scenario") == name]
    assert len(items) == 1
    item = items[0]
    assert (item.scope, item.target) == (scope, target) and text in item.state
    assert marked_class(item.state) == "design_incomplete"
    result = run(SCENARIOS / f"{name}.yaml", tmp_path / "run")
    assert result.problems == []
    # 評価の (scope, 対象, seq) → 分類器が見た状態文書。対象は、ゲート（scope が phase）ではフェーズの id
    seen: dict[tuple[str, str, int], str] = {}
    for event in result.trace:
        classification = event.get("classification")
        if event["event"] != "evaluation" or classification is None:
            continue
        assert isinstance(classification, dict) and isinstance(event["seq"], int)
        digest = str(classification["state"])
        state = result.store.get(digest).decode("utf-8")
        assert hashlib.sha256(state.encode("utf-8")).hexdigest() == digest
        scope_of = str(event["scope"])
        target_of = str(event["phase"] if scope_of == "phase" else event["stage"])
        seen[(scope_of, target_of, event["seq"])] = state
    assert item.state in {s for (sc, t, _), s in seen.items() if (sc, t) == (scope, target)}
    built = labeling.scenario_corpus(name, tmp_path / "corpus")
    for i in built:
        assert seen[(i.scope, i.target, i.source["seq"])] == i.state, i.item
    assert {i.state for i in built} == set(seen.values())


def test_material_does_not_depend_on_marks_ids_sources_or_order(
    committed: list[CorpusItem],
) -> None:
    """材料の文は、印のクラス、項目の id（同じ実行かどうかのほか）、出どころ（分類器の選択を含む）、渡す順によらない。
    印も、選んだ規則も、項目の id も、並べ方から推せない。"""
    text = labeling.render(committed)
    assert labeling.arrange(committed) == committed

    def remark(item: CorpusItem) -> CorpusItem:
        state = re.sub(r"\[\[class ([^=\]]+)=[^\]]*\]\]", r"[[class \1=zz_other]]", item.state)
        return replace(item, state=state)

    runs = sorted({_run_of(i) for i in committed}, reverse=True)
    renamed = {run: f"r{n:04d}" for n, run in enumerate(runs)}

    def rename(item: CorpusItem) -> CorpusItem:
        seq = int(item.item.rsplit("-", 1)[1])
        return replace(item, item=f"{renamed[_run_of(item)]}-{seq * 7 + 1}", source={"choice": "x"})

    for variant in (
        [remark(i) for i in committed],
        [rename(i) for i in committed],
        list(reversed(committed)),
        sorted(committed, key=lambda i: i.item),
    ):
        assert labeling.render(labeling.arrange(variant)) == text
    # 印を変えれば状態文書（印つき）は変わるが、人に見せる状態文書は変わらない
    assert all(labeling.shown_state(remark(i)) == labeling.shown_state(i) for i in committed)


def test_material_hides_marks_ids_rules_and_counts(
    committed: list[CorpusItem], material: str
) -> None:
    text = labeling.render(committed)
    for written in (text, material):
        assert "[[class" not in written
        for item in committed:
            assert item.item not in written
            assert _run_of(item) not in written
        for word in ("review-findings", "progress.md", "choice", "seq"):
            assert word not in written, word
    # 項目は通し番号だけで示し、番号と id の対応はコーパスの側（並びと source の number）に持つ
    numbers = [int(n) for n in re.findall(r"^### 項目 (\d+)$", text, flags=re.M)]
    assert numbers == list(range(1, len(committed) + 1))
    assert [item.source["number"] for item in committed] == numbers
    assert all("choice" not in item.source for item in committed)
    # 選んだ規則と組ごとの数を書かない（状態文書と選択肢の記述の外）
    prose = "\n".join(
        line
        for line in _outside_fences(text).split("\n")
        if not line.startswith(("- `", "選べる選択肢:"))
    )
    for word in RULE_WORDS:
        assert word not in prose, word
    assert not re.search(r"\d+\s*項目", prose)
    assert str(len(committed)) not in re.sub(r"^### 項目 \d+$", "", prose, flags=re.M)
    # 選び方は README にあり、ラベルを付け終えるまで読まない
    head = text.split("\n## ", 2)[:2]
    assert "ラベルを付け終えるまで" in "\n".join(head) and "記述と代表の整合" in "\n".join(head)
    readme = (ROOT / "README.md").read_text("utf-8")
    section = readme.split("\n## 記述と代表の整合", 1)[1]
    assert "ラベルを付け終えるまで" in section.split("\n\n")[1]


def test_items_of_the_same_run_are_not_adjacent(committed: list[CorpusItem]) -> None:
    for a, b in itertools.pairwise(committed):
        assert _run_of(a) != _run_of(b), (a.item, b.item)
    # 対象ごとにまとめ、対象の順はワークフローの順
    order = list(labeling.EVIDENCE)
    targets = [order.index((i.scope, i.target)) for i in committed]
    assert targets == sorted(targets)


def _target_sections(text: str) -> dict[str, list[str]]:
    """材料の、対象の節（「## 」の見出し）ごとの行。囲みの中の見出しは数えない。"""
    sections: dict[str, list[str]] = {}
    current: list[str] = []
    inside = False
    for line in text.split("\n"):
        if line in (f"{labeling.FENCE}text", labeling.FENCE):
            inside = line != labeling.FENCE
        elif not inside and line.startswith("## "):
            current = sections.setdefault(line[3:], [])
            continue
        current.append(line)
    return sections


def test_options_and_common_sections_are_shown_once_per_target(
    committed: list[CorpusItem],
) -> None:
    text = labeling.render(committed)
    sections = _target_sections(text)
    blocks = labeling.item_blocks(text)
    assert [n for n, _ in blocks] == list(range(1, len(committed) + 1))
    for (scope, target), group in labeling.by_target(committed).items():
        lines = sections[labeling.target_title(scope, target)]
        joined = "\n".join(lines)
        head = joined.split("\n### 項目 ", 1)[0]
        # 選択肢の記述は、対象の節の頭に一度だけ
        for option in {o.id: o for i in group for o in i.options}.values():
            assert joined.count(f"- `{option.id}`: {option.description}") == 1
            assert f"- `{option.id}`: {option.description}" in head
        common = labeling.common_sections(group)
        for item in group:
            number = int(item.source["number"])
            block = dict(blocks)[number]
            assert f"選べる選択肢: {labeling.option_ids(item)}" in block
            assert all(o.description not in block for o in item.options)
            # 共通の区切りを戻すと、人に見せる状態文書に戻る
            fenced = block.split(f"{labeling.FENCE}text\n", 1)[1]
            shown = fenced.split(f"\n{labeling.FENCE}\n", 1)[0]
            for name, body in common.items():
                shown = shown.replace(f"{name}{labeling.COMMON}", body)
            assert shown == labeling.shown_state(item), number
        # 共通の区切りは、対象の節の頭の囲みに一度だけ示し、項目の過半（二つ以上）がそれと同じ
        if common:
            shared = head.split(f"{labeling.FENCE}text\n", 1)[1].split(f"\n{labeling.FENCE}", 1)[0]
            assert shared == "\n\n".join(common.values())
        else:
            assert labeling.FENCE not in head
        for name in common:
            same = [
                i
                for i in group
                if f"{name}{labeling.COMMON}" in dict(blocks)[int(i.source["number"])]
            ]
            assert len(same) >= 2 and 2 * len(same) > len(group), name
    # 見せ方で減らした（全項目に選択肢の記述と状態文書の全文を並べた形の半分より短い）
    full = sum(
        len(labeling.shown_state(i)) + sum(len(o.description) for o in i.options) for i in committed
    )
    assert len(text) < full / 2


def test_only_mark_lines_are_dropped_from_the_shown_state(committed: list[CorpusItem]) -> None:
    """人に見せる状態文書は、印を除いた状態文書から、印だけの行（印の跡が空か「#」だけになる行）を落とし、区切りの間の空行を
    一つにしたもの。ほかの行は変えない。"""
    mark_only = re.compile(r"(#\s*)?\[\[class [^\]]*\]\]\s*")
    for item in committed:
        kept = [unmarked(line) for line in item.state.split("\n") if not mark_only.fullmatch(line)]
        shown = labeling.shown_state(item)
        assert "[[class" not in shown
        assert [line for line in shown.split("\n") if line] == [line for line in kept if line]


def test_reading_guide_states_the_policy_and_the_facts(committed: list[CorpusItem]) -> None:
    head = labeling.render(committed).split("\n## ステージ ", 1)[0]
    for phrase in (
        "分類器と同じ立場",
        "字義どおり",
        "中身の条件",
        "括弧の中の列挙",
        "迷ったら unknown",
        "「（なし）」",
        "持ち帰った問いとその回答",
        "goal に優先する",
        "跡",
        "examples/software-factory/",
        "uv run python -m software_factory.labeling labels --labeler",
        "uv run python -m software_factory.labeling compare",
    ):
        assert phrase in head, phrase


def test_commands_say_where_to_run() -> None:
    readme = (ROOT / "README.md").read_text("utf-8").split("\n## 記述と代表の整合", 1)[1]
    readme = readme.split("\n## ", 1)[0]
    for text in (readme, labeling.__doc__ or ""):
        assert "examples/software-factory/" in text
        assert "uv run python -m software_factory.labeling" in text


def _set_label(text: str, number: int, line: str) -> str:
    """材料の項目 number の「ラベル:」の行を line にした文。"""
    head, sep, rest = text.partition(f"\n### 項目 {number}\n")
    body, nxt, tail = rest.partition("\n### 項目 ")
    body = re.sub(r"^ラベル:$", lambda _: line, body, count=1, flags=re.M)
    return head + sep + body + nxt + tail


def _filled(
    text: str, committed: list[CorpusItem], wrong: int | None = None, skip: int | None = None
) -> str:
    """印どおりのラベル（ゲートは goal）を「ラベル:」に書いた材料。番号 wrong の項目だけは unknown と理由を書き、番号 skip の
    項目は空のままにする。"""
    for item in committed:
        number = int(item.source["number"])
        if number == skip:
            continue
        label = "unknown（迷った）" if number == wrong else str(marked_class(item.state) or "goal")
        text = _set_label(text, number, f"ラベル: {label}")
    return text


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
    # 番号から id を引く（ラベルの item はコーパスの id）
    assert [label.item for label in load_labels(labels)] == [i.item for i in committed]
    capsys.readouterr()
    assert labeling.main(["compare", "--labels", str(labels)]) == 0
    out = capsys.readouterr().out
    assert "kappa 1.000" in out and "食い違い: 0 件" in out

    # 一項目だけ印と違うラベル（unknown と理由）にすると、その項目を番号で挙げる
    wrong = next(i for i in committed if marked_class(i.state) == "goal")
    number = int(wrong.source["number"])
    material.write_text(_filled(text, committed, wrong=number), "utf-8")
    assert labeling.main(["labels", "--labeler", "人", *args]) == 0
    capsys.readouterr()
    assert labeling.main(["compare", "--labels", str(labels)]) == 0
    out = capsys.readouterr().out
    assert "食い違い: 1 件" in out and f"項目 {number}（" in out


def test_label_lines_accept_a_fullwidth_colon_and_backquotes(committed: list[CorpusItem]) -> None:
    text = labeling.render(committed)
    first, second = committed[0], committed[1]
    text = _set_label(text, 1, f"ラベル：{first.options[-1].id}（理由）")
    text = _set_label(text, 2, f"ラベル: `{second.options[0].id}`")
    found, empty, errors, warnings = labeling.parse_labels(text, committed, "人")
    assert errors == [] and warnings == []
    assert [(x.item, x.label) for x in found] == [
        (first.item, first.options[-1].id),
        (second.item, second.options[0].id),
    ]
    assert len(empty) == len(committed) - 2


@pytest.mark.parametrize(
    "line", ["ラベル: ゴール", "ラベル: no_such_class", "ラベル goal", "ラベル: Goal"]
)
def test_unreadable_labels_are_errors_with_the_item_number(
    committed: list[CorpusItem],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    line: str,
) -> None:
    material, labels = tmp_path / "human-labeling.md", tmp_path / "human-labels.jsonl"
    material.write_text(_set_label(labeling.render(committed), 3, line), "utf-8")
    args = ["--material", str(material), "--out", str(labels)]
    capsys.readouterr()
    assert labeling.main(["labels", "--labeler", "人", *args]) == 2
    assert "項目 3:" in capsys.readouterr().out
    assert not labels.exists()


def test_text_after_an_empty_label_is_warned(
    committed: list[CorpusItem], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    material, labels = tmp_path / "human-labeling.md", tmp_path / "human-labels.jsonl"
    text = labeling.render(committed)
    filled = _set_label(_filled(text, committed, skip=4), 4, "ラベル:\ngoal")
    material.write_text(filled, "utf-8")
    assert labeling.blank_labels(filled) == text
    args = ["--material", str(material), "--out", str(labels)]
    capsys.readouterr()
    assert labeling.main(["labels", "--labeler", "人", *args]) == 0
    out = capsys.readouterr().out
    assert "警告" in out and "項目 4:" in out
    assert len(load_labels(labels)) == len(committed) - 1


def test_compare_reports_a_missing_label_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert labeling.main(["compare", "--labels", str(tmp_path / "none.jsonl")]) == 1
    assert "ラベルのファイルが無い" in capsys.readouterr().out


def test_received_labels_fit_the_corpus(committed: list[CorpusItem], material: str) -> None:
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
    found, _, errors, _ = labeling.parse_labels(material, committed, "人")
    assert errors == []
    assert {(x.item, x.label) for x in found} == {(x.item, x.label) for x in labels}


def _discount(variant: str) -> dict[str, Any]:
    """implement の変種の repo/src/shopcart/discount.py を実行した名前空間。import しない（フィクスチャの下に __pycache__ を
    作ると、偽の本体がそれも作業領域に写し、指標 out_of_scope_changes が落ちる）。"""
    path = FIXTURES / "implement" / variant / "repo" / "src" / "shopcart" / "discount.py"
    namespace: dict[str, Any] = {"__name__": f"_discount_{variant}"}
    exec(compile(path.read_text("utf-8"), str(path), "exec"), namespace)
    return namespace


def test_requirement_unmet_is_passed_only_after_the_implementations_it_holds_for(
    committed: list[CorpusItem], trial: list[CorpusItem]
) -> None:
    """acceptance の requirement_unmet の代表（333 円に PCT10 で 299 円、Discount.apply が支払額を切り捨てている）は、
    分布テストの主経路の goal の実装（ok、ok_b）でだけ成り立ち、正しい実装 ok_fixed とは食い違う（手引き第12節）。
    markov では ok_fixed を置かないので組まないが、divergent と試しの実行 labeling では組む。材料からはその組を外す。"""
    for variant in labeling.IMPLEMENTATIONS:
        paid = _discount(variant)["parse_code"]("PCT10").apply(333)
        assert paid == (299 if variant in labeling.MAIN_IMPLEMENTATIONS else 300), variant
    assert not list(FIXTURES.rglob("__pycache__"))
    assert {"ok", "ok_b"} == labeling.MAIN_IMPLEMENTATIONS
    profiles = TABLE["profiles"]
    for name in ("markov", "divergent"):
        implement = set(profiles[name]["implement"]["first"]) | set(
            profiles[name]["implement"]["again"]
        )
        assert ("ok_fixed" in implement) == (name == "divergent"), name
        assert profiles[name]["acceptance"]["first"]["unmet"] > 0
    assert all(
        labeling.implementation(i) in labeling.MAIN_IMPLEMENTATIONS
        for i in committed
        if i.target == "acceptance"
    )
    assert any(
        i.target == "acceptance"
        and marked_class(i.state) == "requirement_unmet"
        and labeling.implementation(i) == "ok_fixed"
        for i in trial
    )


def test_review_findings_hold_for_every_unit_test_that_reaches_review() -> None:
    """review の changes_requested の代表の指摘（無効なコードを Cart.total で確かめるテストが無い）は、review に届くどの
    単体テストの代表（unit_test の goal になる変種）でも事実で、repo/tests/ の修正で解消する（design.md は変えない）。"""
    review = json.loads((FIXTURES / "review" / "changes" / "review.json").read_text("utf-8"))
    blocking = [f for f in review["findings"] if f["blocking"]]
    assert len(blocking) == 1 and blocking[0]["path"].startswith("repo/tests/")
    assert blocking[0]["path"] in review["reviewed"]
    goal_tests = set()
    for name, spec in TABLE["variants"]["unit_test"].items():
        for resolved in spec.get("by_family", {}).values() or [spec]:
            if resolved["class"] == "goal":
                goal_tests.add(resolved.get("fixture", name))
    assert goal_tests == {"ok", "defect_passed"}
    invalid = ("PCT0", "PCT51", "XYZ", "OFF")
    for name in goal_tests:
        tests = (FIXTURES / "unit_test" / name / "repo" / "tests" / "test_discount.py").read_text(
            "utf-8"
        )
        assert all(f'"{code}"' in tests for code in invalid), name
        assert "parse_code(code)" in tests, name
        assert not re.search(r"\.total\((code|\"(PCT0|PCT51|XYZ|OFF)\")\)", tests), name
    memory = TABLE["variants"]["review"]["changes"]["memory"]
    assert memory["design_issues"] == []
    assert [blocking[0]["path"] in m and "Cart.total" in m for m in memory["review_findings"]] == [
        True
    ]
