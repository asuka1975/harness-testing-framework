# software-factory

harness-testing-framework の利用者として、docs/adopting.md だけを手引きに作ったワークフロー型ハーネスの例。依頼（feature_request.md）から、小さなコードベース（repo/: shopcart の Cart）に割引コードの機能を足してリリースするまでのソフトウェア開発のワークフローを、5 フェーズ 9 ステージで定義する。フレームワーク本体はこの例を参照しない。

ステージ本体はすべて偽物で、LLM は使わない。決定論的な本体（シナリオの台本）はフィクスチャの成果物を写し、確率的な本体は種を固定した既知の分布（tests/stochastic.yaml）で変種を選ぶ。実装と単体テストの指標（ビルド、テスト、カバレッジ、lint、変更パスの範囲）は、フィクスチャのコードベースに実在のツールをかけて測る。

- workflow.yaml: ワークフロー定義
- software\_factory/metrics.py: 指標レジストリ（実在のツールで測るものを含む）
- software\_factory/personas.py: 要求の取り込みに束縛するユーザーシミュレータ（ペルソナ 3 つ）
- software\_factory/stages/: 偽のステージ本体（deterministic はシナリオ、probabilistic は確率的なもの）
- software\_factory/design.py: 設計値の MarkovModel（ゲートの分布を足せる）を作り、synthesize の予測から分布テストの基準の根拠（評価の数の期待値 E[n]、訪問の回数の分散）を出す
- software\_factory/scenarios.py: tests/scenarios/ のシナリオの YAML を作る（`python -m software_factory.scenarios`）。遷移の列を手で並べ、ファイルはフィクスチャを `{from: パス}` で参照する
- tests/: テスト、フィクスチャ、シナリオ、expectations（tests/README.md）
- docs/progress.md: 作業ログ
- docs/adopting-gaps.md: adopting.md だけでは判断できなかったこと、足りなかったこと、回避したくなったこと

## 構成

| フェーズ | ステージ | 読む | 書く | end\_state → 戻り先（carry、max） |
| --- | --- | --- | --- | --- |
| discovery | intake（ユーザー待ち） | feature_request.md | intake.md | （unknown のみ） |
| discovery | analyze | feature_request.md, intake.md | requirements.md | needs\_unclear → intake（intake\_questions、2） |
| architecture | design | requirements.md, repo/ | design.md | requirements\_gap → analyze（requirement\_gaps、1）。フェーズ境界越え |
| architecture | plan\_tasks | requirements.md, design.md, repo/ | tasks.yaml | design\_incomplete → design（design\_issues、2） |
| construction | implement | requirements.md, design.md, tasks.yaml, repo/ | repo/src/, impl\_notes.md | task\_unclear → plan\_tasks（task\_questions、1）。フェーズ境界越え<br>quality\_violation → implement（impl\_violations、2） |
| construction | unit\_test | requirements.md, tasks.yaml, repo/, impl\_notes.md | repo/tests/, test\_report.md | impl\_defect → implement（failing\_tests、2）<br>tests\_insufficient → unit\_test（coverage\_gaps、2） |
| assurance | acceptance | feature_request.md, intake.md, requirements.md, tasks.yaml, repo/, test\_report.md | verification.md | requirement\_misread → analyze（requirement\_gaps、1）。三つのフェーズ境界越え<br>requirement\_unmet → implement（unmet\_requirements、2）。フェーズ境界越え |
| assurance | review | design.md, tasks.yaml, repo/, verification.md | review.json | design\_flaw → design（design\_issues、1）。フェーズ境界越え<br>changes\_requested → implement（review\_findings、2）。フェーズ境界越え。assurance のゲートの不合格もこれで戻る |
| delivery | release | requirements.md, verification.md, review.json, repo/ | CHANGELOG.md, release.json | notes\_incomplete → release（missing\_notes、1） |

inputs は feature_request.md と repo/（変更前のコードベース）。

## 実在のツールで測る指標

指標はスナップショットの repo/ を一時ディレクトリに書き出し、このインタプリタで次を走らせる。結果は指標名、引数、内容のハッシュで覚える（同じ内容には同じ値）。

| 指標 | ツール | 使うところ |
| --- | --- | --- |
| build\_passes | `compileall` と、src の下の全モジュールの import | implement、construction のゲート |
| tests\_pass | `pytest` | implement（既存のテスト）、unit\_test、acceptance、construction と delivery のゲート |
| line\_coverage | `coverage run -m pytest` と `coverage json` | unit\_test（80% 以上）、construction のゲート |
| lint\_errors | `ruff check --isolated`（E、F、W、行の長さ 100） | implement（src）、unit\_test（tests）、construction のゲート（両方） |
| out\_of\_scope\_changes | `view.baseline()` との差を、tasks.yaml のタスクの paths と tests に照らす | implement（paths）、unit\_test（tests）、construction のゲート（フェーズの開始から） |

writes（repo/src/、repo/tests/）の外を変えるのは契約違反で、評価の前に escalate される。out\_of\_scope\_changes はそれより狭い、タスクの範囲を測る。

結果を覚えるのは、意味の決まった終了コード（compileall と import は 0 と 1、pytest は 0、1、5 と収集の失敗による 2、ruff は 0 と 1）の時だけ。ツールが異常に終わった時（シグナル、ほかの終了コード、時間切れ）は MetricError にして覚えない（adopting.md 第4節）。分布テストに使う実行の集まりに測定の失敗が一度も無いことを、tests/test\_stochastic.py で確かめる。

要件の id の照合（design\_covers\_requirements、changelog\_covers\_requirements）は、id の前後を英数字の境界だけで切る（「REQ-1は」も数え、REQ-10 は REQ-1 と数えない）。changelog\_covers\_requirements は、最新の版の見出しの下の「- 」で始まる変更の行だけを数える。

## フェーズゲートの落ち方

ゲートは、フェーズの最終ステージが goal に達した直後に評価する（adopting.md 第2.4節）。

- end\_state で自動に戻すのは assurance のゲートだけ。review の changes\_requested は、goal の時にも修正を要しない指摘を記憶 review\_findings に書くので、ゲートから選ばれても持ち帰るものがある
- discovery（analyze）、architecture（plan\_tasks）、construction（unit\_test）、delivery（release）の最終ステージの end\_state は、goal の時には空になる記憶を証拠にするので、ゲートでは選ばれない。この四つのゲートの不合格は unknown になり、人に戻る
- 四つのゲートの指標は、最終ステージかそれより前のステージの goal の指標がすでに満たしている。ゲートで指標が落ちるのは、運用者が goal 到達扱いで続行した後だけ
- ゲートに固有の定性の条件（これに反するとゲートは unknown。assurance は changes\_requested で戻る）
  - discovery: intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）が、すべて requirements.md の要件か受け入れ基準に反映されている
  - architecture: design.md の構成と tasks.yaml のタスクが対応し、すべての要件が「## 対応」とタスクの requirements の両方で扱われている
  - construction: impl\_notes.md と test\_report.md に未解決の違反、問い、失敗、未網羅が無い
  - assurance: review.json の修正を要しない指摘も、verification.md の結果と合わせて、リリースしてよい
  - delivery: CHANGELOG.md と release.json が、合格したすべての要件を挙げて互いに一致する

## 記述の意図と、直さなかったこと

ワークフロー定義の事前レビュー（docs/review-findings.md）を受けて決めたこと。

- **implement の指標が落ちても、記憶 impl\_violations が空なら unknown になる。** implement は終える前にビルド、既存のテスト、lint、変更の範囲、設計との一致を自分で確かめて違反を書く。気づかずに指標だけが落ちた状態は、戻り先が直すための情報が無いので、人に戻すのが正しい（意図どおり）
- **memory\_out の記憶は訪問のたびに書く（問題が無ければ空の一覧）。** 書かないと、持ち帰った前の値が状態文書に残る（adopting.md 第2.1節）。task\_unclear は、記憶 task\_questions と impl\_notes.md の「## 問い」の両方を条件にする。impl\_notes.md は implement の開始時スナップショットに無いので、前の値が残らない
- **持ち帰る記憶は、行番号ではなく、パス、関数、期待する振る舞いで書く。** implement に戻ると repo/src/ は実装の前に戻り、unit\_test のテストも捨てられる。implement は持ち帰った failing\_tests のテストと、repo/tests/ に関する review\_findings を impl\_notes.md の「## テストへの依頼」に書き写し、unit\_test がそれに応える。unit\_test の memory\_in に failing\_tests や review\_findings を足す案は、整合性検査が拒む（unit\_test 自身か前のステージが生成しない記憶を受け取れない）。implement の開始時スナップショットには前の持ち帰りの記憶も残るが、コードを一から書き直すので、それもまだ有効な指摘として扱う
- **analyze の requirement\_count の min 3 は、この依頼（四つの要件）に合わせた値。** 要件が一つか二つで足りる依頼では、goal が選択肢から外れて unknown になる。ほかの依頼に使う時は min 1 にする
- **intake が持ち帰った問いを尋ねたかは、goal では観測しない。** 持ち帰った問いは intake.md の「## 質問と回答」に、ほかの質問と同じ形で書くので、回答の有無は観測できる。尋ねた問いと持ち帰った問いの対応は、memory\_in が状態文書に入らないので観測できない。この例の偽の本体は必ず尋ねる（tests/test\_personas.py）。実際の本体では、intake.md に「## 持ち帰った問い」の節を設け、goal に「その節の問いにすべて回答がある」を足すとよい。acceptance → analyze → intake と連鎖すると、intake の開始時スナップショットに requirement\_gaps は無いので、analyze は依頼者に尋ねるしかない食い違いを intake\_questions に含める（analyze の description に書いた）
- **release はパッケージの版を上げない。** release.json はリリースの記録で、repo/src/shopcart/\_\_init\_\_.py の \_\_version\_\_ の更新は範囲外（release の description に書いた）。版を上げていない状態は notes\_incomplete に含めず unknown のままにする。含めると、release の unknown の代表（版も変更の記録も欠けている）が notes\_incomplete の記述に当たり、代表と記述が食い違うため
- **acceptance の tests\_pass は残す。** unit\_test の goal と construction のゲートが保証するので、goal 到達扱いで続行した後にしか落ちない。検証のステージが、自分の結果の前提（テストが通る）を測る指標として残した

## 記述と代表の整合（試しのラベル）

adopting.md 第15.1節の手順（印を除いた状態文書を記述だけで分類し、印と比べる）を、エージェントが試しのラベルで試した（人手のラベルではない。人間のレビューで付け直す）。markov と divergent の実行のコーパスから (ステージ, 印) ごとに一つ、30 項目で、κ は 0.915。記述と食い違う代表が見つかった（どれも直していない。人間のレビューで扱う）。

- **acceptance の requirement\_misread:** 「## 依頼との食い違い」の前提（購入者がレジの画面でコードを入力する）は precise\_pm の回答にしか無い。ほかのペルソナの intake.md と組むと、記述の上では unknown。直し方の案: 食い違いを依頼そのものから言える点（たとえば、配るコードの書き方の揺れ）にするか、全ペルソナの回答に前提を入れる
- **plan\_tasks の design\_incomplete:** design.md に REQ-3 と REQ-4 を受け持つ構成要素が無いとするが、plan\_tasks の前の design はいつも goal で、その design.md は両方を受け持たせている。記述の上ではいつも unknown。直し方の案: 代表を、goal の design.md でも本当に割り当てられない点（たとえば、構成の一つのファイルに二つの要件の相反する変更が要る）にする。クラスの分布を変えると分布テストの数値を取り直すことになる
- **analyze の goal:** requirements.md の「nn は 1〜50」は、vague\_founder の回答（上限は決めていない）と組むと根拠を持たない。直し方の案: vague\_founder にも上限だけは答えさせるか、vague\_founder の時は analyze が needs\_unclear になる設計にする（後者は分布が変わる）

分類体系の変更の提案（人間の承認を待つ。今の定義は変えていない）:

- unit\_test のテストの不備（lint の違反、tests に無いファイル、要件に反する期待）は、tests\_insufficient の境界を広げて含めた。別案として、テストの不備の end\_state（たとえば tests\_defective）を足して unit\_test 自身に戻す方法がある。不足（テストが無い）と不備（テストが誤っている）を分けて数えたい時に採る

## 確率的な本体の仕掛け

- carry を受けた再進入で分布が変わる: release は、記憶 missing\_notes を受けたかで分布を選ぶ（goal 0.75 → 0.97）。release に戻る辺は自分自身への一本だけで、運用者が中止で答える実行では「訪問 2 以降」と一致する
- クラス内で下流の分布が分かれる: divergent では、implement の goal の二つの変種のうち ok は REQ-1 の割引額の切り捨てを誤り、ok\_fixed は正しい。unit\_test の変種 defect のテストは、実在の pytest で ok では落ち（impl\_defect）、ok\_fixed では通る（goal）。markov では二つ目の変種が ok と同じ誤りを持つ ok\_b なので分かれない
- intake は、種から選んだペルソナに尋ね、回答で intake.md を書く。ペルソナごとの intake.md は intake の goal の違う代表になるが、下流は変えない
- ゲートの分布: markov の実行のゲートはいつも goal。もう一つの実行の集まり（tests/expectations/markov\_gated.yaml）では、assurance のゲートを、実行の種で組み立てた RandomGateClassifier が成果物によらず 0.2 の確率で changes\_requested にする（review の goal の時にも書く review\_findings を持って implement に戻る）。ゲートの答えが代表によらないので独立性検証は違反を出さず、ゲートの分布を足した設計値のモデルの予測が実測と合う

## 通したランナー

| ランナー | テスト |
| --- | --- |
| 整合性検査 | tests/test\_definition.py |
| 契約適合テスト（パッケージに同梱した全シナリオ。参照ランタイムを使うので必須ではなく、版の確認として） | tests/test\_conformance.py |
| 遷移の決定論テスト（14 シナリオ、遷移の六種、escalate の四択、記録再生、ペルソナの束縛） | tests/test\_scenarios.py |
| 分布テスト（expectations。ゲートを揺らす実行を含む） | tests/test\_stochastic.py |
| 独立性検証 | tests/test\_independence.py |
| E2E のカバレッジ（ペルソナを束縛）とマルコフ合成（ゲートの分布を含む） | tests/test\_e2e.py |
| 偽の分類器によるオラクル検証 | tests/test\_oracle.py |
| トリアージの一周 | tests/test\_triage.py |
| 指標とフィクスチャの整合、ユーザーシミュレータ | tests/test\_metrics.py、tests/test\_personas.py |
