# software-factory の作業ログ

harness-testing-framework（v0.1.0）の利用者として、adopting.md だけを手引きに、ソフトウェア開発のワークフロー型ハーネスを作る。

- 読取の制限: docs/adopting.md、docs/api.md、docs/api-reference.md、examples/toy-minimal/、公開 API の文書（api.md が挙げるもの）だけ。本体の実装（src/、tests/、scripts/、pyproject.toml、conftest.py の中身）、docs/plan.md、docs/progress.md、docs/decisions.md、reports/ は読まない。本体は直さない
- 分からなかったこと、足りなかったこと、回避したくなったことは docs/adopting-gaps.md に書く
- コミットはしていない（依頼に無いため）

## 状態（2026-10-22）

往復 13（N17 を受けて改められた手引き第15.1節の三つの目安の確かめと、人に渡す材料の選び方の見直し）まで完了。`scripts/check.sh` が通る（ruff check、ruff format、mypy strict、pytest 662 件で 144.6 秒、全体で約 2 分 25 秒）。この例のテストは 199 件。変更は examples/software-factory/ の中だけ。adopting-gaps.md の未解消は無い（往復 13 で新しい不足は無かった）。N17 は往復 13 で解消した。

最初の版（下の「経過」）の後、フレームワークの側が adopting-gaps.md の 30 項目を受けて直したので、往復 1 で各項目を確かめ、要らなくなった回避策を外した（下の「往復 1」）。往復 1 で見つけた N1〜N7 も直ったので往復 2 で、往復 2 で見つけた N8、N9 も直ったので往復 3 で、往復 3 で見つけた N10 も直ったので往復 4 で、往復 4 で見つけた N11 も直ったので往復 5 で確かめた（下の「往復 2」〜「往復 5」）。往復 6 で、人間のレビューの前の検証役の指摘（docs/review-findings.md）に対応した（下の「往復 6」）。往復 8 で完了判定の指摘（E）に、往復 10 で人間のレビューの回答と完了判定の二回目の指摘（F）に、往復 11 で往復 10 の後の人間の決定（G。tests\_defective の分割の取り消しと、人が付けるラベルの材料）に対応した。往復 12 で、往復 11 で見つけた N16 を受けた手引きの書き足しを確かめ、人に渡す材料の選び方をそれに合わせた（下の「往復 12」）。往復 13 で、往復 12 で見つけた N17 を受けて改められた手引きの目安を確かめ、人に渡す材料の選び方をそれに合わせた（下の「往復 13」）。今の未解消は adopting-gaps.md の先頭にある（往復 13 の後は無い）。

| 求められたこと | どこで満たしたか |
| --- | --- |
| 4 フェーズ以上、8 ステージ以上 | workflow.yaml（5 フェーズ、9 ステージ）。tests/test\_definition.py |
| フェーズ境界越えのロールバック、carry、ユーザー回答待ち | 越境の辺 6 本（design → analyze、implement → plan\_tasks、acceptance → analyze と implement、review → design と implement）。全辺に carry。intake が awaits\_user |
| end\_state は観測できる条件、戻り先つき、unknown を含む | 全ステージに unknown、unknown 以外の 12 クラスにそれぞれ戻り先（往復 10 で足した unit\_test の tests\_defective は、往復 11 で人間の決定により取り消した）。carry する記憶を記述が証拠として名指す（テストで確かめる） |
| 偽のステージ本体（LLM なし） | 決定論的: シナリオの台本でフィクスチャを写す。確率的: tests/stochastic.yaml の設計値で、種だけから変種を選ぶ |
| carry を受けた再進入で分布が変わるもの | release（missing\_notes を受けると goal 0.75 → 0.97）。訪問 2 以降と carry の有無が一致することを全実行で確かめる |
| クラス内で下流の分布が分かれるもの | divergent の implement の goal（ok は REQ-1 の切り捨てを誤り、ok\_fixed は正しい）。unit\_test の defect のテストは実在の pytest で前者だけ落ちる |
| 実装と単体テストに本物の指標 | build\_passes、tests\_pass、line\_coverage、lint\_errors、out\_of\_scope\_changes。フィクスチャの repo/ に compileall、pytest、coverage、ruff を実際にかける |
| 要求の取り込みにペルソナ 3 つ以上 | software\_factory/personas.py（precise\_pm、vague\_founder、terse\_engineer）。確率的な実行では種からペルソナを選ぶ。決定論テストと E2E のカバレッジにも束縛する |
| 全ランナー | 下の「結果」 |

## 結果

- 整合性検査: 誤り 0、警告 0
- 契約適合テスト: パッケージに同梱した 25 シナリオ（`conformance_scenarios()`）すべてが参照ランタイムで期待どおり（tests/test\_conformance.py。参照ランタイムを使うので必須ではなく、版の確認として残す）。ハーネスの本体は、400 回の実行で契約違反、本体の例外、範囲外のファイルの警告が一度も無い
- 遷移の決定論テスト: 17 シナリオ。遷移の六種、escalate の四択、越境の 7 通り（定義の上の六本の辺のすべてと、運用者による越境）、定義の上のロールバックの辺 12 本のすべて（自分自身への辺と plan\_tasks → design を含む）を通し、どの辺でも、戻った直後の訪問の開始時スナップショットに carry する記憶が空でない値で届くことを expect.starts で確かめる（往復 11）。実在の指標の値で goal が選択肢から外れることを expect.options で確かめる。記録再生で同一のスナップショットの列。inputs と開始時スナップショットのファイルはフィクスチャを `{from: パス}` で参照する。三つのペルソナを台本の user の代わりに束縛しても期待どおり（持ち帰った問いを尋ねる、最初の質問で保留して再開する）。偽の本体は訪問のたびに memory\_out のすべての項目を書き、持ち帰った記憶は、問いが解けた後の訪問が空の一覧を書くので最後の記憶に残らない（expect.memory で確かめる）
- 分布テスト: markov.yaml の 12 基準がすべて通り（400 回、種 20000）、markov\_shifted.yaml の 14 基準はすべて落ちる。release の訪問 2 以降の goal は 0.969（62/64）で、基準 [0.88, 1.0]（二項分布の裾から決めた）に入り、「carry で変わらない」とした基準（0.65〜0.85）は落ちる。assurance のゲートを RandomGateClassifier で揺らす markov\_gated.yaml の 4 基準もすべて通る（400 回、種 50000。ゲートの訪問 1 の changes\_requested 0.209（45/215）、訪問 2 以降 0.156（17/109）、完了 0.625、implement の訪問の回数の平均 2.002。往復 8 の設計値の変更の後の値）。markov\_gated\_shifted.yaml の 3 基準はすべて落ちる。各基準が設計値の両側に標準誤差の 3 倍以上 5 倍以下あることを、synthesize の evaluations（厳密な E[n]）と visits\_variance から確かめ、外れる側の期待件数が 10 に届かない基準は二項分布の裾の確率（0.1% 以下）で確かめる。分布テストに使う二つの実行の集まりに、指標の測定の失敗と、印が goal なのに goal が選択肢から外れた評価が一度も無い
- 独立性検証: divergent は stage:implement=goal（訪問 1 → 1）で violated（p = 0.0005、代表 136 と 126）。markov は、全状態を判定できた検定の数で alpha を割って violated が無く、同じ状態は p = 0.23（「p 値が 0.001 以上」で確かめる。往復 10）。intake の goal のペルソナごとの三つの代表は、markov で p = 0.44、divergent で p = 0.78。ゲートを揺らす実行にも violated が無い
- E2E: カバレッジ計画が全 (ステージ, クラス) の 30 を踏む（往復 10 で 31 にし、往復 11 で tests\_defective を取り消して 30 に戻った。誘発と注入の両方で、誘発の台本を与えた目標はすべて誘発で踏む。intake の質問にはペルソナが答える）。推定したモデルと設計値のモデルの予測が、どちらもゲートの評価の結果を含むすべての量で実測と一致（k = 4）。ゲートの分布を足した設計値のモデルの予測も、ゲートを揺らした実行の 46 の量（assurance のゲートの goal と changes\_requested を含む。往復 8 で plan\_tasks の design\_incomplete を設計値から外して 47 から減った）と一致する。入り方が二つ以上あるステージの訪問 2 以降の結果は、markov とゲートを揺らす実行のどちらでも入り方によらない（entry\_dependence で、判定できた検定の数で alpha を割って violated 無し。implement は入り方 5 通りで p = 0.56 と 0.43）
- オラクル: `build_corpus(..., unique_states=True)` でステージの 123 項目（往復 8 で plan\_tasks の design\_incomplete を外したので、往復 7 までの 127 から変わった。往復 10、往復 11 では変わらない）。印を読む分類器は κ 1、ECE 0.1。既知の混同行列の分類器は κ 0.603、ECE 0.275、答え無し 6（選択肢に無いクラス）で、独立に計算した値と一致。揺れる分類器の再実行の一致率は 0.748（1 − ⌈123/4⌉/123 に一致）
- 記述と代表の整合（第15.1節）: 人がラベルを付ける材料 docs/human-labeling.md（49 項目。訪問 1 が 37（intake 2、analyze 7、discovery のゲート 3、design 3、plan\_tasks 2、architecture のゲート 1、unit\_test 3、acceptance 12、review 4）、訪問 2 以降が 12（intake 2、analyze 7、discovery のゲート 3））を、試しの実行（tests/stochastic.yaml の labeling、240 回、種 90000）から、手引き第15.1節の変えた所に絞る時の目安（対象、訪問、まとめ方）で選ぶ。人のラベルはまだ無い。受け取ったら `python -m software_factory.labeling compare` で印と比べる（往復 11 で作り、往復 12 で選び方を目安に合わせ、往復 13 で改められた目安に合わせて review を足した）
- トリアージ: 確信度 0.6 の印を読む分類器で 24 回実行し、全評価（unknown を含む 361 項目）を確信度 0.7 未満として待ち行列に足し、五種類の判定（label、classifier\_error、new\_class\_proposal、description\_revision\_proposal、not\_a\_problem）を付けて未判定を無くした。ワークフロー定義は変わらない。ラベルを付けた項目をコーパスに足してオラクルのレポートを出した（κ 1、ECE 0.4）

## 経過（2026-10-22）

1. 読んだもの: adopting.md、api.md、toy-minimal 一式、schema/workflow.schema.json、contract/contract.md、contract/conformance/README.md と scenario.schema.json、contract/formats/*.schema.json、contract/trace.schema.json。公開の名前の引数は `inspect.signature` と docstring で確かめた（gaps A1）
2. 使い捨てのワークフロー（スクラッチ）で、入れ子のディレクトリのフィクスチャの写し、ディレクトリの inputs、記憶が無い時の `read_memory`、保留中の質問の形を試した
3. `scripts/check.sh` を読まずに実行し、出力から手順を知った。意図的に壊したコードのフィクスチャがリポジトリ全体の検査に拾われるので、mypy と ruff の振る舞いを試して tests/fixtures/.code/ に置くことにした（gaps B1）
4. 固定のコードベース（tests/fixtures/.code/baseline/repo/: shopcart の Cart）と、実装（8 変種）と単体テスト（5 変種）のフィクスチャ。変種ごとに実在の指標を測り、設計どおり（lint は違反 2、scope は範囲外 1、broken はビルド失敗、thin はカバレッジ 68〜71%、defect\_found のテストは ok と ok\_b で落ち ok\_fixed で通る）
5. 指標レジストリ。ツールの結果を内容のハッシュで覚える（gaps B4）。ランタイムが args を読み取り専用の Mapping で渡すので鍵の作り方を直した（gaps B3）
6. workflow.yaml。全ステージ goal の台本で 5 つのゲートまで通ることを確かめた
7. シナリオ 14 本。遷移の列を手で並べる道具で YAML を書いた（gaps F1）。最初の実行で全部通った。道具は後で software_factory/scenarios.py としてコミットし、出力と YAML の一致をテストにした
8. 確率的な本体、ペルソナ、設計値の表。50 回の実行で 1 回あたり約 46 ms（ツールの結果を覚えた後）
9. 設計値から expectations の根拠を出す design.py（gaps D3）。synthesize と一致することを確かめてから、幅を設計値の両側に 3.2〜3.6 SE で置いた
10. 独立性検証、E2E、オラクル、トリアージ。オラクルでコーパスの重複が FlakyClassifier を狂わせることに気づき、状態文書ごとに一項目にした（gaps E1）。トリアージは項目の数の二乗で遅いので、確信度を下げる評価を絞った（gaps E3）
11. check.sh で本体のテスト（例の id が本体の語と重ならない）が落ち、`verify` → `acceptance`、`request.md` → `feature_request.md`、`open_questions` → `intake_questions` に改名した（gaps B2）。改名でステージの種が変わったので、全テストと数値を取り直した
12. 実行の集まりをセッションで共有し、例のテストの時間を約 3 分から約 2 分に（gaps B6）
13. release に戻る辺が自分自身からの一本だけであることを、定義の上でも確かめるテストを足した（実行の集まりによらない）。`HTF_RUNS=600` でも確率的なテストが全部通ることを確かめた

## 種の割り当て

| 用途 | 本体 | 回数 | 種 |
| --- | --- | --- | --- |
| 分布テスト、独立性検証（markov）、マルコフ合成の実測、オラクル（最初の 60 回） | markov | 400 | 20000 |
| 独立性検証（divergent） | divergent | 400 | 30000 |
| マルコフ合成の推定 | markov | 400 | 40000 |
| ゲートを揺らす分布テスト、独立性検証、マルコフ合成の実測（markov\_gated.yaml） | markov と RandomGateClassifier | 400 | 50000 |
| トリアージ | markov | 24 | 80000 |
| 第15.1節の試し（往復 10。スクラッチで、例のテストには無い） | markov に implement の ok\_fixed と unit\_test の defective を足した試しの分布 | 300 | 70000 |
| 人がラベルを付ける材料（往復 11。往復 12 で分布を変え、120 回から増やした。往復 13 で review の訪問 1 の分布を変えた。docs/human-labeling.md、tests/test\_labeling.py） | labeling（tests/stochastic.yaml） | 240 | 90000 |

種は基準を書く前に決め、基準が通るように選び直してはいない。回数は環境変数 `HTF_RUNS` で増やせる。

## 往復 1（2026-10-22）

フレームワークの側が adopting-gaps.md の 30 項目を直したと言うので、利用者として、読んでよい文書（adopting.md、api.md、api-reference.md、契約と形式、契約適合テスト一式）と実際の振る舞いで確かめた。項目ごとの判定と確かめ方は adopting-gaps.md の「解消済み（往復 1）」にある。

1. 前の状態で check.sh を実行（598 件、116 秒）。例のテストは 148 件、カバレッジの計測の下で約 91 秒
2. 文書を読んで、A1〜A7、B3〜B5、C1、C2、D1、D5、D6、E2、E4 を確かめた。契約に「決定 A2」が二か所残る（gaps N2）。signature の中の型の一部が書かれていない（gaps N1）
3. B1: tests/fixtures/.code/ を普通のディレクトリに移した（implement/、unit\_test/ は他のステージと同じ並びに、変更前のコードベースは inputs/repo/ に）。tests/fixtures/ruff.toml、tests/fixtures/.ruff\_cache/、tests/conftest.py の collect\_ignore を外した。fixture\_dir の .code の分岐と、inputs() の二か所からの寄せ集めが要らなくなった
4. F1: software\_factory/scenarios.py が inputs と expect.starts の files をフィクスチャへの参照で書くようにし、14 のシナリオを作り直した。読み込んだシナリオが前と同じことを全項目で比べた。シナリオの inputs のテストは load\_scenario の結果で比べる
5. F2: シナリオの実行（deterministic.run）に user を通し、三つのペルソナを二つのシナリオに束縛するテストを足した。E2E のカバレッジで intake の goal の台本に質問を足し、ペルソナを束縛した
6. D3: synthesize の evaluations と visit\_outcomes から E[n] を出すようにした（design.expected\_count）。markov.yaml の注記を厳密な値に直し、基準の幅を確かめるテストを足した。design.simulate は訪問の回数の標準偏差のためだけに残した（gaps N4）
7. E1: tests/test\_oracle.py の手書きの重複除きを unique\_states=True に替えた
8. E3: tests/test\_triage.py の Hesitant を外し、確信度 0.6 の MarkerClassifier で全評価を待ち行列に入れる形にした
9. B7: tests/test\_conformance.py を conformance\_scenarios() に、形式の schema を load\_contract\_schema に替えた
10. B2: workflow.yaml を一時的に前の名前（verify、request.md、open\_questions）に戻し、tests/test\_package.py が通ることを確かめて元に戻した。改名は戻していない（種が変わり数値を取り直すことになるため）。重なる語の報告は一度に出るが、pytest の既定の出力では切れうる（gaps N3）
11. D4: 実行ごとの乱数でゲートを揺らす偽の分類器で、ゲートの分布を持つマルコフ合成が実測と合うことをスクラッチで確かめた（gaps N5。例には入れていない）
12. B6: synthesize は約 2.5 秒（計測の下）になった。指標の tasks.yaml の読み込みを内容ごとに覚えた。例のテストは約 82 秒で、第11節の目安（一分）を超える（gaps N7）
13. README.md の構成の表に残っていた open\_questions を intake\_questions に直した。README、tests/README.md、tests/fixtures/README.md、stochastic.yaml の注記を新しい置き場に合わせた
14. check.sh が通る（602 件、105.3 秒）

外した回避策: tests/fixtures/.code/ と ruff.toml と collect\_ignore（B1）、シナリオにフィクスチャの内容を写すこと（F1）、標本による E[n] の見積もり（D3）、コーパスの手書きの重複除き（E1）、確信度を下げる評価を絞る偽の分類器（E3）、リポジトリのパスでの契約適合テストと形式の読み込み（B7）。残した回避策: 指標の結果を覚えること（B4。文書が勧める形になった）、改名した名前（B2）、訪問の回数の標準偏差のための標本（N4）。

## 往復 2（2026-10-22）

フレームワークの側が往復 1 の N1〜N7 を直したと言うので（コミット 1412a8d。往復 1 の変更は a8c7468）、読んでよい文書の差分と実際の振る舞いで確かめた。項目ごとの判定と確かめ方は adopting-gaps.md の「解消済み（往復 2）」にある。

1. 往復 2 の前の状態で、例のテストは 152 件、カバレッジの計測の下で約 88 秒（synthesize が遅くなった分、往復 1 の約 82 秒より長い）
2. N1、N2: 公開の名前に足された型を import し、契約と文書から決定の番号が消えたことを検索で確かめた
3. N3: workflow.yaml の記憶の名前を一時的に本体の語（checkpoint、runner、fakes）にして check.sh を実行し、16 か所が一行ずつ出ることを確かめて元に戻した（一回目は自分の conftest.py の mypy の誤りで pytest まで進まなかったので、直してやり直した）
4. N4: visits\_variance の値が前の標本と合うことを確かめ、design.simulate と test\_design\_samples\_match\_exact\_synthesis を外した。test\_correct\_expectations\_follow\_the\_design の mean\_visits の幅は visits\_variance から出す。markov.yaml の注記を直した
5. N5: RandomGateClassifier を例に取り込んだ。run\_set に gates、design\_model に gates、expected\_count に scope を足し、run\_expectations は bindings の gates も読む。tests/expectations/markov\_gated.yaml（種 50000 は基準を書く前に決めた）と、その実行の集まり（conftest の gated\_runs）と予測（gated\_prediction）を足した。テストを四つ足した（gated の基準が通る、gated の基準が設計値に沿う、ゲートの分布の予測が実測と合う、ゲートを揺らしても violated が無い）
6. N6: 第14節の調べ方（訪問 2 以降を直前の辺で分ける）を、carry で変わる本体と変わらない本体でスクラッチで試した。調べ方は違いを見分けたが、推定したモデルの予測は carry で変わる本体でも実測と合った（gaps N9）
7. N7: 例のテストは約 107 秒で、新しい目安（およそ二分以内）に収まる。推定の集まりは estimate\_model を確かめるために残した
8. compare\_prediction がゲートの評価を比べないことに気づき、ゲートの回数は visit\_outcomes と手で比べた（gaps N8）
9. README.md、tests/README.md を新しい実行の集まりに合わせた
10. check.sh が通る（609 件、133.9 秒）

外した回避策: 訪問の回数の標準偏差のための標本 design.simulate（N4）。足したもの: ゲートを揺らす実行の集まり（N5。往復 1 では「確率的な実行のゲートはいつも goal」が残っていた）。

## 往復 3（2026-10-22）

フレームワークの側が往復 2 の N8、N9 を直したと言うので（コミット前の作業ツリー）、読んでよい文書の差分と実際の振る舞いで確かめた。判定と確かめ方は adopting-gaps.md の「解消済み（往復 3）」にある。

1. N8: compare\_prediction の比べる量にゲートの量（gate:<フェーズ>=<結果>）が入り、ゲートを揺らした実行で 41 から 47 になって全部一致することを試した。tests/test\_e2e.py の test\_estimated\_prediction\_matches\_measurement が量の種類を {status, visits, outcome} の固定の集合で確かめていて落ちていたので、gate を足した。test\_gate\_distribution\_prediction\_matches\_measurement の、ゲートの評価の回数を visit\_outcomes と訪問の区分ごとに手で比べていた部分を外し、ゲートの量が比べる量に入ることを確かめる形にした（区分ごとの割合は markov\_gated.yaml の基準が確かめる）
2. N9: entry\_dependence を、往復 2 のスクラッチの carry で振る舞いが変わる本体と、markov、ゲートを揺らす実行、divergent にかけた。前者だけ implement の訪問 2 以降が violated（p = 0.0005）。例のテストに test\_class\_distributions\_do\_not\_depend\_on\_the\_entry（markov とゲートを揺らす実行で violated が無く、implement は入り方 5 通りで not\_detected、release の入り方は自分自身からの一本だけ）を足した
3. 量が増えたことを公開の文書から知る手段が無いことを、gaps N10 に書いた
4. check.sh が通る（614 件、144.5 秒）

外した回避策: ゲートの評価の回数の手での比較（N8）。往復 2 で手で辿った入り方の分け方（N9）はスクラッチだけだったので、例の側で外すものは無い。

## 往復 4（2026-10-22）

フレームワークの側が N10 を直したと言うので（コミット a583f19）、docs/changelog.md だけを読み、往復 1〜3 で知らされた変更のうちこの例が使うものがすべて載っているか、互換性に注意する変更が分かるかを確かめた。v0.1.0 からの公開の文書の差分（git の差分。読んでよい文書だけ）とも突き合わせた。

1. N10 は解消。互換性に注意する変更（compare\_prediction の量の追加）が先頭にあり、往復 3 で落ちたテストの理由と直し方が分かる。この例が使う変更はすべて載っている
2. 載っていない小さな変化（第11節の例の語の検査の除外と報告、時間の目安）を gaps N11 に書いた。この例は頼っていない
3. 例のコードとテストは変えていないので、check.sh は実行していない（往復 3 の最後で 614 件が通っている）

## 往復 5（2026-10-22）

フレームワークの側が N11 を直したと言うので（コミット 9c7b4cd）、docs/changelog.md の「変えたもの」を読んだ。

1. N11 は解消。「このリポジトリの中に例を作る場合（adopting.md 第11節）」に、fixtures の除外、例の語の検査の変化（公開の名前とワークフロー定義の例の語を除き、重なりを一度に一行ずつ出す）、時間の目安の変化（一分以内からおよそ二分以内）がまとめて載った。adopting.md 第11節の文と食い違いが無い
2. adopting-gaps.md の未解消は無しになった
3. 例のコードとテストは変えていないので、check.sh は実行していない（往復 3 の最後で 614 件が通っている）

## 往復 6（2026-10-22）

人間が workflow.yaml をレビューする前に、検証役（第三者）が二つの確認をした（docs/review-findings.md）。workflow.yaml の事前レビューは「直してから出すべき」（高 2、中 8、低 9）、分布テストの基準の確認は「承認」（中 2、低 4）。フレームワークの側も手引きを直した（adopting.md 第2.1節、第4節、第12節）。高と中はすべて直し、低も一つを除いて直した。分類体系（end\_state の追加、分割、統合）は変えていない。種は変えていない。

指摘ごとの対応:

| 指摘 | 対応 |
| --- | --- |
| 高 1 記憶が前の値のまま状態文書に出る | 直した。全ステージの description に「無ければ空の一覧。訪問のたびに必ず書く」。task\_unclear の条件を記憶と impl\_notes.md の「## 問い」の両方に。シナリオの台本も memory\_out のすべてを毎回書くようにし（goal の訪問は tests/stochastic.yaml の ok の値）、開始時スナップショットの記憶（上流が書いた空の一覧を含む）と最後の記憶の期待を直した。持ち帰った値が最後の記憶に残らないことを、5 本のシナリオの expect.memory で確かめる。偽の本体の全変種とシナリオの全訪問が memory\_out を書くことをテストにした |
| 高 2 plan\_tasks の goal を代表が満たせない | 直した。goal を「paths が design.md の構成に収まり、tests が repo/tests/ の下にあり、paths が重ならない」に |
| 中 3 implement の指標が落ちた時の行き先 | 直した。description に自己点検と違反の記録を、quality\_violation に「既存のテストを落とす」「design.md の構成から外れる」を足した（境界の変更）。impl\_violations が空なら unknown になるのは意図どおりと README に書いた |
| 中 4 unit\_test のテストの不備が unknown | 直した。description に自己点検を足し、tests\_insufficient を「unit\_test 自身が直すべき不足か不備」に広げた（境界の変更。「テストはすべて通るが」を外した）。不備の end\_state を足す案は README に提案として書いた |
| 中 5 四つのゲートが unknown に落ちる | README に「フェーズゲートの落ち方」を書いた |
| 中 6 review の goal が観測できない | 直した。review.json を {"reviewed": [...], "findings": [...]} にし、goal を「reviewed が paths と tests をすべて含む」に。四つの代表の review.json に reviewed を足した |
| 中 7 テストへの指摘が unknown | 直した。changes\_requested を repo/tests/ の修正にも広げ、implement が failing\_tests と repo/tests/ の指摘を impl\_notes.md の「## テストへの依頼」に書き写し、unit\_test がそれに応える形を description に書いた。implement の代表の impl\_notes.md に節を足した |
| 中 8 changes\_requested が指摘無しでも成り立つ | 直した。「修正を要する指摘が一つ以上あり」と、ゲートの条件を書き分けた |
| 中 9 「REQ-1は」を数えない | 直した。照合を英数字の境界だけで切る。design の「## 対応」と CHANGELOG.md の行の書き方を description に決めた。テストを足した |
| 中 10 代表が記述と合わない | 直した。requirement\_unmet の代表を REQ-1（割引額でなく支払額を切り捨てる。333 円に PCT10 で 299 円）の不合格にし、記述を「要件の記述か受け入れ基準に反する」に広げた（設計値の記憶とシナリオの UNMET も同じ文に）。plan\_tasks の unknown の代表を、paths が重なるタスクにした |
| 基準 中 1 release の訪問 2 以降の幅 | 直した。min 0.90 → 0.88（二項分布 n = 65、p = 0.97 で誤って落ちる確率 0.33% → 0.07%）。注記に根拠を書き、歪む基準を裾の確率で確かめるテストを足した |
| 基準 中 2 異常終了を覚える | 直した。意味の決まった終了コードだけを覚え、異常終了は MetricError にする（pytest の 2 は収集の失敗の時だけ「通らない」）。分布テストの二つの実行の集まりで、測定の失敗が無く、印が goal の評価に goal が選択肢にあることを確かめるテストを足した。契約のテスト（例外と警告が無い）もゲートを揺らす集まりに広げた |
| 低 L-1 requirement\_count の min 3 | README に「この依頼に合わせた値」と書いた |
| 低 L-2 持ち帰った問いが goal で観測できない | 一部。連鎖で失われる食い違いは analyze の description に「intake\_questions に含める」と書いた。intake.md に「## 持ち帰った問い」を設ける案は、偽の本体とフィクスチャの形を変えるので採らず、理由と案を README に書いた |
| 低 L-3 範囲の違反は分類器に見えない、paths が狭すぎる時 | 直した。quality\_violation に「この列挙で判断する」と、implement に「paths の外を変えないと実装できない時は task\_questions に」を書いた |
| 低 L-4 blocking が真偽値でない | 直した（MetricError） |
| 低 L-5 CHANGELOG.md のどこでも数える | 直した。最新の版の見出しの下の「- 」の行だけを数える |
| 低 L-6 release がパッケージの版を上げない | 直さない。release.json はリリースの記録で版の更新は範囲外と description と README に書いた。版を上げていない状態を notes\_incomplete に含めない理由（unknown の代表と食い違う）も README に |
| 低 L-7 割り当てたうえで問いを残す design | 直した。requirements\_gap を広げ、「goal に優先する」を書いた（境界の変更） |
| 低 L-8 戻りで成果物が捨てられる前提 | 直した。持ち帰る記憶をパス、関数、期待する振る舞いで書くことと、開始時に残る前の記憶の扱いを description と README に |
| 低 L-9 冗長な指標と曖昧な文 | 直した（delivery の goal の「review.json の結果に合い」と、construction の goal の「repo/ の変更全体」）。acceptance の tests\_pass は残し、理由を README に |
| 基準 低 L1 ずらした基準が端を共有 | 直した（max 0.17 → 0.16、4.1 SE） |
| 基準 低 L2 release の訪問 1 が規則をわずかに下回る | 直した（[0.15, 0.31] → [0.14, 0.32]）。注記の倍数のずれ（acceptance 3.5、status の上側 3.5）も直した |
| 基準 低 L3 markov\_gated のずらした基準が無い | 直した。markov\_gated\_shifted.yaml（3 基準）と、すべて落ちるテストを足した。status\_rate と mean\_visits が揺らす前後を見分けないことを注記に書いた |
| 基準 低 L4 幅の上限を確かめない | 直した。幅が設計値の両側に 5 SE 以下であることも確かめる |

基準を変えたもの: markov.yaml の release の訪問 1（[0.14, 0.32]）と訪問 2 以降（[0.88, 1.0]）、markov\_shifted.yaml の analyze（max 0.16）。markov\_gated\_shifted.yaml を足した。どれも設計値から導き直し、注記に根拠を書いた。種は変えていない。フィクスチャの内容を変えたが、クラスの選び方は種だけで決まり、metrics\_fail との整合も保ったので、分布テストの観測値、独立性検証の p 値、オラクルの数値（κ 0.623、ECE 0.269、答え無し 7、揺れる分類器の一致率 0.748）、トリアージの 361 項目は前と同じ。

1. 例のテストは 173 件（前は 157 件）で、すべて通る
2. フレームワークの文書だけでは判断できなかったこととして、印を読む偽の分類器の下では記述と代表の食い違いがテストに出ないことを gaps N12 に書いた
3. check.sh が通る（633 件、145.5 秒）

## 往復 7（2026-10-22）

フレームワークの側が N12 を直したと言うので（コミット ef46fe8。adopting.md 第15.1節と `unmarked`）、手順を試した。

1. markov と divergent の 400 回ずつを一つの置き場で走らせ、`build_corpus(..., unique_states=True)` のステージの 315 項目から (ステージ, 印) ごとに一つ、30 項目を選んだ。並びを混ぜ、`unmarked` で印を除いた状態文書と選択肢の記述だけを読んで、試しのラベルを付けた（スクラッチで。例のテストには入れていない）
2. `oracle_report(MarkerClassifier(), corpus, labels)` で κ 0.915。食い違いは acceptance の requirement\_misread（前提が precise\_pm の回答にしか無い）と、plan\_tasks の design\_incomplete（goal の design.md は REQ-3 と REQ-4 を受け持たせている）の 2 件。同じ見方で、analyze の goal の代表が vague\_founder の回答と組むと根拠を欠くことも分かった
3. N12 は解消。三つの食い違いはこの例の代表の誤りで、直し方の案とともに README の「記述と代表の整合（試しのラベル）」に書き、人間のレビューに回す（直していない）
4. 例のコードとテストは変えていないので、check.sh は実行していない（往復 6 の最後で 633 件が通っている）

## 往復 8（2026-10-22）

第三者の検証役が F4 の完了を判定した（完了の条件はすべて満たし、読取の制限も守られている）。例の側の指摘、中 2 と低 6（docs/review-findings.md の E）に対応した。フレームワークの側も手引き第15.1節を直した（ゲートの項目も含める、上流の違いで分ける）。分類体系は変えていない。種は変えていない。

| 指摘 | 対応 |
| --- | --- |
| E-M1 (1) acceptance の requirement\_misread の前提が precise\_pm にしか無い | 直した。三つのペルソナとも「レジの画面で入力」を答え、代表の verification.md は前提を intake.md の回答と requirements.md の「## 利用者」に置く |
| E-M1 (2) plan\_tasks の design\_incomplete が design の goal の代表と矛盾する | 成果物の直しでは整合させられない（design の goal の後に記述どおりに起こる代表が無い）ので、設計値から外した（incomplete を引いていた訪問は ok になり、ほかの選び方は変わらない）。フィクスチャを消し、E2E は注入で踏む。判断を README の「人間のレビューで確かめてほしいこと」に書いた |
| E-M1 (3) analyze の goal が vague\_founder と矛盾する | 直した。vague\_founder は、言い方はくだけているが値を決めて答える |
| E-M1 (4) REQ-2 の下限が最初の回答に根拠を持たない | 直した。三つのペルソナとも、最初の回答に割引額の切り捨てと 0 円の下限を含める。それに合わせ、needs\_unclear が持ち帰る問いを、どのペルソナも今は決めていない点（キャンペーンの後も使えるか、何回使えるか）にし、analyze の unclear の代表を直した |
| E-M2 discovery のゲートの goal を代表が満たさない | 直した。requirements.md に「## 利用者」の節を設けた（代表の直し） |
| E-L1 主経路は REQ-1 の欠陥を持ったままリリースする | assurance のゲートの goal に「判断は verification.md と review.json に基づく」を足し（記述の改訂）、意図を README に書いた |
| E-L2 越境の数え方と requirement\_misread のシナリオ | 直した。docstring を直し、acceptance → analyze のシナリオ（15 本目）を足した |
| E-L3 unit\_test の goal がテストへの依頼を見ない | 直した（記述の改訂） |
| E-L4 揺れる分類器の一致率の確かめ方 | 直した（1 − ⌈n/4⌉/n と一致を確かめる） |
| E-L5 memory\_out を毎回書くことを設計値の表でだけ確かめる | 直した。分布テストの二つの実行の集まりで、印が goal の評価の終了時スナップショットの memory\_out が goal の変種の値に等しいことを確かめる |
| E-L6 補正の無い alpha で全状態を確かめる | 直した。仕込んだ状態はそのまま確かめ、全状態は判定できた検定の数で alpha を割って確かめる（独立性検証と入り方の検定の両方） |

基準を変えたもの: plan\_tasks の分布を変えたので、markov.yaml と markov\_gated.yaml の全基準を設計値から導き直した（E[n]、中心、標準誤差を注記に書いた）。変わった値は、markov.yaml の release の訪問 1（[0.15, 0.31]）、status\_rate（[0.62, 0.77]）、mean\_visits（[1.48, 1.86]）、markov\_gated.yaml の status\_rate（[0.59, 0.75]）と mean\_visits（[1.67, 2.11]）、markov\_gated\_shifted.yaml の status\_rate（[0.76, 0.90]。正しい基準と端を共有しないように）。release の訪問 2 以降は、二項分布（n = 66）で 0.88 の誤って落ちる確率が 0.08% で、そのまま。markov\_shifted.yaml は値を変えず、注記の距離を測り直した。

第15.1節のやり直し: markov、divergent、ゲートを揺らす実行（各 400 回）を一つの置き場で走らせ、`build_corpus(..., unique_states=True)` の 484 項目（ステージ 371、ゲート 113）から、(scope, 対象, 印, ペルソナ) ごとに一つ、56 項目（ステージ 47、ゲート 9。ペルソナで変わる項目は各ペルソナ 11）を選んだ。並びを混ぜ、`unmarked` で印を除いた文書と選択肢の記述だけを読んで試しのラベルを付けた（人手のラベルではない。ラベルを付けたのはフィクスチャを作ったエージェント自身）。`oracle_report(MarkerClassifier(), corpus, labels)` で κ 1.0、食い違い無し。

1. 例のテストは 177 件（前は 173 件）で、すべて通る。シナリオは 15 本
2. 指摘の三つの食い違いは、同じ形（クラスを種だけで選ぶので、代表は組みうるすべての上流と整合しなければならない）だった。手引きにこの制約が無いことを gaps N13 に書いた
3. check.sh が通る（638 件、133.3 秒）

## 往復 9（2026-10-22）

フレームワークの側が N13 を直したと言うので（コミット 6220773）、adopting.md 第12節の差分と changelog.md を読んだ。

1. N13 は解消。第12節の「実行のしかた」に「代表は、届きうるすべての上流の成果物と整合させる」の項があり、ペルソナの回答や上流の変種と組み合わさること、上流の goal と両立しないクラスには確率的な代表を置かずシナリオか E2E の注入で踏むこと、第15.1節で上流の違いを分けて確かめることが書かれている。changelog.md の「未公開」にも載っている
2. この例は往復 8 で、この項のとおりにしてある（plan\_tasks の design\_incomplete は E2E の注入、ペルソナと持ち帰る問いの整合、第15.1節のペルソナごとのやり直し）ので、例は変えていない
3. adopting-gaps.md の未解消は無しになった。例のコードを変えていないので、check.sh は実行していない（往復 8 の最後で 638 件が通っている）

## 往復 10（2026-10-22）

人間が README の「人間のレビューで確かめてほしいこと」と、完了判定の二回目（正常）が渡した事項をレビューして回答した（docs/review-findings.md の F）。回答に合わせて F-1〜F-3 に対応し、低の F-L1〜F-L3 もすべて直した。記述の意味を変えたのは F-1（人間が採った分類体系の変更）の範囲だけ。種は変えていない。

| 指摘 | 対応 |
| --- | --- |
| F-1 unit\_test に tests\_defective を足す | 足した。end\_state は impl\_defect、tests\_defective、tests\_insufficient、unknown（優先はこの順）。tests\_defective → unit\_test（carry test\_defects と coverage\_gaps、max 2）。記憶 test\_defects と test\_report.md の節「## 不備」を新しくし、description、memory\_in と memory\_out、goal（「## 不備」が空）、construction のゲートの goal（「不備」）を合わせた。今の不足の代表 thin に不備に当たる点が無かったので、確率的な本体の分布、設計値、基準は変えず、代表 unit\_test/defective を確率 0 の変種として置いて、E2E の誘発とシナリオ unit\_test\_defective\_self\_rollback で踏む。第15.1節の試しをやり直した。README の構成の表、遷移の被覆（通したランナー）、「人間のレビューで確かめてほしいこと」を合わせた |
| F-2 README に人間の回答 | 「人間のレビューで確かめてほしいこと」を、決まったこと、確かめてほしいこと、まだのこと、低への対応、提案に分けて書き直した。design\_incomplete に、design の goal を正しく満たした後でも implement の task\_unclear（paths の外のファイル）から起きうる経路を書き足し、「運用者の goal 到達扱いか分類の誤りで通った後にしか起きない」を直した（tests/stochastic.yaml の plan\_tasks の注記も） |
| F-3 plan\_tasks → design のシナリオ | 足した（plan\_tasks\_design\_incomplete\_rollback）。design が要件への問いを残すが確信度が低く unknown になり、運用者が goal 到達扱いで続行し、plan\_tasks が構成の欠け（REQ-3 と REQ-4）を記憶 design\_issues に書いて design に戻る。expect.starts で design の訪問 2 の記憶に空でない design\_issues が届くことを確かめる。代表 plan\_tasks/incomplete は上流の design/gap と組むので記述と食い違わない（design/ok とは組まない） |
| F-L1 注記の数字 | 直した（markov.yaml の release の訪問 1 は 3.21 SE と誤って落ちる確率 約 0.13%、visits\_variance 1.358 と標準偏差 1.165、markov\_shifted.yaml の 4.7 SE、design.py の docstring）。指摘の外で、markov\_gated.yaml と markov\_gated\_shifted.yaml の倍数の丸めを四捨五入に揃えた。基準の値は変えていない |
| F-L2 絞った独立性の確かめ | 直した。markov の stage:implement=goal の訪問 1 → 1 と、入り方の検定の implement を「判定でき、p 値が 0.001 以上」で確かめる。同じ形の intake のペルソナの代表の確かめ（markov と divergent）も合わせた。tests/README.md に、HTF\_RUNS や種を変えると落ちうることを書いた |
| F-L3 (1) discovery のゲートの「利用者」 | 代表の側で直した。analyze の goal と needs\_unclear の代表の requirements.md から「## 利用者」を外し、REQ-3 を「購入者（店のお客さん）がレジの画面で入力したコードのうち、…ValueError で拒む」にした。design の goal の代表の REQ-3 の対応に「画面は repo/ の外で、コードを文字列で受け取る」を、acceptance の requirement\_misread の代表の参照を REQ-3 に。discovery の goal の記述は変えていない |
| F-L3 (2) vague\_founder | 「割り引く額の端数は切り捨て」にした |
| F-L3 README の表 | 「フェーズゲートの落ち方」の定性の条件を、workflow.yaml のフェーズの goal の文に合わせた |

決めた境界と理由（全文は README の「確かめてほしいこと」）:

- 不足は「足りない」（テストを足せば直る: テストの無い受け入れ基準と「## テストへの依頼」、実行されない箇所）、不備は「誤っている」（今あるテストを直すか消す: 要件に反する期待、lint の違反、tests に無いファイルの変更）。F-1 の案のとおりで、案に「テスト自身の誤り（準備、呼び出し、import）で失敗するテスト」を足した。impl\_defect（テストではなく repo/src/ が誤っている失敗）と合わせて、失敗したテストをどちらが誤っているかで分けきるため
- 要件に反する期待は、通るか失敗するかによらず不備（通るテストは誤りを隠す）
- 優先は impl\_defect、tests\_defective、tests\_insufficient の順。誤ったテストがあると、カバレッジや「基準にテストがあるか」の判断が当てにならないので、不備を不足より先にした
- 不備で戻る時は同時にある不足も持ち帰る（carry test\_defects と coverage\_gaps）。前は coverage\_gaps 一つで両方を持ち帰っていたので、分けて情報を落とさないため
- max は 2（implement の自分自身への quality\_violation と同じ）。unit\_test が自分自身に戻れる回数の合計は 2 から 4 になる
- 記憶と節を分け、条件は記憶 test\_defects と「## 不備」の両方（implement の task\_unclear と同じ形）

変わった数値:

- unknown 以外の end\_state: 12 → 13。E2E のカバレッジの (ステージ, クラス): 30 → 31。定義の上のロールバックの辺: 12 → 13
- シナリオ: 15 → 17。定義の上のロールバックの辺 13 本をすべてシナリオが通る（前は plan\_tasks → design を E2E の注入だけが通っていた）
- 分布（tests/stochastic.yaml の profiles）、設計値のモデル、expectations の基準: 変えていない。変種 defective は variants にあるが、どの分布にも無いので、種と変種の対応も、分布テストの観測値も前と同じ（markov.yaml の unit\_test の訪問 1 の tests\_insufficient の基準 [0.12, 0.28]、設計値 0.20 もそのまま）。注記の数字だけを直した（F-L1）
- オラクル: ステージの 123 項目、既知の混同行列の分類器は κ 0.603、ECE 0.275、答え無し 6、揺れる分類器の一致率 0.748。どれも前と同じ（tests\_defective の行は足されたが、確率的な実行に現れないので効かない）
- 独立性検証と入り方の検定の p 値: markov の stage:implement=goal（訪問 1 → 1）0.23、intake のペルソナの代表 0.44（divergent で 0.78）、入り方の implement 0.56（ゲートを揺らす実行で 0.43）。divergent の検出は 0.0005 で violated のまま
- 第15.1節の試しのラベル: 32 項目（ステージ 25、ゲート 7）で κ 1.0、食い違い無し（下の 4）
- 例のテスト: 177 → 188 件

検証:

1. 先に完了条件をテストにした: unit\_test の end\_state と戻りと記憶（test\_definition.py）、unit\_test の全フィクスチャの test\_report.md の節が印のクラスの記述の証拠と合うこと（同）、どのペルソナも割引額の端数の切り捨てを答えること、analyze の goal の代表が利用者を受け入れ基準のある要件に書くこと（test\_personas.py）、シナリオ二本（scenarios.py で作る）、E2E の誘発の tests\_defective（test\_e2e.py）、変種 defective の指標（test\_metrics.py が variants から自動で作る）。直す前に 11 件が落ちることを確かめた（E2E のカバレッジのテストは、定義に tests\_defective が無いうちは踏むべき対象に入らないので、その時点では通った）
2. 直した後、定義の上のロールバックの辺 13 本をすべてシナリオが通ることのテストを足した（test\_scenarios.py）
3. 二本の新しいシナリオで、expect.starts の持ち帰った記憶（design\_issues、test\_defects）を空に書き換えると落ちることを、スクラッチで確かめた（持ち帰った記憶を実際に確かめている）
4. 第15.1節の試し（スクラッチ。例のテストには入れていない）: 全変種を踏むように、markov の分布に implement の ok\_fixed と unit\_test の defective を足した試しの分布で 300 回（種 70000）を一つの置き場で走らせ、`build_corpus(..., unique_states=True)` の 353 項目（ステージ 263、ゲート 90）から、変えた所に絞って (scope, 対象, 印, 上流の違い) ごとに一つ、32 項目を選んだ（unit\_test 14: 印 5 種を implement の変種で分けた。analyze の goal と needs\_unclear をペルソナで分けて 6、acceptance の requirement\_misread 3、design の goal と requirements\_gap 2、construction のゲート 4、discovery のゲートをペルソナで分けて 3）。並びを混ぜ、`unmarked` で印を除いた文書（同じ対象の二つ目からは一つ目との差分）と選択肢の記述だけを読んで試しのラベルを付けた。差分で読んだので、analyze の二項目（「## 未決事項」と記憶が一つ目と同じで、問いを持つ）を一度 goal と読みかけ、差分に現れない節を一つ目で確かめて needs\_unclear にした。`oracle_report(MarkerClassifier(), corpus, labels)` で κ 1.0、食い違い無し。人手のラベルではない（ラベルを付けたのはフィクスチャを作ったエージェント自身）
5. 例のテストは 188 件すべて通る。ruff check、ruff format、mypy strict も例の中で通る
6. check.sh が通る（ruff check、ruff format、mypy strict、pytest 649 件で 142.6 秒、全体で約 2 分 23 秒）

手引きと公開 API の文書だけでは判断できなかったこととして、クラスの粒度を独立性検証の結果以外の理由で変えてよいか（N14）と、シナリオの files でディレクトリの参照とその下のファイルの鍵が重なる時の扱い（N15）を adopting-gaps.md に書いた。

## 往復 11（2026-10-22）

往復 10 の後、第三者が二度確かめ（事前レビューと、別のモデルによる敵対的なレビュー）、人間が決めた（docs/review-findings.md の G）。決定は二つ: unit\_test の tests\_defective の分割を取り消す（戻り先が同じで、違いは集計の都合だけ。クラスは下流の振る舞いに関する同値類で、集計のための分類ではない。手引き第13節に書き足された）、往復 10 で代表を変えた所は人が印を除いて読んでラベルを付ける（全部の付け直しはしない）。G-1〜G-6 に対応した。記述は、G-1 で人間が承認した往復 10 の前の文に戻したほかは変えていない。種と、分布テストの分布（markov、divergent）、設計値、基準の値は変えていない。

| 指摘 | 対応 |
| --- | --- |
| G-1 unit\_test と construction のゲートの記述を往復 10 の前に戻す | 戻した。`git show 08f79b4:examples/software-factory/workflow.yaml` をそのまま書き、`git diff 08f79b4 -- examples/software-factory/workflow.yaml` が空（差の無いことを確かめた）。往復 10 と 08f79b4 の差は unit\_test（description、memory\_in と memory\_out、goal、end\_state、rollback）と construction のゲートの goal だけだったので、ファイル全体を戻しても同じ。記憶 test\_defects、tests\_defective の rollback、test\_report.md の「## 不備」が無くなった（節は「## テスト」「## 失敗」「## 未網羅」）。unit\_test の六つのフィクスチャの test\_report.md も、defective を除いて往復 10 の前のものに戻した。coverage\_gaps の項目の書き方で不足と不備を区別すること（任意）はしていない |
| G-2 代表、シナリオ、E2E、テストを合わせる | 代表 unit\_test/defective を tests\_insufficient の確率 0 の代表にした（印、test\_report.md の不備を「## 未網羅」に、記憶を coverage\_gaps に。「## 失敗」は（なし）。tests/stochastic.yaml の variants のクラスと記憶も）。シナリオ unit\_test\_defective\_self\_rollback を、tests\_insufficient で空でない coverage\_gaps を持って unit\_test に戻り、expect.starts で unit\_test#2 の記憶を確かめる形にした（名前は代表に合わせて残した）。E2E の誘発から tests\_defective を外した。README の構成の表、フェーズゲートの落ち方、確率的な本体の仕掛け、通したランナー、tests/README.md、tests/fixtures/README.md、markov.yaml の注記を合わせた |
| G-3 README を人間の決定に合わせる | 「人間のレビューで確かめてほしいこと」から tests\_defective の記述と境界の項目、往復 10 の提案を除き、決まったこと（分割の取り消し、記述を往復 10 の前の文に戻したこと、テスト自身の誤りで落ちるテストは unknown、defective を tests\_insufficient の確率 0 の代表にしたこと、人がラベルを付けること）と、まだのこと（人手のラベル）を書いた |
| G-4 N14、N15 | どちらも解消（adopting-gaps.md の「解消済み（往復 11）」）。N14 は第13節の書き足しで判断でき、取り消しに第13節のクラスを変えた後の一覧を当てはめた。N15 は鍵の並びを変えた 7 通りで「より長い鍵の内容」を確かめ、回避の ok\_files\_by\_file を外した |
| G-5 第三者の事前レビューの低 | 四つとも直した。(1) 戻った直後の訪問の expect.starts が無かった三本（construction\_rollbacks の unit\_test#2、assurance\_gate\_rolls\_back の implement#2、release\_notes\_self\_rollback の release#2）に足し、定義の上のロールバックの辺 12 本のすべてで、どれかのシナリオが戻った直後の訪問の expect.starts に carry する記憶を空でない値で持つことをテストにした（test\_every\_rollback\_edge\_has\_its\_carry\_checked\_at\_the\_next\_start。docstring もそれを指す）。(2) E2E のカバレッジのテストに、誘発の台本を与えた目標がすべて induce で踏まれることを足した。(3) README の「記述と代表の整合」に、plan\_tasks/incomplete はシナリオで分類器が見る状態文書（design/gap と組むもの）を記述だけで読んで確かめたことを書いた（実際に読んだ。design\_incomplete に当たる）。(4) markov.yaml と markov\_gated.yaml の 1.674 を 1.673 にした |
| G-6 人がラベルを付ける材料と、印と比べる仕組み | software\_factory/labeling.py と docs/human-labeling.md（30 項目）、そのコーパス docs/human-labeling.corpus.jsonl を足した。下の「材料」 |

材料（G-6）:

- 試しの実行: tests/stochastic.yaml に分布 labeling を足した（分布テスト、独立性検証、マルコフ合成には使わない）。訪問 1 の分布を寄せ（intake の unknown 0.15、analyze の needs\_unclear 0.35 と unknown 0.15、design の requirements\_gap 0.25 と unknown 0.15、implement の ok、ok\_b、ok\_fixed をほぼ三等分、unit\_test の defective 0.5、acceptance の四つのクラスを 0.25 ずつ）、訪問 2 以降は goal に寄せた。120 回、種 90000（回数と種は材料の項目を選ぶ規則を決めた後に決め、30 の組がすべて出ることを確かめた。`HTF_RUNS` によらない）。約 5 秒
- コーパス: `build_corpus(..., unique_states=True)` で 170 項目（ステージ 123、ゲート 47）。そのうち 162 項目が往復 10 で変えた代表のどれかを含む（requirements.md が下流のほとんどの状態文書に入るため）
- 選び方: 変えた代表を状態文書に含む評価のうち、記述がその内容を証拠に使う対象（intake: vague\_founder の回答、analyze と discovery のゲート: requirements.md と回答、design: requirements.md と design.md、unit\_test: defective、acceptance: requirements.md、verification.md、回答）の訪問 1 のもの（64 項目）から、(対象, 印, 上流の違い) ごとに状態文書の短いものを一つ。上流の違いは、intake.md を読む対象ではペルソナ、unit\_test では goal の実装の変種。acceptance は主経路の実装（ok、ok\_b）の後のものに限る（requirement\_unmet の代表は REQ-1 の誤りを見つけるので ok\_fixed とは組まない）
- 項目の数: 30。intake 2（vague\_founder の goal と unknown）、analyze 7（goal と needs\_unclear を三つのペルソナで 6、vague\_founder の unknown 1）、discovery のゲート 3（ペルソナ）、design 3（goal、requirements\_gap、unknown）、unit\_test 3（defective を ok、ok\_b、ok\_fixed の後で）、acceptance 12（四つのクラスを三つのペルソナで）。ステージ 27、ゲート 3
- human-labeling.md: 冒頭に読み方（印を探さず、選択肢の記述だけで選ぶ。迷った時は unknown と書き、理由を添える）、選んだ項目の範囲と数、ラベルを付けた後の手順。項目ごとに id、対象と訪問、印を除いた状態文書（`unmarked(item.state)`）、選択肢（id と記述）、空の「ラベル:」。並びは対象ごとで、対象の中は項目の id の順（クラスの順ではない）。印は無い（テストで確かめる）。コーパスの source からは分類器の選択（印と同じ）を除いた
- 比べる仕組み: `python -m software_factory.labeling labels --labeler <名前>` が「ラベル:」の最初の id を読み、選択肢に無い id は誤りにして、docs/human-labels.jsonl（label.schema.json の形）を書く。`python -m software_factory.labeling compare` が `oracle_report(MarkerClassifier(), corpus, labels)` と食い違う項目を出す。ラベルのファイルが無ければ「ラベルのファイルが無い」と報告して 1 で終わる（スキップしない。今はこの状態）。`write` が材料を作り直す（埋めた「ラベル:」は空になる）。人が手で書くのは「ラベル:」の行だけで、埋めた後も test\_labeling.py は通る（「ラベル:」を空にして作り直したものと比べる）。ラベルのファイルがあれば、項目と選択肢に合い、human-labeling.md の「ラベル:」と同じであることを確かめる

変わった数値:

- unknown 以外の end\_state: 13 → 12。定義の上のロールバックの辺: 13 → 12。E2E のカバレッジの (ステージ, クラス): 31 → 30（往復 10 の前と同じ）
- シナリオ: 17 本のまま（unit\_test\_defective\_self\_rollback は tests\_insufficient の辺を通す形に）。戻った直後の訪問の expect.starts に carry する記憶を空でない値で持つ辺: 往復 10 は 13 本のうち 9、往復 11 は 12 本のすべて（新しいテストを直す前に走らせて、欠けていた 4 本を確かめた）
- 人がラベルを付ける材料: 30 項目（新しい）
- 分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較: 変わらない（markov と divergent の分布、種、変種の選び方を変えていない）。オラクル: ステージの 123 項目、既知の混同行列の分類器は κ 0.603、ECE 0.275、答え無し 6、揺れる分類器の一致率 0.748（往復 10 と同じことを独立に計算して確かめた）
- 例のテスト: 188 → 197 件（tests/test\_labeling.py の 7 件、test\_stochastic.py の defective の 1 件、test\_scenarios.py の carry の 1 件を足し、test\_definition.py の unit\_test の分割のテストを取り消しの形のテストに置き換えた）

検証:

1. 先に完了条件をテストにした: unit\_test の記述が往復 10 の前の形（end\_state、rollback、記憶、goal と construction のゲートの文）であること、test\_report.md の節が三つで印のクラスの節だけが埋まること（test\_definition.py）、defective が tests\_insufficient の確率 0 の代表であること（test\_stochastic.py）、ロールバックの辺が 12 本で、すべての辺に戻った直後の carry の expect.starts があること（test\_scenarios.py）、E2E の (ステージ, クラス) が 30 で誘発の目標が誘発で踏まれること（test\_e2e.py）、人がラベルを付ける材料と比べる仕組み（test\_labeling.py）。直す前に 6 件が落ち、test\_labeling.py は labeling.py が無いので収集で落ちることを確かめた
2. G-1 の後、`git diff 08f79b4 -- examples/software-factory/workflow.yaml` が空であることを確かめた
3. N15: 鍵の並びを変えた 7 通りのシナリオを `load_scenario` で読み、より長い鍵の内容になることを確かめてから、ok\_files\_by\_file を外してシナリオを作り直した。作り直したシナリオのうち往復 10 の前からある 15 本の、08f79b4 との差は、足した expect.starts（と YAML の別名）だけ
4. 戻った直後の訪問の expect.starts を足した三本と unit\_test\_defective\_self\_rollback で、持ち帰った記憶の期待を空の一覧に書き換えると、どれも開始時スナップショットの記憶の食い違いで落ちることを、スクラッチで確かめた（持ち帰った記憶を実際に確かめている）
5. plan\_tasks/incomplete: シナリオ plan\_tasks\_design\_incomplete\_rollback を走らせ、置き場から plan\_tasks の訪問 1 の状態文書を読み、印を除いて記述だけで読んだ（design\_incomplete に当たる。README）
6. オラクルの数値（123 項目、κ 0.603、ECE 0.275、答え無し 6、一致率 0.748）を、フィクスチャを戻した後に独立に計算し直して確かめた
7. defective（implement の ok の後）の状態文書を、往復 10 の前の記述だけで読んだ。goal は指標で外れ、impl\_defect は落ちるテストの期待が REQ-2 に反し、記憶 failing\_tests と「## 失敗」も空なので当たらず、tests\_insufficient（要件に反する期待を持つテストが記憶 coverage\_gaps と「## 未網羅」に列挙）に当たる。エージェントが読んだもので、人手のラベルは材料（unit\_test の 3 項目）で受け取る
8. 人がラベルを付けた後を試した: 印どおりの試しのラベル（ゲートは goal）を human-labeling.md の「ラベル:」に理由つきで埋め、`labels` で docs/human-labels.jsonl を作り（30 件）、`compare` で κ 1.000、食い違い 0 件。この状態で test\_labeling.py が通ることを確かめ（最初は、空の「ラベル:」を前提にした二つのテストが落ちたので、`write` が作る形を使うように直した）、材料を元に戻してラベルのファイルを消した
9. 例のテストは 197 件すべて通る。ruff check、ruff format、mypy strict も例の中で通る
10. check.sh が通る（ruff check、ruff format、mypy strict、pytest 660 件で 139.3 秒、全体で約 2 分 20 秒）

手引きと公開 API の文書だけでは判断できなかったこととして、変えた所に絞ってラベルを付け直す時にコーパスのどの項目を人に渡すか（N16）を adopting-gaps.md に書いた。

## 往復 12（2026-10-22）

往復 11 で上げた N16 を受けて、フレームワークの側が手引き第15.1節に、変えた所に絞ってラベルを付け直す時の目安（対象、訪問、まとめ方）と、人に渡す形から `item.source` を除くことを書き足した（changelog.md の「未公開」の最後の項目）。利用者として、書き足しで N16 を判断できるかを確かめ、この例の人に渡す材料（docs/human-labeling.md）の選び方を目安に合わせた。記述（workflow.yaml）、分布テストの分布（markov、divergent）、設計値、基準、種は変えていない。人のラベルはまだ無かった（docs/human-labels.jsonl が無く、「ラベル:」はすべて空）ので、材料の作り直しで失われるものは無い。

| やること | 対応 |
| --- | --- |
| N16 を判断できるか | できる（解消。adopting-gaps.md の「解消済み（往復 12）」）。往復 11 で決められなかった三点（「証拠に使う」の範囲、訪問 2 以降を省いてよいか、同じ組をまとめてよいか）は、それぞれ対象、訪問、まとめ方の目安で決まり、source のことは第15.1節の 2 で決まる |
| 材料の選び方が目安と合うか | 二か所合わなかったので直した（記述は変えず、人に渡す材料の選び方だけ）。対象: plan\_tasks と architecture のゲートの記述は、変えた requirements.md の REQ-3 と design.md の「## 対応」を根拠にするのに、渡していなかった。訪問: すべて訪問 1 だけで、持ち帰った記憶を受け取る対象の訪問 2 以降を渡していなかった。まとめ方（組ごとに一つ、短い状態文書）と source（選択を除き、人には human-labeling.md だけを渡す）は合っていた |
| 新しい不足 | N17（三つの目安の組み合わせ方と範囲。まとめ方の組に訪問が入っていない、訪問の目安が memory\_in の無い対象に及ぶか、対象の目安が成果物の全体か変えた所か） |

選び方（software\_factory/labeling.py の docstring と EVIDENCE、AGAIN の注記、README の「記述と代表の整合」、human-labeling.md の「選んだ項目」に記録した）:

- 対象: 選択肢の記述（ゲートはフェーズの goal）が、変えた代表の変えた所を判断の根拠にする対象。intake、analyze、discovery のゲート、design、plan\_tasks（足した）、architecture のゲート（足した）、unit\_test（defective だけ）、acceptance。渡さない対象と理由（implement、unit\_test と construction のゲートの requirements.md、review、release、assurance と delivery のゲート）は README に書いた
- 訪問: 訪問 1 を渡す。持ち帰った記憶を受け取るステージ（memory\_in のある intake、analyze、design、plan\_tasks、unit\_test）と、そういうステージを持つフェーズのゲート（discovery、architecture）では、訪問 2 以降も見る。対象の一覧（AGAIN）は workflow.yaml の memory\_in から決め、テストで確かめる。acceptance は訪問 1 だけ
- まとめ方: (対象, 訪問の区分, 印, 上流の違い) ごとに一つ。訪問 2 以降では、見出しのほかは訪問 1 の項目と同じ状態文書を除き、持ち帰った問いの回答を含むものを先に、その中で短いもの。この例の偽の本体は入り直しても同じ代表を写すので、訪問 2 以降で訪問 1 と違う状態文書になるのは intake、analyze、discovery のゲート（持ち帰った問いとペルソナの回答が intake.md に入る）だけ

試しの実行（tests/stochastic.yaml の labeling、software\_factory/labeling.py の TRIAL\_RUNS）:

- 分布: plan\_tasks の訪問 1 に unknown 0.1 を置き、訪問 2 以降を見る対象の訪問 2 以降に markov で出るクラスを置いた（intake の unknown 0.25、analyze の needs\_unclear 0.3 と unknown 0.2、design の requirements\_gap 0.25 と unknown 0.15、plan\_tasks の unknown 0.4）。unknown では運用者が中止するので、acceptance まで届く実行を保つため、訪問 1 の unknown を下げた（intake、analyze、design とも 0.15 → 0.1）。design、plan\_tasks、architecture のゲートの訪問 2 以降の項目は材料に入らないが、どのクラスでも訪問 1 と同じ状態文書になることをこの分布で確かめる
- 回数: 120 → 240。種は 90000 のまま。規則を決めた後に、メモリの上で labeling を差し替えて候補の分布を試した（スクラッチ）。種 90000 では 120 回と 160 回で acceptance の (unknown, terse\_engineer) が出ず、200 回で、design、plan\_tasks、architecture の訪問 2 以降を含む 51 の組がすべて出た。分布の余裕を見るために種 91000〜95000 でも試し、200 回では一つの種で一つの組が欠け、240 回では六つの種のすべてで全部出たので 240 回にした（種は選び直していない）。約 5 秒
- コーパス: `build_corpus(..., unique_states=True)` で 203 項目（ステージ 159、ゲート 44）。181 項目が変えた代表を含む。対象と訪問で絞ると 108 項目（訪問 1 が 53、訪問 2 以降が 55。訪問 2 以降のうち 21 項目は、見出しのほかは訪問 1 と同じ）

変わった数値:

- 人がラベルを付ける材料: 30 → 45 項目。訪問 1 が 33（intake 2、analyze 7、discovery のゲート 3、design 3、plan\_tasks 2、architecture のゲート 1、unit\_test 3、acceptance 12）、訪問 2 以降が 12（intake 2、analyze 7、discovery のゲート 3）。ステージ 38、ゲート 7。往復 11 の 30 項目の組はすべて残る。項目の id は、13 項目が往復 11 と同じで、ほかは試しの実行が変わったので変わった
- 例のテスト: 197 → 199 件（tests/test\_labeling.py に、訪問 2 以降を見る対象が workflow.yaml の memory\_in から決まること、design、plan\_tasks、architecture のゲートの訪問 2 以降が訪問 1 と同じ状態文書で、intake.md を読む対象の各組に持ち帰った問いの回答を含む訪問 2 以降があることの 2 件を足し、組と数の期待を 45 に直した）
- 分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較、オラクル、トリアージ: 変わらない（labeling の分布は使わない）

検証:

1. 056374f の adopting.md と changelog.md の差分を読み、N16 の三点と source のことが、それぞれどの文で決まるかを確かめた
2. 往復 11 の選び方を目安に当てはめた。試しのコーパス（往復 11 の 120 回）を対象、訪問の区分、印、上流の違い、含む変えた代表で数え、記述と突き合わせて、対象の抜け（plan\_tasks、architecture のゲート）と訪問 2 以降の抜けを見つけた（スクラッチ）
3. 訪問の区分を組に入れずに短いものを選ぶと、訪問 2 以降の項目は訪問 1 の項目に代わり、訪問 2 以降の中で短いものを選ぶと、design、plan\_tasks、architecture のゲートと、requirement\_gaps で入り直した analyze は、見出しのほかは訪問 1 と同じ状態文書になることを確かめた（N17 の (a)）
4. 材料を作り直した（`python -m software_factory.labeling write`）。human-labeling.md に印が無く、コーパスの source が run と seq だけであることを確かめた。訪問 2 の analyze の項目を読み、持ち帰った二つの問いと vague\_founder の回答（そのうち考える、まだ決めていない）が intake.md に入っていることを確かめた
5. 例のテスト 199 件がすべて通る。check.sh は、最初に ruff の SIM300（定数を左に置いた比較）で 2 件落ちたので直し、通る（ruff check、ruff format、mypy strict、pytest 662 件で 147.6 秒、全体で約 2 分 28 秒）

変えたファイル: software\_factory/labeling.py、tests/stochastic.yaml、tests/test\_labeling.py、docs/human-labeling.md、docs/human-labeling.corpus.jsonl、README.md、tests/README.md、docs/adopting-gaps.md、docs/progress.md。

## 往復 13（2026-10-22）

往復 12 で上げた N17 を受けて、フレームワークの側が手引き第15.1節の三つの目安（対象、訪問、まとめ方）の文を改めた（changelog.md の「未公開」の第15.1節の項目）。利用者として、改めた文で N17 の (a)〜(c) を判断できるかを確かめ、この例の人に渡す材料（docs/human-labeling.md）の選び方を改めた目安に合わせた。記述（workflow.yaml）、分布テストの分布（markov、divergent）、設計値、基準、種は変えていない。人のラベルはまだ無かった（docs/human-labels.jsonl が無く、「ラベル:」は 45 項目すべて空）ので、材料の作り直しで失われるものは無い。

| やること | 対応 |
| --- | --- |
| N17 を判断できるか | できる（解消。adopting-gaps.md の「解消済み（往復 13）」）。(a) まとめ方の組に訪問の区分が入り、訪問 2 以降の見出しのほかは訪問 1 と同じ状態文書を除くことが書かれた。(b) 訪問 2 以降を渡すのは memory\_in を持つステージとそのフェーズのゲートだけと書かれた。(c) 対象は変えた所（成果物の全体ではない）で見ると書かれた |
| 材料の選び方が目安と合うか | 対象の一か所が合っていなかったので直した: review（design\_flaw と changes\_requested の境界は design.md の構成かインターフェースの変更を要するかで、「## 対応」の REQ-3 に足した句（コードを文字列で受け取る、画面は repo/ の外）はインターフェースと境界を述べるので、判断の根拠にしうる）を足した。往復 12 の外した理由（review は「## 対応」に触れない）は節で分けたもので、記述は節を名指さず、design\_flaw の代表の指摘も「## 対応」の内容を根拠にする。ほかに、目安に無い規則（訪問 2 以降は持ち帰った問いの回答を含むものを先に選ぶ。往復 12 の N17 (a) の回避）を外し、目安の字のとおり組ごとに短いものにした（選ぶ項目は変わらない）。README と labeling.py の、改める前の手引きの文の引用と、手引きに無い条件（記述が持ち帰った記憶の扱いを書く）を、改めた文に合わせた。記述は変えていない |
| 新しい不足 | 無い。改めた文の中で読み方を選んだ所（変えた所の区切りを REQ-3 の句にした、review の上流の違いを無しとした、「訪問 1 の項目と同じ」をコーパスの訪問 1 の項目と比べた）は、手引きの「選んだ規則を記録する」のとおり README と labeling.py に記録した。最後のものは、どちらに読んでもこの例では同じ項目になる |

選び方（software\_factory/labeling.py の docstring と EVIDENCE、AGAIN の注記、README の「記述と代表の整合」、human-labeling.md の「選んだ項目」に記録した）:

- 対象: 記述（ステージの goal と end\_state、フェーズの goal）が、変えた所を判断の根拠にしうる対象。intake、analyze、discovery のゲート、design、plan\_tasks、architecture のゲート、unit\_test（defective だけ）、acceptance、review（足した。design.md の変えた句）。渡さない対象は implement、unit\_test と construction のゲートの requirements.md、release、assurance と delivery のゲートで、理由は README に書いた。unit\_test の impl\_defect と tests\_insufficient は「要件の記述」「要件に反する期待」に触れるので「しうる」で確かめ直した（変えたのは REQ-3 の誰がどこで入力するかの句で、テストの期待はそれを確かめも否定もできないので、渡さないまま）
- 訪問: 訪問 1 を渡す。訪問 2 以降も渡すのは memory\_in を持つステージ（intake、analyze、design、plan\_tasks、unit\_test）と、そのステージを含むフェーズのゲート（discovery、architecture）だけ（往復 12 と同じ）。acceptance と review は訪問 1 だけ
- まとめ方: (対象, 訪問の区分, 印, 上流の違い) ごとに一つ、状態文書の短いもの。訪問 2 以降の、見出しのほかは訪問 1 の項目と同じ状態文書は除く。上流の違いは、intake.md を読む対象ではペルソナ、unit\_test では goal の実装の変種、review を含むほかの対象には無い

試しの実行（tests/stochastic.yaml の labeling）:

- 分布: review の訪問 1 を ok 1.0 から ok 0.4、changes、design\_flaw、unknown 0.2 ずつにした（review は acceptance の訪問 1 の後なので、acceptance に届く実行は減らない）。ほかは往復 12 のまま
- 回数と種: 240 回、種 90000 のまま。規則を決めた後に、メモリの上で labeling を差し替えて試した（スクラッチ）。240 回では種 90000〜95000 の六つすべてで 49 の組が出た。200 回では一つの種（91000）で acceptance の (requirement\_unmet, terse\_engineer) が欠けた（往復 12 と同じ余裕）。約 5 秒
- コーパス: `build_corpus(..., unique_states=True)` で 242 項目（ステージ 187、ゲート 55）。220 項目が変えた代表を含む。対象と訪問で絞ると 122 項目（訪問 1 が 65、訪問 2 以降が 57。訪問 2 以降のうち 23 項目は、見出しのほかは訪問 1 と同じ）

変わった数値:

- 人がラベルを付ける材料: 45 → 49 項目。訪問 1 が 37（intake 2、analyze 7、discovery のゲート 3、design 3、plan\_tasks 2、architecture のゲート 1、unit\_test 3、acceptance 12、review 4）、訪問 2 以降が 12（intake 2、analyze 7、discovery のゲート 3）。ステージ 42、ゲート 7。往復 12 の 45 項目の状態文書はすべて残る。項目の id は、33 項目が往復 12 と同じで、12 項目は試しの実行が変わったので変わった
- 例のテスト: 199 件のまま（tests/test\_labeling.py の組の期待に review の 4 を足し、数を 49 に、訪問 2 以降を渡さない対象に review を足した）
- 分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較、オラクル、トリアージ: 変わらない（labeling の分布は使わない）

検証:

1. 3b28deb の adopting.md と changelog.md の差分を読み、N17 の (a)〜(c) が、それぞれどの文で決まるかを確かめた
2. 往復 12 の選び方を改めた文に当てはめた。対象は、各ステージの goal と end\_state、各フェーズの goal を、変えた所（REQ-3 の句、外した「## 利用者」の節、design.md の「## 対応」の REQ-3 の句、verification.md の「## 依頼との食い違い」、vague\_founder の回答、defective）と突き合わせ、review の抜けを見つけた。review の代表 4 つ（ok、changes、design\_flaw、unknown）の review.json も読んだ（design\_flaw の指摘は「## 対応」の REQ-1 と REQ-2 の分岐を、changes の指摘は REQ-3 の ValueError が呼び出し側に届くことを述べる）
3. 往復 12 の試しのコーパス（203 項目）で、「回答を含むものを先に」を外して目安の字のとおりに選ぶと、往復 12 の 45 項目と同じになることを確かめた（訪問 1 と同じものを除いた後の訪問 2 以降の候補 34 項目は、どれも持ち帰った問いの回答を含む）。往復 13 の試しのコーパスでも同じ（候補 34 項目がすべて回答を含む）。「訪問 1 の項目と同じ」を、選んだ訪問 1 の項目と比べる読み方にしても、除く項目は変わらない（どちらのコーパスでも差は 0 項目）
4. 試しの実行で review の訪問 1 の四つのクラスが出ることを確かめ、材料を作り直した（`python -m software_factory.labeling write`）。往復 12 の 45 項目の状態文書がすべて残り、review の 4 項目が足されたことを、コミット済みのコーパスとの比較で確かめた。review の項目を読み、design.md の「## 対応」の REQ-3 に変えた句があり、印が除かれていること、選択肢が review の goal と end\_state の記述であること（指標 blocking\_findings が落ちる changes\_requested と design\_flaw の代表の 2 項目では goal が無い）を確かめた
5. 例のテスト 199 件がすべて通る。check.sh が通る（ruff check、ruff format、mypy strict、pytest 662 件で 144.6 秒、全体で約 2 分 25 秒）

変えたファイル: software\_factory/labeling.py、tests/stochastic.yaml、tests/test\_labeling.py、docs/human-labeling.md、docs/human-labeling.corpus.jsonl、README.md、docs/adopting-gaps.md、docs/progress.md。

## 残っていること

- markov.yaml の実行のゲートはいつも goal（前の数値を保つため）。ゲートの分布は markov\_gated.yaml の実行の集まりで確かめる
- release 以外で carry によって分布が変わる本体は、マルコフ合成と合わないので例には置いていない（gaps D2）。entry\_dependence がそれを見分けることはスクラッチで確かめた（gaps N9）
- 分類器の検証の閾値は、偽の分類器なので決めていない（第15節の「人間が閾値を決める」は実際の分類器の時の手順）
- 記述と代表の整合の人手のラベル: docs/human-labeling.md の 49 項目に人がラベルを付ける（まだ）。受け取ったら `python -m software_factory.labeling labels --labeler <名前>` と `compare` で印と比べ、食い違いがあれば代表か記述を直す（記述を直すのは人間の承認の後）。これまでの試しのラベル（エージェント）は往復 8 の 56 項目と往復 10 の 32 項目で、どちらも κ 1.0
- plan\_tasks の design\_incomplete は、人間の回答で、記述を変えず確率的な代表を置かない今の形のまま残すと決まった（E2E の注入とシナリオで踏む）
- 不足と不備を分けて数えることは、記述を変えずに coverage\_gaps の項目の書き方で区別できる（第13節。任意）。今はしていない
