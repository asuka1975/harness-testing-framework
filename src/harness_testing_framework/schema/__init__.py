"""ワークフロー定義の JSON Schema。

正はリポジトリ最上位の schema/workflow.schema.json で、ここにはその複製を同梱する。
両者の一致はテストで保証する。
"""

import json
from importlib.resources import files
from typing import Any

SCHEMA_FILE = "workflow.schema.json"


def load_workflow_schema() -> dict[str, Any]:
    """同梱したワークフロースキーマを読み込む。"""
    text = files(__package__).joinpath(SCHEMA_FILE).read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(text)
    return schema
