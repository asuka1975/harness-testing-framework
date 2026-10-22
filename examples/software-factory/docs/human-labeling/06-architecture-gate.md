# 人がラベルを付ける材料（6 / 10）: フェーズ architecture のゲート

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（05-plan_tasks.md）を付け終えるまで、このファイル（06-architecture-gate.md）を開かない
- このファイルを付け終えるまで、次のファイル（07-implement.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
