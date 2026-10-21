"""整合性検査器のコマンド。

    python -m harness_testing_framework.testing.spec WORKFLOW.yaml \\
        (--registry MODULE:ATTR | --metrics-file FILE)

指標レジストリは、names() で指標名を返すオブジェクト（--registry）か、
metrics: [名前, ...] を持つ YAML（--metrics-file）で与える。
違反（error）が一つでもあれば終了コード 1。警告（warning）だけなら 0。
"""

import argparse
import importlib
import sys
from collections.abc import Collection, Sequence
from pathlib import Path

from harness_testing_framework.schema import load_workflow_document
from harness_testing_framework.testing.spec.checker import Severity, check_workflow_file


def _registry_names(spec: str) -> Collection[str]:
    module_name, _, attr = spec.partition(":")
    registry = getattr(importlib.import_module(module_name), attr)
    return set(registry.names())


def _metrics_file_names(path: str) -> Collection[str]:
    doc = load_workflow_document(Path(path))
    metrics = doc.get("metrics") if isinstance(doc, dict) else None
    if not isinstance(metrics, list) or not all(isinstance(m, str) for m in metrics):
        raise SystemExit(f"{path}: metrics: [指標名, ...] の形でない")
    return set(metrics)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harness_testing_framework.testing.spec")
    parser.add_argument("workflow", type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--registry", help="指標レジストリのオブジェクト（module:attribute）")
    source.add_argument("--metrics-file", help="metrics: [指標名, ...] を持つ YAML")
    args = parser.parse_args(argv)

    if args.registry:
        metrics = _registry_names(args.registry)
    else:
        metrics = _metrics_file_names(args.metrics_file)
    violations = check_workflow_file(args.workflow, metrics)
    for v in violations:
        print(f"{v.severity.value}\t{v.code}\t{v.location}\t{v.message}")
    errors = sum(1 for v in violations if v.severity is Severity.ERROR)
    print(f"{errors} error(s), {len(violations) - errors} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
