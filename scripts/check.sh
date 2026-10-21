#!/usr/bin/env bash
# ローカルと CI で同じ検査を実行する。
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest

# 配布物にスキーマが同梱されていること
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
uv build --wheel --out-dir "$out" >/dev/null 2>&1
uv run python -c "
import sys, zipfile, glob
whl = glob.glob(sys.argv[1] + '/*.whl')[0]
names = zipfile.ZipFile(whl).namelist()
assert 'harness_testing_framework/schema/workflow.schema.json' in names, names
print('wheel: schema packaged')
" "$out"
