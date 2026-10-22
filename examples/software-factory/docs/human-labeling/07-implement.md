# 人がラベルを付ける材料（7 / 10）: ステージ implement

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（06-architecture-gate.md）を付け終えるまで、このファイル（07-implement.md）を開かない
- このファイルを付け終えるまで、次のファイル（08-unit_test.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
