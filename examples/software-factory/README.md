# software-factory

harness-testing-framework の利用者として、docs/adopting.md だけを手引きに作ったワークフロー型ハーネスの例。依頼（feature_request.md）から、小さなコードベース（repo/: shopcart の Cart）に割引コードの機能を足してリリースするまでのソフトウェア開発のワークフローを、5 フェーズ 9 ステージで定義する。フレームワーク本体はこの例を参照しない。

ステージ本体はすべて偽物で、LLM は使わない。決定論的な本体（シナリオの台本）はフィクスチャの成果物を写し、確率的な本体は種を固定した既知の分布（tests/stochastic.yaml）で変種を選ぶ。実装と単体テストの指標（ビルド、テスト、カバレッジ、lint、変更パスの範囲）は、フィクスチャのコードベースに実在のツールをかけて測る。

- workflow.yaml: ワークフロー定義
- software\_factory/metrics.py: 指標レジストリ（実在のツールで測るものを含む）
- software\_factory/personas.py: 要求の取り込みに束縛するユーザーシミュレータ（ペルソナ 3 つ）
- software\_factory/stages/: 偽のステージ本体（deterministic はシナリオ、probabilistic は確率的なもの）
- software\_factory/design.py: 設計値の MarkovModel（ゲートの分布を足せる）を作り、synthesize の予測から分布テストの基準の根拠（評価の数の期待値 E[n]、訪問の回数の分散）を出す
- software\_factory/scenarios.py: tests/scenarios/ のシナリオの YAML を作る（`python -m software_factory.scenarios`）。遷移の列を手で並べ、ファイルはフィクスチャを `{from: パス}` で参照する
- software\_factory/labeling.py: 人がラベルを付ける材料（docs/human-labeling.md）を試しの実行から作り、受け取ったラベルを印と比べる（examples/software-factory/ で `uv run python -m software_factory.labeling`。下の「記述と代表の整合」）
- tests/: テスト、フィクスチャ、シナリオ、expectations（tests/README.md）
- docs/progress.md: 作業ログ
- docs/adopting-gaps.md: adopting.md だけでは判断できなかったこと、足りなかったこと、回避したくなったこと
- docs/human-labeling.md: 人がラベルを付ける材料（66 項目。docs/human-labeling.corpus.jsonl がそのコーパス）

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
- ゲートの定性の条件（workflow.yaml のフェーズの goal の文。これに反するとゲートは unknown。assurance は changes\_requested で戻る）
  - discovery: requirements.md の各要件が、feature\_request.md の依頼か intake.md の回答に根拠を持ち、intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映されている
  - architecture: design.md の構成と tasks.yaml のタスクが対応し、requirements.md のすべての要件が、design.md の「## 対応」と、タスクの requirements の両方で扱われている
  - construction: repo/tests/ のテストがすべて通って requirements.md の受け入れ基準を確かめ、impl\_notes.md と test\_report.md に未解決の違反、問い、失敗、未網羅が無い（repo/ の変更がタスクの範囲に収まることは、指標 out\_of\_scope\_changes が測る）
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

## 記述と代表の整合（試しのラベルと、人が付けるラベルの材料）

人がラベルを付ける材料（docs/human-labeling.md）でラベルを付ける人は、ラベルを付け終えるまでこの節を読まない（項目の選び方、組ごとの数、クラスの名前を書いてある）。材料の冒頭にも同じ注意がある。コマンドは examples/software-factory/ で `uv run python -m software_factory.labeling …` として実行する（リポジトリの根では `No module named 'software_factory'` になる）。

確率的な本体は、クラスを種だけで選び、そのクラスの代表（フィクスチャ）を写す。上流の成果物（ペルソナの回答で変わる intake.md など）とは無関係に選ぶので、代表は、組みうるすべての上流の成果物と並べても記述どおりでなければならない。adopting.md 第15.1節の手順（印を除いた状態文書を記述だけで読んでラベルを付け、印と比べる）で確かめる。

- 往復 7: ステージの項目だけ、(ステージ, 印) ごとに 30 項目。κ 0.915。食い違いが三つ（acceptance の requirement\_misread、plan\_tasks の design\_incomplete、analyze の goal）
- 往復 8（直した後）: markov、divergent、ゲートを揺らす実行（各 400 回、種 20000、30000、50000）を一つの置き場で走らせたコーパス（484 項目。ステージ 371、ゲート 113）から、(scope, 対象, 印, ペルソナ) ごとに一つ、56 項目（ステージ 47、ゲート 9。ペルソナで変わる項目は三つのペルソナにそれぞれ 11）。κ 1.0、食い違い無し
- 往復 10（tests\_defective を足し、F-L3 で代表を直した後）: 変えた所に絞った 32 項目（スクラッチの試しの分布、300 回、種 70000）。κ 1.0、食い違い無し。tests\_defective は往復 11 で取り消したので、その時の unit\_test の 14 項目は今の記述には当たらない

ここまでは、エージェントが付けた試しのラベルで、人手のラベルではない。ラベルを付けたエージェントはフィクスチャを作った本人で、記述にも代表にも先入観がある。

**人が付けるラベルの材料（docs/human-labeling.md、66 項目）。** 人間の決定（docs/review-findings.md の G）で、往復 10 で代表を変えた所は、人が印を除いて読んでラベルを付ける（全部の付け直しはしない）。往復 11 で作り（30 項目）、往復 12 で項目の選び方を手引き第15.1節の目安（変えた所に絞ってラベルを付け直す時の、対象、訪問、まとめ方）に合わせ（45 項目）、往復 13 で改められた目安に合わせて review を足した（49 項目）。往復 14 で、差分の確かめ（docs/review-findings.md の H）を受けて、implement を足し、acceptance の上流の違いに持ち帰った問いの回答の有無を足し、シナリオだけが写す plan\_tasks/incomplete を項目にし、人に渡す形を改めた（66 項目）。software\_factory/labeling.py が、試しの実行（tests/stochastic.yaml の profiles の labeling。分布を寄せ、分布テストの分布に無い unit\_test の defective と implement の全クラスも置いた。480 回、種 90000）のコーパス（`build_corpus(..., unique_states=True)` で 308 項目。ステージ 246、ゲート 62）に、シナリオ plan\_tasks\_design\_incomplete\_rollback で分類器が見る plan\_tasks の訪問 1 の状態文書（1 項目）を足した 309 項目（286 項目が変えた代表を含む）から、次の規則で選ぶ。

- 変えた代表と変えた所: REQ-3 に利用者と入力の場所（購入者がレジの画面で入力する）の句をまとめ、「## 利用者」の節を外した requirements.md（REQ-3 の振る舞いと受け入れ基準は変えていない）、「## 対応」の REQ-3 に画面は repo/ の外でコードを文字列で受け取ると書いた design/ok の design.md、「## 依頼との食い違い」の根拠を REQ-3 にした acceptance/misread の verification.md、「割り引く額の端数は切り捨て」にした vague\_founder の回答、往復 11 で tests\_insufficient の確率 0 の代表にした unit\_test/defective
- 対象: 記述（ステージの goal と end\_state、フェーズの goal）が、変えた所（成果物の全体ではない）を判断の根拠にしうる対象。項目は、その対象が根拠にしうる変えた代表のどれかを状態文書に含む評価。変えた所は、節や要件より細かい句で区切った（REQ-3 なら誰がどこで入力するかの句。手引きの「直した節、要件、回答など」の「など」として。REQ-3 を一つの変えた所とすると、要件の記述に照らす unit\_test も対象になるが、その句はテストが期待も否定もできない）
  - requirements.md: 要件の根拠を見る analyze と discovery のゲート、要件の構成要素への割り当てと受け持つ構成要素の欠けを見る design、plan\_tasks、architecture のゲート、要件と依頼や回答の食い違いを見る acceptance。design.md: 「## 対応」を見る design と architecture のゲート、要件を受け持つ構成要素の欠けを見る plan\_tasks、修正を要する指摘が design.md の構成かインターフェースを変えなければ解消しないか（design\_flaw と changes\_requested の境界）を見る review、repo/src/ の変更が design.md の構成どおりか（goal）と「## 構成」から外れていないか（quality\_violation）を見る implement。回答: intake.md を読む intake、analyze、discovery のゲート、acceptance。defective: unit\_test
  - implement を足した理由（往復 14。review と同じ当てはめ）: implement の goal の「repo/src/ の変更が design.md の構成どおり」は、review の記述と同じく design.md の節を名指さない。変えた句のうち「コードを文字列で受け取る」は parse\_code のインターフェースを、「画面は repo/ の外」は画面を repo/ に置かないという構成を述べるので、goal と quality\_violation の判断の根拠になりうる。往復 13 までは「「## 構成」で判断する」として外していたが、それは節で分けた理由で、往復 13 で review を足した理由（記述は節を名指さず、変えた句はインターフェースを述べる）と揃っていなかった
  - 渡さない対象: unit\_test と construction のゲートの requirements.md（テストの期待と結果を、受け入れ基準と要件の振る舞いに照らす。REQ-3 の受け入れ基準と振る舞いは変えておらず、変えたのは誰がどこで入力するかで、テストが期待も否定もできない）、construction のゲートの design.md（状態文書には implement が読む design.md が入るが、フェーズの goal は design.md に触れず、impl\_notes.md と test\_report.md に未解決の違反、問い、失敗、未網羅が無いかで判断する）、release、assurance と delivery のゲート（verification.md の合格、review.json と要件の id で判断する。どれも変えた所を含まない）
  - 往復 11 との違い: plan\_tasks と architecture のゲートを足した（往復 11 は design.md を design だけの根拠とし、requirements.md も plan\_tasks とそのゲートに渡していなかった）。往復 12 との違い: review を足した（往復 13）。往復 13 との違い: implement を足した（往復 14）
- 訪問: 訪問 1 を渡す。訪問 2 以降も渡すのは、memory\_in を持つステージ（対象のうち intake、analyze、design、plan\_tasks、implement、unit\_test）と、そのステージを含むフェーズのゲート（discovery、architecture。ゲートの状態文書はフェーズの全体で、ゲートの訪問は最終ステージの訪問）だけ。見出しのほかは訪問 1 の項目と同じ状態文書は除く（記述の当てはまり方が同じなので訪問 1 の項目で代える）。acceptance と review は memory\_in を持たないので訪問 1 だけ
- まとめ方: (対象, 訪問の区分, 印, 上流の違い) ごとに一つ、状態文書の短いもの（上流の違いのほかの違いが少ないもの）。上流の違いは、intake.md を読む対象では (依頼者のペルソナ, 持ち帰った問いの回答の有無)、unit\_test では goal の実装の変種（ok、ok\_b、ok\_fixed）、ほかの対象（implement と review を含む）には無い
  - acceptance の上流の違いに持ち帰った問いの回答の有無を足した（往復 14）。持ち帰った問いと未定の回答（キャンペーンの後も使えるか、同じ購入者が何回使えるか）を含む intake.md は、acceptance の状態文書と、requirements.md と回答の食い違いの読みを変える。intake、analyze、discovery のゲートでは、回答の有無は訪問の区分と一致する（訪問 1 は無く、訪問 1 と同じものを除いた後の訪問 2 以降は有る。テストで確かめる）ので、組は往復 13 と同じ
  - この例の偽の本体は入り直しても同じ代表を写すので、訪問 2 以降の状態文書が訪問 1 と違うのは、持ち帰った問いとペルソナの回答（どれも未定）が intake.md に入る intake、analyze、discovery のゲートだけ。design、plan\_tasks、architecture のゲート、implement は、試しの実行でどのクラスの訪問 2 以降も出るが、見出しのほかは訪問 1 と同じ（テストで確かめる）。unit\_test の defective は訪問 1 にしか写らない
  - acceptance は分布テストの主経路の goal の実装（ok、ok\_b）の後のものに限る。requirement\_unmet の代表の「小計 333 円に PCT10 で 299 円になる。Discount.apply が支払額を切り捨てている」は ok と ok\_b でだけ成り立ち、正しい実装 ok\_fixed（300 円になる）とは食い違う。markov は ok\_fixed を置かないので組まないが、divergent と試しの実行 labeling では ok\_fixed の後にも requirement\_unmet を選び、その組は手引き第12節の整合（代表は、届きうるすべての上流の成果物と整合させる）を満たさない。材料からはその組を外した（試しのコーパスでは、ok\_fixed の後の acceptance の訪問 1 が 20 項目あり、うち requirement\_unmet が 6 項目）。divergent の組は、独立性検証のための本体として許す: divergent が確かめるのは implement の goal の代表ごとの下流（unit\_test のクラス）の分布で、acceptance の代表の文が実装と合うかは、代表の鍵（書いた成果物のハッシュ）にも次の状態にも関わらない。divergent の実行は、分布テストの基準、オラクル、トリアージ、人に渡す材料には使わない
  - 試しのコーパスに出ない組は無い（66 の組がすべて出る）。回数 480 は、種の基点を 90000〜97000 の八つにして試し、八つすべてで 66 の組が出た回数（300 回では四つで acceptance の組が一つか二つ欠けた）。種 90000 は前のまま
- 確率的な実行に置かない代表（plan\_tasks/incomplete）: シナリオ plan\_tasks\_design\_incomplete\_rollback だけが写す代表で、試しの実行には出ない（上流の design/gap を運用者が goal 到達扱いで通した後にしか組まず、試しの実行の運用者は中止で答える）。手引き第15.1節の 1 のとおり、そのシナリオで分類器が見る plan\_tasks の訪問 1 の状態文書を項目の候補にした（往復 14。往復 11 はエージェントが記述だけで読んで design\_incomplete に当たると確かめ、材料には入れていなかった）。`run_scenario` は置き場を返さないので、シナリオの台本の偽物（`ScriptedBody`、`ScriptedClassifier`、`ScriptedOperator`、`ScriptedUser`）でランタイムを組み立てて実行し、実行記録の要約がシナリオの期待と一致することと、状態文書の SHA-256 が `run_scenario` の実行記録のものと同じことを確かめる（tests/test\_labeling.py）

| 対象 | 訪問 1 | 訪問 2 以降 | 内訳 |
| --- | --- | --- | --- |
| intake | 2 | 2 | vague\_founder の回答の goal と unknown（訪問 2 以降は持ち帰った問いと回答を含む） |
| analyze | 7 | 7 | goal と needs\_unclear を三つのペルソナで 6、vague\_founder の回答の unknown 1（訪問 2 以降は持ち帰った問いと回答を含む） |
| discovery のゲート | 3 | 3 | 三つのペルソナ（訪問 2 以降は持ち帰った問いと回答を含む） |
| design | 3 | 0 | goal、requirements\_gap、unknown |
| plan\_tasks | 3 | 0 | goal、unknown と、シナリオの design\_incomplete |
| architecture のゲート | 1 | 0 | 一つ（ゲートの上流に違いが無い） |
| implement | 4 | 0 | goal、task\_unclear、quality\_violation、unknown（上流の違いが無い） |
| unit\_test | 3 | 0 | defective（要件に反する期待を持つテスト）を、goal の実装の三つの変種の後で |
| acceptance | 24 | 0 | goal、requirement\_unmet、requirement\_misread、unknown を、三つのペルソナと持ち帰った問いの回答の有無の六通りで |
| review | 4 | 0 | goal、changes\_requested、design\_flaw、unknown（上流の違いが無い） |
| 合わせて | 54 | 12 | 66 項目（ステージ 59、ゲート 7） |

**人に渡す形（往復 14。docs/review-findings.md の H-M1、H-L1〜H-L3）。** 人に渡すのは human-labeling.md だけで、印（分類器の選択、代表のクラス）、選んだ規則、組ごとの数、項目の id を書かない（手引き第15.1節の 2）。選んだ規則と組ごとの数はこの節にだけ置き、材料には「選び方は README にある。ラベルを付け終えるまで README の『記述と代表の整合』を読まない」とだけ書く。README のほかの節、docs/ のほかの文書、tests/ と software\_factory/ の下にも代表のクラスが書いてあるので、材料には、ラベルを付け終えるまで材料のほかは開かないことも書いた（比べる時のコーパスとフィクスチャには印が残る）。

- 項目は通し番号（項目 1〜66）だけで示す。番号と id の対応はコーパス（docs/human-labeling.corpus.jsonl）の並びと source の number に持ち、ラベルを読む処理は番号から id を引く。コーパスの source からは分類器の選択（印と同じ）を除いてある
- 並びは対象ごと（ワークフローの順）で、対象の中は人に見せる文（選べる選択肢と状態文書）の SHA-256 の順。同じ実行の項目が続く所は、同じ対象の中の別の項目と入れ替えて無くす。材料の文は、項目の (scope, 対象, 選択肢, 印を除いた状態文書) と、どの項目が同じ実行のものかだけで決まり、印のクラス、id、出どころ、渡す順を変えても同じ文になる（テストで確かめる）
- 分量（見せ方だけで減らし、記述と状態文書の中身は変えない）: 選択肢の記述は対象の節の頭に一度だけ示し、項目には選べる選択肢の id だけを示す。対象の項目の過半（二つ以上）で同じ区切り（「## ファイル …」と「## 記憶 …」）は、節の頭に一度だけ示し、項目の状態文書では見出しに「（共通）」を付けて分類器が見た順の位置に示す（すべての項目で同じ区切りに限ると、acceptance の 24 項目のうち一つだけ違う実装の変種の repo/src/shopcart/discount.py が 24 回並ぶ）。印だけの行（印を除くと空か「#」だけになる行）は落とし、区切りの間の空行は一つにした。共通の区切りを戻すと、印を除いた状態文書に戻る（テストで確かめる）。156,390 文字（往復 13、49 項目）から 100,276 文字（66 項目）になった。66 項目のすべてに選択肢の記述と状態文書の全文を並べた形（231,447 文字）の 43%
- 読み方（H-L3）: 方針（分類器と同じ立場で、記述を字義どおりに読み、状態文書から判断できることだけで選ぶ。記述が中身の条件を書いていれば中身を確かめ、書いていなければ確かめない。記述の括弧の中の列挙は記述が書いた範囲として読む。迷ったら unknown を選び理由を添える）と、事実（「（なし）」などの置き書きは空の節。戻りの後の intake.md には持ち帰った問いと回答が入る。goal が選択肢に無い時は goal に優先する文は働かない。印を除いた跡に意味は無い）を冒頭に書いた
- ラベルの読み取り（H-L5）: `uv run python -m software_factory.labeling labels --labeler <名前>` は、全角のコロン（「ラベル：」）と ` で囲んだ id も読む。読めないラベル、選べる選択肢に無い id、「ラベル:」の行の無い項目は、項目の番号を添えた誤り（終了コード 2）にし、ラベルのファイルを書かない。「ラベル:」の後が空で次の行に文がある時は、項目の番号を添えて警告し、その項目を空として数える。`uv run python -m software_factory.labeling compare` で `oracle_report(MarkerClassifier(), corpus, labels)` と、印と食い違う項目（番号と id）を出す。ラベルのファイルが無い間、compare はそのことを報告して 1 で終わる

tests/test\_labeling.py が、材料が試しの実行（とシナリオ）から作り直したものと一致すること、66 の組をすべて一つずつ含むこと、訪問 2 以降を見る対象が workflow.yaml の memory\_in から決まること、design、plan\_tasks、architecture のゲート、implement の訪問 2 以降が訪問 1 と同じ状態文書であること、上の人に渡す形、ラベルの読み取りと比べ方、代表の前提（下の二つ）を確かめる。人が手で書くのは human-labeling.md の「ラベル:」の行だけで、埋めた後もテストは通る（「ラベル:」とその後を空にして作り直したものと比べる）。代表、ペルソナ、記述を変えたら `uv run python -m software_factory.labeling write` で作り直す。write は埋めた「ラベル:」を空にし、項目の id は実行記録の内容のハッシュから決まるので変わりうる。ラベルを受け取った後に作り直す時は、ラベルを付け直す範囲を決めてから。

**代表の前提（往復 14。docs/review-findings.md の H-L6）。** review の changes\_requested の代表の指摘を、前提が事実に合うものに直した（記述は変えていない）。前の指摘「Cart.total が parse\_code の ValueError をそのまま上げており、呼び出し側が無効なコードと数量の誤りを区別できない。専用の例外にする」は、数量の ValueError を出すのは Cart.add で Cart.total ではなく、前提が事実と合わなかった（専用の例外にすることも、REQ-3 と design.md が決めた ValueError を変えるので、design.md を変えずに解消するとは言いにくかった）。今の指摘は「test\_invalid\_codes\_are\_rejected は無効なコード（PCT0、PCT51、XYZ、OFF）を parse\_code に直接渡すだけで、Cart.total に無効なコードを渡した時に ValueError で拒むこと（REQ-3）を確かめていない。Cart.total で確かめるテストを足す」（path は repo/tests/test\_discount.py、修正を要する）で、記憶 review\_findings も同じ（tests/stochastic.yaml）。review に届く単体テストの代表（unit\_test の goal になる ok と defect\_passed）のどちらでも事実で、repo/tests/ の修正で解消する（design.md は変えない）ことをテストで確かめる。acceptance の requirement\_unmet の代表は直していない（上の「まとめ方」。主経路の実装でだけ成り立つことと、その組を材料から外したことをテストで確かめる）

## 人間のレビューで確かめてほしいこと

人間が往復 8 の後のこの節と完了判定の二回目が渡した事項に回答し（docs/review-findings.md の F。往復 10 で対応）、往復 10 の後に第三者が二度確かめたうえで決めた（同じく G。往復 11 で対応）。

### 決まったこと（人間の回答と決定）

1. **plan\_tasks の design\_incomplete は残す。** 記述は変えない。確率的な本体に代表を置かず、E2E のカバレッジの注入で踏む今の形のまま
   - 判断の材料として直したこと: 往復 8 のこの節の「design\_incomplete は、design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」は言い過ぎだった。記述の上では、design の goal を正しく満たした後でも、implement の task\_unclear（タスクの paths の外のファイルを変えないと実装できない）で plan\_tasks に戻り、そのファイルが design.md の「## 構成」に無いと分かる経路で、design\_incomplete は起きうる
   - 確率的な本体に代表を置かない理由はそのまま: クラスは (ステージ, 訪問の区分) と種だけで選ぶので、代表は、その区分に届きうるすべての上流の成果物と整合しなければならない。design の goal の代表の design.md はすべての要件を構成のファイルに割り当てていて、plan\_tasks の訪問 1 と、design から next で入り直した訪問は、paths の外のファイルについての問いを持たない（この例の implement の task\_unclear の代表の問いも、割引の適用の単位で、paths の外のファイルではない）。上流の goal の代表と両立しない（tests/stochastic.yaml の注記）
   - 往復 10 で、この辺（carry design\_issues、max 2）を通るシナリオ plan\_tasks\_design\_incomplete\_rollback を足した（F-3）。design が要件への問いを残すが分類の確信度が低く unknown になり、運用者が goal 到達扱いで続行する。plan\_tasks は、その design.md の「## 構成」に REQ-3 と REQ-4 を受け持つ構成要素が無いことを記憶 design\_issues に書いて design に戻り、空でない design\_issues が design の訪問 2 の開始時スナップショットに届く（expect.starts）。代表（tests/fixtures/plan\_tasks/incomplete/）は上流の design/gap と組むので、記述と食い違わない（上の「記述と代表の整合」）
2. **利用者役が変えた記述は承認。** 往復 8 の unit\_test の goal（「## テストへの依頼」のすべてを確かめる）と assurance のゲートの goal（判断は verification.md と review.json に基づく）、往復 6 の end\_state の範囲の拡大
3. **ペルソナの設計は承認。** 三人とも要件の値（利用者と入力の場所、コードの形と上限、割引額の切り捨てと 0 円の下限、無効なコードの扱い）を答え、曖昧さは analyze が尋ね返す問い（キャンペーンの後も使えるか、同じ購入者が何回使えるか）でだけ入る
4. **unit\_test の tests\_defective の分割は取り消す（往復 11 の人間の決定）。** 往復 10 で、テストの不備（誤っているテスト）を end\_state tests\_defective として tests\_insufficient（足りないテスト）から分けたが、二つは戻り先が同じ（unit\_test 自身）で、違いは集計の都合（分けて数えたい）だけだった。end\_state のクラスは下流の振る舞いに関する同値類で、集計のための分類ではない（adopting.md 第13節）
   - unit\_test（description、artifacts の memory\_in と memory\_out、goal、end\_state、rollback）と construction のゲートの goal は、往復 10 の前の文（人間が承認した文）に一字も変えずに戻した（`git diff 08f79b4 -- examples/software-factory/workflow.yaml` が空）。記憶 test\_defects、tests\_defective の rollback、test\_report.md の「## 不備」は無くなり、節は「## テスト」「## 失敗」「## 未網羅」の三つ
   - テストの不足と不備は、前と同じく tests\_insufficient と一つの記憶 coverage\_gaps で扱う（要件に反する期待を持つテスト、lint の違反、tests に無いファイルの変更は不備として「## 未網羅」と coverage\_gaps に書く）
   - 利用者役が往復 10 で足した句（テスト自身の誤り（準備、呼び出し、import）で失敗するテスト）も入らない。そうした失敗は、前と同じく unknown（人に戻す）になる
   - 不足と不備を分けて数えることは、記述を変えずに coverage\_gaps の項目の書き方で区別してよい（第13節。必須ではない）。この例ではしていない（数える使い道が今は無いので、偽の本体の記憶の値は往復 10 の前のまま）
   - 代表 tests/fixtures/unit\_test/defective/（REQ-2 の 0 円の下限に反して、小計 300 円に OFF500 で -200 円を期待するテスト。どちらの実装の系統でも実在の pytest で落ちる）は、tests\_insufficient の確率 0 の代表として残した。往復 10 の前の tests\_insufficient には、要件に反する期待を持つテストの代表が無かった。不備は「## 未網羅」と記憶 coverage\_gaps に書き、「## 失敗」は（なし）にした（「## 失敗」と記憶 failing\_tests は、repo/src/ の欠陥を示した失敗の証拠で、impl\_defect の条件になる）。分布テストの分布には置かないので、分布、設計値、基準は変わらない。シナリオ unit\_test\_defective\_self\_rollback が、tests\_insufficient で空でない coverage\_gaps を持って unit\_test に戻り、それが訪問 2 の開始時スナップショットに届くことを確かめる（expect.starts）
5. **主経路が REQ-1 に反するコードをリリースすること（玩具の意図）は、読んだうえで良い。** markov の goal の実装（ok、ok\_b）は小計 333 円に PCT10 で 299 円にする（割引額の切り捨てなら 300 円）。受け入れ基準と単体テストの ok の代表はこの場合を確かめないので、主経路はこの既知の欠陥を持ったままリリースする
6. **往復 10 で代表を変えた所は、人が印を除いて読んでラベルを付ける（全部の付け直しはしない）。** 材料は docs/human-labeling.md の 66 項目（上の「記述と代表の整合」。往復 12 で選び方を手引き第15.1節の目安に合わせて 30 項目から 45 項目に、往復 13 で改められた目安に合わせて review を足し 49 項目に、往復 14 で差分の確かめ（review-findings.md の H）を受けて 66 項目にした）

### まだのこと

- 第15.1節の人手のラベル（人間がする）。材料は docs/human-labeling.md（66 項目）。受け取ったら examples/software-factory/ で `uv run python -m software_factory.labeling labels --labeler <名前>` と `uv run python -m software_factory.labeling compare` で印と比べ、食い違いがあれば代表か記述を直す（記述を直すのは人間の承認の後）

### 第三者の事前レビューの低（往復 11。review-findings.md の G-5）への対応

- **戻った直後の開始時スナップショット:** test\_every\_rollback\_edge\_is\_taken の docstring の主張が、三本（unit\_test → unit\_test、review → implement、release → release）で成り立っていなかった。三本のシナリオ（construction\_rollbacks、assurance\_gate\_rolls\_back、release\_notes\_self\_rollback）に、戻った直後の訪問の expect.starts を足した。定義の上のロールバックの辺 12 本のすべてについて、どれかのシナリオが戻った直後の訪問の expect.starts で carry する記憶を空でない値で期待することを、test\_every\_rollback\_edge\_has\_its\_carry\_checked\_at\_the\_next\_start で確かめる
- **誘発の目標は誘発で踏む:** test\_coverage\_plan\_reaches\_every\_stage\_class に、誘発の台本を与えた目標の計画の項目がすべて induce であることを足した
- **plan\_tasks/incomplete:** 上の「記述と代表の整合」に、シナリオで分類器が見る状態文書を記述だけで読んだことを書いた
- **1.674:** tests/expectations/markov.yaml と markov\_gated.yaml の注記を 1.673（厳密な値 1.67349）にした

### 完了判定の二回目の指摘（低）への対応（往復 10）

- **F-L1 注記の数字:** 直した。markov.yaml の release の訪問 1 は「両側 3.21 SE（規則の 3.2 SE をわずかに上回る）。誤って落ちる確率は正規近似で約 0.13%」、mean\_visits は visits\_variance 1.358、標準偏差 1.165、markov\_shifted.yaml の mean\_visits [1.95, 2.50] は 4.7 SE（4.745）、software\_factory/design.py の docstring の visits\_variance は手引き第12節の言い方に。指摘の外で、markov\_gated.yaml と markov\_gated\_shifted.yaml の SE の倍数の丸めを四捨五入に揃えた（3.45 → 3.5、3.55 → 3.6、5.75 → 5.8）。基準の値はどれも変えていない
- **F-L2 絞った独立性の確かめ:** 直した。markov の stage:implement=goal の訪問 1 → 1（tests/test\_independence.py）と、入り方の検定の implement（tests/test\_e2e.py）を、「判定でき、p 値が 0.001 以上」で確かめる。同じ形の intake のペルソナの代表の確かめも同じにした。`HTF_RUNS` や種を変えると落ちうることを tests/README.md に書いた
- **F-L3 (1) discovery のゲートの「利用者」:** 代表の側で直した。analyze の goal の代表（と needs\_unclear の代表）の requirements.md から「## 利用者」の節を外し、REQ-3 を「購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む」にした（受け入れ基準のある要件の文）。design の goal の代表の「## 対応」の REQ-3 に、画面は repo/ の外で、コードを文字列で受け取ることを書いた（要件の画面の部分を構成要素に割り当てていないと読まれないように）。acceptance の requirement\_misread の代表の参照も REQ-3 にした。discovery の goal の記述は変えていない
- **F-L3 (2) vague\_founder の「端数は切り捨て」:** 「割り引く額の端数は切り捨て」にした
- **F-L3 README の表:** 「フェーズゲートの落ち方」の定性の条件を、workflow.yaml のフェーズの goal の文に合わせた（assurance の判断の範囲を含む。construction の文は、往復 11 で往復 10 の前の文に戻したので、表もそれに合わせた）

### 提案（人間の承認を待つ）

今は無い。往復 10 の提案（tests\_defective を確率的な実行にも出す）は、分割の取り消しで要らなくなった。

## 確率的な本体の仕掛け

- carry を受けた再進入で分布が変わる: release は、記憶 missing\_notes を受けたかで分布を選ぶ（goal 0.75 → 0.97）。release に戻る辺は自分自身への一本だけで、運用者が中止で答える実行では「訪問 2 以降」と一致する
- クラス内で下流の分布が分かれる: divergent では、implement の goal の二つの変種のうち ok は REQ-1 の割引額の切り捨てを誤り、ok\_fixed は正しい。unit\_test の変種 defect のテストは、実在の pytest で ok では落ち（impl\_defect）、ok\_fixed では通る（goal）。markov では二つ目の変種が ok と同じ誤りを持つ ok\_b なので分かれない。divergent では acceptance の requirement\_unmet の代表（REQ-1 の誤りを述べる）が ok\_fixed の後にも出て、その組は代表がコードと食い違う。独立性検証のための本体として許し、分布テストの基準、オラクル、人に渡す材料には使わない（上の「記述と代表の整合」）
- intake は、種から選んだペルソナに尋ね、回答で intake.md を書く。ペルソナごとの intake.md は intake の goal の違う代表になるが、下流は変えない
- 分布に置かない代表: unit\_test の defective（tests\_insufficient の二つ目の代表。要件に反する期待を持つテスト）は tests/stochastic.yaml の variants にあるが、分布テストの分布（markov、divergent）には置かない（確率 0）。シナリオ unit\_test\_defective\_self\_rollback と、人がラベルを付ける材料の試しの実行（profiles の labeling）だけが写し、test\_metrics.py が実在の指標を確かめる。plan\_tasks の design\_incomplete は変種も置かず、代表 tests/fixtures/plan\_tasks/incomplete/ はシナリオだけが写す（E2E のカバレッジでは注入で踏む。人がラベルを付ける材料には、そのシナリオで分類器が見る状態文書を項目にした）。確率的な実行で踏まない (ステージ, クラス) は、plan\_tasks の design\_incomplete だけ
- profiles の labeling は、人がラベルを付ける材料（docs/human-labeling.md）を作る試しの実行の分布で、分布テスト、独立性検証、マルコフ合成には使わない。材料の対象の各クラスが少ない実行で出るように寄せる（往復 13 で、review の訪問 1 にも四つのクラスを置いた。往復 14 で implement に全クラスを置き、analyze の訪問 1 の needs\_unclear を増やした。480 回）
- ゲートの分布: markov の実行のゲートはいつも goal。もう一つの実行の集まり（tests/expectations/markov\_gated.yaml）では、assurance のゲートを、実行の種で組み立てた RandomGateClassifier が成果物によらず 0.2 の確率で changes\_requested にする（review の goal の時にも書く review\_findings を持って implement に戻る）。ゲートの答えが代表によらないので独立性検証は違反を出さず、ゲートの分布を足した設計値のモデルの予測が実測と合う

## 通したランナー

| ランナー | テスト |
| --- | --- |
| 整合性検査 | tests/test\_definition.py |
| 契約適合テスト（パッケージに同梱した全シナリオ。参照ランタイムを使うので必須ではなく、版の確認として） | tests/test\_conformance.py |
| 遷移の決定論テスト（17 シナリオ、遷移の六種、定義の上のロールバックの辺 12 本のすべてと、それぞれで戻った直後の開始時スナップショットの carry、escalate の四択、記録再生、ペルソナの束縛） | tests/test\_scenarios.py |
| 分布テスト（expectations。ゲートを揺らす実行を含む） | tests/test\_stochastic.py |
| 独立性検証 | tests/test\_independence.py |
| E2E のカバレッジ（ペルソナを束縛）とマルコフ合成（ゲートの分布を含む） | tests/test\_e2e.py |
| 偽の分類器によるオラクル検証 | tests/test\_oracle.py |
| 記述と代表の整合（第15.1節）: 人がラベルを付ける材料と、ラベルを印と比べる仕組み | tests/test\_labeling.py |
| トリアージの一周 | tests/test\_triage.py |
| 指標とフィクスチャの整合、ユーザーシミュレータ | tests/test\_metrics.py、tests/test\_personas.py |
