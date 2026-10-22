# F4 完了判定 二回目（検証役）

- 日付: 2026-10-22
- 対象: コミット 115149b（「F4 往復 9: N13 は解消し、adopting-gaps.md の「未解消」が空になった」）。一回目の判定（reports/f4-completion.md、32b4d68）からの差分を `git diff 32b4d68 115149b` で読んだ（docs/progress.md は除いた）。元の作業ツリーには docs/progress.md の未コミットの変更があるが、ほかのファイルには変更が無い。HEAD の内容を見た
- 役割: 検証役（第三者、plan.md 第5.9節）。成果物と仕様だけを読み、実装の作業過程は見ていない。docs/progress.md（計画エージェントの作業ログ）は読んでいない
- 読んだもの
  - 完了条件と目的: docs/plan.md 第5〜6節（F4）と第7節の二つ目のプロンプト
  - 前の判定: reports/f4-completion.md（全文）、reports/f4-criteria-review.md（全文）、reports/f4-workflow-review.md（総合判定と、往復 8 の変更に関係する H-1、H-2、M-5〜M-8）
  - 成果物: examples/software-factory/ の差分のすべてと、workflow.yaml、tests/stochastic.yaml、software\_factory/design.py、stages/probabilistic.py、tests/test\_stochastic.py、test\_e2e.py、test\_independence.py、test\_oracle.py、tests/conftest.py、tests/expectations/ の四つ、README.md、docs/review-findings.md、docs/adopting-gaps.md、examples/software-factory/docs/progress.md（利用者の作業ログ）
  - 本体と文書: 差分のある docs/adopting.md、docs/api.md、docs/api-reference.md、docs/changelog.md、docs/decisions.md（D-11 の D4 の行と D-16 の表）、scripts/api\_reference.py、src の markov.py。遷移の規則は runtime/runner.py（遷移、辺の回数、ゲート、評価）で確かめた。contract/ と schema/ には差分が無い
- 実験の環境
  - scratchpad に自分専用の新しいディレクトリ f4c2/ を作り、そこにリポジトリを複製した（git clone、115149b）。`uv sync --locked` の環境（Python 3.12.3）で行い、元の作業ツリーでは pytest も check.sh も走らせていない。`HTF_RUNS` は外した
  - 変異の実験は、もう一つの複製（f4c2/mut/）の上で一つずつ行い、`git checkout` で戻した（最後に `git status` が空であることを確かめた）
  - 参照値は、フレームワークを import しない自前の模型で計算した。模型は workflow.yaml と tests/stochastic.yaml だけを読む。実行には scratchpad に前からあった環境 refenv/（numpy 2.5.4、scipy 1.18.1、scikit-learn、PyYAML 6.0.3）を読むだけに使い、何も入れていない
  - 実際のランタイム: 400 回ずつ互いに重ならない種のブロックで、markov を 200 ブロック（種 4,000,000〜4,079,999）、ゲートを揺らす実行を 200 ブロック（種 5,000,000〜5,079,999）、計 160,000 回。divergent を 24 ブロック（種 6,000,000〜6,009,599）。ほかに既定の種（20000、50000、30000）
- 人間のゲート（workflow.yaml のレビューと承認）は判定しない

## 総合判定: 正常

第6節 F4 の完了条件（人間の承認を除く）は、今のコミットでもすべて満たしている。整合性検査は誤りも警告も無く通り、`scripts/check.sh` は複製の上で通った（638 件が通過、例のテストは 177 件）。一回目に「準正常」とした理由の、例の側の中の二つは直っている。

- E-M1（記述と代表の三つの食い違いと REQ-2 の下限）: (1)、(3)、(4) は成果物とペルソナの回答の直しで解消した。(2) は、成果物の直しではなく、plan\_tasks の確率的な分布から design\_incomplete の変種を外す形で対応された。この対応は妥当と判断する（第1.2節）。クラスはワークフロー定義に残り、E2E のカバレッジで注入して踏まれ、分布テストの基準は設計値から正しく導き直されている（第2節）。ただし、人間に渡す理由づけに一つ不正確な所がある（E2-L2）
- E-M2（discovery のゲートの goal を代表が満たさない）: requirements.md に「## 利用者」の節を設けて解消した。字義の上で「要件か受け入れ基準に」と読むと、まだ一点の揺れがある（E2-L5、低）

分布テストの基準は承認する。中心、E[n]、標準誤差、幅の倍数は、自前の独立な計算と一致した（`synthesize` とは 1e-14 の桁まで一致）。ずらした基準は、既定の種でも、種を変えた 200 ブロックずつでも、すべて落ちた。注記に一か所、誤った倍数がある（E2-L1、低）。

読取制限は守られている。往復 8・9 で例が足した import（`IndependenceResult`、`EntryDependenceResult`）も公開の `__all__` にあり、本体の内部の名前や内部の文書は例に現れない。

本体の側の指摘 B-L1〜B-L5 は直り、B-L6 は以後のコミットで守られている。changelog.md の「未公開」は、v0.1.0 からの公開 API と公開の文書の変更を漏れなく載せている。

判定の規則は一回目と同じにした。完了条件を満たし、高と中の指摘が残っていなければ正常、完了条件を満たしても中以上の指摘が残れば準正常とする。新しい指摘は、本体の側に低 1、例の側に低 5 で、高と中は無い（第8節）。人間のレビューに渡す事項は第9節にまとめた。

## 1. 一回目の指摘への対応

### 1.1 例の側

| 指摘 | 判定 | 証拠 |
| --- | --- | --- |
| E-M1 (1) acceptance の requirement\_misread の前提が precise\_pm の回答にしか無い | 直った | 三つのペルソナの「利用者」の回答に、どれも「レジの画面」で入力することが入った（precise\_pm「ネットショップの購入者。レジの画面でコードを入力する」、vague\_founder「お客さん全般かな。レジの画面でコードを打ってもらう感じ」、terse\_engineer「購入者。レジの画面で入力」）。代表の verification.md は、前提を intake.md の回答と requirements.md の「## 利用者」に置く。三つのペルソナの代表に、自分で記述だけを読んでラベルを付け、三つとも requirement\_misread になった（第6節）。食い違いは「人が打つコードには大文字と小文字の揺れが出る」という推論で、回答との直接の矛盾ではない。記述の優先の文（requirement\_gaps に列挙されていれば、表の結果によらずこの状態）で決まる。人のラベル付けで確かめる点として第9節に挙げた |
| E-M1 (2) plan\_tasks の design\_incomplete が design の goal の代表と矛盾する | 対応は妥当（第1.2節）。残りは E2-L2、E2-L3 | 変種を設計値から外し、フィクスチャを消し、E2E のカバレッジで注入して踏む。基準を導き直した |
| E-M1 (3) analyze の goal が vague\_founder の回答と矛盾する | 直った | vague\_founder は「百分率は半分（50%）まで。端数は切り捨てで、引きすぎたら 0 円でいい」「使えないコードはエラーにして、割引しないで」と値を決めて答える。analyze の goal の代表の REQ-1〜REQ-4 は、どのペルソナの回答にも根拠を持つ。三つのペルソナの代表に自分でラベルを付け、三つとも goal になった。ただし vague\_founder の「端数は切り捨て」は、何を切り捨てるか（割引額か支払額か）を言わない（E2-L5） |
| E-M1 (4) REQ-2 の 0 円の下限が最初の回答に根拠を持たない | 直った | 三つのペルソナとも、最初の「種類と上限」の回答に下限を含める（「定額で小計を超えたら 0 円にする」「引きすぎたら 0 円でいい」「下限 0 円」）。needs\_unclear が持ち帰る問いは、どのペルソナも今は決めていない二点（キャンペーンの後も使えるか、同じ購入者が何回使えるか）に替わり、analyze の unclear の代表の「## 未決事項」と記憶 intake\_questions が同じ二つの問いを持つ |
| E-M2 discovery のゲートの goal を goal の代表が満たさない | 直った（字義の揺れが一点。E2-L5） | analyze の ok と unclear の代表の requirements.md に「## 利用者」（購入者がレジの画面で割引コードを入力する）が入った。vague\_founder の上限も 50% に決まった。discovery のゲートの三つのペルソナの項目（訪問 1 と 2）に自分でラベルを付け、どれも goal になった。ただ、ゲートの goal は「requirements.md の要件か受け入れ基準に反映」と書き、「## 利用者」は要件（REQ-n）でも受け入れ基準でもない節にある。README の「人間のレビューで確かめてほしいこと」4 は「requirements.md に反映」と言い換えている |
| E-L1 主経路が REQ-1 の欠陥を持ったままリリースする | 直った（記述の改訂。人間の承認の対象） | assurance のゲートの goal に「判断は verification.md と review.json に基づき、このゲートで repo/ のコードを改めて検証しない」が入り、意図を README の 7 に書いた。assurance のゲートの項目に自分でラベルを付け、goal になった（repo/ の discount.py は支払額を切り捨てているが、記述は repo/ の検証を求めない） |
| E-L2 越境の数え方と、acceptance → analyze のシナリオ | 直った | 15 本目のシナリオ acceptance\_misread\_crosses\_phases（assurance から discovery へ三つのフェーズ境界を越え、三つのゲートを評価し直し、持ち帰った食い違いが最後の記憶に残らない）。test\_crossing\_rollbacks\_from\_every\_later\_phase は定義の上の六本すべてと運用者による越境を求める。このシナリオを消すと、そのテストと test\_committed\_scenarios\_match\_the\_generator の二つが落ちた |
| E-L3 unit\_test の goal がテストへの依頼を見ない | 直った（記述の改訂。人間の承認の対象） | goal が「requirements.md のすべての受け入れ基準と、impl\_notes.md の「## テストへの依頼」のすべてを確かめ」になった。README の 6 |
| E-L4 揺れる分類器の一致率を `approx(0.75, abs=0.05)` で確かめる | 直った | `1 - ceil(n / 4) / n` と一致を確かめる。今のコーパス（123 項目）で 92/123 = 0.747967。自分の計算と一致（第3節） |
| E-L5 memory\_out を毎回書くことを設計値の表でだけ確かめる | 直った | test\_bodies\_write\_memory\_out\_on\_every\_visit が、分布テストの二つの実行の集まりで、印が goal のステージの評価の終了時スナップショットの memory\_out を goal の変種の値と比べる。一回目に生き残った変異（`if value:` の時だけ書く）を入れると、markov と gated の二つがどちらも落ちた（analyze の intake\_questions が None） |
| E-L6 補正の無い alpha 0.01 で全状態を確かめる | 一部直った（残りは E2-L4） | 全状態の確かめは、判定できた検定の数で alpha を割る（Bonferroni）形になった（独立性検証と入り方の検定の両方）。一方、implement に絞った二つの確かめ（入り方の検定の verdict が not\_detected、markov の implement=goal の訪問 1 → 1 が not\_detected）は補正の無い alpha 0.01 のまま残った。種の基点を変えた 200 ブロックずつで、正しい本体でもどれかが落ちるブロックは markov の集まりで 8/200、ゲートを揺らす集まりで 6/200 あった（第2.6節） |

### 1.2 E-M1 (2) の対応は妥当か

**したこと:** tests/stochastic.yaml の plan\_tasks の分布を、markov と divergent の両方で first {ok 0.82, incomplete 0.15, unknown 0.03} → {ok 0.97, unknown 0.03}、again {ok 0.93, incomplete 0.05, unknown 0.02} → {ok 0.98, unknown 0.02} にした。フィクスチャ tests/fixtures/plan\_tasks/incomplete/ を消し、test\_e2e.py の誘発の表から外した。

**同じ種での選び方:** `choose_variant` は変種の名前を並べ替え、`random.Random(seed).choices` で累積の重みから選ぶ。前は [incomplete, ok, unknown] の累積 [0.15, 0.97, 1.0]（again は [0.05, 0.98, 1.0]）、今は [ok, unknown] の [0.97, 1.0]（[0.98, 1.0]）なので、同じ一様乱数で incomplete だった訪問は ok になり、ok と unknown はそのまま。README の「同じ種で incomplete を引いていた訪問は ok になり、ほかの訪問の選び方は変わらない」は正しい。既定の種 20000 で、implement の訪問 1 の分母が 349 → 351、完了が 286 → 287 になったのも、これと合う。

**クラスの被覆:** design\_incomplete はワークフロー定義に残り、辺（plan\_tasks → design、carry design\_issues、max 2）も残る。`coverage_targets` の 30 の対象に入り、`plan_coverage` は注入で踏む（注入するのは intake の unknown、plan\_tasks の design\_incomplete、review の unknown の三つ）。その項目だけを `run_coverage` にかけ、reached が真、missing が空になることを確かめた。test\_coverage\_plan\_reaches\_every\_stage\_class も通る。

**E2E での踏み方:** 注入の項目は、plan\_tasks の訪問 1 に goal の代表（plan\_tasks/ok）を写し、記憶 design\_issues に空の一覧を書かせたうえで、分類を design\_incomplete に決める。辺は通り、design の訪問 2 が空の design\_issues を受けて走る。遷移は確かめられるが、持ち帰る記憶の中身は空で、成果物と分類は食い違ったままである（注入なのでそれ自体は正しい）。tests/scenarios/ と software\_factory/ に design\_incomplete や plan\_tasks/incomplete を参照する所は無い。往復 7 までは確率的な実行がこの辺を空でない design\_issues で何度も通っていたが、今は空でない carry でこの辺を通るテストが無い（E2-L3）。

**分布と合成:** 自前の模型でも、plan\_tasks の分布が変わった後の量を計算し直し、`synthesize` と一致した（第2節）。マルコフ合成の比較は、markov で 45 の量（前は 46）、ゲートを揺らす実行で 46 の量（前は 47）。独立性検証の状態 stage:plan\_tasks=design\_incomplete は無くなった。オラクルのコーパスは 127 → 123 項目になった。

**記述との整合:**

- 理由づけ（plan\_tasks は design の goal の後に走り、goal の代表の design.md はすべての要件を構成のファイルに割り当てるので、それと組んで記述どおりに design\_incomplete になる代表は作れない）は、確率的な本体については正しい。design の goal の代表を二つにして片方の後でだけ design\_incomplete にすると、design=goal というクラスの中で下流の分布が分かれ、markov の本体がマルコフでなくなる（divergent と同じ形）。plan\_tasks の訪問 2 以降は、implement の task\_unclear からも design の入り直しからも入るので、入り方で分布を変えることもできない。markov の本体から外すのが正しい選択である
- ただし README の 1 の「design\_incomplete は、design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」は言い過ぎで、記述の上には正当な経路がもう一つある。implement の task\_unclear は「タスクの paths の外のファイルを変えないと実装できない」場合を含み、plan\_tasks に戻る。plan\_tasks の goal は paths が design.md の「## 構成」のファイルに収まることを求め、description は「変えるファイルを決められない構成要素がある時は design\_issues に書く」とする。実装して初めて構成に無いファイルが要ると分かれば、design の goal を正しく満たした後でも design\_incomplete になりうる（E2-L2）。人間が「この end\_state を残すか」を決める材料として、この経路を添えるべきである
- design\_incomplete には代表が無いので、第15.1節の手順では記述を確かめられない。人間のレビューでは、記述そのものを読んで確かめることになる（第9節）

**判定:** 妥当。クラスの被覆は注入で保たれ、分布テストの基準は正しく導き直され、判断は人間のレビューに回されている。残りは、人間に渡す理由づけの不正確さ（E2-L2）と、空でない carry で辺を通るテストが無いこと（E2-L3）で、どちらも低。

### 1.3 本体の側

| 指摘 | 判定 | 証拠 |
| --- | --- | --- |
| B-L1 第15.1節がゲートの項目を含めるかを書いていない | 直った | 手順 2 に「ステージの項目だけでなく、ゲートの項目も含める」、手順 1 に「上流の違い（ユーザーシミュレータのペルソナなど）で同じ代表の状態文書が変わるなら、それぞれが別の項目になる」、手順 3 に、ゲートの項目で人のラベルが goal でなければフェーズの goal の記述と代表が食い違う、が入った。手順 3 の「いつも goal を答える」には小さな不正確さがある（B2-L1） |
| B-L2 visits\_variance の説明 | 直った | api.md の `Prediction` の行、adopting.md 第12節、markov.py の docstring（と生成した api-reference.md）が「実行ごとの訪問の回数（一度も訪れない実行は 0）の、実行の間での分散」になった。例の software\_factory/design.py の docstring は前の言い方のまま（E2-L1 に含めた） |
| B-L3 公開の範囲の明記が changelog に無い | 直った | 「互換性に注意する変更」に一行。`StageContext` の公開の名前（stage\_id、visit、workspace、seed、read\_memory、write\_memory、user\_io、llm）は contract の Protocol と一致し、`RunState` の to\_json、from\_json、current、pending は docstring と adopting.md 第7節の使い方と一致する |
| B-L4 D-11 の D4 の行が覆されたまま | 直った | 「置換（D-12 の N5 で解消。`RandomGateClassifier`）。以下はこの表を書いた時の判断で、後半は誤り」 |
| B-L5 api-reference.md の `SCHEMA_FILES` が切れる | 直った | scripts/api\_reference.py は、文字列の組と列を切り詰めない。8 つのスキーマのファイル名がすべて出る。生成物との一致は tests/test\_docs.py が確かめ、通る |
| B-L6 本体と例の変更が一つのコミットに混ざる | 守られている | 32b4d68 の後の 5 つのコミットは、f93fd31（本体の文書、scripts、src、reports）、76ab78f（例の docs/review-findings.md だけ。計画の側が D-15 の経路で渡したもの）、d2ebc85（例だけ、27 ファイル）、6220773（本体の文書だけ）、115149b（例だけ）で、混ざっていない。D-16 の表に記録がある |

## 2. 基準の確認

### 2.1 方法

- workflow.yaml と tests/stochastic.yaml だけを読む模型を自分で書いた（フレームワークを import しない）。遷移の規則は runtime/runner.py で確かめた: 訪問の番号はステージごとに数えて戻らない。分布の区分は訪問 1 なら first、2 以降なら again（release は carry の有無で、自分自身への辺しか無いので訪問の区分と一致）。goal なら次へ、フェーズの最終ステージなら続けてゲートを評価（ゲートの訪問は最終ステージの訪問）。unknown は中止。end\_state は辺（ステージ/状態）ごとの回数が max 以上なら中止、そうでなければ 1 増やして戻る。ゲートの end\_state は最終ステージの同じ名前の辺を使う。markov の unit\_test の変種 defect はいつも impl\_defect
- 厳密な計算: 状態（いまのステージ、訪問の回数、辺ごとの回数）を後ろから再帰でたどった（`synthesize` は前へ流すので別の方法）。状態は markov とゲートを揺らす実行でそれぞれ 101,003 個
  - `synthesize(design_model(...))` との差: markov は (scope, 対象, 区分) の評価の数で最大 3.3e-15、(scope, 対象, 区分, 結果) の 68 の量で最大 3.1e-15、完了の確率 4.2e-15、implement の訪問の回数の分散 1.8e-15。ゲートを揺らす実行は 70 の量で最大 4.2e-15、平均 1.2e-14
  - 完了 0.694154（ゲートあり 0.666231）、implement の訪問の回数の平均 1.673485、分散 1.358292（標準偏差 1.16546）。ゲートありは 1.887174、1.818179（1.34840）
- 標本: 同じ規則の模擬を 400 回 × 24,000 試行ずつ（計 9,600,000 回ずつ）走らせ、誤判定の割合を出した。20 万回の模擬の平均が厳密な値と合うことも確かめた
- 実際のランタイム: 冒頭の「実験の環境」の 200 ブロックずつ。本体の例外、契約違反、範囲外のファイルの警告、指標の測定の失敗は 160,000 回で一度も無かった

### 2.2 markov.yaml（runs 400、種 20000）

倍数は「設計値から min まで」と「設計値から max まで」を SE で割ったもの（0 と 1 で切る側は除く）。

| 基準 | 中心（注記 / 自分） | E[n]（注記 / 自分） | SE（注記 / 自分） | 倍数 下・上（注記 / 自分） | 判定 |
| --- | --- | --- | --- | --- | --- |
| intake 訪問 1 = unknown [0.0, 0.06] | 0.03 / 0.0300 | 400 / 400.00 | 0.0085 / 0.00853 | 上 3.5 / 上 3.52 | 一致 |
| analyze 訪問 1 = needs\_unclear [0.17, 0.33] | 0.25 / 0.2500 | 388.0 / 388.00 | 0.0220 / 0.02198 | 3.6 / 3.64・3.64 | 一致 |
| implement 訪問 1 = goal [0.64, 0.80] | 0.72 / 0.7200 | 346.4 / 346.40 | 0.0241 / 0.02412 | 3.3 / 3.32・3.32 | 一致 |
| implement 訪問 2 以降 = goal [0.84, 0.96] | 0.90 / 0.9000 | 323.0 / 322.99 | 0.0167 / 0.01669 | 3.6 / 3.59・3.59 | 一致 |
| unit\_test 訪問 1 = impl\_defect [0.14, 0.30] | 0.22 / 0.2200 | 333.2 / 333.25 | 0.0227 / 0.02269 | 3.5 / 3.53・3.53 | 一致 |
| unit\_test 訪問 1 = tests\_insufficient [0.12, 0.28] | 0.20 / 0.2000 | 333.2 / 333.25 | 0.0219 / 0.02191 | 3.7 / 3.65・3.65 | 一致 |
| acceptance 訪問 1 = requirement\_unmet [0.04, 0.16] | 0.10 / 0.1000 | 316.2 / 316.24 | 0.0169 / 0.01687 | 3.6 / 3.56・3.56 | 一致 |
| review 訪問 1 = changes\_requested [0.07, 0.21] | 0.14 / 0.1400 | 301.6 / 301.56 | 0.0200 / 0.01998 | 3.5 / 3.50・3.50 | 一致 |
| release 訪問 1 = notes\_incomplete [0.15, 0.31] | 0.23 / 0.2300 | 285.3 / 285.34 | 0.0249 / 0.02491 | **3.6** / **3.21・3.21** | 値は規則を満たすが、注記の倍数が誤り（E2-L1） |
| release 訪問 2 以降 = goal [0.88, 1.0] | 0.97 / 0.9700 | 65.6 / 65.63 | 0.0211 / 0.02106 | 下 4.3 / 下 4.27 | 一致。二項分布（n = 66、p = 0.97）の下側の裾は min 0.88 で 0.080%、0.90 で 0.362%（注記どおり） |
| status\_rate completed [0.62, 0.77] | 0.6942 / 0.694154 | 400 | 0.0230 / 0.02304 | 3.2・3.3 / 3.22・3.29 | 一致 |
| mean\_visits implement [1.48, 1.86] | 1.674 / 1.673485 | 400 | 0.0583 / 0.05827 | 3.3・3.2 / 3.32・3.20 | 値は一致。注記の分散 1.360、標準偏差 1.166 は 1.358、1.165（E2-L1） |

- release の訪問 1: 往復 7 までは [0.14, 0.32]（E[n] 283.0 で 3.6 SE。基準の確認の L2 で直した値）だった。E[n] が 285.3 になり、設計値 ± 3.2 SE が [0.15029, 0.30971] になったので、規則（3.2 倍以上をとり、0.01 の単位で外側に丸める）どおりに [0.15, 0.31] に狭めた。値は規則に合う（3.211 SE。規則の境から 0.011 SE）が、注記は前の「両側 3.6 SE」のままである。誤って落ちる確率は 0.135% で、正規近似で幅を決めた基準の中でいちばん大きい
- visit で絞った基準の E[n] は、400 × そのステージに一度でも達する確率（implement 0.86601、unit\_test 0.83312、acceptance 0.79061、review 0.75391、release 0.71334）と一致する。release の訪問 2 以降は 400 × 0.16407
- 中心、E[n]、SE の注記の値は、ほかはすべて丸めの範囲で一致した

### 2.3 markov\_gated.yaml（runs 400、種 50000、assurance のゲート {goal: 0.8, changes\_requested: 0.2}）

| 基準 | 中心（注記 / 自分） | E[n]（注記 / 自分） | SE（注記 / 自分） | 倍数 下・上（注記 / 自分） | 判定 |
| --- | --- | --- | --- | --- | --- |
| ゲート assurance 訪問 1 = changes\_requested [0.11, 0.29] | 0.20 / 0.2000 | 235.2 / 235.22 | 0.0261 / 0.02608 | 3.4 / 3.45・3.45 | 一致（丸めた SE で割ると 3.45） |
| ゲート assurance 訪問 2 以降 = changes\_requested [0.07, 0.33] | 0.20 / 0.2000 | 107.1 / 107.11 | 0.0387 / 0.03865 | 3.4 / 3.36・3.36 | 一致 |
| status\_rate completed [0.59, 0.75] | 0.6662 / 0.666231 | 400 | 0.0236 / 0.02358 | 3.2・3.5 / 3.23・3.55 | 一致 |
| mean\_visits implement [1.67, 2.11] | 1.887 / 1.887174（標準偏差 1.348 / 1.34840） | 400 | 0.0674 / 0.06742 | 3.2・3.3 / 3.22・3.31 | 一致 |

- 注記の「ゲートを揺らさない本体でも status\_rate は 99%、mean\_visits は 52% ほど通る」は、正規近似で 99.2% と 52.4% になり、合う

### 2.4 ずらした基準

| 基準 | 注記 | 自分 | 正しい幅との関係 |
| --- | --- | --- | --- |
| intake unknown [0.08, 0.20] | 上へ 5.9 | 5.86 | 離れている |
| analyze needs\_unclear [0.36, 0.50] | 上へ 5.0 | 5.00 | 離れている |
| analyze needs\_unclear [0.0, 0.16] | 下へ 4.1 | 4.09 | 0.01 の隙間 |
| implement 訪問 1 goal [0.84, 1.0] | 上へ 5.0 | 4.97 | 離れている |
| implement 訪問 2 以降 goal [0.70, 0.83] | 下へ 4.2 | 4.19 | 0.01 の隙間 |
| unit\_test impl\_defect [0.03, 0.13] | 下へ 4.0 | 3.97 | 0.01 の隙間 |
| unit\_test tests\_insufficient [0.30, 0.45] | 上へ 4.6 | 4.56 | 離れている |
| acceptance requirement\_unmet [0.18, 0.30] | 上へ 4.7 | 4.74 | 離れている |
| review changes\_requested [0.0, 0.06] | 下へ 4.0 | 4.00 | 0.01 の隙間 |
| release notes\_incomplete [0.0, 0.13] | 下へ 4.0 | 4.01 | 0.02 の隙間 |
| release 訪問 2 以降 goal [0.65, 0.85] | 下へ 5.7 | 5.70 | 離れている |
| status completed [0.80, 1.0] | 上へ 4.6 | 4.59 | 離れている |
| mean\_visits implement [1.95, 2.50] | 上へ 4.8 | **4.74** | 離れている（注記は 4.7 が正しい。E2-L1） |
| mean\_visits implement [1.0, 1.40] | 下へ 4.7 | 4.69 | 離れている |
| ゲート訪問 1 changes\_requested [0.35, 0.50] | 上へ 5.7 | 5.75 | 離れている |
| ゲート訪問 1 changes\_requested [0.0, 0.10] | 下へ 3.8 | 3.83 | 0.01 の隙間 |
| status completed（ゲートあり）[0.76, 0.90] | 上へ 4.0 | 3.98 | 0.01 の隙間（端を共有しないように 0.75 → 0.76 にした） |

正しい幅と端を共有するものは無い。設計値が幅の中に入るものも無い。

### 2.5 既定の種での実行

- markov.yaml（種 20000）: 12 基準すべて通る。intake 0.015（6/400）、analyze 0.246（97/394）、implement 訪問 1 0.698（245/351）、訪問 2 以降 0.926（324/350）、impl\_defect 0.223（75/336）、tests\_insufficient 0.211（71/336）、requirement\_unmet 0.101（33/326）、changes\_requested 0.181（57/315）、release 訪問 1 0.214（64/299）、訪問 2 以降 0.969（62/64）、完了 0.7175、implement の訪問の回数 1.7525。markov\_shifted.yaml の 14 基準はすべて落ちる
- markov\_gated.yaml（種 50000）: 4 基準すべて通る。ゲート訪問 1 0.209（45/215）、訪問 2 以降 0.156（17/109）、完了 0.625、訪問の回数 2.0025。markov\_gated\_shifted.yaml の 3 基準はすべて落ちる
- どちらも利用者の作業ログの値と同じ

### 2.6 誤判定の割合

「模型」は自前の模型で落ちる確率。分母が一回の実行に 0 か 1 の基準（訪問 1、release の訪問 2 以降、ゲートの訪問 1）と status\_rate は二項分布の混合で厳密に出した（分母が min\_samples 30 未満なら落ちるとした）。ほかは 24,000 試行の標本。「実際」は実際のランタイムの 200 ブロックで落ちた数。

| 基準 | 模型 | 実際（/200） |
| --- | --- | --- |
| intake 訪問 1 unknown | 0.055% | 0 |
| analyze 訪問 1 needs\_unclear | 0.027% | 0 |
| implement 訪問 1 goal | 0.090% | 0 |
| implement 訪問 2 以降 goal | 0.063%（標本） | 0 |
| unit\_test 訪問 1 impl\_defect | 0.044% | 0 |
| unit\_test 訪問 1 tests\_insufficient | 0.028% | 0 |
| acceptance 訪問 1 requirement\_unmet | 0.048% | 0 |
| review 訪問 1 changes\_requested | 0.053% | 0 |
| release 訪問 1 notes\_incomplete | 0.135% | 0 |
| release 訪問 2 以降 goal | 0.056%（前の min 0.90 なら 0.355%） | 0 |
| status completed | 0.095% | 0 |
| mean\_visits implement | 0.088%（標本） | 0 |
| ゲート訪問 1 changes\_requested | 0.062% | 1（種 5,039,200 で 68/234 = 0.291、上へ 3.5 SE） |
| ゲート訪問 2 以降 changes\_requested | 0.117%（標本） | 0 |
| status completed（ゲートあり） | 0.071% | 0 |
| mean\_visits implement（ゲートあり） | 0.075%（標本） | 0 |

| 基準の集まり | 模型（24,000 試行） | 実際（200 ブロック） |
| --- | --- | --- |
| markov.yaml: どれかが落ちる | 0.80%（192） | 0/200（Wilson 95% [0%, 1.9%]） |
| markov\_gated.yaml: どれかが落ちる | 0.32%（77） | 1/200 = 0.5%（[0.09%, 2.8%]） |
| markov\_shifted.yaml: どれかが通る | 0.033%（8。implement 訪問 2 以降 5、release 訪問 2 以降 2、review 1） | 0/200 |
| markov\_gated\_shifted.yaml: どれかが通る | 0%（0） | 0/200 |

- 基準の確認（87f03d5）の時の markov.yaml の 1.16% から 0.80% に下がった。主に release の訪問 2 以降を min 0.88 にした効果（0.367% → 0.056%）
- 実際のランタイムの 200 ブロックの観測値の標準偏差は、SE と比 0.92〜1.09 で合う（200 ブロックでの標準偏差の相対誤差は約 5%）。分母の最小は release の訪問 2 以降で 50、ゲートの訪問 2 以降で 80 で、min\_samples 30 を下回らない
- 独立性検証と入り方の検定（E-L6 の確かめ）: 正しい本体で、補正の無い alpha 0.01 で violated が出たブロックは、独立性検証が markov 10/200・ゲートあり 15/200、入り方の検定が 8/200・11/200。Bonferroni では、独立性検証が 1/200・0/200、入り方の検定が 4/200・3/200。implement の入り方の検定が not\_detected でないブロックは 3/200・4/200。例のテストのどれかが落ちるブロックは、markov の集まりで 8/200（4%）、ゲートを揺らす集まりで 6/200（3%）（E2-L4）

### 2.7 判定

基準は承認する。四つの基準の集まりは設計値から正しく導かれ、幅は規則（設計値の両側に 3.2 SE 以上、テストの 3〜5 SE、歪む基準は二項分布の裾 0.1% 以下）を満たし、ずらした基準はすべて落ちる。注記の誤り（E2-L1）は値に影響しないが、基準の根拠の記録なので直すとよい。

## 3. 完了条件の判定

| 完了条件 | 判定 | 証拠（一回目からの変化を中心に） |
| --- | --- | --- |
| workflow.yaml が整合性検査を通る | 満たす | 複製の上で `PYTHONPATH=examples/software-factory python -m harness_testing_framework.testing.spec examples/software-factory/workflow.yaml --registry software_factory.metrics:REGISTRY` → `0 error(s), 0 warning(s)`、終了コード 0 |
| 4 フェーズ以上、8 ステージ以上 | 満たす | 5 フェーズ、9 ステージ（変わらない） |
| フェーズ境界を越えるロールバック 1 以上 | 満たす | 定義の上で 6 本。今は 6 本すべてと運用者による越境（release → implement）をシナリオで通す（15 本目の acceptance\_misread\_crosses\_phases で acceptance → analyze が加わった） |
| ユーザー待ちのステージ 1 以上 | 満たす | intake。中断と再開のシナリオと、ペルソナが保留して再開するテストが通る |
| 実在のツールに裏づけられた決定論指標 3 以上 | 満たす | build\_passes、tests\_pass、line\_coverage、lint\_errors と out\_of\_scope\_changes。metrics.py と test\_metrics.py は一回目から変わっていない。160,000 回の実行で測定の失敗は無かった |
| 参照ランタイムを組み込み、契約適合テストを通す | 満たす | test\_conformance.py（同梱の 25 シナリオ）が通る。160,000 回の実行で契約違反、本体の例外、範囲外のファイルの警告は無かった。判定の対象の読み方は一回目の第10節の 6 のまま（第9節） |
| 全ランナーが通る: 6 種の遷移 | 満たす | test\_all\_six\_transition\_kinds（15 シナリオ）、escalate の四択 |
| 確率的な偽の本体に対する分布テスト | 満たす | 第2節。既定の種で正しい基準が通り、ずらした基準がすべて落ちる。種を変えた 200 ブロックずつでも、ずらした基準が通ったブロックは無い |
| 仕込んだ粗いクラスの検出 | 満たす | divergent（種 30000）は stage:implement=goal の訪問 1 → 1 で violated（p = 0.0005、代表 126 と 137）。種の基点を 24 通り変えて 24/24 で violated（どれも p = 0.0005）。markov の同じ状態は not\_detected（p = 0.229） |
| (stage, end\_state) のカバレッジ 100% | 満たす | 30 の対象をすべて踏み、missing が空。計画は 22 項目（全ステージが goal の実行 1 と誘発 18、注入 3。注入は intake の unknown、plan\_tasks の design\_incomplete、review の unknown）。design\_incomplete は往復 8 から注入（第1.2節） |
| マルコフ予測と実測の一致 | 満たす | 設計値のモデルと markov（種 20000）の実測は 45 の量すべてが 4 標準誤差以内（最大 \|z\| 2.30、visits:review）。ゲートの分布を足したモデルとゲートを揺らした実行は 46 の量すべて（最大 3.03、outcome:review=changes\_requested）。推定したモデルの比較と entry\_dependence のテストも通る |
| 偽の分類器に対するオラクル検証 | 満たす | コーパス 123 項目（markov の最初の 60 回、ステージの項目）。ROWS の配分から自分で組み立てると、p\_o 0.723577、p\_e 0.304316、κ 0.602660（scikit-learn の `cohen_kappa_score` も 0.602660）、答えた 117 項目の ECE 0.274872、答え無し 6、揺れる分類器の一致率 92/123 = 0.747967。フレームワークの `oracle_report` と利用者の作業ログの値（κ 0.603、ECE 0.275、答え無し 6、0.748）と一致した。印を読む分類器は κ 1、ECE 0.1 |
| トリアージの一周 | 満たす | test\_one\_round\_of\_triage が通る（一回目から変わっていない） |
| adopting-gaps.md の全項目が本体で解消されるか、解消しない理由が decisions.md にある | 満たす | 未解消は無し。N13 は D-16 の表（「解消（文書）、adopting.md 第12節」）で扱われ、第12節に「代表は、届きうるすべての上流の成果物と整合させる」が入り、changelog.md にも載った。解消しないのは D2 だけで、理由は D-11 と D-12 の N6 にある（一回目と同じ） |
| 人間が workflow.yaml をレビューして承認 | 判定しない | 人間のゲート |

第7節の二つ目のプロンプトが求めたもの（一回目の第2節）は、ペルソナ 3 つ以上（三つのまま。ただし性格が変わった。第9節の 4）を含めて、すべて揃ったままである。

## 4. 読取制限

### 4.1 import の解析

examples/software-factory/ の Python ファイル 19 個（tests/fixtures/ の下を除く）を AST で読み、`harness_testing_framework` からの import をすべて集め、9 つの公開モジュールの `__all__`（実行時に読んだもの）と照合した。

- すべて `__all__` にある。往復 8 で足されたのは testing.stages の `IndependenceResult` と `EntryDependenceResult`（software\_factory/design.py の `family_wise_violations`）だけ
- `import harness_testing_framework.…` の形、`import_module`、`__import__` は無い
- 先頭が `_` の属性への参照は `_measures`（metrics.py）と `_RESULTS`（test\_metrics.py）で、どちらも例自身のモジュールのもの
- 新しいコードが本体のオブジェクトに使う名前（`store.get_snapshot`、`Snapshot.memory`、`Stage.memory_out`、`r.p_value`、`r.state`、`r.stage`、`r.visit`、`r.verdict`、`run.events`、`report.rerun_agreement`）は、どれも api-reference.md にある

### 4.2 語の検索

- src/ のファイル名: 例の中に現れない
- src/ の最上位の名前のうち、どの `__all__` にも無い 77 個: 現れたのは GOAL、classify、main、measure、options、sha256、`__version__` だけで、一回目と同じく一般の語、公開の操作の名前と同じつづり、フィクスチャのコードベースの属性である
- 決定の番号、plan.md、decisions.md、progress.md、reports/、`harness_testing_framework/`、`src/harness`: 一回目と同じ所（adopting-gaps.md の第5行・第51行・第67行の「読まない」宣言と「検索した」という記述、progress.md の第5行の読取の制限、README の docs/progress.md の説明）にだけ現れる。往復 8・9 の追記と docs/review-findings.md の E の節には現れない
- docs/review-findings.md の E の節は、計画の側が公開の文書の語で渡したもの（D-15 の経路）。検証役の報告のパスや決定の番号は書かれていない

判定: 読取制限が破られた証拠は無い。

## 5. 第15.1節の手順を自分で試した

### 5.1 方法

- markov（種 20000）とゲートを揺らす実行（種 50000）の各 400 回を一つの置き場で走らせ、`build_corpus(..., unique_states=True)` で 351 項目（ステージ 274、ゲート 77）。(scope, 対象, 印, ペルソナ) ごとに一つを選ぶと 56 項目（ステージ 47、ゲート 9）で、利用者の試しと同じ分け方になった
- そのうち 16 項目について、`unmarked(item.state)` と選択肢の記述だけを読んでラベルを付け、`oracle_report(MarkerClassifier(), 項目, ラベル)` をかけた
- 留保: 項目の一覧（群の鍵に印がある）を見てから読んだので、盲検ではない。印と食い違う読み方を探す向きで読んだが、人手のラベルの代わりにはならない

### 5.2 項目とラベル

| 項目 | 対象 | ペルソナ（訪問） | 印（分類器の答え） | 自分のラベル |
| --- | --- | --- | --- | --- |
| 06 | ゲート discovery | precise\_pm（2。持ち帰った二つの問いに「来月の末に決める」「法務と相談してから決める」） | （無し → goal） | goal |
| 07 | ゲート discovery | terse\_engineer（2。「未定」「未定（後で決める）」） | goal | goal |
| 08 | ゲート discovery | vague\_founder（1） | goal | goal |
| 00 | ゲート architecture | — | goal | goal |
| 03 | ゲート assurance | vague\_founder | goal | goal |
| 21 | analyze | precise\_pm（2） | goal | goal |
| 22 | analyze | terse\_engineer（2） | goal | goal |
| 23 | analyze | vague\_founder（1） | goal | goal |
| 26 | analyze | vague\_founder（1） | needs\_unclear | needs\_unclear |
| 29 | analyze | vague\_founder（1） | unknown | unknown |
| 43 | plan\_tasks | — | goal | goal |
| 52 | unit\_test | — | goal | goal |
| 11 | acceptance | vague\_founder | goal | goal |
| 12 | acceptance | precise\_pm | requirement\_misread | requirement\_misread |
| 13 | acceptance | terse\_engineer | requirement\_misread | requirement\_misread |
| 14 | acceptance | vague\_founder | requirement\_misread | requirement\_misread |

κ 1.0（16 項目、一致 16）。往復 7 で見つかった三つの食い違いと E-M2 は、ペルソナを分けても、ゲートの項目でも、もう出ない。

### 5.3 字義どおりに読むと揺れる点（ラベルは緩い読みで付けた）

1. discovery のゲートの goal は「intake.md の回答（利用者、…）がすべて requirements.md の**要件か受け入れ基準に**反映」と書く。利用者は「## 利用者」の節にあり、REQ-n でも受け入れ基準でもない（項目 06〜08）
2. vague\_founder の「端数は切り捨て」は、割引額と支払額のどちらを切り捨てるかを言わない。REQ-1 は「割引額の 1 円未満は切り捨てる」と決める。precise\_pm と terse\_engineer は「割引額」と言う。これは markov の主経路の実装（ok、ok\_b が支払額を切り捨てる）の既知の欠陥と同じ点で、vague\_founder の時だけ REQ-1 の根拠が薄い（項目 08、23）
3. 訪問 2 の analyze の goal（項目 21、22）と discovery のゲート（06、07）では、intake.md に「未定」の二つの回答があり、requirements.md の「## 未決事項」は「（なし）」。記述（goal は要件の網羅を求めず、needs\_unclear は記憶 intake\_questions の列挙を証拠にする）の上では goal で、README の 3 が人間に確かめるよう挙げている点
4. acceptance の requirement\_misread（12〜14）の食い違いは推論による（第1.1節）
5. design\_incomplete には代表が無いので、この手順では記述を確かめられない（第1.2節）
6. assurance のゲート（03）の repo/ は REQ-1 に反するが、新しい goal の文（repo/ を改めて検証しない）で goal になる

1 と 2 は E2-L5 にした。3〜6 は人間のレビューに渡す（第9節）。

## 6. changelog.md の「未公開」

一回目の第6節は v0.1.0 から 32b4d68 までを照合し、足りないのは B-L3 だけとした。32b4d68 から 115149b までの公開 API と公開の文書の差分は次のとおりで、どれも載っているか、載せる必要が無い。

| 変更 | changelog に |
| --- | --- |
| `RunState` と `StageContext` の公開の範囲（B-L3） | ある（互換性に注意する変更） |
| adopting.md 第12節の N13 の項 | ある |
| adopting.md 第15.1節の改訂（ゲートの項目を含める、上流の違いで項目を分ける） | 「`unmarked` … 手引き第15.1節」の行。第15.1節は v0.1.0 に無く、未公開の期間に足された節なので、その中の改訂は節を足したことに含まれる。必要なら行に「ゲートの項目も含める」を書き足してもよい |
| api.md、adopting.md、`Prediction` の docstring の visits\_variance の言い方（B-L2） | `Prediction` の三つの量を足した行（`visits_variance` も v0.1.0 に無い）。意味は変わっていない |
| api-reference.md の `SCHEMA_FILES` の表示（B-L5） | api-reference.md 自体が未公開の期間に足された |
| `__all__` と signature | 変化なし（src の差分は markov.py の docstring だけ） |

判定: 漏れは無い。

## 7. 追加の実験（変異）

| 変異（f4c2/mut/ の上で一つずつ） | 結果 | 落としたテスト |
| --- | --- | --- |
| 確率的な本体が空の記憶を書かない（`if value:` の時だけ書く。一回目に生き残ったもの） | 落ちた | test\_bodies\_write\_memory\_out\_on\_every\_visit[markov]、[gated] |
| acceptance → analyze のシナリオを消す | 落ちた | test\_crossing\_rollbacks\_from\_every\_later\_phase、test\_committed\_scenarios\_match\_the\_generator |

## 8. 新しい指摘

### 本体の側

高と中は無い。

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| B2-L1 | 低 | docs/adopting.md 第15.1節の手順 3 | 「印を読む分類器はゲートにいつも goal を答える」とあるが、`MarkerClassifier` が goal を答えるのは goal が選択肢にある時だけで、ゲートの指標が落ちた項目では答え無しになる（api-reference.md の `MarkerClassifier`）。その項目で人のラベルが goal でなくても、記述と代表の食い違いではない | api-reference.md の `MarkerClassifier` の説明、ランタイムの選択肢の作り方 | 「goal が選択肢にあれば goal を答える」と書く。答え無しの項目は、食い違いではなく指標が落ちた評価として別に見る |

### 例の側

高と中は無い。

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| E2-L1 | 低 | tests/expectations/markov.yaml、markov\_shifted.yaml、software\_factory/design.py | 基準の根拠の注記に誤りが残る。release の訪問 1 [0.15, 0.31] の「両側 3.6 SE」は 3.21 SE（前の [0.14, 0.32] の時の値のまま）。mean\_visits の「visits\_variance 1.360、標準偏差 1.166」は 1.358、1.165。markov\_shifted.yaml の mean\_visits [1.95, 2.50] の「上へ 4.8 SE」は 4.74。design.py の docstring の visits\_variance は「一回の実行の中での訪問の回数の分散」のまま（B-L2 の言い方が入っていない）。基準の値はどれも正しい | 第2.2・2.4節 | 注記を直す。release の訪問 1 には「3.21 SE（規則の 3.2 SE をわずかに上回る）。誤って落ちる確率 0.135%」と書く |
| E2-L2 | 低 | README.md の「人間のレビューで確かめてほしいこと」1、tests/stochastic.yaml の plan\_tasks の注記 | 「design\_incomplete は、design の goal が運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」は言い過ぎ。記述の上では、implement の task\_unclear（タスクの paths の外のファイルを変えないと実装できない）から plan\_tasks に戻り、そのファイルが design.md の構成に無いと分かる経路で、design の goal を正しく満たした後でも起きうる。人間が end\_state を残すかを決める材料が不完全になる | workflow.yaml の implement の description と task\_unclear、plan\_tasks の description と goal。第1.2節 | README の 1 に、この経路（実装して初めて分かる構成の不足）を書き足す。確率的な本体に代表を置けない理由（markov の本体ではクラスの中で下流が分かれる）は、そのまま正しい |
| E2-L3 | 低 | tests/scenarios/ | plan\_tasks → design（design\_incomplete、carry design\_issues、max 2）の辺を通るのは、E2E のカバレッジの注入の一回だけで、そこで持ち帰る design\_issues は空の一覧。シナリオにも確率的な実行にも無いので、空でない design\_issues がこの辺で design の開始時スナップショットに届くことを確かめるテストが無い（往復 7 までは確率的な実行が確かめていた） | 第1.2節。tests/scenarios/ と software\_factory/ に design\_incomplete の参照が無い | 一回目の E-L2 と同じく、台本で plan\_tasks を design\_incomplete に分類し、空でない design\_issues を持って design に戻るシナリオを一本足す（expect.starts で design の訪問 2 の記憶を確かめる） |
| E2-L4 | 低 | tests/test\_independence.py、tests/test\_e2e.py（E-L6 の残り） | 全状態の確かめは Bonferroni になったが、implement に絞った二つの確かめ（入り方の検定の verdict が not\_detected、markov の implement=goal の訪問 1 → 1 が not\_detected）は補正の無い alpha 0.01 のまま。種の基点を変えた 200 ブロックずつで、正しい本体でもどれかが落ちたのは markov の集まりで 8/200（4%）、ゲートを揺らす集まりで 6/200（3%）。docstring は「補正の無い alpha 0.01 で全状態を見ると数 % で落ちる」と書くが、直した後にも同じくらい残ることは書いていない | 第2.6節 | 絞った確かめは「violated でない」ではなく「p 値が 0.001 以上」のようにする（仕込んだ所の検出は divergent で p = 0.0005 なので、この確かめを厳しくしても検出の確かめには響かない）か、`HTF_RUNS` や種を変えると数 % の確率で落ちうることを tests/README.md に書く |
| E2-L5 | 低 | workflow.yaml の discovery の goal、software\_factory/personas.py の vague\_founder、README.md の「フェーズゲートの落ち方」 | 第15.1節の試しで、緩く読めば合うが字義どおりには揺れる点が二つある。(1) discovery のゲートは回答を「要件か受け入れ基準に」反映することを求めるが、利用者は「## 利用者」の節にある。README の「人間のレビューで確かめてほしいこと」4 は「requirements.md に反映」と言い換えている。(2) vague\_founder の「端数は切り捨て」は何を切り捨てるかを言わず、REQ-1 の「割引額の 1 円未満は切り捨てる」の根拠が薄い。あわせて、README の「フェーズゲートの落ち方」の assurance の行は、goal に足した「repo/ を改めて検証しない」を反映していない | 第5.3節 | (1) 代表の側で直すなら、利用者を受け入れ基準のある要件にする。記述の側で直すなら（人間の承認が要る）、discovery の goal を「requirements.md に反映」にする。(2) vague\_founder の回答を「割り引く額の端数は切り捨て」にする。どちらも人のラベル付けで確かめる。README のゲートの一覧を workflow.yaml の文に合わせる |

## 9. 人間のレビューに渡すべき事項

一回目の第10節を更新したもの。

1. **記述と代表の整合を、人がやり直す（第15.1節）。** 往復 8 の試しのラベル（56 項目、κ 1.0）は、フィクスチャを作ったエージェント自身のもの。検証役の 16 項目の試し（κ 1.0、盲検ではない）でも食い違いは無かったが、字義どおりに読むと揺れる点がある（第5.3節。E2-L5 と、未定の回答と「未決事項（なし）」、推論による requirement\_misread、assurance のゲートの範囲）。ゲートの項目とペルソナごとの項目を含めて付け直す
2. **plan\_tasks の design\_incomplete を残すか、design の goal と範囲を揃えるか（README の 1）。** 確率的な本体には代表が無く、第15.1節では記述を確かめられないので、記述そのものを読んで決める。判断の材料に、implement の task\_unclear から plan\_tasks に戻って構成の不足が分かる正当な経路がある（E2-L2）ことを加える
3. **往復 8 で変えた記述の意味（第5.4節の分類体系の変更に当たる）。** unit\_test の goal に「テストへの依頼のすべてを確かめる」、assurance のゲートの goal に「判断は verification.md と review.json に基づき、repo/ を改めて検証しない」を足した（README の 6、7）。利用者は提案で止まらず定義を変えて人間のレビューに回した（往復 6 の M-2、M-8 の境界の変更と同じ扱い）。承認するかを決める。あわせて、第5.9節は各玩具の workflow.yaml と expectations を計画エージェントだけが書ける保護ファイルとするが、F4 では第7節の指示どおり利用者役が書いている。この関係も確かめる
4. **ペルソナの性格が変わった。** vague\_founder は「曖昧な創業者（値を決めていない）」から「くだけた創業者（値は決めている）」になり、三つのペルソナは言い方だけが違う。曖昧さは、種で選ぶ analyze の needs\_unclear と、どのペルソナも決めない二つの問い（キャンペーンの後、使える回数）でだけ入る。analyze の goal は要件の網羅を求めないので、二度目の訪問で「未定」の回答があっても goal になる（README の 3）。F4 の「ペルソナ 3 つ以上」は満たすが、この設計でよいかを確かめる
5. 分類体系の変更の提案（一回目の 2）: unit\_test のテストの不備を tests\_insufficient に含めた。別案（tests\_defective を足して unit\_test 自身に戻す）を採るか
6. 意図として書かれた選択（一回目の 3、変わらない）: implement の指標が落ちても impl\_violations が空なら unknown。discovery、architecture、construction、delivery のゲートの不合格は unknown。release は版を上げない。analyze の requirement\_count の min 3。acceptance の tests\_pass を残す。intake の「## 持ち帰った問い」は採らない
7. markov.yaml の実行のゲートはいつも goal で、ゲートの分布は markov\_gated.yaml の集まりだけで確かめる（一回目の 4、変わらない）
8. markov の主経路は REQ-1 に反するコードをリリースする（E-L1）。assurance の goal の文と README の 7 に意図が書かれた。玩具の意図としてよいか
9. 契約適合テストの読み方: 計画書第5.8節（このテストでのみ判定する）と、契約 第10節と手引き第9節（判定の対象はランタイムの実装）の食い違い（一回目の 6、変わらない）
10. 往復 6 と往復 8 の直しは、本体の実装を読んだ検証役の指摘を、計画の側が公開の文書の語で渡したもの（D-15、docs/review-findings.md の B〜E）に基づく。往復 8 で分かった一般の不足（N13）は手引き第12節に入ったので、次の利用者は手引きだけで知れる。「adopting.md だけで作れる」の判断では、この経緯を踏まえる
11. carry の有無をマルコフ合成のモデルに入れないこと（D2）は、F5 と決定 #6 で扱う（変わらない）

## 10. 実行したコマンドと出力の要旨

- `bash scripts/check.sh`（複製の上で、`HTF_RUNS` を外して）: ruff check、ruff format（97 ファイル）、mypy（src と tests で 42 ファイル、software-factory で 19、toy-minimal で 12）、pytest 638 件が通過（133.9 秒）、runtime の行カバレッジ 90% 以上、wheel にスキーマと契約適合テスト一式。全体で 2 分 16 秒。`pytest --collect-only examples/software-factory` は 177 件
- 整合性検査のコマンド（第3節）: 0 error(s)、0 warning(s)
- 自前の模型（後ろからの再帰、状態 101,003 個ずつ）と `synthesize` の比較。模型の標本 24,000 試行 × 400 回 × 2。二項分布の混合による厳密な誤判定の確率
- 実際のランタイムの掃引: markov とゲートを揺らす実行を 200 ブロックずつ（12 並列で 7 分 39 秒）。各ブロックで四つの expectations、独立性検証、entry\_dependence、`family_wise_violations`、本体の例外・警告・測定の失敗を記録
- divergent の 24 ブロックの独立性検証。既定の種での `compare_prediction`（設計値のモデル）
- E2E のカバレッジ計画の注入の項目の中身と、その項目だけの `run_coverage`
- オラクルのコーパス（123 項目）の書き出しと、別の環境での κ と ECE の計算
- 第15.1節の試し（351 項目のコーパス、56 群、16 項目のラベル、`oracle_report`）
- import の AST 解析と語の検索。v0.1.0 の adopting.md の節の確かめ。コミットごとの変更の範囲（B-L6）
- 変異 2 個（第7節。どちらも落ちた）

## 触ったファイル

- 書いた: reports/f4-completion-2.md（このファイル）だけ。元の作業ツリーでは、ほかのファイルを変えておらず、テストも実験も走らせていない（docs/progress.md の未コミットの変更は、この作業の前からあったもので、触れていない）
- 副作用: scratchpad に自分専用のディレクトリ f4c2/ を新しく作り、その中にリポジトリの複製を二つ（repo/、mut/）、実験のスクリプトと出力（model.py、sim.py、criteria.py、exact\_fail.py、sweep\_block.py、sweep/、label/ など）を置いた。実験の作業ディレクトリは f4c2/ の中に作り、使った後に消した。scratchpad に前からあったもの（repo/、f4c/、exp/、refenv/ など）は消しておらず、refenv/ は読むだけに使った
