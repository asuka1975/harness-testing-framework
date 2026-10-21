# ハーネスを作る人のための手引き（初版）

この文書は、harness-testing-framework（以下フレームワーク）の上にワークフロー型のハーネスを作る人のためのもの。ハーネスが満たすべきことと、作る順序を書く。

ほかに読むもの:

- [docs/api.md](api.md): 公開 API と、公開 API の文書（スキーマ、契約、シナリオの形式）
- [examples/toy-minimal/](../examples/toy-minimal/): 最小の実例（ワークフロー定義、指標レジストリ、決定論テスト）

扱うのは、ワークフロー定義、整合性検査、契約、参照ランタイム、決定論テスト、契約適合テスト（第1〜11節）と、分布テスト、独立性検証、E2E とマルコフ合成、分類器の検証、トリアージ（第12〜16節）。

## 1. フレームワークとハーネスの分担

フレームワークが提供するもの:

- ワークフロー定義のスキーマと整合性検査器
- ハーネス契約（三つの操作、スナップショット、実行記録、インターフェース）
- 参照ランタイム。ワークフロー定義を読んで遷移とゲートを駆動する
- テストのランナー。シナリオによる決定論テストと契約適合テスト

ハーネスが用意するもの:

- ワークフロー定義（workflow.yaml）
- ステージ本体
- 指標レジストリ（指標の実装）
- ユーザー入出力
- LLM クライアント
- 分類器と運用者（人間の判断の受け口）の束縛

ステージの順序や遷移を、ハーネスのコードに書かない。遷移はワークフロー定義だけが決め、ランタイムがそれを駆動する。仕様に問題があれば、コードで回避せずにワークフロー定義を直す。フレームワークで表せないことがあれば、ハーネスの中で回避せず、フレームワークの不足として報告する。

## 2. ワークフロー定義を書く

形は schema/workflow.schema.json で決まる。examples/toy-minimal/workflow.yaml が実例。

### 2.1 終了状態の三層（goal、end_state、unknown）

ステージの結果は必ず次のどれか一つに落ちる。

- **goal**（正常系）: ステージの目的を達した状態
  - quantitative は決定論的な指標と基準
  - qualitative は自然言語の記述
- **end\_state**（準正常系）: 目的を達していないが、どこへ戻れば直せるかが分かっている状態
  - 自然言語で書く
  - 各クラスに戻り先（rollback）が一つずつある
- **unknown**（例外系）: どちらでもない状態。人間に差し戻す（escalate）
  - すべてのステージの end\_state に `unknown` を必ず入れる
  - unknown には rollback を付けない

記述の書き方:

- **観測できる条件として書く。** 分類器が見るのは、そのステージの reads と writes のファイルの内容と、memory\_out の値だけ（契約 2.4）。そこから判断できない条件は書かない
- **goal と end\_state と unknown を合わせて、漏れなく重なりなく分ける。** end\_state を goal の言い換えにしない
- **二つのクラスに当てはまりうるなら、記述の中に優先を書く。** たとえば「この状態は X に優先する」「goal に優先する」。優先順は記述の一部で、別の属性は無い
- **戻り先が直すのに使う情報は、記憶（memory\_out）に書かせ、その記憶を証拠として記述に書く。** 戻るとファイルは捨てられ、carry で運べるのは記憶だけだから
- `goal` と `unknown` は予約語。end\_state の id に `goal` は使えない

### 2.2 成果物の宣言（artifacts）

各ステージに次の四つを宣言する。

- `reads`: 読むファイル。ワークフローの `inputs` か、前のステージの `writes` にあるもの
- `writes`: 書くファイル
- `memory_in`: 受け取る記憶
- `memory_out`: 生成する記憶

パスの規則:

- 作業領域からの相対パスで、字義どおりに書く。glob は使えない
- `/` で終わるパスはディレクトリ全体を表す
- `writes` に無い範囲内のパスを変えると、契約違反になる

宣言から導かれるもの:

- スナップショットの範囲は、`inputs` と全ステージの `writes` の和
- 分類器に渡す状態文書は、宣言から作る

### 2.3 rollback、carry、max

end\_state ごとに、rollback を一つずつ書く。

- **戻り先**: そのステージ自身か、それより前のステージ
  - 自分自身を戻り先にすると、carry を持ってそのステージをやり直せる
- **carry**: 戻り先へ持ち帰る記憶の項目。元ステージの `memory_out` と、戻り先の `memory_in` の両方に書く
- **max**: その辺を通れる回数。1 以上の整数
  - 超えたら escalate する
  - 回数は戻っても元に戻らない

戻る時の動き:

- 戻り先の直近の開始時スナップショットを復元する
- その上に carry の項目だけを重ねる
- 戻った区間で作られたファイルと記憶は捨てる

### 2.4 フェーズゲート

フェーズの goal も、quantitative と qualitative を持つ。フェーズの最終ステージが goal に達した直後に、ゲートとして評価する。

- **指標**: 最終ステージの終了時のスナップショット全体を測る
- **分類**: 選択肢は、フェーズの goal と、最終ステージの end\_state
- **不合格の時**: 最終ステージの end\_state に分類されればその rollback に従い、どれにも当たらなければ unknown になる
  - ゲートの不合格を自動で戻したいなら、最終ステージの end\_state の記述に、フェーズ全体の不足として観測できる条件を含める
  - goal に達した時にも、carry に使う記憶を書いておく
- **フェーズ境界を越えて戻った時**: そのフェーズのゲートは未通過に戻り、再び最終ステージに達した時に評価し直す

### 2.5 ユーザー回答待ち（awaits\_user）

ステージ本体がユーザーに尋ねることがあるなら、`awaits_user: true` を宣言する。宣言の無いステージはユーザー入出力を使えない。回答待ちは end\_state にしない。ランタイムが実行を中断し、回答を得て再開する。

### 2.6 指標

quantitative のキーが指標名で、値が基準になる。

- 基準は `description` と、`equals`（真偽値か数）または `min` / `max`（数）
- `args` で実装に引数を渡せる
- 比較はフレームワークが行い、ハーネスは測るだけ
- 測定できない指標は未達として扱う

ワークフロー定義に、N 回実行して何割といった分布の基準を書かない。それはテストの側（expectations）に置く。

### 2.7 拡張属性

ハーネス固有の付加情報は、`x-` で始まる属性に書ける。それ以外の知らない属性は、スキーマが拒む。

## 3. 整合性検査を通す

ワークフロー定義を直すたびに検査を通す。

```sh
python -m harness_testing_framework.testing.spec workflow.yaml --registry パッケージ.モジュール:レジストリ
```

検査する性質:

- 参照整合（id の重複、rollback の参照先、読むファイルの出どころ）
- unknown を除く end\_state と rollback の一対一
- 戻り先の前方性（自分自身か前）
- max の存在と有界性
- carry の生成と消費
- 指標がレジストリにあること
- unknown の存在
- 指標の基準の範囲

違反が一つでもあれば終了コード 1 になる。記憶が生成されても使われない場合は警告で、終了コードは 0。参照ランタイムの `load_workflow` も、違反のある定義を拒む。

指標レジストリの渡し方は二つある。

- `--registry MODULE:ATTR`: `names()` を持つオブジェクト。MODULE は import できる名前で書く（必要なら `PYTHONPATH` にパッケージの親ディレクトリを加える）
- `--metrics-file FILE`: `metrics: [指標名, ...]` だけを持つ YAML。レジストリの実装より先に、ワークフロー定義だけを検査したい時に使う

## 4. 指標レジストリを実装する

`MetricRegistry` を満たすオブジェクトを一つ用意する（実例は examples/toy-minimal/toy\_minimal/metrics.py）。

- `names()`: 実装している指標名の一覧
- `measure(name, view, args)`: 真偽値か数を返す
  - view は読み取り専用のスナップショット（`SnapshotView`）
  - 測れなければ `MetricError` を送出する

ビルドやテストの実行のような実在のツールに裏づけられた指標も、ここに実装する。

- ツールを走らせるには、一時ディレクトリに `view.list_files()` と `view.read_bytes(path)` でファイルを書き出し、そこでツールを実行して結果を値にする
- 前後を比べる指標（変更されたパスの範囲など）には、`view.baseline()` を使う。ステージの指標ならそのステージの開始時、フェーズの指標ならフェーズの最初のステージの開始時のスナップショットが返る
- 指標は同じスナップショットに対して同じ値を返すように書く（記録再生と分布テストの前提）

## 5. ステージ本体を実装する

ステージ本体は `StageContext` を受け取る関数（またはそれを満たす呼び出し可能なオブジェクト）。ワークフロー定義を読んでから書く。

`context` が提供するもの:

- `workspace`: 作業領域。ランタイムが毎回スナップショットから作る
- `read_memory(name)`、`write_memory(name, value)`: memory\_in / memory\_out に宣言した記憶
- `seed`: 確率的な振る舞いの唯一の乱数の源
- `user_io`: awaits\_user のステージだけ
- `llm`: LLM クライアント。必ずこれを通す（記録再生のため）

契約違反になること:

- 宣言外の記憶を読み書きする
- 範囲内で writes に無いパスを変える（削除を含む）
- awaits\_user の無いステージでユーザー入出力を使う

違反と、本体の例外は、評価をせずに escalate される。宣言した writes を書かなかったことは違反にならず、指標と分類で扱われる。

## 6. ユーザー入出力、分類器、運用者、LLM を束縛する

- **ユーザー入出力**（`UserIO.ask`）: 回答を返すか、まだ無いなら `AwaitingAnswer` を送出する。テストではユーザーシミュレータを束縛する
- **分類器**（`Classifier.classify(state, options)`）: 状態文書と選択肢を受け取り、選んだ id と確信度を返す
  - 選択肢はワークフロー定義の記述そのもの。分類のための規則をコードに書かない
  - 閾値は、分類器の較正結果から決める
  - 状態文書の先頭行が評価の対象を示す（`# 評価: stage <id> visit <n>` か `# 評価: phase <id> visit <n>`）
- **運用者**（`Operator.decide(escalation)`）: escalate の時に、四つの選択肢から一つを返す
  - 再実行
  - 指定ステージへのロールバック
  - goal 到達扱いで続行
  - 中止

  まだ選べないなら `AwaitingDecision` を送出する
- **LLM クライアント**（`LLMClient.complete(request)`）: request と response は JSON で表せる値

## 7. ランタイムを組み立てて実行する

参照ランタイムを組み込む場合の最小の組み立て。玩具のワークフローに、決まった成果物を書く本体と、台本どおりの分類器と運用者を束縛して、最後まで走らせる。

```python
# 実行できる例
import os
from pathlib import Path

from harness_testing_framework.runtime import BlobStore, Runtime, load_workflow
from harness_testing_framework.testing.harness import ScriptedClassifier, ScriptedOperator
from toy_minimal.metrics import REGISTRY

workdir = Path(os.environ.get("WORKDIR", "work"))
workflow = load_workflow(Path("examples/toy-minimal/workflow.yaml"), REGISTRY.names())
fixtures = Path("examples/toy-minimal/tests/fixtures")


def copy_fixture(name):
    def body(context):
        for path in (fixtures / name).iterdir():
            (context.workspace / path.name).write_bytes(path.read_bytes())

    return body


bodies = {
    "ask_topic": copy_fixture("ask_topic/ok"),
    "plan_outline": copy_fixture("plan_outline/ok"),
    "write_note": copy_fixture("write_note/ok"),
    "review_note": copy_fixture("review_note/ok"),
}
goal = {"choice": "goal", "confidence": 0.9}
classifier = ScriptedClassifier(
    {f"{stage}#1": goal for stage in bodies}, {"intake#1": goal, "compose#1": goal}
)
runtime = Runtime(
    workflow,
    bodies,
    registry=REGISTRY,
    classifier=classifier,
    operator=ScriptedOperator([]),
    store=BlobStore(workdir / "store"),
    workdir=workdir,
    threshold=0.5,
)
result = runtime.start(seed=0, inputs={"brief.txt": "議事録の書き方をまとめてほしい".encode()})
assert result.status == "completed", result.status
```

`Runtime` の引数:

| 引数 | 内容 | 既定値 |
| --- | --- | --- |
| `workflow` | `load_workflow` で読んだワークフロー | （必須） |
| `bodies` | ステージの id からステージ本体への対応 | （必須） |
| `registry` | 指標レジストリ | （必須） |
| `classifier` | 分類器 | （必須） |
| `operator` | 運用者 | （必須） |
| `store` | スナップショットの置き場（`BlobStore(ディレクトリ)`）。再開では同じものを使う | （必須） |
| `workdir` | 作業領域を作るディレクトリ。各ステージの作業領域は実行の後に消える | （必須） |
| `user_io` | ユーザー入出力。awaits\_user のステージが無ければ不要 | なし |
| `llm` | LLM クライアント | なし |
| `threshold` | 分類の確信度の閾値。これ未満は unknown | 0.5 |
| `recorder` | 記録再生（`Passthrough`、`Recording`、`ReplayOnly`） | `Passthrough()` |
| `state_limit` | 状態文書の長さの上限（文字数） | 20000 |

最後のスナップショットは `runtime.snapshot(result.state.current)` で取り出せる。ファイルの内容は `store.get(snapshot.files[パス])` で読める。

実行が中断（`suspended`）か escalate 待ち（`awaiting_operator`）で止まったら、次のように再開する。

1. `result.state.to_json()` で状態を保存する。中断なら `state.pending["question"]` に保留中の質問（文と選択肢）がある
2. 必要なら別のプロセスで、`RunState.from_json` で状態を読み戻す
3. 同じ置き場（`BlobStore`）を使うランタイムを組み立てる
4. 中断なら `resume(state, answer=...)`、escalate 待ちなら `resume(state, decision=...)` を呼ぶ

実行記録（出来事の列）は `result.events` にあり、形は contract/trace.schema.json で決まっている。条件を満たさない運用者の選択は拒まれ、実行は escalate 待ちに戻る。

### 7.1 記録再生

外から入る値（LLM の応答、ユーザーの回答、運用者の選択、分類器の結果、指標の値）は、すべて recorder を通る。

- `Recording(path)` を束縛すると記録する
- `ReplayOnly(path)` を束縛すると、記録だけから再生する
  - 記録に無い呼び出しは `ReplayOnly.Missing` で止まる
  - 同じ種と入力なら、同じスナップショットの列になる

テストで LLM を呼ぶ時は、必ず記録してから再生を使う。

## 8. 決定論テストをシナリオで書く

ハーネスのロジック（遷移、ゲート、ロールバック）は、偽のステージ本体と台本で決定論的に確かめる。

シナリオの書き方:

- 形は contract/conformance/scenario.schema.json で決まっている。書き方と実行記録の要約の規則は contract/conformance/README.md にある
- 実例は examples/toy-minimal/tests/scenarios/
- `visits["<ステージ>#<訪問の回数>"]` に、その訪問で本体がすること（`fixture` を写す、`files` を書く、`memory` を書く、`ask` で尋ねる、`raise`）と、分類の結果（`classify`）を書く
- `gates["<フェーズ>#<最終ステージの訪問の回数>"]` に、ゲートの分類の結果を書く
- `operator` と `user` に、選択と回答の台本を書く。`defer` は保留
- `expect.trace` に、期待する実行記録の要約を書く。**実装より先に書く**
- 戻りのあるシナリオでは、`expect.starts["<ステージ>#<訪問>"]` に、その訪問の開始時スナップショット（ファイルの内容、記憶、ゲート）を書く。要約だけでは、戻った時に何が復元されたかを確かめられない
- 必要なら `expect.options["stage:<ステージ>#<訪問>"]` に評価の選択肢の並びを書く

シナリオの実行のしかた:

- `run_scenario(load_scenario(path), workdir, registry=..., fixtures=...)` で実行する。結果の `problems` が空なら期待どおり（食い違いが一行ずつ入る）
- 実例は examples/toy-minimal/toy\_minimal/stages/deterministic.py と tests/test\_scenarios.py

### 8.1 遷移の六種と escalate の四択

決定論テストは、ワークフローの上で次の六種の遷移をすべて通す。`transition_coverage(trace)` で確かめられる。

1. next（完了を含む）
2. rollback
3. max 超過による escalate
4. unknown による escalate（本体の例外と契約違反を含む）
5. 中断と再開
6. フェーズ境界を越えるロールバックと、ゲートの再評価

escalate の四つの選択（再実行、指定ステージへのロールバック、goal 到達扱いで続行、中止）も、それぞれ一度は通す。

## 9. 契約適合テスト

参照ランタイムを使わず、自前のランタイムを用意する場合（他の言語など）は、contract/conformance/scenarios/ のすべてのシナリオを通す。ハーネスが契約を満たしているかは、このテストでのみ判定する。

手順は contract/conformance/README.md にある。偽物の振る舞いと、実行記録の要約の規則が書かれている。スナップショットの id の計算（マニフェストの正規形）は、契約の第5節にある。

## 10. サブワークフローは扱わない

実行時に数の決まる子の作業（例: タスク分割で生じた N 個の実装）は、そのステージの本体の内部ループとして書く。フレームワークが三層で判定するのは、ステージの成果物だけ。

- 子ごとの分類、回数の上限、記録は、ステージ本体が自分で持つ
- 子の結果は、ステージの成果物と記憶にまとめる
- 親ステージの end\_state の記述は、まとめた成果物から観測できる条件で書く

子ワークフローを契約に含めることは、将来の版の候補。

## 11. このリポジトリの中にワークフローを作る場合

examples/<名前>/ に次のように置けば、設定を直さずに検査に乗る。

- `examples/<名前>/workflow.yaml`: ワークフロー定義
- `examples/<名前>/<パッケージ>/`: 指標レジストリ、ステージ本体、ユーザーシミュレータなどの Python のパッケージ。テストから `import <パッケージ>` で読める（リポジトリの最上位の conftest.py が examples/<名前>/ を import パスに加える）
- `examples/<名前>/tests/test_*.py`: テスト。`scripts/check.sh` の pytest が拾う
- `examples/<名前>/tests/fixtures/`、`examples/<名前>/tests/scenarios/`: フィクスチャとシナリオ

`scripts/check.sh` は、ruff、pytest、型検査（mypy の strict。examples/<名前>/ ごとに別に走らせる）をすべて実行し、CI も同じものを呼ぶ。型検査に通るように、関数に型注釈を付ける。

## 12. 分布テスト（expectations）

LLM を使うステージの振る舞いは毎回揺れる。ハーネスのロジックは決定論テストで確かめ、LLM の振る舞いの分布は分布テストで確かめる。

- **基準の置き場:** 「N 回実行して何割」という基準は、ワークフロー定義に書かず expectations に書く。形は contract/formats/expectations.schema.json で、実例は examples/toy-minimal/tests/expectations/
  - `runs`: 実行の回数
  - `seed`: 最初の種。i 回目は seed + i
  - `bindings`: ハーネスが実行を組み立てるための自由な情報
  - `criteria`: 基準の一覧。基準は次の三種類
    - `outcome_rate`: あるステージ（`scope: stage`、既定）かフェーズのゲート（`scope: phase`）の評価のうち、結果が `outcome` の割合。分母は条件に合う評価の数。`visit` でその訪問だけ、`from_visit` でその訪問以降に絞れる。ゲートの評価の訪問は、フェーズの最終ステージの訪問の回数
    - `status_rate`: 実行の最後の状態の割合。分母は実行の数
    - `mean_visits`: ステージを訪れる回数の平均
  - 各基準の `min_samples`（既定 30）: 分母がこれ未満なら判定できず、通らない
- **判定の規則:** 観測した値が [min, max] に入れば通る。報告（`ExpectationReport.lines()`）には Wilson の 95% 区間とその幅が付く。区間が基準の幅より広ければ、実行の回数が足りない
- **幅の決め方:** 期待する割合 p と、条件に合う評価の数の期待値 E[n] から、標準誤差 sqrt(p(1-p)/E[n]) を出し、p の両側にその 3 倍ほどをとる
  - 幅は回数に依存するので、expectations に回数（`runs`）と幅の根拠を注記として書く
  - 「80% 以上」のような片側の基準でも、真の割合がちょうど 0.80 なら約半分の確率で落ちる。下限は、許せる最低の割合から標準誤差の 3 倍ほど下げて置く
- **実行のしかた:** ハーネスは、種を受けて一回実行する関数を用意する。中身は `record_run(runtime, seed, inputs)` を呼ぶもので、`run_many` で回し、`evaluate_expectations` で判定する。escalate には中止で答える運用者（`AbortOperator`）を、ユーザーには `AutoUser` かユーザーシミュレータを束縛する
- **回数:** 環境変数 `HTF_RUNS` で増やせる。幅は expectations の回数から決めてあるので、減らすことはできない
- **LLM を使う時:**
  - 分布テストは、人間が明示的に許可した時だけ実行する（コストのため）
  - LLM の呼び出しは recorder を通す
- **基準を設定・変更する時:** 実装した人とは別の検証役に、基準の根拠と設計値を見せて確かめてもらう

## 13. 独立性検証と遷移行列

end\_state のクラスは、下流の振る舞いに関する同値類として作る。同じクラスに入る違う成果物（代表）からは、下流の分布が揃うはず。揃わなければ、クラスが粗すぎる。

- **代表:** `record_run` が、ステージが書いた成果物の内容のハッシュを、評価ごとに記録する
- **`transition_matrix(runs)`:** 評価の結果から、次の評価の結果（または実行の終わり）への遷移の経験分布
- **次の状態:** 評価の後に続くゲートの評価（あれば `>` でつなぐ）と、その次のステージの評価の結果。フェーズの最終ステージの goal でも、次のフェーズの最初のステージまで見る
- **`independence(runs)`:** 状態と訪問の区分（既定 cap 2）の組ごとに、代表どうしで次の状態の分布が違うかを、カイ二乗統計量の並べ替え検定で判定する
  - 既定値: alpha 0.01、並べ替え 2000 回、種 0、代表ごとに 10 件以上
  - 判定は次の三つ
    - `not_detected`: この件数では違いを検出しなかった。揃うことの証明ではない。代表ごとに数十件では、0.15 程度の違いはほとんど検出できない
    - `violated`: 違う（p 値が alpha 未満）
    - `undetermined`: 十分な件数のある代表が二つ未満
  - 状態ごとに独立に検定し、多重性の補正はしない
- **代表の鍵:** 既定（成果物のハッシュ）は、偽の本体のように同じ成果物が繰り返し出る時に向く。LLM の出力では毎回違うので、そのままではいつも `undetermined` になる。意味の近い成果物を同じ鍵にまとめる関数を、`record_run(..., representative=...)` に与える
- **violated が出たら:** クラスを分ける提案を書く。クラスの粒度は、この検証の結果でのみ変える。分類体系の変更は人間の承認が要る

## 14. E2E のカバレッジ計画とマルコフ合成

E2E では、各ステージの各クラス（goal、end\_state、unknown）を一度は踏む。組み合わせは網羅しない。

- **`coverage_targets(workflow)`:** 踏むべき (ステージ, クラス)
- **`plan_coverage(...)`:** 計画を作る
  - ステージごとの goal の台本と、(ステージ, クラス) ごとの誘発の台本（その状態を実際に表す成果物を書かせる）を与える
  - 誘発の台本が無いクラスは、注入（分類の結果だけを変える）で踏む
  - `run_coverage` で実行し、`missing` が空なら全部踏めた
- **マルコフ合成:**
  - `estimate_model(runs, cap)` は、(ステージ, 訪問の区分) ごとのクラスの分布を推定する。訪問の番号は cap（既定 2）以上を一つにまとめる。観測の無い区分では、下の区分の分布を使う
  - `synthesize(model, workflow)` は、遷移規則をたどって、完了の確率、訪問の回数、評価の結果ごとの回数の期待値を厳密に計算する。escalate の後は中止とする
  - `compare_prediction` で、別の実行の集まりの実測と比べる。差が標準誤差の k 倍（既定 4）以内なら一致
  - 予測と実測が合わない時は、クラスの分布が (ステージ, 訪問) だけでは決まっていない（マルコフ性が成り立たない）疑いがある

## 15. 分類器の検証

分類器の確信度の閾値は、人手のラベルとの一致率と較正の結果から決める。ベンダーの主張は自分のコーパスで確かめる。

1. **コーパスを作る:** `build_corpus(runs, store, workflow)` で、実行記録から、分類器が見た状態文書と選択肢の項目を作る（置き場に状態文書が残っている）。`save_corpus` で JSON Lines に書く
2. **人手でラベルを付ける:** 形は contract/formats/label.schema.json。ラベルは項目の選択肢のどれか
3. **レポートを出す:** `oracle_report(classifier, corpus, labels)` は次を出す
   - Cohen の κ
   - 混同行列
   - ECE（確信度を等幅 10 区間に分ける。区間は左閉じで、最後の区間だけ 1 を含む。答えた項目だけで計算する）
   - 答えた割合と、答え無しの件数。分類器の例外、0〜1 の有限の数でない確信度、選択肢に無い id は答え無しとする（ランタイムと同じ）
   - 対象（ステージやフェーズ）ごとの κ と ECE
   - 再実行の一致率（同じ項目を何度か分類して答えが揃う割合）
4. **レポートを人間が見て閾値を決める:** 閾値と、その根拠（レポート）を記録する。これは高リスクの検証なので、実装した人とは別の検証役を通す

`ConfusionClassifier` と `FlakyClassifier` は、既知の混同行列と揺れを持つ偽の分類器で、レポートの計算を確かめるのに使う。

## 16. トリアージ

unknown と確信度の低い評価は、待ち行列に入れて人が判定する。

- **`enqueue(queue, run, review_below=閾値)`:** 待ち行列（JSON Lines、慣例として reports/triage/）に足す
  - 確信度が閾値と等しいものは足さない（閾値未満だけ）
  - 項目の id は、実行の一意な id（実行記録の内容のハッシュ）と評価の seq。同じ実行を二度足しても重ならない。同じ種でも設定が違う実行は別の項目になる
  - 項目は状態文書の SHA-256 を持ち、内容は置き場で読める
- **`decide(queue, record, Decision(...))`:** 判定を記録する。判定の種類は次のとおり
  - `label`: 正しいクラスを付ける
  - `not_a_problem`
  - `classifier_error`
  - `new_class_proposal`、`description_revision_proposal`: 分類体系の変更の提案。ワークフロー定義は変えず、人間の承認を待つ
- **`open_items(queue, record)`:** 判定のまだ無い項目
- **判定の使い道:** ラベルを付けた項目は、分類器の検証のコーパスに足せる
