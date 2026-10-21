"""パッケージの骨格、スキーマの同梱、ライセンス、汎用性の規律（plan.md 第5.8節）の検査。"""

import importlib
import json
import re
import tomllib
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "harness_testing_framework"
SUBPACKAGES = [
    "contract",
    "runtime",
    "schema",
    "testing",
    "testing.spec",
    "testing.harness",
    "testing.oracle",
    "testing.stages",
    "testing.e2e",
    "testing.triage",
]


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_importable(name: str) -> None:
    importlib.import_module(f"{PACKAGE}.{name}")


def test_canonical_schema_conforms_to_metaschema() -> None:
    schema = json.loads((ROOT / "schema/workflow.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_packaged_schema_matches_canonical() -> None:
    from harness_testing_framework.schema import load_workflow_schema

    canonical = json.loads((ROOT / "schema/workflow.schema.json").read_text(encoding="utf-8"))
    assert load_workflow_schema() == canonical


def test_license_is_gpl3_or_later() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["license"] == "GPL-3.0-or-later"
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in text.splitlines()[0]
    assert "Version 3, 29 June 2007" in text


def test_requires_python_312() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["requires-python"] == ">=3.12"


# --- 汎用性の規律: フレームワーク本体に玩具や特定のハーネス・ツール・LLM の名前を書かない ---

BODY_ROOTS = ["src", "schema", "contract"]
BANNED = re.compile(
    r"toy|玩具|software[-_ ]?factory|\bjev\b|system ?one|typesafe|claude|anthropic|openai|\bgpt"
    r"|gemini|llama|mistral|\blean\b|\bcoq\b|isabelle|\bagda\b|\bz3\b",
    re.IGNORECASE,
)
# スキーマが参照するメタスキーマの URL は本体の一部で、名前の検査の対象外
ALLOWED_URLS = ["https://json-schema.org/draft/2020-12/schema"]


def _body_files() -> list[Path]:
    files: list[Path] = []
    for r in BODY_ROOTS:
        files += [p for p in (ROOT / r).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    return files


def _lines(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for url in ALLOWED_URLS:
        text = text.replace(url, "")
    return list(enumerate(text.splitlines(), 1))


def test_body_has_no_banned_names() -> None:
    hits = [
        f"{p.relative_to(ROOT)}:{n}"
        for p in _body_files()
        for n, line in _lines(p)
        if BANNED.search(line)
    ]
    assert not hits


def _example_ids() -> set[str]:
    """examples/ の各ワークフロー定義に現れる id と指標名（unknown を除く）。"""
    ids: set[str] = set()
    for wf in ROOT.glob("examples/*/workflow.yaml"):
        doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
        w = doc["workflow"]
        ids.add(w["name"])
        for phase in w["phases"]:
            ids.add(phase["id"])
            ids.update(phase["goal"].get("quantitative", {}))
            for stage in phase["stages"]:
                ids.add(stage["id"])
                ids.update(stage["goal"].get("quantitative", {}))
                ids.update(e["id"] for e in stage["end_state"])
                art = stage.get("artifacts", {})
                for key in ("reads", "writes", "memory_in", "memory_out"):
                    ids.update(art.get(key, []))
    ids.discard("unknown")
    return ids


def test_body_does_not_mention_example_ids() -> None:
    ids = _example_ids()
    if not ids:
        pytest.skip("examples/ にワークフロー定義がまだ無い")
    pattern = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, sorted(ids))) + r")(?![\w-])")
    hits = [
        f"{p.relative_to(ROOT)}:{n}:{m.group(1)}"
        for p in _body_files()
        for n, line in _lines(p)
        for m in [pattern.search(line)]
        if m
    ]
    assert not hits
