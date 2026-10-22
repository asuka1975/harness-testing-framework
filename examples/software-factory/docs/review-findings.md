# 検証役の指摘（workflow.yaml の事前レビューと、分布テストの基準の確認）

人間が workflow.yaml をレビューする前に、第三者の検証役が二つの確認をした。指摘を、公開の文書（adopting.md、契約、スキーマ、公開 API の文書）とこの例自身の語だけで書き直したものをここに置く。

- workflow.yaml の事前レビュー: 直してから人間に出すべき（高 2、中 8、低 9）
- 分布テストの基準の確認: 承認（中 2、低 4）。基準の中心、E[n]、標準誤差は独立な計算と一致した

高と中は直す。低は任意（直すか、直さない理由を adopting-gaps.md か README に書く）。分類体系の変更（end\_state の追加・分割・統合）は避け、要る時は提案として書く。

フレームワークの側も、これを受けて手引きを直した（changelog.md の「未公開」の最後の三項目）: adopting.md 第2.1節（memory\_out の記憶は訪問のたびに書く）、第4節（指標の結果を覚える時に異常終了を覚えない）、第12節（割合が 0 か 1 に近い基準の幅）。

## A. workflow.yaml の事前レビュー（高と中）


この節は、workflow.yaml、adopting.md、契約（contract/contract.md）、スキーマの語だけで書いている。

### 高

**1. implement と design の記憶が、持ち帰った古い値のまま分類器に見える**

- 記憶はスナップショットに含まれる（契約 5）。carry で重ねた記憶は戻り先の開始時スナップショットに入り（契約 2.3）、その後のステージにも残る（スキーマの memory\_in の説明「前のステージの memory\_out」）。ステージが memory\_out の項目を書かなければ、状態文書（契約 2.4）の記憶の欄にはその残った値が出る
- implement の description は「タスクの記述が曖昧で実装を決められない時は、その問いを記憶 task\_questions に書いて」としか書いていない。task\_unclear で plan\_tasks に戻ると、次の implement の開始時スナップショットには前の問いが入っている。問いが解けて実装した訪問で task\_questions を書かないと、状態文書に前の問いが出る。task\_unclear の「task\_questions に問いが列挙されていればこの状態とし、goal と quality\_violation に優先する」が記憶だけで成り立ち、task\_unclear に分類されうる。この辺は max 1 なので、そこで escalate（max\_exceeded）になる。参照ランタイムで、前の問いが状態文書に出ることを確かめた
- 同じことが、implement の impl\_violations（quality\_violation で自分自身に戻った後。その後に implement へ戻るたびにも入る）と、design の requirement\_gaps（requirements\_gap か acceptance の requirement\_misread で analyze へ戻った後）で起きる。analyze、plan\_tasks、unit\_test、acceptance、review、release の記憶は「無ければ空の一覧」と書かれているので起きない
- 直し方: implement の task\_questions と impl\_violations、design の requirement\_gaps にも「（無ければ空の一覧）」を書く。task\_unclear の優先の条件を「記憶 task\_questions と impl\_notes.md の『## 問い』の両方に問いが列挙されていれば」にする。impl\_notes.md は implement の writes で、implement の開始時スナップショットには無い（戻りはそのステージかそれより前の開始時スナップショットを復元する）ので、古い値が出ない。偽のステージ本体が記憶を毎回書き、MarkerClassifier が記憶を読まないと、テストではこの問題が見えない

**2. plan\_tasks の goal が、代表の成果物で満たせない**

- plan\_tasks の goal は「各タスクの paths と tests が design.md の『## 構成』のファイルに収まり」を求める。design の「## 構成」は「変えるファイルと役割」で、goal の代表の design.md も repo/src/ のファイルしか挙げていない。一方、代表の tasks.yaml の tests は repo/tests/test\_discount.py である。分類器は記述そのものを選択肢として読む（契約 2.2）ので、goal を選べない。design\_incomplete（タスクにすべての要件を割り当てられない）にも当たらず、unknown になる
- 直し方: goal を「各タスクの paths が design.md の『## 構成』のファイルに収まり、tests が repo/tests/ の下にあり、タスクどうしで paths が重ならない」にする

### 中

**3. implement で指標が落ちた時に当たる end\_state が無い所がある**

- 既存のテスト（tests\_pass）が落ちた時と、repo/src/ の変更が design.md の構成から外れた時は、どの end\_state にも当たらず unknown になる
- quality\_violation は「違反の内容が記憶 impl\_violations と impl\_notes.md の『## 違反』に列挙されている」を条件にする。分類器は指標の値を見ない（契約 2.4 の状態文書はファイルと memory\_out だけ）。本体が違反に気づかずに指標だけが落ちた場合は unknown になる。選ばれても carry が空になる（adopting.md 2.1「戻り先が直すのに使う情報は、記憶に書かせ、その記憶を証拠として記述に書く」）
- 直し方: description に「終える前に、ビルド、既存のテスト、lint、paths に照らした変更の範囲を自分で確かめ、違反を記憶 impl\_violations と impl\_notes.md の『## 違反』に書く（無ければ空の一覧）」と書く。quality\_violation の列挙に「repo/tests/ の既存のテストを落とす」と「design.md の構成から外れている」を足す（既存のクラスの境界を広げる。end\_state の追加ではない）。それでも impl\_violations が空なら unknown になることを、意図として README に書く

**4. unit\_test でテストの側の不備が unknown に落ちる**

- repo/tests/ の lint（lint\_errors）、tasks.yaml の tests の外のファイル（out\_of\_scope\_changes）、要件に反する期待のテストは、impl\_defect にも tests\_insufficient にも当たらない。tests\_insufficient の「行カバレッジが 80% に届かない」は、指標の値を見ない分類器には判定できない
- 直し方: description に、終える前に pytest、行カバレッジ、lint、範囲を自分で確かめて記憶に書くことを足す。tests\_insufficient を「unit\_test 自身が直すべき不足か不備がある（テストの無い受け入れ基準、実行されない箇所、lint の違反、tests に無いファイル、要件に反する期待）」に広げる（境界の変更）。別案として、テストの不備の end\_state を足して unit\_test 自身に戻す方法もあるが、これは分類体系の変更（end\_state の追加）になる

**5. 四つのフェーズゲートの不合格が unknown に落ちることが書かれていない**

- discovery、architecture、construction、delivery の最終ステージの end\_state は、goal の時には空になる記憶を証拠にするので、ゲートでは選ばれない。ゲートの不合格はすべて unknown になる。adopting.md 2.4 の注意に沿った選択だが、workflow.yaml にも README にも書かれていない。四つのゲートの指標は、ステージの goal がすでに満たしていて、goal 到達扱いで続行した後にだけ落ちる
- 直し方: README に「フェーズゲートの落ち方」を書く。end\_state で戻すのは assurance だけ（changes\_requested）であること、ほかの四つは unknown で人に戻ること、ゲートに固有の定性の条件（discovery の回答の反映、architecture の構成とタスクの対応、delivery の review.json との整合）を明記する

**6. review の goal の「paths と tests の変更を見た結果があり」が観測できない**

- review.json は指摘だけを持ち、指摘の無いパスを見たかは書かれない。代表の review.json は一つのファイルへの指摘だけである
- 直し方: review.json の形を `{"reviewed": [パス], "findings": [...]}` にし、goal を「reviewed が tasks.yaml の paths と tests をすべて含み、修正を要する指摘が一つも無い」にする。指標にしてもよい

**7. テストへの修正を要する指摘が unknown に落ちる**

- changes\_requested は repo/src/ の修正で解消する指摘に限られる。review は tests の変更も見るのに、repo/tests/ の修正で解消する指摘はどこにも当たらない。unit\_test は review\_findings を受け取らないので、implement に戻って unit\_test が書き直す時にも指摘が届かない
- 直し方: changes\_requested を「repo/src/ か repo/tests/ の修正で解消する」に広げる（境界の変更）。指摘は、implement が書き unit\_test が読む impl\_notes.md で渡す。implement は持ち帰った review\_findings のうちテストに関するもの（と failing\_tests のテスト）を impl\_notes.md の「## テストへの依頼」に書き写し、unit\_test はそれに応えるテストを書く。unit\_test の memory\_in に review\_findings や failing\_tests を足す方法は、整合性検査が拒む（memory\_in の項目を、carry も前のステージも生成しないため）

**8. changes\_requested が、修正を要する指摘が無くても成り立つ**

- 「修正を要する指摘が、すべて repo/src/ の修正で解消する」は、修正を要する指摘が無い時にも成り立つ。ステージでもゲートでも goal と重なる読みが残る
- 直し方: 「review.json に修正を要する指摘が一つ以上あり、そのすべてが…」にし、ゲートの条件は「フェーズ assurance の評価では、修正を要する指摘が無くても…」と書き分ける

**9. 要件の id の照合が、日本語の文に続く id を数えない**

- design\_covers\_requirements と changelog\_covers\_requirements の実装は、「REQ-1は」「REQ-1の」「REQ-1と」の REQ-1 を数えない。design の description は「## 対応」の行の形を決めていないので、自然な書き方で goal が選択肢から外れる。本体は割り当てたつもりなので記憶に列挙せず、unknown になる
- 直し方: 照合を英数字の境界だけで切る（例 `(?<![A-Za-z0-9_-])REQ-1(?![0-9])`）。design と release の description に行の書き方を決める

**10. クラスの代表の成果物（フィクスチャ）が記述と合わない**

- requirement\_unmet の代表の verification.md は、REQ-2 の要件にも受け入れ基準にも無い振る舞い（コードは一回の支払いに一回）を不合格にしている。記述の上では要件の欠落（requirement\_misread）か unknown である。plan\_tasks の unknown の代表の tasks.yaml は、記述の上では goal を満たす
- MarkerClassifier は成果物の印を読むので、テストはこの食い違いを捕まえない。分類器の検証（adopting.md 第15節）のラベルに使うと、ラベルが記述と食い違う
- 直し方: requirement\_unmet の代表を、要件の記述に反する振る舞いにする。たとえば支払額を切り捨てる実装は REQ-1（割引額の 1 円未満は切り捨てる）に反し、小計 333 円に PCT10 で 299 円を返すが、単体テストがこの場合を確かめなければ acceptance で初めて見つかる。あわせて requirement\_unmet の「受け入れ基準に反する」を「要件の記述か受け入れ基準に反する」に広げる。plan\_tasks の unknown の代表を、goal にも design\_incomplete にも当たらない成果物（例: タスクどうしで paths が重なる）にする

## B. 分布テストの基準の確認（中）


基準（tests/expectations/ の三つ）は、設計値から正しく導かれている。中心、E[n]、標準誤差は、`synthesize` の `evaluations`、`visit_outcomes`、`visits_variance` と独立な計算の両方と一致した。基準はそのまま使える。次の二点は改善として勧める。

### 1. release の訪問 2 以降の goal の基準 [0.90, 1.0] は、正規近似の幅が合わない

- p = 0.97、条件に合う評価の数の期待値 E[n] = 65.1 なので、外れる側の期待件数は約 2 件しかない。二項分布が歪む
  - 注記の「下側 3.3 SE」なら、落ちる確率は約 0.05% のはず
  - 二項分布で厳密に計算すると約 0.37%
  - markov.yaml 全体で正しい基準のどれかが落ちる確率（約 1.2%）の、3 分の 1 がこの基準から来ている
- `ExpectationReport.lines()` の Wilson の 95% 区間の幅も、約 4 割の実行で基準の幅 0.10 を超える。adopting.md 第12節の読み方では「回数が足りない」にあたる
- 次のどれかにするとよい
  - min を 0.88 にする（落ちる確率 0.06%、ほかの基準と同じ水準。markov_shifted.yaml の [0.65, 0.85] とは重ならない）
  - runs を 800 にする
- 一般に、E[n]·min(p, 1−p) が小さい（目安として 10 未満）基準は、標準誤差の倍数ではなく、二項分布の裾の確率から幅を決める

### 2. 例の指標が、ツールの異常終了の結果を覚えてしまい、一度の環境の不調で正しい基準が落ちる

- software_factory/metrics.py は、ツールの結果を指標名、引数、内容のハッシュで覚える。adopting.md 第4節が許す使い方だが、子プロセスが異常終了した時の値も覚える
  - たとえば `build_passes` と `tests_pass` は、終了コードが 0 でなければ False を返して覚える
  - メモリの逼迫などで一度でも異常終了すると、同じ内容の評価はその後ずっと goal が選択肢から外れ、印の goal が unknown になる
- 実際に、markov_gated.yaml の既定の種で、ほかの検証と同時に走らせた一回の実行が、四つの基準のうち三つで落ちた（完了 0.265）。同じ種の実行は、基準をかけたほかの 6 回（tests/test_stochastic.py を含む）すべて通った
- 子プロセスを一度だけ異常終了させると、同じ形の失敗（markov.yaml で完了 0.258、12 個のうち 5 個が通らない）を再現できた
- 次の二つを直すとよい
  - 指標: 終了コードが負、シグナル、時間切れの時は、結果を覚えずに `MetricError` を上げる。意味の決まった終了コード（0 と 1 など）の結果だけを覚える
  - 検査: 分布テストに使う実行の集まり（ゲートを揺らす集まりも含めて）で、次が一つも無いことを確かめる
    - 本体の例外
    - 指標の測定の失敗
    - tests/stochastic.yaml の metrics_fail が空の変種（印が goal）なのに goal が選択肢から外れた評価
  - 今の test_bodies_keep_the_contract は、ゲートを揺らさない集まりの例外と警告しか見ないので、この失敗を見分けられない

## C. workflow.yaml の事前レビュー（低、任意）


#### L-1 analyze の requirement\_count の min 3 は、要件分析の基準として不自然

依頼によっては要件が一つか二つで足りる。その時は goal が選択肢から外れ、needs\_unclear（問いが要る）にも当たらず unknown になる。この依頼では四つになるので動くが、手本として読む人は誤解する。min 1 にするか、README に「この依頼に合わせた値」と書く。

#### L-2 持ち帰った記憶への対応が、戻り先の goal で観測できず、連鎖で失われる

- intake は持ち帰った intake\_questions を尋ねるが、memory\_in は状態文書に入らない。尋ねたかを goal で判定できない。intake.md に「## 持ち帰った問い」の節を設け、goal に「その節の問いにすべて回答がある」を足すと観測できる
- acceptance → analyze（requirement\_gaps）→ needs\_unclear → intake → analyze と連鎖すると、intake の開始時スナップショットには requirement\_gaps が無いので、再び analyze に来た時には消えている。依頼に根拠の無い食い違いは依頼者に尋ねるしかない（analyze の goal は根拠を求める）ので、これが想定の経路である。analyze の description に「持ち帰った食い違いを依頼者に尋ねる時は、その内容を intake\_questions に含める」と書いておくとよい

#### L-3 quality\_violation の「paths に無いファイルを変えている」は差で、分類器には見えない。paths が狭すぎる場合の行き先も決まっていない

分類器は repo/src/ の今の内容しか見ず、どれが変わったかは分からない（既存の \_\_init\_\_.py はどのタスクの paths にも無い）。指標と impl\_violations が頼りなので、記述は「…変更の範囲の違反が記憶 impl\_violations に列挙されている」を主にする書き方がよい。また、tasks.yaml の paths が狭すぎて実装できない時は、implement 自身へ戻しても直らない。description に「paths の外のファイルを変えないと実装できない時は、変えずに task\_questions に書く（task\_unclear）」と書く。

#### L-4 blocking\_findings が真偽値でない blocking を数える

`if f["blocking"]` は文字列の `"false"` も修正要と数える。真偽値でなければ MetricError にする。

#### L-5 changelog\_covers\_requirements は CHANGELOG.md のどこに id があっても数える

「未対応: REQ-3」のような行でも REQ-3 を載せたと数える。最新の版の見出しの下だけを数えるか、description に書き方を決める。

#### L-6 release がパッケージの版を上げず、版を上げ忘れると unknown になる

release は repo/ を書かないので、リリースした repo/src/shopcart/\_\_init\_\_.py の \_\_version\_\_ は古い版のままで、release.json の版と食い違う。実際のリリースとしては不自然である。release.json を「リリースの記録」として版の更新を範囲外にするなら、README に書く。含めるなら、release の writes に \_\_init\_\_.py を足し、version\_bumped を view.baseline() と比べる形にする。また、版を上げていない状態は notes\_incomplete に当たらず unknown になる。自分で直せる不足なので、notes\_incomplete の記述に含めてもよい（境界の変更）。

#### L-7 design が全要件を割り当てたうえで問いを残すと unknown になる

暫定の解釈で割り当て、「## 要件への問い」にも書くのは自然な振る舞いである。goal（問いが無い）にも requirements\_gap（割り当てていない）にも当たらない。requirements\_gap を「割り当てていないか、割り当てたが『## 要件への問い』に問いがある」に広げ、「goal に優先する」を書く（境界の変更）。

#### L-8 戻りで成果物が捨てられることを前提にした書き方が無い

- impl\_defect → implement は implement の開始時スナップショットを復元するので、欠陥を見つけたテストも捨てられる。unit\_test は failing\_tests を受け取らないので、書き直す unit\_test はそのテストを回帰テストとして書き直せない。unit\_test の memory\_in に failing\_tests を足す案は、整合性検査が `memory_unsupplied` で拒む（複製の上で確かめた。failing\_tests は unit\_test 自身の memory\_out で、carry は implement にしか運ばない）。M-5 と同じく、implement が「持ち帰った failing\_tests のテストを impl\_notes.md の『## テストへの依頼』に書き写す」形にする
- review や acceptance から implement へ戻ると、implement は実装前のコードから書き直す。持ち帰る記憶（review\_findings、unmet\_requirements、failing\_tests）は、捨てられるコードの行番号ではなく、パス、関数、期待する振る舞いで書くべきである。また implement の開始時スナップショットには、前の carry の記憶も残っている。コードを一から書き直すので、古い指摘もまだ有効である。これらを README か各 description に書いておくと、本体を作る人が誤解しない

#### L-9 冗長な指標と曖昧な文

acceptance の tests\_pass は unit\_test の goal と construction のゲートが保証しており、強制通過の後にしか落ちない。delivery の goal の「review.json の結果に合い」は、何と何が合うのか分からない（修正要の指摘が残っていない、のことなら assurance のゲートがすでに保証している）。construction の goal の「repo/ の変更全体」は分類器には見えず、out\_of\_scope\_changes だけが判定する。

## D. 分布テストの基準の確認（低、任意）


**L1 ずらした基準 analyze needs_unclear [0.0, 0.17] が、正しい [0.17, 0.33] と端 0.17 を共有する**

- 観測値がちょうど 0.17 なら、正しい基準もずらした基準も通る。確率は 1.6e-10 で実害は無い
- 「すぐ外側」の意図に合わせ、max を 0.16 にするとよい（設計値から 4.1 SE）

**L2 release の訪問 1 の notes_incomplete [0.15, 0.31] は 3.198 SE で、注記の規則「3.2 倍以上をとり、0.01 の単位で外側に丸めた」をわずかに下回る**

- p ± 3.2 SE は [0.14995, 0.31005] で、外側に丸めると [0.14, 0.32] になる
- 落ちる確率は、今の幅で 0.141%、[0.14, 0.32] で 0.034%
- ほかに、注記の倍数に丸めの差がある。acceptance の「3.6」は、正確な SE では 3.54。status_rate の「両側 3.4」は、上側が 3.52
- 幅を規則どおりに直すか、規則の書き方を「およそ 3.2 倍」に改める

**L3 markov_gated.yaml には、ずらした基準が無い。四つのうち二つ（status_rate と mean_visits）は、ゲートを揺らさない本体も通す**

- ゲートを揺らさない本体（完了 0.6885、訪問の回数 1.660）をこの二つにかけると、status_rate は 99%、mean_visits は 57% の確率で通る
- ゲートの分布が効いているかを確かめているのは、ゲートの二つの基準だけ。ゲートの束縛が抜ければ割合が 0 になるので、それは落とせる
- markov_gated の「ずらした基準」を足すとよい。例:
  - ゲートの訪問 1 の changes_requested [0.35, 0.50]（上へ約 5.7 SE）と [0.0, 0.10]（下へ約 3.8 SE）
  - status [0.75, 0.90]（上へ 3.8 SE）
- 注記には、二つの基準が揺らす前後を見分けないことを書くとよい

**L4 test_correct_expectations_follow_the_design は、幅の下限（3 SE 以上）だけを確かめ、上限を確かめない**

- 正しい基準の幅を広げても（たとえば [0.0, 1.0]）、このテストは通る。ずらした基準は固定の値なので、正しい幅とずらした幅が重なっても気づかない
- 幅が 5 SE 以下であること、または正しい幅とずらした幅が重ならないことも確かめるとよい

## E. 完了判定の指摘（往復 7 の後）

第三者の検証役が F4 の完了を判定した。完了の条件はすべて満たし、読取の制限も守られているが、例の側に直すべき点が中 2、低 6 ある。中は直す。低は任意（直すか、直さない理由を README か adopting-gaps.md に書く）。

### 中

**E-M1. 記述と代表の成果物の食い違い（README の「記述と代表の整合（試しのラベル）」の三つ）が直されていない**

検証役も同じ食い違いを確かめた。

1. acceptance の requirement\_misread の代表（tests/fixtures/acceptance/misread/verification.md）の「依頼と intake.md はレジの画面で入力する前提」は、precise\_pm の回答にしか無く、feature\_request.md にも無い。記述どおりに読む分類器では、vague\_founder と terse\_engineer の実行で unknown になる
2. plan\_tasks の design\_incomplete の代表（tests/fixtures/plan\_tasks/incomplete/tasks.yaml）の「構成に REQ-3 と REQ-4 を受け持つ箇所が無い」は、plan\_tasks がいつも読む design の goal の代表の design.md（REQ-3 は parse\_code、REQ-4 は Cart.total）と矛盾する。いつも unknown になる
3. analyze の goal の代表（tests/fixtures/analyze/ok/requirements.md）の「nn は 1〜50」は、vague\_founder の「上限はまだ決めていない」と矛盾する。vague\_founder の実行で unknown になる
4. あわせて、REQ-2 の「支払額は 0 円を下回らない」は、最初の訪問ではどのペルソナの回答にも根拠が無い（その点を尋ねる問いは needs\_unclear の変種だけが持ち帰る）

どれも、分類器の検証のコーパスのラベルとも食い違う（手引き第15.1節）。クラスの選び方は種だけで決まるので、成果物の中身を直しても分布テストの数値は変わらない。

- 直し方の案:
  - (1) 食い違いを依頼から言える点にする（たとえば「10% 引き」の書き方の揺れを要件が扱わない）か、全ペルソナの回答に前提を入れる
  - (2) design の goal の代表の design.md でも、本当に割り当てられない点を代表にする
  - (3) analyze の goal の成果物をペルソナごとに用意する（種でクラスを選んだ後に、intake.md の回答に合う成果物を写す）か、vague\_founder の回答を値の決まったものにする
  - REQ-2 の下限は、回答に根拠を持たせるか、goal の代表から外す
  - 分類体系は変えない

**E-M2. discovery のゲートの goal を、goal の代表がどのペルソナでも字義どおりには満たさない**

- discovery の goal の qualitative は「intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映されている」を求める
- 一方、goal の代表の requirements.md は、利用者に一言も触れない（precise\_pm の「ネットショップの購入者。レジの画面でコードを入力する」、terse\_engineer の「購入者」が反映されない）。vague\_founder では「上限はまだ決めていない」も反映されず、要件の「nn は 1〜50」と食い違う
- ゲートの状態文書は intake.md と requirements.md を含む（契約 2.4）。ゲートの選択肢は goal、needs\_unclear、unknown で、needs\_unclear は goal の時に空の intake\_questions を証拠にするので選ばれない。記述どおりに読む分類器では、主経路が毎回このゲートで unknown になる（「反映」を緩く読めば precise\_pm と terse\_engineer では満たしうるが、vague\_founder では満たさない）
- 第15.1節の試しがステージの項目だけだったので見つかっていなかった。手引き第15.1節は、ゲートの項目も含めるように直された
- 直し方の案:
  - 代表の側を直す: requirements.md に利用者（と入力の場所）を書く節を設け、goal の代表に書く。これは成果物の直しで、人間の承認は要らない
  - 記述の側を直す（discovery の goal から「利用者」を外す、または要件にしない回答の置き場を決める）のは記述の改訂なので、人間のレビューで承認を受ける。直すなら提案として README に書く
  - vague\_founder の食い違いは E-M1 の (3) と一緒に直す
  - ゲートの項目も、第15.1節の手順で試しのラベルを付けて確かめる

### 低（任意）

- **E-L1:** markov では goal の実装が二つとも REQ-1 の切り捨てを誤る（333 円に PCT10 で 299 円）。そのため、完了した実行はいつも REQ-1 の記述に反するコードをリリースし、acceptance/ok は REQ-1 を合格とする。記述（表がすべて合格）には合っているが、assurance のゲートの「repo/ をこのままリリースしてよい」は、repo/ を読む分類器には満たさないと読まれうる。直し方の案: ゲートの判定の範囲が「verification.md と review.json に基づく」ことを記述に書くか、README に意図（玩具の主経路は既知の欠陥を持つ）として書く
- **E-L2:** tests/test\_scenarios.py の docstring は「フェーズ境界越えは五通り」とあるが、定義の上の越境は六本ある。acceptance→analyze（requirement\_misread）は決定論のシナリオでは通らない（E2E のカバレッジで踏む）。直し方の案: docstring を直し、requirement\_misread で analyze に戻るシナリオを一本足す
- **E-L3:** unit\_test の goal に「impl\_notes.md の『## テストへの依頼』のすべてに応えるテストがある」が無いので、依頼を無視したテストでも goal に分類される。直し方の案: goal に足す（unit\_test は impl\_notes.md を読むので観測できる）
- **E-L4:** tests/test\_oracle.py の揺れる分類器のテストは、一致率を `approx(0.75, abs=0.05)` で確かめている。値は 95/127 に決まる。直し方の案: `1 - ceil(len(corpus) / 4) / len(corpus)` と一致することを確かめる
- **E-L5:** 本体が memory\_out を毎回書くことを、本体の振る舞いではなく設計値の表（tests/stochastic.yaml）でだけ確かめている。空の記憶を書かない変更をしても、テストが落ちない。直し方の案: 分布テストの実行の集まりで、各評価の終了時スナップショットの記憶が、そのステージの memory\_out をすべてその訪問の値で持つことを確かめる
- **E-L6:** markov とゲートを揺らす実行の全状態に violated が無いことを、補正の無い alpha 0.01 の検定 5〜7 個で求めている。既定の種では通るが、種か回数を変えると、正しい本体でも数 % の確率で落ちる（`entry_dependence` は、markov の 20 通りの種の基点で 1 回、ゲートを揺らす実行の 12 通りで 1 回 violated になった）。直し方の案: 確かめる状態を絞る（仕込んだ所と、入り方の多い implement だけ）か、多重性を見込んだ alpha にする。「HTF\_RUNS を増やすと偶然に落ちうる」ことを注記する

## F. 人間のレビューの回答と、完了判定の二回目の指摘

人間が README の「人間のレビューで確かめてほしいこと」と、完了判定の二回目（正常）が人間に渡した事項をレビューした。回答と、それに合わせて直すことをここに置く。完了判定の二回目の指摘は低だけで、ここに公開の文書の語で書き直した。

### 人間の回答

1. plan\_tasks の design\_incomplete は**残す**。記述は変えない。確率的な本体に代表を置かず、E2E のカバレッジの注入で踏む今の形のまま
2. 利用者役が変えた記述（往復 8 の unit\_test の goal と assurance のゲートの goal、往復 6 の end\_state の範囲の拡大）は**承認**
3. ペルソナの設計（三人とも要件の値を答え、曖昧さは analyze が尋ね返す問いでだけ入る）は**承認**
4. 分類体系の提案（unit\_test のテストの不備を、end\_state tests\_defective として tests\_insufficient から分ける）を**採る**
5. 主経路が REQ-1 に反するコードをリリースすること（玩具の意図）は、**読んだうえで良い**

まだ答えが無いもの: 第15.1節の手順で人がラベルを付け直すこと。これは人間がする（人手のラベル）。

### 直すこと

**F-1. unit\_test に end\_state tests\_defective を足す（分類体系の変更。人間が採った）**

- 今の tests\_insufficient は「不足か不備」をまとめている。これを分ける
  - 不足（tests\_insufficient に残す）: requirements.md の受け入れ基準のうちテストの無いもの、repo/src/ の実行されない箇所（行カバレッジが 80% に届かない）、impl\_notes.md の「## テストへの依頼」のうちテストの無いもの
  - 不備（tests\_defective）: テストが誤っている。repo/tests/ の lint の違反、tasks.yaml のタスクの tests に無いファイルの変更、requirements.md の要件に反する期待を持つテスト
  - 上の振り分けは README の提案に沿った案で、境界は利用者役が決めてよい。決めた境界と理由を README に書く
- tests\_defective の戻り先は unit\_test 自身（自分自身へのロールバック）。carry、記憶の名前、max は利用者役が決める。不足と不備を分けて数えられるように、持ち帰る記憶と test\_report.md の節を分けるかも決める
- 二つが同時にある時の優先、impl\_defect との優先を記述に書き、goal、impl\_defect、tests\_insufficient、tests\_defective、unknown が MECE になるようにする。unit\_test の description（何を記憶に書くか）も合わせる
- 確率的な本体の今の tests\_insufficient の代表（フィクスチャ）のうち、新しい境界では不備に当たるものがあるかを確かめる
  - あれば、その変種を tests\_defective に移す。分布が変わるので、tests/stochastic.yaml、設計値のモデル（software\_factory/design.py）、expectations の基準と注記を導き直す
  - 無ければ、確率的な実行には tests\_defective が現れない。E2E のカバレッジで踏み（すべての (ステージ, end\_state) を踏む）、空でない記憶を持って unit\_test に戻るシナリオを一本足す（expect.starts で unit\_test の訪問 2 の記憶を確かめる）
- 第15.1節の試しのラベルを、新しい境界でやり直す（unit\_test の項目）。tests\_defective の代表があれば含める
- README の構成の表、遷移の被覆、「人間のレビューで確かめてほしいこと」を合わせる

**F-2. README に人間の回答を書く**

- 「人間のレビューで確かめてほしいこと」を、回答を受けた形に書き直す（何が決まったか、何がまだか）
- 1（design\_incomplete）には、判断の材料として次の経路を書き足す。記述の上では、implement の task\_unclear（タスクの paths の外のファイルを変えないと実装できない）から plan\_tasks に戻り、そのファイルが design.md の「## 構成」に無いと分かる経路で、design の goal を正しく満たした後でも design\_incomplete は起きうる。今の README の「design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」は言い過ぎなので直す（tests/stochastic.yaml の plan\_tasks の注記も同じ）。確率的な本体に代表を置かない理由（上流の goal の代表と両立しない）はそのまま

**F-3. plan\_tasks から design へ、空でない design\_issues を持って戻るシナリオを足す**

- 今、この辺（design\_incomplete、carry design\_issues、max 2）を通るのは E2E のカバレッジの注入の一回だけで、そこで持ち帰る design\_issues は空の一覧。空でない design\_issues が design の開始時スナップショットに届くことを確かめるテストが無い
- 台本で plan\_tasks を design\_incomplete に分類し、空でない design\_issues を持って design に戻るシナリオを一本足す（expect.starts で design の訪問 2 の記憶を確かめる）

### 低（任意。直すか、直さない理由を README に書く）

- **F-L1. 基準の根拠の注記の数字の誤り。** 基準の値はどれも正しい
  - tests/expectations/markov.yaml の release の訪問 1 の [0.15, 0.31] の「両側 3.6 SE」は 3.21 SE（前の [0.14, 0.32] の時の値のまま）。「3.21 SE（規則の 3.2 SE をわずかに上回る）。誤って落ちる確率 0.135%」のように書く
  - mean\_visits の「visits\_variance 1.360、標準偏差 1.166」は 1.358、1.165
  - tests/expectations/markov\_shifted.yaml の mean\_visits [1.95, 2.50] の「上へ 4.8 SE」は 4.74
  - software\_factory/design.py の docstring の visits\_variance は「一回の実行の中での訪問の回数の分散」のまま。api-reference.md の `Prediction` と手引き第12節の言い方（実行ごとの訪問の回数の、実行の間での分散。一度も訪れない実行は 0 と数える）に合わせる
  - F-1 で基準を導き直すなら、そこで合わせて直す
- **F-L2. implement に絞った二つの独立性の確かめに、多重性の補正が無い。** tests/test\_independence.py の入り方の検定（`entry_dependence`）の verdict が not\_detected であることと、tests/test\_e2e.py の markov の implement=goal の訪問 1 → 1 が not\_detected であることは、補正の無い alpha 0.01 のまま。種の基点を変えて 200 回ずつ試すと、正しい本体でもどちらかが落ちたのは markov の集まりで 8/200（4%）、ゲートを揺らす集まりで 6/200（3%）。docstring は全状態の確かめについてだけ「補正の無い alpha 0.01 で数 % 落ちる」と書いている。直し方の案: 絞った確かめを「violated でない」ではなく「p 値が 0.001 以上」のようにする（仕込んだ所の検出は divergent で p = 0.0005 程度なので、この確かめを厳しくしても検出の確かめには響かない）。または、`HTF_RUNS` や種を変えると数 % の確率で落ちうることを tests/README.md に書く
- **F-L3. 第15.1節の試しで、字義どおりに読むと揺れる点が二つと、README の表の古い行**
  - (1) discovery のゲートの goal は、回答を「requirements.md の要件か受け入れ基準に」反映することを求めるが、利用者は「## 利用者」の節にあり、要件でも受け入れ基準でもない。README の 4 は「requirements.md に反映」と言い換えている。**代表の側で直す**（利用者を、受け入れ基準のある要件として書くなど）。discovery の goal の記述を変えるのは新しい記述の改訂で、人間の承認が要るので、ここでは採らない
  - (2) vague\_founder の「端数は切り捨て」は何を切り捨てるかを言わず、REQ-1 の「割引額の 1 円未満は切り捨てる」の根拠が薄い。「割り引く額の端数は切り捨て」のようにする
  - README の「フェーズゲートの落ち方」の assurance の行は、ゲートの goal に足した「判断は verification.md と review.json に基づき、このゲートで repo/ のコードを改めて検証しない」を反映していない。workflow.yaml の文に合わせる

## G. 人間の決定（往復 10 の後）

往復 10 の後、第三者が二度確かめ（事前レビューと、別のモデルによる敵対的なレビュー）、人間が決めた。

### 人間の決定

1. **unit\_test の tests\_defective の分割を取り消す。** 二つは戻り先が同じ（unit\_test 自身）で、違いは集計の都合（不足と不備を分けて数えたい）だけだった。end\_state のクラスは下流の振る舞いに関する同値類で、集計のための分類ではない。手引き第13節に、このことと、クラスを変えた後に確かめることを書き足した（「violated が出たら」の下）。往復 10 の前も、一つの記憶 coverage\_gaps が不足と不備の両方を運んでいた
   - 利用者役が足した句（テスト自身の誤りで失敗するテスト）も入らない。そうした失敗は、前と同じく unknown（人に戻す）になる
2. **往復 10 で代表を変えた所は、人が印を除いて読んでラベルを付ける**（手引き第15.1節。全部の付け直しはしない）

### 直すこと

**G-1. unit\_test と construction のゲートの記述を、往復 10 の前の文に戻す**

- 戻す文は `git show 08f79b4:examples/software-factory/workflow.yaml` の unit\_test（description、artifacts の memory\_in と memory\_out、goal、end\_state、rollback）と、construction のゲートの goal。これは人間が承認した文
- 記憶 test\_defects と、tests\_defective の rollback を除く。test\_report.md の節は「## テスト」「## 失敗」「## 未網羅」の三つに戻す
- 不足と不備を数えたいなら、記述は変えずに、coverage\_gaps の項目の書き方で区別してよい（手引き第13節）。必須ではない

**G-2. 代表とテストを合わせる**

- tests/fixtures/unit\_test/defective/ は、確率 0 の tests\_insufficient の変種として残す（往復 10 の前の tests\_insufficient には、要件に反する期待を持つテストの代表が無かった）。test\_report.md の不備を「## 未網羅」と記憶 coverage\_gaps に書く形にし、往復 10 の前の tests\_insufficient の記述どおりにそのクラスになることを確かめる
- 自分自身へ戻るシナリオ（unit\_test\_defective\_self\_rollback）を、tests\_insufficient で空でない coverage\_gaps を持って unit\_test に戻り、expect.starts で unit\_test の訪問 2 の記憶を確かめる形にする
- E2E のカバレッジの (ステージ, クラス) の数、構成の表、遷移の被覆、テストを合わせる。分布と基準の値は変えない（確率的な実行には不備の代表を出さない）

**G-3. README を人間の決定に合わせる**

- 「人間のレビューで確かめてほしいこと」から tests\_defective の記述と境界の項目を除き、決まったこと（分割は取り消し、テスト自身の誤りで落ちるテストは unknown）を書く

**G-4. 前の不足の確かめ**

- N14: 手引き第13節の書き足しで判断できるかを確かめ、adopting-gaps.md の扱いを直す
- N15: contract/conformance/README.md の「ファイルの内容」に、鍵が重なる時の規則（より長い鍵の内容になり、鍵の並びによらない）が書かれた。判断できるかを確かめる。ファイルごとに展開した回避（software\_factory/scenarios.py）を外せるなら外す

**G-5. 第三者の事前レビューの低（分割の取り消しの後も残るもの）**

- tests/test\_scenarios.py の test\_every\_rollback\_edge\_is\_taken の docstring は、「持ち帰る記憶が戻り先の開始時スナップショットに届くことは、各シナリオの expect.starts が確かめる」と言うが、unit\_test → unit\_test（construction\_rollbacks）、review → implement（assurance\_gate\_rolls\_back）、release → release（release\_notes\_self\_rollback）の三本は、戻り先の訪問の expect.starts が無い。三本に足すか、docstring を事実に合わせる
- tests/test\_e2e.py の test\_coverage\_plan\_reaches\_every\_stage\_class は、誘発で踏むはずの目標が誘発で踏まれることを確かめていない（注入で踏まれても通る）。誘発の目標がすべて induce であることを確かめる一行を足す
- README の「記述と代表の整合」に、plan\_tasks/incomplete（シナリオだけが写す代表）は、design/gap と組む状態文書を記述だけで読んで確かめた、と書き足す（試しのコーパスには出ないので）
- tests/expectations/markov.yaml と markov\_gated.yaml の注記の「implement の訪問の回数 1.674」は、厳密な値 1.67349 を丸めると 1.673（任意）

**G-6. 人がラベルを付ける材料を作る（人間の決定 2）**

- 手引き第15.1節の手順で、往復 10 で代表を変えた所の項目を集める
  - REQ-3 に利用者をまとめた requirements.md を状態文書に含む評価（analyze、discovery のゲート、acceptance など。ペルソナごと）
  - design/ok を含む評価（design）
  - acceptance/misread（ペルソナごと）
  - vague\_founder の回答を含む intake.md（intake）
  - G-2 で tests\_insufficient の確率 0 の変種にした不備の代表（unit\_test）
- 状態文書と選択肢の組ごとに一項目にし（`unique_states=True`）、確率的な実行に出ない代表は、その代表が届く上流の組み合わせを踏む試しの実行で入れる（手引き第15.1節）
- docs/human-labeling.md に、項目ごとに、項目の id、対象（ステージかフェーズと訪問）、印を除いた状態文書（`unmarked(item.state)`）、選択肢（id と記述）、空欄の「ラベル:」を書く。冒頭に、読み方（印を探さず、選択肢の記述だけで選ぶ。迷った時は unknown と書き、理由を添える）を書く
- 人のラベルを受け取ったら、contract/formats/label.schema.json の形の JSON Lines にして `oracle_report(MarkerClassifier(), corpus, labels)` を出せるように、コーパスの書き出しと、ラベルのファイルがあれば比べるテスト（無ければスキップではなく、ファイルが無いことを報告する小さなコマンド）を用意する。項目の数を README に書く
