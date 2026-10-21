# 契約適合テスト

ランタイムの実装が契約（../contract.md）を満たすかを判定する、言語に依存しないテスト。シナリオ（合成のワークフローと、偽の本体・分類器・運用者・ユーザーの台本）と、期待する実行記録の要約の組で書く。参照ランタイムと、ハーネスが自前で用意したランタイムの両方が通す（plan.md 第5.8節）。

- workflows/: 合成のワークフロー定義
- scenarios/: シナリオ。形は scenario.schema.json

## シナリオの実行のしかた

1. `workflow`（シナリオのファイルからの相対パス）を読み、整合性検査を通す
2. 作業領域に、`inputs` のファイルを置いた最初のスナップショットを作る
3. 下記の偽物を束縛してランタイムを組み立て、種 `seed` と閾値 `threshold`（省略時 0.5）で実行を始める
4. 実行が中断（suspended）したら `user` の次の項目で、escalate 待ち（awaiting\_operator）になったら `operator` の次の項目で再開する。再開は、保存した実行の状態から新しく組み立てたランタイムで行う
5. 実行記録を下記の規則で要約し、`expect.trace` と一致すること、最後の状態が `expect.status` であることを確かめる。`expect.memory` があれば、最後のスナップショットの記憶がそれを含むこと、`expect.annotations` があれば注記の数が一致することも確かめる

## 偽物

- **本体**: 訪問ごとに `visits["<ステージ id>#<訪問の回数>"]` を読み、次の順に行う。台本に無い訪問は例外で終わる
  1. `ask` の各質問を順にユーザー入出力で尋ねる
  2. `fixture`（ハーネスが与えるフィクスチャの置き場からの相対ディレクトリ）の下のファイルを作業領域に写す
  3. `files` の各パスに内容を書く（null なら削除する）
  4. `memory` の各項目を記憶に書く
  5. `raise` が `stage_error` なら例外で終わる
- **分類器**: 状態文書の見出し行（契約 2.4）から評価の対象を読み、ステージなら `visits[...].classify`、フェーズゲートなら `gates["<フェーズ id>#<最終ステージの訪問の回数>"]` を返す。台本に無いか、選んだ id が選択肢に無ければ「答え無し」
- **運用者**: `operator` を先頭から一つずつ使う。`defer` は選択の保留
- **ユーザー**: `user` を先頭から一つずつ使う。`defer` は回答の保留
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
