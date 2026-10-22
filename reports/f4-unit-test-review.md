# F4 software-factory unit\_test の tests\_defective 事前レビュー（検証役）

- 検証日: 2026-10-22
- 対象: `git diff 08f79b4 077cc91 -- examples/software-factory`（往復 10。D-17 の 4、review-findings.md の F-1〜F-3、F-L1〜F-L3）
- 役割: 検証（第三者、計画書 第5.9節）。人間が足した記述をもう一度確かめる前の事前確認。実装の作業過程は見ておらず、差分と成果物と仕様だけから判定した
- 読んだもの
  - 対象: examples/software-factory/ の差分の全体、workflow.yaml、README.md、docs/（progress.md、adopting-gaps.md、review-findings.md の F）、software\_factory/（design.py、personas.py、scenarios.py、stages/probabilistic.py）、tests/fixtures/ の全変種、tests/stochastic.yaml、tests/expectations/ の四つ、tests/scenarios/ の新しい二本、test\_definition.py、test\_scenarios.py、test\_e2e.py、test\_independence.py、test\_personas.py の差分
  - 基準: contract/contract.md 第2・3節（とくに 2.4）、docs/adopting.md 第2.1〜2.4節、第12〜15.1節、docs/decisions.md の D-17 と D-18、docs/plan.md 第5.9節
  - 参照ランタイムのうち、状態文書と代表の鍵と並べ替え検定とシナリオの照合の実装（src/harness\_testing\_framework/testing/ の oracle、stages/runs.py、stages/independence.py、harness/scenario.py の verify）
- 実験はすべて scratchpad の複製の上で行った（末尾の「実行したコマンド」）。元の作業ツリーでは読むだけの git コマンドしか使っていない
- 書いたもの: このファイルだけ

## 総合判定: 人間に出してよい（中の二つを添えて）

高の指摘は無い。差分は D-17 の 4 と F-1 の指示どおりで、記述の変更は unit\_test と construction のゲートの goal の「不備」の一語に限られる。分布、設計値、expectations の基準の値は変わっておらず（注記だけ）、直した注記の数字はすべて独立に再現した。新しい代表と変えた代表は、届きうる上流の成果物のどの組み合わせでも、記述どおりに印のクラスになった（第15.1節の手順を自分でやり直した。食い違い無し）。複製の上で check.sh は 077cc91 と、レビュー中に入った 7547a75 の両方で通る。

中の指摘は二つで、どちらも、利用者役が F-1 の案に足した「テスト自身の誤り（準備、呼び出し、import）で失敗するテスト」と impl\_defect の境界にある。

1. **M-1（記述の文）**: impl\_defect を tests\_defective から分けているのは、括弧書きの「（テストではなく repo/src/ が誤っている）」だけで、本文の条件「その期待が要件に従っている」は、テスト自身の誤りで落ちるテストでも満たされる。impl\_defect が優先するので、字義どおりに読むとそちらに寄る。また、状態文書には pytest の出力が入らないので、失敗の原因がテストか repo/src/ かは、コードを読んだ推測と本体の自己申告でしか分からない
2. **M-2（代表）**: この句に当たる代表が、フィクスチャにも、シナリオにも、E2E の誘発にも、第15.1節の試しにも無い。人間に判断を求めている境界を、どのテストも踏んでいない

どちらも人間に出すのを止める理由にはしない。M-1 の直し方は、人間がこの句を残すか外すか（README の境界の 2 が「要らなければ外しても他の境界は変わらない」と問うている）で決まるので、直してから出すより、書き換え案を添えて人間に選んでもらう方がよい。M-2 は記述を変えないので、人間に出す前に足しても、人間が句を残すと決めた後に足してもよい。低の指摘は並行して直せる。

あわせて、人間が tests\_defective を承認する前に、D-18 の N14（この分割が計画書 第2節の固定された判断「クラスの粒度は独立性検証の結果でのみ変える」と矛盾する）を決める必要がある。D-17 の 4 で人間が提案を採った時、この矛盾は示されていなかった（D-18 の記録）。(b) を選べば、この変更はすべて取り消しになる。

## 前提と方法

### 分類器が見るもの（unit\_test と construction のゲート）

契約 2.4 により、状態文書は reads と writes のファイルの内容と、memory\_out の値でできる。memory\_in と指標の値は入らない。指標が落ちたことは、選択肢から goal が外れることでしか分からない。

| 対象 | ファイル | 記憶 |
| --- | --- | --- |
| unit\_test | requirements.md、tasks.yaml、repo/（src と tests）、impl\_notes.md、test\_report.md | failing\_tests、coverage\_gaps、test\_defects |
| construction のゲート | 上に design.md を足したもの（implement の reads） | unit\_test の memory\_out |

design.md は unit\_test の reads に無い。pytest、coverage、ruff の出力も状態文書に無い。実際の状態文書の長さは最大 5882 文字（assurance のゲート。unit\_test は 4951）で、既定の上限 20000 に届かず、切り詰めは起きない。

### 確かめ方

- 記述の MECE: 失敗したテストと通るテストのそれぞれを、期待が要件に従う、要件に反する、要件が決めていない、の三つと、失敗の原因（repo/src/ かテスト自身か）で場合分けし、各場合がどのクラスに当たるかを記述の文から読んだ
- 代表と上流の組み合わせ: implement の goal の三つの変種（ok、ok\_b、ok\_fixed）と unit\_test の六つのフィクスチャの 18 通りを一時ディレクトリに組み、実在の pytest と ruff をかけた
- 第15.1節: 全変種を踏む試しの分布（markov に、implement の ok\_fixed と unit\_test の defective を足したもの。複製の中だけ）で 300 回（種 91000）走らせ、`build_corpus(..., unique_states=True)` の 320 項目（ステージ 243、ゲート 77）を、(scope, 対象, 印, 上流の違い) で 107 の組に分けた。変えた所の組について、`unmarked` で印を除いた状態文書と選択肢の記述だけを読んでラベルを付けた
- 基準: 設計値のモデルを、フレームワークを使わない独立な厳密計算（吸収マルコフ連鎖を、辺の回数と訪問の回数を状態に持たせてたどる）で解き、フレームワークの `synthesize` とも突き合わせた
- 観測値が前と同じか: 08f79b4 と 077cc91 のそれぞれで、markov（種 20000）、divergent（種 30000）、ゲートを揺らす実行（種 50000）を 400 回ずつ走らせ、全評価の結果と最後の状態と p 値を比べた

## 確かめた結果（指摘でないもの）

### 1. unit\_test のクラス集合

| 確かめたこと | 結果 |
| --- | --- |
| 各 end\_state に戻り先がある | 合う。tests\_defective → unit\_test（carry test\_defects と coverage\_gaps、max 2） |
| carry する記憶が memory\_out と memory\_in の両方にある | 合う。memory\_in [coverage\_gaps, test\_defects]、memory\_out [failing\_tests, coverage\_gaps, test\_defects] |
| 記述が carry する記憶を証拠として名指す | 合う（「記憶 test\_defects」「記憶 coverage\_gaps」。test\_definition.py も確かめる） |
| description が訪問のたびに書くと述べる | 合う。「どれも無ければ空の一覧を書く（訪問のたびに必ず書く）」。偽の本体もすべての変種で三つとも書く |
| 二つに当たりうる所の優先 | impl\_defect > tests\_defective > tests\_insufficient と書いてある。goal とは「「## 失敗」「## 不備」「## 未網羅」が空」で分かれる |
| 観測できるか | 各クラスの証拠は記憶と test\_report.md の節の列挙で、状態文書に入る。「要件に反する期待」は requirements.md とテストを読めば分かる。lint、カバレッジ、変更の範囲、「失敗する」は状態文書から直接は分からないが、列挙を条件にしているので判断できる（変更の範囲は記述自身がそう断っている）。例外は M-1 |
| 以前の穴が塞がったか | 塞がった。前の tests\_insufficient は「## テストへの依頼」の未対応を挙げておらず、goal（往復 8 で足した）に当たらないのに end\_state も無かった。今は tests\_insufficient に入る |

### 2. construction のゲートの「不備」

妥当。前は不備も「## 未網羅」に書いていたので、ゲートの「未網羅が無い」が不備も含んでいた。節を分けたので、一語を足さないとゲートの意味が狭まる。差分で、workflow.yaml の unit\_test の外の変更はこの一語だけだった。tests\_defective は goal の時に空になる test\_defects を証拠にするので、ゲートからは選ばれず、ゲートの不合格は unknown になる（手引き 2.4 の注意と README の「フェーズゲートの落ち方」に合う）。

### 3. 代表と上流の組み合わせ（実在のツール）

| implement \ unit\_test | ok | thin | defect\_found | defect\_passed | defective | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| ok | 11 passed | 4 passed | 1 failed | 1 failed | 1 failed | 11 passed |
| ok\_b | 11 passed | 4 passed | 1 failed | 1 failed | 1 failed | 11 passed |
| ok\_fixed | 11 passed | 4 passed | 12 passed | 12 passed | 1 failed | 11 passed |

lint はどの組でも違反無し。defective は三つの実装のどれと組んでも、要件に反する期待のテスト（小計 300 円に OFF500 で -200 円）だけが落ちる（README の「どちらの実装の系統でも落ちる」のとおり）。defect\_found と defect\_passed は同じテストで、偽の本体が系統で振り分けるので、確率的な実行では ok と ok\_b の後は defect\_found、ok\_fixed の後は defect\_passed になる。unit\_test は intake.md を読まないので、ペルソナの違いは unit\_test の状態文書に出ない。requirements.md は analyze の goal の代表一つだけが届く。

### 4. 第15.1節の手順（自分でやり直した）

選んだ組と、自分のラベル（印を見ずに付けた後、印と比べた）:

| 対象 | 組（上流の違い） | ラベルと印 |
| --- | --- | --- |
| unit\_test | goal（ok、ok\_b、ok\_fixed。ok\_fixed の組には defect\_passed の状態文書も含む）、impl\_defect（ok、ok\_b）、tests\_defective（三つ）、tests\_insufficient（三つ）、unknown（三つ） | すべて印と一致 |
| construction のゲート | ok、ok\_b、ok\_fixed（ok\_fixed は defect\_passed の後も） | すべて goal で一致 |
| analyze | goal と needs\_unclear と unknown をペルソナで分けて 9 | すべて一致 |
| discovery のゲート | ペルソナで分けて 3 | すべて goal で一致。利用者と入力の場所は REQ-3 の文にあり、「要件か受け入れ基準に反映」を満たす |
| design | goal、requirements\_gap | 一致。REQ-3 の新しい文でも、コードを Cart のどの操作で受け取るかは決まっていない |
| acceptance | requirement\_misread（ペルソナと実装の 7 組）、goal | 一致（参照が REQ-3 に変わっただけ） |
| plan\_tasks の design\_incomplete（シナリオの代表。コーパスには出ない） | design/gap と組む | design\_incomplete で一致。design/gap の「## 構成」に cart.py と REQ-3、REQ-4 の受け持ちが無く、tasks.yaml は REQ-1、REQ-2 しか扱わない |

食い違いは無かった。印を除いた状態文書を直接開いて読んだのは、unit\_test の 15 組（一組は全文、ほかはテストの関数、test\_report.md、記憶の部分）、construction のゲートの一組、analyze の goal と discovery のゲートの各一組。残りの組は、状態文書を組み立てる元のフィクスチャとペルソナの回答（どちらも全文を読んだ）から組み合わせて読んだ。ただし、これもエージェントの試しのラベルで、人手のラベルではない。私はラベルを付ける前にフィクスチャを全部読んでいるので、先入観がある。

### 5. 新しいシナリオ二本と E2E

- plan\_tasks\_design\_incomplete\_rollback: 空でない design\_issues が design の訪問 2 の開始時スナップショットに届くことを、expect.starts（記憶の完全一致）で確かめている
- unit\_test\_defective\_self\_rollback: 空でない test\_defects が unit\_test の訪問 2 に届くことを確かめている。coverage\_gaps は空の一覧で運ばれる（低 L-2）
- 照合は記憶の完全一致なので、carry に coverage\_gaps が無ければ鍵が無くて落ちる。辺の carry の設定そのものは確かめられている
- 新しいシナリオは inputs の repo/ をファイルごとに展開して書いているので、N15（7547a75。重なる鍵はより具体的な鍵が勝つ）の前後どちらでも同じに動く
- E2E のカバレッジ: 目標は 31。(unit\_test, tests\_defective) は注入ではなく誘発で踏まれ、`reached` は真、`missing` は空（複製で計画を作って確かめた）

### 6. 基準（軽く）

差分で、expectations の min と max と stochastic.yaml の profiles は一字も変わっていない（変わったのは注記と、variants に足した defective と、各変種の記憶に足した `test_defects: []`）。defective はどの分布にも無く、変種の選び方は profiles の名前だけで決まるので、種と変種の対応は変わらない。実際に、08f79b4 と 077cc91 で同じ種の三つの実行の集まり（各 400 回）を走らせると、全評価の結果、最後の状態、独立性と入り方の検定の p 値まで、出力がバイト単位で同じだった。

直した注記の数字（独立な厳密計算。`synthesize` とも小数点以下 6 桁まで一致）:

| 注記 | 書いてある値 | 計算した値 |
| --- | --- | --- |
| markov.yaml release の訪問 1 [0.15, 0.31] | 3.21 SE、誤って落ちる確率 約 0.13% | E[n] 285.34、SE 0.02491、両側 3.211 SE、正規近似で 0.132% |
| markov.yaml mean\_visits | visits\_variance 1.358、標準偏差 1.165 | 1.35829、1.16546、SE 0.05827、下側 3.32、上側 3.20 |
| markov\_shifted.yaml mean\_visits [1.95, 2.50] | 上へ 4.7 SE | 4.745 |
| markov\_gated.yaml ゲートの訪問 1 | 両側 3.5 SE | 3.451 |
| markov\_gated.yaml status\_rate | 下側 3.2、上側 3.6 | 3.233、3.553 |
| markov\_gated\_shifted.yaml [0.35, 0.50] | 上へ 5.8 SE | 5.751 |

ほかの注記（markov.yaml の残りの 10 基準、markov\_shifted.yaml の 14 基準、markov\_gated の残り）も、丸めの範囲ですべて合う。release の訪問 2 以降の二項分布の裾（n = 66、p = 0.97）も 0.36%（0.90）と 0.08%（0.88）で注記どおり。

独立性の絞った確かめ（「判定でき、p 値が 0.001 以上」）は、仕込んだ所の検出を弱めていない。

- 仕込んだ所の検出（divergent の stage:implement=goal、訪問 1 → 1）は `verdict == "violated"`（p < 0.01）のまま変わっていない。観測した p は 0.0004998 = 1/2001（並べ替え 2000 回の下限）
- 緩めたのは、仕込んでいない側（markov の同じ状態、intake のペルソナの代表、入り方の検定の implement）の確かめだけ。p = (1 + 超えた回数) / 2001 なので、「0.001 以上」は超えた回数が 2 以上のこと。正しい本体で落ちる確率は 2/2001 ≈ 0.1%（tests/README.md のとおり）
- 仕込んだ違いと同じ大きさの違いが markov に紛れ込めば、p は 0.0005 程度になり、この確かめでも落ちる。見逃すのは p が 0.001〜0.01 の弱い違いだけで、それはもともと検出の確かめの対象ではない
- 観測した p: markov 0.229、intake のペルソナ 0.439（divergent で 0.778）、入り方の implement 0.560（ゲートを揺らす実行で 0.429）。progress.md の往復 10 の値と合う（前の版の progress.md の markov の「p = 0.24」は、08f79b4 でも同じ種で 0.229 なので、今の実行の値ではなかった。往復 10 で 0.23 に直っている）

## 指摘

### 例の側

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| M-1 | 中 | workflow.yaml の unit\_test の impl\_defect の記述（と unit\_test の description） | テスト自身の誤りで落ちるテストのうち、期待が要件に従うものが、字義どおりには impl\_defect にも当たる。impl\_defect の本文の条件は「テストの一部が失敗し、その期待が要件に従っている」で、テストか repo/src/ かを分けるのは括弧書きの説明「（テストではなく repo/src/ が誤っている）」だけ。前はこの括弧は本文の言い換えだったが、F-1 の案に足した句で、期待が要件に従っていてもテストが誤っている失敗がありうることになり、括弧が唯一の判別の条件になった。impl\_defect は tests\_defective に優先する。本体が正しく自己申告すれば（test\_defects と「## 不備」にだけ書けば）、impl\_defect の証拠（failing\_tests と「## 失敗」）が欠けるので分かれるが、本体が「## 失敗」に書いた時（両方に書いた時も）は、記述の読み方で行き先が変わる。また状態文書には pytest の出力が無く、test\_report.md の節にも、失敗で何が観測されたか（期待と実際の値か、テストのどこで何の例外か）を書く決まりが無い。分類器は、コードを読んで実行を頭の中でたどるか、本体の申告を信じるしかない。呼び出しの誤りについては、インターフェースを決める design.md が unit\_test の reads に無い（implement が goal なら repo/src/ は design どおりという前提に立つ） | 例: `cart.add("item", 1000, 0)` で準備を誤り、ValueError で落ちる `assert _cart(1000).total("PCT10") == 900`。期待は REQ-1 の受け入れ基準どおりで、落ちる原因はテスト。README の境界の 2 は、この括弧を条件として読む前提で書かれている | 人間がこの句を残すなら、括弧を条件に上げる。たとえば「repo/tests/ のテストの一部が、テストの準備、呼び出し、import の誤りではなく repo/src/ の振る舞いのために失敗し、その期待が requirements.md の受け入れ基準か要件の記述に従っている」。あわせて unit\_test の description に「「## 失敗」と「## 不備」の各項目に、観測した結果（期待した値と実際の値、またはテストのどこで何の例外が出たか）を書く」を足し、境界を状態文書から確かめられるようにする。句を外すなら、テスト自身の誤りで落ちるテストは impl\_defect（implement に戻り、「## テストへの依頼」を経て書き直される）か unknown になることを README に書く。どちらも記述の改訂なので、人間に案を示して選んでもらう |
| M-2 | 中 | tests/fixtures/unit\_test/、tests/scenarios/、tests/test\_e2e.py | 案に足した句（テスト自身の誤りで失敗するテスト）に当たる代表がどこにも無い。defective の不備は「要件に反する期待」で、lint、変更の範囲、テスト自身の誤りの句は踏まれない。lint と範囲は前の tests\_insufficient にもあった不備だが、この句は新しく、impl\_defect との新しい境界を作る。第15.1節の試し（往復 10 の 32 項目と、この検証）も、この境界を一度も読んでいない | フィクスチャの一覧、stochastic.yaml の variants、test\_e2e.py の INDUCED、二本のシナリオ | 句を残すなら、テスト自身の誤りで落ちる代表（期待は要件どおりで、準備か import を誤るテスト。test\_report.md の「## 不備」と test\_defects に書く）を一つ置き、E2E の誘発かシナリオで写し、第15.1節の試しに入れる。実在の pytest で三つの実装のどれと組んでも落ちることを確かめる。人間が判断する時の具体例にもなる |
| L-1 | 低 | tests\_defective の記述の「同時に不足もあれば、それも記憶 coverage\_gaps と「## 未網羅」に列挙されている」 | これは条件として読める。不備が列挙されていても、不足が列挙から漏れていれば tests\_defective に当たらず、tests\_insufficient（不備が無いこと）にも当たらず、unknown になる。分類器は、テストの無い受け入れ基準を自分で読めるので、漏れを見つけうる | 記述の文 | 漏れを unknown にするのが意図なら、そのままでよい（README に一言）。意図でなければ、この文を unit\_test の description（本体への指示）に移すか、「（不足もあれば、それも列挙する）」のように条件でない形にする |
| L-2 | 低 | tests/scenarios/unit\_test\_defective\_self\_rollback.yaml（software\_factory/scenarios.py の 16） | carry する coverage\_gaps が空の一覧で、README の境界の 5（不備で戻る時は同時にある不足も持ち帰る）を、空でない値で踏むシナリオも、不備と不足が同時にある代表も無い。シナリオの description は「持ち帰った不備と不足（test\_defects と coverage\_gaps）を受けて書き直す」と言う。照合は記憶の完全一致なので、辺の carry の設定は確かめられているが、人間が判断を求められている点の具体例が無い | 照合した記憶の値（test\_defects は空でない、coverage\_gaps は []） | 不備と不足を両方持つ代表（defective に、テストの無い「## テストへの依頼」か受け入れ基準を一つ足した変種）を置き、空でない coverage\_gaps も運ぶシナリオにする。test\_definition.py の FILLED は、その変種を tests\_defective の節の組として受け入れるように直す。または description を「持ち帰った不備（と、空の不足）」に直す |
| L-3 | 低 | tests/test\_scenarios.py の test\_every\_rollback\_edge\_is\_taken の docstring | 「持ち帰る記憶が戻り先の開始時スナップショットに届くことは、各シナリオの expect.starts が確かめる」は言い過ぎ。13 本の辺のうち、unit\_test → unit\_test（tests\_insufficient、construction\_rollbacks）、review → implement（changes\_requested、assurance\_gate\_rolls\_back）、release → release（notes\_incomplete、release\_notes\_self\_rollback）は、戻り先の訪問の expect.starts が無い。三本とも往復 10 より前からのシナリオ | 各シナリオの trace の rollback の行と expect.starts の突き合わせ（下の「実行したコマンド」） | docstring を「10 本は expect.starts が確かめる」のように事実に合わせるか、三本のシナリオに戻り先の訪問の expect.starts を足す |
| L-4 | 低 | tests/test\_e2e.py の test\_coverage\_plan\_reaches\_every\_stage\_class | (unit\_test, tests\_defective) を誘発で踏むことを確かめていない。確かめているのは方法の集合が {induce, inject} であることと、全目標を踏むことだけで、INDUCED から tests\_defective の行が消えても注入で踏まれて通る。今は誘発で踏まれている（確かめた） | 計画を作って各目標の方法を表示した | INDUCED のすべての目標が induce であることを確かめる一行を足す |
| L-5 | 低 | README の「記述と代表の整合」の往復 10 | 往復 10 の第15.1節の試しの 32 項目に、往復 10 で新しく置いた代表 plan\_tasks/incomplete（シナリオだけが写す）が入っていない。この検証で読んだ限りでは、design/gap と組んで design\_incomplete になり、食い違いは無い | README の内訳（unit\_test 14、analyze 6、acceptance 3、design 2、ゲート 7） | README に、plan\_tasks/incomplete は design/gap と組む状態文書を記述だけで読んで確かめた、と書き足す（試しのコーパスには出ない） |
| L-6 | 低 | tests/expectations/markov.yaml の mean\_visits の注記、markov\_gated.yaml の注記の「implement の訪問の回数 1.674」 | 厳密な値は 1.67349 で、小数点以下 3 桁に丸めると 1.673。SE の倍数（下側 3.3、上側 3.2）は正しい。この差分で直した数字ではない | 独立な厳密計算と synthesize | 1.673 にする（任意） |

### フレームワーク本体の側

| 番号 | 重大度 | 場所 | 問題 | 根拠 | 直し方の案 |
| --- | --- | --- | --- | --- | --- |
| FW-1 | 中（既に人間待ち） | docs/plan.md 第2節、docs/adopting.md 第13節（D-18 の N14） | tests\_defective の分割は独立性検証の結果からではなく、計画書 第2節の固定された判断の帰結「クラスの粒度は独立性検証の結果でのみ変える」と矛盾する。D-18 が人間待ちとして記録している。新しい指摘ではないが、人間が tests\_defective の記述を承認するかどうかは、この決定に先に依存する | D-18、adopting-gaps.md の N14 | D-18 の (a) か (b) を人間が先に決める。(a) なら、手引きに分類体系を変える理由の範囲と、変えた後に確かめることの一覧（D-18 の文案）を入れる |
| FW-2 | 低 | docs/adopting.md 第15.1節 | 手順 1 は「全変種を踏む実行の集まりから」コーパスを作るとするが、確率的な分布に置かない代表（確率 0 の変種、シナリオか E2E だけが写す代表）を、どうコーパスに入れてラベルを付けるかが無い。第12節は、上流と両立しないクラスは「シナリオか E2E の注入で踏む」と言い、この例でも defective と plan\_tasks/incomplete がそれに当たる。利用者役もこの検証も、試しの分布を複製の中に作って入れた。シナリオだけの代表は試しのコーパスに出ず、往復 10 の試しから漏れた（L-5） | 往復 10 の試しの記録、この検証の手順 | 第15.1節に、分布に無い代表の扱いを書く。たとえば「全変種を踏む試しの分布を一時的に作る」「シナリオだけの代表は、そのシナリオの実行記録と置き場から状態文書を作るか、状態文書を読んで確かめる」 |
| FW-3 | 低 | docs/adopting.md 第2.1節 | 「分類器が見るのは reads と writes の内容と memory\_out の値だけ」とあるが、指標やツールの出力（pytest の失敗の内容など）が状態文書に入らないことと、クラスの境界がツールの結果の原因（テストの誤りか本体の誤りか）で分かれる時に、本体に観測を成果物へ書かせる必要があることは書いていない。契約 2.4 から導けるが、M-1 はちょうどこの形 | 契約 2.4、M-1 | 第2.1節の「観測できる条件として書く」に一文足す。「指標の値とツールの出力は状態文書に入らない（指標が落ちたことは選択肢から goal が外れることでしか分からない）。クラスの境界がツールの結果の中身で分かれるなら、その中身を本体に成果物か記憶へ書かせる」 |

## 人間が確かめるべき点

### 先に決めること

1. **D-18 の N14**: tests\_defective の分割を、計画書 第2節の固定された判断と矛盾したまま採るか（(a) 第2節の帰結を改める / (b) 分割を取り消す）。D-17 の 4 で提案を採った時、この矛盾は示されていなかった

### 記述の文そのもの（workflow.yaml。README の「確かめてほしいこと」に全文がある）

2. **tests\_defective**: 「repo/tests/ に、unit\_test 自身が直すべき不備（テストが誤っている）がある: requirements.md の要件の記述か受け入れ基準に反する期待を持つテスト（通るか失敗するかによらない）、テスト自身の誤り（準備、呼び出し、import）で失敗するテスト、repo/tests/ の lint の違反、tasks.yaml のタスクの tests に無いファイルの変更。その不備が、記憶 test\_defects と test\_report.md の「## 不備」の両方に列挙されている（…）。同時に不足もあれば、それも記憶 coverage\_gaps と「## 未網羅」に列挙されている（一度に持ち帰って直す）。tests\_insufficient に優先する。」
3. **tests\_insufficient**: 「unit\_test 自身が直すべき不足（テストが足りない）があり、不備は無い: 受け入れ基準のうちテストの無いもの、「## テストへの依頼」のうちテストの無いもの、repo/src/ の実行されない箇所（行カバレッジが 80% に届かない）。その不足が、記憶 coverage\_gaps と「## 未網羅」に列挙されている。」
4. **impl\_defect**: 文は優先の一句（「tests\_defective と tests\_insufficient に優先する」）しか変わっていない。M-1 の書き換え案と合わせて見る
5. **unit\_test の description と goal**: test\_report.md を「## テスト」「## 失敗」「## 不備」「## 未網羅」の四節にした。自己点検に「各テストの期待と requirements.md の要件との一致」を足した
6. **construction のゲートの goal**: 「未解決の違反、問い、失敗、不備、未網羅が無い」（「不備」の一語。この検証は妥当と見た）

### 境界の選択

7. **テスト自身の誤りで失敗するテストを不備に入れるか**（利用者役が案に足した句）。残すなら M-1 の書き換えと M-2 の代表が要る。外すなら、そういう失敗は impl\_defect か unknown になる
8. **要件が決めていない期待で落ちるテストの行き先**: 期待が要件に「従う」でも「反する」でもない時（例: 同じコードを二度使うと二度目は ValueError になると期待するテスト。requirements.md は使える回数を決めておらず、analyze の needs\_unclear が尋ね返す未決の点でもある）、テスト自身の誤りでもなければ、どのクラスにも当たらず unknown になる。unit\_test には analyze へ戻る辺が無いので、unknown で人に戻すのは筋が通るが、記述はこの場合に触れていない
9. **「## 失敗」の意味**: 「## 失敗」は「repo/src/ の欠陥を示した失敗」の節で、pytest で落ちたテストの一覧ではない。defective の代表では pytest は 1 件落ちるが「## 失敗」は（なし）で、落ちたテストは「## 不備」にある。節の名前の素直な読みとずれるので、分類器や人が名前だけで読むと迷いうる。名前をこのままにするか（「## 本体の欠陥」のような名前にするか）
10. **通るのに要件に反する期待のテスト**: 不備に入る（goal ではない）とした。ただし goal の文が除くのは「「## 不備」が空でない」ことだけで、本体がそのテストを見落として列挙しなければ、goal の文は満たされる。この見落としは acceptance が拾う前提でよいか
11. **優先**（impl\_defect > tests\_defective > tests\_insufficient）と、不備で戻る時に不足も持ち帰ること（carry test\_defects と coverage\_gaps）。不足の漏れを unknown にするか（L-1）
12. **max 2**: 辺が二本になり、unit\_test が自分自身に戻れる回数の合計は 2 から 4 になる。試しの実行では unit\_test の訪問が 7 回に達する実行があった
13. **確率的な実行に tests\_defective を出さない**: 分布テストと独立性検証は、このクラスを見ていない。出すかどうかは README の提案のとおり、人間の判断を待つ
14. **第15.1節の人手のラベル**（D-17 の 6）はまだ。tests\_defective で項目が増える。M-2 の代表を足すなら、その項目も含める

## 実行したコマンドと出力の要旨

複製の場所: 検証役の scratchpad の `f4u/`（以下 `$S`）。

| コマンド | 要旨 |
| --- | --- |
| `git clone <元のリポジトリ> $S/repo`（077cc91） | 複製 |
| `bash scripts/check.sh`（`$S/repo`、077cc91） | 通った。ruff check、ruff format（97 ファイル）、mypy strict（42、19、12 ファイル）、pytest 649 passed（137.3 秒）、ランタイムの行カバレッジ 90% 以上、wheel にスキーマ同梱。全体 2 分 19 秒。ログは `$S/check_077cc91.log` |
| `git clone <元のリポジトリ> $S/repo_wt`（レビュー中に入った 7547a75。N15 の本体の変更） | 複製 |
| `bash scripts/check.sh`（`$S/repo_wt`、7547a75） | 通った。pytest 651 passed（137.5 秒）、ほかは同じ。ログは `$S/check_7547a75.log` |
| `python3 -I $S/scripts/markov_dp.py`、同 `gated` | 設計値のモデルの独立な厳密計算。完了 0.694154、implement の訪問の平均 1.673485、分散 1.358292。ゲートを揺らすモデルで完了 0.666231、1.887174、1.818179。各基準の E[n]、SE、倍数は上の表 |
| `synthesize(design_model(...))`（`$S/repo` の venv） | 上の厳密計算と一致 |
| `git worktree add $S/old 08f79b4`（複製の中）と `$S/scripts/obs.py` を両方の版で実行 | markov、divergent、ゲートを揺らす実行の各 400 回の全評価、最後の状態、検定の p 値が、二つの版でバイト単位で同じ（`$S/obs_old.json`、`$S/obs_new.json`） |
| `$S/scripts/corpus.py $S/corpus 300 91000` | 試しの分布 allv（複製の中だけ）で 300 回。320 項目を 107 の組に分け、印を除いた状態文書を `$S/corpus/groups.json` に書いた。11 秒 |
| `$S/combo/` に implement と unit\_test のフィクスチャを組んで pytest と `ruff check --isolated --select E,F,W` | 上の 18 通りの表 |
| 複製で `plan_coverage` と `run_coverage` | 目標 31、(unit\_test, tests\_defective) は induce、missing は空 |
| シナリオの trace の rollback の行と expect.starts の突き合わせ（複製で） | 13 本の辺のうち 10 本に戻り先の expect.starts がある（L-3）。tests\_defective の辺は test\_defects が空でなく coverage\_gaps が []（L-2） |
| 元の作業ツリーでは `git log`、`git diff`、`git status`、`git show` だけ | 読むだけ |

## 触ったファイル

- 元のリポジトリ: reports/f4-unit-test-review.md（このファイル）を新しく書いただけ。ほかは変えていない。コミットしていない
- scratchpad（`$S`）: 複製 `repo/`（077cc91。中に `old/` の worktree を足した）、複製 `repo_wt/`（7547a75）、`scripts/markov_dp.py`、`scripts/corpus.py`、`scripts/obs.py`、`corpus/`、`combo/`、`obs_old.json`、`obs_new.json`、`prof_old.txt`、`check_077cc91.log`、`check_7547a75.log`
