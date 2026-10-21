# 公開 API

ハーネスを作る人が使ってよい、フレームワークの名前と文書の一覧。ここに無いモジュールと名前は内部のもので、予告なく変わる。手順は [adopting.md](adopting.md) にある。

## 公開 API の文書

言語に依存しない仕様で、ハーネスを作る人が読む。

- schema/workflow.schema.json: ワークフロー定義のスキーマ
- contract/contract.md: ハーネス契約（三つの操作、遷移、スナップショット、実行記録、インターフェース、記録再生、契約適合テスト）
- contract/snapshot.schema.json: スナップショットのマニフェストの形式
- contract/trace.schema.json: 実行記録の一行の形式
- contract/conformance/README.md: 契約適合テストとシナリオの書き方、偽物の振る舞い、実行記録の要約の規則
- contract/conformance/scenario.schema.json: シナリオの形式
- contract/conformance/manifests.json: マニフェストの正規形のテストベクトル
- contract/formats/expectations.schema.json: 分布テストの基準（expectations）の形式

## `harness_testing_framework.schema`

ワークフロー定義のスキーマと YAML の読み込み。

| 名前 | 内容 |
| --- | --- |
| `load_workflow_schema` | 同梱したワークフロースキーマを読む |
| `load_workflow_document` | ワークフロー定義の YAML を読む。真偽値と数は YAML 1.2 core に揃え、日付は文字列のまま。キーの重複と、文字列でないキーは誤り |
| `WorkflowDocumentError` | YAML の文書として読めない |
| `SCHEMA_FILE` | 同梱したスキーマのファイル名 |

## `harness_testing_framework.testing.spec`

整合性検査器。コマンドは `python -m harness_testing_framework.testing.spec WORKFLOW.yaml (--registry MODULE:ATTR | --metrics-file FILE)`。

| 名前 | 内容 |
| --- | --- |
| `check_workflow` | 読み込んだ文書を検査し、違反の一覧を返す |
| `check_workflow_file` | ファイルを読んで検査する |
| `Violation` | 違反（場所、符号、説明、重大度） |
| `Severity` | 重大度（error / warning） |
| `CODES` | 違反の符号と、その重大度と説明 |

## `harness_testing_framework.contract`

ハーネス契約の Python 束縛（契約の第7節）。

| 名前 | 内容 |
| --- | --- |
| `StageBody` | ステージ本体。`StageContext` を受け取る呼び出し |
| `StageContext` | 本体に渡す文脈（作業領域、記憶、種、ユーザー入出力、LLM） |
| `MetricRegistry` | 指標レジストリ（`names`、`measure`） |
| `SnapshotView` | 指標が読む、読み取り専用のスナップショット。`baseline()` で比べる基準（開始時）のスナップショット |
| `MetricError` | 指標を測定できない |
| `UserIO` | ユーザー入出力（`ask`） |
| `Question` | 質問（文と選択肢） |
| `AwaitingAnswer` | 回答がまだ無いことの合図。ランタイムは実行を中断する |
| `LLMClient` | LLM クライアント（`complete`） |
| `Classifier` | 分類器（`classify`） |
| `Option` | 分類の選択肢（id と記述） |
| `Classification` | 分類の結果（選んだ id と確信度） |
| `Operator` | 運用者（`decide`） |
| `Escalation` | escalate の状況（理由、ステージ、辺、回数） |
| `EscalationReason` | escalate の理由（max\_exceeded / unknown / stage\_error / contract\_violation） |
| `Edge` | rollback の辺（元ステージ、end\_state、戻り先） |
| `Decision` | 運用者の選択（下の四つのどれか） |
| `Rerun` | 再実行 |
| `RollbackTo` | 指定ステージへのロールバック（carry つき） |
| `ContinueAsGoal` | goal 到達扱いで続行（注記つき） |
| `Abort` | 中止 |
| `AwaitingDecision` | 選択がまだ無いことの合図。ランタイムは実行を escalate 待ちで止める |
| `JSONValue` | JSON で表せる値 |
| `CONTRACT_VERSION` | 契約の版 |
| `load_contract_schema` | 同梱した契約の JSON Schema を読む |

## `harness_testing_framework.runtime`

参照ランタイム。

| 名前 | 内容 |
| --- | --- |
| `load_workflow` | ワークフロー定義を読み、整合性検査を通してからモデルにする |
| `WorkflowInvalid` | 整合性検査で誤りの出たワークフロー定義 |
| `build_workflow` | 検査済みの文書からモデルを作る |
| `Workflow` | ワークフローのモデル |
| `Stage` | ステージのモデル |
| `Runtime` | ランタイム。`start(seed, inputs)` で始め、`resume(state, answer=... / decision=...)` で再開する。引数と既定値は adopting.md の第7節 |
| `RunResult` | 一区切りの結果（状態、出来事、スナップショットの id） |
| `RunState` | 保存して再開できる実行の状態（`to_json` / `from_json`） |
| `BlobStore` | 内容アドレスのファイル置き場とスナップショットの置き場 |
| `Snapshot` | スナップショット（ファイル、記憶、ゲート、注記）。`id` はマニフェストの正規形の SHA-256 |
| `SnapshotReader` | `SnapshotView` の実装 |
| `Annotation` | 注記（goal 到達扱いの記録など） |
| `canonical_json` | マニフェストの正規形 |
| `Recorder` | 記録再生の口 |
| `Passthrough` | 記録も再生もしない |
| `Recording` | 外を呼び、応答を記録する |
| `ReplayOnly` | 記録だけから再生する。記録に無い呼び出しは `ReplayOnly.Missing` |
| `ContractViolation` | 本体が契約に反した |
| `OperatorDecisionInvalid` | 運用者の選択が契約の条件を満たさない |

## `harness_testing_framework.testing.harness`

シナリオによる決定論テストと契約適合テスト。

| 名前 | 内容 |
| --- | --- |
| `load_scenario` | シナリオを読み、形式を検査する |
| `run_scenario` | シナリオを参照ランタイムで実行する（記録と再生も）。結果の `problems` は期待との食い違い |
| `verify` | 実行の結果をシナリオの期待（実行記録の要約、状態、開始時スナップショット、選択肢、記憶、注記）と比べる |
| `Scenario` | 読み込んだシナリオ |
| `ScenarioInvalid` | 形式に適合しないシナリオ |
| `Expectation` | シナリオの期待（状態、実行記録の要約、記憶、注記の数） |
| `ScenarioResult` | 実行の結果（状態、要約、実行記録、スナップショット） |
| `summarize` | 実行記録を要約する |
| `transition_coverage` | 実行記録で通った遷移の種類 |
| `TRANSITION_KINDS` | 遷移の六種 |
| `ScriptedBody` | 訪問ごとの台本どおりに動く偽のステージ本体 |
| `ScriptedClassifier` | 台本どおりに分類する偽の分類器 |
| `ScriptedOperator` | 台本どおりに選ぶ偽の運用者 |
| `ScriptedUser` | 台本どおりに答える偽のユーザー |
| `ConformanceRegistry` | 契約適合テストの指標レジストリ（flag と number） |
| `Unreachable` | 呼ばれたら失敗する代役（再生の検査で使う） |
| `MarkerClassifier` | 成果物の先頭の印 `[[class <対象の id>=<クラス>]]` を読む偽の分類器（確率的な偽の本体と組む） |
| `AbortOperator` | escalate にいつも中止で答える運用者 |
| `AutoUser` | いつも同じ回答をその場で返すユーザー |
| `ReplayOnly` | runtime の `ReplayOnly` と同じもの |
| `evaluation_target` | 状態文書の見出し行から、評価の対象を読む |

## `harness_testing_framework.testing.stages`

多数の実行による分布テスト（expectations）と、独立性検証と遷移行列の推定。

| 名前 | 内容 |
| --- | --- |
| `RunRecord` | 一回の実行の記録（種、最後の状態、実行記録、評価ごとの代表のハッシュ） |
| `RunSet` | 実行の記録の集まり |
| `record_run` | ランタイムで一回実行し、代表のハッシュ（ステージが書いた成果物の内容のハッシュ）を添えて記録する |
| `run_many` | 種を一つずつ変えて何回も実行する |
| `runs_from_environment` | 実行の回数。環境変数 `HTF_RUNS` があればそれを使う |
| `load_expectations` | expectations を読み、形式を検査する |
| `Expectations` | 読み込んだ expectations |
| `ExpectationsInvalid` | 形式に適合しないか、基準が矛盾する expectations |
| `evaluate_expectations` | 実行の集まりで各基準を判定する |
| `ExpectationReport` | 判定の結果（`passed`、`lines()`） |
| `CriterionResult` | 一つの基準の判定（観測値、件数、Wilson の 95% 区間、成否） |
| `wilson_interval` | 二項の割合の Wilson の区間 |
