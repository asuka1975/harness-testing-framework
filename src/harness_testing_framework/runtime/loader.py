"""ワークフロー定義を読み、整合性検査を通してからモデルにする。"""

from collections.abc import Collection
from pathlib import Path

from harness_testing_framework.runtime.model import Workflow, build_workflow
from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.spec import Severity, Violation, check_workflow_file


class WorkflowInvalid(ValueError):
    """整合性検査で誤り（error）が出たワークフロー定義。"""

    def __init__(self, path: Path, violations: list[Violation]) -> None:
        lines = "\n".join(f"  {v.code} {v.location}: {v.message}" for v in violations)
        super().__init__(f"{path} は整合性検査を通らない:\n{lines}")
        self.violations = violations


def load_workflow(path: Path, metrics: Collection[str]) -> Workflow:
    """ワークフロー定義を読む。metrics は指標レジストリにある指標名。警告は読み込みを妨げない。"""
    errors = [v for v in check_workflow_file(path, metrics) if v.severity is Severity.ERROR]
    if errors:
        raise WorkflowInvalid(path, errors)
    return build_workflow(load_workflow_document(path))
