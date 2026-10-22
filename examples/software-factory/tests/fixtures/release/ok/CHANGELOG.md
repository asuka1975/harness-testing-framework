[[class release=goal]]
# Changelog

## 0.2.0
- 割引コードを足した。PCTnn で百分率の割引（REQ-1）、OFFnnn で定額の割引（REQ-2、支払額は 0 円が下限）
- 無効なコードは ValueError で拒む（REQ-3）
- Cart.total(code=None) で、割引を適用した支払額を出す。コードが無ければ小計（REQ-4）
