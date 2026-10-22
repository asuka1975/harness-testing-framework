# 人がラベルを付ける材料（9 / 10）: ステージ acceptance

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（08-unit_test.md）を付け終えるまで、このファイル（09-acceptance.md）を開かない
- このファイルを付け終えるまで、次のファイル（10-review.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
