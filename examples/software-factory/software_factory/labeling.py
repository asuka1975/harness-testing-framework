"""人がラベルを付ける材料（docs/human-labeling/ の下）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

往復 10 で代表を変えた所を、人が印を除いて読み、選択肢の記述だけでラベルを付ける（docs/review-findings.md の G-6）。
項目の選び方は、手引き第15.1節の「変えた所に絞ってラベルを付け直す時」の目安（対象、訪問、まとめ方）に従う（往復 12。
往復 13 で対象に review を、往復 14 で implement を足し、acceptance の上流の違いに持ち帰った問いの回答の有無を足した）。

- 対象（EVIDENCE）: 記述（ステージの goal と end_state、フェーズの goal）が、変えた代表の変えた所（成果物の全体ではない）を
  判断の根拠にしうる対象。項目は、その対象が根拠にしうる変えた代表（CHANGED）のどれかを状態文書に含む評価
- 訪問（AGAIN）: 訪問 1 を渡す。訪問 2 以降も渡すのは、memory_in を持つステージと、そのステージを含むフェーズのゲートだけ。
  見出しのほかは訪問 1 の項目と同じ状態文書は除く
- まとめ方: (対象, 訪問の区分, 印, 上流の違い) ごとに一つ、状態文書の短いもの。上流の違いは、intake.md を読む対象では
  (ペルソナ, 持ち帰った問いの回答の有無)、unit_test では goal の実装の変種。review と acceptance の状態文書も goal の実装の
  変種で repo/src/shopcart/discount.py だけが変わる（review は ok、ok_b、ok_fixed、acceptance は材料に入れる ok と ok_b）が、
  記述は review.json、verification.md と記憶で判断し、変種で当てはまり方が変わらないので、まとめる（往復 16。
  docs/review-findings.md の I-L4）。implement には上流の違いが無い。この例の偽の本体は入り直しても同じ代表を写すので、
  訪問 2 以降で訪問 1 と違う状態文書になるのは、持ち帰った問いの回答が intake.md に入る intake、analyze、discovery の
  ゲートだけ（design、plan_tasks、architecture のゲート、implement の訪問 2 以降は、見出しのほかは訪問 1 と同じなので除く）
- 確率的な実行に置かない代表（SCENARIO_ONLY。plan_tasks/incomplete）は、それを写すシナリオで分類器が見る状態文書を、
  `run_scenario` の結果の置き場（`ScenarioResult.store`）から読んで、項目の候補に足す（往復 15）
- acceptance は、分布テストの主経路（markov）の goal の実装（ok、ok_b）の後のものに限る。requirement_unmet の代表の
  「Discount.apply が支払額を切り捨てている」は ok と ok_b でだけ成り立ち、試しの実行 labeling（と divergent）では正しい
  実装 ok_fixed とも組んで食い違う（手引き第12節）ので、その組を材料から外す

確率的な実行の分布に無い代表（unit_test の defective）と、訪問 2 以降の各クラスも届くように、試しの実行は
tests/stochastic.yaml の profiles の labeling（分布を寄せたもの）で走らせる。

人に渡す材料には、印（分類器の選択、代表のクラス）、比べる相手の答え、選んだ規則、組ごとの数、項目の id を書かない
（手引き第15.1節の 2）。項目は全ファイルを通した通し番号で示し、番号と id の対応はコーパス
（docs/human-labeling.corpus.jsonl）の並びと source の number に持つ。並びは対象ごとで、対象の中は人に見せる文の
SHA-256 の順にし、同じ実行の項目を続けない（材料の文は、印のクラス、項目の id、出どころ、渡す順によらない）。選択肢の
記述と、対象の項目の過半（二つ以上）で同じ区切りは、対象のファイルの頭に一度だけ示す。印だけの行（印を除くと空か「#」
だけになる行）は落とす。

材料は、読み方のファイル（00-guide.md）と、対象ごとのファイル（01-intake.md から）に分ける（往復 16。
docs/review-findings.md の I-M2）。ワークフローは goal でだけ進むので、後の対象とゲートの状態文書は前の対象の goal の
成果物を含み、前の対象の項目の印が推せる。対象のファイルはワークフローの順（ORDER）で、ゲートはそのフェーズの最終
ステージの直後に置く（最終ステージより前に置くと、ゲートの状態文書が最終ステージの goal の成果物を先に見せる。最後に回すと、
後のフェーズの対象の状態文書が、ゲートの状態文書のファイルをすべて含み（フェーズを通った状態文書）、ゲートのラベルより先に
見える）。各ファイルの冒頭に、前のファイルを付け終えるまで開かないこと、付け終えたラベルを後で変えないこと、ほかの項目や
ファイルと見比べないことを書く。

コマンドは examples/software-factory/ で実行する（リポジトリの根では `No module named 'software_factory'` になる）。

    uv run python -m software_factory.labeling write                   # 試しの実行から材料とコーパスを書き直す
    uv run python -m software_factory.labeling labels --labeler <名前>  # 埋めた「ラベル:」を docs/human-labels.jsonl にする
    uv run python -m software_factory.labeling compare                 # human-labels.jsonl を印と比べる

ラベルの形は contract/formats/label.schema.json、比べるのは `oracle_report(MarkerClassifier(), corpus, labels)`。
tests/test_labeling.py が、コミットした材料が試しの実行から作り直したものと一致することを確かめる。
"""

import argparse
import hashlib
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from harness_testing_framework.runtime import Workflow
from harness_testing_framework.testing.harness import (
    MarkerClassifier,
    load_scenario,
    marked_class,
    unmarked,
)
from harness_testing_framework.testing.oracle import (
    CorpusItem,
    Label,
    build_corpus,
    load_corpus,
    load_labels,
    oracle_report,
    save_corpus,
    save_labels,
)
from harness_testing_framework.testing.stages import RunRecord, RunSet
from software_factory.personas import AFTER, KINDS, PERSONAS, REUSE, WHO
from software_factory.stages.deterministic import FIXTURES, ROOT, SCENARIOS, WORKFLOW, run
from software_factory.stages.probabilistic import DISCOUNT, TABLE, WORKFLOW_MODEL, run_set

DOCS = ROOT / "docs"
# 人に渡す材料のファイルを置くディレクトリ（この下のファイルだけを渡す）
MATERIAL_DIR = DOCS / "human-labeling"
GUIDE = "00-guide.md"
CORPUS = DOCS / "human-labeling.corpus.jsonl"
LABELS = DOCS / "human-labels.jsonl"
TRIAL_PROFILE = "labeling"
TRIAL_RUNS = 480
TRIAL_SEED = 90000
# 上流の違いのうち、intake.md に持ち帰った問いの回答が入っていること（ペルソナの名前の後に付ける）
CARRIED = "+carried"
FENCE = "~~~~~~"
# 項目の状態文書で、対象のすべての項目に共通の区切りの見出しに付ける文
COMMON = "（共通）"


def _fixture(stage: str, variant: str, name: str) -> str:
    return (FIXTURES / stage / variant / name).read_text("utf-8")


# 往復 10 で変えた代表と、それを見分ける文（状態文書に印つきのまま入る、成果物の内容か回答）。review は往復 14 で直した代表
CHANGED: dict[str, tuple[str, ...]] = {
    # REQ-3 に利用者と入力の場所をまとめた requirements.md（analyze の goal と needs_unclear の代表）
    "requirements": (
        _fixture("analyze", "ok", "requirements.md"),
        _fixture("analyze", "unclear", "requirements.md"),
    ),
    # 「## 対応」の REQ-3 に、画面は repo/ の外でコードを文字列で受け取ることを書いた design.md
    "design": (_fixture("design", "ok", "design.md"),),
    # 食い違いの根拠を REQ-3 にした verification.md
    "verification": (_fixture("acceptance", "misread", "verification.md"),),
    # 「割り引く額の端数は切り捨て」にした vague_founder の回答
    "answer": (f"A: {PERSONAS[1].answer(KINDS)}\n",),
    # 往復 11 で tests_insufficient の確率 0 の代表にした、要件に反する期待を持つテスト
    "tests": (_fixture("unit_test", "defective", "test_report.md"),),
    # 往復 14 で、前提が事実に合う指摘に直した changes_requested の代表の review.json（docs/review-findings.md の H-L6）。
    # review.json は review だけが書き、changes_requested では後のステージに進まないので、review の状態文書にだけ届く
    "review": (_fixture("review", "changes", "review.json"),),
}
# 対象（scope, id）→ 記述（ステージの goal と end_state、フェーズの goal）がその変えた所を判断の根拠にしうる、変えた代表。
# 変えた所は、requirements.md の REQ-3 の文のうち誰がどこで入力するかの句（購入者がレジの画面で入力する。外した「## 利用者」
# の節の中身。REQ-3 の振る舞いと受け入れ基準は変えていない）、design.md の「## 対応」の REQ-3 の、画面は repo/ の外でコードを
# 文字列で受け取るという句、verification.md の「## 依頼との食い違い」、vague_founder の回答、defective のテストと「## 未網羅」、
# review.json の changes_requested の指摘。変えた所の区切りは、成果物の節や要件より細かい句にした（手引きの「直した節、要件、
# 回答など」の「など」として。REQ-3 を一つの変えた所とすると、要件の記述に照らす unit_test も対象になるが、変えた句はテストが
# 期待も否定もできない）
# - requirements.md: 要件の根拠（analyze、discovery）、要件の構成要素への割り当てと受け持つ構成要素の欠け（design、
#   plan_tasks、architecture）、要件と依頼や回答の食い違い（acceptance）を判断する記述
# - design.md: 「## 対応」を判断に使う記述（design の goal、architecture）。plan_tasks は「## 構成」に要件を受け持つ構成要素が
#   欠けているかを判断するので、REQ-3 の画面の部分を「## 対応」がどう受け持つかを読みうる。review の design_flaw と
#   changes_requested の境界は、修正を要する指摘が design.md の構成かインターフェースを変えなければ解消しないかで、変えた句
#   （コードを文字列で受け取る、画面は repo/ の外）はインターフェースと境界を述べるので、その判断の根拠になりうる（往復 13）。
#   implement の goal の「repo/src/ の変更が design.md の構成どおり」も節を名指さず、変えた句は parse_code のインターフェース
#   （文字列で受け取る）と、画面を repo/ に置かないという構成を述べるので、goal と quality_violation（「## 構成」から外れる）の
#   判断の根拠になりうる（往復 14）
# - review.json: review の記述（goal、design_flaw、changes_requested）は review.json の指摘で判断する（往復 16 で記録した。
#   review の項目はどれも design.md を含むので、選ぶ項目は変わらない）
# 渡さない対象: unit_test と construction のゲートの requirements.md（テストの期待と結果を、受け入れ基準と要件の振る舞いに
# 照らす。REQ-3 の受け入れ基準と振る舞いは変えておらず、変えたのは誰がどこで入力するかで、テストが期待も否定もできない）、
# construction のゲートの design.md（状態文書には入るが、フェーズの goal は design.md に触れず、impl_notes.md の違反と
# test_report.md で判断する）、release、assurance、delivery（verification.md の合格、review.json と要件の id で判断する。
# どれも変えた所を含まない。changes_requested の review.json はゲートに届かない）
EVIDENCE: dict[tuple[str, str], tuple[str, ...]] = {
    ("stage", "intake"): ("answer",),
    ("stage", "analyze"): ("requirements", "answer"),
    ("phase", "discovery"): ("requirements", "answer"),
    ("stage", "design"): ("requirements", "design"),
    ("stage", "plan_tasks"): ("requirements", "design"),
    ("phase", "architecture"): ("requirements", "design"),
    ("stage", "implement"): ("design",),
    ("stage", "unit_test"): ("tests",),
    ("stage", "acceptance"): ("requirements", "verification", "answer"),
    ("stage", "review"): ("design", "review"),
}
# 確率的な実行に置かない代表（手引き第15.1節の 1）: シナリオの名前 → (scope, 対象, 代表を見分ける文)。往復 10 で足した
# plan_tasks/incomplete は、上流の design/gap を運用者が goal 到達扱いで通した後にしか組まない（試しの実行の運用者は中止で
# 答える）ので、それを写すシナリオで分類器が見る状態文書を項目の候補にする（往復 14。docs/review-findings.md の H-L4）
SCENARIO_ONLY: dict[str, tuple[str, str, str]] = {
    "plan_tasks_design_incomplete_rollback": (
        "stage",
        "plan_tasks",
        _fixture("plan_tasks", "incomplete", "tasks.yaml"),
    ),
}


def receives_carry(workflow: Workflow) -> set[tuple[str, str]]:
    """持ち帰った記憶を受け取る対象: memory_in のあるステージと、そういうステージを持つフェーズのゲート（ゲートの状態文書は
    フェーズの全体で、ゲートの訪問はフェーズの最終ステージの訪問）。"""
    stages = {s.id: s for s in workflow.stages}
    out = {("stage", s.id) for s in workflow.stages if s.memory_in}
    out |= {("phase", p.id) for p in workflow.phases if any(stages[s].memory_in for s in p.stages)}
    return out


def target_order(workflow: Workflow, targets: Collection[tuple[str, str]]) -> list[tuple[str, str]]:
    """材料の対象の順: フェーズとステージのワークフローの順で、ゲートはそのフェーズの（対象にある）最終ステージの直後。"""
    out: list[tuple[str, str]] = []
    for phase in workflow.phases:
        out += [("stage", s) for s in phase.stages if ("stage", s) in targets]
        if ("phase", phase.id) in targets:
            out.append(("phase", phase.id))
    if set(out) != set(targets):
        raise ValueError(f"ワークフローに無い対象: {sorted(set(targets) - set(out))}")
    return out


# 対象のファイルの順（docs/review-findings.md の I-M2）
ORDER = tuple(target_order(WORKFLOW_MODEL, EVIDENCE))
# 訪問 2 以降の項目も渡す対象（手引き第15.1節の「memory_in を持つステージと、そのステージを含むフェーズのゲートだけ」）。
# acceptance と review は memory_in を持たないので訪問 1 だけ（そのフェーズ assurance にも memory_in を持つステージは無い）
AGAIN = {target for target in EVIDENCE if target in receives_carry(WORKFLOW_MODEL)}
# 持ち帰った問い（analyze の needs_unclear の代表が intake に持ち帰る）。訪問 2 以降の intake.md には、その回答が入る
CARRIED_QUESTIONS = (AFTER, REUSE)
# goal の実装の変種（unit_test の上流の違い）。acceptance の項目は、分布テストの主経路（markov）の goal の実装の後のものに
# 限る。requirement_unmet の代表（333 円に PCT10 で 299 円。Discount.apply が支払額を切り捨てている）は ok と ok_b でだけ
# 成り立つ。markov は ok_fixed を置かないので組まないが、divergent と試しの実行 labeling では ok_fixed とも組み、その時は
# 代表の文が ok_fixed のコードと食い違う（手引き第12節）。divergent は独立性検証のための本体（README）
IMPLEMENTATIONS = ("ok", "ok_b", "ok_fixed")
MAIN_IMPLEMENTATIONS = {
    v
    for v in TABLE["profiles"]["markov"]["implement"]["first"]
    if TABLE["variants"]["implement"][v]["class"] == "goal"
}
_SECTION = re.compile(r"^(?=## (?:ファイル|記憶) )", re.M)
_MARK_ONLY = re.compile(r"(#\s*)?\[\[class [^\]]*\]\]\s*")
_LABEL = re.compile(r"^ラベル[:：](.*)$")
_ITEM = re.compile(r"### 項目 (\d+)")
# 材料のファイルの名前（読み方のファイルと、対象ごとのファイル）
_FILE = re.compile(r"\d{2}-[a-z0-9_-]+\.md")
# 置き書き: 行の全体が括弧の中の文（箇条の印が付いてもよい）。「（なし）」など
PLACEHOLDER = re.compile(r"\s*(?:- )?([（(][^（）()]+[）)])\s*")
# 「ラベル:」の後の、選択肢の id の形の語
_ID_TOKEN = re.compile(r"(?<![A-Za-z0-9_-])([a-z][a-z0-9_]*)(?![A-Za-z0-9_-])")


def visit_of(item: CorpusItem) -> int:
    """状態文書の見出し行（`# 評価: <scope> <対象> visit <n>`）の訪問。ゲートはフェーズの最終ステージの訪問。"""
    match = re.match(r"# 評価: (?:stage|phase) \S+ visit (\d+)\n", item.state)
    if match is None:
        raise ValueError(f"{item.item} の状態文書に見出し行が無い")
    return int(match[1])


def implementation(item: CorpusItem) -> str | None:
    """状態文書の repo/src/shopcart/discount.py が、goal の実装のどの変種か（無ければ None）。"""
    found = [
        v
        for v in IMPLEMENTATIONS
        if f"## ファイル {DISCOUNT}\n{_fixture('implement', v, DISCOUNT)}" in item.state
    ]
    if len(found) > 1:
        raise ValueError(f"{item.item} の実装の変種が一つに決まらない: {found}")
    return found[0] if found else None


def persona(item: CorpusItem) -> str | None:
    """状態文書の intake.md の回答が、どのペルソナのものか（intake.md が無ければ None）。"""
    found = [p.name for p in PERSONAS if f"A: {p.answer(WHO)}\n" in item.state]
    if len(found) > 1:
        raise ValueError(f"{item.item} のペルソナが一つに決まらない: {found}")
    return found[0] if found else None


def responded(item: CorpusItem) -> bool:
    """状態文書の intake.md に、持ち帰った問い（とその回答）があるか。"""
    return any(f"- Q: {question}\n" in item.state for question in CARRIED_QUESTIONS)


def upstream(item: CorpusItem) -> str:
    """上流の違い: unit_test では goal の実装の変種、intake.md を読む対象ではペルソナ（持ち帰った問いの回答があれば、後に
    CARRIED を付ける）、ほかは空（review と acceptance の goal の実装の変種はまとめる）。"""
    if item.target == "unit_test":
        return implementation(item) or ""
    name = persona(item)
    if name is None:
        return ""
    return name + (CARRIED if responded(item) else "")


def again(item: CorpusItem) -> bool:
    """訪問の区分: 訪問 2 以降か。"""
    return visit_of(item) != 1


def body(item: CorpusItem) -> str:
    """状態文書の、見出し行（対象と訪問）より後。"""
    return item.state.split("\n", 1)[1]


def same_as_first(corpus: Sequence[CorpusItem]) -> set[str]:
    """訪問 2 以降の項目のうち、状態文書が同じ対象の訪問 1 の項目と、見出しの訪問の番号のほかは同じもの（応答が状態文書に
    現れていない）の id。"""
    firsts = {(i.scope, i.target, body(i)) for i in corpus if not again(i)}
    return {i.item for i in corpus if again(i) and (i.scope, i.target, body(i)) in firsts}


def wanted(item: CorpusItem) -> bool:
    """往復 10 で変えた代表を、記述がその変えた所を根拠にしうる対象で含む評価か（訪問 2 以降は AGAIN の対象だけ）。"""
    target = (item.scope, item.target)
    evidence = EVIDENCE.get(target)
    if evidence is None or (again(item) and target not in AGAIN):
        return False
    if item.target == "acceptance" and implementation(item) not in MAIN_IMPLEMENTATIONS:
        return False
    return any(text in item.state for name in evidence for text in CHANGED[name])


def _parts(item: CorpusItem) -> tuple[str, list[tuple[str, str]]]:
    """人に見せる状態文書の (見出し行, [(区切りの見出し, 区切りの全文)])。印を除き、印だけの行を落とし、区切りの末尾の
    空行を除く。区切りは「## ファイル …」と「## 記憶 …」。"""
    lines = [unmarked(line) for line in item.state.split("\n") if not _MARK_ONLY.fullmatch(line)]
    head, *chunks = _SECTION.split("\n".join(lines))
    parts = [(chunk.split("\n", 1)[0], chunk.rstrip("\n")) for chunk in chunks]
    if len({name for name, _ in parts}) != len(parts):
        raise ValueError(f"{item.item} の状態文書の区切りが読めない")
    return head.rstrip("\n"), parts


def shown_state(item: CorpusItem) -> str:
    """人に見せる状態文書: 印を除いた状態文書から、印だけの行を落とし、区切りの間の空行を一つにしたもの。"""
    head, parts = _parts(item)
    shown = "\n\n".join([head, *(text for _, text in parts)])
    if FENCE in shown:
        raise ValueError(f"{item.item} の状態文書に {FENCE} がある")
    return shown


def option_ids(item: CorpusItem) -> str:
    """項目で選べる選択肢の id の並び。"""
    return "、".join(f"`{o.id}`" for o in item.options)


def _run(item: CorpusItem) -> str:
    """項目の実行（id の `<実行の id>-<評価の seq>` の前半）。"""
    return item.item.rsplit("-", 1)[0]


def _order_key(item: CorpusItem) -> str:
    """対象の中の並びの鍵: 人に見せる文（選べる選択肢と状態文書）の SHA-256。印、id、出どころによらない。"""
    return hashlib.sha256(f"{option_ids(item)}\n{shown_state(item)}".encode()).hexdigest()


def _same_runs(out: Sequence[CorpusItem]) -> list[int]:
    """out の中で、直前の項目と同じ実行の項目の位置。"""
    return [k for k in range(1, len(out)) if _run(out[k]) == _run(out[k - 1])]


def arrange(items: Sequence[CorpusItem]) -> list[CorpusItem]:
    """材料の並びにし、source に通し番号（number）を書く（分類器の選択 choice は除く）。対象は ORDER の順、対象の中は
    _order_key の順にし、同じ実行の項目が続く所は、その項目か直前の項目を、同じ対象の中の別の項目と入れ替えて無くす
    （並びは、人に見せる文と、実行が同じかどうかだけで決まる）。"""
    order = list(ORDER)
    groups: dict[tuple[str, str], list[CorpusItem]] = {}
    for item in items:
        groups.setdefault((item.scope, item.target), []).append(item)
    out: list[CorpusItem] = []
    spans: list[range] = []
    for target in sorted(groups, key=order.index):
        start = len(out)
        out += sorted(groups[target], key=_order_key)
        spans += [range(start, len(out))] * (len(out) - start)

    def improve(k: int, count: int) -> bool:
        for p in (k, k - 1):
            for j in spans[p]:
                out[p], out[j] = out[j], out[p]
                if len(_same_runs(out)) < count:
                    return True
                out[p], out[j] = out[j], out[p]
        return False

    while bad := _same_runs(out):
        if not improve(bad[0], len(bad)):
            a, b = out[bad[0] - 1], out[bad[0]]
            raise ValueError(f"同じ実行の項目が続かないように並べられない: {a.item} と {b.item}")
    return [
        replace(
            item,
            source={
                **{k: v for k, v in item.source.items() if k not in ("choice", "number")},
                "number": n,
            },
        )
        for n, item in enumerate(out, start=1)
    ]


def select(corpus: Sequence[CorpusItem]) -> list[CorpusItem]:
    """(対象, 訪問の区分, 印, 上流の違い) ごとに一項目。訪問 2 以降の、見出しのほかは訪問 1 の項目と同じ状態文書は除く
    （記述の当てはまり方が同じなので、訪問 1 の項目で代える）。組の中では、上流の違い（ペルソナ、持ち帰った問いの回答、
    実装の変種）のほかの違いが少ないように状態文書の短いものを選ぶ。並びは arrange。"""
    chosen: dict[tuple[str, str, bool, str | None, str], CorpusItem] = {}
    repeated = same_as_first(corpus)

    def rank(item: CorpusItem) -> tuple[int, str]:
        return (len(item.state), item.item)

    for item in corpus:
        if not wanted(item) or item.item in repeated:
            continue
        key = (item.scope, item.target, again(item), marked_class(item.state), upstream(item))
        best = chosen.get(key)
        if best is None or rank(item) < rank(best):
            chosen[key] = item
    return arrange(list(chosen.values()))


def scenario_corpus(name: str, workdir: Path) -> list[CorpusItem]:
    """シナリオで分類器が見る状態文書の項目（状態文書と選択肢の組ごとに一項目）。シナリオを `run_scenario` で実行し
    （deterministic.run。期待どおりであること、つまり結果の problems が空であることを確かめる）、結果の実行記録（trace）を
    RunRecord にして、結果の置き場（store。手引き第15.1節）から `build_corpus` で項目にする。trace は再開をまたいで続いた
    実行記録なので、中断するシナリオでもこのまま使える。source にシナリオの名前を足す。"""
    path = SCENARIOS / f"{name}.yaml"
    scenario = load_scenario(path)
    if scenario.workflow.resolve() != WORKFLOW.resolve() or scenario.metrics is not None:
        raise ValueError(f"{name} はこの例のワークフローと指標のシナリオではない")
    result = run(path, workdir)
    if result.problems:
        raise ValueError(f"{name} の実行がシナリオの期待と違う: {result.problems}")
    record = RunRecord(scenario.seed, result.status, result.trace)
    items = build_corpus(RunSet([record]), result.store, WORKFLOW_MODEL, unique_states=True)
    return [replace(i, source={**i.source, "scenario": name}) for i in items]


def trial_corpus(workdir: Path) -> list[CorpusItem]:
    """試しの実行（tests/stochastic.yaml の labeling）を走らせたコーパス（状態文書と選択肢の組ごとに一項目）に、確率的な
    実行に置かない代表（SCENARIO_ONLY）の項目を足したもの。"""
    runs, store = run_set(TRIAL_PROFILE, TRIAL_RUNS, TRIAL_SEED, workdir / "trial")
    corpus = build_corpus(runs, store, WORKFLOW_MODEL, unique_states=True)
    for name, (scope, target, text) in SCENARIO_ONLY.items():
        corpus += [
            i
            for i in scenario_corpus(name, workdir / name)
            if (i.scope, i.target) == (scope, target) and text in i.state
        ]
    return corpus


def trial_items(workdir: Path) -> list[CorpusItem]:
    """試しの実行のコーパスから材料の項目を選ぶ。"""
    return select(trial_corpus(workdir))


def by_target(items: Sequence[CorpusItem]) -> dict[tuple[str, str], list[CorpusItem]]:
    """対象ごとの項目（項目の並びのまま）。"""
    groups: dict[tuple[str, str], list[CorpusItem]] = {}
    for item in items:
        groups.setdefault((item.scope, item.target), []).append(item)
    return groups


def target_title(scope: str, target: str) -> str:
    """材料の対象の見出し。"""
    return f"フェーズ {target} のゲート" if scope == "phase" else f"ステージ {target}"


def file_names(items: Sequence[CorpusItem]) -> dict[tuple[str, str], str]:
    """対象 → 対象のファイルの名前（項目のある対象を ORDER の順に 01 から番号を付ける）。"""
    present = {(item.scope, item.target) for item in items}
    targets = [t for t in ORDER if t in present]
    if len(targets) != len(present):
        raise ValueError(f"ORDER に無い対象: {sorted(present - set(targets))}")
    return {
        (scope, target): f"{n:02d}-{target}{'-gate' if scope == 'phase' else ''}.md"
        for n, (scope, target) in enumerate(targets, start=1)
    }


def _target_line(item: CorpusItem) -> str:
    if item.scope == "phase":
        return (
            f"フェーズ {item.target} のゲート（フェーズの最終ステージの訪問 {visit_of(item)} の後）"
        )
    return f"ステージ {item.target} の訪問 {visit_of(item)}"


def common_sections(group: Sequence[CorpusItem]) -> dict[str, str]:
    """対象の項目の過半（二つ以上）で同じ区切り（見出し → 全文。区切りごとに最も多い全文で、並びは最初に現れた順）。
    項目の状態文書では、これと同じ区切りを見出しだけにする。違う全文の区切りは、その項目に全文で示す。"""
    counts: Counter[tuple[str, str]] = Counter()
    order: dict[str, int] = {}
    for item in group:
        for name, text in _parts(item)[1]:
            counts[(name, text)] += 1
            order.setdefault(name, len(order))
    out: dict[str, str] = {}
    for (name, text), n in sorted(counts.items(), key=lambda kv: (-kv[1], len(kv[0][1]), kv[0])):
        if name not in out and n >= 2 and 2 * n > len(group):
            out[name] = text
    return dict(sorted(out.items(), key=lambda kv: order[kv[0]]))


def _options(group: Sequence[CorpusItem]) -> list[tuple[str, str]]:
    """対象の選択肢の (id, 記述)。項目ごとの選択肢は、選択肢の最も多い項目の並びの部分列で、記述は同じ。"""
    longest = max((item.options for item in group), key=len)
    ids = [o.id for o in longest]
    for item in group:
        mine = [o.id for o in item.options]
        if [i for i in ids if i in mine] != mine or any(o not in longest for o in item.options):
            raise ValueError(f"{item.item} の選択肢が対象のほかの項目と合わない")
    return [(o.id, o.description) for o in longest]


def placeholders(items: Sequence[CorpusItem]) -> list[str]:
    """人に見せる状態文書に現れる置き書き（行の全体が括弧の中の文）。多く現れる順。"""
    counts: Counter[str] = Counter()
    for item in items:
        for line in shown_state(item).split("\n"):
            match = PLACEHOLDER.fullmatch(line)
            if match is not None:
                counts[match[1]] += 1
    return [text for text, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def guide(items: Sequence[CorpusItem]) -> str:
    """読み方のファイル（00-guide.md）の文。地の文には、比べる相手の答え、選んだ規則、組ごとの数を書かない。"""
    names = list(file_names(items).values())
    listed = "".join(f"「{p}」" for p in placeholders(items))
    return f"""# 人がラベルを付ける材料: 読み方

ワークフロー定義の記述（選択肢の記述）だけを読んで、各項目の状態文書がどの選択肢に当たるかを選んでもらうための材料。
材料は、このファイルと、対象（ステージか、フェーズのゲート）ごとのファイル（{names[0]} から {names[-1]}）。手で書くのは、
対象ごとのファイルの各項目の「ラベル:」の行だけで、ほかは直さない。

項目の選び方は README にある。ラベルを付け終えるまで README の「記述と代表の整合」を読まない。README のほかの節、docs/ の
ほかの文書、tests/ と software\\_factory/ の下にも、代表がどの選択肢に当たるかが書いてあるので、ラベルを付け終えるまで
この材料（docs/human-labeling/ の下のファイル）のほかは開かない（比べる時のコーパス docs/human-labeling.corpus.jsonl と
フィクスチャには、分類器が読む印が残っている）。

## 付ける順

- 対象ごとのファイルを、番号の順に一つずつ付ける。前のファイルを付け終えるまで、次のファイルを開かない
- 付け終えたファイルのラベルは、後で変えない。後のファイルを読んでから前のファイルの項目を思い直しても、変えない
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- ファイルを一つずつ受け取る時は、付け終えたファイルを返してから、次のファイルを受け取る

## 読み方

方針:

- 分類器と同じ立場で選ぶ。記述を字義どおりに読み、状態文書から判断できることだけで選ぶ
- 迷ったら unknown を選び、理由を一行添える（例: `ラベル: unknown（REQ-3 の根拠が回答に無い）`）。ほかの選択肢にも理由を
  添えてよい。理由は比べる時には使わないが、食い違いを直す時に読む

事実:

- 各項目の「状態文書」は、分類器が見たもの（そのステージの reads と writes のファイルの内容と、memory\\_out の記憶）から、
  偽の本体が書いた印を除いたもの
- ゲートの項目の状態文書は、フェーズの全体（フェーズのすべてのステージの reads と writes のファイルの内容と、memory\\_out の
  記憶）
- 指標の値は入っていない。テストを実際に実行した結果（指標の一つ）も入っていないので、テストが通るかは、状態文書のコードと
  テストから判断することになる
- 指標が落ちた評価では、goal が選べる選択肢に無い。goal が選べる選択肢に無い時は、選択肢の記述の「goal に優先する」という
  文は働かない
- 節の中身が置き書き（この材料に現れるのは、次のすべて: {listed}）だけの時は、空の節
  として数える
- 記憶の `[]` は空の一覧
- 訪問 2 以降の項目は、戻りの後に入り直した評価。持ち帰った記憶（memory\\_in）そのものは状態文書に入らない。戻りの後の
  状態文書（intake の訪問 2 以降と、それより後の評価）では、intake.md の「## 質問と回答」に持ち帰った問いとその回答が入る
- 印を除いた跡（review.json の `"marker": ""` のような空の値）が残るが、意味は無い。印だけの行は落としてある
- 項目の番号と、ファイルの中の並びに意味は無い

## 見せ方

- 項目は対象ごとのファイルにある。ファイルの頭に、選択肢の記述（ワークフロー定義の記述そのもの）を一度だけ示す。各項目
  には、その項目で選べる選択肢の id を示す
- 対象の項目の半分より多くで同じ区切り（「## ファイル …」と「## 記憶 …」）は、ファイルの頭に一度だけ示す。項目の状態
  文書では、それと同じ区切りを、見出しに「（共通）」を付けて、分類器が見た順の位置に示す。「（共通）」の付かない区切りは、
  その項目の全文を示す

## ラベルの書き方

- 当てはまる選択肢の id を一つ、「ラベル:」と同じ行に書く（例: `ラベル: goal`）。コロンは全角でもよい
- 理由は、id の後の括弧の中に書く。括弧の外に選択肢の id を二つ以上書くと、読めない誤りになる（例:
  `ラベル: goal か unknown`）

## 付けた後

- 付け終えたら、examples/software-factory/ で次を実行する（リポジトリの根で実行すると `No module named 'software_factory'`
  になる）
  1. `uv run python -m software_factory.labeling labels --labeler <名前>`: docs/human-labeling/ の下のファイルの「ラベル:」
     から docs/human-labels.jsonl（contract/formats/label.schema.json の形）を作る。空の「ラベル:」は数えて報告し、
     「ラベル:」の後が空で次の行に文がある時は警告する。読めないラベル、括弧の外の二つ以上の id、選べる選択肢に無い id、
     別のファイルに移った項目は、項目の番号を添えた誤りにする（終了コード 2）
  2. `uv run python -m software_factory.labeling compare`: ラベルを印と比べ、食い違う項目を番号で挙げる
- 選び方と比べ方の手引きは adopting.md 第15.1節にある。ラベルを付け終えるまで読まない
- `uv run python -m software_factory.labeling write` は材料を作り直し、埋めた「ラベル:」を空にする（付け始めた後は、
  付け直す範囲を決めてから実行する）
"""


def _file_head(n: int, names: Sequence[str], title: str) -> str:
    """対象のファイルの冒頭: 読み方のファイルと、付ける順と、見比べないことの頼み。"""
    name = names[n - 1]
    before = (
        f"{GUIDE} を読んでから、このファイルを開く"
        if n == 1
        else f"前のファイル（{names[n - 2]}）を付け終えるまで、このファイル（{name}）を開かない"
    )
    after = (
        f"このファイルを付け終えるまで、次のファイル（{names[n]}）を開かない"
        if n < len(names)
        else "これが最後のファイル"
    )
    return f"""# 人がラベルを付ける材料（{n} / {len(names)}）: {title}

読み方は {GUIDE} にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- {before}
- {after}
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える
"""


def render(items: Sequence[CorpusItem]) -> dict[str, str]:
    """材料のファイルの名前 → 文。読み方のファイルと、対象ごとのファイル。項目は渡された並びで、番号はその位置（全ファイルを
    通した通し番号）。対象ごとの項目が ORDER の順に、続いて並んでいること。"""
    groups = by_target(items)
    names = file_names(items)
    seen = [(item.scope, item.target) for item in items]
    runs = [t for k, t in enumerate(seen) if k == 0 or seen[k - 1] != t]
    if runs != list(names):
        raise ValueError("項目が、対象ごとに ORDER の順で続いて並んでいない")
    ordered = list(names.values())
    out = {GUIDE: guide(items)}
    numbers = {id(item): n for n, item in enumerate(items, start=1)}
    for k, (target, name) in enumerate(names.items(), start=1):
        group = groups[target]
        title = target_title(*target)
        common = common_sections(group)
        options = "\n".join(f"- `{i}`: {d}" for i, d in _options(group))
        parts = [
            _file_head(k, ordered, title),
            f"\n## {title}\n\n選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を"
            f"示す）:\n\n{options}\n",
        ]
        if common:
            shared = "\n\n".join(common.values())
            parts.append(
                "\nこの対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:"
                f"\n\n{FENCE}text\n{shared}\n{FENCE}\n"
            )
        for item in group:
            shown_state(item)  # 囲みの印が状態文書に無いことを確かめる
            head, sections = _parts(item)
            shown = "\n\n".join(
                [head, *(s + COMMON if common.get(s) == text else text for s, text in sections)]
            )
            parts.append(
                f"\n### 項目 {numbers[id(item)]}\n\n対象: {_target_line(item)}\n\n"
                f"選べる選択肢: {option_ids(item)}\n\n"
                f"状態文書:\n\n{FENCE}text\n{shown}\n{FENCE}\n\nラベル:\n"
            )
        out[name] = "".join(parts)
    return out


def item_blocks(text: str) -> list[tuple[int, str]]:
    """材料のファイルの項目ごとの (番号, 見出しより後の本文)。囲みの中の行は見出しとして読まない。"""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    inside = False
    for line in text.split("\n"):
        if not inside:
            match = _ITEM.fullmatch(line)
            if match is not None:
                current = []
                blocks.append((int(match[1]), current))
                continue
            if line.startswith(("# ", "## ")):
                current = None
                continue
        if line == f"{FENCE}text":
            inside = True
        elif line == FENCE:
            inside = False
        if current is not None:
            current.append(line)
    return [(n, "\n".join(lines)) for n, lines in blocks]


def blank_labels(text: str) -> str:
    """埋めた材料のファイルの各項目の、状態文書の囲みより後を `write` が作る形（空の「ラベル:」）に戻した文。状態文書の
    中の行には触れない。「ラベル:」の後の行に書いた文も除く。"""
    out: list[str] = []
    inside = in_item = after = False

    def close() -> None:
        if in_item and after:
            out.extend(["", "ラベル:", ""])

    for line in text.split("\n"):
        if not inside and (_ITEM.fullmatch(line) or line.startswith(("# ", "## "))):
            close()
            in_item, after = _ITEM.fullmatch(line) is not None, False
            out.append(line)
            continue
        if in_item and after and not inside:
            continue
        if line == f"{FENCE}text":
            inside = True
        elif line == FENCE:
            inside = False
            after = in_item
        out.append(line)
    close()
    return "\n".join(out)


def read_material(directory: Path = MATERIAL_DIR) -> dict[str, str]:
    """材料のファイルの名前 → 文（読み方のファイルと、対象ごとのファイル。名前の順）。"""
    if not directory.is_dir():
        return {}
    return {
        path.name: path.read_text("utf-8")
        for path in sorted(directory.iterdir())
        if _FILE.fullmatch(path.name)
    }


def _outside_parens(text: str) -> str:
    """括弧（「（ ）」と「( )」。入れ子も）の外の文。閉じない括弧は行の終わりまで。"""
    out: list[str] = []
    depth = 0
    for char in text:
        if char in "（(":
            depth += 1
        elif char in "）)" and depth:
            depth -= 1
        elif depth == 0:
            out.append(char)
    return "".join(out)


def parse_labels(
    files: Mapping[str, str], corpus: Sequence[CorpusItem], labeler: str
) -> tuple[list[Label], list[str], list[str], list[str]]:
    """埋めた材料のファイル（名前 → 文）から (ラベル, 空の項目の id, 誤り, 警告)。項目は全ファイルを通した通し番号で、番号 n
    の項目はコーパスの n 番目（source の number と同じ）で、その対象のファイルにある。ラベルは「ラベル:」（全角のコロンも
    読む）の後の最初の id（` で囲んでもよい）で、括弧の中の理由は捨てる。括弧の外に選択肢の id がほかにもあれば誤り。
    誤りと警告には項目の番号を添える。"""
    numbered: dict[int, CorpusItem] = {}
    for n, item in enumerate(corpus, start=1):
        if int(item.source.get("number", n)) != n:
            raise ValueError(f"コーパスの {n} 番目の項目の番号が {item.source.get('number')}")
        numbered[n] = item
    names = file_names(corpus)
    every_id = {o.id for item in corpus for o in item.options}
    labels: list[Label] = []
    empty: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen: list[int] = []
    for name in sorted(files):
        for n, block in item_blocks(files[name]):
            seen.append(n)
            if n not in numbered:
                errors.append(f"項目 {n}: コーパスに無い番号（{name}）")
                continue
            item = numbered[n]
            home = names[(item.scope, item.target)]
            if name != home:
                errors.append(f"項目 {n}: {name} にあるが、{home} の項目")
                continue
            ids = [o.id for o in item.options]
            tail = block.rsplit(f"\n{FENCE}\n", 1)[-1].split("\n")
            found = [k for k, line in enumerate(tail) if _LABEL.match(line)]
            if len(found) != 1:
                what = "無い" if not found else f" {len(found)} 個ある"
                errors.append(f"項目 {n}: 状態文書の後の「ラベル:」の行が{what}")
                continue
            match = _LABEL.match(tail[found[0]])
            value = match[1].strip() if match is not None else ""
            if not value:
                if any(line.strip() for line in tail[found[0] + 1 :]):
                    warnings.append(
                        f"項目 {n}: 「ラベル:」の後が空で、次の行に文がある。ラベルは「ラベル:」と同じ行に書く"
                        "（この項目は空として数えた）"
                    )
                empty.append(item.item)
                continue
            label = re.match(r"`?([a-z][a-z0-9_-]*)`?(?![a-z0-9_-])", value)
            if label is None:
                errors.append(
                    f"項目 {n}: 「{value}」を読めない（選べる選択肢の id を一つ書く: {ids}）"
                )
                continue
            others = [
                t for t in _ID_TOKEN.findall(_outside_parens(value[label.end() :])) if t in every_id
            ]
            if others:
                errors.append(
                    f"項目 {n}: 「{value}」は括弧の外に選択肢の id が二つ以上ある（{[label[1], *others]}）。"
                    "id を一つだけ書き、理由は括弧の中に書く"
                )
                continue
            if label[1] not in ids:
                errors.append(f"項目 {n}: 「{value}」は選べる選択肢 {ids} のどれでもない")
                continue
            labels.append(Label(item.item, label[1], labeler))
    for n in sorted({n for n in seen if seen.count(n) > 1}):
        errors.append(f"項目 {n}: 材料に {seen.count(n)} 回ある")
    errors += [f"項目 {n}: 材料に無い" for n in sorted(set(numbered) - set(seen))]
    return labels, empty, errors, warnings


def write(material: Path = MATERIAL_DIR, corpus: Path = CORPUS) -> list[CorpusItem]:
    """試しの実行から材料（material の下のファイル）とコーパスを作り直す。material の下の、材料のファイルの名前の形で、
    作り直した材料に無いファイルは消す。"""
    with tempfile.TemporaryDirectory() as tmp:
        items = trial_items(Path(tmp))
    save_corpus(items, corpus)
    files = render(items)
    material.mkdir(parents=True, exist_ok=True)
    for path in material.iterdir():
        if _FILE.fullmatch(path.name) and path.name not in files:
            path.unlink()
    for name, text in files.items():
        (material / name).write_text(text, "utf-8")
    return items


def compare(labels_path: Path, corpus_path: Path = CORPUS) -> int:
    """ラベルを印と比べて報告する。ラベルのファイルが無ければ、そのことを報告して 1 を返す。"""
    if not labels_path.exists():
        print(
            f"ラベルのファイルが無い: {labels_path}\n"
            f"{MATERIAL_DIR.name}/ の下のファイルの「ラベル:」を埋め、examples/software-factory/ で "
            "`uv run python -m software_factory.labeling labels --labeler <名前>` を実行して作る"
        )
        return 1
    loaded = load_corpus(corpus_path)
    corpus = {item.item: item for item in loaded}
    numbers = {item.item: int(item.source.get("number", n)) for n, item in enumerate(loaded, 1)}
    names = file_names(loaded)
    labels = load_labels(labels_path)
    missing = [label.item for label in labels if label.item not in corpus]
    if missing:
        print(f"コーパスに無い項目のラベル: {missing}")
        return 2
    items = [corpus[label.item] for label in labels]
    report = oracle_report(MarkerClassifier(), items, labels)
    marker = MarkerClassifier()
    differ = []
    for item, label in zip(items, labels, strict=True):
        choice = marker.classify(item.state, item.options).choice
        if choice != label.label:
            differ.append(
                f"- 項目 {numbers[item.item]}（{names[(item.scope, item.target)]}、{item.item}、"
                f"{item.scope} {item.target}、訪問 {visit_of(item)}）: 印 {choice}、ラベル {label.label}"
                f"（{label.labeler}）"
            )
    print(f"ラベル {len(labels)} 件（コーパス {len(corpus)} 項目）")
    print(f"kappa {report.kappa:.3f}、一致率 {report.accuracy:.3f}")
    print("\n".join(report.lines()))
    print(f"食い違い: {len(differ)} 件")
    if differ:
        print("\n".join(differ))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m software_factory.labeling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("write", help="試しの実行から docs/human-labeling/ の下とコーパスを書き直す")
    labels = sub.add_parser("labels", help="埋めた「ラベル:」を JSON Lines にする")
    labels.add_argument("--labeler", required=True)
    labels.add_argument("--material", type=Path, default=MATERIAL_DIR)
    labels.add_argument("--out", type=Path, default=LABELS)
    labels.add_argument("--corpus", type=Path, default=CORPUS)
    comparing = sub.add_parser("compare", help="ラベルを印と比べる")
    comparing.add_argument("--labels", type=Path, default=LABELS)
    comparing.add_argument("--corpus", type=Path, default=CORPUS)
    args = parser.parse_args(argv)
    if args.command == "write":
        items = write()
        print(f"{MATERIAL_DIR}: {len(items)} 項目")
        return 0
    if args.command == "labels":
        corpus = load_corpus(args.corpus)
        found, empty, errors, warnings = parse_labels(
            read_material(args.material), corpus, args.labeler
        )
        for warning in warnings:
            print(f"警告: {warning}")
        if errors:
            print("\n".join(f"誤り: {error}" for error in errors))
            return 2
        save_labels(found, args.out)
        print(f"{args.out}: ラベル {len(found)} 件、空の「ラベル:」{len(empty)} 件")
        return 0
    return compare(args.labels, args.corpus)


if __name__ == "__main__":
    sys.exit(main())
