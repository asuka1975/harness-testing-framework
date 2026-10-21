# F1 初期化タスクの完了条件の検査

F1 の初期化タスクの完了条件を、実装より先に実行可能な形で書いたもの（plan.md 第5.3節の 2）。#10（言語・ツールチェーン）が未決でリポジトリに .py を置けないので、ここに全文を残す。再実行するには、下のコードを任意の場所に check_init.py として保存し、`python3 -I check_init.py <リポジトリの根>` を実行する（jsonschema 4 系が要る）。T1 で、恒久的に意味のある条件をリポジトリのテストへ移す。

## 版の履歴

- 一回目（16 条件）: 検証役の変異テスト 10 件をすべて素通りさせた（reports/f1-init-verification.md の M-6）
- 二回目（21 条件）: 10 件を捕まえたが、二件の退行が入った（README.md と .gitkeep をどこでも許す、$schema の URL を含む行を丸ごと除外する。R2-M1）。ほかに、選択肢の追加、推奨の矛盾、一覧の表と追加の論点の承認を素通りさせた（R2-L1）
- 三回目（23 条件、下記）: 骨格のディレクトリにだけ README.md を許した。URL は部分文字列だけを取り除くようにした。次の検査を加えた
  - 選択肢の記号の集合が第3節と一致すること
  - 推奨の最初の文に別の選択肢が無いこと
  - 一覧の表と追加の論点が未決であること
- 三回目に検証役の mutate2.sh（変異 19 件と陽性対照 3 件）を再実行した。捕まえられなかったのは N7 の一件だけだった
  - N7 は、選択肢の文言を書き換える変異
  - 選択肢の中身が正しいかは機械的に照合できないので、検証役と人間のレビューに委ねる

## 実行結果（三回目の版。作業ツリーで実行）

```text
PASS  C1 git リポジトリの根が対象ディレクトリ
PASS  C2 ディレクトリ骨格
PASS  C2b 骨格が git で追跡可能（空ディレクトリなし）
PASS  C3a 付録 A の JSON を plan.md から抽出
PASS  C3b スキーマが JSON として読める
PASS  C3c スキーマが付録 A と意味的に一致
PASS  C3d スキーマが付録 A と文字列として一致（末尾改行を除く）
PASS  C3e スキーマが Draft 2020-12 メタスキーマに適合
PASS  C4a 第3節の表から十行を抽出
PASS  C4b decisions.md に #1〜#10 の節がこの順にある
PASS  C4c 各節が第3節と一致し（選択肢・推奨・強制点）、文脈を持ち、未決のまま
PASS  C4e 一覧の表の全行が未決で、決定欄が空
PASS  C4f 追加の論点も未決で、決定が未記入
PASS  C4d #6 は F5 で決める扱い
PASS  C5a progress.md の最初の節が「次にやること」
PASS  C5b 日付の節がある
PASS  C5c 日付節の中に固定の小見出しがそろう
PASS  C6 本体に玩具・特定ハーネスの名前がない
PASS  C7 許すファイルの一覧の外にファイルが無い（言語固有物・後の成果物の先取りなし）
PASS  C8 software-factory は F4 の作業領域として空（.gitkeep のみ）
PASS  C9a コミットがある
PASS  C9b plan.md が最初のコミットから変わっていない（作業ツリーを含む）
PASS  C9c progress.md に plan.md の sha256 が記録され一致する

23/23 PASS
```

## check_init.py

```python
"""F1 初期化タスクの完了条件（実装より先に書く）。

使い方: python3 -I check_init.py <repo_root>
各条件を PASS/FAIL で出力し、FAIL が一つでもあれば終了コード 1。
"""
import json
import pathlib
import re
import subprocess
import sys

from jsonschema import Draft202012Validator

root = pathlib.Path(sys.argv[1]).resolve()
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


# C1 git リポジトリが初期化されている
r = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                   capture_output=True, text=True)
check("C1 git リポジトリの根が対象ディレクトリ", r.stdout.strip() == str(root), r.stdout.strip() or r.stderr.strip())

# C2 第4節の骨格（言語に依存しない範囲）と reports/（第5.9/5.10節が書き込み先として参照）
dirs = [
    "schema", "schema/examples", "contract", "runtime",
    "testing/spec", "testing/harness", "testing/oracle", "testing/stages",
    "testing/e2e", "testing/triage",
    "examples/toy-minimal", "examples/toy-minimal/stages", "examples/toy-minimal/tests",
    "examples/software-factory", "docs", "reports",
]
missing = [d for d in dirs if not (root / d).is_dir()]
check("C2 ディレクトリ骨格", not missing, f"missing={missing}")
# 空ディレクトリは git が追跡しないので、各ディレクトリに追跡用ファイルがあること
untracked_dirs = [d for d in dirs if (root / d).is_dir() and not any(p.is_file() for p in (root / d).iterdir())]
check("C2b 骨格が git で追跡可能（空ディレクトリなし）", not untracked_dirs, f"empty={untracked_dirs}")

# C3 schema/workflow.schema.json が付録 A と一致し、メタスキーマに適合する
plan = (root / "docs/plan.md").read_text(encoding="utf-8")
m = re.search(r"## 付録 A 基底スキーマ.*?```json\n(.*?)\n```", plan, re.S)
appendix_a = m.group(1) if m else None
check("C3a 付録 A の JSON を plan.md から抽出", appendix_a is not None)
schema_path = root / "schema/workflow.schema.json"
schema_text = schema_path.read_text(encoding="utf-8") if schema_path.exists() else None
try:
    schema = json.loads(schema_text)
    parsed = True
except Exception as e:  # noqa: BLE001
    schema, parsed = None, False
check("C3b スキーマが JSON として読める", parsed)
check("C3c スキーマが付録 A と意味的に一致", parsed and appendix_a and schema == json.loads(appendix_a))
check("C3d スキーマが付録 A と文字列として一致（末尾改行を除く）",
      schema_text is not None and appendix_a is not None and schema_text.rstrip("\n") == appendix_a)
try:
    Draft202012Validator.check_schema(schema)
    meta_ok, meta_err = True, ""
except Exception as e:  # noqa: BLE001
    meta_ok, meta_err = False, str(e)[:200]
check("C3e スキーマが Draft 2020-12 メタスキーマに適合", parsed and meta_ok, meta_err)

# C4 decisions.md を第3節の表と照合する
dec_path = root / "docs/decisions.md"
dec = dec_path.read_text(encoding="utf-8") if dec_path.exists() else ""
sec3 = re.search(r"## 3\. 未決事項.*?\n(\| # \|.*?)\n\n", plan, re.S).group(1)
rows = {}
for line in sec3.splitlines():
    cells = [c.strip() for c in line.strip("|").split("|")]
    if cells and cells[0].isdigit():
        rows[int(cells[0])] = {"options": cells[2], "rec": cells[3], "force": cells[4]}
check("C4a 第3節の表から十行を抽出", sorted(rows) == list(range(1, 11)), f"{sorted(rows)}")
h2_all = list(re.finditer(r"^## .*$", dec, re.M))
sections = {}
for i, h in enumerate(h2_all):
    mm = re.match(r"^## #(\d+)\b", h.group(0))
    if mm:
        sections[int(mm.group(1))] = dec[h.end(): h2_all[i + 1].start() if i + 1 < len(h2_all) else len(dec)]
check("C4b decisions.md に #1〜#10 の節がこの順にある", list(sections) == list(range(1, 11)), f"found={list(sections)}")


def subsec(body, title):
    m2 = re.search(rf"^### {title}[^\n]*\n(.*?)(?=^### |\Z)", body, re.M | re.S)
    return m2.group(1) if m2 else ""


problems = []
for n, row in rows.items():
    body = sections.get(n, "")
    for t in ["文脈", "選択肢と帰結", "推奨"]:
        if not re.search(rf"^### {t}", body, re.M):
            problems.append(f"#{n}:###{t}なし")
    status = re.search(r"^- 状態: (.*)$", body, re.M)
    if not status or not status.group(1).startswith("提案（下書き・未決"):
        problems.append(f"#{n}:状態が下書きでない")
    decided = re.search(r"^- 決定: (.*)$", body, re.M)
    if not decided or decided.group(1).strip() != "（未記入）":
        problems.append(f"#{n}:決定が未記入でない")
    force = re.search(r"^- 強制点: (.*)$", body, re.M)
    want_f = re.match(r"F\d", row["force"]).group(0)
    if not force or not force.group(1).startswith(want_f):
        problems.append(f"#{n}:強制点が{want_f}で始まらない")
    # 選択肢: 記号 (a)(b)(c) か、#3 の四つの語
    opts = re.findall(r"\([a-c]\)", row["options"]) or [o.strip() for o in row["options"].split("/")]
    if n == 10:
        opts = [t for t in ["Python 3.12", "uv", "pytest", "ruff", "jsonschema", "PyYAML", "GitHub Actions",
                            "git tag", "GitHub Release"]]
    choices = subsec(body, "選択肢と帰結")
    if n not in (3, 10):
        listed = set(re.findall(r"^- (\([a-z]\))", choices, re.M))
        if listed != set(opts):
            problems.append(f"#{n}:選択肢の記号 {sorted(listed)} が第3節 {sorted(set(opts))} と違う")
    for o in opts:
        key = o.split("（")[0]
        found = (key in choices) if n == 10 else re.search(rf"^\s*(?:- |\d+\. ){re.escape(key)}", choices, re.M)
        if not found:
            problems.append(f"#{n}:選択肢 {key} なし")
    # 推奨: 第3節の推奨の先頭（記号か「四つすべて」）
    rec_head = re.match(r"\([a-c]\)|四つすべて|Python 3\.12", row["rec"]).group(0)
    rec_text = subsec(body, "推奨").strip()
    if not rec_text.startswith(rec_head) and rec_head not in rec_text[:40]:
        problems.append(f"#{n}:推奨が {rec_head} で始まらない")
    first_sentence = rec_text.split("。")[0]
    if set(re.findall(r"\([a-z]\)", first_sentence)) - {rec_head} or "ではなく" in first_sentence:
        problems.append(f"#{n}:推奨の最初の文に別の選択肢がある")
check("C4c 各節が第3節と一致し（選択肢・推奨・強制点）、文脈を持ち、未決のまま", not problems, f"{problems}")
table = re.search(r"^## 一覧\n(.*?)(?=^## )", dec, re.M | re.S)
bad_rows = []
for line in (table.group(1).splitlines() if table else []):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 6 and cells[0] not in ("#", "---"):
        if not cells[4].startswith("未決") or cells[5]:
            bad_rows.append(cells[0])
check("C4e 一覧の表の全行が未決で、決定欄が空", table is not None and not bad_rows, f"rows={bad_rows}")
extra_bad = []
for i, h in enumerate(h2_all):
    if h.group(0).startswith("## 追加の論点"):
        body = dec[h.end(): h2_all[i + 1].start() if i + 1 < len(h2_all) else len(dec)]
        st = re.search(r"^- 状態: (.*)$", body, re.M)
        de = re.search(r"^- 決定: (.*)$", body, re.M)
        if not st or not st.group(1).startswith("提案（下書き・未決") or not de or de.group(1).strip() != "（未記入）":
            extra_bad.append(h.group(0)[3:12])
check("C4f 追加の論点も未決で、決定が未記入", not extra_bad, f"{extra_bad}")
check("C4d #6 は F5 で決める扱い", "F5" in (re.search(r"^- 状態: (.*)$", sections.get(6, ""), re.M) or [""])[0],
      "状態の行に F5 が無い")

# C5 progress.md が第4節の固定形式に従う
prog_path = root / "docs/progress.md"
prog = prog_path.read_text(encoding="utf-8") if prog_path.exists() else ""
h2 = re.findall(r"^## (.+)$", prog, re.M)
check("C5a progress.md の最初の節が「次にやること」", bool(h2) and h2[0].strip() == "次にやること", f"h2={h2[:3]}")
check("C5b 日付の節がある", any(re.match(r"\d{4}-\d{2}-\d{2}", h) for h in h2), f"h2={h2}")
needed = ["完了したこと", "未完了と理由", "発見した問題", "ワークフロー定義の問題", "フレームワーク本体の不足",
          "実行した検証とその結果の要旨"]
date_sec = re.search(r"^## \d{4}-\d{2}-\d{2}.*?(?=^## |\Z)", prog, re.M | re.S)
h34 = re.findall(r"^#{3,4} (.+)$", date_sec.group(0), re.M) if date_sec else []
lacking = [k for k in needed if not any(k in h for h in h34)]
check("C5c 日付節の中に固定の小見出しがそろう", not lacking, f"lacking={lacking}")

# C6 汎用性: フレームワーク本体に玩具・特定ハーネス・特定 LLM/分類器の名前がない
body_dirs = ["schema", "contract", "runtime", "testing"]
pat = re.compile(r"toy|玩具|software[-_ ]?factory|jev|system ?one|typesafe|claude|anthropic|openai|\bgpt|gemini|llama"
                 r"|mistral|\blean\b|\bcoq\b|isabelle|\bagda\b|\bz3\b|\bverify\b|\bdraft\b|\bcollect\b"
                 r"|要求の取り込み|要件分析|受け入れ条件|タスク分割", re.I)
hits = []
for d in body_dirs:
    for p in (root / d).rglob("*"):
        if p.is_file():
            for ln, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if pat.search(line.replace("https://json-schema.org/draft/2020-12/schema", "")):
                    hits.append(f"{p.relative_to(root)}:{ln}")
check("C6 本体に玩具・特定ハーネスの名前がない", not hits, f"{hits[:10]}")

# C7 #10 が未決で、後のマイルストーンの成果物も先取りしていない: 許すファイルの一覧の外にファイルが無い
allowed_files = ({f"{d}/README.md" for d in dirs if d not in ("docs", "examples/software-factory")}
                 | {"examples/README.md", "testing/README.md", "examples/software-factory/.gitkeep",
                    "docs/plan.md", "docs/decisions.md", "docs/progress.md", "schema/workflow.schema.json"})
allowed = re.compile("^(?:" + "|".join(re.escape(f) for f in sorted(allowed_files)) + r")$|^reports/[^/]+\.md$")
extra = sorted(str(p.relative_to(root)) for p in root.rglob("*")
               if p.is_file() and ".git" not in p.relative_to(root).parts and not allowed.match(str(p.relative_to(root))))
check("C7 許すファイルの一覧の外にファイルが無い（言語固有物・後の成果物の先取りなし）", not extra, f"{extra}")
sf = sorted(str(p.relative_to(root)) for p in (root / "examples/software-factory").rglob("*"))
check("C8 software-factory は F4 の作業領域として空（.gitkeep のみ）", sf == ["examples/software-factory/.gitkeep"], f"{sf}")

# C9 コミットがあり、保護ファイル plan.md が最初のコミットから変わっておらず、progress.md に記録した sha256 と一致する
import hashlib
head = subprocess.run(["git", "-C", str(root), "rev-list", "--max-parents=0", "HEAD"], capture_output=True, text=True)
first = head.stdout.split()[0] if head.returncode == 0 and head.stdout.split() else None
check("C9a コミットがある", first is not None, head.stderr.strip())
if first:
    d = subprocess.run(["git", "-C", str(root), "diff", "--quiet", first, "--", "docs/plan.md"])
    check("C9b plan.md が最初のコミットから変わっていない（作業ツリーを含む）", d.returncode == 0)
sha = hashlib.sha256((root / "docs/plan.md").read_bytes()).hexdigest()
check("C9c progress.md に plan.md の sha256 が記録され一致する", sha in prog, sha)

width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail if not ok else ''}".rstrip())
fails = sum(1 for _, ok, _ in results if not ok)
print(f"\n{len(results) - fails}/{len(results)} PASS")
sys.exit(1 if fails else 0)
```
