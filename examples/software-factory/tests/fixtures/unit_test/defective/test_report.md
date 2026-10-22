[[class unit_test=tests_defective]]
# 単体テストの記録

## テスト
- repo/tests/test_discount.py: REQ-1〜REQ-4 の受け入れ基準を確かめる（百分率、定額、0 円の下限、コード無し、無効なコード）。あわせて、定額のコードが小計を超えた時の支払額を確かめる

## 失敗
（なし）

## 不備
- test_amount_code_subtracts_the_whole_amount: 小計 300 円に OFF500 で -200 円を期待しているが、REQ-2 は支払額が 0 円を下回らない（受け入れ基準は 0 円）。期待が要件に反するので、このテストは落ちる。repo/src/ ではなくテストが誤っている

## 未網羅
（なし）
