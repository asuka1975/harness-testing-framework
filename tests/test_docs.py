"""利用者向けの文書の完了条件（plan.md 第6節 F2 の adopting.md 初版、第7節の F4 の読取制限）。

- 公開 API の各名前が docs/api.md に書かれている
- docs/adopting.md が、ハーネスを作るのに要る手順をすべて扱う
- 利用者が読まない文書（plan / progress / decisions）と、本体の実装（src/）を参照しない
- docs/adopting.md の実行できる例が、そのまま動く
"""

import importlib
import importlib.util
import inspect
import os
import re
import typing
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
    "harness_testing_framework.testing.e2e",
    "harness_testing_framework.testing.oracle",
    "harness_testing_framework.testing.triage",
]


@pytest.mark.parametrize("module", PUBLIC_MODULES)
def test_every_public_name_is_documented(module: str) -> None:
    names = getattr(importlib.import_module(module), "__all__", None)
    assert names, module
    assert f"`{module}`" in API
    missing = [n for n in names if f"`{n}`" not in API]
    assert not missing, "\n".join(missing)


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
        "分布テスト",
        "独立性",
        "マルコフ合成",
        "分類器の検証",
        "トリアージ",
    ],
)
def test_adopting_covers(topic: str) -> None:
    headings = [line.replace("\\", "") for line in ADOPTING.splitlines() if line.startswith("#")]
    assert any(topic in h for h in headings), topic


@pytest.mark.parametrize("doc", ["docs/adopting.md", "docs/api.md", "docs/api-reference.md"])
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


# 計画書・決定記録・作業ログと、その中の番号（決定 #n、決定 A2、追加の論点、D-n、マイルストーン F1〜F5）
INTERNAL = re.compile(
    r"plan\.md|progress\.md|decisions\.md|決定 ?[#A-Z0-9]|追加の論点|\bD-\d+\b|\bF[1-5]\b|（A2?）|\bA2\b"
)


def _public_texts() -> list[Path]:
    """利用者が読む、または公開の名前の docstring として見える本体のファイル。"""
    paths = [*ROOT.glob("contract/**/*.md"), *ROOT.glob("contract/**/*.json")]
    paths += [
        *ROOT.glob("contract/**/*.yaml"),
        *ROOT.glob("src/**/*.yaml"),
        *ROOT.glob("src/**/*.md"),
    ]
    paths += [ROOT / "schema/workflow.schema.json", *ROOT.glob("src/**/*.py")]
    paths += [*ROOT.glob("src/**/*.json")]
    return [p for p in paths if "__pycache__" not in p.parts]


def test_public_material_does_not_cite_internal_documents() -> None:
    """契約、スキーマ、本体のコード（docstring）は、利用者が読まない文書（計画書、決定記録、作業ログ）や
    その番号を根拠として指さない。根拠は本文に書く。"""
    hits = [
        f"{p.relative_to(ROOT)}:{n}: {m.group(0)}"
        for p in _public_texts()
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        for m in INTERNAL.finditer(line)
    ]
    assert not hits, "\n".join(hits)


def test_api_reference_is_generated_from_the_body() -> None:
    """docs/api-reference.md（公開の名前の引数、属性、docstring）が本体と食い違わない。"""
    spec = importlib.util.spec_from_file_location(
        "api_reference", ROOT / "scripts/api_reference.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    written = (ROOT / "docs/api-reference.md").read_text(encoding="utf-8")
    assert written == module.render(), "uv run python scripts/api_reference.py --write で書き直す"
    assert "docs/api-reference.md" in API or "(api-reference.md)" in API


def _referenced(annotation: object, into: dict[int, object]) -> None:
    into[id(annotation)] = annotation
    value = getattr(annotation, "__value__", None)  # type 文の別名
    if value is not None and id(value) not in into:
        _referenced(value, into)
    for arg in typing.get_args(annotation):
        if id(arg) not in into:
            _referenced(arg, into)


def test_names_used_in_public_signatures_are_public() -> None:
    """公開の名前の signature（引数、戻り値、属性、既定値）に出てくる本体の型と関数は、それ自身も公開する。"""
    public = [
        getattr(importlib.import_module(m), n)
        for m in PUBLIC_MODULES
        for n in importlib.import_module(m).__all__
    ]
    public_ids = {id(o) for o in public}
    seen: dict[int, object] = {}
    for obj in public:
        targets = [obj]
        if inspect.isclass(obj):
            targets += [v for k, v in vars(obj).items() if not k.startswith("_") and callable(v)]
            targets += [p.fget for p in vars(obj).values() if isinstance(p, property) and p.fget]
        for target in targets:
            try:
                signature = inspect.signature(target)
            except (TypeError, ValueError):
                continue
            for parameter in signature.parameters.values():
                _referenced(parameter.annotation, seen)
                if callable(parameter.default):
                    seen[id(parameter.default)] = parameter.default
            _referenced(signature.return_annotation, seen)
    missing = sorted(
        {
            getattr(o, "__name__", repr(o))
            for o in seen.values()
            if str(getattr(o, "__module__", "")).startswith("harness_testing_framework")
            and id(o) not in public_ids
        }
    )
    assert not missing, "\n".join(missing)
