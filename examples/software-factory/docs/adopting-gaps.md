# adopting.md の不足の記録（software-factory）

software-factory を作る途中で、docs/adopting.md（と、それが指す公開 API の文書、examples/toy-minimal/）だけでは判断できなかったこと、足りなかったこと、回避したくなったことの記録。最初の版（30 項目、A1〜F2）を受けてフレームワークの側が直したので、往復 1 として各項目を利用者の立場で確かめ直した。

読んだのは adopting.md、api.md、api-reference.md、examples/toy-minimal/、schema/workflow.schema.json、contract/ の文書と形式（contract.md、README.md、conformance/ の下のすべて、formats/ と trace と snapshot の schema）だけ。フレームワーク本体の実装（src/、tests/、scripts/、pyproject.toml、conftest.py の中身を含む）、plan.md、progress.md、decisions.md、reports/ は読んでいない。本体について知ったことは、公開の名前の signature と docstring、`scripts/check.sh` と本体のテスト（tests/test\_package.py だけ）を実行した時の出力、cProfile の出力（関数の名前と時間）からだけ。本体は直していない。回避策はこの例の中にだけ置いた。

## 未解消

### N1. 公開の名前の signature に出てくる型の一部が、どこにも書かれていない

api-reference.md の signature が、api.md に無い名前を使う: `Dist`（MarkovModel）、`Key`（Recorder.call）、`Event`（RunResult、RunRecord）、`Goal`、`EndState`、`Phase`、`Rollback`（Stage、Workflow.phase）、`writes_hash`（record\_run の representative の既定）、`SCHEMA_FILES`（load\_contract\_schema）。

- 困ったところ: この例は `Stage.end_states` の各項目の `.id` を使う（tests/test\_oracle.py）が、`EndState` の属性は書かれていない。`load_contract_schema` が受け取る名前（`triage_item.schema.json` など）は試して分かった。MarkovModel に渡す分布は `dict[str, float]` で動いたが、`Dist` の定義は見ていない
- 欲しいもの: これらの型の属性か定義を api-reference.md に。`load_contract_schema` には受け取る名前の一覧を

### N2. 契約に、読めない文書の決定の番号が二つ残っている（A3 の残り）

contract/contract.md 第1節の「辺」の定義の末尾「（決定 A2）」と、contract/conformance/scenarios/self\_rollback.yaml の description の「（A2）」。ほかの参照（plan.md、decisions.md、決定 #n）は契約、形式、docstring から消えている。戻り先を自分自身にできる理由は adopting.md 第2.3節（carry を持ってやり直せる）から読み取れるので、判断には困らない。

### N3. 例と本体の語の重なりの報告が、pytest の既定の出力で切れる（B2 の残り）

重なった語は一度にすべて検査の値に入るようになった（下の B2）。ただし pytest の既定の出力は長い一覧を `...` で切るので、重なりが多いと一部の語が見えない（`-vv` を付ければ全部見える）。check.sh の出力で同じことが起きるかは、check.sh を読んでいないので分からない。試した時は語が二つで、どちらも見えた。

### N4. synthesize は訪問の回数の分散を出さない（D3 の残り）

visit や from\_visit で絞った基準の E[n] は `synthesize` で厳密に出るようになった（下の D3）。一方、`mean_visits` の基準の幅には、一回の実行の中での訪問の回数の標準偏差が要るが、`Prediction` は期待値（`mean_visits`）しか持たない。

- どうしたか: 設計値とワークフロー定義の辺を辿る標本（software\_factory/design.py の simulate）を、この標準偏差のためだけに残した。標本の最後の状態と訪問の回数の平均が synthesize の厳密な値と一致することを tests/test\_e2e.py で確かめる
- 回避したいこと: 遷移規則を例の中で書き直している（ハーネスの実行には使わない）。`Prediction` に訪問の回数の二次の積率（か分散）があれば要らない

### N5. 第14節の「ゲートを落とすには…しかなく」は強すぎる（D4 の説明の残り）

第14節は、確率的な実行でゲートを揺らすには最終ステージの goal の成果物にゲートの印を入れるしかないと書く。試したところ、成果物ではなく実行ごとの乱数でゲートの答えを決める偽の分類器でも揺らせ、その時は独立性検証が違反を出さず、ゲートの分布を持つマルコフ合成が実測と合った。

- 試したこと（スクラッチで。この例には入れていない）: 実行の種から作った `random.Random` を持つ偽の分類器を、ペルソナと同じく実行ごとに組み立てて束縛した。assurance のゲートで changes\_requested が選択肢にあれば確率 0.2 でそれを返し、ほかは `MarkerClassifier` に任せる。markov の本体で 400 回（種 20000）を実測、400 回（種 40000）を推定に使い、ゲートの評価 370 件のうち changes\_requested は 86 件。推定したモデルの予測も、設計値のモデルに assurance のゲートの分布 {goal: 0.8, changes\_requested: 0.2} を足した予測も、41 の量すべてで実測と一致した（k = 4）。独立性検証の violated は無い
- 欲しいもの: 第14節にこの形（実行ごとに組み立てる、成果物によらない乱数の偽の分類器）を書くか、フレームワークにその偽の分類器を置く。この例に入れなかったのは、実行の集まりを二つ足すと例のテストの時間が目安（N7）からさらに離れるため

### N6. carry で振る舞いが変わる実際の本体で、マルコフ合成をどう扱うか（D2 の説明の残り）

第14節の説明で、偽の本体で確かめる時の置き方は分かる（下の「直さないと言われたもの」）。実際の LLM の本体は carry を受ければたいてい振る舞いを変え、この例の implement のように carry を持つ辺が四本入るステージもある。そういうハーネスで、合成の予測が合わない時に、carry によるものかほかの非マルコフ性によるものかをどう見分けるか、合成をどのステージまで信じてよいかは書かれていない。

### N7. この例のテストが、第11節の時間の目安（一つの例で一分以内）を超える

第11節に目安が書かれ、`synthesize` も速くなった（下の B6）。それでもこの例のテストはカバレッジの計測の下で約 82 秒かかる（check.sh 全体は約 1 分 46 秒）。大半は 400 回の実行の集まり三つ（分布テスト、独立性検証の divergent、マルコフ合成の推定。一つ約 16〜18 秒）。

- どうしたか: 指標の tasks.yaml の読み込みを内容ごとに覚えた（計測の下で、400 回の実行の集まり一つが約 20 秒から約 16〜18 秒に。計測なしでは約 7.8 秒）。cProfile（覚える前、計測なしの 100 回）では、ランタイムのスナップショットの作成（作業領域の走査と正規形の JSON）が約三分の一、残りは本体のフィクスチャの写し、指標、遷移の処理に分かれる。回数を減らさずに大きく縮める手は、例の側には見つからなかった
- 判断できないこと: 回数を減らすと基準の幅（回数から決めた）と独立性検証の検出力が変わるので、減らしていない。目安を超えてよいのか、三つ目（推定）の集まりを分布テストの集まりと分け合うべきか（推定と実測が同じ実行になると比べる意味が薄れる）は決められない

## 解消済み（往復 1）

### A. 文書と API の参照

- **A1 api.md に引数と属性が無い**: 解消。api-reference.md に、前に挙げた名前（Question、record\_run、ConfusionClassifier、FlakyClassifier、enqueue、decide、plan\_coverage、MarkovModel、OracleReport など）の signature、属性、docstring があることを読んで確かめた。StageContext の項は使ってよい属性だけを挙げ、adopting.md 第5節が `dir(context)` で見えるほかの名前を使わないよう書く。signature の中の一部の型が無いことは N1
- **A2 StageContext の属性の一覧の食い違い**: 解消。adopting.md 第5節と api-reference.md の StageContext に `stage_id` と `visit` がある
- **A3 契約が読めない文書を根拠として指す**: 一部。contract/、schema/workflow.schema.json、api.md、api-reference.md を plan.md、decisions.md、「決定 #」で検索し、残りは二か所だけ（N2）
- **A4 記憶がまだ無い時の read\_memory**: 解消。adopting.md 第5節と StageContext.read\_memory の docstring に「値がまだ無ければ None」
- **A5 保留中の質問の形**: 解消。adopting.md 第7節の手順 1 と RunState の docstring に `{"kind": "user", "question": {"text": ..., "choices": [...]}}`
- **A6 置き場から状態文書を読む方法**: 解消。adopting.md 第7節（`store.get(snapshot.files[パス])`）、第15節（evaluation の `classification.state`）、第16節（`store.get(item.state)`）と BlobStore.get の docstring
- **A7 OracleReport.by\_target の鍵**: 解消。adopting.md 第15節と OracleReport の docstring に `stage:<id>` か `phase:<id>`

### B. リポジトリの中に例を置くこと

- **B1 壊れたコードのフィクスチャとリポジトリ全体の検査**: 解消。adopting.md 第11節に「tests/fixtures/ の下は ruff、mypy、pytest の収集から外れる」。試した: tests/fixtures/.code/ を普通のディレクトリ（tests/fixtures/implement/、unit\_test/、inputs/repo/）に移し、tests/fixtures/ruff.toml と tests/conftest.py の collect\_ignore を外した。check.sh が通る（ruff check、ruff format、mypy strict がこの例で 19 ファイル（前と同じ）、pytest 602 件）。意図的に lint に反するコード、構文の誤り、失敗するテスト、同じ名前のモジュールの 8 変種がそのまま置ける
- **B2 例の id が本体の語と重なってはいけない**: 解消（報告の見え方は N3）。adopting.md 第11節に制約と除外が書かれた。試した: workflow.yaml を一時的に前の名前（`verify`、`request.md`、`open_questions`）に戻して tests/test\_package.py を実行すると、全部通った。記憶の名前を本体にありそうな語（`checkpoint` と `runner`）に一時的に変えると、一回の失敗で両方の語が一覧に出た。戻した名前は採らなかった（`acceptance`、`feature_request.md`、`intake_questions` でも自然で、`verify` に戻すとステージの種が変わり、全テストの数値を取り直すことになるため）
- **B3 指標の args の型**: 解消。adopting.md 第4節と MetricRegistry.measure の docstring に「読み取り専用の Mapping。必要なら dict(args)」
- **B4 実在のツールに裏づけられた指標の費用**: 解消。adopting.md 第4節と第11節、MetricRegistry.measure の docstring に「読むファイルの内容のハッシュと args を鍵に覚えてよい」。この例の覚え方（指標名、引数、内容のハッシュ）がそのまま当てはまる。recorder に任せられるかは書かれていないが、覚えてよいと分かったので要らない
- **B5 変更パスの範囲の指標と writes**: 解消。adopting.md 第4節に「writes より狭い範囲と比べる」と理由
- **B6 例のテストの時間**: 解消（この例が目安を超えることは N7）。adopting.md 第11節に、一つの例で一分以内の目安、実行の集まりを session の fixture で共有すること、synthesize の時間が到達しうる状態の数に比例することが書かれた。試した: 9 ステージ 12 辺の synthesize は約 8 秒から約 0.8 秒に（カバレッジの計測の下では約 17 秒から約 2.5 秒に）
- **B7 契約適合テストの意味**: 解消。契約第10節、contract/conformance/README.md、adopting.md 第9節に「判定の対象はランタイムの実装。参照ランタイムを使うハーネスは自分で通す必要は無く、ハーネスの側が守ることはランタイムが実行のたびに検査する」。シナリオ一式は `conformance_dir()` と `conformance_scenarios()` で場所が分かる（25 件）。tests/test\_conformance.py はリポジトリのパスをやめて `conformance_scenarios()` を読み、必須ではない版の確認として残した。形式の schema も `load_contract_schema` で読むようにした（tests/test\_oracle.py、test\_triage.py）

### C. ワークフロー定義

- **C1 ゲートの不合格を end\_state で戻すことと「goal に優先」の衝突**: 解消。adopting.md 第2.4節の注意に、goal の時に空になる記憶を証拠にしたクラスにはフェーズ全体の条件を書かず、goal の時にも中身を持てる記憶のクラスに限るとある。この例の書き方（review の changes\_requested だけ）と同じ
- **C2 goal 到達扱いと後のゲートの実在の指標**: 解消。adopting.md 第7節の末尾と ContinueAsGoal の docstring に「後のゲートの指標は免れない。テストでは後の指標を満たす成果物の状態で使う」

### D. 確率的な本体と分布テスト

- **D1 ユーザーシミュレータに実行の種が届かない**: 解消。adopting.md 第12節に、`run_many` に渡す関数の中で選んだシミュレータのランタイムを実行ごとに組み立て、置き場と作業ディレクトリは共有する形と、回答を保留するシミュレータを束縛すると実行が中断のまま記録される注意がある（record\_run の docstring にも）。この例の run\_set と同じ形
- **D3 visit で絞った基準の分母の期待値**: 解消（分散の残りは N4）。`synthesize(design_model, workflow).evaluations[("stage", 対象, 区分)]` と `visit_outcomes` で、markov.yaml の 10 の outcome\_rate の基準の E[n] と設計値の割合が出ることを試した。前に標本で出した値との差は 400 回の実行で最大 0.7（例: analyze の訪問 1 は 388.1 → 388.0、implement の訪問 2 以降は 320.9 → 320.3）で、基準の値は変わらない。markov.yaml の注記を厳密な値に直し、各基準が設計値の両側に標準誤差の 3 倍以上あることを synthesize の値から確かめるテスト（tests/test\_stochastic.py の test\_correct\_expectations\_follow\_the\_design）を足した。design.simulate から訪問ごとの評価の数え上げを除いた
- **D5 実在の指標と偽の本体のクラスの整合**: 解消。adopting.md 第12節の「偽の本体と実在の指標を組み合わせる時」。この例の設計値の metrics\_fail と tests/test\_metrics.py と同じ形
- **D6 種の分布を疑った**: 解消。adopting.md 第5節と StageContext.seed の docstring に「`random.Random(seed)` にそのまま渡してよい。訪問ごとに独立な一様の種とみなせる」

### E. 分類器の検証とトリアージ

- **E1 コーパスの重複と FlakyClassifier**: 解消。`build_corpus(..., unique_states=True)` と、adopting.md 第15節、ConfusionClassifier と FlakyClassifier の docstring の注意。tests/test\_oracle.py の手書きの重複除きをこれに替えた（ステージの項目に絞る）。markov の最初の 60 回で、手書きの重複除きと同じ 127 項目、同じ順になることを試した。κ、ECE、再実行の一致率のテストはそのまま通る
- **E2 ゲートの項目のラベル**: 解消。adopting.md 第15節に、MarkerClassifier の印はステージのクラスでゲートの状態文書には無いので、ステージの項目に絞るかゲートには人手でラベルを付けるとある
- **E3 トリアージの関数の費用**: 解消。試した: 確信度 0.6 の MarkerClassifier と review\_below 0.7 で 24 回の実行の全評価（361 項目）を待ち行列に足すのに約 0.25 秒、全項目に判定を付けるのに約 0.17 秒（前は約 360 項目で約 18 秒）。tests/test\_triage.py の Hesitant（review と assurance のゲートだけ確信度を下げる偽の分類器）を外し、全評価を待ち行列に入れる形にした。テストは約 4 秒
- **E4 トリアージの項目とコーパスの項目の id**: 解消。adopting.md 第16節と CorpusItem、TriageItem の docstring に、同じ形 `<実行の id>-<評価の seq>` で突き合わせられるとある

### F. 決定論テストと E2E

- **F1 シナリオの inputs にディレクトリやフィクスチャを指せない**: 解消。contract/conformance/README.md の「ファイルの内容」と adopting.md 第8節に `{from: パス}`（ディレクトリは鍵と from を / で終える）。software\_factory/scenarios.py が inputs と expect.starts の files をフィクスチャへの参照（`repo/: {from: ../fixtures/inputs/repo/}` など）で書くようにした。14 のシナリオの YAML は 2841 行から 1635 行になり、load\_scenario で読んだ inputs、visits、gates、台本、期待が前と同じ（フィクスチャのパスの `.code/` を除いて）ことを全項目で比べた。フィクスチャの中身を変えても作り直さなくてよくなった。遷移の列を手で並べる道具としては残した。`plan_coverage` の inputs は文字列だけを取るが、inputs() を読めば足りる
- **F2 シナリオと E2E にユーザーシミュレータを束縛できない**: 解消。`run_scenario(..., user=...)` と `run_coverage(..., user=...)`。三つのペルソナを、持ち帰った問いを尋ねるシナリオ（needs\_unclear\_asks\_again）と、最初の質問で回答を保留するシナリオ（happy\_path\_user\_suspend。再開の回答は台本の user から取る）に束縛し、どちらも期待どおりに通ることをテストにした。E2E のカバレッジでは intake の goal の台本に三つの質問を足し、ペルソナに答えさせて全 (ステージ, クラス) を踏む

## 直さないと言われたもの

### D2. carry を受けたかで分布が変わる本体と、(ステージ, 訪問) のマルコフモデル

adopting.md 第14節に「モデルの区分は (ステージ, 訪問の区分) だけで、carry を受けたかは入らない。そのステージに戻ってくる辺が carry を持つ一本だけでない限り仮定を壊し、予測が合わない。偽の本体で確かめる時は、戻ってくる辺が一本のステージに置く」とある。

判断: この例にとっては十分。前に自分で選んだ置き方（release に戻る辺は自分自身への一本だけで、訪問 2 以降と carry を受けたことが一致する）が、そのまま文書の勧めになっている。制限として明示されたので、合成が合わない時の第一の疑いにできる。実際のハーネスでの扱いが足りないことは N6 に書いた。

### D4. MarkerClassifier の下でのゲートの分布

adopting.md 第14節に「ゲートを落とすには最終ステージの goal の成果物の一部にゲートの印を入れるしかなく、その成果物は goal の中で下流が違う代表になり、独立性検証は violated と判定する（正しい判定）。ゲートからの戻りはシナリオで確かめ、確率的な実行のゲートはいつも goal にする」とある。

判断: MarkerClassifier を使う限りの説明として正しく、この例のやり方（確率的な実行のゲートは goal、ゲートからの戻りはシナリオの assurance\_gate\_rolls\_back）と一致する。ただし「しかない」は強すぎる。実行ごとの乱数でゲートを揺らす偽の分類器で、ゲートの分布を持つマルコフ合成を偽の本体のまま確かめられた（N5）。
