"""人がラベルを付ける材料（docs/human-labeling/ の下）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

- 材料のコーパス（docs/human-labeling.corpus.jsonl）と docs/human-labeling/ の下のファイルは、試しの実行（と、シナリオだけが
  写す代表のシナリオ）から作り直したものと一致する（フィクスチャ、ペルソナ、記述を変えたら
  `uv run python -m software_factory.labeling write` で作り直す）
- 材料は、往復 10 で代表を変えた所の、手引き第15.1節の目安で選んだ (対象, 訪問の区分, 印, 上流の違い) の組をすべて一つずつ
  含む。訪問 2 以降を見るのは、memory_in を持つステージと、そのステージを含むフェーズのゲート（workflow.yaml の memory_in
  から決まる）だけ。そのうち、見出しのほかは訪問 1 と同じ状態文書は渡さない（design、plan_tasks、architecture のゲート、
  implement は訪問 2 以降がすべてそう）。上流の違いは、intake.md を読む対象では (ペルソナ, 持ち帰った問いの回答の有無)、
  unit_test では goal の実装の変種。review と acceptance の goal の実装の変種は、repo/src/shopcart/discount.py だけが違う
  のでまとめる。シナリオだけが写す代表（plan_tasks/incomplete）は、シナリオで分類器が見る状態文書を（run_scenario の結果の
  置き場から）項目にする
- 人に渡す材料は、印（分類器の選択、代表のクラス）、比べる相手の答え、選んだ規則、組ごとの数、項目の id を、地の文、並び、
  見せ方のどこにも含まない。材料の文は、項目の (scope, 対象, 選択肢, 印を除いた状態文書) と、どの項目が同じ実行のものか、
  だけで決まる（印のクラス、項目の id、出どころ、渡す順を変えても同じ文になる）。項目は通し番号で示し、番号と id の対応は
  コーパスの側（source の number と並び）に持つ。同じ実行の項目は続けて並べない
- 材料は、読み方のファイル（00-guide.md）と、対象ごとのファイルに分ける（後の対象とゲートの状態文書は前の対象の goal の
  成果物を含み、前の対象の印が推せるため。docs/review-findings.md の I-M2）。対象のファイルはワークフローの順で、ゲートは
  そのフェーズの最終ステージの直後（手引き第15.1節の 2）。前のファイルは、後の対象が書いた成果物を含まない。各ファイルの冒頭に、前のファイルを
  付け終えるまで開かないこと、付け終えたラベルを後で変えないこと、ほかの項目やファイルと見比べないことを書く
- 見せ方: 選択肢の記述と、対象の項目の過半（二つ以上）で同じ区切りは、対象のファイルの頭に一度だけ示す。項目の状態文書は、
  共通の区切りを見出しだけ（「（共通）」）にした形で、共通の区切りを戻すと印を除いた状態文書（印だけの行を落とし、区切りの
  間の空行を一つにしたもの）に戻る
- 読み方は事実と頼みだけ（人間の決定で、記述の読み方を決める二つの方針を外した。docs/review-findings.md の I）。材料に
  現れる置き書きは、すべて読み方に挙げる
- 埋めた「ラベル:」から contract/formats/label.schema.json の形の JSON Lines を作り、`oracle_report(MarkerClassifier(), ...)`
  で印と比べられる。全角のコロンも読む。読めない行、選択肢に無い id、括弧の外の二つ以上の id、別のファイルにある項目は、
  項目の番号を添えた誤り（終了コード 2）。「ラベル:」の後が空で次の行に文がある時は警告する
- ラベルのファイルが無ければ、比べるコマンドはそのことを報告する（テストをスキップしない）。受け取ったラベルのファイルが
  あれば、コーパスの項目と選択肢に合い、材料の「ラベル:」と同じであることを確かめる
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
from software_factory.stages.probabilistic import DISCOUNT, TABLE

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
# シナリオだけが写す代表。review と implement には上流の違いが無い（review の実装の変種はまとめる）
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
# 比べる相手の答えを述べる句（人に渡す文に書かない。docs/review-findings.md の I-M1）
ANSWER_PHRASES = ("ゲートは goal", "（ゲートは", "goal と比べ", "印（", "ゲートの項目は goal")
# 材料に現れうる置き書き（行の全体が括弧の中の文。箇条の印が付いてもよい）
PLACEHOLDER_LINE = re.compile(r"^\s*(?:- )?[（(][^（）()]+[）)]\s*$")
_ID_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])([a-z][a-z0-9_]*)(?![A-Za-z0-9_-])")


@pytest.fixture(scope="module")
def committed() -> list[CorpusItem]:
    return load_corpus(labeling.CORPUS)


@pytest.fixture(scope="module")
def trial(tmp_path_factory: pytest.TempPathFactory) -> list[CorpusItem]:
    return labeling.trial_corpus(tmp_path_factory.mktemp("labeling"))


@pytest.fixture(scope="module")
def material() -> dict[str, str]:
    return labeling.read_material(labeling.MATERIAL_DIR)


@pytest.fixture(scope="module")
def rendered(committed: list[CorpusItem]) -> dict[str, str]:
    return labeling.render(committed)


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


def _inside_fences(text: str) -> list[str]:
    """材料の文のうち、囲みの中の行。"""
    out, inside = [], False
    for line in text.split("\n"):
        if line in (f"{labeling.FENCE}text", labeling.FENCE):
            inside = line != labeling.FENCE
            continue
        if inside:
            out.append(line)
    return out


def _prose(text: str) -> str:
    """地の文: 囲みの外から、選択肢の記述（ワークフロー定義の記述そのもの）と、選べる選択肢の id の行を除いたもの。"""
    return "\n".join(
        line
        for line in _outside_fences(text).split("\n")
        if not line.startswith(("- `", "選べる選択肢:"))
    )


def _sentences(prose: str) -> list[str]:
    """地の文の文: 段落と箇条（折り返しの行を含む）を単位にし、さらに「。」で分ける。"""
    units = re.split(r"\n(?=\s*(?:- |\d+\. |#))|\n\n", prose)
    return [s for unit in units for s in _flat(unit).split("。") if s.strip()]


def _flat(text: str) -> str:
    """折り返した行をつないだ文（改行と、続く行の頭の空白を除く）。"""
    return re.sub(r"\n\s*", "", text)


def _option_ids(corpus: list[CorpusItem]) -> set[str]:
    return {o.id for item in corpus for o in item.options}


def _head(text: str) -> str:
    """ファイルの最初の「## 」の節より前（冒頭の頼み）。"""
    return text.split("\n## ", 1)[0]


def _target_files(files: dict[str, str]) -> list[str]:
    """対象ごとのファイルの名前（並びの順）。"""
    return [name for name in sorted(files) if name != labeling.GUIDE]


def _items_in(text: str) -> list[int]:
    return [n for n, _ in labeling.item_blocks(text)]


def test_material_is_regenerated_from_the_trial_runs(
    committed: list[CorpusItem],
    trial: list[CorpusItem],
    material: dict[str, str],
    rendered: dict[str, str],
) -> None:
    items = labeling.select(trial)
    assert items == committed
    # 人が「ラベル:」を埋めた後も、それを空にすれば作り直したものと一致する
    assert sorted(material) == sorted(rendered)
    for name, text in material.items():
        assert labeling.blank_labels(text) == rendered[name], name
    # 一つのファイルにまとめた前の材料は無い
    assert not (labeling.DOCS / "human-labeling.md").exists()
    assert sorted(p.name for p in labeling.MATERIAL_DIR.iterdir()) == sorted(rendered)


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
    読んだ状態文書と同じ。"""
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
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    """材料の文（ファイルの分け方、並び、見せ方を含む）は、印のクラス、項目の id（同じ実行かどうかのほか）、出どころ
    （分類器の選択を含む）、渡す順によらない。印も、選んだ規則も、項目の id も、並べ方や見せ方から推せない。"""
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
        assert labeling.render(labeling.arrange(variant)) == rendered
    # 印を変えれば状態文書（印つき）は変わるが、人に見せる状態文書は変わらない
    assert all(labeling.shown_state(remark(i)) == labeling.shown_state(i) for i in committed)


def test_material_hides_marks_ids_rules_and_counts(
    committed: list[CorpusItem], material: dict[str, str], rendered: dict[str, str]
) -> None:
    for files in (rendered, material):
        for name, written in files.items():
            assert "[[class" not in written, name
            for item in committed:
                assert item.item not in written
                assert _run_of(item) not in written
            for word in ("review-findings", "progress.md", "choice", "seq"):
                assert word not in written, (name, word)
    # 項目は全ファイルを通した通し番号だけで示し、番号と id の対応はコーパスの側（並びと source の number）に持つ
    numbers = [n for name in _target_files(rendered) for n in _items_in(rendered[name])]
    assert numbers == list(range(1, len(committed) + 1))
    assert [item.source["number"] for item in committed] == numbers
    assert all("choice" not in item.source for item in committed)
    # 選んだ規則と組ごとの数を書かない（状態文書と選択肢の記述の外）
    for name, text in rendered.items():
        prose = _prose(text)
        for word in RULE_WORDS:
            assert word not in prose, (name, word)
        assert not re.search(r"\d+\s*項目", prose), name
        assert str(len(committed)) not in re.sub(r"^### 項目 \d+$", "", prose, flags=re.M), name
    # 選び方は README にあり、ラベルを付け終えるまで読まない
    head = _head(rendered[labeling.GUIDE])
    assert "ラベルを付け終えるまで" in head and "記述と代表の整合" in head
    readme = (ROOT / "README.md").read_text("utf-8")
    section = readme.split("\n## 記述と代表の整合", 1)[1]
    assert "ラベルを付け終えるまで" in section.split("\n\n")[1]


def test_prose_does_not_state_the_answers_to_compare_with(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    """地の文は、比べる相手の答え（ゲートの項目は goal と比べる、など）を述べない（docs/review-findings.md の I-M1）。比べ方と
    ゲートを述べる文には、選択肢の id が一つも無い。"""
    ids = _option_ids(committed)
    for name, text in rendered.items():
        prose = _prose(text)
        for phrase in ANSWER_PHRASES:
            assert phrase not in _flat(prose), (name, phrase)
        for sentence in _sentences(prose):
            if "比べ" in sentence or "ゲート" in sentence or "印と" in sentence:
                found = set(_ID_TOKEN.findall(sentence)) & ids
                assert not found, (name, sentence, found)
    assert "ラベルを印と比べ" in _flat(_prose(rendered[labeling.GUIDE]))


def test_items_of_the_same_run_are_not_adjacent(committed: list[CorpusItem]) -> None:
    for a, b in itertools.pairwise(committed):
        assert _run_of(a) != _run_of(b), (a.item, b.item)
    # 対象ごとにまとめ、対象の順は材料のファイルの順
    order = list(labeling.ORDER)
    targets = [order.index((i.scope, i.target)) for i in committed]
    assert targets == sorted(targets)


def _workflow_order(targets: set[tuple[str, str]]) -> list[tuple[str, str]]:
    """workflow.yaml のフェーズとステージの順で、ゲートはそのフェーズの（材料にある）最終ステージの直後に置いた対象の順。"""
    out: list[tuple[str, str]] = []
    for phase in WORKFLOW_DOC["workflow"]["phases"]:
        out += [("stage", s["id"]) for s in phase["stages"] if ("stage", s["id"]) in targets]
        if ("phase", phase["id"]) in targets:
            out.append(("phase", phase["id"]))
    return out


def test_material_is_split_into_files_in_the_order_of_the_targets(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    """材料は、読み方のファイルと、対象ごとのファイルに分ける。対象のファイルはワークフローの順で、ゲートはそのフェーズの
    最終ステージの直後（手引き第15.1節の 2 の「そのフェーズの最終ステージの項目の直後」）。各ファイルの冒頭に、付ける順と、
    見比べないことを頼む（docs/review-findings.md の I-M2）。"""
    targets = {(i.scope, i.target) for i in committed}
    expected = _workflow_order(targets)
    assert list(labeling.ORDER) == _workflow_order(set(labeling.EVIDENCE))
    # 手引きの字のとおり: ゲートのファイルの直前は、workflow.yaml のそのフェーズの最後のステージ（材料に対象があるかに
    # よらない）のファイル。_workflow_order は対象にある最後のステージの後に置くので、この例でそれが同じことも確かめる
    for k, (kind, gate) in enumerate(expected):
        if kind == "phase":
            phase = next(p for p in WORKFLOW_DOC["workflow"]["phases"] if p["id"] == gate)
            assert k > 0 and expected[k - 1] == ("stage", phase["stages"][-1]["id"]), gate
    names = _target_files(rendered)
    assert names[0] > labeling.GUIDE and len(names) == len(expected)
    by_file = labeling.file_names(committed)
    assert [by_file[t] for t in expected] == names
    for n, (name, target) in enumerate(zip(names, expected, strict=True), start=1):
        assert name.startswith(f"{n:02d}-"), name
        numbers = set(_items_in(rendered[name]))
        assert numbers == {
            int(i.source["number"]) for i in committed if (i.scope, i.target) == target
        }, name
        # ファイルの冒頭の頼み: 読み方のファイル、付ける順（前のファイルを付け終えるまで開かない）、付け終えたラベルを
        # 変えない、見比べない
        head = _flat(_head(rendered[name]))
        for phrase in (labeling.GUIDE, "付け終えるまで", "開かない", "後で変えない", "見比べない"):
            assert phrase in head, (name, phrase)
        if n > 1:
            assert names[n - 2] in head, name
        if n < len(names):
            assert names[n] in head, name
    assert _items_in(rendered[labeling.GUIDE]) == []
    guide = _flat(rendered[labeling.GUIDE])
    for phrase in (
        "番号の順",
        "開かない",
        "後で変えない",
        "その項目の状態文書と選択肢の記述だけで選ぶ",
        "見比べない",
    ):
        assert phrase in guide, phrase
    assert names[0] in guide and names[-1] in guide


def _written(item: CorpusItem) -> set[str]:
    """項目の対象（ステージ）が書いた区切りの全文: workflow.yaml の writes のファイル（ディレクトリはその下）と
    memory_out の記憶。ワークフローの inputs と同じ内容のファイルと、空の一覧の記憶は除く（どの対象の成果物か決まらない）。
    ゲートは何も書かない。"""
    if item.scope == "phase":
        return set()
    stage = next(
        s for p in WORKFLOW_DOC["workflow"]["phases"] for s in p["stages"] if s["id"] == item.target
    )
    writes = stage["artifacts"].get("writes", [])
    memory = stage["artifacts"].get("memory_out", [])
    out = set()
    for name, text in labeling._parts(item)[1]:
        path = name.removeprefix("## ファイル ")
        if name.startswith("## ファイル ") and any(
            path == w or (w.endswith("/") and path.startswith(w)) for w in writes
        ):
            source = FIXTURES / "inputs" / path
            if source.exists() and text == f"{name}\n{source.read_text('utf-8')}".rstrip("\n"):
                continue
            out.add(text)
        elif name.startswith("## 記憶 ") and name.removeprefix("## 記憶 ") in memory:
            if text.split("\n", 1)[1:] != ["[]"]:
                out.add(text)
    return out


def _files(item: CorpusItem) -> set[str]:
    """状態文書のファイルの区切りの全文。"""
    return {text for name, text in labeling._parts(item)[1] if name.startswith("## ファイル ")}


def test_earlier_files_do_not_contain_what_later_targets_write(committed: list[CorpusItem]) -> None:
    """前のファイルの状態文書は、後のファイルの対象が書いた成果物を含まない（後の対象の状態文書は前の対象の goal の成果物を
    含むが、前の対象を付け終えてから開く）。ゲートを最終ステージより前に置くと、ゲートの状態文書が最終ステージの成果物を先に
    見せる。ゲートを最後に回すと、後のフェーズの対象の状態文書が、ゲートの状態文書の区切りをすべて含み（フェーズを通った
    状態文書）、ゲートのラベルより先に見える。"""
    groups = labeling.by_target(committed)
    order = list(labeling.ORDER)
    sections = {
        t: {text for i in g for _, text in labeling._parts(i)[1]} for t, g in groups.items()
    }
    written = {t: set().union(*(_written(i) for i in g)) for t, g in groups.items()}
    for a, b in itertools.combinations(order, 2):
        assert not sections[a] & written[b], (a, b)
    assert all(written[t] for t in order if t[0] == "stage")
    for gate in (t for t in order if t[0] == "phase"):
        phase = next(p for p in WORKFLOW_DOC["workflow"]["phases"] if p["id"] == gate[1])
        last = max(
            (t for t in order if t[0] == "stage" and t[1] in [s["id"] for s in phase["stages"]]),
            key=order.index,
        )
        # 前に置くと漏れる: ゲートの状態文書は、最終ステージが書いた成果物を含む
        assert sections[gate] & written[last], gate
        # 最後に回すと漏れる: 後のフェーズの対象に、ゲートの状態文書のファイルをすべて含む状態文書がある
        later = order[order.index(gate) + 1 :]
        assert any(
            _files(g) <= _files(i) for g in groups[gate] for t in later for i in groups[t]
        ), gate


def test_options_and_common_sections_are_shown_once_per_target(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    by_file = labeling.file_names(committed)
    for (scope, target), group in labeling.by_target(committed).items():
        text = rendered[by_file[(scope, target)]]
        blocks = dict(labeling.item_blocks(text))
        joined = text.split(f"\n## {labeling.target_title(scope, target)}\n", 1)[1]
        head = joined.split("\n### 項目 ", 1)[0]
        # 選択肢の記述は、対象のファイルの頭に一度だけ
        for option in {o.id: o for i in group for o in i.options}.values():
            assert joined.count(f"- `{option.id}`: {option.description}") == 1
            assert f"- `{option.id}`: {option.description}" in head
        common = labeling.common_sections(group)
        for item in group:
            number = int(item.source["number"])
            block = blocks[number]
            assert f"選べる選択肢: {labeling.option_ids(item)}" in block
            assert all(o.description not in block for o in item.options)
            # 共通の区切りを戻すと、人に見せる状態文書に戻る
            fenced = block.split(f"{labeling.FENCE}text\n", 1)[1]
            shown = fenced.split(f"\n{labeling.FENCE}\n", 1)[0]
            for name, body in common.items():
                shown = shown.replace(f"{name}{labeling.COMMON}", body)
            assert shown == labeling.shown_state(item), number
        # 共通の区切りは、対象のファイルの頭の囲みに一度だけ示し、項目の過半（二つ以上）がそれと同じ
        if common:
            shared = head.split(f"{labeling.FENCE}text\n", 1)[1].split(f"\n{labeling.FENCE}", 1)[0]
            assert shared == "\n\n".join(common.values())
        else:
            assert labeling.FENCE not in head
        for name in common:
            same = [
                i for i in group if f"{name}{labeling.COMMON}" in blocks[int(i.source["number"])]
            ]
            assert len(same) >= 2 and 2 * len(same) > len(group), name
    # 見せ方で減らした（全項目に選択肢の記述と状態文書の全文を並べた形の半分より短い）
    full = sum(
        len(labeling.shown_state(i)) + sum(len(o.description) for o in i.options) for i in committed
    )
    assert sum(len(text) for text in rendered.values()) < full / 2


def test_only_mark_lines_are_dropped_from_the_shown_state(committed: list[CorpusItem]) -> None:
    """人に見せる状態文書は、印を除いた状態文書から、印だけの行（印の跡が空か「#」だけになる行）を落とし、区切りの間の空行を
    一つにしたもの。ほかの行は変えない。"""
    mark_only = re.compile(r"(#\s*)?\[\[class [^\]]*\]\]\s*")
    for item in committed:
        kept = [unmarked(line) for line in item.state.split("\n") if not mark_only.fullmatch(line)]
        shown = labeling.shown_state(item)
        assert "[[class" not in shown
        assert [line for line in shown.split("\n") if line] == [line for line in kept if line]


def test_reading_guide_states_facts_and_requests_only(rendered: dict[str, str]) -> None:
    """読み方は、事実と頼み（付ける順、見比べない、迷ったら unknown と理由）。人間の決定で、記述の読み方を決める二つの方針
    （記述が中身の条件を書いている時だけ中身を確かめる、記述の括弧の中の列挙は記述が書いた範囲として読む）は書かない。"""
    guide = _flat(rendered[labeling.GUIDE])
    for phrase in ("中身の条件", "中身を確かめる", "括弧の中の列挙", "記述が書いた範囲"):
        assert phrase not in guide, phrase
    for phrase in (
        "分類器と同じ立場",
        "字義どおり",
        "迷ったら unknown",
        "理由を一行添える",
        "見比べない",
        "「（なし）」",
        "空の節として数える",
        "持ち帰った問いとその回答",
        "goal に優先する",
        "指標の値",
        "テストを実際に実行した結果",
        "テストが通るかは、状態文書のコードとテストから判断する",
        "跡",
        "examples/software-factory/",
        "uv run python -m software_factory.labeling labels --labeler",
        "uv run python -m software_factory.labeling compare",
    ):
        assert phrase in guide, phrase
    for name in _target_files(rendered):
        head = _flat(_head(rendered[name]))
        assert "迷ったら unknown" in head and "中身の条件" not in head, name


def test_placeholders_in_the_material_are_listed_in_the_guide(
    committed: list[CorpusItem], material: dict[str, str]
) -> None:
    """材料の状態文書に現れる置き書き（行の全体が括弧の中の文）は、すべて読み方の事実に挙げる（docs/review-findings.md の
    I-L3）。挙げた置き書きは、どれも材料に現れる。"""
    found = {
        line.strip().removeprefix("- ")
        for text in material.values()
        for line in _inside_fences(text)
        if PLACEHOLDER_LINE.fullmatch(line)
    }
    listed = labeling.placeholders(committed)
    assert set(listed) == found
    assert {"（なし）", "（判断できない）", "（実行できなかった）"} <= found
    bullet = _flat(
        next(
            b
            for b in re.split(r"\n(?=- )", _outside_fences(material[labeling.GUIDE]))
            if "置き書き" in b
        )
    )
    assert all(f"「{p}」" in bullet for p in listed) and "空の節として数える" in bullet


def test_guide_refers_to_the_handbook_only_after_labeling(rendered: dict[str, str]) -> None:
    """冒頭は手引きを指さない。選び方と比べ方の手引き（adopting.md 第15.1節）は「付けた後」の節で、ラベルを付け終えるまで
    読まないと添えて示す（docs/review-findings.md の I-L2）。"""
    guide = rendered[labeling.GUIDE]
    head = _head(guide)
    assert "adopting.md" not in head and "15.1" not in head
    after = guide.split("\n## 付けた後\n", 1)[1].split("\n## ", 1)[0]
    bullet = _flat(next(b for b in re.split(r"\n(?=- )", after) if "adopting.md" in b))
    assert "adopting.md 第15.1節" in bullet and "ラベルを付け終えるまで読まない" in bullet
    assert guide.count("adopting.md") == 1
    for name in _target_files(rendered):
        assert "adopting.md" not in rendered[name], name


def test_commands_say_where_to_run() -> None:
    readme = (ROOT / "README.md").read_text("utf-8").split("\n## 記述と代表の整合", 1)[1]
    readme = readme.split("\n## ", 1)[0]
    for text in (readme, labeling.__doc__ or ""):
        assert "examples/software-factory/" in text
        assert "uv run python -m software_factory.labeling" in text


def _set_label(files: dict[str, str], number: int, line: str) -> dict[str, str]:
    """材料の項目 number の「ラベル:」の行を line にしたファイルの集まり。"""
    out = dict(files)
    marker = f"\n### 項目 {number}\n"
    name = next(n for n, text in files.items() if marker in text)
    head, sep, rest = files[name].partition(marker)
    body, nxt, tail = rest.partition("\n### 項目 ")
    body = re.sub(r"^ラベル:$", lambda _: line, body, count=1, flags=re.M)
    out[name] = head + sep + body + nxt + tail
    return out


def _filled(
    files: dict[str, str],
    committed: list[CorpusItem],
    wrong: int | None = None,
    skip: int | None = None,
) -> dict[str, str]:
    """印どおりのラベル（ゲートは goal）を「ラベル:」に書いた材料。番号 wrong の項目だけは unknown と理由を書き、番号 skip の
    項目は空のままにする。"""
    for item in committed:
        number = int(item.source["number"])
        if number == skip:
            continue
        label = "unknown（迷った）" if number == wrong else str(marked_class(item.state) or "goal")
        files = _set_label(files, number, f"ラベル: {label}")
    return files


def _write(directory: Path, files: dict[str, str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (directory / name).write_text(text, "utf-8")
    return directory


def test_filled_labels_compare_with_the_marks(
    committed: list[CorpusItem],
    rendered: dict[str, str],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    labels = tmp_path / "human-labels.jsonl"
    material = _write(tmp_path / "material", _filled(rendered, committed))
    for name, text in labeling.read_material(material).items():
        assert labeling.blank_labels(text) == rendered[name]
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
    _write(material, _filled(rendered, committed, wrong=number))
    assert labeling.main(["labels", "--labeler", "人", *args]) == 0
    capsys.readouterr()
    assert labeling.main(["compare", "--labels", str(labels)]) == 0
    out = capsys.readouterr().out
    assert "食い違い: 1 件" in out and f"項目 {number}（" in out


def test_only_the_labeled_files_count(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    """前のファイルから順に付けている間は、付けたファイルの項目だけがラベルになり、後のファイルの項目は空として数える。"""
    first = _target_files(rendered)[0]
    numbers = set(_items_in(rendered[first]))
    files = _filled(rendered, [i for i in committed if int(i.source["number"]) in numbers])
    found, empty, errors, warnings = labeling.parse_labels(files, committed, "人")
    assert errors == [] and warnings == []
    assert {x.item for x in found} == {
        i.item for i in committed if int(i.source["number"]) in numbers
    }
    assert len(empty) == len(committed) - len(numbers)


def test_label_lines_accept_a_fullwidth_colon_backquotes_and_reasons(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    first, second, third = committed[0], committed[1], committed[2]
    assert {"goal", "unknown"} <= {o.id for o in third.options}
    files = _set_label(rendered, 1, f"ラベル：{first.options[-1].id}（理由）")
    files = _set_label(files, 2, f"ラベル: `{second.options[0].id}`")
    # 括弧の中の id は数えない
    files = _set_label(files, 3, "ラベル: unknown（goal か迷った。(goal) とも読める）")
    found, empty, errors, warnings = labeling.parse_labels(files, committed, "人")
    assert errors == [] and warnings == []
    assert [(x.item, x.label) for x in found] == [
        (first.item, first.options[-1].id),
        (second.item, second.options[0].id),
        (third.item, "unknown"),
    ]
    assert len(empty) == len(committed) - 3


@pytest.mark.parametrize(
    "line",
    [
        "ラベル: ゴール",
        "ラベル: no_such_class",
        "ラベル goal",
        "ラベル: Goal",
        # 括弧の外に選択肢の id が二つ以上（docs/review-findings.md の I-L1）
        "ラベル: goal か unknown（迷う）",
        "ラベル: goal/unknown",
        "ラベル: `goal` `unknown`",
        "ラベル: unknown、goal かもしれない",
    ],
)
def test_unreadable_labels_are_errors_with_the_item_number(
    committed: list[CorpusItem],
    rendered: dict[str, str],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    line: str,
) -> None:
    assert {"goal", "unknown"} <= {o.id for o in committed[2].options}
    labels = tmp_path / "human-labels.jsonl"
    material = _write(tmp_path / "material", _set_label(rendered, 3, line))
    args = ["--material", str(material), "--out", str(labels)]
    capsys.readouterr()
    assert labeling.main(["labels", "--labeler", "人", *args]) == 2
    assert "項目 3:" in capsys.readouterr().out
    assert not labels.exists()


def test_an_item_in_another_file_is_an_error(
    committed: list[CorpusItem], rendered: dict[str, str]
) -> None:
    """項目を別のファイルに写すと、項目の番号を添えた誤り。"""
    names = _target_files(rendered)
    a, b = names[0], names[1]
    moved = rendered[a].split("\n### 項目 ", 1)
    block = "\n### 項目 " + moved[1].split("\n### 項目 ", 1)[0]
    number = int(block.split("\n", 2)[1].removeprefix("### 項目 "))
    files = {**rendered, a: rendered[a].replace(block, ""), b: rendered[b] + block}
    _, _, errors, _ = labeling.parse_labels(files, committed, "人")
    assert any(e.startswith(f"項目 {number}:") and b in e for e in errors), errors


def test_text_after_an_empty_label_is_warned(
    committed: list[CorpusItem],
    rendered: dict[str, str],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    labels = tmp_path / "human-labels.jsonl"
    filled = _set_label(_filled(rendered, committed, skip=4), 4, "ラベル:\ngoal")
    material = _write(tmp_path / "material", filled)
    for name, text in filled.items():
        assert labeling.blank_labels(text) == rendered[name]
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


def test_received_labels_fit_the_corpus(
    committed: list[CorpusItem], material: dict[str, str]
) -> None:
    """人から受け取ったラベル（docs/human-labels.jsonl）があれば、項目と選択肢に合い、材料の「ラベル:」と同じ。無ければ、
    比べるコマンドは無いことを報告する（人がラベルを付けるまで、このリポジトリには無い）。"""
    if not labeling.LABELS.exists():
        assert labeling.main(["compare"]) == 1
        return
    options = {item.item: {o.id for o in item.options} for item in committed}
    labels = load_labels(labeling.LABELS)
    assert all(n == 1 for n in Counter(label.item for label in labels).values())
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


def test_merged_implementation_variants_differ_only_in_the_code(trial: list[CorpusItem]) -> None:
    """review と acceptance の項目の候補は、同じ (訪問の区分, 印, 上流の違い) の組の中で、goal の実装の変種による
    repo/src/shopcart/discount.py の区切りだけが違う（review は ok、ok_b、ok_fixed の 3 通り、acceptance は ok と ok_b の
    2 通り）。記述が判断に使う review.json、verification.md、記憶は同じなので、一つにまとめる（docs/review-findings.md の
    I-L4）。往復 14 で直した review の changes_requested の代表は、変えた代表として記録し、review の状態文書にだけ届く。"""
    for target, variants in (("review", 3), ("acceptance", 2)):
        groups: dict[tuple[bool, str | None, str], list[CorpusItem]] = {}
        for item in trial:
            if item.target == target and labeling.wanted(item):
                key = (labeling.again(item), marked_class(item.state), labeling.upstream(item))
                groups.setdefault(key, []).append(item)
        assert groups and all(not again for again, _, _ in groups), target
        differ: set[str] = set()
        for group in groups.values():
            parts = [dict(labeling._parts(i)[1]) for i in group]
            for name in set().union(*parts):
                if len({p.get(name) for p in parts}) > 1:
                    differ.add(name)
        assert differ == {f"## ファイル {DISCOUNT}"}, target
        assert max(len(g) for g in groups.values()) == variants, target
        implementations = {labeling.implementation(i) for g in groups.values() for i in g}
        assert len(implementations) == variants, target
    changed = labeling.CHANGED["review"]
    assert changed == ((FIXTURES / "review" / "changes" / "review.json").read_text("utf-8"),)
    assert {(i.scope, i.target) for i in trial if changed[0] in i.state} == {("stage", "review")}
    assert [t for t, names in labeling.EVIDENCE.items() if "review" in names] == [
        ("stage", "review")
    ]


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
