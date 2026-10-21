"""toy-minimal の指標レジストリ。"""

import json
from collections.abc import Sequence

import pytest
from toy_minimal.metrics import REGISTRY

from harness_testing_framework.contract import JSONValue, MetricError


class DictView:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = files

    def exists(self, path: str) -> bool:
        return path in self.files

    def read_bytes(self, path: str) -> bytes:
        return self.read_text(path).encode()

    def read_text(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def list_files(self, prefix: str = "") -> Sequence[str]:
        return sorted(p for p in self.files if p.startswith(prefix))

    def memory(self, name: str) -> JSONValue:
        return None


OUTLINE = "## 節\n- 背景: 経緯\n- 方法: 手順\n- 結果: 数値\n\n## 問い\n- 読者: 誰向けか？\n"


def test_names_match_implementations() -> None:
    assert set(REGISTRY.names()) == {
        "file_nonempty",
        "files_nonempty",
        "section_count",
        "sections_covered",
        "blocking_findings",
    }


def test_file_nonempty() -> None:
    view = DictView({"a.txt": "x", "b.txt": " \n"})
    assert REGISTRY.measure("file_nonempty", view, {"path": "a.txt"}) is True
    assert REGISTRY.measure("file_nonempty", view, {"path": "b.txt"}) is False
    assert REGISTRY.measure("file_nonempty", view, {"path": "c.txt"}) is False
    assert REGISTRY.measure("files_nonempty", view, {"paths": ["a.txt", "b.txt"]}) is False


def test_section_count_and_coverage() -> None:
    note = "## 背景\n経緯。\n## 方法\n手順。\n"
    view = DictView({"outline.md": OUTLINE, "note.md": note})
    assert REGISTRY.measure("section_count", view, {"path": "outline.md"}) == 3
    covered = REGISTRY.measure(
        "sections_covered", view, {"outline": "outline.md", "note": "note.md"}
    )
    assert covered == pytest.approx(2 / 3)


def test_blocking_findings() -> None:
    review = {"findings": [{"blocking": True}, {"blocking": False}, {"blocking": True}]}
    view = DictView({"review.json": json.dumps(review)})
    assert REGISTRY.measure("blocking_findings", view, {"path": "review.json"}) == 2


def test_measurement_failure_raises_metric_error() -> None:
    view = DictView({"review.json": "not json"})
    with pytest.raises(MetricError):
        REGISTRY.measure("blocking_findings", view, {"path": "review.json"})
    with pytest.raises(MetricError):
        REGISTRY.measure("section_count", view, {"path": "missing.md"})
    with pytest.raises(MetricError):
        REGISTRY.measure("no_such_metric", view, {})
