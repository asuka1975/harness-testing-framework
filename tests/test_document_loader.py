"""ワークフロー定義の YAML の読み込み（決定 #10: YAML 1.1 の真偽値の誤読を避ける）。"""

from pathlib import Path

import pytest

from harness_testing_framework.schema import WorkflowDocumentError, load_workflow_document


def _load(tmp_path: Path, text: str) -> object:
    path = tmp_path / "w.yaml"
    path.write_text(text, encoding="utf-8")
    return load_workflow_document(path)


def test_yaml11_booleans_are_strings(tmp_path: Path) -> None:
    doc = _load(tmp_path, "a: yes\nb: no\non: 1\noff: [y, n, On, OFF]\n")
    assert doc == {"a": "yes", "b": "no", "on": 1, "off": ["y", "n", "On", "OFF"]}


def test_yaml12_booleans_are_booleans(tmp_path: Path) -> None:
    assert _load(tmp_path, "a: true\nb: false\nc: True\nd: FALSE\n") == {
        "a": True,
        "b": False,
        "c": True,
        "d": False,
    }


def test_non_string_key_is_rejected_with_location(tmp_path: Path) -> None:
    with pytest.raises(WorkflowDocumentError, match=r"workflow\.phases\.0.*1"):
        _load(tmp_path, "workflow:\n  phases:\n    - 1: x\n")


def test_syntax_error_is_reported(tmp_path: Path) -> None:
    with pytest.raises(WorkflowDocumentError):
        _load(tmp_path, "workflow: [\n")


def test_duplicate_key_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(WorkflowDocumentError, match="rollback"):
        _load(tmp_path, "stage:\n  rollback: []\n  rollback: [x]\n")
