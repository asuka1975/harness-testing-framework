[[class acceptance=requirement_unmet]]
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off、小計 333 円に PCT10 を適用する確認 | 不合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-1: 小計 333 円に PCT10 を適用すると、支払額が 299 円になる。要件は割引額（33.3 円）の 1 円未満を切り捨てるので 300 円になるべきだが、repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている。repo/tests/ の単体テストはこの場合を確かめていない

## 依頼との食い違い
（なし）
