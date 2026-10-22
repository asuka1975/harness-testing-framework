"""人がラベルを付ける材料（docs/human-labeling.md）と、受け取ったラベルを印と比べる仕組み（adopting.md 第15.1節）。

往復 10 で代表を変えた所を、人が印を除いて読み、選択肢の記述だけでラベルを付ける（docs/review-findings.md の G-6）。
項目は、変えた代表（CHANGED）のどれかを状態文書に含む評価のうち、記述がその内容を証拠に使う対象（EVIDENCE）の訪問 1 の
もの。(対象, 印, 上流の違い) ごとに一つを選ぶ。上流の違いは、intake.md を読む対象ではペルソナ、unit_test では goal の実装の
変種。確率的な実行の分布に無い代表（unit_test の defective）も届くように、試しの実行は tests/stochastic.yaml の profiles の
labeling（訪問 1 の分布を寄せたもの）で走らせる。

    python -m software_factory.labeling write                   # 試しの実行から human-labeling.md とコーパスを書き直す
    python -m software_factory.labeling labels --labeler <名前>  # 埋めた「ラベル:」を docs/human-labels.jsonl にする
    python -m software_factory.labeling compare                 # human-labels.jsonl を印と比べる（無ければ、無いと報告する）

ラベルの形は contract/formats/label.schema.json、比べるのは `oracle_report(MarkerClassifier(), corpus, labels)`。
tests/test_labeling.py が、コミットした材料が試しの実行から作り直したものと一致することを確かめる。
"""

import argparse
import re
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from harness_testing_framework.testing.harness import MarkerClassifier, marked_class, unmarked
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
from software_factory.personas import KINDS, PERSONAS, WHO
from software_factory.stages.deterministic import FIXTURES, ROOT
from software_factory.stages.probabilistic import DISCOUNT, TABLE, WORKFLOW_MODEL, run_set

DOCS = ROOT / "docs"
MATERIAL = DOCS / "human-labeling.md"
CORPUS = DOCS / "human-labeling.corpus.jsonl"
LABELS = DOCS / "human-labels.jsonl"
TRIAL_PROFILE = "labeling"
TRIAL_RUNS = 120
TRIAL_SEED = 90000


def _fixture(stage: str, variant: str, name: str) -> str:
    return (FIXTURES / stage / variant / name).read_text("utf-8")


# 往復 10 で変えた代表と、それを見分ける文（状態文書に印つきのまま入る、成果物の内容か回答）
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
}
# 対象（scope, id）→ 記述がその内容を証拠に使う、変えた代表。並びは human-labeling.md の並び
EVIDENCE: dict[tuple[str, str], tuple[str, ...]] = {
    ("stage", "intake"): ("answer",),
    ("stage", "analyze"): ("requirements", "answer"),
    ("phase", "discovery"): ("requirements", "answer"),
    ("stage", "design"): ("requirements", "design"),
    ("stage", "unit_test"): ("tests",),
    ("stage", "acceptance"): ("requirements", "verification", "answer"),
}
# goal の実装の変種（unit_test の上流の違い）。acceptance の項目は、分布テストの主経路（markov）の実装の後のものに限る
# （requirement_unmet の代表は REQ-1 の誤りを見つけるので、正しい実装 ok_fixed とは組まない。ok_fixed は divergent だけ）
IMPLEMENTATIONS = ("ok", "ok_b", "ok_fixed")
MAIN_IMPLEMENTATIONS = {
    v
    for v in TABLE["profiles"]["markov"]["implement"]["first"]
    if TABLE["variants"]["implement"][v]["class"] == "goal"
}
FENCE = "~~~~~~"


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


def upstream(item: CorpusItem) -> str:
    """上流の違い: unit_test では goal の実装の変種、intake.md を読む対象ではペルソナ、ほかは空。"""
    if item.target == "unit_test":
        return implementation(item) or ""
    return persona(item) or ""


def wanted(item: CorpusItem) -> bool:
    """往復 10 で変えた代表を、記述がその内容を証拠に使う対象の訪問 1 で含む評価か。"""
    evidence = EVIDENCE.get((item.scope, item.target))
    if evidence is None or visit_of(item) != 1:
        return False
    if item.target == "acceptance" and implementation(item) not in MAIN_IMPLEMENTATIONS:
        return False
    return any(text in item.state for name in evidence for text in CHANGED[name])


def select(corpus: Sequence[CorpusItem]) -> list[CorpusItem]:
    """(対象, 印, 上流の違い) ごとに一項目。上流の違い（ペルソナ、実装の変種）のほかの違い（持ち帰った問いへの回答など）が
    少ないように、状態文書の短いものを選ぶ。並びは EVIDENCE の対象の順、その中は項目の id の順（印の順にならない）。
    出どころ（source）から分類器の選択（印）を除く。"""
    chosen: dict[tuple[str, str, str | None, str], CorpusItem] = {}
    for item in corpus:
        if not wanted(item):
            continue
        key = (item.scope, item.target, marked_class(item.state), upstream(item))
        best = chosen.get(key)
        if best is None or (len(item.state), item.item) < (len(best.state), best.item):
            chosen[key] = item
    order = list(EVIDENCE)
    items = sorted(chosen.values(), key=lambda i: (order.index((i.scope, i.target)), i.item))
    return [replace(i, source={k: v for k, v in i.source.items() if k != "choice"}) for i in items]


def trial_items(workdir: Path) -> list[CorpusItem]:
    """試しの実行（tests/stochastic.yaml の labeling）を走らせ、コーパスから材料の項目を選ぶ。"""
    runs, store = run_set(TRIAL_PROFILE, TRIAL_RUNS, TRIAL_SEED, workdir)
    return select(build_corpus(runs, store, WORKFLOW_MODEL, unique_states=True))


def unmarked_state(item: CorpusItem) -> str:
    """人に見せる状態文書（印を除いたもの。末尾の空行を落とす）。"""
    return unmarked(item.state).rstrip("\n")


def _target(item: CorpusItem) -> str:
    if item.scope == "phase":
        return (
            f"フェーズ {item.target} のゲート（フェーズの最終ステージの訪問 {visit_of(item)} の後）"
        )
    return f"ステージ {item.target} の訪問 {visit_of(item)}"


HEADER = """# 人がラベルを付ける材料（往復 11）

往復 10 で代表（偽の本体が写す成果物と、ペルソナの回答）を変えた所を、記述だけで分類してもらうための材料
（adopting.md 第15.1節、docs/review-findings.md の G-6）。`python -m software_factory.labeling write` が作る。手で書くのは
「ラベル:」の行だけで、ほかは直さない。`write` は材料を作り直し、埋めた「ラベル:」を空にする（ラベルを付け始めた後は、
付け直す範囲を決めてから実行する）。

## 読み方

- 各項目の「状態文書」は、分類器が見たものそのもの（そのステージの reads と writes のファイルの内容と、memory\\_out の記憶。
  ゲートの項目はフェーズの全体）から、偽の本体の印を除いたもの。指標の値は入っていない。指標が落ちた評価では、goal が
  選択肢に無い
- 印や、どの代表かを探さない（印は除いてある）。状態文書を読み、選択肢の記述だけで選ぶ（選択肢の記述は、ワークフロー
  定義の記述そのもの）。当てはまる選択肢の id を一つ、「ラベル:」の後に書く（例: `ラベル: goal`）
- 迷った時は unknown と書き、理由を添える（例: `ラベル: unknown（REQ-3 の根拠が回答に無い）`）。ほかのラベルにも理由を
  添えてよい。理由は「ラベル:」と同じ行に書く。理由は比べる時には使わないが、食い違いを直す時に読む
- 項目の並びは対象ごと。対象の中の並びは項目の id の順で、クラスの順ではない

## 選んだ項目

変えた代表のどれかを状態文書に含む評価のうち、記述がその内容を証拠に使う対象の訪問 1 のもの。(対象, クラス, 上流の違い)
ごとに一つ（上流の違いは、intake.md を読む対象では依頼者のペルソナ、unit\\_test では実装の変種）。

{counts}

## ラベルを付けた後

1. `python -m software_factory.labeling labels --labeler <名前>` で、この文書の「ラベル:」から docs/human-labels.jsonl
   （contract/formats/label.schema.json の形）を作る。空の「ラベル:」は数えて報告し、選択肢に無い id は誤りにする
2. `python -m software_factory.labeling compare` で、`oracle_report(MarkerClassifier(), corpus, labels)` を出し、印（ゲートは
   goal）とラベルが食い違う項目を挙げる。コーパスは docs/human-labeling.corpus.jsonl（項目の id はこの文書と同じ）
"""


def render(items: Sequence[CorpusItem]) -> str:
    """human-labeling.md の文。"""
    counts: dict[tuple[str, str], int] = {}
    for item in items:
        counts[(item.scope, item.target)] = counts.get((item.scope, item.target), 0) + 1
    names = {"stage": "ステージ", "phase": "ゲート"}
    lines = [f"- {names[s]} {t.replace('_', chr(92) + '_')}: {n}" for (s, t), n in counts.items()]
    lines.append(f"- 合わせて {len(items)} 項目")
    out = [HEADER.replace("{counts}", "\n".join(lines))]
    for n, item in enumerate(items, start=1):
        state = unmarked_state(item)
        if FENCE in state:
            raise ValueError(f"{item.item} の状態文書に {FENCE} がある")
        options = "\n".join(f"- `{o.id}`: {o.description}" for o in item.options)
        out.append(
            f"\n## 項目 {n}: `{item.item}`\n\n対象: {_target(item)}\n\n状態文書:\n\n"
            f"{FENCE}text\n{state}\n{FENCE}\n\n選択肢:\n\n{options}\n\nラベル:\n"
        )
    return "".join(out)


def sections(text: str) -> list[tuple[str, str]]:
    """human-labeling.md の項目ごとの (項目の id, 本文)。"""
    out = []
    for part in re.split(r"^(?=## 項目 \d+: `)", text, flags=re.M)[1:]:
        match = re.match(r"## 項目 \d+: `([^`]+)`\n", part)
        if match is None:
            raise ValueError(f"項目の見出しが読めない: {part[:40]!r}")
        out.append((match[1], part))
    return out


def _label_line(body: str) -> str:
    """本文の状態文書の後にある「ラベル:」の行の、「ラベル:」より後の文。"""
    tail = body.rsplit(f"\n{FENCE}\n", 1)[-1]
    found = re.findall(r"^ラベル:(.*)$", tail, flags=re.M)
    if len(found) != 1:
        raise ValueError(f"「ラベル:」の行が {len(found)} 個ある")
    return str(found[0]).strip()


def blank_labels(text: str) -> str:
    """埋めた human-labeling.md の「ラベル:」の行を空にした文（`write` が作る形。状態文書の中の行には触れない）。"""
    head, *parts = re.split(r"^(?=## 項目 \d+: `)", text, flags=re.M)
    out = [head]
    for part in parts:
        body, sep, tail = part.rpartition(f"\n{FENCE}\n")
        out.append(body + sep + re.sub(r"^ラベル:.*$", "ラベル:", tail, flags=re.M))
    return "".join(out)


def parse_labels(
    text: str, corpus: Sequence[CorpusItem], labeler: str
) -> tuple[list[Label], list[str], list[str]]:
    """埋めた human-labeling.md から (ラベル, 空の項目, 誤り)。ラベルは「ラベル:」の後の最初の id で、後の理由は捨てる。"""
    options = {item.item: [o.id for o in item.options] for item in corpus}
    labels: list[Label] = []
    empty: list[str] = []
    errors: list[str] = []
    for item_id, body in sections(text):
        if item_id not in options:
            errors.append(f"{item_id}: コーパスに無い項目")
            continue
        line = _label_line(body)
        if not line:
            empty.append(item_id)
            continue
        match = re.match(r"[a-z][a-z0-9_-]*", line)
        if match is None or match[0] not in options[item_id]:
            errors.append(f"{item_id}: 「{line}」は選択肢 {options[item_id]} のどれでもない")
            continue
        labels.append(Label(item_id, match[0], labeler))
    return labels, empty, errors


def write(material: Path = MATERIAL, corpus: Path = CORPUS) -> list[CorpusItem]:
    """試しの実行から材料を作り直す。"""
    with tempfile.TemporaryDirectory() as tmp:
        items = trial_items(Path(tmp))
    save_corpus(items, corpus)
    material.write_text(render(items), "utf-8")
    return items


def compare(labels_path: Path, corpus_path: Path = CORPUS) -> int:
    """ラベルを印と比べて報告する。ラベルのファイルが無ければ、そのことを報告して 1 を返す。"""
    if not labels_path.exists():
        print(
            f"ラベルのファイルが無い: {labels_path}\n"
            f"{MATERIAL.name} の「ラベル:」を埋め、`python -m software_factory.labeling labels "
            "--labeler <名前>` で作る"
        )
        return 1
    corpus = {item.item: item for item in load_corpus(corpus_path)}
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
                f"- {item.item}（{item.scope} {item.target}、訪問 {visit_of(item)}）: "
                f"印 {choice}、ラベル {label.label}（{label.labeler}）"
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
    sub.add_parser("write", help="試しの実行から human-labeling.md とコーパスを書き直す")
    labels = sub.add_parser("labels", help="埋めた「ラベル:」を JSON Lines にする")
    labels.add_argument("--labeler", required=True)
    labels.add_argument("--material", type=Path, default=MATERIAL)
    labels.add_argument("--out", type=Path, default=LABELS)
    labels.add_argument("--corpus", type=Path, default=CORPUS)
    comparing = sub.add_parser("compare", help="ラベルを印と比べる")
    comparing.add_argument("--labels", type=Path, default=LABELS)
    comparing.add_argument("--corpus", type=Path, default=CORPUS)
    args = parser.parse_args(argv)
    if args.command == "write":
        items = write()
        print(f"{MATERIAL}: {len(items)} 項目")
        return 0
    if args.command == "labels":
        corpus = load_corpus(args.corpus)
        found, empty, errors = parse_labels(args.material.read_text("utf-8"), corpus, args.labeler)
        if errors:
            print("\n".join(errors))
            return 2
        save_labels(found, args.out)
        print(f"{args.out}: ラベル {len(found)} 件、空の「ラベル:」{len(empty)} 件")
        return 0
    return compare(args.labels, args.corpus)


if __name__ == "__main__":
    sys.exit(main())
