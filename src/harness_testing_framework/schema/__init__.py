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

    YAML 1.1 では yes / no / on / off も真偽値になり、1:30 は 60 進数、日付は日付型になって、
    id や指標名や基準を誤読する。真偽値・整数・浮動小数点数の暗黙の解決を YAML 1.2 の
    core schema に揃え、日付は文字列のままにする。マッピングのキーの重複は誤りにする。
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                raise WorkflowDocumentError(
                    f"{key_node.start_mark}: キー {key!r} がハッシュできない"
                ) from None
            if key in seen:
                raise WorkflowDocumentError(f"{key_node.start_mark}: キー {key!r} が重複している")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


_BOOL_TAG = "tag:yaml.org,2002:bool"
_INT_TAG = "tag:yaml.org,2002:int"
_FLOAT_TAG = "tag:yaml.org,2002:float"
_REPLACED = {_BOOL_TAG, _INT_TAG, _FLOAT_TAG, "tag:yaml.org,2002:timestamp"}
_Loader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag not in _REPLACED]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver(
    _BOOL_TAG, re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF")
)
_Loader.add_implicit_resolver(
    _INT_TAG, re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$"), list("-+0123456789")
)
_Loader.add_implicit_resolver(
    _FLOAT_TAG,
    re.compile(
        r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
        r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"
    ),
    list("-+.0123456789"),
)


def _construct_int(loader: yaml.SafeLoader, node: yaml.ScalarNode) -> int:
    text = str(loader.construct_scalar(node))
    if text.startswith(("0o", "0x")):
        return int(text, 0)
    return int(text, 10)


_Loader.add_constructor(_INT_TAG, _construct_int)


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
