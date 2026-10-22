[[class implement=goal]]
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
