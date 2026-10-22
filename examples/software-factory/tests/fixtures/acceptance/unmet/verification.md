[[class acceptance=requirement_unmet]]
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off | 不合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 不合格の内容
- REQ-2: 複数の商品の小計 1200 円に OFF500 を二回続けて適用すると、二回目も割り引かれる（コードは一回の支払いに一回）

## 依頼との食い違い
（なし）
