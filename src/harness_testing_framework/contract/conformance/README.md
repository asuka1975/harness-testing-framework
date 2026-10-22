# 契約適合テスト

ランタイムの実装が契約（../contract.md）を満たすかを判定する、言語に依存しないテスト。シナリオ（合成のワークフローと、偽の本体・分類器・運用者・ユーザーの台本）と、期待する実行記録の要約の組で書く。参照ランタイムと、ハーネスが自前で用意したランタイムの両方が通す。

判定の対象はランタイムの実装で、ハーネスの本体や指標ではない。参照ランタイムを使うハーネスは、これを自分で通す必要は無い（参照ランタイムはフレームワークの側で通してある）。ハーネスの側が守ること（ステージ本体が宣言の外を変えない、など。契約 第8節）は、ランタイムが実行のたびに検査し、違反は escalate と実行記録に残る。

- workflows/: 合成のワークフロー定義
- scenarios/: シナリオ。形は scenario.schema.json（Python のパッケージに同梱した写しでは、一つ上のディレクトリにある）
- files/: シナリオがファイルの参照で読む内容
- manifests.json: マニフェストの正規形のテストベクトル（契約 第5節）

この一式は Python のパッケージにも同梱してある（`harness_testing_framework.testing.harness.conformance_dir()`）。

## シナリオの実行のしかた

1. `workflow`（シナリオのファイルからの相対パス）を読み、整合性検査を通す
2. 作業領域に、`inputs` のファイルを置いた最初のスナップショットを作る（内容の書き方は下の「ファイルの内容」）
3. 下記の偽物を束縛してランタイムを組み立て、種 `seed` と閾値 `threshold`（省略時 0.5）で実行を始める
4. 実行が中断（suspended）したら `user` の次の項目で、escalate 待ち（awaiting\_operator）になったら `operator` の次の項目で再開する。再開は、保存した実行の状態から新しく組み立てたランタイムで行う
5. 結果を `expect` と比べる
   - 実行記録を下記の規則で要約したものが `expect.trace` と一致する
   - 最後の状態が `expect.status` である
   - `expect.starts` の各訪問について、その訪問の `stage_start` が指すスナップショットの files（パスと内容）、memory、gates が完全に一致する（契約 2.3 の restore と overlay、3.2 のゲートの無効化を確かめる）
   - `expect.options` の各評価について、`evaluation` の選択肢の id の並びが一致する（契約 2.2）
   - `expect.memory` があれば、最後のスナップショットの記憶がそれを含む
   - `expect.annotations` があれば、最後のスナップショットの注記の数が一致する

## ファイルの内容

`inputs` と `expect.starts` の `files` の値は、内容の文字列か、`{from: パス}` で書く。

- `from` はシナリオのファイルからの相対パスで、そのファイルの内容（UTF-8）を読む
- 鍵が `/` で終わる時は、`from` も `/` で終わるディレクトリで、その下のすべてのファイル（下位のディレクトリを含む）を、鍵の下の同じ相対パスに置く
- 同じパスに鍵が重なる時（ディレクトリの鍵と、その下のファイルの鍵や、より深いディレクトリの鍵）は、より長い鍵（そのパスに最も具体的な鍵）の内容になる。鍵の並びにはよらない。ディレクトリの下の一部のファイルだけを差し替える時に使える
- 鍵と `from` の一方だけが `/` で終わる、または指す先が無い場合は、シナリオの誤り

## 偽物

- **本体**: 訪問ごとに `visits["<ステージ id>#<訪問の回数>"]` を読み、次の順に行う。台本に無い訪問は例外で終わる
  1. `ask` の各質問を順にユーザー入出力で尋ねる（再開した訪問では、保存した回答が先に再生される）
  2. `fixture`（ハーネスが与えるフィクスチャの置き場からの相対ディレクトリ）の下のファイルを作業領域に写す
  3. `files` の各パスに内容を書く（null なら削除する）
  4. `answers_to` があれば、1 で得た回答を改行でつないでそのパスに書く
  5. `memory` の各項目を記憶に書く
  6. `raise` が `stage_error` なら例外で終わる
- **分類器**: 状態文書の見出し行（契約 2.4）から評価の対象を読み、ステージなら `visits[...].classify`、フェーズゲートなら `gates["<フェーズ id>#<最終ステージの訪問の回数>"]` を返す。台本に無いか、選んだ id が選択肢に無ければ「答え無し」
- **運用者**: `operator` を先頭から一つずつ使う。`defer` は選択の保留。`continue_as_goal` の `by` は注記の「誰が」（省略時はランタイムが `operator` とする）
- **ユーザー**: `user` を先頭から一つずつ使う。`defer` は回答の保留
- 運用者とユーザーの台本が尽きた時は、シナリオの誤りとしてテストを失敗させる
- **指標レジストリ**（`metrics: conformance` の時）: `flag`（args の path のファイルの内容の前後の空白を除いたものが `true` なら真、それ以外とファイルが無い時は偽）、`number`（path のファイルの内容を数として読む。読めなければ測定の失敗）

## 実行記録の要約

実行記録の各出来事を、次の一行に写す（何も書かないものは要約に現れない）。

| 出来事 | 要約 |
| --- | --- |
| run\_start | （書かない） |
| stage\_start | `start <ステージ>#<訪問>` |
| stage\_end（error あり） | `error <ステージ>#<訪問> <kind>`。error が null なら書かない |
| evaluation | `eval stage <ステージ> = <結果>` または `eval phase <フェーズ> = <結果>` |
| transition next | `next <from> -> <to>` |
| transition rollback | `rollback <from> -> <to> [<state> <回数>]`。運用者の選択による戻り（edge が null）は `[operator]`。フェーズ境界を越えるなら末尾に ` crossing` |
| transition gate\_pass / complete / abort / suspend / resume | `gate_pass <from>`、`complete`、`abort`、`suspend <from>`、`resume <from>` |
| transition escalate | （書かない。escalation が表す） |
| escalation | `escalation <ステージ> <理由> -> <選択の kind>`。保留なら `-> pending` |
| warning | `warning` |
| run\_end | `end <状態>` |
