"""割引コード。"""

import os
from dataclasses import dataclass


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
    if code.startswith("PCT") and code[3:].isdigit():
        percent = int(code[3:])
        if not 1 <= percent <= 50:
            raise ValueError(f"percent out of range: {code}")
        return Discount(percent=percent)
    if code.startswith("OFF") and code[3:].isdigit():
        return Discount(amount=int(code[3:]))
    raise ValueError(f"unknown code: {code} (expected PCTnn with nn between 1 and 50, or OFFnnn in yen)")
