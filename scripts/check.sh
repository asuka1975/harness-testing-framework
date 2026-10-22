#!/usr/bin/env bash
# ローカルと CI で同じ検査を実行する。
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
# examples/ の下の各ワークフローを、それぞれ別に型検査する（同じ名前のテストのモジュールがぶつからないように）
for example in examples/*/; do
    if [ -n "$(find "$example" -name '*.py' -print -quit)" ]; then
        MYPYPATH="src:${example%/}" uv run mypy --explicit-package-bases "${example%/}"
    fi
done
uv run pytest
# 参照ランタイムの行カバレッジ 90% 以上（plan.md 第6節 F2）
uv run coverage report --include="src/harness_testing_framework/runtime/*" --fail-under=90 >/dev/null
echo "runtime coverage >= 90%"

# 配布物にスキーマが同梱されていること
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
uv build --wheel --out-dir "$out" >/dev/null 2>&1
uv run python -c "
import sys, zipfile, glob
whl = glob.glob(sys.argv[1] + '/*.whl')[0]
names = zipfile.ZipFile(whl).namelist()
for n in ['schema/workflow.schema.json', 'contract/trace.schema.json',
          'contract/snapshot.schema.json', 'contract/scenario.schema.json',
          'contract/conformance/workflows/basic.yaml',
          'contract/conformance/scenarios/happy_path.yaml',
          'contract/conformance/files/in.txt', 'contract/conformance/manifests.json']:
    assert 'harness_testing_framework/' + n in names, (n, names)
print('wheel: schemas packaged')
" "$out"
