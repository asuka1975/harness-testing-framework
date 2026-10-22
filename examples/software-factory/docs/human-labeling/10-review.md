# 人がラベルを付ける材料（10 / 10）: ステージ review

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（09-acceptance.md）を付け終えるまで、このファイル（10-review.md）を開かない
- これが最後のファイル
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
