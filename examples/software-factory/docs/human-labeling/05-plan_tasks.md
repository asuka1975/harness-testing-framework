# 人がラベルを付ける材料（5 / 10）: ステージ plan_tasks

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（04-design.md）を付け終えるまで、このファイル（05-plan_tasks.md）を開かない
- このファイルを付け終えるまで、次のファイル（06-architecture-gate.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
