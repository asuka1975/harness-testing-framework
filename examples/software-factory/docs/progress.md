# software-factory の作業ログ

harness-testing-framework（v0.1.0）の利用者として、adopting.md だけを手引きに、ソフトウェア開発のワークフロー型ハーネスを作る。

- 読取の制限: docs/adopting.md、docs/api.md、docs/api-reference.md、examples/toy-minimal/、公開 API の文書（api.md が挙げるもの）だけ。本体の実装（src/、tests/、scripts/、pyproject.toml、conftest.py の中身）、docs/plan.md、docs/progress.md、docs/decisions.md、reports/ は読まない。本体は直さない
- 分からなかったこと、足りなかったこと、回避したくなったことは docs/adopting-gaps.md に書く
- コミットはしていない（依頼に無いため）

## 状態（2026-10-23）

往復 16（人に渡す材料の確かめ直し（docs/review-findings.md の I）への対応。材料を対象ごとのファイルに分け、読み方の方針の二つを外した）まで完了。`scripts/check.sh` が通る（ruff check、ruff format、mypy strict、pytest 689 件で 146.6 秒、全体で約 2 分 27 秒）。この例のテストは 225 件。変更は examples/software-factory/ の中だけ。adopting-gaps.md の未解消は N19（往復 16 で見つけた。人に渡す材料を対象の順に分ける時のゲートの置き場が、手引きから一つに決まらない。この例は最終ステージの直後を選び、理由を記録した）。

最初の版（下の「経過」）の後、フレームワークの側が adopting-gaps.md の 30 項目を受けて直したので、往復 1 で各項目を確かめ、要らなくなった回避策を外した（下の「往復 1」）。往復 1 で見つけた N1〜N7 も直ったので往復 2 で、往復 2 で見つけた N8、N9 も直ったので往復 3 で、往復 3 で見つけた N10 も直ったので往復 4 で、往復 4 で見つけた N11 も直ったので往復 5 で確かめた（下の「往復 2」〜「往復 5」）。往復 6 で、人間のレビューの前の検証役の指摘（docs/review-findings.md）に対応した（下の「往復 6」）。往復 8 で完了判定の指摘（E）に、往復 10 で人間のレビューの回答と完了判定の二回目の指摘（F）に、往復 11 で往復 10 の後の人間の決定（G。tests\_defective の分割の取り消しと、人が付けるラベルの材料）に対応した。往復 12 で、往復 11 で見つけた N16 を受けた手引きの書き足しを確かめ、人に渡す材料の選び方をそれに合わせた（下の「往復 12」）。往復 13 で、往復 12 で見つけた N17 を受けて改められた手引きの目安を確かめ、人に渡す材料の選び方をそれに合わせた（下の「往復 13」）。往復 14 で、往復 10〜13 の差分の確かめ（review-findings.md の H）に対応し、人に渡す材料から印、選んだ規則、組ごとの数、項目の id が漏れないようにし、分量を減らし、対象と上流の違いを目安に揃えた（下の「往復 14」）。往復 15 で、往復 14 で見つけた N18 を受けた `ScenarioResult.store` と文書の書き足しを確かめ、人に渡す材料を作る時にシナリオの状態文書を読む回避を、公開の手段（`run_scenario` の結果の `store`）に置き換えた（下の「往復 15」）。往復 16 で、人に渡す材料の確かめ直し（review-findings.md の I）に対応し、人間の決定で読み方の方針の二つを外し、材料を対象の順のファイルに分け、比べる相手の答えと、括弧の外の二つ以上の id、置き書き、まとめた実装の変種を直した（下の「往復 16」）。今の未解消は adopting-gaps.md の先頭にある（往復 16 の後は N19）。

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
- 記述と代表の整合（第15.1節）: 人がラベルを付ける材料 docs/human-labeling/（66 項目。訪問 1 が 54（intake 2、analyze 7、discovery のゲート 3、design 3、plan\_tasks 3、architecture のゲート 1、implement 4、unit\_test 3、acceptance 24、review 4）、訪問 2 以降が 12（intake 2、analyze 7、discovery のゲート 3）。ステージ 59、ゲート 7）を、試しの実行（tests/stochastic.yaml の labeling、480 回、種 90000）とシナリオ plan\_tasks\_design\_incomplete\_rollback から、手引き第15.1節の変えた所に絞る時の目安（対象、訪問、まとめ方）で選ぶ。材料は、読み方の 00-guide.md と、対象ごとの 10 のファイル（ワークフローの順で、ゲートはそのフェーズの最終ステージの直後。01-intake.md 4 項目、02-analyze.md 14、03-discovery-gate.md 6、04-design.md 3、05-plan\_tasks.md 3、06-architecture-gate.md 1、07-implement.md 4、08-unit\_test.md 3、09-acceptance.md 24、10-review.md 4）に分け、番号の順に付け、前のファイルを付け終えるまで次を開かず、付け終えたラベルを変えず、見比べないよう頼む（往復 16）。人に渡す形は、印、比べる相手の答え、選んだ規則、組ごとの数、項目の id を、地の文、並び、見せ方のどこにも含まない（項目は全ファイルを通した通し番号。材料の文が印、id、出どころ、渡す順によらないこと、前のファイルが後の対象の成果物を含まないことをテストで確かめる）。読み方は事実と、迷ったら unknown と理由を添える頼みだけ（人間の決定で、記述の読み方を決める二つの方針を外した）。156,390 文字（往復 13）から 100,276 文字（往復 14）、104,151 文字（往復 16）。人のラベルはまだ無い。受け取ったら docs/human-labeling/ の下に置き、examples/software-factory/ で `uv run python -m software_factory.labeling labels --labeler <名前>` と `uv run python -m software_factory.labeling compare` で印と比べる（往復 11 で作り、往復 12 で選び方を目安に合わせ、往復 13 で review を足し、往復 14 で H に、往復 16 で I に対応した）
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
| 人がラベルを付ける材料（往復 11。往復 12 で分布を変え、120 回から増やした。往復 13 で review の訪問 1 の分布を変えた。往復 14 で analyze、intake、implement の分布を変え、240 回から増やした。docs/human-labeling.md、tests/test\_labeling.py） | labeling（tests/stochastic.yaml） | 480 | 90000 |

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

## 往復 14（2026-10-23）

第三者の検証役が往復 10〜13 の差分を確かめ、人に渡す材料（docs/human-labeling.md）に中 1、低 6 の指摘を docs/review-findings.md の H に書いた。フレームワークの側は、手引き第15.1節の 2 に「選んだ規則と項目の id も人に渡す形に書かず、項目は通し番号で渡す」を書き足し、1 の「E2E の注入だけが写す代表」を「誘発の台本だけが写す代表」に直した（changelog.md の「未公開」の第15.1節の項目）。利用者として H-M1、H-L1〜H-L6 を直した（「記録だけ」の項目は直していない）。記述（workflow.yaml）、分布テストの分布（markov、divergent）、設計値、基準、種は変えていない。代表は review の changes\_requested の一つだけ直した（H-L6）。人のラベルはまだ無かった（docs/human-labels.jsonl が無く、「ラベル:」はすべて空）ので、材料の作り直しで失われるものは無い。

完了条件を先にテストにした。tests/test\_labeling.py を書き直し、直す前のコード（定数 CARRIED だけを足したもの）で 23 件のうち 19 件が落ちることを確かめてから直した（通っていた 4 件は、ラベルのファイルが無い時の報告、受け取ったラベルの確かめ、直す前の材料の作り直しの一致、H-L6 の requirement\_unmet の前提の確かめ）。

| 指摘 | 対応 |
| --- | --- |
| H-M1 材料が組ごとのクラスの構成を明かす | 直した。材料から選んだ規則（「選んだ項目」の節）と、対象と訪問の区分ごとの数を除き、「項目の選び方は README にある。ラベルを付け終えるまで README の「記述と代表の整合」を読まない」とだけ書いた。README のほかの節、docs/ のほかの文書、tests/ と software\_factory/ の下にも代表のクラスが書いてあるので、ラベルを付け終えるまで材料のほかは開かないことも書いた（比べる時のコーパスとフィクスチャには印が残る）。README のその節の頭にも同じ注意を書いた。選んだ規則と組ごとの数（クラスの名前の表）は README にだけ置く。材料の文に、規則を述べる語（まとめ方、上流の違い、ペルソナなど）と項目の数が無いことをテストで確かめる |
| H-L1 項目の id から印が推せる | 直した。項目は通し番号（項目 1〜66）だけで示し、id、実行の id、実行の種、seq、分類器の選択を書かない（テストで確かめる）。番号と id の対応はコーパスの並びと source の number に持ち、ラベルを読む処理は番号から id を引く。並びは対象ごと（ワークフローの順）で、対象の中は人に見せる文の SHA-256 の順、同じ実行の項目が続く所は同じ対象の中の別の項目と入れ替える。材料の文が、印のクラスを変えても、id を付け替えても（同じ実行かどうかは保つ）、出どころを変えても、渡す順を変えても同じになることをテストで確かめる（並べ方から印も id も推せない） |
| H-L2 分量 | 直した（見せ方だけ。記述と状態文書の中身は変えない）。選択肢の記述は対象の節の頭に一度だけ示し、項目には選べる選択肢の id だけを示す。対象の項目の過半（二つ以上）で同じ区切りは節の頭に一度だけ示し、項目では見出しに「（共通）」を付けて分類器が見た順の位置に示す。指摘の案（全項目で同じ区切り）では、acceptance の 24 項目のうち一つだけ goal の実装の変種が違い、repo/src/shopcart/discount.py が 24 回並んだ（117,027 文字）ので、過半にした。印だけの行を落とし（H-L3）、区切りの間の空行を一つにした。共通の区切りを戻すと印を除いた状態文書に戻ることをテストで確かめる。156,390 文字（49 項目）→ 100,276 文字（66 項目）。66 項目のすべてに選択肢の記述と状態文書の全文を並べた形（231,447 文字）の 43% |
| H-L3 読み方 | 直した。冒頭に方針（分類器と同じ立場、字義どおり、中身の条件を書いていれば確かめる、括弧の中の列挙は記述が書いた範囲、迷ったら unknown と理由）と事実（指標の値は入らない、goal が無い時は goal に優先する文は働かない、「（なし）」は空の節、戻りの後の intake.md に持ち帰った問いと回答が入る、印を除いた跡に意味は無い、番号と並びに意味は無い）を書いた。印だけの行（印を除くと空か「#」だけになる行）は落とした。review.json の `"marker": ""` は一行の JSON の中なので残し、意味が無いと書いた |
| H-L4 対象の範囲 | 直した。(a) 上流の違いを、intake.md を読む対象では (ペルソナ, 持ち帰った問いの回答の有無) にした。acceptance は 12 → 24 項目。intake、analyze、discovery のゲートでは回答の有無が訪問の区分と一致するので、組は変わらない。試しのコーパスに出ない組は無い（README に書いた）。(b) implement を目安に当てはめて足した（review と同じ当てはめ: goal の「design.md の構成どおり」は節を名指さず、変えた句は parse\_code のインターフェースと、画面を repo/ に置かない構成を述べる）。4 項目（goal、task\_unclear、quality\_violation、unknown）。訪問 2 以降は、試しの実行でどのクラスも出るが、見出しのほかは訪問 1 と同じ（テストで確かめる）。construction のゲートは design.md を状態文書に含むが、フェーズの goal が design.md に触れないので渡さない（README に理由を書いた）。(c) plan\_tasks/incomplete を、シナリオで分類器が見る状態文書から項目にした（plan\_tasks は 2 → 3 項目）。`run_scenario` は置き場を返さないので、シナリオの台本の偽物でランタイムを組み立て、実行記録の要約がシナリオの期待と一致し、状態文書の SHA-256 が `run_scenario` の実行記録のものと同じことを確かめる（N18） |
| H-L5 ラベルを読む処理と手順 | 直した。全角のコロン（「ラベル：」）と ` で囲んだ id も読む。読めないラベル、選べる選択肢に無い id、「ラベル:」の行が無い項目は、項目の番号を添えた誤り（終了コード 2。ラベルのファイルを書かない）。「ラベル:」の後が空で次の行に文がある時は、番号を添えて警告し、空として数える（blank\_labels はその行も除くので、作り直したものとの比べは落ちない）。材料、README、labeling.py の docstring、compare の案内に、examples/software-factory/ で `uv run python -m software_factory.labeling …` と書いた |
| H-L6 注釈の言い過ぎと代表の前提 | 直した。(1) README と labeling.py の「ok\_fixed とは組まない」を、markov では組まないが、divergent と試しの実行 labeling では組み、その時は代表の文が ok\_fixed のコードと食い違う（手引き第12節）に直した。材料からはその組を外していること（試しのコーパスで ok\_fixed の後の acceptance の訪問 1 が 20 項目、うち requirement\_unmet が 6 項目）と、divergent の組は独立性検証のための本体として許すこと（divergent が確かめるのは implement の goal の代表ごとの下流の分布で、acceptance の代表の文の真偽は、代表の鍵にも次の状態にも関わらない。分布テストの基準、オラクル、トリアージ、材料には使わない）を README に記録した。代表の文が ok と ok\_b でだけ成り立つこと（小計 333 円に PCT10 で 299 円。ok\_fixed は 300 円）を、フィクスチャの discount.py を実行して確かめるテストを足した。(2) review の changes\_requested の代表の指摘を、前提が事実に合うものに直した（「test\_invalid\_codes\_are\_rejected は無効なコード（PCT0、PCT51、XYZ、OFF）を parse\_code に直接渡すだけで、Cart.total に無効なコードを渡した時に ValueError で拒むこと（REQ-3）を確かめていない。Cart.total で確かめるテストを足す」。path は repo/tests/test\_discount.py、修正を要する）。記憶 review\_findings（tests/stochastic.yaml）も同じ指摘にした。review に届く単体テストの代表（unit\_test の goal になる ok と defect\_passed）のどちらでも事実で、repo/tests/ の修正で解消することをテストで確かめる。前の指摘の「専用の例外にする」は、REQ-3 と design.md が決めた ValueError を変えるので、design\_flaw とも読めた |
| 新しい不足 | N18（シナリオで分類器が見る状態文書を読む手段と、`ScriptedClassifier` の引数の形が公開の文書に無い）を adopting-gaps.md に書いた |

人に渡す形（software\_factory/labeling.py の docstring と HEADER、README の「記述と代表の整合」に記録した）:

- 冒頭: 何の材料か、「ラベル:」の行だけを書くこと、選び方は README にありラベルを付け終えるまで README の「記述と代表の整合」とコーパスとフィクスチャを開かないこと、読み方（方針と事実）、見せ方、ラベルの書き方と付けた後のコマンド
- 対象の節（「## ステージ intake」など。ワークフローの順）: 選択肢の記述（一度だけ）、対象の項目の過半で同じ区切り（一度だけ）、項目（「### 項目 n」、対象と訪問、選べる選択肢の id、状態文書（共通の区切りは見出しだけ）、空の「ラベル:」）

試しの実行（tests/stochastic.yaml の labeling）:

- 分布: intake の again を ok 0.8、unknown 0.2 に、analyze の first を ok 0.4、unclear 0.5、unknown 0.1 に、again を ok 0.65、unclear 0.2、unknown 0.15 にした（acceptance に届く実行のうち、持ち帰った問いの回答を含むものを増やす）。implement の first と again に全変種を置いた（ok 0.27、ok\_b 0.27、ok\_fixed 0.16、lint、scope、broken 0.06 ずつ、unclear 0.07、unknown 0.05）。ほかは往復 13 のまま
- 回数と種: 480 回、種 90000。規則を決めた後に、メモリの上で分布を差し替えて試した（スクラッチ）。480 回では種 90000〜97000 の八つすべてで 66 の組が出た。300 回では八つのうち四つで、240 回では六つのうち五つで、acceptance の組が一つから三つ欠けた。種 90000 は前のまま（通るように選び直していない）。`write` は約 8 秒
- コーパス: `build_corpus(..., unique_states=True)` で 308 項目（ステージ 246、ゲート 62）に、シナリオの 1 項目を足して 309 項目。286 項目が変えた代表を含む。対象と訪問で絞ると 183 項目（訪問 1 が 87、訪問 2 以降が 96。訪問 2 以降のうち 58 項目は、見出しのほかは訪問 1 と同じ）

変わった数値:

- 人がラベルを付ける材料: 49 → 66 項目。訪問 1 が 54（intake 2、analyze 7、discovery のゲート 3、design 3、plan\_tasks 3、architecture のゲート 1、implement 4、unit\_test 3、acceptance 24、review 4）、訪問 2 以降が 12（intake 2、analyze 7、discovery のゲート 3）。ステージ 59、ゲート 7。往復 13 の 49 項目のうち 42 項目の状態文書が残る。残らない 7 項目のうち 6 項目（analyze 4、discovery のゲート 2。どれも訪問 2 以降）は、試しの実行が変わり、同じ組の別の訪問（2 と 3）の状態文書になった（見出しのほかは同じ）。1 項目は直した review の changes\_requested の代表
- 文字数: 156,390 文字（238,418 バイト）→ 100,276 文字（163,942 バイト）
- 例のテスト: 199 → 213 件（tests/test\_labeling.py が 9 → 23 件）
- 分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較、オラクル、トリアージ: 変わらない（labeling の分布は使わない。review の changes\_requested の代表の中身を変えたが、クラスは種だけで選ぶ）。markov の stage:implement=goal の訪問 1 → 1 は p = 0.23、intake の goal は markov で p = 0.44、divergent で p = 0.78、divergent の implement は p = 0.0005、入り方の検定の implement の訪問 2 以降は p = 0.56 のまま（スクラッチで計算し直した）

検証:

1. docs/review-findings.md の H と、85c7ed5 から今までの adopting.md と changelog.md の差分（第15.1節の 1 と 2、changelog.md の「未公開」の第15.1節の項目）を読んだ
2. 完了条件を tests/test\_labeling.py に先に書き、直す前のコードで 23 件のうち 19 件が落ちることを確かめた
3. labeling.py を直し、試しの分布をスクラッチで決め、examples/software-factory/ で `uv run python -m software_factory.labeling write` で材料を作り直した。材料を読み、各対象の節の頭の選択肢の記述と共通の区切り、項目の「（共通）」の位置、plan\_tasks のシナリオの項目（design/gap の design.md と組む）を確かめた
4. H-L6 の確かめのテストで、最初はフィクスチャの discount.py を import した。フィクスチャの下に \_\_pycache\_\_ ができ、偽の本体がそれも作業領域に写して implement の指標 out\_of\_scope\_changes が落ちた（シナリオの再現が運用者の台本切れで止まって気づいた）。\_\_pycache\_\_ を消し、テストは import せずにソースを実行する形にし、フィクスチャの下に \_\_pycache\_\_ が無いことも確かめるようにした
5. review の代表を変えた後に、独立性検証と入り方の検定の値（上）をスクラッチで計算し直し、変わらないことを確かめた
6. examples/software-factory/ で `uv run python -m software_factory.labeling compare` がラベルのファイルが無いことを報告して 1 で終わり、リポジトリの根では `No module named 'software_factory'` になることを確かめた
7. check.sh が通る（ruff check、ruff format、mypy strict、pytest 676 件で 145.9 秒、全体で約 2 分 27 秒）。最初の実行では ruff（RUF007、SIM300）と mypy（Optional の代入）で落ち、直した

変えたファイル: software\_factory/labeling.py、tests/test\_labeling.py、tests/stochastic.yaml、tests/fixtures/review/changes/review.json、tests/README.md、docs/human-labeling.md、docs/human-labeling.corpus.jsonl、README.md、docs/adopting-gaps.md、docs/progress.md。

## 往復 15（2026-10-23）

往復 14 で上げた N18 を受けて、フレームワークの側が `run_scenario` の結果（`ScenarioResult`）に `store`（実行が使った置き場）を足し、api-reference.md に `ScenarioResult` の属性の説明と `ScriptedBody`、`ScriptedClassifier` の引数の形を書き、手引き第15.1節の 1 にシナリオの状態文書の読み方を一文足した（changelog.md の「未公開」の `ScenarioResult.store` の項目。コミット 453fd31）。利用者として、それで N18 を判断できるかを確かめ、この例の回避を公開の手段に置き換えた。記述（workflow.yaml）、分布、設計値、基準、種、フィクスチャ、人に渡す材料（docs/human-labeling.md とそのコーパス）は変えていない。人のラベルはまだ無い（docs/human-labels.jsonl が無く、「ラベル:」はすべて空）。

| やること | 対応 |
| --- | --- |
| N18 を判断できるか | できる（解消。adopting-gaps.md の「解消済み（往復 15）」）。分類器が見た状態文書は、trace の evaluation の `classification.state` を `result.store.get` に渡して読める（中断して再開するシナリオでも）。`verify` に渡す store は、`result.store` のほかに無い（`verify(scenario, result, result.store)` が `problems` と同じく空）。`ScriptedClassifier` の stages と gates、`ScriptedBody` の visits の形は、往復 14 に試して知った形と同じ |
| 回避の置き換え | 置き換えた。software\_factory/labeling.py の scenario\_corpus は、シナリオを `run_scenario`（software\_factory/stages/deterministic.py の run）で実行し、`problems` が空であることを確かめ、`RunRecord(scenario.seed, result.status, result.trace)` を `build_corpus(RunSet([...]), result.store, ...)` にかける。シナリオの台本の偽物（`ScriptedBody`、`ScriptedClassifier`、`ScriptedOperator`、`ScriptedUser`）と自分の置き場でランタイムを組み立て直すこと、`record_run`、実行記録の要約をシナリオの期待と自分で比べることを外した。README の「記述と代表の整合」と labeling.py の docstring を合わせた |
| 材料の文 | 変わらない。置き換えた後のコードで試しの実行から作り直した human-labeling.md とコーパスは、コミットしたもの（往復 14 の回避で作った）とバイト単位で同じ。シナリオの項目の id（実行の id 46612a644073df0b）も同じ |
| 新しい不足 | 無い。シナリオの状態文書をコーパスの項目にするために trace を `RunRecord` にしたのは、api-reference.md の `RunRecord`、`ScenarioResult.trace`、`build_corpus` の説明から判断できた（この例の選んだ手順として、adopting-gaps.md、README、labeling.py に記録した）。api-reference.md の `ScenarioResult` の属性の説明に `problems` が無いこと（手引き第8節にある）と、signature で `store` が `resumes` の前に入ったことは、判断に困らないので小さなこととして adopting-gaps.md に書いた |

検証:

1. 453fd31 の adopting.md、api-reference.md、changelog.md の差分を読み、N18 の三つ（置き場とその場所、`verify` に渡す store、`ScriptedClassifier` と `ScriptedBody` の引数の形）が、それぞれどの文で決まるかを確かめた
2. スクラッチで、plan\_tasks\_design\_incomplete\_rollback（評価 16 件）と happy\_path\_user\_suspend（再開 1 回、評価 14 件）を `run_scenario` で実行した。trace の全評価の状態文書を `result.store.get` で読め、trace を `RunRecord` にした `build_corpus` の項目の状態文書がそれと同じで、`verify(scenario, result, result.store)` は空だった。plan\_tasks のシナリオでは、往復 14 の回避の出力と、16 項目の id、scope、対象、選択肢、状態文書、source（種と seq）が同じだった
3. scenario\_corpus を置き換え、tests/test\_labeling.py の test\_scenario\_only\_representative\_is\_the\_state\_the\_classifier\_sees を、項目の状態文書を `result.store.get` で読んだ状態文書と文として比べ（前は SHA-256 が実行記録にあることだけ）、scenario\_corpus の全項目が評価ごとにそう読んだ状態文書と同じことも確かめる形にした。最初は、ゲートの評価の対象を出来事の stage で引いて KeyError で落ちた（ゲートの対象は出来事の phase）ので直した
4. 材料を作り直さずに（コミットしたものは往復 14 の回避で作ったまま）tests/test\_labeling.py の 23 件を走らせ、すべて通る。test\_material\_is\_regenerated\_from\_the\_trial\_runs が、置き換えた後のコードで作り直した項目と材料の文が、コミットしたものと同じことを確かめる。加えて `labeling.write` をスクラッチのパスに書き、docs/human-labeling.md と docs/human-labeling.corpus.jsonl とバイト単位で同じことを確かめた
5. check.sh が通る（ruff check、ruff format、mypy strict、pytest 677 件で 146.6 秒、全体で約 2 分 28 秒。往復 14 の 676 件から増えた 1 件は本体の側のテスト（往復 14 の後の本体のコミットは 453fd31 だけで、変えたファイルの名前に本体のテストがある。中身は読んでいない）。この例のテストは 213 件のまま）

変わった数値: 無い。人に渡す材料は 66 項目、100,276 文字のまま。例のテストは 213 件のまま（tests/test\_labeling.py の 1 件を書き直した）。分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較、オラクル、トリアージも変わらない（シナリオの状態文書を読む手段だけを変えた）。

変えたファイル: software\_factory/labeling.py、tests/test\_labeling.py、README.md、docs/adopting-gaps.md、docs/progress.md。

## 往復 16（2026-10-23）

第三者の検証役が往復 14〜15 の後の人に渡す材料を確かめ直し、docs/review-findings.md の I に、人間の側の決定（材料の読み方の方針のうち、記述の読み方を決める二つを外す）と、中 2（I-M1、I-M2）、低 4（I-L1〜I-L4）を書いた。フレームワークの側は、手引き第15.1節の 2 に、比べ方の説明に比べる相手の答えを書かないこと、後の対象とゲートの状態文書から前の対象の印が推せるので対象の順に分けて渡すこと、完全な盲検にならないことを記録することを書き足した（changelog.md の「未公開」の第15.1節の項目。コミット 227c72e）。利用者として、そのすべてに対応した。記述（workflow.yaml）、分布、設計値、基準、種、フィクスチャは変えていない（tests/stochastic.yaml は注記の一行のパスだけ）。人のラベルはまだ無い（docs/human-labels.jsonl が無く、「ラベル:」はすべて空）ので、材料の作り直しで失われるものは無い。

完了条件を先にテストにした。tests/test\_labeling.py を書き直し（23 件 → 35 件。パラメータを含む）、直す前のコードで 35 件のうち 25 件が落ちる（21 件が失敗、4 件が読み込みの誤り）ことを確かめてから直した。通っていた 10 件は、組の網羅、訪問 2 以降の扱い二つ、シナリオだけが写す代表、材料が印と id と出どころと順によらないこと（その時は一つの文を比べていた）、印だけの行、コマンドの場所、ラベルのファイルが無い時の報告、代表の前提の二つ。

| 指摘 | 対応 |
| --- | --- |
| 人間の側の決定（読み方の方針の二つを外す） | 直した。読み方の方針から「記述が中身の条件を書いていれば中身を確かめ、書いていなければ確かめない」と「記述の括弧の中の列挙は、記述が書いた範囲として読む」を外した。残る方針は、決定が名指さなかった「分類器と同じ立場で、記述を字義どおりに読み、状態文書から判断できることだけで選ぶ」と、決定が頼む「迷ったら unknown を選び、理由を一行添える」だけ（決定の範囲を広げなかった）。ほかは事実だけ。二つの句（と「中身を確かめる」「記述が書いた範囲」）が材料に無いことをテストで確かめる。README に決定と理由（記述の曖昧さを材料の外で埋めると、第15.1節で見つけたい食い違いが隠れる。割れた項目は記述の問題として後で扱う）を書いた |
| I-M1 比べ方の説明が、ゲートの項目の比べる相手を名指す | 直した。「付けた後」の compare の説明を「ラベルを印と比べ、食い違う項目を番号で挙げる」にした（括弧書き「ゲートは goal」を消した）。地の文（囲みの外から、選択肢の記述と選べる選択肢の id の行を除いたもの）のうち、比べ方、ゲート、印を述べる文に選択肢の id が一つも無いことと、「ゲートは goal」「（ゲートは」「goal と比べ」「印（」「ゲートの項目は goal」の句が無いことを、すべてのファイルでテストで確かめる。ゲートの事実（状態文書はフェーズの全体）と、goal の事実（指標が落ちると選択肢に無い）は別の箇条にした |
| I-M2 後の対象とゲートの状態文書から前の対象のクラスが推せる | 直した。材料を docs/human-labeling/ の下の、読み方の 00-guide.md と、対象ごとの 10 のファイルに分けた（下の表）。対象のファイルはワークフローの順で、ゲートのファイルはそのフェーズの最終ステージのファイルの直後（検証役の二つの案はどちらも漏れるので、三つ目を選んだ。README に理由を書いた）。00-guide.md の「付ける順」と各ファイルの冒頭に、番号の順に付けること、前のファイルを付け終えるまで次のファイルを開かないこと、付け終えたファイルのラベルを後で変えないこと、各項目はその項目の状態文書と選択肢の記述だけで選びほかの項目やファイルと見比べないこと、ファイルを一つずつ受け取る時は返してから次を受け取ることを書いた。ラベルを読む処理（labels）は、docs/human-labeling/ の下のファイルをすべて読み、付けていないファイルの項目は空として数える。番号は全ファイルを通した通し番号のまま（コーパスはバイト単位で変わらない）。README の「人に渡す形」に、この性質と選んだ対策、ゲートの置き場の理由、残る手がかり（設計を知る人には完全な盲検にならない。同じファイルの中の訪問をまたぐ同じ代表と、持ち帰った問い。付け終えたラベルを変えないことは頼むだけ）を書いた |
| I-L1 「ラベル:」の後の二つ以上の id | 直した。最初の id の後の文から括弧（「（ ）」と「( )」、入れ子も）の中を除き、選択肢の id（コーパスのどれかの選択肢の id）が語として残れば、項目の番号を添えた誤り（終了コード 2）にする。「ラベル: goal か unknown（迷う）」「ラベル: goal/unknown」「ラベル: `goal` `unknown`」「ラベル: unknown、goal かもしれない」が誤りになり、「ラベル: unknown（goal か迷った。(goal) とも読める）」は unknown として読むことをテストで確かめる。00-guide.md の「ラベルの書き方」に、理由は括弧の中に書き、括弧の外に id を二つ以上書くと誤りになることを書いた |
| I-L2 冒頭が手引きを指す | 直した。00-guide.md の冒頭から「（adopting.md 第15.1節）」を外し、「付けた後」に「選び方と比べ方の手引きは adopting.md 第15.1節にある。ラベルを付け終えるまで読まない」を置いた。冒頭（最初の「## 」より前）に adopting.md と 15.1 が無く、「付けた後」の一つの箇条に節の名と「ラベルを付け終えるまで読まない」があり、材料の中で adopting.md を指すのはその一か所だけで、対象のファイルは指さないことをテストで確かめる |
| I-L3 事実の説明 | 直した。(a) 置き書きを、人に見せる状態文書から機械的に集めて（行の全体が括弧の中の文。多く現れる順）、読み方の事実に列挙し、どれも空の節として数えると書いた。今は「（なし）」「（判断できない）」「（実行できなかった）」「（未完）」の四つ（「A: 未定（後で決める）」のような、行の一部だけが括弧の文は入らない）。材料の囲みの中の、置き書きの形の行の集まりが、列挙と一致することをテストで確かめる。(b) 「指標の値は入っていない。テストを実際に実行した結果（指標の一つ）も入っていないので、テストが通るかは、状態文書のコードとテストから判断することになる」と書いた。あわせて「記憶の `[]` は空の一覧」を足した |
| I-L4 review と acceptance の実装の変種 | 直した。README の「まとめ方」の「ほかの対象（implement と review を含む）には無い」を、implement には無く、review と acceptance は goal の実装の変種で repo/src/shopcart/discount.py の区切りだけが変わる（試しのコーパスで review は各クラス 3 通り、acceptance は材料に入れる ok と ok\_b の 2 通り）がまとめた、と直し、まとめた理由（記述は review.json、verification.md と記憶で判断し、変種で当てはまり方が変わらない。review の指摘は design.md と repo/tests/ について述べ、requirement\_unmet の代表が挙げる振る舞いは ok と ok\_b で同じ）を書いた。往復 14 で直した review の changes\_requested の代表を、変えた代表として記録した（labeling.py の CHANGED の review と EVIDENCE の review。README の「変えた代表と変えた所」）。届く対象は review だけ（review.json は review だけが書き、changes\_requested では後へ進まない）。まとめた組の中で違う区切りが discount.py だけであること、変種の数、changes の review.json を含む状態文書の対象が review だけであることをテストで確かめる。review の項目はどれも design.md を含むので、選ぶ項目は変わらない |
| 新しい不足 | N19（人に渡す材料を対象の順に分ける時、ゲートの項目を順のどこに置くかが手引きから一つに決まらない）を adopting-gaps.md に書いた |

材料のファイルの分け方と項目の数（番号は全ファイルを通した通し番号。文字数は Python の len、括弧の中はバイト数）:

| ファイル | 対象 | 項目の数 | 番号 | 文字数 |
| --- | --- | --- | --- | --- |
| 00-guide.md | 読み方（項目は無い） | 0 | | 2,571（5,935） |
| 01-intake.md | ステージ intake | 4 | 1〜4 | 2,911（6,179） |
| 02-analyze.md | ステージ analyze | 14 | 5〜18 | 15,557（31,037） |
| 03-discovery-gate.md | フェーズ discovery のゲート | 6 | 19〜24 | 5,274（10,508） |
| 04-design.md | ステージ design | 3 | 25〜27 | 4,364（7,122） |
| 05-plan\_tasks.md | ステージ plan\_tasks | 3 | 28〜30 | 5,392（8,276） |
| 06-architecture-gate.md | フェーズ architecture のゲート | 1 | 31 | 3,387（5,293） |
| 07-implement.md | ステージ implement | 4 | 32〜35 | 9,459（13,469） |
| 08-unit\_test.md | ステージ unit\_test | 3 | 36〜38 | 9,271（12,895） |
| 09-acceptance.md | ステージ acceptance | 24 | 39〜62 | 37,584（60,852） |
| 10-review.md | ステージ review | 4 | 63〜66 | 8,381（11,539） |
| 合わせて | | 66 | | 104,151（173,105） |

- 往復 15 までの一つのファイル（docs/human-labeling.md、100,276 文字、163,942 バイト）は消した。増えた 3,875 文字は、読み方のファイルの頭と「付ける順」と、各ファイルの冒頭の頼み。66 項目のすべてに選択肢の記述と状態文書の全文を並べた形（231,447 文字）の 45%
- 項目、番号、コーパス（docs/human-labeling.corpus.jsonl）は変わらない（作り直したコーパスがバイト単位で同じ）。項目の状態文書と、対象ごとの選択肢の記述と共通の区切りの見せ方も変わらない

ゲートの置き場（README の「人に渡す形」と N19）:

- 最終ステージより前（検証役の案の一つ）: ゲートの状態文書が、最終ステージの goal の成果物（analyze の requirements.md、plan\_tasks の tasks.yaml）を最終ステージを付ける前に見せる
- 別のファイルにして最後（もう一つの案）: 後のフェーズの対象の状態文書が、ゲートの状態文書のファイルをすべて含む（acceptance ⊇ discovery のゲート、implement ⊇ architecture のゲート）。フェーズを通った状態文書が、ゲートを付ける前に見える
- 最終ステージの直後（選んだ並び）: どちらも、付けた後でしか見えない。前のファイルの状態文書が後のファイルの対象の書いた成果物を含まないことと、上の二つの事実をテストで確かめる。並びを二つの案に変えると、ファイルの順のテストと、前後の成果物のテストのどちらも落ちる（スクラッチで ORDER を差し替えて確かめた）

検証:

1. docs/review-findings.md の I と、227c72e の adopting.md と changelog.md の差分（第15.1節の 2 と、changelog.md の「未公開」の第15.1節の項目）を読んだ
2. 試しのコーパスを読み（スクラッチ）、review と acceptance のまとめた組で違う区切りが discount.py だけであること、changes の review.json が review の状態文書にだけ届くこと、材料のゲートの 7 項目がどれも goal を選べること、置き書きの四つ、各対象の状態文書の区切り（acceptance の区切りが discovery のゲートのファイルを、implement の区切りが architecture のゲートのファイルを含むこと）を確かめた
3. 第三者役（advisor）に方針を相談した。最初の答えは「ゲートは最後に回す」だったが、2 の包含の事実（acceptance ⊇ discovery のゲート、implement ⊇ architecture のゲート）を示して相談し直し、直後に置くことで一致した。読み方の方針の残りの一つ（分類器と同じ立場、字義どおり）は、人間の決定が二つを名指しているので残すことにした
4. 完了条件を tests/test\_labeling.py に先に書き、直す前のコードで 35 件のうち 25 件が落ちることを確かめた
5. labeling.py を直し、examples/software-factory/ で `uv run python -m software_factory.labeling write` で材料を作り直し、docs/human-labeling.md を消した。コーパスが前とバイト単位で同じことを cmp で確かめた。00-guide.md と、各ファイルの冒頭と節の頭を読んだ
6. 最初の実行で 2 件が落ちた。読み方の文が折り返しの行の頭の空白を挟み、句の検索に掛からなかった（テストの側で、折り返しをつなぐ時に行の頭の空白も除くようにした）。ゲートの包含の確かめに記憶の区切りを含めていた（discovery のゲートの記憶 intake\_questions は acceptance の状態文書に無い。ファイルの区切りで比べるようにした）
7. スクラッチで ORDER を、ゲートを最終ステージの前に置いた並びと、ゲートを最後に回した並びに差し替え、ファイルの順のテストと前後の成果物のテストがどちらも落ちることを確かめた
8. check.sh が通る（ruff check、ruff format、mypy strict、pytest 689 件で 146.6 秒、全体で約 2 分 27 秒。往復 15 の 677 件から増えた 12 件は tests/test\_labeling.py）。その後、受け取ったラベルの確かめ（test\_received\_labels\_fit\_the\_corpus）が、ラベル 0 件の docs/human-labels.jsonl（返却の前に labels を走らせるとできる）で例外になる所を、重なりの無いことを全件で確かめる形に直し、手で書いた文書（README.md、progress.md、adopting-gaps.md、tests/README.md）を変えた後に、もう一度通した（689 件で 146.9 秒、全体で約 2 分 28 秒）。実物の docs/human-labeling/ に対しては labels を走らせていない（docs/human-labels.jsonl は無いまま。compare は無いことを報告して 1 で終わる）

変わった数値:

- 人がラベルを付ける材料: 一つのファイル（100,276 文字）→ 11 のファイル（104,151 文字）。66 項目と、番号と id の対応は変わらない
- 例のテスト: 213 → 225 件（tests/test\_labeling.py が 23 → 35 件）
- 分布テストの観測値、独立性検証と入り方の検定の p 値、マルコフ合成の比較、オラクル、トリアージ: 変わらない（材料の見せ方と、ラベルを読む処理だけを変えた）

変えたファイル: software\_factory/labeling.py、tests/test\_labeling.py、tests/README.md、tests/stochastic.yaml（注記の一行）、docs/human-labeling/（新しく 11 のファイル）、docs/human-labeling.md（消した）、README.md、docs/adopting-gaps.md、docs/progress.md。docs/human-labeling.corpus.jsonl は書き直したが中身は同じ。

## 残っていること

- markov.yaml の実行のゲートはいつも goal（前の数値を保つため）。ゲートの分布は markov\_gated.yaml の実行の集まりで確かめる
- release 以外で carry によって分布が変わる本体は、マルコフ合成と合わないので例には置いていない（gaps D2）。entry\_dependence がそれを見分けることはスクラッチで確かめた（gaps N9）
- 分類器の検証の閾値は、偽の分類器なので決めていない（第15節の「人間が閾値を決める」は実際の分類器の時の手順）
- 記述と代表の整合の人手のラベル: docs/human-labeling/ の下の 66 項目に人がラベルを付ける（まだ）。00-guide.md と 01-intake.md から番号の順に一つずつ渡し、付け終えたファイルが返ってから次を渡す。受け取ったら docs/human-labeling/ の下に置き、examples/software-factory/ で `uv run python -m software_factory.labeling labels --labeler <名前>` と `uv run python -m software_factory.labeling compare` で印と比べ、食い違いがあれば代表か記述を直す（記述を直すのは人間の承認の後。割れた項目は記述の問題として扱う）。これまでの試しのラベル（エージェント）は往復 8 の 56 項目と往復 10 の 32 項目で、どちらも κ 1.0
- plan\_tasks の design\_incomplete は、人間の回答で、記述を変えず確率的な代表を置かない今の形のまま残すと決まった（E2E の注入とシナリオで踏む）
- 不足と不備を分けて数えることは、記述を変えずに coverage\_gaps の項目の書き方で区別できる（第13節。任意）。今はしていない
