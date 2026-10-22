[[class implement=quality_violation]]
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、割引コードの読み取りと適用を足した
- T2: repo/src/shopcart/cart.py に、Cart.total を足した

## 違反
- lint: repo/src/shopcart/discount.py に使っていない import（os）と、100 文字を超える行がある

## 問い
（なし）
