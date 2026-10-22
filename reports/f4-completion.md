# F4 完了判定（検証役）

- 日付: 2026-10-22
- 対象: コミット 32b4d68（「F4 往復 7: N12 は解消し、adopting-gaps.md の「未解消」が空になった」）。元の作業ツリーには docs/progress.md の未コミットの変更があったが、examples/、src/、docs/ のほかの文書、contract/、schema/ には変更が無い。HEAD の内容を見た
- 役割: 検証役（第三者、plan.md 第5.9節）。成果物と仕様だけを読み、実装の作業過程は見ていない。docs/progress.md（計画エージェントの作業ログ）は読んでいない
- 読んだもの
  - 完了条件と目的: docs/plan.md 第6節 F4、第7節の二つ目のプロンプト（あわせて第1〜5節の関係する所）
  - 成果物: examples/software-factory/ 一式（workflow.yaml、README.md、software\_factory/、tests/（フィクスチャ、シナリオ、expectations を含む）、docs/adopting-gaps.md、docs/review-findings.md、docs/progress.md）
  - 本体と文書: src/ の公開の __init__ と、v0.1.0 からの差分、tests/test\_package.py、docs/adopting.md、docs/api.md、docs/api-reference.md、docs/changelog.md、contract/ の文書、docs/decisions.md の D-10〜D-16
  - 前例: reports/f3-completion.md、reports/f4-workflow-review.md、reports/f4-criteria-review.md
- 実験の環境
  - リポジトリを scratchpad に複製（git clone、32b4d68）し、その上で `uv sync --locked` した環境（Python 3.12.3）で行った。元の作業ツリーでは pytest も check.sh も走らせていない
  - 変異を入れる実験は、もう一つの複製の上で行い、一つずつ元に戻した（最後に git status が空であることを確かめた）
  - 参照値の計算には、フレームワークの依存とは別の環境（numpy 2.5.4、scipy 1.18.1、scikit-learn 1.9.1、statsmodels 0.15.0、PyYAML 6.0.3）を使った。フレームワークを import しない
- 人間のゲート（workflow.yaml のレビューと承認）は判定しない

## 総合判定: 準正常

第6節 F4 の完了条件（人間の承認を除く）は、すべて満たしている。整合性検査は誤りも警告も無く通り、`scripts/check.sh` は複製の上で通った（634 件が通過、例のテストは 173 件）。分布テスト、独立性検証、E2E のカバレッジとマルコフ合成、オラクル検証、トリアージは、どれも自分で実行し直して同じ結果を得た。オラクルの期待値（κ 0.623244、ECE 0.2685、答え無し 7、再実行の一致率 95/127）は、偽の分類器の配分から独立に計算した値と一致した。adopting-gaps.md の未解消は無く、直さないのは D2 だけで、その理由は D-11 にある。

読取制限は守られている。例のコードの import は、9 つの公開モジュールの `__all__` にある名前だけで、内部のモジュールや非公開の名前は一つも無い。例の中に、src/ のファイル名、決定の番号、本体の内部の名前は現れない。plan.md と decisions.md の語は「読んでいない」と書いた所にだけ現れる。

フレームワーク本体には、software factory の語も前提も入っていない。

それでも正常としないのは、例の側に、直すべき欠陥が二つ（中）残っているため（F2・F3 と同じく、完了条件を満たしていても直すべき欠陥があれば準正常とする）。

- 中 E-M1: 利用者役が手引き第15.1節を試して見つけた、記述と代表の成果物の三つの食い違いが、直されずに人間のレビューに回されている。どれも分類体系の変更ではなく、フィクスチャ（と、ペルソナに応じた成果物の選び方）の直しで済む。第5.4節が人間の承認を求めるのは分類体系の変更だけで、ここに当たらない
- 中 E-M2: discovery のゲートの goal（「intake.md の回答（利用者、…）がすべて requirements.md の要件か受け入れ基準に反映されている」）を、goal の代表の成果物がどのペルソナでも満たさない。記述どおりに読む分類器では、主経路が毎回このゲートで unknown になる。第15.1節の試しはステージの項目だけで行われ、ゲートの項目を見ていないので、README の一覧にも無い

本体の側には、高と中の指摘は無い。低が六つある（第9節）。

## 1. 完了条件の判定

| 完了条件 | 判定 | 証拠 |
| --- | --- | --- |
| workflow.yaml が整合性検査を通る | 満たす | 複製の上で `PYTHONPATH=examples/software-factory python -m harness_testing_framework.testing.spec examples/software-factory/workflow.yaml --registry software_factory.metrics:REGISTRY` → `0 error(s), 0 warning(s)`、終了コード 0。例の test\_passes\_checker\_without\_warnings も通る |
| 4 フェーズ以上 | 満たす | 5 フェーズ（discovery、architecture、construction、assurance、delivery） |
| 8 ステージ以上 | 満たす | 9 ステージ（intake、analyze、design、plan\_tasks、implement、unit\_test、acceptance、review、release） |
| フェーズ境界を越えるロールバック 1 以上 | 満たす | 定義の上で 6 本（design→analyze、implement→plan\_tasks、acceptance→analyze、acceptance→implement、review→design、review→implement）。シナリオで 5 本と運用者による越境（release→implement）を実際に通す（test\_crossing\_rollbacks\_from\_every\_later\_phase）。acceptance→analyze はシナリオでは通らず、E2E のカバレッジで踏む（E-L2） |
| ユーザー待ちのステージ 1 以上 | 満たす | intake（awaits\_user: true）。中断と再開のシナリオ（happy\_path\_user\_suspend）と、ペルソナが保留して再開するテストが通る |
| 実在のツールに裏づけられた決定論指標 3 以上 | 満たす | build\_passes（compileall と全モジュールの import）、tests\_pass（pytest）、line\_coverage（coverage run と coverage json）、lint\_errors（ruff）の 4 つ。ほかに out\_of\_scope\_changes（`view.baseline()` との差を tasks.yaml の範囲と比べる）。各指標を常に通す値に変える変異は、どれも test\_metrics.py で落ちる（第8.2節） |
| 参照ランタイムを組み込み、契約適合テストを通す | 満たす | 例は `Runtime` を組み込む。パッケージに同梱した 25 のシナリオ（`conformance_scenarios()`）が、例の束縛する参照ランタイムで期待どおり（test\_conformance.py）。ハーネスの側の義務は、分布テストの 800 回の実行で、契約違反、本体の例外、範囲外のファイルの警告が一度も無いことで確かめている（test\_bodies\_keep\_the\_contract）。契約適合テストの判定の対象をランタイムとする読み方（D-11 の B7）は、人間に確かめてもらう事項に挙げた（第10節） |
| 全ランナーが通る: 6 種の遷移 | 満たす | test\_all\_six\_transition\_kinds（14 シナリオで `transition_coverage` が `TRANSITION_KINDS` と一致）。escalate の四つの選択（rerun、rollback、continue\_as\_goal、abort）も通す |
| 確率的な偽の本体に対する分布テスト | 満たす | markov.yaml の 12 基準がすべて通り、markov\_shifted.yaml の 14 基準はすべて落ちる。markov\_gated.yaml の 4 基準が通り、markov\_gated\_shifted.yaml の 3 基準はすべて落ちる（第8.1節に観測値）。release の carry を無視させる変異と、ゲートを揺らさない変異は、正しい基準を落とす |
| 仕込んだ粗いクラスの検出 | 満たす | divergent は `stage:implement=goal`（訪問の区分 1 → 1、代表 126 と 136）で violated（p = 0.0005）、markov は同じ状態で not\_detected（p = 0.236）。種の基点を 20 通り変えると、divergent は 20/20 で violated、markov の独立性検証は 20/20 で違反なし（第8.3節） |
| (stage, end\_state) のカバレッジ 100% | 満たす | test\_coverage\_plan\_reaches\_every\_stage\_class: 30 の対象（goal、end\_state、unknown）をすべて踏み、`missing` が空。誘発と注入の両方を使い、intake の質問にはペルソナが答える |
| マルコフ予測と実測の一致 | 満たす | 実行し直した結果: 設計値のモデルの予測と markov の実測（400 回）は 46 の量すべてが 4 標準誤差以内（最大 \|z\| 2.44）。推定したモデル（種 40000 の 400 回）の予測も 46 すべて（最大 3.43）。ゲートの分布を足したモデルと、ゲートを揺らした実行は 47 すべて（最大 3.08）。入り方が二つ以上あるステージの訪問 2 以降は、`entry_dependence` で violated が無い |
| 偽の分類器に対するオラクル検証 | 満たす | 印を読む分類器で κ 1、ECE 0.1、再実行の一致率 1。既知の混同行列の分類器で κ 0.623244、ECE 0.2685、答え無し 7。揺れる分類器で一致率 95/127。どれも独立に計算した値と一致（第7節） |
| トリアージの一周 | 満たす | test\_one\_round\_of\_triage: 24 回の実行の全評価を待ち行列に入れ、五種類の判定で未判定を無くし、提案でワークフロー定義が変わらないことを確かめ、ラベルを付けた項目でオラクルのレポートを出す（κ 1、ECE 0.4 = \|1 − 0.6\|） |
| adopting-gaps.md の全項目が本体で解消されるか、解消しない理由が decisions.md にある | 満たす | 第1回の 30 項目は D-11、N1〜N7 は D-12、N8・N9 は D-13、N10 は D-14、N12 は D-16 で扱われ、N11 は 9c7b4cd で changelog.md に書き足された（本体の側の解消）。adopting-gaps.md の「未解消」は無し。解消しないのは D2 だけで、理由は D-11 の表（「モデルの区分に carry の有無を入れるのは、合成の仮定の拡張で、実ハーネスでの方法の検証（#6、F5）と合わせて決める」）と D-12 の N6 にある。D-11 で解消しないとした D4 は、D-12 の N5 で `RandomGateClassifier` により解消した（D-11 の D4 の行は書き換えられていない。B-L4） |
| 人間が workflow.yaml をレビューして承認 | 判定しない | 人間のゲート |

## 2. 第7節の二つ目のプロンプトが求めたもの

| 求めたもの | 判定 | 証拠 |
| --- | --- | --- |
| 4 フェーズ以上 8 ステージ以上、フェーズ境界を越えるロールバック、carry、ユーザー回答待ち | 揃っている | 第1節。12 本の辺がすべて carry を持つ |
| end\_state は自然言語で、成果物から観測できる条件。各クラスに戻り先、unknown を必ず含む | 揃っている（ただし E-M1、E-M2） | 全ステージの end\_state の最後が unknown で、unknown 以外の 12 クラスにそれぞれ一つの戻り先（test\_every\_class\_has\_a\_target\_and\_unknown\_has\_none）。carry する記憶を記述が証拠として名指す（test\_end\_states\_name\_the\_carried\_memory\_as\_evidence） |
| 決定論的な偽の本体はフィクスチャを写し、確率的な偽の本体は種を固定した既知の分布 | 揃っている | シナリオの台本（`ScriptedBody`）はフィクスチャを写す。確率的な本体は `context.seed` だけを乱数の源にして tests/stochastic.yaml の分布で変種を選ぶ（test\_choice\_depends\_only\_on\_the\_seed、test\_empirical\_choice\_matches\_design、test\_same\_seed\_gives\_the\_same\_run） |
| carry を受けた再進入で分布が変わる本体 | 揃っている | release は記憶 missing\_notes を受けたかで分布を選ぶ（goal 0.75 → 0.97）。訪問 2 以降と carry の有無が一致することを全実行で確かめる。carry を無視させる変異は markov.yaml の正しい基準を落とす |
| クラス内で下流の分布が分かれる本体 | 揃っている | divergent の implement の goal の二つの代表（ok は REQ-1 の切り捨てを誤る、ok\_fixed は正しい）。unit\_test の変種 defect のテストが実在の pytest で前者だけ落ちる。ok\_fixed を ok\_b に戻す変異は test\_divergent\_body\_is\_detected で落ちる |
| 実装と単体テストのステージで、fixtures の小さなコードベースに実際にビルドとテストを走らせる | 揃っている | implement と unit\_test の評価（と construction・delivery のゲート、acceptance）で、スナップショットの repo/ を一時ディレクトリに書き出し、compileall と import、pytest、coverage、ruff を子プロセスで走らせる。本体はフィクスチャを写すだけで、指標の値を偽らない |
| ビルド通過・テスト通過・カバレッジ・lint・変更パスの範囲を本物の指標に | 揃っている | build\_passes、tests\_pass、line\_coverage、lint\_errors、out\_of\_scope\_changes。各変種で、落ちるはずの指標だけが落ちることを実在のツールで確かめる（test\_variant\_fails\_exactly\_the\_designed\_metrics）。異常終了は覚えずに `MetricError`（test\_abnormal\_tool\_exit\_is\_an\_error\_and\_is\_not\_remembered） |
| 要求の取り込みにペルソナ 3 つ以上のユーザーシミュレータ | 揃っている | precise\_pm、vague\_founder、terse\_engineer。確率的な実行では種からペルソナを選び、実行ごとにランタイムを組み立てる。シナリオと E2E のカバレッジにも束縛する。ペルソナをいつも一つにする変異は、独立性検証の「ペルソナごとの三つの代表」のテストで落ちる |
| フレームワークのランナーをすべて通す | 揃っている | 第1節 |
| adopting-gaps.md と progress.md を書く | 揃っている | どちらもある。サブエージェントを使った記録は無い |

## 3. F4 の目的の三つ

### 3.1 フレームワーク本体が特定のワークフローに依存していない

- tests/test\_package.py の三つの検査（禁止語、例の id が本体に現れないこと、本体の語の範囲）は、check.sh の中で通った
- 自分でも grep した。software factory のワークフロー定義の全 id、指標名、成果物のパス、記憶の名前（91 語）に、shopcart、Cart、REQ-、割引、ペルソナ、persona、ペルソナの名前、compileall、ruff、pytest、coverage、software、factory、PCT10、OFF500、ok\_fixed、divergent などを足して、src/、schema/、contract/ を語の境界で照合した。現れたのは coverage だけで、これは v0.1.0 からある E2E のカバレッジ（testing/e2e/coverage.py）と `OracleReport.coverage`（答えた割合）の一般語である
- v0.1.0 からの本体の変更（`RandomGateClassifier`、`entries`・`entry_dependence`、`unique_states`、シナリオの `{from: パス}`、`user=`、`Prediction` の三つの量、トリアージの読み足し）は、どれも一般化した形で書かれ、toy-minimal と本体のテストで確かめられている。ステージ名、ツール名、ペルソナの前提は入っていない
- adopting.md 第7節の例にある `intake#1` は toy-minimal のフェーズの id で、software factory の語ではない。adopting.md 第12節の「ペルソナ」は、ユーザーシミュレータを実行ごとに変える一般の書き方として出てくる

### 3.2 adopting.md だけでハーネスを作れる

- 例は公開の名前だけで書かれている（第4節）。最初の版で足りなかった 30 項目と、往復で見つかった N1〜N12 は、すべて本体の文書か公開の API の追加で解消した。手引きは、往復で分かったこと（記憶を訪問のたびに書く、異常終了を覚えない、偏った割合の幅、第15.1節の手順など）を取り込んでいる
- 留保: 往復 6 の直しは、本体の実装を読んだ検証役の事前レビューを、計画の側が公開の文書の語で書き直して渡したもの（docs/review-findings.md、D-15）に基づく。そこで分かった一般の不足は手引きに入った（第2.1・4・12節）ので、次の利用者は手引きだけで同じことを知れる。ただ「利用者が手引きだけで MECE な定義に到達した」とまでは言えない。人間のレビューでこの経緯を踏まえてほしい（第10節）

### 3.3 実在の決定論指標が指標レジストリに乗る

- `REGISTRY`（`MetricRegistry` を満たす例の実装）は 17 の指標を持ち、うち 4 つが実在のツール、1 つがスナップショットの差に裏づけられる。整合性検査器がワークフロー定義の参照する指標がすべてレジストリにあることを確かめ、ランタイムが評価のたびに測る
- 分布テストに使う 800 回の実行で、測定の失敗は一度も無く、印が goal の評価ではいつも goal が選択肢にある（test\_metrics\_never\_fail\_to\_measure\_and\_goal\_marks\_keep\_goal）
- 基準の確認の M2（異常終了を覚える）は直った。意味の決まった終了コードだけを覚え、ほかは `MetricError` にする。終了コード −9、3、4 を注入するテストと、収集の失敗（pytest の 2）のテストがある

## 4. 読取制限（第7節）の機械的な証拠

作業ログの申告ではなく、成果物そのものを解析した。

### 4.1 import の解析

examples/software-factory/ の Python ファイル 19 個（tests/fixtures/ の下を除く）を AST で読み、`harness_testing_framework` からの import をすべて集め、9 つの公開モジュールの `__all__`（実行時に読んだもの）と照合した。

| モジュール | 例が import する名前 |
| --- | --- |
| schema | load\_workflow\_document |
| testing.spec | check\_workflow\_file |
| contract | AwaitingAnswer、Classifier、JSONValue、MetricError、Question、SnapshotView、StageContext、UserIO、load\_contract\_schema |
| runtime | BlobStore、RunState、Runtime、load\_workflow |
| testing.harness | AbortOperator、MarkerClassifier、RandomGateClassifier、ScenarioResult、TRANSITION\_KINDS、conformance\_scenarios、load\_scenario、marked\_class、run\_scenario、transition\_coverage |
| testing.stages | Expectations、RunRecord、RunSet、entry\_dependence、evaluate\_expectations、independence、load\_expectations、record\_run、run\_many、runs\_from\_environment |
| testing.e2e | MarkovModel、Prediction、compare\_prediction、coverage\_targets、estimate\_model、plan\_coverage、run\_coverage、synthesize |
| testing.oracle | ConfusionClassifier、CorpusItem、FlakyClassifier、Label、build\_corpus、load\_corpus、load\_labels、oracle\_report、save\_corpus、save\_labels |
| testing.triage | Decision、PROPOSALS、TriageInvalid、decide、decisions、enqueue、items、open\_items |

- すべて `__all__` にある。内部のモジュール（runtime.runner、testing.harness.fakes、testing.e2e.markov など）からの import は無い。`import harness_testing_framework.…` の形も、文字列による動的な import も無い
- 先頭が `_` の属性への参照は、`_RESULTS`、`_measures`、`_run` の三つだけで、どれも例自身のモジュール software\_factory.metrics のもの（テストが自分の指標の覚え方を確かめるために触る）。本体の非公開の名前ではない
- 本体のオブジェクトに対して使う属性と引数の名前（`r.next_visit`、`c.within`、`report.reached`、`prediction.visit_outcomes`、`state.pending` など）を集め、api-reference.md、api.md、adopting.md に無いものを探した。見つかったのは pytest と PyYAML の名前（MonkeyPatch、SafeDumper など）だけだった
- `dir(context)`、`vars(`、`__dict__` による内部の覗き見も無い。toy-minimal のコードも import していない

### 4.2 語の検索

- src/ のファイル名（checkpoint.py、loader.py、model.py、runner.py、recorder.py、fakes.py、scenario.py、trace.py、checker.py、expectations.py、independence.py、runs.py、markov.py、coverage.py、oracle.py、\_\_main\_\_.py）: 現れない（test\_oracle.py と test\_e2e.py の自分のファイル名を除く）
- `harness_testing_framework/`、`src/harness`、`runtime/` などの本体のパス: 現れない（`repo/src/` はフィクスチャのコードベースのパス）
- 決定の番号（`D-数字`、`決定 #`、ADR）: 例のコードには現れない。文書には一か所だけ、examples/software-factory/docs/progress.md の第71行に「契約に「決定 A2」が二か所残る（gaps N2）」とある。これは当時の contract.md（公開の文書）にあった文を、不足として引いたもので、決定記録を読んだ形跡ではない。契約のその文は N2 で消された
- plan.md、decisions.md、progress.md、reports/: examples/software-factory/docs/adopting-gaps.md の第5行と examples/software-factory/docs/progress.md の第5行の「読まない」「読んでいない」の宣言と、adopting-gaps.md の N2・A3 の「公開の文書を plan.md、decisions.md で検索した」という記述にだけ現れる。内容の引用は無い
- 本体の内部の名前: src/ の最上位の関数、クラス、変数の名前のうち、どの `__all__` にも無い 77 個（`safe_classify`、`state_document`、`derive_seed`、`restore_overlay`、`materialize`、`initial_snapshot`、`request_hash`、`MetricResult`、`StageFailure`、`Evaluation`、`_MARKER`、`_permutation_test` など）を、例の全ファイル（フィクスチャを除く）で語として探した。現れたのは、一般の語か公開の操作の名前と同じつづりのもの（GOAL、UNKNOWN、classify、measure、options、main、sha256）と、Markdown の `\_` の書き方が語の切れ目に見えたもの（`end\_state` の `_state`、`happy\_path` の `_path`、`design\_covers` の `_covers`）だけで、本体の内部の名前を指すものは無い
- examples/software-factory/docs/review-findings.md の L-1〜L-9 の番号は、事前レビューの番号を計画の側がそのまま渡したもの（D-15 の経路）

### 4.3 境界の事例（違反とはしない）

- adopting-gaps.md は、本体について知ったことのうちに「`scripts/check.sh` と本体のテスト（tests/test\_package.py だけ）を実行した時の出力、cProfile の出力（関数の名前と時間）」を挙げている。cProfile の出力には内部の関数の名前が出る。例のコードにそれらの名前は現れない（4.1）ので、読んだ内容が成果物に入った形跡は無い
- コミット a2d1b2a は、本体の変更（N8、N9）と、利用者役の往復 3 の例の変更を一つにしている（ほかのコミットは、本体と例のどちらか一方だけ）。この往復は、履歴の上では「利用者が本体を直していない」を機械的に切り分けられない。差分の中身（本体の側は N8、N9 の実装とテスト、例の側は test\_e2e.py と文書）は、それぞれの役の申告と合う（B-L6）
- scratchpad に残っていた試しのスクリプト（exp/ の 19 個。書いた役は特定できない）も同じ解析にかけた。公開の名前だけを import し、本体の非公開の属性に触れていない

判定: 読取制限が破られた証拠は無い。

## 5. 事前レビューと基準の確認の指摘は直ったか

### 5.1 workflow.yaml の事前レビュー（reports/f4-workflow-review.md）

| 指摘 | 判定 | 証拠 |
| --- | --- | --- |
| H-1 記憶が持ち帰った古い値のまま状態文書に出る | 直った | 全ステージの description に「無ければ空の一覧。訪問のたびに必ず書く」。task\_unclear は記憶 task\_questions と impl\_notes.md の「## 問い」の両方を条件にする（impl\_notes.md は implement の開始時スナップショットに無い）。偽の本体の全変種とシナリオの全訪問が memory\_out を全部書くことをテストで確かめ（test\_every\_body\_writes\_every\_memory\_out\_item）、5 本のシナリオの expect.memory で持ち帰った値が最後に残らないことを確かめる。手引き第2.1・5節にも入った（E-L5 に残りの小さな点） |
| H-2 plan\_tasks の goal を代表が満たせない | 直った | goal が「paths が design.md の構成に収まり、tests が repo/tests/ の下にあり、paths が重ならない」になった。goal の代表（plan\_tasks/ok と design/ok）はこれを満たす |
| M-1 implement で指標が落ちた時の行き先 | 直った | description に自己点検と違反の記録。quality\_violation に「既存のテストを落とす」「design.md の構成から外れている」。impl\_violations が空なら unknown になる意図を README に書いた |
| M-2 unit\_test のテストの不備が unknown に落ちる | 直った | description に自己点検。tests\_insufficient を「unit\_test 自身が直すべき不足か不備」に広げた（境界の変更）。不備の end\_state を足す案は提案として README にある |
| M-3 四つのゲートの不合格が unknown に落ちることが書かれていない | 直った | README に「フェーズゲートの落ち方」の節。ゲートに固有の定性の条件も挙げた（ただし discovery の条件は E-M2） |
| M-4 review の goal が観測できない | 直った | review.json を `{"reviewed": [...], "findings": [...]}` にし、goal を「reviewed が paths と tests をすべて含む」に。四つの代表に reviewed がある |
| M-5 テストへの指摘が unknown に落ちる | 直った（一部は任意の提案を採らず） | changes\_requested を repo/tests/ の修正にも広げ、implement が impl\_notes.md の「## テストへの依頼」に書き写し、unit\_test がそれに応える経路を description に書いた。レビューが「足せば観測できる」とした unit\_test の goal の条件（依頼のすべてに応えるテストがある）は足していない（E-L3） |
| M-6 changes\_requested が指摘無しでも成り立つ | 直った | 「修正を要する指摘が一つ以上あり」と、フェーズ assurance の評価での条件を書き分けた |
| M-7 「REQ-1は」を数えない | 直った | `(?<![A-Za-z0-9_-])REQ-1(?![0-9])` で照合する。日本語が続く id、REQ-10 を数えないことのテストがある。design の「## 対応」と CHANGELOG.md の行の書き方を description に決めた |
| M-8 代表が記述と合わない | 直った | acceptance/unmet は REQ-1（333 円に PCT10 で 299 円）の不合格になり、記述が「要件の記述か受け入れ基準に反する」に広がった。plan\_tasks/unknown は paths が重なるタスクになった。どちらも記述どおりに読んで印のクラスになることを確かめた |
| 低 L-1〜L-9 | L-6 を除き対応 | L-1 は README に注記、L-2 は一部（「## 持ち帰った問い」の節は採らず理由を README に）、L-3・L-4・L-5・L-7・L-8・L-9 は直した。L-6（release が版を上げない）は理由を書いて直さない |

### 5.2 基準の確認（reports/f4-criteria-review.md）

| 指摘 | 判定 | 証拠 |
| --- | --- | --- |
| M1 release の訪問 2 以降の goal の幅が正規近似で合わない | 直った | min 0.90 → 0.88。自分の計算で、n = 65、p = 0.97 の二項分布の下側の裾は 0.90 で 0.332%、0.88 で 0.072%。分母の揺れ（400 回 × 0.16273 の二項分布）を混ぜると 0.367% と 0.059%。注記と、裾の確率を確かめるテスト（`_outside` で 0.1% 以下）がある |
| M2 指標が異常終了を覚える | 直った | 第3.3節 |
| L1 ずらした基準が端を共有する | 直った | analyze の下へのずらしが [0.0, 0.16] |
| L2 release の訪問 1 が 3.2 SE をわずかに下回る | 直った | [0.14, 0.32] |
| L3 markov\_gated にずらした基準が無い | 直った | markov\_gated\_shifted.yaml（3 基準）と、すべて落ちるテスト |
| L4 幅の上限を確かめない | 直った | 設計値の両側に 3 SE 以上 5 SE 以下であることを確かめる |
| L5 visits\_variance の説明 | 一部（本体の側） | docstring と api-reference.md には「一度も訪れない実行は 0 と数える」が足されたが、api.md の `Prediction` の行と adopting.md 第12節は「一回の実行の中での訪問の回数の分散」のまま（B-L2） |

## 6. changelog.md の「未公開」は漏れなく載っているか

`git diff v0.1.0 HEAD -- src docs/api.md docs/adopting.md contract schema`（と pyproject.toml、conftest.py、scripts/）を読み、公開の名前の signature を v0.1.0 と HEAD の両方で実行時に取り出して比べた。

| 変更 | changelog に |
| --- | --- |
| `__all__` に足された名前（contract の `SCHEMA_FILES`、runtime の `Criterion`・`EndState`・`Event`・`Goal`・`Key`・`Phase`・`Rollback`、harness の `RandomGateClassifier`・`conformance_dir`・`conformance_scenarios`・`unmarked`、stages の `Entry`・`EntryDependenceResult`・`Event`・`entries`・`entry_dependence`・`writes_hash`、e2e の `Dist`）。消えた名前は無い | ある |
| signature の変化: `run_scenario(..., user=)`、`run_coverage(..., user=)`、`build_corpus(..., unique_states=)`、`Prediction` の `evaluations`・`visit_outcomes`・`visits_variance` | ある |
| `compare_prediction` が `gate:` の量を返す（互換性に注意） | ある（先頭） |
| `synthesize` の書き直し、トリアージの読み足し | ある |
| シナリオの形式の `{from: パス}` と契約適合テストのシナリオ inputs\_from\_file、パッケージへの同梱 | ある |
| 契約の文書から決定の番号と計画書への参照を除き、契約 第10節に判定の対象を書いた | ある |
| adopting.md の第2.1・4・9・11・12・14・15・15.1・16節の追記 | ある（第11節の三点、第2.1・4・12節、第15.1節、ほかは「利用者が試して知ったこと」にまとめて） |
| examples/\*/tests/fixtures/ を ruff、mypy、pytest の収集から外した（pyproject.toml、conftest.py） | ある |
| ランタイムのコードの変更（runtime/ の差分） | docstring と、決定の番号の削除だけで、振る舞いは変わらない |

判定: 公開 API と公開 API の文書の変更は、実質的に漏れなく載っている。載っていない小さな点が一つある（B-L3）。`RunState` の docstring が「pending と current のほかの属性はランタイムの内部の状態で、読み書きしない」と、`StageContext` が「これ以外の名前は内部のもの」と書くようになった。v0.1.0 では dataclass の属性として見えていたものを内部と宣言しており、互換性に注意する変更に当たりうる。

## 7. オラクル検証の期待値の計算し直し

例の tests/test\_oracle.py は、期待値を数で書かず、テストの中で配分を組み立て直して κ と ECE を計算する。そこで、偽の分類器の配分（ROWS）だけから、テストとフレームワークを使わずに計算し直した。

- コーパス: markov の種 20000〜20059 の 60 回の実行の、状態文書ごとに一つのステージの項目 127 件（作るのにだけ例の `run_set` と `build_corpus` を使い、項目ごとの印と選択肢を書き出した）。真のクラスごとの件数は goal 73、unknown 12、needs\_unclear 7、impl\_defect 6、quality\_violation 6、requirement\_unmet 5、tests\_insufficient 4、changes\_requested 3、design\_flaw・design\_incomplete・notes\_incomplete・requirement\_misread・requirements\_gap 各 2、task\_unclear 1
- 配分: 真のクラスごとに、初めて見た順に ROWS の行を巡る。選んだクラスが項目の選択肢に無ければ答え無し（needs\_unclear の design\_flaw は analyze の選択肢に無い。unknown の goal は、指標が落ちた変種では選択肢に無い）
- 混同行列: goal→goal 55、goal→unknown 18、unknown→unknown 6、unknown→goal 2、unknown→答え無し 4、needs\_unclear→needs\_unclear 4、needs\_unclear→答え無し 3、ほかの end\_state は三件に二件が正解、一件が unknown
- κ: p\_o = 93/127 = 0.732283、p\_e = 0.289417（答え無しは分類器の側だけのカテゴリ）、κ = 0.623244。scikit-learn の `cohen_kappa_score` も 0.623244
- ECE（答えた 120 項目、等幅 10 区間、左閉じで最後の区間だけ 1 を含む）: 区間 5（2 件、正解率 0、平均確信度 0.57）、6（25 件、0、0.6412）、7（31 件、1、0.7510）、8（39 件、1、0.8554）、9（23 件、1、0.9265）。ECE = 0.2685。右閉じにしても同じ（境目ちょうどの確信度が無い）。答えた割合 0.944882、答え無し 7
- 再実行の一致率: FlakyClassifier（every 4）は初めて見た順の 0、4、8、… 番目の 32 件を揺らすので、95/127 = 0.748031
- 印を読む分類器（確信度 0.9）: 全問正解で κ 1、ECE \|1 − 0.9\| = 0.1。トリアージのテスト（確信度 0.6）: ECE 0.4
- フレームワークの `oracle_report` を同じコーパスにかけた値（κ 0.623244、ECE 0.2685、答え無し 7、一致率 0.748031）、作業ログの値（κ 0.623、ECE 0.269、答え無し 7、0.748）と一致した
- ただし、揺れる分類器のテストは `approx(0.75, abs=0.05)` で、0.70〜0.80 なら通る。値はちょうど 95/127 と決まるので、そう書けば数え違いも捕まえられる（E-L4）

## 8. 追加の実験

### 8.1 分布テストの観測値（既定の種）

- markov.yaml（400 回、種 20000）: intake 訪問 1 の unknown 0.015（6/400）、analyze の needs\_unclear 0.246（97/394）、implement 訪問 1 の goal 0.699（244/349）、訪問 2 以降 0.928（323/348）、unit\_test の impl\_defect 0.222（74/334）、tests\_insufficient 0.213（71/334）、acceptance の requirement\_unmet 0.102（33/325）、review の changes\_requested 0.182（57/314）、release 訪問 1 の notes\_incomplete 0.215（64/298）、訪問 2 以降の goal 0.969（62/64）、完了 0.715（286/400）、implement の訪問の回数の平均 1.742。12 基準すべて通る
- markov\_shifted.yaml の 14 基準は、同じ実行ですべて落ちる
- markov\_gated.yaml（400 回、種 50000）: ゲートの訪問 1 の changes\_requested 0.211（45/213）、訪問 2 以降 0.156（17/109）、完了 0.620、訪問の回数の平均 1.995。4 基準すべて通り、markov\_gated\_shifted.yaml の 3 基準はすべて落ちる
- 基準そのもの（中心、E[n]、SE）は基準の確認（承認済み）で確かめられているので、ここでは改めた二つの幅（第5.2節）だけを計算し直した

### 8.2 変異（例のテストが欠陥を捕まえるか）

複製の上で、例のコードに変異を一つずつ入れ、関係するテストを走らせ、元に戻した。

| 変異 | 結果 | 落としたテスト |
| --- | --- | --- |
| divergent の二つ目の goal の実装を ok\_b に戻す（粗いクラスを仕込まない） | 落ちた | test\_divergent\_body\_is\_detected |
| release が carry を無視する | 落ちた | test\_correct\_expectations\_pass |
| build\_passes が常に真 | 落ちた | test\_variant\_fails\_exactly\_the\_designed\_metrics[implement-broken] |
| out\_of\_scope\_changes が常に 0 | 落ちた | 同上 [implement-scope] |
| lint\_errors が常に 0 | 落ちた | 同上 [implement-lint] |
| line\_coverage が常に 100 | 落ちた | 同上 [unit\_test-thin] |
| ゲートを揺らさない（gates を無視） | 落ちた | test\_gated\_expectations\_pass |
| intake が持ち帰った問いを尋ねない | 落ちた | test\_intake\_writes\_the\_personas\_answers |
| ペルソナをいつも一つにする | 落ちた | test\_persona\_representatives\_do\_not\_change\_downstream |
| 確率的な本体が空の記憶を書かない（`if value:` のときだけ書く） | **生き残った** | なし（test\_stochastic.py、test\_e2e.py、test\_independence.py の 33 件が通る。E-L5） |

最後の変異が生き残るのは、本体が memory\_out を毎回書くことを、本体の振る舞いではなく設計値の表で確かめているため。印を読む分類器は記憶を読まないので、分布にも出ない。事前レビューの H-1 と同じ種類の退行を、確率的な本体の側では捕まえられない。

### 8.3 種による揺れ

種の基点を変えて、400 回ずつの実行の集まりで独立性検証と `entry_dependence` をかけた。

- markov（20 通り）: 独立性検証は 20/20 で violated 無し（判定できた状態は 6〜7 個、implement の goal の p 値は 0.04〜0.90）。`entry_dependence` は 19/20 で violated 無し。基点 1001000 では plan\_tasks の訪問 2 以降が p = 0.0095 で violated になった（判定できる検定は毎回 5 個で、alpha 0.01 の偶然の範囲）
- divergent（20 通り）: 20/20 で `stage:implement=goal` の訪問の区分 1 → 1 が violated（どれも p = 0.0005）。区分 2 でも 19/20 で violated。仕込んだ所の外では、基点 2012000 で `stage:unit_test=goal` が p = 0.006 で一度 violated になった（偶然の範囲）。`entry_dependence` は 20/20 で violated 無し
- ゲートを揺らす実行（12 通り）: 独立性検証は 12/12 で violated 無し。`entry_dependence` は 11/12 で violated 無し。基点 3010000 では analyze の訪問 2 以降が p = 0.004 で violated になった（偶然の範囲）
- 例のテストは、markov とゲートを揺らす実行の全状態に「violated が一つも無い」を求める。補正の無い 5〜7 個の検定なので、種や回数（`HTF_RUNS` で増やせる）を変えると、正しい本体でも数 % の確率で落ちる（E-L6）

## 9. 指摘

### 本体の側

高と中は無い。

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| B-L1 | 低 | docs/adopting.md 第15.1節 | 手順が、ゲートの項目を含めるかを書いていない。第15節は「印をラベルの代わりにするならステージの項目に絞る」と書くので、利用者はステージの項目だけで試し、ゲートの代表の食い違い（E-M2）を見落とした | adopting-gaps.md の N12 の試し（「ステージの 315 項目」）。`MarkerClassifier` はゲートにいつも goal を答えるので、ゲートの項目も同じ手順で比べられる | 第15.1節に「ゲートの項目も含める（印を読む分類器はゲートに goal を答えるので、人のラベルが goal でなければ、ゲートの goal の記述と代表が食い違う）」と、上流の違い（ペルソナなど）でも項目を分けることを書く |
| B-L2 | 低 | docs/api.md の `Prediction` の行、docs/adopting.md 第12節 | 「一回の実行の中での訪問の回数の分散」のままで、基準の確認の L5（訪れなかった実行を 0 として含む、実行の間の分散）が docstring にしか入っていない。D-16 は L5 を解消としている | 第5.2節 | 二つの文書に「実行ごとの訪問の回数（訪れなかった実行は 0）の、実行の間での分散」と書く |
| B-L3 | 低 | docs/changelog.md の「未公開」 | `RunState` の pending と current のほかの属性、`StageContext` の宣言の外の名前を内部と宣言したことが、互換性に注意する変更に載っていない | 第6節 | 「互換性に注意する変更」に一行足す |
| B-L4 | 低 | docs/decisions.md D-11 の D4 の行 | 「解消しない（判定は正しい）…分類器に種を渡す（契約のインターフェースの変更）必要がある」のままで、D-12 の N5 がそれを誤りとした。この文書の決まり（覆されたものは置換とする）に合わない | D-11、D-12 | D-11 の D4 の行に「D-12 の N5 で置換（RandomGateClassifier で解消）」と書く |
| B-L5 | 低 | docs/api-reference.md の `SCHEMA_FILES` | 値の表示が `'triage_decision.schema.jso …` で切れる（往復 2 で利用者が気づいたまま） | api-reference.md 第124行 | 生成の切り詰めを、組の値では外すか、長さの上限を上げる |
| B-L6 | 低 | 作業の手順（コミット a2d1b2a） | 本体の変更と利用者役の例の変更を一つのコミットにしたので、履歴の上で「利用者が本体を直していない」を切り分けられない往復がある | 第4.3節 | 本体の変更と例の変更は別のコミットにする（F5 で software factory を保守する時も） |

### 例の側

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| E-M1 | 中 | tests/fixtures/acceptance/misread/verification.md、tests/fixtures/plan\_tasks/incomplete/tasks.yaml、tests/fixtures/analyze/ok/requirements.md と software\_factory/personas.py | README の「記述と代表の整合（試しのラベル）」の三つの食い違いが直されていない。自分でも確かめた: (1) misread の「依頼と intake.md はレジの画面で入力する前提」は precise\_pm の回答にしか無く、feature\_request.md にも無い。(2) design\_incomplete の「構成に REQ-3 と REQ-4 を受け持つ箇所が無い」は、plan\_tasks がいつも読む design/ok の design.md（REQ-3 は parse\_code、REQ-4 は Cart.total）と矛盾する。(3) analyze の goal の代表の「nn は 1〜50」は、vague\_founder の「上限はまだ決めていない」と矛盾する。加えて、REQ-2 の「支払額は 0 円を下回らない」は、最初の訪問ではどのペルソナの回答にも根拠が無い（その点を尋ねる問い FLOOR は needs\_unclear の変種だけが持ち帰る） | 記述どおりに読む分類器では、(1) は vague\_founder と terse\_engineer の実行で unknown、(2) はいつも unknown、(3) は vague\_founder の実行で unknown になる。どれも、分類器の検証のコーパスのラベルとも食い違う（手引き第15.1節）。クラスの選び方は種だけで決まるので、成果物の中身を直しても分布テストの数値は変わらない（往復 6 で M-8 を直した時と同じ） | (1) 食い違いを依頼から言える点にする（たとえば「10% 引き」の書き方の揺れを要件が扱わない）か、全ペルソナの回答に前提を入れる。(2) design/ok の design.md でも本当に割り当てられない点を代表にする。(3) analyze の goal の成果物をペルソナごとに用意する（種でクラスを選んだ後に、intake.md の回答に合う成果物を写す）か、vague\_founder の回答を値の決まったものにする。REQ-2 の下限は、回答に根拠を持たせるか、goal の代表から外す。分類体系は変えない |
| E-M2 | 中 | workflow.yaml の discovery の goal の qualitative と、README の「フェーズゲートの落ち方」 | 「intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映されている」を、goal の代表（analyze/ok の requirements.md）は、どのペルソナでも字義どおりには満たさない。requirements.md は利用者に一言も触れない（precise\_pm の「ネットショップの購入者。レジの画面でコードを入力する」、terse\_engineer の「購入者」が反映されない）。vague\_founder では「上限はまだ決めていない」も反映されず、要件の「nn は 1〜50」と食い違う | ゲートの状態文書は intake.md と requirements.md を含む（契約 2.4）。ゲートの選択肢は goal、needs\_unclear、unknown で、needs\_unclear は goal の時に空の intake\_questions を証拠にするので選ばれない。記述どおりに読む分類器では、主経路が毎回このゲートで unknown（escalate）になる。事前レビューが高とした H-2 と同じ種類の欠陥（主経路が unknown）で、ゲートにある。ここで中とするのは、「利用者」の回答の「反映」は、要件の前提として緩く読む余地があり、緩く読めば precise\_pm と terse\_engineer では満たしうるため（vague\_founder では緩く読んでも満たさない）。第15.1節の試しがステージの項目だけだったので見つかっていない | 代表の側を直す: requirements.md に利用者（と入力の場所）を書く節を設け、goal の代表に書く。これは成果物の直しで、人間の承認は要らない。記述の側を直す（discovery の goal から「利用者」を外す、または要件にしない回答の置き場を決める）のは記述の改訂なので、人間の承認が要る。vague\_founder の食い違いは E-M1 の (3) と一緒に直す。あわせて、ゲートの項目も第15.1節の手順で人がラベルを付ける |
| E-L1 | 低 | tests/stochastic.yaml の markov、tests/fixtures/acceptance/ok/verification.md | markov では goal の実装が二つとも REQ-1 の切り捨てを誤る（333 円に PCT10 で 299 円）ので、完了した実行はいつも REQ-1 の記述に反するコードをリリースし、acceptance/ok は REQ-1 を合格とする。記述（表がすべて合格）には合っているが、assurance のゲートの「repo/ をこのままリリースしてよい」は、repo/ を読む分類器には満たさないと読まれうる | acceptance/unmet の内容と families の注記 | ゲートの判定の範囲が「verification.md と review.json に基づく」ことを記述に書くか、README に意図（玩具の主経路は既知の欠陥を持つ）として書く |
| E-L2 | 低 | tests/test\_scenarios.py の docstring | 「フェーズ境界越えは五通り」とあるが、定義の上の越境は六本で、テストが確かめるのは五本と運用者による越境。acceptance→analyze（requirement\_misread）は決定論のシナリオでは通らない（E2E のカバレッジで踏む） | 第1節 | docstring を直し、requirement\_misread で analyze に戻るシナリオを一本足す（三つのフェーズを越える、いちばん費用の大きい辺） |
| E-L3 | 低 | workflow.yaml の unit\_test の goal | 「impl\_notes.md の『## テストへの依頼』のすべてに応えるテストがある」が goal に無い。依頼を無視したテストでも goal に分類される | 事前レビューの M-5 の提案 | goal に足す（unit\_test は impl\_notes.md を読むので観測できる） |
| E-L4 | 低 | tests/test\_oracle.py の test\_flaky\_classifier\_disagrees\_on\_reruns | 一致率を `approx(0.75, abs=0.05)` で確かめる。値は 95/127 に決まる | 第7節 | `1 - ceil(len(corpus) / 4) / len(corpus)` と一致することを確かめる |
| E-L5 | 低 | software\_factory/stages/probabilistic.py の `StochasticBody` | 本体が memory\_out を毎回書くことを、本体の振る舞いではなく設計値の表（tests/stochastic.yaml）でだけ確かめている。空の記憶を書かない変異が生き残る | 第8.2節 | 分布テストの実行の集まりで、各評価の終了時スナップショットの記憶が、そのステージの memory\_out をすべてその訪問の値で持つことを確かめる（たとえば、変種の表の値と一致する） |
| E-L6 | 低 | tests/test\_independence.py と tests/test\_e2e.py | markov とゲートを揺らす実行の全状態に violated が無いことを、補正の無い alpha 0.01 の検定 5〜7 個で求める。既定の種では通るが、種か回数を変えると正しい本体でも数 % で落ちる（`entry_dependence` は markov の 20 通りの基点で 1 回、ゲートを揺らす実行の 12 通りで 1 回 violated） | 第8.3節 | 確かめる状態を絞る（仕込んだ所と、入り方の多い implement だけ）か、多重性を見込んだ alpha にする。「HTF\_RUNS を増やすと偶然に落ちうる」ことを注記する |

## 10. 人間のレビューに渡すべき事項

README と作業ログに書かれた未決の点と、この判定で見つけた点。

1. 記述と代表の食い違い（E-M1 の三つと REQ-2 の下限、E-M2 の discovery のゲート）。直すか、直さないなら理由を記録する。利用者役の κ 0.915 はエージェントの試しのラベルで、人手のラベルではない。人のレビューでは、ゲートの項目も含めて第15.1節の手順をやり直す
2. 分類体系の変更の提案: unit\_test のテストの不備を、tests\_insufficient を広げて含めた。別案（tests\_defective を足して unit\_test 自身に戻す）を採るか
3. 意図として書かれた選択: implement の指標が落ちても impl\_violations が空なら unknown（人に戻す）。discovery、architecture、construction、delivery のゲートの不合格は unknown。release はパッケージの版を上げない（L-6 を直さない）。analyze の requirement\_count の min 3 はこの依頼に合わせた値。acceptance の tests\_pass を残す。intake の「## 持ち帰った問い」は採らない（L-2 の一部）
4. markov.yaml の実行のゲートはいつも goal で、ゲートの分布は markov\_gated.yaml の実行の集まりだけで確かめる
5. markov の主経路は、REQ-1 に反するコードをリリースする（E-L1）。玩具の意図としてよいか
6. 契約適合テストの読み方: plan.md 第5.8節は「ハーネスが契約を満たしているかはこのテストでのみ判定する」と書くが、D-11 の B7 以後の契約 第10節と手引き第9節は「判定の対象はランタイムの実装で、参照ランタイムを使うハーネスは通す必要が無い。ハーネスの義務はランタイムが実行のたびに検査する」とする。例は両方の読み方で条件を満たす（同梱のシナリオを通し、800 回の実行に違反が無い）が、計画書の文と決定の食い違いは人間が確かめる
7. 往復 6 の直しは、本体の実装を読んだ検証役の指摘を、計画の側が公開の文書の語で渡したもの（D-15、docs/review-findings.md）に基づく。F4 の「adopting.md だけで作れる」の判断では、この経緯を踏まえる（そこで分かった一般の不足は手引きに入っている）
8. carry の有無をマルコフ合成のモデルに入れないこと（D2）は、F5 と決定 #6 で扱う

## 11. 実行したコマンドと出力の要旨

- `bash scripts/check.sh`（複製の上で）: ruff check、ruff format、mypy（src と tests で 42 ファイル、software-factory で 19、toy-minimal で 12）、pytest 634 件が通過（145.7 秒）、runtime の行カバレッジ 90% 以上、wheel にスキーマと契約適合テスト一式が入っている。全体で 2 分 28 秒
- `pytest --collect-only examples/software-factory`: 173 件（本体と toy-minimal で 461 件）
- 整合性検査のコマンド（第1節）: 0 error(s)、0 warning(s)
- import と属性の AST 解析、語の検索（第4節）。v0.1.0 と HEAD の `__all__` と signature の比較（第6節）
- markov（種 20000）、ゲートを揺らす実行（種 50000）、divergent（種 30000）、推定用（種 40000）の 400 回ずつを実行し、四つの expectations、独立性検証、三つのモデルの `compare_prediction`、`entry_dependence` をかけた（第1・8節）
- オラクルのコーパス（60 回、127 項目）を書き出し、別の環境で κ と ECE を計算した（第7節）
- 二項分布の裾の確率（第5.2節）
- 変異 10 個（第8.2節。9 個が落ち、1 個が生き残った）。種の基点を変えた独立性検証と `entry_dependence`（markov 20 通り、divergent 20 通り、ゲートを揺らす実行 12 通り）

## 触ったファイル

- 書いた: reports/f4-completion.md（このファイル）だけ。元の作業ツリーでは、ほかのファイルを変えておらず、テストも実験も走らせていない
- 副作用: scratchpad にリポジトリの複製を二つ作った（repo/ と f4c/mut/）。実験のスクリプトと出力は scratchpad の f4c/ と scripts/ にある。参照値の環境は scratchpad に前からあった refenv/ を使い、`uv pip install numpy scipy scikit-learn statsmodels pyyaml` を実行した（入れる前に何が入っていたかは確かめていない）
- 注意: この scratchpad は、前のセッション（ほかの役）と共有されていた（check\_r\*.log、exp/、refenv/、backup\*/ などがあった）。最初に `rm -rf repo && git clone … repo` を実行し、`check.log` に書いたので、前からあった scratchpad の repo/ と check.log を消したか上書きした可能性がある（実行の前に在ったかどうかは確かめていない）。ほかの既存のファイルには触れていない
