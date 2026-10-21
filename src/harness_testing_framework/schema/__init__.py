"""ワークフロー定義の JSON Schema と、ワークフロー定義の YAML の読み込み。

スキーマの正はリポジトリ最上位の schema/workflow.schema.json で、ここにはその複製を同梱する。
両者の一致はテストで保証する。
"""

import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

SCHEMA_FILE = "workflow.schema.json"


def load_workflow_schema() -> dict[str, Any]:
    """同梱したワークフロースキーマを読み込む。"""
    text = files(__package__).joinpath(SCHEMA_FILE).read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(text)
    return schema


class WorkflowDocumentError(ValueError):
    """ワークフロー定義の YAML が文書として読めない（構文、キーの型、キーの重複）。"""


class _Loader(yaml.SafeLoader):
    """YAML 1.2 の core schema に寄せた読み込み。

    YAML 1.1 では yes / no / on / off も真偽値になり、id や指標名を誤読する。
    真偽値は true / false（と大文字の綴り）だけにする。マッピングのキーの重複は誤りにする。
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise WorkflowDocumentError(f"{key_node.start_mark}: キー {key!r} が重複している")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


_BOOL_TAG = "tag:yaml.org,2002:bool"
_Loader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != _BOOL_TAG]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver(
    _BOOL_TAG, re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)


def _check_keys(node: Any, path: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if not isinstance(key, str):
                raise WorkflowDocumentError(f"{path}: キー {key!r} が文字列でない")
            _check_keys(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            _check_keys(value, f"{path}.{i}")


def load_workflow_document(path: Path) -> Any:
    """ワークフロー定義の YAML を読む。スキーマの検証はしない。"""
    try:
        # _Loader は SafeLoader の派生なので、任意のオブジェクトは構築しない
        doc = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)
    except yaml.YAMLError as e:
        raise WorkflowDocumentError(f"{path}: YAML として読めない: {e}") from e
    _check_keys(doc, "")
    return doc
