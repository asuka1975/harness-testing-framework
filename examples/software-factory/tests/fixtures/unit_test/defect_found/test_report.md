[[class unit_test=impl_defect]]
# 単体テストの記録

## テスト
- repo/tests/test_discount.py: REQ-1〜REQ-4 の受け入れ基準と、REQ-1 の割引額の切り捨てを確かめる

## 失敗
- test_percent_discount_rounds_the_discount_down: 小計 333 円に PCT10 で 299 円になる（REQ-1 では割引額 33.3 円を 33 円に切り捨てるので 300 円）。repo/src/shopcart/discount.py が支払額を切り捨てている

## 不備
（なし）

## 未網羅
（なし）
