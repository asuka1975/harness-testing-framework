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


@pytest.mark.parametrize(
    ("name", "canonical"),
    [
        ("snapshot.schema.json", "contract/snapshot.schema.json"),
        ("trace.schema.json", "contract/trace.schema.json"),
        ("scenario.schema.json", "contract/conformance/scenario.schema.json"),
        ("expectations.schema.json", "contract/formats/expectations.schema.json"),
        ("corpus_item.schema.json", "contract/formats/corpus_item.schema.json"),
        ("label.schema.json", "contract/formats/label.schema.json"),
        ("triage_item.schema.json", "contract/formats/triage_item.schema.json"),
        ("triage_decision.schema.json", "contract/formats/triage_decision.schema.json"),
    ],
)
def test_packaged_contract_schema_matches_canonical(name: str, canonical: str) -> None:
    from harness_testing_framework.contract import load_contract_schema

    expected = json.loads((ROOT / canonical).read_text(encoding="utf-8"))
    assert load_contract_schema(name) == expected


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


def _ids_in(node: object, into: set[str]) -> None:
    """ワークフロー定義らしい文書から、id、指標名、成果物のパス、記憶の名前を拾う（形の崩れた文書も読む）。"""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "id" and isinstance(value, str):
                into.add(value)
            elif key == "quantitative" and isinstance(value, dict):
                into.update(k for k in value if isinstance(k, str))
            elif key in ("reads", "writes", "memory_in", "memory_out", "carry", "inputs") and (
                isinstance(value, list)
            ):
                into.update(v for v in value if isinstance(v, str))
            _ids_in(value, into)
    elif isinstance(node, list):
        for value in node:
            _ids_in(value, into)


def _framework_vocabulary() -> set[str]:
    """本体自身の語: 公開 API の名前と、本体が持つワークフロー定義の例（schema/examples/、
    contract/conformance/workflows/）の id など。例の id がこれと重なるのは、本体が例を前提にした
    ことにはならない（ありふれた語の偶然の一致）。"""
    words: set[str] = set()
    for name in SUBPACKAGES:
        words.update(getattr(importlib.import_module(f"{PACKAGE}.{name}"), "__all__", []))
    documents = [
        *ROOT.glob("schema/examples/**/*.yaml"),
        *ROOT.glob("contract/conformance/workflows/*.yaml"),
    ]
    for path in documents:
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        _ids_in(doc, words)
    words.discard("unknown")
    return words


def test_framework_vocabulary_holds_own_words_only() -> None:
    words = _framework_vocabulary()
    # 公開 API の名前と、本体の例の id・パス・記憶
    assert {"verify", "run_scenario", "request.md", "open_questions"} <= words
    # 例（toy-minimal）だけにある語は含まない
    assert not {"write_note", "brief.txt", "toy-minimal"} & words


def test_body_does_not_mention_example_ids() -> None:
    ids = _example_ids() - _framework_vocabulary()
    if not ids:
        pytest.skip("examples/ にワークフロー定義がまだ無い")
    pattern = re.compile(r"(?<![\w-])(" + "|".join(map(re.escape, sorted(ids))) + r")(?![\w-])")
    hits = [
        f"{p.relative_to(ROOT)}:{n}:{m.group(1)}"
        for p in _body_files()
        for n, line in _lines(p)
        for m in pattern.finditer(line)
    ]
    assert not hits
