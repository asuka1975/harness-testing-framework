# 人がラベルを付ける材料（8 / 10）: ステージ unit_test

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（07-implement.md）を付け終えるまで、このファイル（08-unit_test.md）を開かない
- このファイルを付け終えるまで、次のファイル（09-acceptance.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
