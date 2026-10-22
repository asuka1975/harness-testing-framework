# 変更の記録

版ごとの、公開 API と公開 API の文書の変更。各版では、互換性に注意する変更（既存の使い方やテストが変わりうるもの）を先に書く。v1.0 までの版では、互換性を壊しうる変更もありうる。

## 未公開（v0.1.0 の後）

### 互換性に注意する変更

- `compare_prediction` が返す量に、ゲートの評価の結果ごとの回数（`gate:<フェーズ>=<結果>`）を足した。返す量の種類を固定の集合で確かめているテストは、`gate` を足す必要がある

### 足したもの

- 公開の名前ごとの引数、属性、戻り値と説明の一覧 [api-reference.md](api-reference.md)
- 公開の名前: `Criterion`、`EndState`、`Goal`、`Phase`、`Rollback`、`Event`、`Key`（runtime）、`Event`、`writes_hash`、`entries`、`Entry`、`entry_dependence`、`EntryDependenceResult`（testing.stages）、`Dist`（testing.e2e）、`SCHEMA_FILES`（contract）、`RandomGateClassifier`、`conformance_dir`、`conformance_scenarios`（testing.harness）
- シナリオの形式: `inputs` と `expect.starts` の `files` の値に、ファイルとディレクトリの参照 `{from: パス}`（contract/conformance/README.md の「ファイルの内容」）。契約適合テストのシナリオ `inputs_from_file` を足した
- `run_scenario(..., user=)` と `run_coverage(..., user=)`: 台本の代わりにユーザーシミュレータを束縛する
- `Prediction` の `evaluations`、`visit_outcomes`（訪問の区分ごとの評価の回数の期待値）と `visits_variance`（訪問の回数の分散）
- `build_corpus(..., unique_states=True)`: 状態文書と選択肢の組ごとに一項目にする
- `entries` と `entry_dependence`: 訪問 2 以降の評価の結果が入り方で違うかの検定（マルコフ合成の仮定の確かめ）
- `RandomGateClassifier`: フェーズゲートの答えを実行ごとの種で決める偽の分類器
- 契約適合テスト一式（workflows/、scenarios/、files/、manifests.json）を Python のパッケージに同梱した

### 変えたもの（使い方は変わらない）

- `synthesize` を、状態の確率を前へ流す計算に書き直した。結果は前と同じで、大きいワークフローで速い
- トリアージの待ち行列と判定の記録を、追記された行だけを検査して読み足すようにした（判定を一件ずつ記録しても遅くならない）
- 契約の文書から、利用者が読まない文書への参照を除き、根拠を本文に書いた。契約適合テストが判定するのはランタイムの実装で、参照ランタイムを使うハーネスは通す必要が無いことを明記した（契約 第10節）。契約の意味は変えていない
- このリポジトリの中に例を作る場合（adopting.md 第11節）
  - examples/<名前>/tests/fixtures/ の下を、リポジトリの lint、型検査、テストの収集から外した
  - 例の語が本体に現れないことの検査で、本体の公開の名前と、本体が持つワークフロー定義の例にある語を除くようにした。重なった語は一度にすべて、一行ずつ出す
  - テストの時間の目安を、一つの例で一分以内から、およそ二分以内（カバレッジの計測の下）に改めた
- 手引き（adopting.md）に、利用者が試して知ったこと（記憶が無い時の値、保留中の質問の形、費用の高い指標、ゲートの不合格を戻す書き方、ユーザーシミュレータの束縛、実ハーネスでの合成の読み方など）を書き足した
- 手引き第2.1節: memory\_out の記憶は訪問のたびに必ず書かせる（書かないと前の値が状態文書に残る）。examples/toy-minimal/ の記述と偽の本体も、問題が無い時に空の一覧を書くように直した
- 手引き第4節: 指標の結果を覚える時は、ツールの異常終了を覚えずに `MetricError` を送出する。測定の失敗が無いことを多数の実行で確かめる
- 手引き第12節: 割合が 0 か 1 に近い基準は、正規近似ではなく二項分布の裾の確率から幅を決める

## v0.1.0（2026-10-22）

最初の公開版。ワークフロー定義のスキーマと整合性検査器、ハーネス契約 v0.1、参照ランタイム、テストランナー（シナリオによる決定論テスト、分布テスト、独立性検証、E2E のカバレッジ計画とマルコフ合成、分類器の検証、トリアージ）、例 examples/toy-minimal/。
