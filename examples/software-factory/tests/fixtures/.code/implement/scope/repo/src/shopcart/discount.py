"""割引コード。"""

from dataclasses import dataclass

from shopcart.utils import numeric_suffix


@dataclass(frozen=True)
class Discount:
    """百分率（percent）か定額（amount）のどちらか一方の割引。"""

    percent: int = 0
    amount: int = 0

    def apply(self, subtotal: int) -> int:
        if self.percent:
            return subtotal * (100 - self.percent) // 100
        return max(subtotal - self.amount, 0)


def parse_code(code: str) -> Discount:
    """PCTnn（nn は 1〜50）か OFFnnn を割引にする。形式に合わなければ ValueError。"""
    percent = numeric_suffix(code, "PCT")
    if percent is not None:
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    amount = numeric_suffix(code, "OFF")
    if amount is not None:
        return Discount(amount=amount)
    raise ValueError(f"unknown code: {code}")
