"""ハーネス契約の文書と形式の検査（plan.md 第6節 F1: 契約が文書化されている）。

契約の中身の正しさは人間の承認で決まる。ここでは、文書が契約の構成要素を
すべて扱っていること、形式の JSON Schema が適合し例が通ることを確かめる。
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import harness_testing_framework.contract as contract

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "contract/contract.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "heading",
    [
        "### 2.1 run(stage, snapshot) → snapshot",
        "### 2.2 evaluate(stage, snapshot) → class",
        "### 2.3 restore(snapshot) + overlay(carry)",
        "## 5. スナップショット形式",
        "### 7.1 ステージ本体",
        "### 7.2 指標レジストリ",
        "### 7.3 ユーザー入出力",
        "### 7.4 LLM クライアント",
        "### 7.5 分類器",
        "### 7.6 運用者",
        "## 9. 記録再生",
        "## 10. 契約適合テスト",
    ],
)
def test_contract_document_covers(heading: str) -> None:
    assert any(line.startswith(heading) for line in DOC.splitlines())


def test_contract_document_lists_six_transition_kinds() -> None:
    section = DOC.split("### 3.5 遷移の種類")[1].split("##")[0]
    assert [line[:2] for line in section.splitlines() if line[:2].rstrip(".").isdigit()] == [
        "1.",
        "2.",
        "3.",
        "4.",
        "5.",
        "6.",
    ]


def test_contract_version_matches_document() -> None:
    assert DOC.splitlines()[0] == f"# ハーネス契約 v{contract.CONTRACT_VERSION}"


@pytest.mark.parametrize("name", ["snapshot", "trace"])
def test_format_schema_conforms_to_metaschema(name: str) -> None:
    Draft202012Validator.check_schema(
        json.loads((ROOT / f"contract/{name}.schema.json").read_text(encoding="utf-8"))
    )


def test_example_snapshot_manifest_is_valid() -> None:
    schema = json.loads((ROOT / "contract/snapshot.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "contract/examples/snapshot.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(manifest))


def test_snapshot_manifest_rejects_directory_and_parent_paths() -> None:
    schema = json.loads((ROOT / "contract/snapshot.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    base = {"format_version": "0.1", "memory": {}, "gates": [], "annotations": []}
    for bad in ["out/", "../x", "/etc/x", "a/../b"]:
        assert list(validator.iter_errors({**base, "files": {bad: "0" * 64}})), bad
    assert not list(validator.iter_errors({**base, "files": {"out/a.txt": "0" * 64}}))


def test_example_trace_is_valid_and_covers_every_event() -> None:
    schema = json.loads((ROOT / "contract/trace.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    lines = (ROOT / "contract/examples/trace.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines]
    for event in events:
        errors = list(validator.iter_errors(event))
        assert not errors, (event, [e.message for e in errors])
    assert [e["seq"] for e in events] == list(range(len(events)))
    assert {e["event"] for e in events} == set(schema["properties"]["event"]["enum"])


def test_trace_rejects_unknown_event() -> None:
    schema = json.loads((ROOT / "contract/trace.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors({"seq": 0, "event": "teleport"}))


def test_python_binding_exports_contract_interfaces() -> None:
    for name in [
        "StageBody",
        "StageContext",
        "MetricRegistry",
        "SnapshotView",
        "UserIO",
        "LLMClient",
        "Classifier",
        "Operator",
        "Rerun",
        "RollbackTo",
        "ContinueAsGoal",
        "Abort",
    ]:
        assert name in contract.__all__
        assert hasattr(contract, name)
