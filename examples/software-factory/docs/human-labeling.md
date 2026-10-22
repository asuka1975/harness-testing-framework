# 人がラベルを付ける材料

ワークフロー定義の記述（選択肢の記述）だけを読んで、各項目の状態文書がどの選択肢に当たるかを選んでもらうための材料
（adopting.md 第15.1節）。手で書くのは各項目の「ラベル:」の行だけで、ほかは直さない。

項目の選び方は README にある。ラベルを付け終えるまで README の「記述と代表の整合」を読まない。README のほかの節、docs/ の
ほかの文書、tests/ と software\_factory/ の下にも、代表がどの選択肢に当たるかが書いてあるので、ラベルを付け終えるまで
この文書のほかは開かない（比べる時のコーパス docs/human-labeling.corpus.jsonl とフィクスチャには、分類器が読む印が残って
いる）。

## 読み方

方針:

- 分類器と同じ立場で選ぶ。記述を字義どおりに読み、状態文書から判断できることだけで選ぶ
- 記述が中身の条件（テストが通る、要件どおり、など）を書いていれば、状態文書の中身（コード、テスト、回答など）を確かめる。
  書いていなければ確かめない
- 記述の括弧の中の列挙は、記述が書いた範囲として読む
- 迷ったら unknown を選び、理由を一行添える（例: `ラベル: unknown（REQ-3 の根拠が回答に無い）`）。ほかの選択肢にも理由を
  添えてよい。理由は「ラベル:」と同じ行に書く。理由は比べる時には使わないが、食い違いを直す時に読む

事実:

- 各項目の「状態文書」は、分類器が見たもの（そのステージの reads と writes のファイルの内容と、memory\_out の記憶。ゲートの
  項目はフェーズの全体）から、偽の本体が書いた印を除いたもの。指標の値は入っていない。指標が落ちた評価では、goal が選べる
  選択肢に無い
- goal が選べる選択肢に無い時は、選択肢の記述の「goal に優先する」という文は働かない
- 「（なし）」などの置き書きは、空の節として数える
- 訪問 2 以降の項目は、戻りの後に入り直した評価。持ち帰った記憶（memory\_in）そのものは状態文書に入らない。戻りの後の
  状態文書（intake の訪問 2 以降と、それより後の評価）では、intake.md の「## 質問と回答」に持ち帰った問いとその回答が入る
- 印を除いた跡（review.json の `"marker": ""` のような空の値）が残るが、意味は無い。印だけの行は落としてある
- 項目の番号と、対象の中の並びに意味は無い

## 見せ方

- 項目は対象（ステージか、フェーズのゲート）ごとの節にある。節の頭に、選択肢の記述（ワークフロー定義の記述そのもの）を
  一度だけ示す。各項目には、その項目で選べる選択肢の id を示す
- 対象の項目の半分より多くで同じ区切り（「## ファイル …」と「## 記憶 …」）は、節の頭に一度だけ示す。項目の状態文書では、
  それと同じ区切りを、見出しに「（共通）」を付けて、分類器が見た順の位置に示す。「（共通）」の付かない区切りは、その項目の
  全文を示す

## ラベルの書き方と、付けた後

- 当てはまる選択肢の id を一つ、「ラベル:」と同じ行に書く（例: `ラベル: goal`）。コロンは全角でもよい
- 付け終えたら、examples/software-factory/ で次を実行する（リポジトリの根で実行すると `No module named 'software_factory'`
  になる）
  1. `uv run python -m software_factory.labeling labels --labeler <名前>`: この文書の「ラベル:」から docs/human-labels.jsonl
     （contract/formats/label.schema.json の形）を作る。空の「ラベル:」は数えて報告し、「ラベル:」の後が空で次の行に文が
     ある時は警告する。読めないラベルと、選べる選択肢に無い id は、項目の番号を添えた誤りにする（終了コード 2）
  2. `uv run python -m software_factory.labeling compare`: ラベルを印（ゲートは goal）と比べ、食い違う項目を番号で挙げる
- `uv run python -m software_factory.labeling write` は材料を作り直し、埋めた「ラベル:」を空にする（付け始めた後は、
  付け直す範囲を決めてから実行する）

## ステージ intake

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: intake.md の「## 質問と回答」のすべての質問に回答があり、回答どうしも、回答と feature_request.md の依頼も矛盾せず、「## 依頼」が feature_request.md の依頼を要約している。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル feature_request.md
# 依頼: 買い物かごに割引コードを入れたい

shopcart ライブラリの Cart に、割引コードを適用した支払額を出す機能を足してほしい。
来月のキャンペーンで「10% 引き」と「500 円引き」のコードを配る予定。
~~~~~~

### 項目 1

対象: ステージ intake の訪問 1

選べる選択肢: `goal`、`unknown`

状態文書:

~~~~~~text
# 評価: stage intake visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
割引コードの機能か、ポイントの機能か、feature_request.md と回答のどちらに従うか決められない。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
（判断できない）
~~~~~~

ラベル:

### 項目 2

対象: ステージ intake の訪問 1

選べる選択肢: `goal`、`unknown`

状態文書:

~~~~~~text
# 評価: stage intake visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う
~~~~~~

ラベル:

### 項目 3

対象: ステージ intake の訪問 2

選べる選択肢: `goal`、`unknown`

状態文書:

~~~~~~text
# 評価: stage intake visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う
~~~~~~

ラベル:

### 項目 4

対象: ステージ intake の訪問 2

選べる選択肢: `goal`、`unknown`

状態文書:

~~~~~~text
# 評価: stage intake visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
割引コードの機能か、ポイントの機能か、feature_request.md と回答のどちらに従うか決められない。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
（判断できない）
~~~~~~

ラベル:

## ステージ analyze

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: requirements.md の「## 要件」に三つ以上の要件があり、各要件に観測できる受け入れ基準が一つ以上あって、どの要件も feature_request.md か intake.md の回答に根拠を持つ。「## 未決事項」に問いが無い。
- `needs_unclear`: intake.md の回答だけでは要件を決められない（上限や境界の値が決まっていない、回答が曖昧）。決められない点が、依頼者に 尋ねるべき問いとして記憶 intake_questions に列挙され、requirements.md の「## 未決事項」にも同じ問いがある。 requirements.md に要件が三つ以上あっても、intake_questions に問いが列挙されていればこの状態とし、goal に優先する。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル feature_request.md
# 依頼: 買い物かごに割引コードを入れたい

shopcart ライブラリの Cart に、割引コードを適用した支払額を出す機能を足してほしい。
来月のキャンペーンで「10% 引き」と「500 円引き」のコードを配る予定。

## 記憶 intake_questions
[]
~~~~~~

### 項目 5

対象: ステージ analyze の訪問 2

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 6

対象: ステージ analyze の訪問 5

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 5

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 7

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 8

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

### 項目 9

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 10

対象: ステージ analyze の訪問 3

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 3

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

### 項目 11

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

### 項目 12

対象: ステージ analyze の訪問 1

選べる選択肢: `needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 割引コードの機能を足す

## 未決事項
（判断できない）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 13

対象: ステージ analyze の訪問 2

選べる選択肢: `needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 割引コードの機能を足す

## 未決事項
（判断できない）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 14

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 15

対象: ステージ analyze の訪問 1

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

### 項目 16

対象: ステージ analyze の訪問 2

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 17

対象: ステージ analyze の訪問 2

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

### 項目 18

対象: ステージ analyze の訪問 4

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: stage analyze visit 4

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
- キャンペーンが終わった後も、割引コードを使えるようにしますか
- 同じ購入者が同じコードを何回でも使えるようにしますか

## 記憶 intake_questions
["キャンペーンが終わった後も、割引コードを使えるようにしますか", "同じ購入者が同じコードを何回でも使えるようにしますか"]
~~~~~~

ラベル:

## フェーズ discovery のゲート

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: requirements.md の各要件が、feature_request.md の依頼か intake.md の回答に根拠を持ち、intake.md の回答（利用者、割引の種類と上限、 無効なコードの扱い）がすべて requirements.md の要件か受け入れ基準に反映されている。
- `needs_unclear`: intake.md の回答だけでは要件を決められない（上限や境界の値が決まっていない、回答が曖昧）。決められない点が、依頼者に 尋ねるべき問いとして記憶 intake_questions に列挙され、requirements.md の「## 未決事項」にも同じ問いがある。 requirements.md に要件が三つ以上あっても、intake_questions に問いが列挙されていればこの状態とし、goal に優先する。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル feature_request.md
# 依頼: 買い物かごに割引コードを入れたい

shopcart ライブラリの Cart に、割引コードを適用した支払額を出す機能を足してほしい。
来月のキャンペーンで「10% 引き」と「500 円引き」のコードを配る予定。

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## 記憶 intake_questions
[]
~~~~~~

### 項目 19

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 1 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 20

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 1 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 21

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 5 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 5

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 22

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 2 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 23

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 1 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

### 項目 24

対象: フェーズ discovery のゲート（フェーズの最終ステージの訪問 2 の後）

選べる選択肢: `goal`、`needs_unclear`、`unknown`

状態文書:

~~~~~~text
# 評価: phase discovery visit 2

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## 記憶 intake_questions（共通）
~~~~~~

ラベル:

## ステージ design

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: design.md の「## 対応」が requirements.md のすべての要件を「## 構成」にある構成要素に割り当てていて、構成要素が repo/ の既存のコードと矛盾しない。「## 要件への問い」に問いが無い。
- `requirements_gap`: requirements.md の要件に、曖昧なもの、互いに矛盾するもの、repo/ の既存のコードでは実現の仕方が決まらないものがあり、 design.md の「## 対応」がその要件を割り当てていないか、暫定の解釈で割り当てたうえで「## 要件への問い」に問いを 残している。その要件と、決めるのに要ることが、記憶 requirement_gaps と design.md の「## 要件への問い」に列挙されて いる。「## 対応」がすべての要件を割り当てていても、requirement_gaps に問いが列挙されていればこの状態とし、goal に 優先する。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## 記憶 requirement_gaps
[]
~~~~~~

### 項目 25

対象: ステージ design の訪問 1

選べる選択肢: `goal`、`requirements_gap`、`unknown`

状態文書:

~~~~~~text
# 評価: stage design visit 1

## ファイル requirements.md（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と、小計に割引を適用する Discount.apply
- repo/src/shopcart/cart.py（変更）: Cart.total(code=None) が小計に割引を適用する

## 対応
- REQ-1: Discount.apply の百分率の分岐。割引額を切り捨ててから小計から引く
- REQ-2: Discount.apply の定額の分岐。支払額の下限を 0 円にする
- REQ-3: parse_code が、購入者がレジの画面で入力したコード（文字列で受け取る。画面は repo/ の外）の形式と百分率の範囲を検査し、ValueError を送出する
- REQ-4: Cart.total はコードが無ければ小計を返す

## 要件への問い
（なし）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 26

対象: ステージ design の訪問 1

選べる選択肢: `requirements_gap`、`unknown`

状態文書:

~~~~~~text
# 評価: stage design visit 1

## ファイル requirements.md（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル design.md
# 設計

## 構成
（未完）

## 対応
（未完）

## 要件への問い
（判断できない）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 27

対象: ステージ design の訪問 1

選べる選択肢: `requirements_gap`、`unknown`

状態文書:

~~~~~~text
# 評価: stage design visit 1

## ファイル requirements.md（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と Discount.apply

## 対応
- REQ-1: Discount.apply の百分率の分岐
- REQ-2: Discount.apply の定額の分岐

## 要件への問い
- REQ-3 と REQ-4 は、コードを Cart のどの操作で受け取るか（追加の時か、支払いの時か）を決めておらず、設計できない

## 記憶 requirement_gaps
["REQ-3 と REQ-4: コードを Cart のどの操作で受け取るかが決まっていない"]
~~~~~~

ラベル:

## ステージ plan_tasks

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: tasks.yaml のタスクが requirements.md のすべての要件を扱い、各タスクの paths が design.md の「## 構成」のファイルに 収まり、tests が repo/tests/ の下にあり、タスクどうしで paths が重ならない。
- `design_incomplete`: design.md の「## 構成」に、要件を受け持つ構成要素か、変えるファイルが欠けていて、tasks.yaml のタスクにすべての要件を 割り当てられない。欠けている点が記憶 design_issues に列挙されている（tasks.yaml の先頭の注記にもある）。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と、小計に割引を適用する Discount.apply
- repo/src/shopcart/cart.py（変更）: Cart.total(code=None) が小計に割引を適用する

## 対応
- REQ-1: Discount.apply の百分率の分岐。割引額を切り捨ててから小計から引く
- REQ-2: Discount.apply の定額の分岐。支払額の下限を 0 円にする
- REQ-3: parse_code が、購入者がレジの画面で入力したコード（文字列で受け取る。画面は repo/ の外）の形式と百分率の範囲を検査し、ValueError を送出する
- REQ-4: Cart.total はコードが無ければ小計を返す

## 要件への問い
（なし）

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## 記憶 design_issues
[]
~~~~~~

### 項目 28

対象: ステージ plan_tasks の訪問 1

選べる選択肢: `design_incomplete`、`unknown`

状態文書:

~~~~~~text
# 評価: stage plan_tasks visit 1

## ファイル requirements.md（共通）

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と Discount.apply

## 対応
- REQ-1: Discount.apply の百分率の分岐
- REQ-2: Discount.apply の定額の分岐

## 要件への問い
- REQ-3 と REQ-4 は、コードを Cart のどの操作で受け取るか（追加の時か、支払いの時か）を決めておらず、設計できない

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル tasks.yaml
# design.md の「## 構成」に、REQ-3 と REQ-4 を受け持つ構成要素（コードを受け取る Cart の操作）と、変えるファイル
# （repo/src/shopcart/cart.py）が無い。REQ-3 と REQ-4 は、どのタスクにも割り当てていない
tasks:
  - id: T1
    title: 割引コードの適用
    requirements: [REQ-1, REQ-2]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]

## 記憶 design_issues
["REQ-3 と REQ-4: design.md の「## 構成」に、コードを受け取る Cart の操作と、変えるファイル（repo/src/shopcart/cart.py）が無く、どのタスクにも割り当てられない"]
~~~~~~

ラベル:

### 項目 29

対象: ステージ plan_tasks の訪問 1

選べる選択肢: `goal`、`design_incomplete`、`unknown`

状態文書:

~~~~~~text
# 評価: stage plan_tasks visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## 記憶 design_issues（共通）
~~~~~~

ラベル:

### 項目 30

対象: ステージ plan_tasks の訪問 1

選べる選択肢: `goal`、`design_incomplete`、`unknown`

状態文書:

~~~~~~text
# 評価: stage plan_tasks visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル tasks.yaml
# 二つのタスクが同じ repo/src/shopcart/cart.py を paths に持ち、どちらのタスクがどの変更を受け持つかが決まらない
tasks:
  - id: T1
    title: 割引コードと支払額
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py, repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: コード無しの支払額
    requirements: [REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## 記憶 design_issues（共通）
~~~~~~

ラベル:

## フェーズ architecture のゲート

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: design.md の構成と tasks.yaml のタスクが対応し、requirements.md のすべての要件が、design.md の「## 対応」と、タスクの requirements の両方で扱われている。
- `design_incomplete`: design.md の「## 構成」に、要件を受け持つ構成要素か、変えるファイルが欠けていて、tasks.yaml のタスクにすべての要件を 割り当てられない。欠けている点が記憶 design_issues に列挙されている（tasks.yaml の先頭の注記にもある）。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

### 項目 31

対象: フェーズ architecture のゲート（フェーズの最終ステージの訪問 1 の後）

選べる選択肢: `goal`、`design_incomplete`、`unknown`

状態文書:

~~~~~~text
# 評価: phase architecture visit 1

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と、小計に割引を適用する Discount.apply
- repo/src/shopcart/cart.py（変更）: Cart.total(code=None) が小計に割引を適用する

## 対応
- REQ-1: Discount.apply の百分率の分岐。割引額を切り捨ててから小計から引く
- REQ-2: Discount.apply の定額の分岐。支払額の下限を 0 円にする
- REQ-3: parse_code が、購入者がレジの画面で入力したコード（文字列で受け取る。画面は repo/ の外）の形式と百分率の範囲を検査し、ValueError を送出する
- REQ-4: Cart.total はコードが無ければ小計を返す

## 要件への問い
（なし）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## 記憶 design_issues
[]
~~~~~~

ラベル:

## ステージ implement

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: impl_notes.md の「## 変更」が tasks.yaml のすべてのタスクについて repo/src/ の変更を述べ、「## 違反」と「## 問い」が 空で、repo/src/ の変更が design.md の構成どおりである。
- `task_unclear`: tasks.yaml のタスクの記述が曖昧か、タスクの paths の外のファイルを変えないと実装できず、repo/src/ をどう変えるかを 決められない。決められない点が、タスクの id とともに記憶 task_questions と impl_notes.md の「## 問い」に列挙されて いる。repo/src/ の変更の有無や指標の結果によらず、task_questions と「## 問い」の両方に問いが列挙されていればこの状態と し、goal と quality_violation に優先する。
- `quality_violation`: repo/src/ が、byte-compile か import に失敗する、repo/tests/ の既存のテストを落とす、lint（ruff の E、F、W）の違反が ある、tasks.yaml のタスクの paths に無いファイルを変えている、または design.md の「## 構成」から外れている。違反の 内容が記憶 impl_violations と impl_notes.md の「## 違反」に列挙されている（どのファイルが変わったかは状態からは 見えないので、変更の範囲の違反はこの列挙で判断する）。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と、小計に割引を適用する Discount.apply
- repo/src/shopcart/cart.py（変更）: Cart.total(code=None) が小計に割引を適用する

## 対応
- REQ-1: Discount.apply の百分率の分岐。割引額を切り捨ててから小計から引く
- REQ-2: Discount.apply の定額の分岐。支払額の下限を 0 円にする
- REQ-3: parse_code が、購入者がレジの画面で入力したコード（文字列で受け取る。画面は repo/ の外）の形式と百分率の範囲を検査し、ValueError を送出する
- REQ-4: Cart.total はコードが無ければ小計を返す

## 要件への問い
（なし）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""

from shopcart.discount import parse_code


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

    def total(self, code: str | None = None) -> int:
        """割引コードを適用した支払額。コードが無ければ小計。"""
        subtotal = self.subtotal()
        if code is None:
            return subtotal
        return parse_code(code).apply(subtotal)

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## 記憶 task_questions
[]

## 記憶 impl_violations
[]
~~~~~~

### 項目 32

対象: ステージ implement の訪問 1

選べる選択肢: `task_unclear`、`quality_violation`、`unknown`

状態文書:

~~~~~~text
# 評価: stage implement visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal * (100 - self.percent) // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code}")

## ファイル repo/tests/test_cart.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、割引コードの読み取りと適用を足した
- T2: repo/src/shopcart/cart.py に、Cart.total を足した

## 違反
- ビルド: repo/src/shopcart/discount.py の parse_code の定義に構文の誤りがあり、byte-compile と import に失敗する

## 問い
（なし）

## テストへの依頼
（なし）

## 記憶 task_questions（共通）

## 記憶 impl_violations
["ビルド: discount.py の parse_code の定義に構文の誤りがある"]
~~~~~~

ラベル:

### 項目 33

対象: ステージ implement の訪問 1

選べる選択肢: `goal`、`task_unclear`、`quality_violation`、`unknown`

状態文書:

~~~~~~text
# 評価: stage implement visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal * (100 - self.percent) // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount:
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code}")

## ファイル repo/tests/test_cart.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1、T2 を実装したつもりだが、どの要件に対応するかは書いていない

## 違反
（判断できない）

## 問い
（判断できない）

## テストへの依頼
（なし）

## 記憶 task_questions（共通）

## 記憶 impl_violations（共通）
~~~~~~

ラベル:

### 項目 34

対象: ステージ implement の訪問 1

選べる選択肢: `goal`、`task_unclear`、`quality_violation`、`unknown`

状態文書:

~~~~~~text
# 評価: stage implement visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード（正規表現で読む版）。"""

import re
from dataclasses import dataclass

_CODE = re.compile(r"(PCT|OFF)([0-9]+)")


@dataclass(frozen=True)
class Discount:
    kind: str
    value: int

    def apply(self, subtotal: int) -> int:
        if self.kind == "PCT":
            return subtotal * (100 - self.value) // 100
        return max(subtotal - self.value, 0)


def parse_code(code: str) -> Discount:
    match = _CODE.fullmatch(code)
    if match is None:
        raise ValueError(f"unknown code: {code}")
    kind, value = match.group(1), int(match.group(2))
    if kind == "PCT" and not 1 <= value <= 50:
        raise ValueError(f"percent out of range: {code}")
    return Discount(kind, value)

## ファイル repo/tests/test_cart.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、正規表現で割引コードを読む parse_code と、種類と値を持つ Discount を足した
- T2: repo/src/shopcart/cart.py に、割引を適用した支払額（Cart.total）を足した

## 違反
（なし）

## 問い
（なし）

## テストへの依頼
（なし）

## 記憶 task_questions（共通）

## 記憶 impl_violations（共通）
~~~~~~

ラベル:

### 項目 35

対象: ステージ implement の訪問 1

選べる選択肢: `goal`、`task_unclear`、`quality_violation`、`unknown`

状態文書:

~~~~~~text
# 評価: stage implement visit 1

## ファイル requirements.md（共通）

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

## ファイル repo/tests/test_cart.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
（なし）

## 違反
（なし）

## 問い
- T2 は Cart.total を足すとあるが、割引を小計に適用するのか、商品ごとに適用するのかが tasks.yaml から決められない

## テストへの依頼
（なし）

## 記憶 task_questions
["T2: 割引を小計に適用するのか、商品ごとに適用するのかが tasks.yaml から決められない"]

## 記憶 impl_violations（共通）
~~~~~~

ラベル:

## ステージ unit_test

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `impl_defect`: repo/tests/ のテストの一部が失敗し、その期待が requirements.md の受け入れ基準か要件の記述に従っている（テストではなく repo/src/ が誤っている）。失敗したテストと、それが示す repo/src/ の欠陥が、記憶 failing_tests と test_report.md の 「## 失敗」に列挙されている。tests_insufficient に優先する。
- `tests_insufficient`: unit_test 自身が直すべき不足か不備がある: requirements.md の受け入れ基準のうちテストの無いもの、repo/src/ の実行され ない箇所（行カバレッジが 80% に届かない）、repo/tests/ の lint の違反、tasks.yaml のタスクの tests に無いファイルの 変更、requirements.md の要件に反する期待を持つテスト。その不足か不備が、記憶 coverage_gaps と test_report.md の 「## 未網羅」に列挙されている。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""

from shopcart.discount import parse_code


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

    def total(self, code: str | None = None) -> int:
        """割引コードを適用した支払額。コードが無ければ小計。"""
        subtotal = self.subtotal()
        if code is None:
            return subtotal
        return parse_code(code).apply(subtotal)

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## ファイル repo/tests/test_discount.py
import pytest
from shopcart.cart import Cart
from shopcart.discount import parse_code


def _cart(subtotal: int) -> Cart:
    cart = Cart()
    cart.add("item", subtotal)
    return cart


def test_percent_code_takes_percentage_off() -> None:
    assert _cart(1000).total("PCT10") == 900


def test_amount_code_takes_amount_off() -> None:
    assert _cart(1000).total("OFF500") == 500


def test_amount_code_never_goes_below_zero() -> None:
    assert _cart(300).total("OFF500") == 0


def test_no_code_pays_subtotal() -> None:
    assert _cart(440).total() == 440


@pytest.mark.parametrize("code", ["PCT0", "PCT51", "XYZ", "OFF"])
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        parse_code(code)


def test_amount_code_subtracts_the_whole_amount() -> None:
    # 定額のコードは、小計を超えても額をそのまま引く
    assert _cart(300).total("OFF500") == -200

## ファイル test_report.md
# 単体テストの記録

## テスト
- repo/tests/test_discount.py: REQ-1〜REQ-4 の受け入れ基準を確かめる（百分率、定額、0 円の下限、コード無し、無効なコード）。あわせて、定額のコードが小計を超えた時の支払額を確かめる

## 失敗
（なし）

## 未網羅
- test_amount_code_subtracts_the_whole_amount: 小計 300 円に OFF500 で -200 円を期待しているが、REQ-2 は支払額が 0 円を下回らない（受け入れ基準は 0 円）。期待が要件に反するので、このテストは落ちる。repo/src/ ではなくテストが誤っている

## 記憶 failing_tests
[]

## 記憶 coverage_gaps
["repo/tests/test_discount.py の test_amount_code_subtracts_the_whole_amount: 小計 300 円に OFF500 で -200 円を期待しているが、REQ-2 は支払額が 0 円を下回らない（受け入れ基準は 0 円）。期待が要件に反するので、このテストは落ちる"]
~~~~~~

### 項目 36

対象: ステージ unit_test の訪問 1

選べる選択肢: `impl_defect`、`tests_insufficient`、`unknown`

状態文書:

~~~~~~text
# 評価: stage unit_test visit 1

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal * (100 - self.percent) // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount:
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code}")

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、割引コードの読み取り（parse_code）と適用（Discount.apply）を足した
- T2: repo/src/shopcart/cart.py に、割引を適用した支払額（Cart.total）を足した

## 違反
（なし）

## 問い
（なし）

## テストへの依頼
（なし）

## ファイル test_report.md（共通）

## 記憶 failing_tests（共通）

## 記憶 coverage_gaps（共通）
~~~~~~

ラベル:

### 項目 37

対象: ステージ unit_test の訪問 1

選べる選択肢: `impl_defect`、`tests_insufficient`、`unknown`

状態文書:

~~~~~~text
# 評価: stage unit_test visit 1

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード（正規表現で読む版）。"""

import re
from dataclasses import dataclass

_CODE = re.compile(r"(PCT|OFF)([0-9]+)")


@dataclass(frozen=True)
class Discount:
    kind: str
    value: int

    def apply(self, subtotal: int) -> int:
        if self.kind == "PCT":
            return subtotal * (100 - self.value) // 100
        return max(subtotal - self.value, 0)


def parse_code(code: str) -> Discount:
    match = _CODE.fullmatch(code)
    if match is None:
        raise ValueError(f"unknown code: {code}")
    kind, value = match.group(1), int(match.group(2))
    if kind == "PCT" and not 1 <= value <= 50:
        raise ValueError(f"percent out of range: {code}")
    return Discount(kind, value)

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、正規表現で割引コードを読む parse_code と、種類と値を持つ Discount を足した
- T2: repo/src/shopcart/cart.py に、割引を適用した支払額（Cart.total）を足した

## 違反
（なし）

## 問い
（なし）

## テストへの依頼
（なし）

## ファイル test_report.md（共通）

## 記憶 failing_tests（共通）

## 記憶 coverage_gaps（共通）
~~~~~~

ラベル:

### 項目 38

対象: ステージ unit_test の訪問 1

選べる選択肢: `impl_defect`、`tests_insufficient`、`unknown`

状態文書:

~~~~~~text
# 評価: stage unit_test visit 1

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal - subtotal * self.percent // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount:
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code}")

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル impl_notes.md
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、割引コードの読み取り（parse_code）と適用（Discount.apply）を足した。百分率の割引は、割引額を切り捨ててから小計から引く
- T2: repo/src/shopcart/cart.py に、割引を適用した支払額（Cart.total）を足した

## 違反
（なし）

## 問い
（なし）

## テストへの依頼
（なし）

## ファイル test_report.md（共通）

## 記憶 failing_tests（共通）

## 記憶 coverage_gaps（共通）
~~~~~~

ラベル:

## ステージ acceptance

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: verification.md の表が requirements.md のすべての要件を挙げてすべて合格で、「## 依頼との食い違い」が空である。
- `requirement_misread`: verification.md の「## 依頼との食い違い」に、requirements.md の要件（またはその欠落）が feature_request.md の依頼か intake.md の回答と食い違う点があり、その点が記憶 requirement_gaps に列挙されている。表の結果によらず、 requirement_gaps に食い違いが列挙されていればこの状態とし、goal と requirement_unmet に優先する。
- `requirement_unmet`: verification.md の表で一つ以上の要件が不合格で、その要件と、要件の記述か受け入れ基準に反する repo/ の振る舞いが、 記憶 unmet_requirements と verification.md の「## 不合格の内容」に列挙されている。requirements.md の要件そのものは 依頼と食い違っていない。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル feature_request.md
# 依頼: 買い物かごに割引コードを入れたい

shopcart ライブラリの Cart に、割引コードを適用した支払額を出す機能を足してほしい。
来月のキャンペーンで「10% 引き」と「500 円引き」のコードを配る予定。

## ファイル requirements.md
# 要件

## 要件
- REQ-1: 百分率の割引コード PCTnn（nn は 1〜50）で、小計から nn% を引く。割引額の 1 円未満は切り捨てる
  - 受け入れ基準: 小計 1000 円に PCT10 で 900 円
- REQ-2: 定額の割引コード OFFnnn（nnn は円）で、小計から nnn 円を引く。支払額は 0 円を下回らない
  - 受け入れ基準: 小計 1000 円に OFF500 で 500 円
  - 受け入れ基準: 小計 300 円に OFF500 で 0 円
- REQ-3: 購入者（店のお客さん）がレジの画面で入力したコードのうち、形式に合わないものと、範囲外の百分率は ValueError で拒む
  - 受け入れ基準: PCT0、PCT51、XYZ、OFF は ValueError
- REQ-4: コードを渡さなければ、支払額は小計に等しい
  - 受け入れ基準: 小計 440 円でコード無しなら 440 円

## 未決事項
（なし）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""

from shopcart.discount import parse_code


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

    def total(self, code: str | None = None) -> int:
        """割引コードを適用した支払額。コードが無ければ小計。"""
        subtotal = self.subtotal()
        if code is None:
            return subtotal
        return parse_code(code).apply(subtotal)

## ファイル repo/src/shopcart/discount.py
"""割引コード（正規表現で読む版）。"""

import re
from dataclasses import dataclass

_CODE = re.compile(r"(PCT|OFF)([0-9]+)")


@dataclass(frozen=True)
class Discount:
    kind: str
    value: int

    def apply(self, subtotal: int) -> int:
        if self.kind == "PCT":
            return subtotal * (100 - self.value) // 100
        return max(subtotal - self.value, 0)


def parse_code(code: str) -> Discount:
    match = _CODE.fullmatch(code)
    if match is None:
        raise ValueError(f"unknown code: {code}")
    kind, value = match.group(1), int(match.group(2))
    if kind == "PCT" and not 1 <= value <= 50:
        raise ValueError(f"percent out of range: {code}")
    return Discount(kind, value)

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## ファイル repo/tests/test_discount.py
import pytest
from shopcart.cart import Cart
from shopcart.discount import parse_code


def _cart(subtotal: int) -> Cart:
    cart = Cart()
    cart.add("item", subtotal)
    return cart


def test_percent_code_takes_percentage_off() -> None:
    assert _cart(1000).total("PCT10") == 900


def test_amount_code_takes_amount_off() -> None:
    assert _cart(1000).total("OFF500") == 500


def test_amount_code_never_goes_below_zero() -> None:
    assert _cart(300).total("OFF500") == 0


def test_no_code_pays_subtotal() -> None:
    assert _cart(440).total() == 440


@pytest.mark.parametrize("code", ["PCT0", "PCT51", "XYZ", "OFF"])
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        parse_code(code)

## ファイル test_report.md
# 単体テストの記録

## テスト
- repo/tests/test_discount.py: REQ-1〜REQ-4 の受け入れ基準を確かめる（百分率、定額、0 円の下限、コード無し、無効なコード）

## 失敗
（なし）

## 未網羅
（なし）

## 記憶 unmet_requirements
[]

## 記憶 requirement_gaps
[]
~~~~~~

### 項目 39

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 40

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 41

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 42

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 43

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 44

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 45

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 46

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 47

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py
"""割引コード。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal * (100 - self.percent) // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount:
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code}")

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 48

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps
["requirements.md にコードの大文字と小文字の扱いが無く、入力された pct10 を拒む"]
~~~~~~

ラベル:

### 項目 49

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 50

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 51

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 52

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 53

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 54

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 55

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 56

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 57

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 58

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 59

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: お客さん全般かな。レジの画面でコードを打ってもらう感じ
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。割り引く額の端数は切り捨てで、引きすぎたら 0 円でいい
- Q: 使えないコードが入力された時はどうしますか
  A: 使えないコードはエラーにして、割引しないで
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: そのうち考えるよ
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: うーん、まだ決めてない

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 60

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: 未定
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 未定（後で決める）

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements
["REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"]

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 61

対象: ステージ acceptance の訪問 1

選べる選択肢: `goal`、`requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: 購入者。レジの画面で入力
- Q: 配る割引コードの種類と上限は何ですか
  A: PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円
- Q: 使えないコードが入力された時はどうしますか
  A: ValueError

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

### 項目 62

対象: ステージ acceptance の訪問 1

選べる選択肢: `requirement_misread`、`requirement_unmet`、`unknown`

状態文書:

~~~~~~text
# 評価: stage acceptance visit 1

## ファイル feature_request.md（共通）

## ファイル intake.md
# 取り込み

## 依頼
shopcart の Cart に、割引コードを適用した支払額を出す機能を足す（feature_request.md）。

## 質問と回答
- Q: この機能を使うのは誰ですか
  A: ネットショップの購入者。レジの画面でコードを入力する
- Q: 配る割引コードの種類と上限は何ですか
  A: PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする
- Q: 使えないコードが入力された時はどうしますか
  A: エラーにして、割引しない
- Q: キャンペーンが終わった後も、割引コードを使えるようにしますか
  A: キャンペーンの結果を見て、来月の末に決める
- Q: 同じ購入者が同じコードを何回でも使えるようにしますか
  A: 回数の制限は、法務と相談してから決める

## 制約
- 金額は円の整数で扱う

## ファイル requirements.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル test_report.md（共通）

## ファイル verification.md
# 検証

## 要件ごとの結果
（実行できなかった）

## 依頼との食い違い
（判断できない）

## 記憶 unmet_requirements（共通）

## 記憶 requirement_gaps（共通）
~~~~~~

ラベル:

## ステージ review

選択肢の記述（この対象のどの項目でも同じ。各項目には、その項目で選べる選択肢の id を示す）:

- `goal`: review.json の reviewed が tasks.yaml のタスクの paths と tests をすべて含み、修正を要する指摘が一つも無い。
- `design_flaw`: review.json に修正を要する指摘があり、そのうち一つ以上が、design.md の構成かインターフェースを変えなければ解消しない。 その指摘が記憶 design_issues に列挙されている。changes_requested に優先する。
- `changes_requested`: review.json に修正を要する指摘が一つ以上あり、そのすべてが repo/src/ か repo/tests/ の修正で解消する（design.md は 変えなくてよい）。その指摘が記憶 review_findings に列挙されている。フェーズ assurance の評価では、修正を要する指摘が 無くても、修正を要しない指摘を verification.md の結果と合わせると repo/ を直してからリリースすべきで、その指摘が review_findings に列挙されている場合も、この状態とする。
- `unknown`: 上記に当てはまらない、または分類の確信度が低い。人間に差し戻す。

この対象の項目に共通の区切り（項目の状態文書で、見出しに「（共通）」を付けた区切りは、これと同じ）:

~~~~~~text
## ファイル design.md
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と、小計に割引を適用する Discount.apply
- repo/src/shopcart/cart.py（変更）: Cart.total(code=None) が小計に割引を適用する

## 対応
- REQ-1: Discount.apply の百分率の分岐。割引額を切り捨ててから小計から引く
- REQ-2: Discount.apply の定額の分岐。支払額の下限を 0 円にする
- REQ-3: parse_code が、購入者がレジの画面で入力したコード（文字列で受け取る。画面は repo/ の外）の形式と百分率の範囲を検査し、ValueError を送出する
- REQ-4: Cart.total はコードが無ければ小計を返す

## 要件への問い
（なし）

## ファイル tasks.yaml
tasks:
  - id: T1
    title: 割引コードの読み取りと適用
    requirements: [REQ-1, REQ-2, REQ-3]
    paths: [repo/src/shopcart/discount.py]
    tests: [repo/tests/test_discount.py]
  - id: T2
    title: 割引を適用した支払額
    requirements: [REQ-1, REQ-2, REQ-4]
    paths: [repo/src/shopcart/cart.py]
    tests: [repo/tests/test_discount.py]

## ファイル repo/src/shopcart/__init__.py
"""小さな買い物かごのライブラリ。"""

__version__ = "0.1.0"

## ファイル repo/src/shopcart/cart.py
"""買い物かご。金額は円の整数。"""

from shopcart.discount import parse_code


class Cart:
    def __init__(self) -> None:
        self.items: dict[str, tuple[int, int]] = {}

    def add(self, sku: str, price: int, qty: int = 1) -> None:
        if qty <= 0:
            raise ValueError("qty must be positive")
        _, held = self.items.get(sku, (price, 0))
        self.items[sku] = (price, held + qty)

    def remove(self, sku: str) -> None:
        self.items.pop(sku, None)

    def subtotal(self) -> int:
        return sum(price * qty for price, qty in self.items.values())

    def total(self, code: str | None = None) -> int:
        """割引コードを適用した支払額。コードが無ければ小計。"""
        subtotal = self.subtotal()
        if code is None:
            return subtotal
        return parse_code(code).apply(subtotal)

## ファイル repo/src/shopcart/discount.py
"""割引コード（正規表現で読む版）。"""

import re
from dataclasses import dataclass

_CODE = re.compile(r"(PCT|OFF)([0-9]+)")


@dataclass(frozen=True)
class Discount:
    kind: str
    value: int

    def apply(self, subtotal: int) -> int:
        if self.kind == "PCT":
            return subtotal * (100 - self.value) // 100
        return max(subtotal - self.value, 0)


def parse_code(code: str) -> Discount:
    match = _CODE.fullmatch(code)
    if match is None:
        raise ValueError(f"unknown code: {code}")
    kind, value = match.group(1), int(match.group(2))
    if kind == "PCT" and not 1 <= value <= 50:
        raise ValueError(f"percent out of range: {code}")
    return Discount(kind, value)

## ファイル repo/tests/test_cart.py
import pytest
from shopcart.cart import Cart


def test_subtotal_sums_price_times_quantity() -> None:
    cart = Cart()
    cart.add("apple", 120, 2)
    cart.add("pear", 200)
    assert cart.subtotal() == 440


def test_remove_drops_the_item() -> None:
    cart = Cart()
    cart.add("apple", 120)
    cart.add("apple", 120)
    cart.remove("apple")
    assert cart.subtotal() == 0


def test_add_rejects_nonpositive_quantity() -> None:
    with pytest.raises(ValueError):
        Cart().add("apple", 120, 0)

## ファイル repo/tests/test_discount.py
import pytest
from shopcart.cart import Cart
from shopcart.discount import parse_code


def _cart(subtotal: int) -> Cart:
    cart = Cart()
    cart.add("item", subtotal)
    return cart


def test_percent_code_takes_percentage_off() -> None:
    assert _cart(1000).total("PCT10") == 900


def test_amount_code_takes_amount_off() -> None:
    assert _cart(1000).total("OFF500") == 500


def test_amount_code_never_goes_below_zero() -> None:
    assert _cart(300).total("OFF500") == 0


def test_no_code_pays_subtotal() -> None:
    assert _cart(440).total() == 440


@pytest.mark.parametrize("code", ["PCT0", "PCT51", "XYZ", "OFF"])
def test_invalid_codes_are_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        parse_code(code)

## ファイル verification.md
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
（なし）

## 記憶 design_issues
[]
~~~~~~

### 項目 63

対象: ステージ review の訪問 1

選べる選択肢: `goal`、`design_flaw`、`changes_requested`、`unknown`

状態文書:

~~~~~~text
# 評価: stage review visit 1

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル verification.md（共通）

## ファイル review.json
{"marker": "", "reviewed": ["repo/src/shopcart/discount.py", "repo/src/shopcart/cart.py", "repo/tests/test_discount.py"], "findings": [{"path": "repo/src/shopcart/discount.py", "blocking": false, "comment": "parse_code の docstring にコードの形式の例があると読みやすい"}]}

## 記憶 review_findings
["（修正を要しない）parse_code の docstring にコードの形式の例があると読みやすい"]

## 記憶 design_issues（共通）
~~~~~~

ラベル:

### 項目 64

対象: ステージ review の訪問 1

選べる選択肢: `design_flaw`、`changes_requested`、`unknown`

状態文書:

~~~~~~text
# 評価: stage review visit 1

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル verification.md（共通）

## ファイル review.json
{"marker": "", "reviewed": ["repo/src/shopcart/discount.py", "repo/src/shopcart/cart.py", "repo/tests/test_discount.py"], "findings": [{"path": "repo/tests/test_discount.py", "blocking": true, "comment": "test_invalid_codes_are_rejected は無効なコード（PCT0、PCT51、XYZ、OFF）を parse_code に直接渡すだけで、Cart.total に無効なコードを渡した時に ValueError で拒むこと（REQ-3）を確かめていない。Cart.total で確かめるテストを足す"}]}

## 記憶 review_findings
["repo/tests/test_discount.py: 無効なコード（PCT0、PCT51、XYZ、OFF）を Cart.total に渡した時に ValueError で拒むこと（REQ-3）を確かめるテストが無い（parse_code だけを確かめている）"]

## 記憶 design_issues（共通）
~~~~~~

ラベル:

### 項目 65

対象: ステージ review の訪問 1

選べる選択肢: `design_flaw`、`changes_requested`、`unknown`

状態文書:

~~~~~~text
# 評価: stage review visit 1

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル verification.md（共通）

## ファイル review.json
{"marker": "", "reviewed": ["repo/src/shopcart/discount.py", "repo/src/shopcart/cart.py", "repo/tests/test_discount.py"], "findings": [{"path": "repo/src/shopcart/discount.py", "blocking": true, "comment": "design.md が割引の種類を Discount の分岐で表しており、種類を足すたびに apply を直すことになる。種類ごとの型に分ける設計にする"}]}

## 記憶 review_findings
[]

## 記憶 design_issues
["割引の種類を Discount の分岐で表しており、種類を足すたびに apply を直すことになる"]
~~~~~~

ラベル:

### 項目 66

対象: ステージ review の訪問 1

選べる選択肢: `goal`、`design_flaw`、`changes_requested`、`unknown`

状態文書:

~~~~~~text
# 評価: stage review visit 1

## ファイル design.md（共通）

## ファイル tasks.yaml（共通）

## ファイル repo/src/shopcart/__init__.py（共通）

## ファイル repo/src/shopcart/cart.py（共通）

## ファイル repo/src/shopcart/discount.py（共通）

## ファイル repo/tests/test_cart.py（共通）

## ファイル repo/tests/test_discount.py（共通）

## ファイル verification.md（共通）

## ファイル review.json
{"marker": "", "reviewed": [], "findings": [{"path": "repo/", "blocking": false, "comment": "どこを見ればよいか判断できない"}]}

## 記憶 review_findings
[]

## 記憶 design_issues（共通）
~~~~~~

ラベル:
