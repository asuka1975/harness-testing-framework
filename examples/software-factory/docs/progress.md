# software-factory の作業ログ

harness-testing-framework（v0.1.0）の利用者として、adopting.md だけを手引きに、ソフトウェア開発のワークフロー型ハーネスを作る。

- 読取の制限: docs/adopting.md、docs/api.md、docs/api-reference.md、examples/toy-minimal/、公開 API の文書（api.md が挙げるもの）だけ。本体の実装（src/、tests/、scripts/、pyproject.toml、conftest.py の中身）、docs/plan.md、docs/progress.md、docs/decisions.md、reports/ は読まない。本体は直さない
- 分からなかったこと、足りなかったこと、回避したくなったことは docs/adopting-gaps.md に書く
- コミットはしていない（依頼に無いため）

## 状態（2026-10-22）

往復 10（人間のレビューの回答と、完了判定の二回目の指摘への対応）まで完了。`scripts/check.sh` が通る（ruff check、ruff format、mypy strict、pytest 649 件で 142.6 秒、全体で約 2 分 23 秒）。この例のテストは 188 件。変更は examples/software-factory/ の中だけ。adopting-gaps.md の未解消は N14、N15（往復 10 で見つけた）。

最初の版（下の「経過」）の後、フレームワークの側が adopting-gaps.md の 30 項目を受けて直したので、往復 1 で各項目を確かめ、要らなくなった回避策を外した（下の「往復 1」）。往復 1 で見つけた N1〜N7 も直ったので往復 2 で、往復 2 で見つけた N8、N9 も直ったので往復 3 で、往復 3 で見つけた N10 も直ったので往復 4 で、往復 4 で見つけた N11 も直ったので往復 5 で確かめた（下の「往復 2」〜「往復 5」）。往復 6 で、人間のレビューの前の検証役の指摘（docs/review-findings.md）に対応した（下の「往復 6」）。往復 8 で完了判定の指摘（E）に、往復 10 で人間のレビューの回答と完了判定の二回目の指摘（F）に対応した。今の未解消は adopting-gaps.md の先頭にある。

| 求められたこと | どこで満たしたか |
| --- | --- |
| 4 フェーズ以上、8 ステージ以上 | workflow.yaml（5 フェーズ、9 ステージ）。tests/test\_definition.py |
| フェーズ境界越えのロールバック、carry、ユーザー回答待ち | 越境の辺 6 本（design → analyze、implement → plan\_tasks、acceptance → analyze と implement、review → design と implement）。全辺に carry。intake が awaits\_user |
| end\_state は観測できる条件、戻り先つき、unknown を含む | 全ステージに unknown、unknown 以外の 13 クラスにそれぞれ戻り先（往復 10 で unit\_test の tests\_defective を足した）。carry する記憶を記述が証拠として名指す（テストで確かめる） |
| 偽のステージ本体（LLM なし） | 決定論的: シナリオの台本でフィクスチャを写す。確率的: tests/stochastic.yaml の設計値で、種だけから変種を選ぶ |
| carry を受けた再進入で分布が変わるもの | release（missing\_notes を受けると goal 0.75 → 0.97）。訪問 2 以降と carry の有無が一致することを全実行で確かめる |
| クラス内で下流の分布が分かれるもの | divergent の implement の goal（ok は REQ-1 の切り捨てを誤り、ok\_fixed は正しい）。unit\_test の defect のテストは実在の pytest で前者だけ落ちる |
| 実装と単体テストに本物の指標 | build\_passes、tests\_pass、line\_coverage、lint\_errors、out\_of\_scope\_changes。フィクスチャの repo/ に compileall、pytest、coverage、ruff を実際にかける |
| 要求の取り込みにペルソナ 3 つ以上 | software\_factory/personas.py（precise\_pm、vague\_founder、terse\_engineer）。確率的な実行では種からペルソナを選ぶ。決定論テストと E2E のカバレッジにも束縛する |
| 全ランナー | 下の「結果」 |

## 結果

- 整合性検査: 誤り 0、警告 0
- 契約適合テスト: パッケージに同梱した 25 シナリオ（`conformance_scenarios()`）すべてが参照ランタイムで期待どおり（tests/test\_conformance.py。参照ランタイムを使うので必須ではなく、版の確認として残す）。ハーネスの本体は、400 回の実行で契約違反、本体の例外、範囲外のファイルの警告が一度も無い
- 遷移の決定論テスト: 17 シナリオ。遷移の六種、escalate の四択、越境の 7 通り（定義の上の六本の辺のすべてと、運用者による越境）、定義の上のロールバックの辺 13 本のすべて（自分自身への辺と plan\_tasks → design を含む）を通す。実在の指標の値で goal が選択肢から外れることを expect.options で確かめる。記録再生で同一のスナップショットの列。inputs と開始時スナップショットのファイルはフィクスチャを `{from: パス}` で参照する。三つのペルソナを台本の user の代わりに束縛しても期待どおり（持ち帰った問いを尋ねる、最初の質問で保留して再開する）。偽の本体は訪問のたびに memory\_out のすべての項目を書き、持ち帰った記憶は、問いが解けた後の訪問が空の一覧を書くので最後の記憶に残らない（expect.memory で確かめる）
- 分布テスト: markov.yaml の 12 基準がすべて通り（400 回、種 20000）、markov\_shifted.yaml の 14 基準はすべて落ちる。release の訪問 2 以降の goal は 0.969（62/64）で、基準 [0.88, 1.0]（二項分布の裾から決めた）に入り、「carry で変わらない」とした基準（0.65〜0.85）は落ちる。assurance のゲートを RandomGateClassifier で揺らす markov\_gated.yaml の 4 基準もすべて通る（400 回、種 50000。ゲートの訪問 1 の changes\_requested 0.209（45/215）、訪問 2 以降 0.156（17/109）、完了 0.625、implement の訪問の回数の平均 2.002。往復 8 の設計値の変更の後の値）。markov\_gated\_shifted.yaml の 3 基準はすべて落ちる。各基準が設計値の両側に標準誤差の 3 倍以上 5 倍以下あることを、synthesize の evaluations（厳密な E[n]）と visits\_variance から確かめ、外れる側の期待件数が 10 に届かない基準は二項分布の裾の確率（0.1% 以下）で確かめる。分布テストに使う二つの実行の集まりに、指標の測定の失敗と、印が goal なのに goal が選択肢から外れた評価が一度も無い
- 独立性検証: divergent は stage:implement=goal（訪問 1 → 1）で violated（p = 0.0005、代表 136 と 126）。markov は、全状態を判定できた検定の数で alpha を割って violated が無く、同じ状態は p = 0.23（「p 値が 0.001 以上」で確かめる。往復 10）。intake の goal のペルソナごとの三つの代表は、markov で p = 0.44、divergent で p = 0.78。ゲートを揺らす実行にも violated が無い
- E2E: カバレッジ計画が全 (ステージ, クラス) の 31 を踏む（往復 10 で 30 から。tests\_defective は誘発で踏む。誘発と注入の両方。intake の質問にはペルソナが答える）。推定したモデルと設計値のモデルの予測が、どちらもゲートの評価の結果を含むすべての量で実測と一致（k = 4）。ゲートの分布を足した設計値のモデルの予測も、ゲートを揺らした実行の 46 の量（assurance のゲートの goal と changes\_requested を含む。往復 8 で plan\_tasks の design\_incomplete を設計値から外して 47 から減った）と一致する。入り方が二つ以上あるステージの訪問 2 以降の結果は、markov とゲートを揺らす実行のどちらでも入り方によらない（entry\_dependence で、判定できた検定の数で alpha を割って violated 無し。implement は入り方 5 通りで p = 0.56 と 0.43）
- オラクル: `build_corpus(..., unique_states=True)` でステージの 123 項目（往復 8 で plan\_tasks の design\_incomplete を外したので、往復 7 までの 127 から変わった。往復 10 では変わらない）。印を読む分類器は κ 1、ECE 0.1。既知の混同行列の分類器は κ 0.603、ECE 0.275、答え無し 6（選択肢に無いクラス）で、独立に計算した値と一致。揺れる分類器の再実行の一致率は 0.748（1 − ⌈123/4⌉/123 に一致）
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

## 残っていること

- markov.yaml の実行のゲートはいつも goal（前の数値を保つため）。ゲートの分布は markov\_gated.yaml の実行の集まりで確かめる
- release 以外で carry によって分布が変わる本体は、マルコフ合成と合わないので例には置いていない（gaps D2）。entry\_dependence がそれを見分けることはスクラッチで確かめた（gaps N9）
- 分類器の検証の閾値は、偽の分類器なので決めていない（第15節の「人間が閾値を決める」は実際の分類器の時の手順）
- 記述と代表の整合は、試しのラベル（エージェント）で κ 1.0（往復 8 は 56 項目、往復 10 は変えた所の 32 項目）。人手のラベルではないので、第15.1節の手順は人間がする（人間の回答でもまだ）
- 往復 10 で足した tests\_defective と、絞った tests\_insufficient の記述と境界は、人間がもう一度確かめる（README の「人間のレビューで確かめてほしいこと」）
- plan\_tasks の design\_incomplete は、人間の回答で、記述を変えず確率的な代表を置かない今の形のまま残すと決まった（E2E の注入とシナリオで踏む）
- tests\_defective は確率的な実行に出ない（分布に置いていない）。出すかどうかは README に提案として書いた
