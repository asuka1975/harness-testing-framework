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
| construction | unit\_test | requirements.md, tasks.yaml, repo/, impl\_notes.md | repo/tests/, test\_report.md | impl\_defect → implement（failing\_tests、2）<br>tests\_defective → unit\_test（test\_defects と coverage\_gaps、2）<br>tests\_insufficient → unit\_test（coverage\_gaps、2） |
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
- ゲートの定性の条件（workflow.yaml のフェーズの goal の文。これに反するとゲートは unknown。assurance は changes\_requested で戻る）
  - discovery: requirements.md の各要件が、feature\_request.md の依頼か intake.md の回答に根拠を持ち、intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映されている
  - architecture: design.md の構成と tasks.yaml のタスクが対応し、requirements.md のすべての要件が、design.md の「## 対応」と、タスクの requirements の両方で扱われている
  - construction: repo/tests/ のテストがすべて通って requirements.md の受け入れ基準を確かめ、impl\_notes.md と test\_report.md に未解決の違反、問い、失敗、不備、未網羅が無い（repo/ の変更がタスクの範囲に収まることは、指標 out\_of\_scope\_changes が測る）
  - assurance: verification.md の表ですべての要件が合格し、review.json の指摘（修正を要しないものを含む）を合わせても、repo/ をこのままリリースしてよい。判断は verification.md と review.json に基づき、このゲートで repo/ のコードを改めて検証しない
  - delivery: CHANGELOG.md と release.json が、verification.md で合格したすべての要件を挙げて互いに一致し、repo/tests/ のテストが通る状態の repo/ をリリースする

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
- 往復 10（tests\_defective を足し、F-L3 で代表を直した後）: 変えた所に絞ってやり直した。全変種を踏むように、markov の分布に implement の ok\_fixed と unit\_test の defective を足した試しの分布（スクラッチ。例には入れていない）で 300 回（種 70000）走らせたコーパス（353 項目。ステージ 263、ゲート 90）から、(scope, 対象, 印, 上流の違い) ごとに一つ、32 項目を選んだ。上流の違いは、unit\_test と construction のゲートでは implement の変種（ok、ok\_b、ok\_fixed）、analyze、acceptance、discovery のゲートではペルソナ。内訳はステージ 25（unit\_test 14: goal、impl\_defect、tests\_defective、tests\_insufficient、unknown の印ごと。analyze の goal と needs\_unclear 6。acceptance の requirement\_misread 3。design の goal と requirements\_gap 2）、ゲート 7（construction 4、discovery 3）。κ 1.0、食い違い無し

どれも、エージェントが付けた試しのラベルで、人手のラベルではない。ラベルを付けたエージェントはフィクスチャを作った本人で、記述にも代表にも先入観がある。人間のレビューで、人が改めてラベルを付ける（第15.1節）。

## 人間のレビューで確かめてほしいこと

人間が往復 8 の後のこの節と、完了判定の二回目が渡した事項をレビューして回答した（docs/review-findings.md の F）。往復 10 で、回答に合わせて直した。

### 決まったこと（人間の回答）

1. **plan\_tasks の design\_incomplete は残す。** 記述は変えない。確率的な本体に代表を置かず、E2E のカバレッジの注入で踏む今の形のまま
   - 判断の材料として直したこと: 往復 8 のこの節の「design\_incomplete は、design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」は言い過ぎだった。記述の上では、design の goal を正しく満たした後でも、implement の task\_unclear（タスクの paths の外のファイルを変えないと実装できない）で plan\_tasks に戻り、そのファイルが design.md の「## 構成」に無いと分かる経路で、design\_incomplete は起きうる
   - 確率的な本体に代表を置かない理由はそのまま: クラスは (ステージ, 訪問の区分) と種だけで選ぶので、代表は、その区分に届きうるすべての上流の成果物と整合しなければならない。design の goal の代表の design.md はすべての要件を構成のファイルに割り当てていて、plan\_tasks の訪問 1 と、design から next で入り直した訪問は、paths の外のファイルについての問いを持たない（この例の implement の task\_unclear の代表の問いも、割引の適用の単位で、paths の外のファイルではない）。上流の goal の代表と両立しない（tests/stochastic.yaml の注記）
   - 往復 10 で、この辺（carry design\_issues、max 2）を通るシナリオ plan\_tasks\_design\_incomplete\_rollback を足した（F-3）。design が要件への問いを残すが分類の確信度が低く unknown になり、運用者が goal 到達扱いで続行する。plan\_tasks は、その design.md の「## 構成」に REQ-3 と REQ-4 を受け持つ構成要素が無いことを記憶 design\_issues に書いて design に戻り、空でない design\_issues が design の訪問 2 の開始時スナップショットに届く（expect.starts）。代表（tests/fixtures/plan\_tasks/incomplete/）は上流の design/gap と組むので、記述と食い違わない
2. **利用者役が変えた記述は承認。** 往復 8 の unit\_test の goal（「## テストへの依頼」のすべてを確かめる）と assurance のゲートの goal（判断は verification.md と review.json に基づく）、往復 6 の end\_state の範囲の拡大
3. **ペルソナの設計は承認。** 三人とも要件の値（利用者と入力の場所、コードの形と上限、割引額の切り捨てと 0 円の下限、無効なコードの扱い）を答え、曖昧さは analyze が尋ね返す問い（キャンペーンの後も使えるか、同じ購入者が何回使えるか）でだけ入る
4. **unit\_test のテストの不備を、end\_state tests\_defective として tests\_insufficient から分ける提案を採る。** 往復 10 で入れた（下の「確かめてほしいこと」）
5. **主経路が REQ-1 に反するコードをリリースすること（玩具の意図）は、読んだうえで良い。** markov の goal の実装（ok、ok\_b）は小計 333 円に PCT10 で 299 円にする（割引額の切り捨てなら 300 円）。受け入れ基準と単体テストの ok の代表はこの場合を確かめないので、主経路はこの既知の欠陥を持ったままリリースする

### 確かめてほしいこと（往復 10 で変えた記述。人間がもう一度確かめる）

unit\_test の end\_state を、impl\_defect、tests\_defective、tests\_insufficient、unknown の四つにした（人間が採った分類体系の変更。F-1）。workflow.yaml の文:

- **tests\_defective**: repo/tests/ に、unit\_test 自身が直すべき不備（テストが誤っている）がある: requirements.md の要件の記述か受け入れ基準に反する期待を持つテスト（通るか失敗するかによらない）、テスト自身の誤り（準備、呼び出し、import）で失敗するテスト、repo/tests/ の lint の違反、tasks.yaml のタスクの tests に無いファイルの変更。その不備が、記憶 test\_defects と test\_report.md の「## 不備」の両方に列挙されている（どのファイルが変わったかは状態からは見えないので、変更の範囲の不備はこの列挙で判断する）。同時に不足もあれば、それも記憶 coverage\_gaps と「## 未網羅」に列挙されている（一度に持ち帰って直す）。tests\_insufficient に優先する。
- **tests\_insufficient**: unit\_test 自身が直すべき不足（テストが足りない）があり、不備は無い: requirements.md の受け入れ基準のうちテストの無いもの、impl\_notes.md の「## テストへの依頼」のうちテストの無いもの、repo/src/ の実行されない箇所（行カバレッジが 80% に届かない）。その不足が、記憶 coverage\_gaps と test\_report.md の「## 未網羅」に列挙されている。
- impl\_defect の優先は「tests\_defective と tests\_insufficient に優先する」にした（前は tests\_insufficient だけ）。それ以外の文は変えていない
- 戻り: tests\_defective → unit\_test（carry test\_defects と coverage\_gaps、max 2）。tests\_insufficient → unit\_test（coverage\_gaps、max 2）はそのまま
- 合わせて変えた記述: unit\_test の description（test\_report.md を「## テスト」「## 失敗」「## 不備」「## 未網羅」の四つの節にし、不備は記憶 test\_defects、不足は coverage\_gaps に書く。自己点検に「各テストの期待と requirements.md の要件との一致」を足した）、memory\_in と memory\_out に test\_defects、unit\_test の goal に「「## 不備」が空」、**construction のゲートの goal に「不備」**（「未解決の違反、問い、失敗、不備、未網羅が無い」）。ゲートは unit\_test の外で触れた唯一の記述で、前は不備も「## 未網羅」に書いていたので、節を分けてもゲートの意味が変わらないように足した

境界と理由:

1. **不足は「足りない」、不備は「誤っている」で分ける。** 不足は、テストを足せば直る（テストの無い受け入れ基準と「## テストへの依頼」、実行されない箇所）。不備は、今あるテストを直すか消さないと直らない（要件に反する期待、テスト自身の誤り、lint の違反、tests に無いファイルの変更）。F-1 の案の振り分けのとおり。何も確かめないテスト（期待が要件に反しない）は、その基準を確かめるテストが無いことになるので、不足に入る
2. **F-1 の案に一つ足した: テスト自身の誤り（準備、呼び出し、import）で失敗するテスト。** impl\_defect は「テストではなく repo/src/ が誤っている」失敗なので、テストの側が誤っている失敗は、案のままでは期待が要件に反しない限りどこにも当たらず unknown になる。失敗したテストを、どちらが誤っているかで impl\_defect と tests\_defective に分けきるために足した。要らなければ、この一句を外しても他の境界は変わらない
3. **要件に反する期待は、通るか失敗するかによらず不備。** 失敗するなら、impl\_defect との境界は「期待が要件に従うか」で決まる。通るなら（実装も同じ誤りを持つ）、そのテストは誤りを隠すので goal ではない（goal は「「## 不備」が空」）
4. **優先は impl\_defect、tests\_defective、tests\_insufficient の順。** impl\_defect が先なのは前と同じ（implement に戻ると repo/src/ もテストも書き直され、テストの不備と不足はその後の unit\_test で改めて扱われる）。不備を不足より先にするのは、誤ったテストがあると、カバレッジや「基準にテストがあるか」の判断そのものが当てにならないため（誤った期待のテストも行を実行し、基準を確かめているように見える）
5. **不備で戻る時は、同時にある不足も持ち帰る（carry test\_defects と coverage\_gaps）。** 前の tests\_insufficient は不足と不備を coverage\_gaps 一つで持ち帰っていた。不備だけを持ち帰ると、両方ある時に不足の記録が戻りで捨てられ、分ける前より悪くなる。戻りの回数は辺ごとに数えるので、不備で戻った回数と不足で戻った回数は分かれたまま
6. **記憶 test\_defects と節「## 不備」を、不足（coverage\_gaps、「## 未網羅」）と分けた。** 不足と不備を分けて数えられるように。tests\_defective の条件は記憶と節の両方に列挙されていること（implement の task\_unclear と同じ形）。test\_report.md は unit\_test の開始時スナップショットに無いので、持ち帰った前の値が節に残らない
7. **max は 2。** implement が自分の違反（ビルド、lint、範囲）で自分自身に戻る quality\_violation（max 2）と同じ、自分で直せる誤りなので揃えた。辺が二本になり、unit\_test が自分自身に戻れる回数の合計は 2 から 4 になる
8. **確率的な実行には tests\_defective を出さない（分布と基準は変えていない）。** 今の tests\_insufficient の代表 thin（REQ-1〜REQ-3 の受け入れ基準にテストが無く、カバレッジが 68〜71%）は新しい境界でも不足で、不備に当たる点（lint の違反、tests に無いファイル、要件に反する期待、テスト自身の誤り）が無かった。そのため tests/stochastic.yaml の分布、設計値のモデル（software\_factory/design.py）、expectations の基準は変えていない（種と変種の対応も、観測値も前と同じ）。tests\_defective の代表 tests/fixtures/unit\_test/defective/（REQ-2 の 0 円の下限に反して、小計 300 円に OFF500 で -200 円を期待するテスト。どちらの実装の系統でも実在の pytest で落ちる）は、tests/stochastic.yaml の variants に置くが、どの分布にも置かない（確率 0）。E2E のカバレッジは誘発で踏み、シナリオ unit\_test\_defective\_self\_rollback が、持ち帰った test\_defects と coverage\_gaps が unit\_test の訪問 2 の開始時スナップショットに届くことを確かめる

### まだのこと

- 第15.1節の人手のラベル（人間がする）。往復 10 の試しのラベル（エージェント）は上の「記述と代表の整合」にある
- 上の tests\_defective と tests\_insufficient の記述と境界の確認（とくに、案に足した「テスト自身の誤りで失敗するテスト」と、不備で戻る時に不足も持ち帰ること）

### 完了判定の二回目の指摘（低）への対応

- **F-L1 注記の数字:** 直した。markov.yaml の release の訪問 1 は「両側 3.21 SE（規則の 3.2 SE をわずかに上回る）。誤って落ちる確率は正規近似で約 0.13%」、mean\_visits は visits\_variance 1.358、標準偏差 1.165、markov\_shifted.yaml の mean\_visits [1.95, 2.50] は 4.7 SE（4.745）、software\_factory/design.py の docstring の visits\_variance は手引き第12節の言い方に。指摘の外で、markov\_gated.yaml と markov\_gated\_shifted.yaml の SE の倍数の丸めを四捨五入に揃えた（3.45 → 3.5、3.55 → 3.6、5.75 → 5.8）。基準の値はどれも変えていない
- **F-L2 絞った独立性の確かめ:** 直した。markov の stage:implement=goal の訪問 1 → 1（tests/test\_independence.py）と、入り方の検定の implement（tests/test\_e2e.py）を、「判定でき、p 値が 0.001 以上」で確かめる。同じ形の intake のペルソナの代表の確かめも同じにした。`HTF_RUNS` や種を変えると落ちうることを tests/README.md に書いた
- **F-L3 (1) discovery のゲートの「利用者」:** 代表の側で直した。analyze の goal の代表（と needs\_unclear の代表）の requirements.md から「## 利用者」の節を外し、REQ-3 を「購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む」にした（受け入れ基準のある要件の文）。design の goal の代表の「## 対応」の REQ-3 に、画面は repo/ の外で、コードを文字列で受け取ることを書いた（要件の画面の部分を構成要素に割り当てていないと読まれないように）。acceptance の requirement\_misread の代表の参照も REQ-3 にした。discovery の goal の記述は変えていない
- **F-L3 (2) vague\_founder の「端数は切り捨て」:** 「割り引く額の端数は切り捨て」にした
- **F-L3 README の表:** 「フェーズゲートの落ち方」の定性の条件を、workflow.yaml のフェーズの goal の文に合わせた（assurance の判断の範囲、construction の不備を含む）

### 提案（人間の承認を待つ。定義は変えていない）

- tests\_defective を確率的な実行にも出す: unit\_test の分布に変種 defective を足し、設計値と基準を第12節の方法で導き直す。今は E2E のカバレッジとシナリオでだけ踏むので、分布テストと独立性検証はこのクラスを見ていない

## 確率的な本体の仕掛け

- carry を受けた再進入で分布が変わる: release は、記憶 missing\_notes を受けたかで分布を選ぶ（goal 0.75 → 0.97）。release に戻る辺は自分自身への一本だけで、運用者が中止で答える実行では「訪問 2 以降」と一致する
- クラス内で下流の分布が分かれる: divergent では、implement の goal の二つの変種のうち ok は REQ-1 の割引額の切り捨てを誤り、ok\_fixed は正しい。unit\_test の変種 defect のテストは、実在の pytest で ok では落ち（impl\_defect）、ok\_fixed では通る（goal）。markov では二つ目の変種が ok と同じ誤りを持つ ok\_b なので分かれない
- intake は、種から選んだペルソナに尋ね、回答で intake.md を書く。ペルソナごとの intake.md は intake の goal の違う代表になるが、下流は変えない
- 分布に置かない代表: unit\_test の defective（tests\_defective）は tests/stochastic.yaml の variants にあるが、どの分布にも置かない（確率 0）。E2E のカバレッジの誘発とシナリオだけが写し、test\_metrics.py が実在の指標を確かめる。plan\_tasks の design\_incomplete は変種も置かず、代表 tests/fixtures/plan\_tasks/incomplete/ はシナリオだけが写す（E2E のカバレッジでは注入で踏む）。確率的な実行で踏まない (ステージ, クラス) は、この二つだけ
- ゲートの分布: markov の実行のゲートはいつも goal。もう一つの実行の集まり（tests/expectations/markov\_gated.yaml）では、assurance のゲートを、実行の種で組み立てた RandomGateClassifier が成果物によらず 0.2 の確率で changes\_requested にする（review の goal の時にも書く review\_findings を持って implement に戻る）。ゲートの答えが代表によらないので独立性検証は違反を出さず、ゲートの分布を足した設計値のモデルの予測が実測と合う

## 通したランナー

| ランナー | テスト |
| --- | --- |
| 整合性検査 | tests/test\_definition.py |
| 契約適合テスト（パッケージに同梱した全シナリオ。参照ランタイムを使うので必須ではなく、版の確認として） | tests/test\_conformance.py |
| 遷移の決定論テスト（17 シナリオ、遷移の六種、定義の上のロールバックの辺 13 本のすべて、escalate の四択、記録再生、ペルソナの束縛） | tests/test\_scenarios.py |
| 分布テスト（expectations。ゲートを揺らす実行を含む） | tests/test\_stochastic.py |
| 独立性検証 | tests/test\_independence.py |
| E2E のカバレッジ（ペルソナを束縛）とマルコフ合成（ゲートの分布を含む） | tests/test\_e2e.py |
| 偽の分類器によるオラクル検証 | tests/test\_oracle.py |
| トリアージの一周 | tests/test\_triage.py |
| 指標とフィクスチャの整合、ユーザーシミュレータ | tests/test\_metrics.py、tests/test\_personas.py |
