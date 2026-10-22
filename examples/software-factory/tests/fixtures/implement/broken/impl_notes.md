[[class implement=quality_violation]]
# 実装の記録

## 変更
- T1: repo/src/shopcart/discount.py に、割引コードの読み取りと適用を足した
- T2: repo/src/shopcart/cart.py に、Cart.total を足した

## 違反
- ビルド: repo/src/shopcart/discount.py の parse_code の定義に構文の誤りがあり、byte-compile と import に失敗する

## 問い
（なし）
