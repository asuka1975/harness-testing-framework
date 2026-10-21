"""CI がローカルと同じ検査（scripts/check.sh）を呼ぶことの検査。"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_ci_runs_check_script_on_python_312() -> None:
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = [s for job in ci["jobs"].values() for s in job["steps"]]
    assert any("scripts/check.sh" in s.get("run", "") for s in steps)
    versions = [str(s.get("with", {}).get("python-version", "")) for s in steps]
    assert "3.12" in versions


def test_check_script_runs_all_tools() -> None:
    script = (ROOT / "scripts/check.sh").read_text(encoding="utf-8")
    for command in [
        "uv sync --locked",
        "ruff check",
        "ruff format --check",
        "mypy",
        "pytest",
    ]:
        assert command in script


def test_tool_configuration_does_not_name_examples() -> None:
    """examples/ の下に新しいワークフローを足しても、設定を直さずにテストと型検査に乗る。"""
    names = [p.name for p in (ROOT / "examples").iterdir() if p.is_dir()]
    names += [q.name for p in (ROOT / "examples").iterdir() if p.is_dir() for q in p.iterdir()]
    for config in ["pyproject.toml", "scripts/check.sh", "conftest.py", ".github/workflows/ci.yml"]:
        text = (ROOT / config).read_text(encoding="utf-8")
        for name in names:
            if name not in {"tests", "README.md", ".gitkeep", "workflow.yaml", "__pycache__"}:
                assert name not in text, (config, name)
