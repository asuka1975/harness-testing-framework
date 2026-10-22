# F4 往復 10〜13 の差分の確かめ（検証役）

- 日付: 2026-10-23
- 対象: コミット 85c7ed5（HEAD）。完了判定の二回目（reports/f4-completion-2.md、正常。対象は 08f79b4 の前の状態）の後の差分 `git diff 08f79b4 HEAD`（47 ファイル）だけを見た。例の側は examples/software-factory/、本体の側はそれ以外
- 役割: 検証役（第三者、plan.md 第5.9節）。成果物と仕様だけを読み、実装の作業過程は見ていない。作業ログ（docs/progress.md と examples/software-factory/docs/progress.md）は読んでいない
- 読んだもの
  - 完了条件と決定: plan.md 第2節、第5.8〜5.9節、第6節 F4（D-19 の注記を含む）、decisions.md の D-17〜D-21、reports/f4-completion-2.md（全文）。reports/f4-astra-review.md と reports/f4-unit-test-review.md は読んでいない
  - 本体の側の差分のすべて: docs/adopting.md（第2.1節、第13節、第15.1節）、docs/changelog.md、contract/conformance/README.md と src の写し、src の testing/harness/scenario.py、tests/test\_conformance.py。変異を当てるために runtime/runner.py の `_rollback` と testing/e2e/coverage.py の `plan_coverage` の該当箇所
  - 例の側の差分のすべて: README.md、docs/adopting-gaps.md、docs/review-findings.md の G、software\_factory/labeling.py、scenarios.py、personas.py、design.py、tests/stochastic.yaml、tests/expectations/ の四つ、tests/fixtures/ の差分、tests/ の差分（test\_labeling.py は冒頭と関数の一覧）、docs/human-labeling.md（冒頭と一部の項目）。workflow.yaml は全文（差分は無い）
- 実験の環境
  - 検証役の scratchpad に自分専用の新しいディレクトリ f4d/ を作り、その中にリポジトリの複製を二つ（repo/ は 85c7ed5、mut/ は変異用）作った。`uv sync --locked`（Python 3.12.3）。`HTF_RUNS` は外した。元の作業ツリーでは、テストも実験も走らせていない
  - 変異は mut/ の上で一つずつ当て、`git checkout` で戻した。ラベルの試しは repo/ の上で行い、戻した。最後に両方の `git status` が空であることを確かめた
- 人間のゲート（workflow.yaml のレビューと承認、第15.1節の人手のラベル）は判定しない

> **人間がラベルを付ける前に読まないでほしい所:** 付録（盲検のラベルの食い違い）は、一部の項目の印に触れる。第4.1節の指摘 E3-M1 は、材料がクラスの構成を明かすことを述べる。ほかの節は読んでよい。

## 総合判定: 準正常

**plan.md 第6節 F4 の完了条件（人間の承認を除く）は、今のコミットでも満たしている。**

- workflow.yaml は 08f79b4 と同じ（`git diff --quiet` が真）
- 整合性検査は誤りも警告も無く通る
- `bash scripts/check.sh` は複製の上で通る（662 件が通過。例のテストは 199 件）
- (stage, end\_state) のカバレッジは 30 の対象のすべてを踏む
- adopting-gaps.md の「未解消」は無い。N14〜N17 は D-18〜D-21 で扱われている
- 読取制限が破られた証拠は無い

**変えた代表の確かめ（第15.1節の試し）。** 印を除いた材料を、この会話の文脈を持たないサブエージェント四つに、盲検の写しとして渡した。付いたのはエージェントのラベルで、人手のラベルではない。結果は κ 0.892（49 項目のうち 45 が印と一致）。

- 食い違った 4 項目は、往復 10 の直し（REQ-3、design/ok、vague\_founder の回答、defective）そのものによるものではない
  - 3 項目は discovery のゲートの訪問 2 以降で、持ち帰った問いへの未定の回答と「## 未決事項」（なし）の組による
  - 1 項目は acceptance の requirement\_misread の代表で、食い違いが推論であることによる
- どちらも、完了判定の二回目で人間に渡し、D-17 の 3 で承認された設計の帰結に当たる
- 人のラベルで同じ食い違いが出ることを見込んでおくべきで、第9節に挙げた

**人がラベルを付ける材料（human-labeling.md）は使える。** 埋めた「ラベル:」から `labels` と `compare` で印と比べる手順は、書かれたとおりに動いた。一方で、問題が二つある。

- 材料の冒頭が、項目の選び方を「(対象, 訪問の区分, クラス, 上流の違い) ごとに一つ」と書き、対象ごとの項目の数も示す。これでラベラーは、組ごとのクラスの構成を知ってしまう（E3-M1、中）
- 項目の id（実行の id と評価の seq）から、49 項目のうち 8 項目の印が推せる（E3-L1）

**新しいシナリオとテストは、壊すと落ちる。** 全辺で空でない carry が戻り先に届くことと、誘発の目標が誘発で踏まれることを確かめるテストに、変異を四つ当てた。四つとも落ちた（第6節）。

**本体の側の差分は正しく、互いに矛盾しない。** N15 の規則と実装、手引き第2.1節・第13節・第15.1節、changelog は整合している。手引き第13節は計画書 第2節の固定された判断（「クラスの粒度は独立性検証の結果でのみ変える」）と合う。

判定の規則は前の二回と同じにした。完了条件を満たし、高と中の指摘が残っていなければ正常、完了条件を満たしても中以上の指摘が残れば準正常とする。指摘は次のとおり（第8節）。

- 例の側: 中 1、低 7
- 本体の側: 低 3

E3-M1 は、材料を人間に渡す前に直すとよい。直しは小さい。

## 1. 完了条件（項目 1）

| 完了条件 | 判定 | 証拠（08f79b4 からの変化を中心に） |
| --- | --- | --- |
| workflow.yaml が整合性検査を通る | 満たす | `git diff --quiet 08f79b4 HEAD -- examples/software-factory/workflow.yaml` が真（往復 10 の tests\_defective は往復 11 で一字も残らず戻った）。複製の上で `PYTHONPATH=examples/software-factory python -m harness_testing_framework.testing.spec examples/software-factory/workflow.yaml --registry software_factory.metrics:REGISTRY` → `0 error(s), 0 warning(s)`、終了コード 0 |
| 4 フェーズ以上、8 ステージ以上、越境 1 以上、ユーザー待ち 1 以上、決定論指標 3 以上 | 満たす | workflow.yaml が変わらないので前と同じ（5 フェーズ、9 ステージ、越境の辺 6 本、intake、指標 5） |
| 参照ランタイムを組み込み、契約適合テストを通す（D-19 の注記: 版が通すことと、ハーネスの実行で契約違反・本体の例外・範囲外のファイルが無いこと） | 満たす | test\_conformance.py が通る。test\_stochastic.py の test\_bodies\_keep\_the\_contract（markov とゲートを揺らす実行のすべてで、契約違反、本体の例外、範囲外のファイルの警告が無い）が通る。計画書 第5.8節と第6節 F4 の注記（D-19 の 4b）で、完了判定の二回目 第9節の 9（判定の対象の読み方の食い違い）は解消した |
| 全ランナーが通る | 満たす | check.sh の pytest が 662 件すべて通過。6 種の遷移（17 シナリオ。往復 10 で 2 本足した）、分布テスト、粗いクラスの検出、マルコフ合成、オラクル検証、トリアージ。分布、設計値、基準の値は変わっていない（expectations の差分は注記だけ。stochastic.yaml の markov と divergent の分布も変わらず、defective は確率 0、profiles に labeling を足しただけ） |
| (stage, end\_state) のカバレッジ 100% | 満たす | test\_coverage\_plan\_reaches\_every\_stage\_class が通る。`coverage_targets` は 30（往復 10 の 31 から、tests\_defective の取り消しで戻った）。missing が空、covered が対象の全体。往復 11 で「誘発の台本を与えた目標はすべて誘発で踏む」の一行が足された（変異 A で効くことを確かめた） |
| adopting-gaps.md の全項目が解消されるか、理由が decisions.md にある | 満たす | 「未解消」は「無し（往復 13 で新しい不足は無かった）」。N14 は D-18 と D-19（(b)。手引き第13節）、N15 は D-18（contract/conformance/README.md と changelog）、N16 は D-20、N17 は D-21（いずれも手引き第15.1節）。changelog の「未公開」にも載る |
| 人間が workflow.yaml をレビューして承認 | 判定しない | 人間のゲート。D-17 で 1〜5 に回答。D-19 で 4 が取り消され、6（人手のラベル）は今回の材料で行う |

### 1.1 読取制限

- examples/software-factory/ の Python ファイル（tests/fixtures/ の下を除く）を AST で読み、`harness_testing_framework` からの import をすべて集め、実行時の `__all__` と照合した
  - すべて公開の名前だった。差分で増えたのは、schema の `load_workflow_document`（test\_scenarios.py）、testing.oracle の `CorpusItem`・`Label`・`build_corpus`・`load_corpus`・`load_labels`・`oracle_report`・`save_corpus`・`save_labels`、testing.harness の `MarkerClassifier`・`marked_class`・`unmarked`、runtime の `Workflow`、contract の `load_contract_schema`（labeling.py と test\_labeling.py）
  - どれも api-reference.md に載っている
  - `import harness_testing_framework.…` の形、`import_module`、`__import__` は無い
- 新しいコードが本体のオブジェクトに使う名前は、すべて api-reference.md の signature と説明にある。使っているのは `CorpusItem` の item・scope・target・options・state・source、`OracleReport` の kappa・accuracy・`lines()`、`IndependenceResult` と `EntryDependenceResult` の p\_value・groups
- 例の側の追加行を検索した。plan.md、decisions.md、reports/、決定の番号、src のパスは、adopting-gaps.md の「読んでいない」宣言の一か所にしか現れない
  - adopting-gaps.md には、往復 11〜13 で公開の文書（adopting.md、changelog.md、contract/）の git の差分を見たと書かれている。これは読んでよい文書の範囲に収まる
- docs/review-findings.md の G は、計画の側が公開の文書の語で書いたもの（54952a9。D-15 の経路）。決定の番号や報告のパスは書かれていない
- コミットは本体と例で分かれている（B-L6 は守られている）
  - 例だけ: 077cc91、11cc836、e72b152、325ffef、54952a9
  - 本体: 7547a75（contract、docs、src、tests）
  - 文書と報告: 4e9a21d、7418064、ca65105、056374f、3b28deb、85c7ed5

判定: 読取制限が破られた証拠は無い。

## 2. 往復 10 で直した代表は、記述どおりにそのクラスになるか（項目 2）

### 2.1 方法（エージェントのラベル。人手のラベルではない）

- 材料 docs/human-labeling.md（49 項目）から、盲検の写しを作った。項目の id は B01〜B49 の番号に置き換え（理由は E3-L1）、冒頭の「選んだ項目」の節は除いた（理由は E3-M1）。「読み方」と各項目の本文（対象、印を除いた状態文書、選択肢、空の「ラベル:」）は、そのまま残した
- 写しを四つ（B01〜B18、B19〜B33、B34〜B41、B42〜B49）に分け、それぞれ別のサブエージェントに渡した
  - サブエージェントは同じモデルで、この会話の文脈を持たない
  - 指示は次のとおり。その写し一つだけを読む。ほかのファイルを読まず、コマンドも実行しない。項目は一つずつ独立に判断し、項目の数や配分から推し量らない。記述の字義に照らし、迷ったら unknown にする
- 返ってきたラベルを、複製の上の human-labeling.md の「ラベル:」に書き入れた。そのうえで `labels` と `compare` を走らせた（第4.4節）
- 留保
  - これはエージェントのラベルで、人手のラベルではない
  - ラベラーは私と同じ系統のモデルなので、人と違う偏りを持ちうる
  - 写しは印と選び方を除いたが、状態文書そのもの（代表の写し）は人に渡すものと同じである

### 2.2 結果

`compare` の出力: ラベル 49 件、κ 0.892、一致率 0.918、食い違い 4 件。

| 対象 | 訪問 | 項目 | 印と一致 |
| --- | --- | --- | --- |
| intake | 1 / 2 以降 | 2 / 2 | 2 / 2 |
| analyze | 1 / 2 以降 | 7 / 7 | 7 / 7 |
| discovery のゲート | 1 / 2 以降 | 3 / 3 | 3 / **0** |
| design | 1 | 3 | 3 |
| plan\_tasks | 1 | 2 | 2 |
| architecture のゲート | 1 | 1 | 1 |
| unit\_test | 1 | 3 | 3 |
| acceptance | 1 | 12 | **11** |
| review | 1 | 4 | 4 |

変えた代表ごとの結果:

| 変えた代表（往復 10） | 結果 |
| --- | --- |
| requirements.md の REQ-3（「## 利用者」を外し、利用者と入力の場所を REQ-3 に入れた） | analyze（14 項目）、訪問 1 の discovery のゲート（3）、design、plan\_tasks、architecture のゲートで一致。訪問 1 の discovery のゲートは、三つのペルソナとも goal になった。完了判定の二回目の E2-L5 (1)（「要件か受け入れ基準に」の字義）は、代表の側の直しで解消した |
| design/ok の「## 対応」の REQ-3（画面は repo/ の外。コードを文字列で受け取る） | design の goal、plan\_tasks、architecture のゲート、review の四つのクラスで一致。「画面が repo/ の外」を、構成要素の欠けや要件への問いと読んだラベラーはいなかった |
| acceptance/misread の verification.md（根拠を REQ-3 にした） | 3 項目のうち 2 項目が一致（確信 中）。残る 1 項目（vague\_founder と組み、持ち帰った問いと未定の回答を含む intake.md）は unknown（確信 低）。どのラベラーも、食い違いが推論（人が打つと大文字と小文字が揺れる）で回答の文と直接に食い違わないことを挙げた。unknown の側は、vague\_founder の「使えないコードはエラーにして」と pct10 を拒むことが合う、と読んだ |
| vague\_founder の回答（「割り引く額の端数は切り捨て」） | intake、analyze、discovery のゲート、acceptance の該当項目で一致。完了判定の二回目の E2-L5 (2) は解消した |
| unit\_test/defective（tests\_insufficient の確率 0 の代表） | 三つの実装の変種のどれと組んでも tests\_insufficient で一致。ok と ok\_b と組む二項目は確信 中（理由は下の (3)） |

### 2.3 上流の成果物と組んだ時（手引き第12節）

1. **未定の回答を含む intake.md と、analyze の goal の代表の組。**
   - analyze の needs\_unclear で intake に戻ると、intake.md には、持ち帰った二つの問い（キャンペーンの後も使えるか、同じ購入者が何回使えるか）と、どのペルソナも決めない回答（「来月の末に決める」「未定」「そのうち考えるよ」など）が入る
   - 一方、analyze の goal の代表の requirements.md は「## 未決事項」が（なし）である
   - analyze の訪問 2 以降（7 項目）は、記述（goal は要件の網羅を求めない）どおりに goal で一致した
   - discovery のゲートの訪問 2 以降（3 項目）は、3 項目とも unknown になった。ゲートの goal「intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映」の括弧を、範囲を限るものと読むか、例示と読むかで割れた（ラベラーは後者を採り、確信 中）
   - 同じ組は acceptance にも届く。acceptance の材料では、この組は 12 項目のうち 2 項目にしか入っていない（E3-L3）
   - この点は完了判定の二回目 第5.3節の 3 で人間に渡し、D-17 の 3（ペルソナの設計）で承認された。ただし盲検のラベルは、人が付けても食い違いが出うることを示す（第9節の 3）
2. **acceptance の requirement\_unmet の代表と、正しい実装 ok\_fixed の組。**
   - README と labeling.py は「requirement\_unmet の代表は REQ-1 の誤りを見つけるので、正しい実装 ok\_fixed とは組まない」と書く
   - これは markov では正しいが、divergent と、試しの実行 labeling では組む。試しのコーパス（242 項目）に、この組の項目が 4 つある
   - この組では、代表の「Discount.apply が支払額を切り捨てている」が ok\_fixed のコードと食い違う（E3-L7）
   - 材料は ok\_fixed の後の acceptance を外したので、人に渡す項目には出ない
3. **主経路の実装（ok、ok\_b）の REQ-1 の欠陥。**
   - unit\_test の defective、acceptance の goal、review の goal の項目で、ラベラーは repo/ の Discount.apply が支払額を切り捨てる（REQ-1 に反する）ことに気づいた
   - それでも、記述が証拠とする節と記憶に従ってラベルを付けた
   - これは D-17 の 5（玩具の意図）で承認されている。人も同じことに気づくはずである（第9節の 6）
4. **plan\_tasks/incomplete（往復 10 で足した代表。シナリオ plan\_tasks\_design\_incomplete\_rollback だけが写す）。**
   - この代表は材料に無い。私が、上流の design/gap と組む状態文書を記述だけで読んだ（エージェントのラベル）
   - 選択肢は design\_incomplete と unknown（tasks\_cover\_requirements が落ちて goal は外れる）
   - 次の三つが揃っているので、design\_incomplete に当たる
     - design.md の「## 構成」は discount.py だけ
     - tasks.yaml は REQ-1 と REQ-2 だけを割り当てる
     - 欠けている点（コードを受け取る Cart の操作と cart.py）が、記憶 design\_issues と tasks.yaml の先頭の注記の両方にある
   - 一点揺れる。REQ-3（形式の検査）は「## 構成」にある parse\_code が受け持てる。そのため「REQ-3 を受け持つ構成要素が無い」は、読み方によって弱い。design/gap の代表（盲検で requirements\_gap に一致）にも、ラベラーが同じ点を挙げた
   - この代表は D-19 の 4a の列挙に無く、人に渡す材料にも入っていない（第9節の 5）

## 3. 新しいシナリオとテストの確かめ（項目 5 の前提）

- 定義の上のロールバックの辺は 12 本ある。test\_every\_rollback\_edge\_is\_taken は、シナリオの実行記録の要約から、12 本すべてが通ることを確かめる
- test\_every\_rollback\_edge\_has\_its\_carry\_checked\_at\_the\_next\_start は、期待の側（expect.trace と expect.starts）だけを読む。そして、各辺で戻った直後の戻り先の訪問の開始時スナップショットが、carry する記憶を空でない値で期待することを確かめる
- 期待どおりに動くことは test\_scenario が確かめる。二つを合わせて「全辺で空でない carry が戻り先に届く」になる。完了判定の二回目の E2-L3（plan\_tasks → design を空でない carry で通るテストが無い）は、plan\_tasks\_design\_incomplete\_rollback で解消した
- unit\_test\_defective\_self\_rollback は、unit\_test が自分自身に戻り、訪問 2 の開始時に coverage\_gaps が届くことを確かめる。construction\_rollbacks、assurance\_gate\_rolls\_back、release\_notes\_self\_rollback には、戻った直後の expect.starts が足された（G-5）
- N15 の規則（より長い鍵の内容になる）を使い、ok\_files は inputs の repo/ のディレクトリの参照に、implement と unit\_test のフィクスチャのファイルの参照を重ねる。往復 10 の回避（ファイルごとの展開）は外された

## 4. 人がラベルを付ける材料（項目 3）

### 4.1 印は漏れていないか

- **印の文字列は無い。** `[[class` は 0 件。コーパスの source からは分類器の選択（choice）が除かれている（`select`）。材料は `unmarked` を通した状態文書だけを持つ
- **クラスの構成が分かる（E3-M1、中）。**
  - human-labeling.md の「選んだ項目」は、まとめ方を「(対象, 訪問の区分, クラス, 上流の違い) ごとに一つ」と書き、その下に対象ごと・訪問の区分ごとの項目の数を書く
  - この二つから、ラベラーは組ごとのクラスの構成を知る。たとえば次のとおり
    - intake の訪問 1 は 2 項目で、選択肢は goal と unknown なので、一つずつである
    - acceptance は 12 項目で、三つのペルソナのそれぞれに、四つのクラスが一つずつある
    - review は 4 項目で、四つのクラスが一つずつある
  - 一つにラベルを付ければ、組の残りが絞られる。迷った項目を消去法で決めると、まさに確かめたい揺れが隠れる
  - README の「記述と代表の整合」の表は、さらに内訳をクラスの名前で書く（「goal、requirement\_unmet、requirement\_misread、unknown を三つのペルソナで」）
  - 手引き第15.1節の「選んだ規則を記録する」は守られているが、記録の置き場が、人に渡す材料そのものになっている
- **項目の id から、印が推せる（E3-L1）。**
  - 項目の id は `<実行の id>-<評価の seq>`（api-reference.md の `CorpusItem`）である。49 項目のうち 32 項目が、10 の実行の id を共有する
  - 同じ実行で、seq が一つ後にそのフェーズのゲートの項目があれば、そのステージは goal である（ゲートは最終ステージの goal の後にしか評価されない）
  - analyze の後の seq に、同じ実行の intake の次の訪問があり、間にゲートが無ければ、その analyze は needs\_unclear である
  - この二つの規則だけで 8 項目の印が推せて、8 項目とも印と一致した
  - 材料に id を書くことは、review-findings.md の G-6 の指示どおりである
- **印を除いた跡（低。E3-L5 に含めた）。**
  - tasks.yaml の先頭に「# 」だけの行が残る（印が YAML の注釈の中にあったため）
  - review.json に `"marker": ""` が残る
  - 印を除いた行は空行になる
  - どれもクラスを示さない（どのクラスでも同じ）。それでも盲検のラベラーは「残った跡に意味があるか判断できない」と挙げた

### 4.2 読み方の説明は十分か

基本は書かれている。印を探さない、選択肢の記述だけで選ぶ、迷ったら unknown と理由、訪問 2 以降の memory\_in は状態文書に入らない、コーパスを開かない、の五つで、四つのラベラーとも、この説明だけでラベルを付け終えた。

一方、ラベラーが共通して迷い、ラベルが割れた点がある（E3-L5）。

1. 記述が証拠とする節と記憶に書かれていることで判断するのか、ラベラーが中身を検算するのか
   - 主経路の実装の REQ-1 の欠陥、acceptance の misread の推論、review の changes\_requested の指摘の前提（数量の ValueError を出すのは Cart.add で、Cart.total ではない）で割れた
   - acceptance の 1 項目の食い違いは、この方針の違いから来ている
2. 「（なし）」「（判断できない）」「（実行できなかった）」を、「空である」「問いが無い」「列挙されている」にどう数えるか
3. 記述の括弧の列挙が、範囲を限るものか、例示か。discovery のゲートの訪問 2 以降の 3 項目は、ここで割れた
4. goal が選択肢に無い時の「goal に優先する」の読み方。ステージの評価がどのフェーズに属するか（review の changes\_requested の「フェーズ assurance の評価では」）
5. 訪問 2 以降で、どの問いが持ち帰ったものかは分からない。応答だけで判断してよいか
6. 印を除いた跡（上）。確信度の目安（どこから unknown か）

1 と 3 は、記述の読み方そのものなので、方針を人間が決めて材料に書くのがよい（第9節の 2）。

### 4.3 49 項目の選び方は、手引き第15.1節の目安と人間の決定に合うか

**合う所。**

- 対象、訪問、まとめ方は、第15.1節の三つの目安（D-20、D-21）の字のとおりに実装されている
  - 対象: EVIDENCE は、記述が変えた句を判断の根拠にしうる対象
  - 訪問: AGAIN は workflow.yaml の memory\_in から決まる。訪問 1 と同じ状態文書は除く
  - まとめ方: 組に訪問の区分を含め、組ごとに短いものを選ぶ
- test\_labeling.py が、49 の組をすべて一つずつ含むこと、作り直したものと一致することなどを確かめる
- 試しの実行（labeling、240 回、種 90000）のコーパスは、自分で作り直して数えた。242 項目のうち 220 項目が変えた代表を含み、`wanted` は 122 項目で、README の数と一致した
- D-19 の 4a の対象（REQ-3 の requirements.md を読む所、design/ok、acceptance/misread、vague\_founder の回答、defective）は、すべて入っている。往復 10 で変えていない代表だけの項目（たとえば analyze の unknown と precise\_pm の組）は入っていない
- 余分は見つからなかった。review を足した理由（design\_flaw と changes\_requested の境界は、design.md のインターフェースで分かれ、変えた句がインターフェースを述べる）は記述の字に合う

**抜けの候補。**

- **implement（E3-L4）。**
  - implement は design.md を読む。goal は「repo/src/ の変更が design.md の構成どおりである」と書き、節を名指していない（quality\_violation は「## 構成」と名指す）
  - 変えた句の「コードを文字列で受け取る」は、parse\_code のインターフェースを述べる
  - 往復 13 で review を足した理由（記述は節を名指さず、変えた句はインターフェースを述べる）を当てはめると、implement の goal も「判断の根拠にしうる」に当たる
  - labeling.py と README は「implement は「## 構成」で判断する」として外している。この扱いは、review を足した理由と揃っていない
  - 実害は小さいとみる。implement の goal の代表は三つとも parse\_code(code: str) で、句と合う
- **acceptance の上流の違い（E3-L3）。**
  - acceptance は intake.md を読み、requirements.md と回答の食い違いを見る。そのため、持ち帰った問いと未定の回答を含む intake.md かどうかは、ペルソナと同じく状態文書を変える上流の違いである
  - 手引き第15.1節の 1 は「上流の違いで同じ代表の状態文書が変わるなら、それぞれが別の項目になる」と書く。ところが例は、上流の違いをペルソナだけにした
  - 短いものを選んだ結果、12 項目のうち持ち帰りありは 2 項目（unknown と precise\_pm、misread と vague\_founder）だけになった。goal と unmet の「持ち帰りあり」の組は材料に無い
  - 試しのコーパスでは、ほとんどの組に両方の形がある。ただし (misread, vague\_founder) は持ち帰りありの形だけである
  - 盲検で食い違った acceptance の 1 項目は、この形だった
- **plan\_tasks/incomplete。** 往復 10 で足した代表で、材料に無い。手引き第15.1節の新しい文（「項目にしない時は、シナリオで分類器が見る状態文書を…読んで確かめ、記録する」）のとおり、エージェントが読んだと README に記録されている。D-19 の 4a の列挙に無いので、人が読むかは人間が決める（第9節の 5）

### 4.4 ラベルを埋めてから比べる手順

手順は README の「記述と代表の整合」と、human-labeling.md の「ラベルを付けた後」に書かれている。複製の上で、盲検のラベル（理由つきの行を含む）を「ラベル:」に書き入れ、次を走らせた。

- `uv run python -m software_factory.labeling labels --labeler agent-blind`（examples/software-factory/ で）
  - 出力は「docs/human-labels.jsonl: ラベル 49 件、空の「ラベル:」0 件」、終了コード 0
  - 行は `{"item": …, "label": …, "labeler": "agent-blind"}` で、label.schema.json の形
- `uv run python -m software_factory.labeling compare`
  - 出力は κ 0.892、一致率 0.918、混同行列、食い違い 4 件（項目の id、対象、訪問、印、ラベル）、終了コード 0
- 埋めた状態で `pytest tests/test_labeling.py` も 9 件すべて通った。human-labels.jsonl がある時の test\_received\_labels\_fit\_the\_corpus を含む
- ラベルのファイルが無い時の compare は、「ラベルのファイルが無い」と報告して 1 で終わる（test\_labeling が確かめる）

使い勝手で引っかかる所があった（E3-L6）。

| 書き方 | 結果 |
| --- | --- |
| `ラベル：unknown`（全角のコロン。日本語の入力で起きやすい） | `ValueError: 「ラベル:」の行が 0 個ある` の traceback で終わる。どの項目かは出ない |
| `` `ラベル: goal` ``（読み方の例を、バッククォートごと写した） | 同じ traceback |
| 「ラベル:」の次の行に goal | 空として数えられ、「空の「ラベル:」49 件」と報告される（誤りにはならない） |
| `ラベル: Goal`、`` ラベル: `goal` `` | 終了コード 2。項目の id と「選択肢のどれでもない」が出る（よい） |
| `ラベル: goal（理由）` | 読める（よい） |

- 実行する場所が書かれていない。リポジトリの根で `uv run python -m software_factory.labeling` を走らせると、`No module named 'software_factory'` で失敗した。examples/software-factory/ で `uv run` を付ければ動く
- README の手順の文は `python -m …` だけで、場所も `uv run` も書いていない
- `write` が埋めた「ラベル:」を空にすることは、材料の冒頭と README に書かれている

### 4.5 人が読む分量と、記述を変えずに減らす案

**数えた分量。** human-labeling.md は 156,390 文字（6,619 行）。

| 内訳 | 文字数 | 割合 |
| --- | --- | --- |
| 印を除いた状態文書 | 128,435 | 82% |
| 選択肢（49 回） | 20,963 | 13% |
| 冒頭、見出し、対象、ラベルの行 | 6,992 | 5% |

対象ごとには、acceptance（12 項目）が 66,793 文字（43%）、analyze（14 項目）が 21,433、review（4 項目）が 20,390、unit\_test（3 項目）が 16,487 で、ほかは 1 万文字未満である。

**繰り返しを数えた。**

- 状態文書は 360 の区切り（「## ファイル …」と「## 記憶 …」）からなり、合わせて 126,960 文字ある。互いに違う内容は 17,412 文字しかない
  - 繰り返しの大きいもの: requirements.md（41 回、内容は 3 通り）、repo/src/shopcart/cart.py（25 回、2 通り）、repo/tests/test\_discount.py（19 回、2 通り）、repo/tests/test\_cart.py（25 回、1 通り。変更前のまま）、discount.py（19 回、3 通り）、intake.md（36 回、10 通り）、tasks.yaml（22 回、2 通り）、feature\_request.md（36 回、1 通り）
- 選択肢の文は 13 通りしかない（5,415 文字）

**案。** どれも記述と状態文書の中身を変えず、見せ方だけを変える。

1. **選択肢を対象ごとに一度だけ示す。** 対象の節の頭に選択肢を置き、項目では id だけを並べる。−15,548 文字（約 10%）
2. **対象ごとに、全項目で同じ区切りを一度だけ示す。** 対象の節の頭に「この対象のすべての項目に共通のファイル」を置き、項目には違うファイルと記憶だけを書く。1 と合わせて、試算で 156,390 → 約 65,100 文字（約 4 割）になる。acceptance は 66,793 → 約 16,400 文字
   - acceptance の項目に残るのは、intake.md（ペルソナと持ち帰りの有無）、verification.md、記憶、実装の変種で変わる discount.py だけになる
3. **違う内容を付録に一度ずつ置き、項目は参照で示す**（「repo/tests/test\_cart.py: 付録 R-7」）。状態文書の中身は約 17,400 文字で、参照と見出しを足しても約 3 万文字（約 2 割）になる。ただし、項目ごとに状態文書を頭の中で組み立て直す手間が増える
4. 2 か 3 を採るなら、各項目の状態文書の区切りの並び（分類器が見た順）を、項目の中で示し続けるとよい（「## ファイル repo/tests/test\_cart.py（共通）」のように）

**注意。**

- どの案でも、同じ内容を共有する項目が目に見えてまとまる。たとえば同じ verification.md を持つ 3 項目は同じクラスの代表である。ただしこれは、全文を並べた今の形でも読めば分かることで、新しい漏れではない
- render と test\_labeling.py（作り直したものとの一致、印が無いこと）を合わせて直す
- `labels` は項目の見出しと「ラベル:」の行を読む。人に渡す形を変えても、この二つの形を保てば、比べ方は変わらない

## 5. 本体の側の差分（項目 4）

| 変更 | 判定 | 根拠 |
| --- | --- | --- |
| N15: シナリオの files で鍵が重なる時は、より長い鍵の内容になる（scenario.py の `_contents`、contract/conformance/README.md と src の写し、changelog の「互換性に注意する変更」） | 正しい | あるパスを覆う鍵は、そのパス自身（ファイルの鍵）か、その前置き（ディレクトリの鍵）である。よって覆う鍵どうしでは、長いほど具体的になる。長さで安定に並べて短い順に置けば、最も具体的な鍵が勝つ。長さが同じで同じパスを覆う二つの鍵はありえない（同じ文字列になる）。README の二つの写しは同一（diff が空）。tests/test\_conformance.py の新しいテストは、鍵の並びを保って書き出し（`sort_keys=False`）、正順と逆順の両方で同じ展開になることを確かめる。changelog の「前は鍵の並びで後に書いたもの」は、前のコード（dict の並びで上書き）と合う。既存のシナリオ（契約適合、toy-minimal、software factory）はすべて通る |
| 手引き第2.1節: 指標の値とツールの出力は状態文書に入らない | 正しい | 状態文書は reads と writes の内容と memory\_out の値（契約 2.4、runner の `_evaluate` が集めるパス）。指標は選択肢から goal を外すことでだけ効く。材料の「読み方」とも合う |
| 手引き第13節: 戻り先が同じで、分けて数えたいだけならクラスを分けない。クラスを変えた後に確かめること | 計画書 第2節と合う | 第2節の帰結「クラスの粒度は独立性検証の結果でのみ変える」を狭める方向の書き足しで、独立性検証のほかに粒度を変える理由を足していない（D-19 で (a) の文案を採らなかったとおり）。「violated が出たら」の下に置かれ、文脈は独立性検証。確かめることの一覧（整合性検査、MECE と優先、記憶を毎回書く、ゲートの記述、代表と基準、シナリオと E2E、独立性、第15.1節のラベル、コーパスとトリアージ）は、往復 11 の取り消しで例が実際に当てはめた手順と合う |
| 手引き第15.1節: 確率的な実行に置かない代表の確かめ方、変えた所に絞る時の三つの目安、`item.source` を人に渡す形から除く | D-20、D-21 と合う（低が二つ） | 三つの目安は D-21 の (a)〜(c) の文と同じ。「シナリオか E2E の注入だけが写す代表」の「注入」は、第14節の定義（分類の結果だけを変える）と合わない（B3-L2）。選んだ規則と項目の id を、人に渡す形に出さないことは書かれていない（B3-L1） |
| changelog の「未公開」 | 漏れは無い | 08f79b4 からの公開の文書と公開の振る舞いの変更五つ（N15、第2.1節、第15.1節の二つ、第13節）が、すべて載る。`__all__` と signature の変化は無い（src の差分は `_contents` だけ） |
| plan.md 第5.8節と第6節 F4 の注記（D-19 の 4b） | 契約 第10節、手引き第9節と合う | 例は test\_conformance.py（版の確認）と test\_stochastic.py（多数の実行で違反と例外が無い）の二つで確かめている |
| decisions.md の D-17 | 古い記述が残る（B3-L3） | 状態の行は「6 と第5.8節の注記は未回答」のまま。表の 4（tests\_defective を足す）、6、第5.8節の行にも、D-19 で取り消しや回答があったことが書かれていない。前の判定の B-L4（D-11 の D4 の行に「置換」と書き足した）と同じ扱いが要る |

## 6. 変異（項目 5）

| 変異（mut/ の上で一つずつ。戻した） | 結果 | 落としたテスト |
| --- | --- | --- |
| A: `plan_coverage` で、誘発の台本がある (unit\_test, tests\_insufficient) を注入にする（src の testing/e2e/coverage.py） | 落ちた | test\_coverage\_plan\_reaches\_every\_stage\_class（往復 11 で足した「誘発の目標はすべて induce」の行）。その一行を消すと同じ変異で通る。missing と covered の確かめだけでは捕まらない |
| B: ランタイムが、自分自身への辺のロールバックで carry を重ねない（src の runtime/runner.py の `_rollback`） | 落ちた | test\_scenario の construction\_rollbacks、release\_notes\_self\_rollback、unit\_test\_defective\_self\_rollback、test\_replay\_gives\_identical\_snapshots[construction\_rollbacks] の 4 件。同じ変異を 08f79b4 に当てると、落ちるのは construction\_rollbacks の 2 件だけだった（release → release の carry は、往復 11 で足した expect.starts で初めて捕まる） |
| C: plan\_tasks\_design\_incomplete\_rollback の expect.starts（design#2）を software\_factory/scenarios.py から除き、YAML を作り直す | 落ちた | test\_every\_rollback\_edge\_has\_its\_carry\_checked\_at\_the\_next\_start だけ（足りない辺 plan\_tasks → design を報告）。シナリオ自体は通るので、この新しいテストが無ければ捕まらない |
| D: 同じシナリオで、plan\_tasks が空の design\_issues を書く（期待は空でないまま） | 落ちた | test\_scenario[plan\_tasks\_design\_incomplete\_rollback] |

## 7. check.sh（項目 6）

複製（repo/）の上で `bash scripts/check.sh`（`HTF_RUNS` は外した）を走らせ、終了コード 0 で通った（全体 2 分 27 秒）。

- ruff check: All checks passed
- ruff format: 100 files already formatted
- mypy: src と tests で 42、software-factory で 21、toy-minimal で 12 のファイル。どれも no issues
- pytest: 662 件が通過（145 秒）
- runtime の行カバレッジ 90% 以上
- wheel にスキーマと契約適合テスト一式が入っている

`pytest --collect-only examples/software-factory` は 199 件（完了判定の二回目の時は 177 件）。

## 8. 指摘の一覧

### 例の側

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| E3-M1 | 中 | docs/human-labeling.md の「選んだ項目」（labeling.py の HEADER と render）、README.md の「記述と代表の整合」の表 | 人に渡す材料が、組ごとのクラスの構成を明かす（「(対象, 訪問の区分, クラス, 上流の違い) ごとに一つ」と、対象・訪問の区分ごとの項目の数）。ラベラーは、たとえば intake の訪問 1 の 2 項目が goal と unknown の一つずつであることや、acceptance の各ペルソナに四つのクラスが一つずつあることを、読む前に知る。消去法でラベルを決められ、確かめたい揺れが隠れる。README の表はクラスの名前まで書く | 第4.1節。手引き第15.1節の 2（印を除いた状態文書と選択肢の記述だけを読む） | 材料の冒頭からまとめ方の「クラス」と、対象ごとの数を除く。選んだ規則は README か別の文書に置き、材料には「選び方は README にある。ラベルを付け終えるまで読まない」とだけ書く。README の内訳の表にも同じ注意を添える。人間に渡す時に、README の該当の節を先に読まないよう伝える |
| E3-L1 | 低 | docs/human-labeling.md の項目の見出し（labeling.py の render） | 項目の id（`<実行の id>-<seq>`）から、同じ実行の項目と評価の順が分かる。直後のゲートの項目や、後の intake の訪問から、49 項目のうち 8 項目の印が推せた（8 項目とも一致） | 第4.1節。review-findings.md の G-6 が id を書くよう指示した | 材料では項目を通し番号（項目 1〜49）だけで示し、番号と id の対応はコーパスの側（labels が読む）に持つ。`parse_labels` は番号から id を引く |
| E3-L2 | 低 | （記録のみ）discovery のゲートの訪問 2 以降と、acceptance の misread の代表 | 盲検のエージェントのラベルで、discovery のゲートの訪問 2 以降の 3 項目と、acceptance の misread の 1 項目が、印と食い違った。前者は、未定の回答と「## 未決事項」（なし）の組で、ゲートの goal の括弧の範囲の読みで割れる。後者は、食い違いが推論である。どちらも人間が承認した設計（D-17 の 3）の帰結で、人のラベルでも食い違いとして出うる | 第2.2節、第2.3節の 1、付録 | 今は直さない。人のラベルで食い違いが出たら、記述の側（ゲートの goal に「最初の三つの質問の回答」と範囲を書く。承認が要る）か、代表の側（misread の食い違いを、回答の文と直接に食い違う点にする）で直す。どちらを採るかを先に決めておく（第9節の 3、4） |
| E3-L3 | 低 | software\_factory/labeling.py の `upstream`、README の「記述と代表の整合」 | acceptance の上流の違いをペルソナだけにした。持ち帰った問いと未定の回答を含む intake.md かどうかも、acceptance の状態文書と読み（requirements.md と回答の食い違い）を変える上流の違いである。12 項目のうち持ち帰りありは 2 項目だけで、goal と unmet の持ち帰りありの組は材料に無い。盲検で食い違った acceptance の 1 項目は、この形だった | 第2.3節の 1、第4.3節。手引き第15.1節の 1 | acceptance の上流の違いを (ペルソナ, 持ち帰りの有無) にする（最大 12 項目増える。試しのコーパスに無い組は記録する）。足さないなら、足さない理由を README に書く |
| E3-L4 | 低 | labeling.py の EVIDENCE の注釈、README | implement を対象から外した理由（「## 構成」で判断する）が、往復 13 で review を足した理由（記述は節を名指さず、変えた句はインターフェースを述べる）と揃っていない。implement の goal「design.md の構成どおり」は節を名指さず、変えた句「コードを文字列で受け取る」は parse\_code のインターフェースを述べる | 第4.3節。workflow.yaml の implement の goal と quality\_violation | implement の訪問 1（試しの実行に出るクラス）を足すか、外す理由を「goal の「構成」は「## 構成」を指す」と書き、review との違いを記録する |
| E3-L5 | 低 | docs/human-labeling.md の「読み方」 | 盲検のラベラーが共通して迷った点が書かれていない。(1) 記述が証拠とする節と記憶で判断するのか、中身を検算するのか、(2)「（なし）」などの置き書きの数え方、(3) 記述の括弧の列挙の範囲、(4) goal が選択肢に無い時の「goal に優先する」、(5) 訪問 2 以降の持ち帰った問いの見分け、(6) 印を除いた跡（tasks.yaml の「# 」行、review.json の `"marker": ""`、空行）。割れたラベルの多くは (1) と (3) から来る | 第4.2節 | (1) と (3) は人間が方針を決めて書く（第9節の 2）。(2)、(5)、(6) は事実なので、そのまま書き足す（「印を除いた跡が残るが、意味は無い」など）。(6) は、unmarked の後に空になった注釈の行を落としてもよい |
| E3-L6 | 低 | labeling.py の `_label_line` と `parse_labels`、README と human-labeling.md の「ラベルを付けた後」 | 全角のコロン（`ラベル：`）や、読み方の例をバッククォートごと写した行は、項目を示さない traceback で終わる。「ラベル:」の次の行に書いたラベルは、黙って空になる。コマンドを走らせる場所（examples/software-factory/）と `uv run` が書かれていない（リポジトリの根では `No module named 'software_factory'`） | 第4.4節 | 全角のコロンを受け付ける。読めない行は項目の id を添えた誤り（終了コード 2）にする。「ラベル:」の後が空で次の行に文がある時は警告する。手順に「examples/software-factory/ で `uv run python -m software_factory.labeling …`」と書く |
| E3-L7 | 低 | README.md の「記述と代表の整合」、labeling.py の MAIN\_IMPLEMENTATIONS の注釈 | 「requirement\_unmet の代表は…正しい実装 ok\_fixed とは組まない」は markov でだけ正しい。divergent と試しの実行 labeling では組み、その時は代表の「Discount.apply が支払額を切り捨てている」が ok\_fixed のコードと食い違う（手引き第12節）。試しのコーパスに 4 項目ある | 第2.3節の 2。stochastic.yaml の divergent と labeling の分布 | 文を「markov では組まない。divergent と試しの実行では組み、その組は記述と食い違うので材料から外した」に直す。divergent の組は、独立性検証のための本体として許すのか、記録する |

### 本体の側

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| B3-L1 | 低 | docs/adopting.md 第15.1節の 1 と 2 | 「選んだ規則を記録する」とあり、まとめ方は印を含む組で決める。しかし、その規則（印でまとめたこと、組ごとの数）と項目の id（`<実行の id>-<seq>`。遷移の順が分かる）を人に渡す形に出すと、印が推せることが書かれていない。例は規則と id を材料に書いた（E3-M1、E3-L1） | 第4.1節。api-reference.md の `CorpusItem` | 2 の「`item.source` は…人に渡す形からは除く」の後に、「選んだ規則（印でまとめたことと組ごとの数）と項目の id も、人に渡す形に書かない。項目は番号で渡し、番号と id の対応は手元に残す」を足す |
| B3-L2 | 低 | docs/adopting.md 第15.1節の 1 の最初の下位項目（と第12節の「シナリオか E2E の注入で踏む」） | 「シナリオか E2E の注入だけが写す代表」の「注入」は、第14節の定義（分類の結果だけを変える）では、そのクラスの代表を写さない。E2E で代表を写すのは誘発である | 第14節の「誘発の台本が無いクラスは、注入（分類の結果だけを変える）で踏む」 | 「シナリオか E2E の誘発の台本だけが写す代表」にする。第12節の文（クラスを踏む方法）は、注入のままでよい |
| B3-L3 | 低 | docs/decisions.md の D-17 | 状態の行が「6 と第5.8節の注記は未回答」のまま。表の 4（tests\_defective を足す）、6、第5.8節の行にも、D-19 で取り消しや回答があったことが書かれていない。D-17 だけを読むと、tests\_defective が採られたように読める | 第5節。前の判定の B-L4 と同じ形 | 状態の行に「4 は D-19 で取り消し、6 と第5.8節は D-19 で回答」と書き、表の該当の行に「D-19 で置換」を添える（保護ファイルなので計画エージェントが直す） |

## 9. 人間に渡すべき事項

1. **材料を渡す前に、E3-M1 と E3-L1 を直すかを決める。**
   - 直さずに渡すなら、ラベルを付け終えるまで、材料の「選んだ項目」、README の「記述と代表の整合」の表、この報告の付録を読まないよう伝える
   - 材料の分量は 156,390 文字ある。第4.5節の案 1〜2（記述を変えず見せ方だけ）で、約 4 割にできる
2. **ラベルの付け方の方針を決めて、材料に書く（E3-L5 の (1)、(3)）。**
   - 盲検のラベラーは、記述が証拠とする節と記憶だけで判断するか、状態文書の中身（コードが要件を満たすか、食い違いの主張が回答と本当に食い違うか）を検算するかで割れた
   - 方針によって、主経路の REQ-1 の欠陥を含む項目と acceptance の misread の項目のラベルが変わる。方針が決まっていないと、κ に、記述の問題とラベラーの方針の違いが混ざる
3. **discovery のゲートの訪問 2 以降は、人のラベルでも unknown が出うる。**
   - 盲検では 3/3 が unknown になった。ゲートの goal の「intake.md の回答（利用者、割引の種類と上限、無効なコードの扱い）がすべて…反映」の括弧が範囲を限るかで割れた
   - analyze の goal（網羅を求めない）では goal で一致した
   - D-17 の 3 でペルソナの設計（未定の回答は analyze が尋ね返す問いでだけ入る）は承認されている。ゲートの記述の範囲（最初の三つの質問だけか）を、人のラベルの前に決めておくとよい
   - 同じ組は acceptance にも届くが、材料にはほとんど入っていない（E3-L3）
4. **acceptance の requirement\_misread の代表の食い違いは推論である。**
   - 盲検では 2/3 が misread（確信 中）、1/3 が unknown（確信 低）になった
   - 記述の優先の文（requirement\_gaps に列挙されていればこの状態）で読めば misread、第一文（回答と食い違う点がある）で読めば揺れる
   - 完了判定の二回目でも渡した点で、往復 10 では根拠の参照を REQ-3 に移しただけである
5. **往復 10 で足した代表 plan\_tasks/incomplete は、人に渡す材料に無い。**
   - D-19 の 4a の列挙にも無い。エージェントが記述だけで読み（README、この報告の第2.3節の 4）、design\_incomplete に当たるとした。ただし REQ-3 は parse\_code が受け持てるという揺れがある
   - 人が読むかを決める。読むなら、シナリオで分類器が見る状態文書を、印を除いて渡す
6. **主経路の実装は REQ-1 に反する（D-17 の 5 で承認）。**
   - 材料の unit\_test、acceptance、review の項目で、人もこの欠陥に気づくはずである。盲検のラベラーは全員が気づき、記述が証拠とする節と記憶に従ってラベルを付けた
   - あわせて、review の changes\_requested の代表の指摘「Cart.total が…数量の誤りを区別できない」は、前提が事実と合わない（数量の ValueError を出すのは Cart.add）と指摘された。往復 10 の差分の外で、前からある
7. **材料の対象の範囲（E3-L3、E3-L4）。** implement と、acceptance の持ち帰りありの組を足すかを決める。足すと 49 → 最大 65 項目ほどになる
8. **D-17 の古い行（B3-L3）。** 計画エージェントが直す
9. 往復 10〜13 の直しは、検証役と別のモデルのレビューを、計画の側が公開の文書の語で渡したもの（review-findings.md の G、D-15 の経路）に基づく。往復 11〜13 で分かった一般の不足（N14、N16、N17）は手引き第13節と第15.1節に入ったので、次の利用者は手引きだけで知れる

## 10. 実行したコマンドと出力の要旨

- `bash scripts/check.sh`（複製の上で）: 終了コード 0。ruff、ruff format（100 ファイル）、mypy（42、21、12 ファイル）、pytest 662 件が通過、runtime の行カバレッジ 90% 以上、wheel の中身。2 分 27 秒
- 整合性検査のコマンド: `0 error(s), 0 warning(s)`
- `pytest --collect-only -q examples/software-factory`: 199 件
- `git diff --quiet 08f79b4 HEAD -- examples/software-factory/workflow.yaml`: 真
- import の AST 解析と `__all__` との照合（自前のスクリプト）: 公開でない名前は 0
- 追加行の語の検索（plan.md、decisions.md、reports/、決定の番号、src のパス）: adopting-gaps.md の宣言の一か所だけ
- コミットごとの変更の範囲（`git show --name-only`）: 本体と例は分かれている
- 試しのコーパスの作り直し（`labeling.trial_corpus`）
  - 242 項目、変えた代表を含む 220、`wanted` 122
  - acceptance の unmet と ok\_fixed の組 4
  - acceptance の (印, ペルソナ) ごとの持ち帰りの有無
- 項目の id の関係から印を推す数え上げ（自前のスクリプト）: 8 項目、すべて印と一致
- 材料の分量と繰り返しの数え上げ（自前のスクリプト）: 156,390 文字。状態文書の区切りは 360 で、違う内容は 17,412 文字。対象ごとに共通の区切りと選択肢を一度にすると、約 65,100 文字
- 盲検の写しの作成と、四つのサブエージェントによるラベル付け。その後 `labels --labeler agent-blind` → 49 件、`compare` → κ 0.892、食い違い 4。埋めた状態で `pytest tests/test_labeling.py` は 9 件が通過
- ラベルの行の書き方の境界の試し 6 通り（第4.4節）
- 変異 4 個（第6節。すべて落ちた）と、変異 A の対照（新しい一行を除くと通る）、変異 B の対照（08f79b4 に当てると 2 件だけ落ちる）

## 触ったファイル

- 書いた: reports/f4-delta-review.md（このファイル）だけ。元の作業ツリーでは、ほかのファイルを変えておらず、テストも実験も走らせていない（終わりに `git status` が空であることを確かめた）
- 副作用
  - 検証役の scratchpad に自分専用のディレクトリ f4d/ を新しく作った。中身は次のとおり
    - リポジトリの複製二つ（repo/、mut/）
    - 実験のスクリプト（scripts/ の imports.py、idleak.py、volume.py、volume2.py、blind.py）
    - 盲検の写しと結果（blind/ の part\_A〜D.md、mapping.json、labels.txt、agent-blind-labels.jsonl）
    - check.sh の出力（check.log）と、境界の試しの作業ディレクトリ（edge/）
  - 複製の上で書き入れたラベルと human-labels.jsonl は、試しの後に戻した（どちらの複製も `git status` が空）

## 付録 盲検のラベルの食い違い（人間がラベルを付け終えるまで読まない）

エージェントのラベルで、人手のラベルではない。

| 材料の項目 | 対象 | 上流 | 印 | 盲検のラベル（確信） | ラベラーの理由の要旨 |
| --- | --- | --- | --- | --- | --- |
| 22 | discovery のゲート（analyze の訪問 2 の後） | precise\_pm、持ち帰った問いに「来月の末に決める」「法務と相談してから決める」 | goal | unknown（中） | 持ち帰った二つの回答が未定なのに、requirements.md に反映も「## 未決事項」も無い。goal の括弧の三つで尽きると読めば goal |
| 23 | 同（訪問 2 の後） | terse\_engineer、「未定」「未定（後で決める）」 | goal | unknown（中） | 同上 |
| 24 | 同（訪問 3 の後） | vague\_founder、「そのうち考えるよ」「まだ決めてない」 | goal | unknown（中） | 同上 |
| 43 | acceptance の訪問 1 | vague\_founder、持ち帰った問いと未定の回答あり | requirement\_misread | unknown（低） | 列挙された点（大文字と小文字の扱いが無く pct10 を拒む）は、どの回答とも食い違わない（回答の例は大文字だけで、「使えないコードはエラーにして」と合う）。本当の食い違い（未定の回答と「## 未決事項」（なし））は列挙されていない。列挙の有無だけを見れば misread |

ほかの 45 項目は印と一致した。一致した項目のうち、ラベラーが確信を「中」以下とし、理由に揺れを書いたのは次のとおり。

- acceptance の misread の 2 項目（食い違いが推論）
- unit\_test の defective の 2 項目（ok と ok\_b。記録されていない REQ-1 の欠陥）
- review の design\_flaw と changes\_requested（「## 対応」がインターフェースに入るか。指摘の前提）
- design の requirements\_gap（REQ-3 を問いに含めるのは弱い）
- analyze と discovery のゲートの一部（REQ-4 と PCT0 の根拠が暗黙、未定の回答）
- intake の訪問 2 の goal（保留の回答を回答に数えるか）
