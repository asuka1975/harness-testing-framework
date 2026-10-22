# 公開 API の引数と属性

公開の名前ごとの引数、属性、戻り値と、その説明（docstring）。scripts/api\_reference.py が本体から作る。
手で直さない。名前の一覧と使い方は [api.md](api.md) と [adopting.md](adopting.md) にある。

## `harness_testing_framework.schema`

### `load_workflow_document(path: Path) -> Any`

ワークフロー定義の YAML を読む。スキーマの検証はしない。

### `load_workflow_schema() -> dict[str, Any]`

同梱したワークフロースキーマを読み込む。

### `SCHEMA_FILE`

`'workflow.schema.json'`

### `WorkflowDocumentError`（例外。ValueError の一種）

ワークフロー定義の YAML が文書として読めない（構文、キーの型、キーの重複）。

## `harness_testing_framework.contract`

### `Abort()`

中止。実行を中止状態で終え、最後のスナップショットを残す。

### `AwaitingAnswer`（例外。Exception の一種）

回答がまだ無いことの合図（3.3）。ランタイムは実行を中断状態にする。

### `AwaitingDecision`（例外。Exception の一種）

運用者の選択がまだ無いことの合図（3.4）。ランタイムは実行を escalate 待ちで保存する。

### `Classification(choice: str | None, confidence: float)`

分類の結果。choice は選んだ選択肢の id（答えられなければ None）、confidence は 0〜1 の確信度。

### `Classifier`（Protocol）

- `classify(state: str, options: Sequence[Option]) -> Classification`

### `ContinueAsGoal(note: str, by: str = '')`

goal 到達扱いで続行。note は注記（なぜ）、by は誰が（空ならランタイムが operator と書く）。

成果物はそのまま後のステージとゲートに渡る。後のゲートの指標は免れないので、成果物が実際に基準を
満たしていなければ、後のゲートで goal が選択肢から外れ、もう一度 escalate しうる。

### `CONTRACT_VERSION`

`'0.1'`

### `Decision`（型）

`Decision = Rerun | RollbackTo | ContinueAsGoal | Abort`

### `Edge(stage: str, state: str, target: str)`

rollback の辺。ステージ stage の end_state state から、ステージ target へ戻る。

### `Escalation(reason: EscalationReason, stage: str, outcome: str | None, edge: Edge | None, count: int | None, message: str = '')`

escalate の状況。stage は escalate したステージ、outcome は評価の結果（評価の前の escalate なら None）。

edge と count は、max を超えた辺と、それを通った回数（max 超過の時だけ）。message は補足（本体の例外や
契約違反の内容など）。

### `EscalationReason`（型）

`EscalationReason = Literal['max_exceeded', 'unknown', 'stage_error', 'contract_violation']`

### `JSONValue`（型）

`JSONValue = bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None`

### `LLMClient`（Protocol）

- `complete(request: JSONValue) -> JSONValue`

### `load_contract_schema(name: str) -> dict[str, Any]`

同梱した契約の JSON Schema（SCHEMA_FILES のいずれか）を読む。

### `MetricError`（例外。Exception の一種）

指標を測定できない。評価ではその指標を未達とする。

### `MetricRegistry`（Protocol）

- `names() -> Collection[str]`
- `measure(name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float`
  値を測る。測定できなければ MetricError を送出する。

  args はワークフロー定義の基準の args で、読み取り専用の Mapping（dict とは限らない。必要なら dict(args)
  で写す）。同じスナップショットと args には同じ値を返す。そのため、費用の高い測定の結果は、読むファイルの
  内容のハッシュと args を鍵にして覚えてよい。

### `Operator`（Protocol）

- `decide(escalation: Escalation) -> Decision`

### `Option(id: str, description: str)`

分類の選択肢。id は goal か end_state の id、description はワークフロー定義の記述そのもの。

### `Question(text: str, choices: tuple[str, ...] = ())`

ユーザーへの質問。text は質問の文、choices は選択肢（自由回答なら空）。

### `Rerun()`

再実行。escalate したステージを、その直近の開始時スナップショットから新しい訪問として実行し直す。

### `RollbackTo(stage: str, carry: tuple[str, ...] = ())`

指定ステージへのロールバック。stage は escalate したステージ自身か、それより前のステージ。

carry は持ち帰る記憶の名前で、戻り先の memory_in にあるものに限る。

### `SnapshotView`（Protocol）

読み取り専用のスナップショット。

- `exists(path: str) -> bool`
- `read_bytes(path: str) -> bytes`
- `read_text(path: str) -> str`
- `list_files(prefix: str = '') -> Sequence[str]`
  prefix で始まるファイルのパスを辞書順に返す。
- `memory(name: str) -> JSONValue`
- `baseline() -> 'SnapshotView | None'`
  比べる基準のスナップショット。ステージの指標ならそのステージの開始時、
  フェーズの指標ならフェーズの最初のステージの直近の開始時。

### `StageBody`（Protocol）

### `StageContext`（Protocol）

ステージ本体に渡す文脈。ここにある属性と操作だけを使う（ほかの名前はランタイムの内部のもの）。

- `stage_id: str`（属性）
  このステージの id。
- `visit: int`（属性）
  この実行でこのステージに入った回数（1 から）。
- `workspace: Path`（属性）
  作業領域。ランタイムが訪問ごとに開始時スナップショットから作り、訪問の後に消す。
- `seed: int`（属性）
  実行の種、ステージの id、訪問の回数から SHA-256 で導いた整数。

  確率的な振る舞いの唯一の乱数の源。`random.Random(seed)` にそのまま渡してよい。訪問ごとの種は
  ハッシュから導くので、互いに独立な一様の種とみなせる。
- `read_memory(name: str) -> JSONValue`
  memory_in に宣言した記憶を読む。値がまだ無ければ（carry で受け取っていなければ）None。

  宣言の無い名前を読むのは契約違反。
- `write_memory(name: str, value: JSONValue) -> None`
  memory_out に宣言した記憶を書く。宣言の無い名前を書くのは契約違反。
- `user_io: UserIO`（属性）
  awaits_user を宣言したステージだけが使える。
- `llm: LLMClient`（属性）
  recorder を経由した LLM クライアント。

### `UserIO`（Protocol）

- `ask(question: Question) -> str`
  回答の文を返す。回答がまだ無ければ AwaitingAnswer を送出する。

## `harness_testing_framework.runtime`

### `Annotation(kind: str, stage: str, note: str, by: str = '')`

### `BlobStore(root: Path)`

内容アドレスのファイル置き場と、スナップショットのマニフェストの置き場。

- `put(data: bytes) -> str`
  内容を置き、その SHA-256 を返す。
- `get(digest: str) -> bytes`
  内容を SHA-256 で読む。スナップショットのファイル（snapshot.files[パス]）も、分類器が見た状態文書
  （実行記録の evaluation、コーパスとトリアージの項目の state）も、これで読める。
- `put_snapshot(snapshot: Snapshot) -> str`
  スナップショットのマニフェストを置き、その id を返す。
- `get_snapshot(snapshot_id: str) -> Snapshot`
  スナップショットを id で読む。

### `build_workflow(doc: Mapping[str, Any]) -> Workflow`

検査を通ったワークフロー定義の文書からモデルを作る。

### `canonical_json(value: Any) -> bytes`

マニフェストの正規形（契約 第5節）。

キーは符号位置の順、区切りに空白なし、文字は UTF-8 のまま（制御文字などは JSON の規則で
エスケープ）、数は ECMAScript の Number::toString の書き方、末尾の改行なし。

### `ContractViolation`（例外。Exception の一種）

本体が契約に反する操作をした（契約 第8節）。

### `load_workflow(path: Path, metrics: Collection[str]) -> Workflow`

ワークフロー定義を読む。metrics は指標レジストリにある指標名。警告は読み込みを妨げない。

### `OperatorDecisionInvalid`（例外。ValueError の一種）

運用者の選択が契約 3.4 の条件を満たさない。

### `Passthrough()`

記録も再生もしない。

- `call(kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]) -> JSONValue`

### `Recorder`（Protocol）

- `call(kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]) -> JSONValue`

### `Recording(path: Path)`

外を呼び、応答を JSON Lines に書き足す。

- `call(kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]) -> JSONValue`

### `ReplayOnly(path: Path)`

記録から応答を返し、外を呼ばない。記録に無い呼び出しは Missing で止める。

- `Missing`（例外）
  記録に無い呼び出し。黙って外を呼ばない。
- `call(kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]) -> JSONValue`

### `RunResult(status: str, state: RunState, events: list[Event], snapshots: list[str])`

start か resume の一区切りの結果。events と snapshots はその区切りの分。

### `RunState(seed: int, status: str = 'running', stage: str = '', visit: int = 0, visits: dict[str, int] = <factory>, starts: dict[str, str] = <factory>, current: str = '', counts: dict[str, int] = <factory>, answers: list[str] = <factory>, responses: list[JSONValue] = <factory>, pending: dict[str, Any] | None = None, escalations: int = 0, seq: int = 0)`

保存して別のプロセスで再開できる、実行の状態。

current は最後のスナップショットの id。status が suspended なら pending は
{"kind": "user", "question": {"text": 質問の文, "choices": [選択肢, ...]}}、awaiting_operator なら
{"kind": "operator", "escalation": escalate の状況}。ほかの属性はランタイムの内部の状態で、読み書きしない。

- `to_json() -> str`
- `from_json(text: str) -> 'RunState'`

### `Runtime(workflow: Workflow, bodies: Mapping[str, StageBody], *, registry: MetricRegistry, classifier: Classifier, operator: Operator, store: BlobStore, workdir: Path, user_io: UserIO | None = None, llm: LLMClient | None = None, threshold: float = 0.5, recorder: Recorder | None = None, state_limit: int = 20000)`

参照ランタイム。ワークフロー定義から遷移とゲートを駆動する。

- `start(seed: int, inputs: Mapping[str, bytes]) -> RunResult`
  種 seed と、ワークフローの inputs のファイル（パスから内容）で実行を始める。
- `resume(state: RunState, *, answer: str | None = None, decision: Decision | None = None) -> RunResult`
  中断（suspended）した実行を answer で、escalate 待ち（awaiting_operator）の実行を decision で
  再開する。state は同じ置き場を使うランタイムで保存したもの。
- `snapshot(snapshot_id: str) -> Snapshot`
  スナップショットを id で読む。最後のものの id は result.state.current。

### `Snapshot(files: Mapping[str, str] = <factory>, memory: Mapping[str, JSONValue] = <factory>, gates: tuple[str, ...] = (), annotations: tuple[Annotation, ...] = ())`

- `manifest() -> dict[str, Any]`
- `id: str`（属性）
- `with_gate(phase_id: str, phase_order: Sequence[str]) -> 'Snapshot'`
- `with_annotation(annotation: Annotation) -> 'Snapshot'`
- `from_manifest(manifest: Mapping[str, Any]) -> 'Snapshot'`

### `SnapshotReader(snapshot: Snapshot, store: BlobStore, baseline: Snapshot | None = None)`

読み取り専用のスナップショット（契約 7.2 の view）。

- `exists(path: str) -> bool`
- `read_bytes(path: str) -> bytes`
- `read_text(path: str) -> str`
- `list_files(prefix: str = '') -> Sequence[str]`
- `memory(name: str) -> JSONValue`
- `baseline() -> 'SnapshotReader | None'`

### `Stage(id: str, name: str, description: str, phase: str, position: int, awaits_user: bool, reads: tuple[str, ...], writes: tuple[str, ...], memory_in: tuple[str, ...], memory_out: tuple[str, ...], goal: Goal, end_states: tuple[EndState, ...], rollbacks: Mapping[str, Rollback] = <factory>)`

### `Workflow(name: str, description: str, inputs: tuple[str, ...], phases: tuple[Phase, ...], stages: tuple[Stage, ...])`

- `stage(stage_id: str) -> Stage`
- `phase(phase_id: str) -> Phase`
- `next_stage(stage_id: str) -> Stage | None`
- `is_last_in_phase(stage_id: str) -> bool`
- `scope: tuple[str, ...]`（属性）
  スナップショットが持つ範囲（inputs と全ステージの writes）。
- `phase_order: tuple[str, ...]`（属性）

### `WorkflowInvalid`（例外。ValueError の一種）

整合性検査で誤り（error）が出たワークフロー定義。

## `harness_testing_framework.testing.spec`

### `check_workflow(doc: Any, metrics: Collection[str]) -> list[Violation]`

ワークフロー定義を検査する。metrics は指標レジストリにある指標名。

### `check_workflow_file(path: Path, metrics: Collection[str]) -> list[Violation]`

ワークフロー定義のファイルを読んで検査する。

### `CODES`

`{'document': (<Severity.ERROR: 'error'>, 'YAML の文書として読めない'), 'schema': (<Severity.ERROR: 'error'>, 'スキーマに適合しない'), 'rollback_max': (<Severity.ERROR: 'error'>, 'rollback の max が無いか、1 以上の整数でない'), 'duplic …`

### `Severity`（列挙）

`ERROR`, `WARNING`

### `Violation(location: str, code: str, message: str)`

- `severity: Severity`（属性）

## `harness_testing_framework.testing.harness`

### `AbortOperator()`

escalate にはいつも中止で答える運用者（分布テストとマルコフ合成の既定の方針）。

- `decide(escalation: Escalation) -> Decision`

### `AutoUser(answer: str = '自動の回答')`

いつも同じ回答をその場で返すユーザー。

- `ask(question: Question) -> str`

### `conformance_dir() -> Path`

パッケージに同梱した契約適合テスト一式（contract/conformance/ の写し。README.md、workflows/、
scenarios/、files/、manifests.json）のディレクトリ。シナリオの形式は load_contract_schema で読む。

### `conformance_scenarios() -> list[Path]`

同梱した契約適合テストのシナリオのファイル（名前の順）。

### `ConformanceRegistry()`

契約適合テストの指標レジストリ（flag と number）。

- `names() -> Collection[str]`
- `measure(name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float`

### `evaluation_target(state: str) -> tuple[str, str, int] | None`

状態文書の見出し行（契約 2.4）から、評価の対象（scope、id、訪問の回数）を読む。

### `Expectation(status: str, trace: list[str], memory: Mapping[str, JSONValue] | None = None, annotations: int | None = None, starts: Mapping[str, Mapping[str, Any]] = <factory>, options: Mapping[str, list[str]] = <factory>)`

### `load_scenario(path: Path) -> Scenario`

シナリオを読む。ファイルの参照（{from: パス}）は、ここで内容の文字列に置き換える。

### `marked_class(state: str) -> str | None`

状態文書の見出し行が示す評価の対象について、印 `[[class <対象>=<クラス>]]` が示すクラス（最後の印）。

### `MarkerClassifier(confidence: float = 0.9)`

成果物に埋めた印 `[[class <対象の id>=<クラス>]]` を読む偽の分類器。

確率的な偽の本体と組む。

状態文書の見出し行から評価の対象を読み、その対象の印が示すクラスを返す。印が無ければ、
goal が選択肢にあれば goal（フェーズゲートの既定）、なければ答え無し。印は成果物の先頭に置く
（状態文書の長さの上限で切り詰められないように）。

- `classify(state: str, options: Sequence[Option]) -> Classification`

### `ReplayOnly(path: Path)`

記録から応答を返し、外を呼ばない。記録に無い呼び出しは Missing で止める。

- `Missing`（例外）
  記録に無い呼び出し。黙って外を呼ばない。
- `call(kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]) -> JSONValue`

### `run_scenario(scenario: Scenario, workdir: Path, *, registry: MetricRegistry | None = None, fixtures: Path | None = None, record: Path | None = None, replay: Path | None = None, max_resumes: int = 50, user: UserIO | None = None) -> ScenarioResult`

シナリオを参照ランタイムで実行する（README.md の手順）。

record を与えると外からの値をそこに記録し、replay を与えると記録だけから再生する。
再生では、偽の分類器・運用者・ユーザー・指標の代わりに、呼ばれたら失敗するものを束縛する。
user を与えると、シナリオの user の台本の代わりにそれ（ユーザーシミュレータなど）に尋ねる。それが回答を
保留して中断した時の再開の回答には、シナリオの user の台本を順に使う。

### `Scenario(path: Path, name: str, description: str, workflow: Path, metrics: str | None, seed: int, threshold: float, inputs: Mapping[str, str], visits: Mapping[str, Mapping[str, Any]], gates: Mapping[str, Mapping[str, Any]], operator: Sequence[Mapping[str, Any]], user: Sequence[Mapping[str, Any]], expect: Expectation)`

読み込んだシナリオ（形は scenario.schema.json）。ファイルの参照は内容の文字列に置き換えてある。

凍結した dataclass なので、一部を変えた写しは `dataclasses.replace(scenario, inputs=...)` で作れる。

### `ScenarioInvalid`（例外。ValueError の一種）

シナリオがスキーマに適合しない。

### `ScenarioResult(status: str, summary: list[str], trace: list[dict[str, JSONValue]], snapshots: list[Snapshot], final_snapshot: Snapshot, state: RunState, resumes: int = 0, problems: list[str] = <factory>)`

### `ScriptedBody(visits: Mapping[str, Mapping[str, Any]], fixtures: Path | None = None)`

訪問ごとの台本どおりに作業領域と記憶を変える偽のステージ本体。全ステージで共有できる。

### `ScriptedClassifier(stages: Mapping[str, Mapping[str, Any]], gates: Mapping[str, Mapping[str, Any]])`

台本どおりに分類する。台本に無いか、選んだ id が選択肢に無ければ「答え無し」。

- `classify(state: str, options: Sequence[Option]) -> Classification`

### `ScriptedOperator(entries: Sequence[Mapping[str, Any]])`

運用者の台本。{"kind": "defer"} は選択の保留。

- `decide(escalation: Escalation) -> Decision`

### `ScriptedUser(entries: Sequence[Mapping[str, Any]])`

ユーザーの台本。{"defer": true} は回答の保留。

- `ask(question: Question) -> str`

### `summarize(events: Sequence[Mapping[str, Any]]) -> list[str]`

実行記録を、出来事ごとの一行の要約にする。

### `transition_coverage(events: Sequence[Mapping[str, Any]]) -> set[str]`

実行記録で通った遷移の種類（TRANSITION_KINDS の部分集合）。

### `TRANSITION_KINDS`

`('next', 'rollback', 'max_exceeded', 'unknown', 'suspend_resume', 'phase_crossing')`

### `Unreachable(names: Collection[str] = ())`

再生の検査で外の代わりに束縛する。呼ばれたら失敗する。

- `Called`（例外）
- `names() -> Collection[str]`
- `measure(name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float`
- `classify(state: str, options: Sequence[Option]) -> Classification`
- `decide(escalation: Escalation) -> Decision`
- `ask(question: Question) -> str`

### `verify(scenario: Scenario, result: ScenarioResult, store: BlobStore) -> list[str]`

結果をシナリオの期待と比べ、食い違いを一行ずつ返す（README.md の手順 5）。

## `harness_testing_framework.testing.stages`

### `chi_square(table: Sequence[Sequence[int]]) -> float`

分割表のピアソンのカイ二乗統計量（期待度数が 0 の列は除く）。

### `CriterionResult(criterion: dict[str, Any], observed: float | None, count: int, n: int, low: float, high: float, passed: bool, note: str = '')`

- `line() -> str`

### `evaluate_expectations(expectations: Expectations, runs: RunSet) -> ExpectationReport`

各基準を判定する。

### `ExpectationReport(expectations: Expectations, results: list[CriterionResult])`

- `passed: bool`（属性）
- `lines() -> list[str]`

### `Expectations(path: Path, name: str, description: str, workflow: Path, runs: int, seed: int, bindings: dict[str, Any], criteria: list[dict[str, Any]])`

### `ExpectationsInvalid`（例外。ValueError の一種）

expectations が形式に適合しない、または基準が矛盾する。

### `independence(runs: RunSet, *, alpha: float = 0.01, permutations: int = 2000, seed: int = 0, min_group: int = 10, cap: int = 2) -> list[IndependenceResult]`

ステージの評価の結果ごとに、代表どうしで次の状態の分布が揃うかを検定する。

判定は not_detected（違いを検出しなかった）、violated（p 値が alpha 未満）、undetermined（件数が min_group
以上の代表が二つ未満）。状態と、訪問の区分（cap 以上は一つ）の組ごとに検定する。

### `IndependenceResult(state: str, visit: int, next_visit: int, groups: dict[str, int], statistic: float | None, p_value: float | None, verdict: str, note: str = '')`

### `load_expectations(path: Path) -> Expectations`

### `record_run(runtime: Runtime, seed: int, inputs: Mapping[str, bytes], *, representative: Callable[[Stage, Snapshot, BlobStore], str] = writes_hash) -> RunRecord`

ランタイムで一回実行し、評価ごとに代表の鍵を添えて記録する。

代表の鍵は、同じクラスの中の違う成果物を見分ける。既定は書いた成果物のハッシュで、偽の本体のように同じ
成果物が繰り返し出る時に向く。LLM の出力のように毎回違う成果物では、意味の近いものを同じ鍵にまとめる関数を与える。
中断や escalate 待ちで止まった実行は、その状態のまま記録する（運用者とユーザーは、その場で答える偽物を束縛しておく）。

### `run_many(runs: int, seed: int, run_one: Callable[[int], RunRecord]) -> RunSet`

種 seed, seed + 1, ... で runs 回実行する。

### `RunRecord(seed: int, status: str, events: Sequence[Event], representatives: Mapping[int, str] = <factory>)`

一回の実行の記録。

representatives は、ステージの評価の seq から、その評価の直前にステージが書いた
成果物（writes に当たるファイル）の内容のハッシュへの対応。同じクラスの中の
「代表」を見分けるのに使う（独立性検証）。

- `run_id: str`（属性）
  実行の一意な id（実行記録の内容のハッシュの先頭 16 桁）。同じ種でも設定が違えば違う。
- `evaluations() -> Iterator[Event]`
- `visits(stage: str) -> int`
  このステージを訪れた回数（訪問の番号の最大）。

### `runs_from_environment(default: int) -> int`

実行の回数。環境変数 HTF_RUNS が default より大きければそれを使う。

基準の幅は default の回数から決めてあるので、環境変数で回数を減らすことはできない（減らすと正しい基準が落ち、
ずれた基準が通りやすくなる）。正の整数でない値は誤り。

### `RunSet(runs: Sequence[RunRecord])`

### `Transition(run: int, seq: int, state: str, visit: int, representative: str | None, next: str, next_visit: int = 0)`

### `transition_counts(runs: RunSet) -> dict[str, Counter[str]]`

### `transition_matrix(runs: RunSet) -> dict[str, dict[str, float]]`

状態ごとの、次の状態（transitions の定義。ゲートをつないで次のステージの評価まで）の経験分布。

### `transitions(runs: RunSet) -> list[Transition]`

全実行の、評価から次の状態への遷移。次の状態は、続くゲートの評価を `>` でつなぎ、その次のステージの評価
（ステージの評価が続かなければ実行の終わり `end:<状態>`）までを含む。

### `wilson_interval(count: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]`

二項の割合の Wilson の区間。n が 0 なら [0, 1]。

## `harness_testing_framework.testing.e2e`

### `compare_prediction(prediction: Prediction, runs: RunSet, k: float = 4.0) -> list[Comparison]`

予測と実測を比べる。差が標準誤差の k 倍以内なら一致とする。

### `Comparison(quantity: str, predicted: float, measured: float, se: float, within: bool)`

- `line() -> str`

### `coverage_targets(workflow: Workflow) -> list[Target]`

踏むべき (ステージ, クラス)。goal、unknown 以外の end_state、unknown の順。

### `CoverageItem(targets: tuple[Target, ...], method: str, scenario: Scenario)`

- `target: Target`（属性）

### `CoverageReport(covered: list[Target], missing: list[Target], reached: dict[Target, bool])`

### `estimate_model(runs: RunSet, cap: int = 2) -> MarkovModel`

実行記録の評価から、(ステージ, 訪問の区分) ごとのクラスの経験分布を推定する。

### `MarkovModel(stage: Mapping[tuple[str, int], Dist], gate: Mapping[tuple[str, int], Dist], cap: int)`

- `stage_distribution(stage: str, visit: int) -> Dist`
- `gate_distribution(phase: str, visit: int) -> Dist`

### `ModelIncomplete`（例外。ValueError の一種）

モデルに、到達しうる (ステージ, 訪問) の分布が無い。

### `plan_coverage(workflow: Workflow, workflow_path: Path, *, goal: Mapping[str, Mapping[str, Any]], induce: Mapping[tuple[str, str], Mapping[str, Any]], inputs: Mapping[str, str], seed: int = 0) -> list[CoverageItem]`

カバレッジ計画を作る。goal はステージごとの goal の台本、induce は (ステージ, クラス) ごとの誘発の台本。

最初の項目は全ステージが goal の実行（全ステージの goal を踏む）。続く各項目は、対象のステージの
最初の訪問だけを対象のクラスにし、ほかの訪問は goal にする。escalate には中止で答える。

### `Prediction(status: dict[str, float], mean_visits: dict[str, float], outcomes: dict[tuple[str, str], float] = <factory>, evaluations: dict[tuple[str, str, int], float] = <factory>, visit_outcomes: dict[tuple[str, str, int, str], float] = <factory>)`

合成の結果。

- status: 最後の状態（completed / aborted）の確率
- mean_visits: ステージごとの訪問の回数の期待値
- outcomes: (ステージ, 結果) ごとのステージの評価の回数の期待値
- evaluations: (scope, 対象, 訪問の区分) ごとの評価の回数の期待値。scope は stage か phase（ゲート）で、
  区分は min(訪問の番号, cap)。ゲートの訪問はフェーズの最終ステージの訪問の番号。visit や from_visit で
  絞った分布テストの基準の分母の期待値 E[n] になる（区分が cap より小さい訪問は、その訪問ちょうど）
- visit_outcomes: (scope, 対象, 訪問の区分, 結果) ごとの評価の回数の期待値

### `run_coverage(plan: list[CoverageItem], workdir: Path, *, registry: MetricRegistry, fixtures: Path | None = None, user: UserIO | None = None) -> CoverageReport`

計画の各項目を実行し、踏んだ (ステージ, クラス) を集める。

user を与えると、awaits_user のステージの台本の ask は、計画の回答の台本の代わりにそれに尋ねる。

### `synthesize(model: MarkovModel, workflow: Workflow, policy: str = 'abort') -> Prediction`

モデルとワークフローから、最後の状態の分布と、訪問と評価の回数の期待値を厳密に計算する（Prediction）。

状態（いまのステージ、ステージごとの訪問の番号、辺ごとの戻りの回数）の確率を、遷移規則に沿って前へ
流す。戻りのたびに回数の和が増え、戻りが無ければステージの位置が進むので、状態は (回数の和, 位置) の
順に一度ずつ処理すれば足りる。訪問の番号は cap で頭打ちにして持つ（分布は min(訪問, cap) だけで決まる）。

### `Target(stage: str, outcome: str)`

## `harness_testing_framework.testing.oracle`

### `build_corpus(runs: RunSet, store: BlobStore, workflow: Workflow, *, unique_states: bool = False) -> list[CorpusItem]`

実行記録の各評価から、分類器が見た状態文書と選択肢の項目を作る。状態文書は置き場から読む。

unique_states が真なら、状態文書と選択肢の組ごとに最初の項目だけを残す。偽の本体のように同じ成果物が
繰り返し出る実行では、同じ状態文書が何度も入り、項目の数の重みが状態文書の出現の回数で偏る。

### `CalibrationBin(low: float, high: float, n: int, accuracy: float, confidence: float)`

### `cohen_kappa(pairs: Sequence[tuple[str | None, str | None]]) -> float`

(人手のラベル, 分類器の選択) の組から Cohen の κ。偶然の一致が 1 なら、一致率が 1 のとき 1。

### `ConfusionClassifier(rows: Mapping[str, Sequence[tuple[str | None, float]]])`

既知の混同行列を持つ偽の分類器。

状態文書の印 `[[class <対象>=<真のクラス>]]` から真のクラスを読み、rows[真のクラス] の (選ぶクラス, 確信度) を
真のクラスごとに、初めて見た順に巡って割り当てる。同じ状態文書には同じ答えを返す（決定論的）。
配分は違う状態文書の数で巡るので、真のクラスごとの違う状態文書の数が rows の長さの倍数で、コーパスに同じ
状態文書が重ならない（build_corpus の unique_states）なら、混同行列は配分どおりになる。

- `classify(state: str, options: Sequence[Option]) -> Classification`

### `CorpusInvalid`（例外。ValueError の一種）

コーパスかラベルが形式に適合しない、または互いに食い違う。

### `CorpusItem(item: str, scope: str, target: str, options: tuple[Option, ...], state: str, source: Mapping[str, Any] = <factory>)`

コーパスの一項目。

item は `<実行の id>-<評価の seq>` で、トリアージの項目の id と同じ形（突き合わせられる）。scope は stage か
phase、target はステージかフェーズの id、options は選択肢、state は分類器が見た状態文書、source は出どころ
（実行の種、seq、分類器の選択）。

- `to_json() -> dict[str, Any]`

### `expected_calibration_error(records: Sequence[tuple[float, bool]], bins: int = 10) -> tuple[float, list[CalibrationBin]]`

(確信度, 正解か) の組の ECE。確信度を [0, 1] の等幅の bins 個の区間に分け（最後の区間は 1 を含む）、
区間ごとの |正解率 - 平均の確信度| を件数で重みづけて足す。

### `FlakyClassifier(base: Classifier, every: int)`

再実行で答えが揺れる偽の分類器。

同じ状態文書を二回目以降に分類する時、初めて見た順で every 件に一件の項目だけ、選択肢の中の別のクラスを返す。
再実行の一致率は 1 - 1/every になる。一回目の答えは基の分類器のもの。
「二回目」は再実行に限らない。コーパスに同じ状態文書が二度あれば、一回目の分類の中でも二度目は揺れる。
重なりの無いコーパス（build_corpus の unique_states）で使う。

- `classify(state: str, options: Sequence[Option]) -> Classification`

### `Label(item: str, label: str, labeler: str)`

人手のラベル。item はコーパスの項目の id、label はその項目の選択肢のどれか、labeler は付けた人。

### `load_corpus(path: Path) -> list[CorpusItem]`

### `load_labels(path: Path) -> list[Label]`

### `oracle_report(classifier: Classifier, corpus: Sequence[CorpusItem], labels: Sequence[Label], *, bins: int = 10, reruns: int = 2) -> OracleReport`

ラベルの付いた各項目を分類器にかけ、κ、混同行列、ECE、再実行の一致率を求める。

同じ項目を reruns 回分類し、すべて同じ選択だった項目の割合を再実行の一致率とする。κ と ECE は一回目の結果で計算する。
分類器の出力はランタイムと同じく「答え無し」に正規化する（例外、範囲外や有限でない確信度、選択肢に無い id）。
答え無しは κ と混同行列では独立のカテゴリとして数え、ECE には入れない。

### `OracleReport(n: int, kappa: float, accuracy: float, confusion: dict[tuple[str, str | None], int], ece: float | None, bins: list[CalibrationBin], rerun_agreement: float, unanswered: int, coverage: float, by_target: dict[str, TargetSummary])`

分類器の検証の結果。

ECE は答えた項目だけで計算する（答え無しを確信度 0 の不正解として入れると、答え無しが多いほど ECE が下がるため）。
答えた割合は coverage に、答え無しの件数は unanswered に出す。κ と混同行列は、答え無しを独立のカテゴリとして数える。
by_target の鍵は `stage:<ステージの id>` か `phase:<フェーズの id>`。

- `lines() -> list[str]`

### `save_corpus(items: Sequence[CorpusItem], path: Path) -> None`

### `save_labels(labels: Sequence[Label], path: Path) -> None`

### `TargetSummary(n: int, kappa: float, accuracy: float, ece: float | None)`

## `harness_testing_framework.testing.triage`

### `decide(queue: Path, record: Path, decision: Decision) -> None`

項目への判定を記録する。label はその評価の選択肢のどれか。分類体系の変更は提案として残す。

### `Decision(item: str, verdict: str, label: str | None, note: str, by: str)`

- `proposal: bool`（属性）

### `decisions(record: Path) -> list[Decision]`

判定の記録の全行（形式を検査する）。

### `enqueue(queue: Path, run: RunRecord, *, review_below: float) -> list[TriageItem]`

実行記録の評価のうち、結果が unknown のものと、確信度が review_below 未満のものを待ち行列に足す。
すでにある項目は足さない。足した項目を返す。

### `items(queue: Path) -> list[TriageItem]`

待ち行列の全項目（形式を検査する）。

### `open_items(queue: Path, record: Path | None = None) -> list[TriageItem]`

判定のまだ無い項目。

### `PROPOSALS`

`('new_class_proposal', 'description_revision_proposal')`

### `TriageInvalid`（例外。ValueError の一種）

待ち行列か判定が形式に適合しない、または項目と食い違う。

### `TriageItem(item: str, run: int, seq: int, scope: str, target: str, visit: int, options: list[str], choice: str | None, confidence: float, outcome: str, state: str, reason: str)`

待ち行列の一項目。

item は `<実行の id>-<評価の seq>` で、分類器の検証のコーパスの項目の id と同じ形。state は状態文書の
SHA-256 で、内容は置き場（BlobStore.get）で読める。reason は unknown か low_confidence。

### `VERDICTS`

`('label', 'not_a_problem', 'classifier_error', 'new_class_proposal', 'description_revision_proposal')`
