# 人がラベルを付ける材料（4 / 10）: ステージ design

読み方は 00-guide.md にある。このファイルで手で書くのは、各項目の「ラベル:」の行だけ。

- 前のファイル（03-discovery-gate.md）を付け終えるまで、このファイル（04-design.md）を開かない
- このファイルを付け終えるまで、次のファイル（05-plan_tasks.md）を開かない
- 付け終えたら、このファイルのラベルを後で変えない（後のファイルを読んでから思い直しても変えない）
- 各項目は、その項目の状態文書と選択肢の記述だけで選ぶ。ほかの項目や、ほかのファイルと見比べない
- 迷ったら unknown を選び、理由を括弧の中に一行添える

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
