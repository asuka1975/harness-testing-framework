"""コードの文字列の小道具。"""


def numeric_suffix(code: str, prefix: str) -> int | None:
    """code が prefix と数字から成れば、その数字。"""
    rest = code.removeprefix(prefix)
    if code.startswith(prefix) and rest.isdigit():
        return int(rest)
    return None
