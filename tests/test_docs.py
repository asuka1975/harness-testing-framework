"""利用者向けの文書の完了条件（plan.md 第6節 F2 の adopting.md 初版、第7節の F4 の読取制限）。

- 公開 API の各名前が docs/api.md に書かれている
- docs/adopting.md が、ハーネスを作るのに要る手順をすべて扱う
- 利用者が読まない文書（plan / progress / decisions）と、本体の実装（src/）を参照しない
- docs/adopting.md の実行できる例が、そのまま動く
"""

import importlib
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ADOPTING = (ROOT / "docs/adopting.md").read_text(encoding="utf-8")
API = (ROOT / "docs/api.md").read_text(encoding="utf-8")
PUBLIC_MODULES = [
    "harness_testing_framework.schema",
    "harness_testing_framework.contract",
    "harness_testing_framework.runtime",
    "harness_testing_framework.testing.spec",
    "harness_testing_framework.testing.harness",
    "harness_testing_framework.testing.stages",
]


@pytest.mark.parametrize("module", PUBLIC_MODULES)
def test_every_public_name_is_documented(module: str) -> None:
    names = getattr(importlib.import_module(module), "__all__", None)
    assert names, module
    assert f"`{module}`" in API
    missing = [n for n in names if f"`{n}`" not in API]
    assert not missing, missing


@pytest.mark.parametrize(
    "topic",
    [
        "ワークフロー定義",
        "end_state",
        "unknown",
        "carry",
        "フェーズゲート",
        "awaits_user",
        "整合性検査",
        "指標レジストリ",
        "ステージ本体",
        "ユーザー入出力",
        "分類器",
        "運用者",
        "LLM",
        "記録再生",
        "シナリオ",
        "遷移の六種",
        "契約適合テスト",
        "サブワークフロー",
    ],
)
def test_adopting_covers(topic: str) -> None:
    headings = [line.replace("\\", "") for line in ADOPTING.splitlines() if line.startswith("#")]
    assert any(topic in h for h in headings), topic


@pytest.mark.parametrize("doc", ["docs/adopting.md", "docs/api.md"])
def test_user_docs_do_not_point_to_internal_documents(doc: str) -> None:
    text = (ROOT / doc).read_text(encoding="utf-8")
    for forbidden in ["plan.md", "progress.md", "decisions.md", "src/harness_testing_framework"]:
        assert forbidden not in text, (doc, forbidden)


def test_adopting_runnable_example(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocks = re.findall(r"```python\n# 実行できる例\n(.*?)```", ADOPTING, re.S)
    assert len(blocks) == 1
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("WORKDIR", str(tmp_path))
    assert os.environ["WORKDIR"] == str(tmp_path)
    exec(compile(blocks[0], "docs/adopting.md", "exec"), {})
