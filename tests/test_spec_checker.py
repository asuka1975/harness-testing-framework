"""整合性検査器の完了条件（plan.md 第6節 F1、付録 B）。

- 正例には違反も警告も無い
- 負例は、それぞれが破る性質の違反だけを報告する（一つの負例が一つの性質だけを破る）
- 第6節 F1 が挙げる検査器の性質のそれぞれに、負例が一つ以上ある
"""

import re
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from harness_testing_framework.testing.spec import CODES, Severity, check_workflow_file
from harness_testing_framework.testing.spec.__main__ import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "schema/examples"
REGISTRY = yaml.safe_load((EXAMPLES / "registry.yaml").read_text(encoding="utf-8"))["metrics"]

VALID = sorted((EXAMPLES / "valid").glob("*.yaml"))
INVALID = sorted(
    [
        *(EXAMPLES / "invalid-document").glob("*.yaml"),
        *(EXAMPLES / "invalid-schema").glob("*.yaml"),
        *(EXAMPLES / "invalid-spec").glob("*/*.yaml"),
    ]
)

# 第6節 F1 の完了条件が挙げる性質と、それを報告する違反の符号
PROPERTIES = {
    "参照整合": {"duplicate_id", "unresolved_reference", "unresolved_read"},
    "unknown を除く end_state と rollback の全単射": {"rollback_bijection"},
    "戻り先の前方性": {"rollback_forward"},
    "max の存在と有界性": {"rollback_max"},
    "carry の生成と消費": {"carry_undeclared", "memory_unsupplied", "memory_unused"},
    "指標の存在": {"metric_unregistered"},
    "unknown の存在": {"unknown_missing"},
}


def _ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(EXAMPLES)) for p in paths]


def _expected_code(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"# check: (\S+)", line)
        if m:
            return m.group(1)
    raise AssertionError(f"{path} に '# check: ...' が無い")


@pytest.mark.parametrize("path", VALID, ids=_ids(VALID))
def test_valid_example_has_no_violation(path: Path) -> None:
    assert check_workflow_file(path, REGISTRY) == []


@pytest.mark.parametrize("path", INVALID, ids=_ids(INVALID))
def test_invalid_example_reports_only_its_property(path: Path) -> None:
    code = _expected_code(path)
    if path.parent.parent.name == "invalid-spec":
        assert path.parent.name == code
    violations = check_workflow_file(path, REGISTRY)
    assert {v.code for v in violations} == {code}, violations


def test_every_code_has_a_negative_example() -> None:
    covered = {_expected_code(p) for p in INVALID}
    assert set(CODES) == covered


def test_every_plan_property_has_a_negative_example() -> None:
    covered = {_expected_code(p) for p in INVALID}
    for prop, codes in PROPERTIES.items():
        assert codes <= set(CODES), prop
        assert codes & covered, prop


def test_memory_unused_is_a_warning_and_others_are_errors() -> None:
    for code, (severity, _) in CODES.items():
        expected = Severity.WARNING if code == "memory_unused" else Severity.ERROR
        assert severity is expected, code


def test_cli_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    registry = str(EXAMPLES / "registry.yaml")
    assert main([str(VALID[0]), "--metrics-file", registry]) == 0
    bad = EXAMPLES / "invalid-spec/rollback_forward/rollback_to_self.yaml"
    assert main([str(bad), "--metrics-file", registry]) == 1
    assert "rollback_forward" in capsys.readouterr().out


def test_cli_warning_only_exits_zero() -> None:
    registry = str(EXAMPLES / "registry.yaml")
    warn = EXAMPLES / "invalid-spec/memory_unused/memory_out_never_consumed.yaml"
    assert main([str(warn), "--metrics-file", registry]) == 0


def test_cli_loads_registry_object(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = tmp_path / "example_registry.py"
    module.write_text(
        textwrap.dedent(
            f"""
            class _Registry:
                def names(self):
                    return {REGISTRY!r}

            REGISTRY = _Registry()
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    assert main([str(VALID[0]), "--registry", "example_registry:REGISTRY"]) == 0
