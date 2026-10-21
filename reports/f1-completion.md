# F1 完了判定（検証役）

- 日付: 2026-10-22
- 役割: 検証役（第三者。plan.md 第5.9節）。実装の作業過程（docs/progress.md、過去の reports/f1-init-*.md）は判定の根拠にしていない。読んだのは仕様（docs/plan.md、docs/decisions.md）と成果物だけ
- 対象: schema/（workflow.schema.json、examples/）、contract/、src/harness\_testing\_framework/、tests/、examples/toy-minimal/、scripts/check.sh、.github/workflows/ci.yml、pyproject.toml
- 書いたもの: この文書だけ。リポジトリを壊す実験は、リポジトリ外の一時ディレクトリに写しを作って行った。git は読み取り（`git ls-files`、`git rev-parse`）だけを使い、変更していない

## 総合判定: 正常（人間の承認を除いて完了条件を満たす）

第6節 F1 の完了条件は、人間の承認を除いてすべて満たしている。第2節の固定判断や決定 #1〜#5、#7〜#10、追加の論点 A〜C、D-1、D-2 との矛盾は見つからなかった。重大度「高」の指摘は無い。

承認の前に直すか、承認者に示すことを勧める重大度「中」の指摘が二つある。

1. 中-1: `goal` を end\_state の id に使えてしまう。スキーマも検査器も通す。契約では evaluate の結果が `goal`、end\_state の id、`unknown` のいずれかになり、分類の選択肢も id で区別するので、`goal` という id は正常系と衝突して三層の区別を崩す。`unknown` は特別に扱っているが、`goal` は扱っていない
2. 中-2: 検査器のいくつかの分岐がテストで固定されていない。変異テストで次の五つが生き残った。D-1 のディレクトリ規則の二つの分岐（末尾の / はディレクトリ全体）、前のステージの memory\_out で memory\_in を供給する分岐、ステージ id の重複、end\_state id の重複。いま検査器が正しく動くことは自作の例で確かめたが、テストはこれらの退行を捕まえない

中-1 を「中」にとどめ「準正常」にしない理由: 第6節 F1 と付録 B が挙げる検査器の性質（参照整合、全単射、前方性、max、carry、指標、unknown）に予約語の検査は入っていない。完了条件を文字どおり読めば満たしている。ただし、スキーマと契約の承認は意味を固定するものなので、承認の前に直すのが安い。

人間の承認（スキーマと契約）はまだ無い。契約の文書も自らを「下書き。人間の承認待ち」としている。この判定は承認待ちとする。

## 項目ごとの判定

### 1. 拡張スキーマ（メタスキーマ適合、正例と負例、付録 A の意味）: 満たす

証拠:

- `Draft202012Validator.check_schema` に適合する（tests/test\_schema\_examples.py と、自分でも別に実行した）
- 正例 2 件（valid/minimal.yaml、valid/full.yaml）が拡張スキーマを通る。付録 A の基底スキーマも通る（拡張が正例を基底の外に出していない）
- invalid-schema の負例 14 件が、それぞれ先頭の注釈で宣言した検証キーワードと位置で落ちる（テストが確かめる。CLI でも全件 exit=1）
- invalid-spec の負例 18 件と toy-minimal は、拡張スキーマと付録 A の基底スキーマの両方を通る（自分で確かめた）。スキーマではなく検査器が捕まえるという D-1 の分け方どおり
- 同梱するスキーマ（src/harness\_testing\_framework/schema/workflow.schema.json）は schema/workflow.schema.json とバイト単位で同じ（`cmp`）

付録 A の意味について:

- goal、end\_state、rollback、phase、stage の必須項目は付録 A のまま残り、artifacts と rollback.max が必須に加わった
- rollback.stage の説明「このステージより以前の全てのステージの中から一つ」は文字どおり残る。前方のみを検査器が強制する（自己ループも禁止。追加の論点 A）
- unknown は分類 id として必須（検査器）で、rollback を持てない（検査器）。例外系の意味を保っている
- 付録 A が列挙する拡張（carry、max、artifacts、指標の形、additionalProperties）を超える追加がある。workflow.inputs、awaits\_user、指標の args、x- 拡張、minItems。どれも D-1 に記録があり、既存の意味は変えていない。ただしスキーマの承認では明示して見せるべき（低-14）

### 2. 検査器の各性質の負例、付録 B との一致、検査器の誤り: 満たす（指摘あり）

性質ごとの負例（schema/examples/）と、CLI の結果:

| 第6節 F1 の性質 | 符号 | 負例 | 結果 |
| --- | --- | --- | --- |
| 参照整合 | duplicate\_id / unresolved\_reference / unresolved\_read | 1 / 2 / 2 | 各 exit=1、その符号だけ |
| unknown を除く end\_state と rollback の全単射 | rollback\_bijection | 3（rollback 無し、二重、unknown に rollback） | 各 exit=1 |
| 戻り先の前方性 | rollback\_forward | 2（後ろへ、自分へ） | 各 exit=1 |
| max の存在と有界性 | rollback\_max | 4（欠落、0、1.5、.inf。スキーマで捕まえ符号を付け替える） | 各 exit=1 |
| carry の生成と消費 | carry\_undeclared / memory\_unsupplied / memory\_unused | 2 / 1 / 1 | memory\_unused は警告で exit=0、他は exit=1 |
| 指標の存在 | metric\_unregistered（と metric\_range） | 2（ステージ、フェーズ）と 1 | 各 exit=1 |
| unknown の存在 | unknown\_missing | 1 | exit=1 |

付録 B の末尾の検査項目との一致:

| 付録 B の項目 | 検査器 |
| --- | --- |
| unknown を除く end\_state と rollback.state が一対一 | rollback\_bijection |
| 戻り先がそのステージより前 | rollback\_forward（位置はフェーズを跨いだ通し順で比べる） |
| 全ての rollback に max があり有界 | rollback\_max（1 以上の整数。真偽値、文字列、小数、inf を拒む） |
| carry の各項目が元の memory\_out と戻り先の memory\_in にある | carry\_undeclared |
| quantitative の指標名が指標レジストリにある | metric\_unregistered（ステージとフェーズの両方） |
| end\_state の記述の良し悪しは人間のレビュー | 検査しない（checker.py の冒頭に明記）。優先順も検査しない（決定 #7） |

一致している。付録 B に無い検査が四つ加わっている。unresolved\_read（D-1 の reads の規則から導ける）、memory\_unsupplied（エラー）、memory\_unused（警告）、metric\_range。締める方向の追加で矛盾ではないが、decisions.md に明示の記録が無いものがある（低-13）。

検査器の誤り（自分で作った例で探した。一時ディレクトリの probe スクリプト。最小の正例と full の正例を一か所ずつ変えて check\_workflow に渡す）:

- 正しく捕まえたもの: ステージ id の重複、end\_state id の重複、自分のステージの writes だけを読む、前方の memory を carry 無しで後ろから供給する、最初のステージから自分へ戻る、戻り先の memory\_in の欠落、max の真偽値・文字列、フェーズを跨ぐ前方の戻り（正しく通す）、`max: 2.0`（JSON Schema では整数。通す）、glob 文字を含む reads（字義どおりのパスとして unresolved\_read）
- 見逃し: end\_state と rollback.state に `goal` を使う（中-1）。指標の `min: .nan`（低-7）。id の末尾の改行（Python の `$` が改行の前でも一致する。低-9）
- 誤検出: `reads: [./request.md]` が `inputs: [request.md]` と一致しない（低-4）。`--metrics-file` で `on` という名の指標が登録済みでも未登録と出る（低-2）
- 隠れる報告: rollback.state の綴り違いがあると、そのステージの全単射の検査を省く。rollback.stage が解決できないと、その carry の元側（memory\_out）の検査も省く（低-8）
- 誤分類: rollback の項目で state と max が両方無いと、state の欠落も rollback\_max と報告する（低-6）
- 落ちる: マッピングのキーが列（`? [a, b]`）だと読み込みが TypeError で落ち、CLI はトレースバックを出す（低-1）

変異テスト（写しの checker.py を一か所ずつ壊して pytest を回した。意味のある変異 16 件）:

- 殺された（11）: 自己ループの許容、unknown への rollback の許容、carry の戻り先側・元側の検査の削除、フェーズの指標の検査の削除、全単射を「2 個以上」だけにする、unknown の存在の検査の削除、解決できない戻り先の carry の抑制の削除、metric\_range の削除、unresolved\_read の削除、memory\_unused の削除
- 生き残った（5）: `_covers` のディレクトリの二つの分岐、前のステージの memory\_out による供給、ステージ id の重複、end\_state id の重複（中-2）

### 3. toy-minimal が検査を通る（3〜4 ステージ、ロールバック、carry、フェーズ境界越え、ユーザー待ち）: 満たす

証拠:

- `PYTHONPATH=examples/toy-minimal uv run python -m harness_testing_framework.testing.spec examples/toy-minimal/workflow.yaml --registry toy_minimal.metrics:REGISTRY` → `0 error(s), 0 warning(s)`、exit=0
- 2 フェーズ 4 ステージ（intake: ask\_topic, plan\_outline / compose: write\_note, review\_note）
- ロールバック 3 辺。すべて carry つき（topic\_questions、outline\_gaps、review\_findings）、max つき（2、1、2）
- フェーズ境界越え: write\_note → plan\_outline（compose → intake）。intake のゲートは plan\_outline が再び goal に達した時に評価し直される
- ユーザー待ち: ask\_topic に `awaits_user: true`
- 全ステージに unknown がある。遷移の六種（追加の論点 B）は、定義の上ではすべて起こりうる（examples/toy-minimal/tests/test\_definition.py）
- 書き方は付録 B の形（artifacts、goal の quantitative に description と基準、end\_state の記述、rollback の carry と max）

指摘: フェーズゲートで最終ステージの end\_state を選ぶ道が実質的に無い。review\_note が goal に達した後（修正を要する指摘が 0）では、findings\_blocking の記述（修正を要する指摘が一つ以上）は成り立たない。plan\_outline と topic\_unclear も同じ関係にある。このため、ゲートが不合格ならほぼ必ず unknown になる。決定 #5 の「最終ステージの end\_state の記述はフェーズ全体の不足も覆う」を玩具は満たしていない。六種の遷移の被覆には影響せず、F1 の完了条件の外だが、MECE レビューの予行として人間に見てほしい（低-12）。

### 4. 契約の文書化と、第2節・決定 #3・#4・#5・#8 との整合: 満たす（人間の承認待ち）

contract/contract.md v0.1 は次をすべて扱う。三操作（2.1〜2.3）、状態文書への投影（2.4）、遷移とフェーズゲート、中断と再開、escalate（3）、実行の状態（4）、スナップショット形式（5、snapshot.schema.json）、実行記録（6、trace.schema.json）、ステージ本体・指標レジストリ・ユーザー入出力・LLM クライアント・分類器・運用者のインターフェース（7）、ランタイムが実行時に強制すること（8）、記録再生（9）、契約適合テスト（10）。Python の束縛（harness\_testing\_framework.contract）は文書と対応し、mypy strict を通る。二つの形式スキーマはメタスキーマに適合し、例も通る（tests/test\_contract.py）。

第2節との照合:

- 境界: 三操作、スナップショット形式、四つのインターフェースがある。ハーネス固有の名前は無い。分類器と運用者のインターフェースは第2節の列挙に無い追加だが、運用者は決定 #3 の追加の提案として採られたもの。分類器は oracle の抽象（第6節 F2）に当たり、矛盾しない。ただし、誰がこれらを実装して束縛するかを契約は書いていない（低-11）
- 三層と評価順序: 2.2 は「指標 → (goal の定性判定と end\_state の分類を一回で) → unknown」。指標がすべて満たされた時だけ goal を選択肢に入れる。一見すると第2節の評価順序「goal 定性判定 → end\_state 分類」を一つにまとめているが、第2節の「分類器」の行は「goal と end\_state の記述をそのまま選択肢として渡して状態を分類させる」としている。両方の固定判断を同時に満たす読みとして整合すると判断した。指標の判定は分類より先にある。F4 の人間ゲートが「goal と end\_state と unknown を合わせたクラス集合が MECE か」を見ることも、一回で分類する読みを支持する。D-2 に明記されている。承認者には、この読みを明示的に確認してもらうのがよい
- 分類器: 記述をそのまま選択肢にし、分解も導出規則もしない。閾値未満と答え無しは unknown。閾値は較正結果からハーネスの設定として決める。整合する
- ロールバック: restore と overlay の二操作で、carry の項目だけを重ねる。辺ごとの max と、超過時の escalate がある。整合する
- 仕様は唯一の情報源: ランタイムは遷移をワークフロー定義から導き、発明しない（8）。整合する
- 非決定性の二層分離: LLM の呼び出しは recorder を経由し、フレームワークのテストは LLM を呼ばない。整合する

決定との照合:

- #3: 四つの選択（再実行、指定ステージへのロールバック、goal 到達扱いで続行（注記つき）、中止）と、運用者インターフェース（3.4、7.6）がある。強制通過は実行記録の escalation.decision とスナップショットの annotations で区別できる。整合する
- #4 (b): runner の中断状態、同期的なユーザー入出力、「まだ無い」の合図、開始時スナップショットからの再実行と回答の再生（3.3、4、7.3）がある。awaits\_user を宣言しないステージはユーザー入出力を使えない。整合する
- #5 (b): 最終ステージが goal に達した後のフェーズゲート。指標はフェーズの集約述語で、選択肢はフェーズの goal と最終ステージの end\_state。end\_state なら最終ステージの辺で戻る。ゲートの状態をスナップショットに含め、restore で無効化する（3.2、5）。整合する
- #8 (b): フレームワークが参照ランタイムを提供し、契約適合テストは参照ランタイムと自前の実装の両方が通す（10）。runtime/ は F2 の置き場として空のパッケージがある。整合する

指摘:

- contract/examples/trace.jsonl は形式の例としては適合するが、筋が契約と合わない。seq 12 のフェーズ評価は outcome が unknown なのに、seq 13 で gate\_pass、seq 14 で complete になる。seq 10 では回数 1 のまま max\_exceeded になる。F2 の手本として誤読されうる（低-10）
- 未記述の点。分類器と運用者の実装を誰が提供するか。フェーズゲートの分類に渡す状態文書の作り方（2.4 はステージの場合だけ）。2.4 の投影は memory\_out だけで memory\_in（carry で持ち帰った指摘）を含まない。決定 #1 の「reads / writes / memory を写す」との差は承認時に確認する（低-11）
- 予約語 `goal` を契約にも明記すべき（中-1 と同じ）

### 5. CI（ローカルと同じ検査を呼ぶ）: 満たす

- .github/workflows/ci.yml は push（main）と pull\_request で、ubuntu-latest に setup-uv（python-version 3.12）を入れ、`scripts/check.sh` を実行する。tests/test\_ci.py もこれを確かめる
- scripts/check.sh は `uv sync --locked`、ruff check、ruff format --check、mypy（strict。src、tests、examples/toy-minimal）、pytest（カバレッジつき）、wheel にスキーマが同梱されているかの確認を行う。実行ビット（100755）で追跡されており、uv.lock、ci.yml、check.sh は git の管理下にある（`git ls-files` で確認）
- ローカルで `scripts/check.sh` を実行して全部通った（下記）。GitHub 上で CI が動いたことは、この判定の範囲では確かめていない（remote での実行記録を見ていない）

### 6. 汎用性の規律（第5.8節）: 満たす

- tests/test\_package.py が src/、schema/、contract/ について、玩具・特定のハーネス・分類器・LLM・定理証明器の名前と、examples/ の各 workflow.yaml に現れる id・指標名・成果物名・記憶の名前が出てこないことを検査し、通っている
- 自分でも同じ範囲を grep した。該当は「boolean」の部分一致（lean）と、schema/examples/valid/full.yaml の一般的な brief.md だけで、玩具の名前ではない
- 本体の前提も確かめた。検査器が特別に扱う名前は unknown だけで、これはスキーマの意味の一部。契約は SHA-256 と JSON Lines という一般的な形式だけを前提にしている。玩具の指標レジストリと偽のステージ本体は examples/toy-minimal/ に閉じている

### 7. 決定の反映: 満たす（細部に指摘あり）

| 決定 | 反映先 | 判定 |
| --- | --- | --- |
| #1 (c) | スキーマの artifacts（reads / writes / memory\_in / memory\_out。必須）、検査器の carry と memory の検査、契約 2.4 の投影 | 反映。投影の範囲は低-11 |
| #2 (b) | 指標は名前と基準だけ（description、equals か min / max、args）。レジストリは契約 7.2 の names / measure。検査器は --registry か --metrics-file で受け取る | 反映 |
| #3 | 契約 3.4、7.6、trace の escalation.decision | 反映 |
| #4 (b) | awaits\_user、契約 3.3、7.3、AwaitingAnswer | 反映 |
| #5 (b) | フェーズの goal の説明、契約 3.2、スナップショットの gates | 反映。玩具の記述は低-12 |
| #7 (a) | priority 属性は無い（additionalProperties: false）。full.yaml は記述中に「優先する」を書く。検査器は優先順を見ない | 反映 |
| #8 (b) | runtime パッケージの置き場と契約 10 | 反映 |
| #9 (a) | 契約にサブワークフローを入れていない（adopting.md への指針は F2） | F1 の範囲で矛盾なし |
| #10 | Python >= 3.12、uv と uv.lock、pytest と pytest-cov、ruff（lint と format）、mypy strict、jsonschema と PyYAML、GitHub Actions、構成 (ii)、uv\_build、GPL-3.0-only、YAML のキーの文字列検査、$id を公開先の URL に | 反映 |
| 追加の論点 A | rollback\_forward が自分自身も拒む（負例 rollback\_to\_self） | 反映 |
| 追加の論点 B | 契約 3.5 の六種、toy-minimal の README と test\_definition | 反映 |
| 追加の論点 C | plan.md 第4節の注記（1）。図の展開（2）は人間待ち | 反映 |
| D-1 | パス、inputs、memory は名前だけ、指標の形、測定失敗は未達、max ≥ 1 の整数で必須、awaits\_user、id と名前の規則、additionalProperties と x-、$id、YAML の読み込み、負例の置き場 | 反映。細部は低-3、低-4、低-5 |
| D-2 | 評価の選択肢、本体の例外と契約違反は unknown、作業領域の作り直し、回数をスナップショットに含めない、ゲートと注記をスナップショットに含める、待ちの合図、実行記録とマニフェストの JSON Schema | 反映 |

## 実行したコマンドと出力の要旨

1. `scripts/check.sh`
   - `uv sync --locked`: 23 packages checked
   - ruff check: All checks passed。ruff format --check: 35 files already formatted
   - mypy: Success: no issues found in 24 source files
   - pytest: 136 passed。カバレッジは合計 99%（未到達は contract/\_\_init\_\_.py の 30-31、spec/\_\_main\_\_.py の 54、checker.py の 113）
   - `wheel: schema packaged`
2. 検査器の CLI を toy-minimal（`--registry toy_minimal.metrics:REGISTRY`）と、schema/examples の全例（`--metrics-file schema/examples/registry.yaml`）に実行した
   - toy-minimal: 0 error(s), 0 warning(s)、exit=0
   - valid 2 件: exit=0、違反なし
   - invalid-document 2 件、invalid-schema 14 件、invalid-spec 18 件: どれも宣言した符号だけを報告した。exit=1。ただし memory\_unused の 1 件は警告だけなので exit=0
3. `cmp schema/workflow.schema.json src/harness_testing_framework/schema/workflow.schema.json`: 一致
4. 付録 A の基底スキーマ（plan.md から抜き出したもの）で toy-minimal と invalid-spec 18 件を検証した: すべて通る
5. 自作の探索（一時ディレクトリの probe.py）: 正例を一か所ずつ変えた 27 件と、YAML の端の例 5 件を検査器に渡した。結果は項目 2 のとおり
   - YAML の読み込みでは `a: 1:30` → 90、`b: 010` → 8、`c: 0x1F` → 31、`d: 2026-10-21` → date になった。`Yes` は文字列のまま、`TRUE` は真偽値
   - レジストリの YAML に `- on` を書き、ワークフローの指標名を `on` にした場合: metric\_unregistered、exit=1（誤検出）
6. 変異テスト（一時ディレクトリの写しで mutate.py と mutate2.py を実行）: 意味のある変異 16 件のうち 11 件が殺され、5 件が生き残った（項目 2）

## 指摘の一覧

| ID | 重大度 | 項目 | 内容 | 直し方の案 |
| --- | --- | --- | --- | --- |
| 中-1 | 中 | 1, 2, 4 | end\_state と rollback.state に `goal` を使えてしまう。evaluate の結果と分類の選択肢の id が衝突し、正常系と準正常系の区別が崩れる | スキーマの end\_state.id に `"not": {"const": "goal"}` を足すか、検査器に符号を足す。invalid-spec に負例を置く。契約 2.2 に予約語（goal、unknown）を明記する |
| 中-2 | 中 | 2 | 検査器の分岐のうち、ディレクトリの被覆（二方向）、前のステージの memory\_out による供給、ステージ id と end\_state id の重複がテストで固定されていない（変異が生き残る） | 正例を足す（out/ を書いて out/x を読む、out/x を書いて out/ を読む、carry 無しで前から後ろへ memory を渡す）。負例を足す（duplicate\_id/stage\_id\_twice、duplicate\_id/end\_state\_id\_twice） |
| 低-1 | 低 | 2, 7 | マッピングのキーが列だと、読み込みが TypeError で落ちる（WorkflowDocumentError にならず、CLI はトレースバックを出す） | 重複を確かめる前にキーの型を確かめるか、ハッシュできないキーを WorkflowDocumentError にする |
| 低-2 | 低 | 2 | `--metrics-file` を `yaml.safe_load`（YAML 1.1）で読むので、on / off / yes / no という名の指標が真偽値になり、誤って未登録と出る | ワークフローと同じローダーで読む。`metrics` が無い時、一覧でない時のエラーも分かるようにする |
| 低-3 | 低 | 7 | ローダーは YAML 1.1 の 60 進数・8 進数・日付の解決を残している（`max: 1:30` が黙って 90 になる）。D-1 の「真偽値は true / false の綴りだけ」に対して、True / TRUE / False / FALSE も真偽値になる（YAML 1.2 core と同じで実害は小さい） | 整数と日付の暗黙の解決も YAML 1.2 core に揃えるか、docstring と D-1 の記述を実装に合わせる |
| 低-4 | 低 | 2, 7 | パスを正規化しない。`./request.md` は `request.md` と一致せず unresolved\_read になり、メッセージから理由が分からない。スキーマは `./`、`a//b`、`.` を許す | スキーマで `./`、空の区切り、`.` を拒むか、検査器で正規化する |
| 低-5 | 低 | 7 | D-1 は glob を入れないとしているが、スキーマのパスのパターンは `*`、`?`、`[` を拒まない | 拒むか、字義どおりのパスとして扱うことを明記する |
| 低-6 | 低 | 2 | rollback の項目で state と max が両方無いと、state の欠落も rollback\_max と報告する | required のエラーのうち、欠けているのが max の場合だけ rollback\_max にする |
| 低-7 | 低 | 1, 2 | 指標の基準に NaN と ±inf を書ける。`min: .nan` は満たしようがないが通り、metric\_range も NaN を比較できない | 基準を有限の数に限る（検査器で math.isfinite） |
| 低-8 | 低 | 2 | 参照の誤りが他の報告を隠す。rollback.state が解決できないと、そのステージの全単射の検査を省く。rollback.stage が解決できないと、元側の memory\_out の検査を省く | 解決できた項目だけで全単射を検査する。元側の検査は戻り先が解決できなくても行う |
| 低-9 | 低 | 1 | id と名前のパターンの `$` は、Python の jsonschema では末尾の改行の前でも一致し、`"abc\n"` が通る。ECMA 262 の検証器では落ちるので、言語に依存しないスキーマとして結果が揃わない | パターンで改行を明示的に除く（例: `^[a-z][a-z0-9_-]*$` に加えて `"not": {"pattern": "\n"}`） |
| 低-10 | 低 | 4 | contract/examples/trace.jsonl の筋が契約と合わない（フェーズ評価が unknown の後に gate\_pass と complete。回数 1 で max\_exceeded） | 筋の通った実行（max: 2 を超えるまで回すなど）に直すか、形式だけの例であると明記する |
| 低-11 | 低 | 4 | 契約の未記述: 分類器と運用者を誰が提供して束縛するか、フェーズゲートの状態文書、2.4 の投影が memory\_in を含まない理由 | 承認の前に書き足すか、F2 での確定事項として明記する |
| 低-12 | 低 | 3 | toy-minimal の最終ステージの end\_state の記述は、goal に達した後のゲート不合格を覆わない。ゲートの不合格はほぼ unknown になる（決定 #5 の「フェーズ全体の不足も覆う」を満たさない） | 人間の MECE レビューで判断する。分類体系の変更なので提案止まり（第5.4節） |
| 低-13 | 低 | 2, 7 | 付録 B に無い検査（unresolved\_read、memory\_unsupplied をエラーにすること、memory\_unused を警告にすること、metric\_range）は、decisions.md に明示の記録が無い（reads の規則だけ D-1 にある） | 承認者に一覧として示し、D-1 に追記する |
| 低-14 | 低 | 1 | 付録 A の列挙（carry、max、artifacts、指標の形、additionalProperties）を超える追加がある（inputs、awaits\_user、args、x- 拡張、minItems）。D-1 に記録があり既存の意味は変えていないが、スキーマの承認で明示して見せるべき | 承認の依頼に一覧を添える |
| 低-15 | 低 | 公開（F1 外） | reports/f1-init-verification.md に、手元のホームディレクトリと一時ディレクトリの絶対パスがある。決定 #10 の公開前の点検の対象 | 公開前に、リポジトリからの相対パスに置き換える |

## 人間の承認（スキーマと契約）で見てほしい点

- 中-1 の予約語 `goal` の扱い（承認の前に直すことを勧める）
- 契約 2.2 の「指標 → goal と end\_state を一回で分類 → unknown」という読みが、第2節の評価順序と分類器の判断を満たすか（検証役は整合すると判断した）
- 付録 A を超えるスキーマの追加（低-14）と、付録 B を超える検査（低-13）
- toy-minimal のフェーズゲートと最終ステージの end\_state の関係（低-12）
