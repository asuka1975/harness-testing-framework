"""拡張スキーマの完了条件（plan.md 第6節 F1）。

- 拡張スキーマがメタスキーマに適合する
- 正例が通り、負例（invalid-schema）が意図した理由で落ちる
- 検査器向けの負例（invalid-spec）はスキーマを通る（スキーマではなく検査器が捕まえる）
- 拡張は付録 A の意味を変えない: 正例はすべて付録 A の基底スキーマも通る
- 付録 B のステージの例が拡張スキーマを通る
"""

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError

from harness_testing_framework.schema import load_workflow_document

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "schema/examples"
SCHEMA = json.loads((ROOT / "schema/workflow.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
PLAN = (ROOT / "docs/plan.md").read_text(encoding="utf-8")


def _appendix(title: str, lang: str) -> str:
    m = re.search(rf"## {title}.*?```{lang}\n(.*?)\n```", PLAN, re.S)
    assert m
    return m.group(1)


BASE_SCHEMA = json.loads(_appendix("付録 A", "json"))


def _load(path: Path) -> Any:
    return load_workflow_document(path)


def _header(path: Path, key: str) -> str:
    """負例の先頭の注釈 '# <key>: <値>' を読む。"""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        m = re.match(rf"# {key}: (.+)$", line)
        if m:
            return m.group(1).strip()
    raise AssertionError(f"{path} に '# {key}: ...' が無い")


def _ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(EXAMPLES)) for p in paths]


VALID = sorted((EXAMPLES / "valid").glob("*.yaml"))
INVALID_SCHEMA = sorted((EXAMPLES / "invalid-schema").glob("*.yaml"))
INVALID_SPEC = sorted((EXAMPLES / "invalid-spec").glob("*/*.yaml"))


def test_examples_exist() -> None:
    assert VALID and INVALID_SCHEMA and INVALID_SPEC


def test_schema_conforms_to_metaschema() -> None:
    Draft202012Validator.check_schema(SCHEMA)


def test_schema_id_points_to_published_location() -> None:
    assert SCHEMA["$id"] == (
        "https://raw.githubusercontent.com/asuka1975/harness-testing-framework/main/"
        "schema/workflow.schema.json"
    )


@pytest.mark.parametrize("path", VALID, ids=_ids(VALID))
def test_valid_example_passes(path: Path) -> None:
    errors = list(VALIDATOR.iter_errors(_load(path)))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", VALID, ids=_ids(VALID))
def test_valid_example_passes_base_schema(path: Path) -> None:
    errors = list(Draft202012Validator(BASE_SCHEMA).iter_errors(_load(path)))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", INVALID_SCHEMA, ids=_ids(INVALID_SCHEMA))
def test_invalid_schema_example_fails_for_intended_reason(path: Path) -> None:
    # schema: <検証キーワード> at <ドット区切りのパスの末尾>
    keyword, _, where = _header(path, "schema").partition(" at ")
    errors = list(VALIDATOR.iter_errors(_load(path)))
    assert errors, "スキーマを通ってしまった"
    found = [(e.validator, ".".join(map(str, e.absolute_path))) for e in _flatten(errors)]
    assert any(k == keyword and p.endswith(where) for k, p in found), found


def _flatten(errors: list[ValidationError]) -> list[ValidationError]:
    out: list[ValidationError] = []
    for e in errors:
        out += [e, *_flatten(list(e.context or []))]
    return out


@pytest.mark.parametrize("path", INVALID_SPEC, ids=_ids(INVALID_SPEC))
def test_invalid_spec_example_passes_schema(path: Path) -> None:
    errors = list(VALIDATOR.iter_errors(_load(path)))
    assert not errors, [e.message for e in errors]


def test_appendix_b_stage_example_passes() -> None:
    stages = yaml.safe_load(_appendix("付録 B", "yaml"))
    doc = {
        "workflow": {
            "name": "appendix-b",
            "description": "付録 B のステージの例を包む最小のワークフロー",
            "phases": [
                {
                    "id": "p",
                    "name": "P",
                    "description": "d",
                    "goal": {"qualitative": "q", "quantitative": {}},
                    "stages": stages,
                }
            ],
        }
    }
    errors = list(VALIDATOR.iter_errors(doc))
    assert not errors, [e.message for e in errors]
