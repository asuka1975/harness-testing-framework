# software-factory の作業ログ

harness-testing-framework（v0.1.0）の利用者として、adopting.md だけを手引きに、ソフトウェア開発のワークフロー型ハーネスを作る。

- 読取の制限: docs/adopting.md、examples/toy-minimal/、公開 API の文書（api.md が挙げるもの）だけ。本体の実装（src/、tests/、scripts/、pyproject.toml）、docs/plan.md、docs/progress.md、docs/decisions.md は読まない。本体は直さない
- 分からなかったこと、足りなかったこと、回避したくなったことは docs/adopting-gaps.md に書く
- コミットはしていない（依頼に無いため）

## 状態（2026-10-22）

完了。`scripts/check.sh` が通る（ruff check、ruff format、mypy strict、pytest 576 件、約 2 分 20 秒）。この例のテストは 147 件。変更は examples/software-factory/ の中だけ。

| 求められたこと | どこで満たしたか |
| --- | --- |
| 4 フェーズ以上、8 ステージ以上 | workflow.yaml（5 フェーズ、9 ステージ）。tests/test\_definition.py |
| フェーズ境界越えのロールバック、carry、ユーザー回答待ち | 越境の辺 6 本（design → analyze、implement → plan\_tasks、acceptance → analyze と implement、review → design と implement）。全辺に carry。intake が awaits\_user |
| end\_state は観測できる条件、戻り先つき、unknown を含む | 全ステージに unknown、unknown 以外の 12 クラスにそれぞれ戻り先。carry する記憶を記述が証拠として名指す（テストで確かめる） |
| 偽のステージ本体（LLM なし） | 決定論的: シナリオの台本でフィクスチャを写す。確率的: tests/stochastic.yaml の設計値で、種だけから変種を選ぶ |
| carry を受けた再進入で分布が変わるもの | release（missing\_notes を受けると goal 0.75 → 0.97）。訪問 2 以降と carry の有無が一致することを全実行で確かめる |
| クラス内で下流の分布が分かれるもの | divergent の implement の goal（ok は REQ-1 の切り捨てを誤り、ok\_fixed は正しい）。unit\_test の defect のテストは実在の pytest で前者だけ落ちる |
| 実装と単体テストに本物の指標 | build\_passes、tests\_pass、line\_coverage、lint\_errors、out\_of\_scope\_changes。フィクスチャの repo/ に compileall、pytest、coverage、ruff を実際にかける |
| 要求の取り込みにペルソナ 3 つ以上 | software\_factory/personas.py（precise\_pm、vague\_founder、terse\_engineer）。種からペルソナを選ぶ |
| 全ランナー | 下の「結果」 |

## 結果

- 整合性検査: 誤り 0、警告 0
- 契約適合テスト: contract/conformance/scenarios/ の 24 シナリオすべてが参照ランタイムで期待どおり（tests/test\_conformance.py）。ハーネスの本体は、400 回の実行で契約違反、本体の例外、範囲外のファイルの警告が一度も無い
- 遷移の決定論テスト: 14 シナリオ。遷移の六種、escalate の四択、越境の 6 通り（運用者による越境を含む）を通す。実在の指標の値で goal が選択肢から外れることを expect.options で確かめる。記録再生で同一のスナップショットの列
- 分布テスト: markov.yaml の 12 基準がすべて通り（400 回、種 20000）、markov\_shifted.yaml の 14 基準はすべて落ちる。release の訪問 2 以降の goal は 0.969（62/64）で、「carry で変わらない」とした基準（0.65〜0.85）は落ちる
- 独立性検証: divergent は stage:implement=goal（訪問 1 → 1）で violated（p = 0.0005、代表 136 と 126）。markov はどこにも violated が無く、同じ状態は not\_detected（p = 0.24）。intake の goal のペルソナごとの三つの代表は、どちらの分布でも not\_detected
- E2E: カバレッジ計画が全 (ステージ, クラス) の 30 を踏む（誘発と注入の両方）。推定したモデルと設計値のモデルの予測が、どちらも 41 の量すべてで実測と一致（k = 4）。設計値の標本（design.simulate）と synthesize の厳密な値が一致
- オラクル: 状態文書ごとに重複を除いたステージの 127 項目で、印を読む分類器は κ 1、ECE 0.1。既知の混同行列の分類器は κ 0.623、ECE 0.269、答え無し 7（選択肢に無いクラス）で、独立に計算した値と一致。揺れる分類器の再実行の一致率は 0.748
- トリアージ: 24 回の実行の unknown と確信度 0.7 未満の評価を待ち行列に足し、五種類の判定（label、classifier\_error、new\_class\_proposal、description\_revision\_proposal、not\_a\_problem）を付けて未判定を無くした。ワークフロー定義は変わらない。ラベルを付けた項目をコーパスに足してオラクルのレポートを出した（κ 1、ECE 0.4）

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
| トリアージ | markov | 24 | 80000 |

種は基準を書く前に決め、基準が通るように選び直してはいない。回数は環境変数 `HTF_RUNS` で増やせる。

## 残っていること

- 確率的な実行のゲートはいつも goal（gaps D4）。ゲートの分布を持つマルコフ合成は確かめていない
- release 以外で carry によって分布が変わる本体は、マルコフ合成と合わないので置いていない（gaps D2）
- 分類器の検証の閾値は、偽の分類器なので決めていない（第15節の「人間が閾値を決める」は実際の分類器の時の手順）
