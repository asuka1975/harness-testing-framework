"""toy-minimal の指標レジストリ（契約 7.2）。"""

import json
import re
from collections.abc import Callable, Collection, Mapping

from harness_testing_framework.contract import JSONValue, MetricError, SnapshotView

type Measure = Callable[[SnapshotView, Mapping[str, JSONValue]], bool | float]


def _text(view: SnapshotView, path: JSONValue) -> str:
    if not isinstance(path, str) or not view.exists(path):
        raise MetricError(f"{path} が無い")
    return view.read_text(path)


def _outline_sections(text: str) -> list[str]:
    """outline.md の節: 「## 節」の見出しから次の見出しまでの、'- 名前: 要約' の行の名前。"""
    m = re.search(r"^## 節[ \t]*$(.*?)(?=^#|\Z)", text, re.M | re.S)
    if not m:
        return []
    return [s.group(1).strip() for s in re.finditer(r"^- ([^:：\n]+)[:：]", m.group(1), re.M)]


def _note_headings(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", text, re.M)]


def file_nonempty(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    path = args["path"]
    return isinstance(path, str) and view.exists(path) and bool(view.read_text(path).strip())


def files_nonempty(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    paths = args["paths"]
    if not isinstance(paths, list):
        raise MetricError("paths が一覧でない")
    return all(file_nonempty(view, {"path": p}) for p in paths)


def section_count(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    return len(_outline_sections(_text(view, args.get("path"))))


def sections_covered(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    sections = _outline_sections(_text(view, args.get("outline")))
    if not sections:
        raise MetricError("outline に節が無い")
    note = args.get("note")
    headings = set(_note_headings(_text(view, note))) if view.exists(str(note)) else set()
    return sum(1 for s in sections if s in headings) / len(sections)


def blocking_findings(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    try:
        review = json.loads(_text(view, args.get("path")))
        return sum(1 for f in review["findings"] if f["blocking"])
    except (ValueError, KeyError, TypeError) as e:
        raise MetricError(f"review.json の形が違う: {e}") from e


class _Registry:
    def __init__(self, measures: Mapping[str, Measure]) -> None:
        self._measures = dict(measures)

    def names(self) -> Collection[str]:
        return self._measures.keys()

    def measure(self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float:
        if name not in self._measures:
            raise MetricError(f"指標 {name} は無い")
        return self._measures[name](view, args)


REGISTRY = _Registry(
    {
        "file_nonempty": file_nonempty,
        "files_nonempty": files_nonempty,
        "section_count": section_count,
        "sections_covered": sections_covered,
        "blocking_findings": blocking_findings,
    }
)
