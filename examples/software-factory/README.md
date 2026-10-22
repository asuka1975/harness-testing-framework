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

確率的な本体は、クラスを種だけで選び、そのクラスの代表（フィクスチャ）を写す。上流の成果物（ペルソナの回答で変わる intake.md など）とは無関係に選ぶので、代表は、組みうるすべての上流の成果物と並べても記述どおりでなければならない。adopting.md 第15.1節の手順（印を除いた状態文書を記述だけで読んでラベルを付け、印と比べる）で確かめた。

- 往復 7: ステージの項目だけ、(ステージ, 印) ごとに 30 項目。κ 0.915。食い違いが三つ（acceptance の requirement\_misread、plan\_tasks の design\_incomplete、analyze の goal）
- 往復 8（直した後）: markov、divergent、ゲートを揺らす実行（各 400 回、種 20000、30000、50000）を一つの置き場で走らせたコーパス（484 項目。ステージ 371、ゲート 113）から、(scope, 対象, 印, ペルソナ) ごとに一つ、56 項目（ステージ 47、ゲート 9。ペルソナで変わる項目は三つのペルソナにそれぞれ 11）。κ 1.0、食い違い無し

どちらも、エージェントが付けた試しのラベルで、人手のラベルではない。ラベルを付けたエージェントはフィクスチャを作った本人で、記述にも代表にも先入観がある。人間のレビューで、人が改めてラベルを付ける（第15.1節）。

## 人間のレビューで確かめてほしいこと

完了判定の指摘（docs/review-findings.md の E）を受けて、往復 8 で変えたこと。分類体系（end\_state の追加、分割、統合）は変えていない。

1. **plan\_tasks の design\_incomplete には、確率的な本体の代表を置かない（設計値から外した）。** plan\_tasks は design が goal の後にしか走らない。design の goal は「「## 対応」がすべての要件を「## 構成」の構成要素に割り当てる」なので、goal の代表の design.md を読む plan\_tasks が、記述どおりに design\_incomplete（構成要素か変えるファイルが欠けて割り当てられない）になる成果物は作れない。design の goal の代表と、requirements.md、変更前の repo/ を並べて、割り当てられない点を探したが見つからなかった（指摘の案「本当に割り当てられない点を代表にする」は成り立たなかった）。tests/stochastic.yaml の plan\_tasks の分布から incomplete を外し（同じ種で incomplete を引いていた訪問は ok になり、ほかの訪問の選び方は変わらない）、フィクスチャも消した。E2E のカバレッジでは注入で踏む。分布テストの基準は設計値から導き直した（tests/expectations/ の注記）。確かめてほしいこと: design\_incomplete は、design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない。この end\_state を残すか、design の goal に「構成要素ごとに変えるファイルを決めている」を足して二つの記述の範囲を揃えるか
2. **ペルソナの回答を、どれも要件に要る値を決めるものにした。** vague\_founder は、言い方はくだけているが、コードの形、上限 50%、割引額の切り捨て、0 円の下限、無効なコードをエラーにすることを答える。三つのペルソナとも、最初の三つの回答に、購入者がレジの画面でコードを入力することと、割引額の切り捨てと 0 円の下限を含める。これで analyze の goal の代表（REQ-1〜REQ-4）は、どのペルソナの回答にも根拠を持つ（E-M1 の 3、4）
3. **analyze の needs\_unclear が持ち帰る問いを、どのペルソナも今は決めていない点にした。** 上限と下限は最初の回答で決まるので、前の問い（上限、小計を超えた時）は needs\_unclear の代表として記述に合わない。新しい問いは「キャンペーンが終わった後も使えるか」「同じ購入者が何回使えるか」で、どのペルソナも尋ねられても決めない（決める時期だけを答える）。analyze の goal の代表はこの二点に触れない。確かめてほしいこと: analyze の goal の記述は、要件の網羅を求めていない（根拠と、未決事項が無いことだけ）ので、この二点を書かない requirements.md も goal に当たる。needs\_unclear は記憶 intake\_questions の有無で goal に優先する。分析する人が問いにするかどうかで分かれるのを、記述が意図しているか
4. **requirements.md に「## 利用者」の節を設けた（代表の直し）。** discovery のゲートの「intake.md の回答（利用者、…）が requirements.md に反映」を、goal の代表がどのペルソナでも満たす（E-M2）。記述は変えていない
5. **acceptance の requirement\_misread の代表は、食い違いの前提を intake.md の回答（と requirements.md の「## 利用者」）に置いた（代表の直し）。** 三つのペルソナとも「レジの画面で入力」を答える（E-M1 の 1）
6. **unit\_test の goal に「impl\_notes.md の「## テストへの依頼」のすべてを確かめる」を足した（記述の改訂。E-L3）。** 依頼を無視したテストが goal に当たらないようにした
7. **assurance のゲートの goal に「判断は verification.md と review.json に基づき、このゲートで repo/ のコードを改めて検証しない」を足した（記述の改訂。E-L1）。** markov の goal の実装（ok、ok\_b）は、どちらも REQ-1 の切り捨てを誤る（小計 333 円に PCT10 で 299 円）が、受け入れ基準と単体テストはこの場合を確かめないので、主経路はこの既知の欠陥を持ったままリリースする（玩具の意図。acceptance の requirement\_unmet の代表がこの欠陥を見つける場合）。repo/ を読む分類器が、ゲートで欠陥を探して goal を外さないように、判断の範囲を書いた

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
| 遷移の決定論テスト（15 シナリオ、遷移の六種、escalate の四択、記録再生、ペルソナの束縛） | tests/test\_scenarios.py |
| 分布テスト（expectations。ゲートを揺らす実行を含む） | tests/test\_stochastic.py |
| 独立性検証 | tests/test\_independence.py |
| E2E のカバレッジ（ペルソナを束縛）とマルコフ合成（ゲートの分布を含む） | tests/test\_e2e.py |
| 偽の分類器によるオラクル検証 | tests/test\_oracle.py |
| トリアージの一周 | tests/test\_triage.py |
| 指標とフィクスチャの整合、ユーザーシミュレータ | tests/test\_metrics.py、tests/test\_personas.py |
