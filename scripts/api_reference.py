"""公開 API の引数と属性の一覧（docs/api-reference.md）を、本体の __all__ と docstring から作る。

`uv run python scripts/api_reference.py --write` で書き直す。tests/test_docs.py が、書かれたものと本体が
一致することを確かめる。
"""

import dataclasses
import enum
import importlib
import inspect
import re
import sys
import typing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "docs/api-reference.md"
MODULES = [
    "harness_testing_framework.schema",
    "harness_testing_framework.contract",
    "harness_testing_framework.runtime",
    "harness_testing_framework.testing.spec",
    "harness_testing_framework.testing.harness",
    "harness_testing_framework.testing.stages",
    "harness_testing_framework.testing.e2e",
    "harness_testing_framework.testing.oracle",
    "harness_testing_framework.testing.triage",
]
HEADER = """# 公開 API の引数と属性

公開の名前ごとの引数、属性、戻り値と、その説明（docstring）。scripts/api\\_reference.py が本体から作る。
手で直さない。名前の一覧と使い方は [api.md](api.md) と [adopting.md](adopting.md) にある。
"""


MODULE_PREFIX = re.compile(
    r"\b(?:harness_testing_framework(?:\.\w+)*|pathlib|collections\.abc|collections|typing)\.(?=[A-Za-z_])"
)


def _short(text: str) -> str:
    """型や既定値の表示から、モジュールの道筋とオブジェクトの番地を除く。"""
    text = re.sub(r"<([\w.]+) object at 0x[0-9a-f]+>", r"\1()", text)
    text = re.sub(r"<function ([\w.]+) at 0x[0-9a-f]+>", r"\1", text)
    text = re.sub(r"<class '([\w.]+)'>", r"\1", text)
    return MODULE_PREFIX.sub("", text)


def _signature(obj: object) -> str:
    try:
        return _short(str(inspect.signature(obj)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "(...)"


def _doc(obj: object, indent: str = "") -> list[str]:
    doc = inspect.getdoc(obj)
    if not doc:
        return []
    return [indent + line if line else "" for line in doc.splitlines()]


def _own_doc(cls: type) -> list[str]:
    """クラス自身の docstring（dataclass が自動で付ける署名と、親から継いだものは除く）。"""
    doc = cls.__dict__.get("__doc__")
    if not doc or doc.startswith(f"{cls.__name__}("):
        return []
    return _doc(cls)


def _members(cls: type) -> list[str]:
    lines: list[str] = []
    fields = {f.name for f in dataclasses.fields(cls)} if dataclasses.is_dataclass(cls) else set()
    for name, value in cls.__dict__.items():
        if name.startswith("_") or name in fields:
            continue
        if isinstance(value, property):
            returns = inspect.signature(value.fget).return_annotation if value.fget else None
            shown = (
                ""
                if returns is inspect.Signature.empty
                else f": {_short(inspect.formatannotation(returns))}"
            )
            lines.append(f"- `{name}{shown}`（属性）")
            lines += _doc(value, "  ")
        elif isinstance(value, (staticmethod, classmethod)):
            lines.append(f"- `{name}{_signature(value.__func__)}`")
            lines += _doc(value.__func__, "  ")
        elif inspect.isfunction(value):
            signature = _signature(value).replace("(self, ", "(").replace("(self)", "()")
            lines.append(f"- `{name}{signature}`")
            lines += _doc(value, "  ")
        elif inspect.isclass(value):
            kind = "例外" if issubclass(value, BaseException) else "クラス"
            lines.append(f"- `{name}`（{kind}）")
            lines += ["  " + line if line else "" for line in _own_doc(value)]
    if not dataclasses.is_dataclass(cls) and not issubclass(cls, BaseException):
        for name, annotation in inspect.get_annotations(cls).items():
            if not name.startswith("_"):
                lines.append(f"- `{name}: {_short(inspect.formatannotation(annotation))}`（属性）")
    return lines


def _entry(name: str, obj: object) -> list[str]:
    if isinstance(obj, typing.TypeAliasType):
        return [f"### `{name}`（型）", "", f"`{name} = {_short(str(obj.__value__))}`"]
    if inspect.isclass(obj):
        if issubclass(obj, BaseException):
            bases = ", ".join(b.__name__ for b in obj.__bases__)
            head = [f"### `{name}`（例外。{bases} の一種）"]
        elif issubclass(obj, enum.Enum):
            head = [f"### `{name}`（列挙）", "", ", ".join(f"`{m.name}`" for m in obj)]
        elif getattr(obj, "_is_protocol", False):
            head = [f"### `{name}`（Protocol）"]
        else:
            head = [f"### `{name}{_signature(obj).removesuffix(' -> None')}`"]
        body = _own_doc(obj)
        members = _members(obj)
        return [*head, *(["", *body] if body else []), *(["", *members] if members else [])]
    if callable(obj):
        doc = _doc(obj)
        return [f"### `{name}{_signature(obj)}`", *(["", *doc] if doc else [])]
    shown = repr(obj)
    if len(shown) > 200:
        shown = shown[:200] + " …"
    return [f"### `{name}`", "", f"`{_short(shown)}`"]


def render() -> str:
    out = [HEADER]
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        out.append(f"## `{module_name}`\n")
        for name in sorted(module.__all__, key=str.lower):
            out.append("\n".join(_entry(name, getattr(module, name))) + "\n")
    return "\n".join(out)


if __name__ == "__main__":
    text = render()
    if "--write" in sys.argv:
        TARGET.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
