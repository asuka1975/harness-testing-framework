[[class design=requirements_gap]]
# 設計

## 構成
- repo/src/shopcart/discount.py（新規）: 割引コードを読む parse_code と Discount.apply

## 対応
- REQ-1: Discount.apply の百分率の分岐
- REQ-2: Discount.apply の定額の分岐

## 要件への問い
- REQ-3 と REQ-4 は、コードを Cart のどの操作で受け取るか（追加の時か、支払いの時か）を決めておらず、設計できない
