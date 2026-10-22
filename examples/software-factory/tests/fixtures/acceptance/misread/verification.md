[[class acceptance=requirement_misread]]
# 検証

## 要件ごとの結果
| 要件 | 確かめたテスト | 結果 |
| --- | --- | --- |
| REQ-1 | test_percent_code_takes_percentage_off | 合格 |
| REQ-2 | test_amount_code_takes_amount_off, test_amount_code_never_goes_below_zero | 合格 |
| REQ-3 | test_invalid_codes_are_rejected | 合格 |
| REQ-4 | test_no_code_pays_subtotal | 合格 |

## 依頼との食い違い
- intake.md の回答では、購入者がレジの画面でコードを入力する（requirements.md の REQ-3 にもある）。人が打つコードには大文字と小文字の揺れが出るが、requirements.md の要件にはその扱いが無く、入力された pct10 を拒む
