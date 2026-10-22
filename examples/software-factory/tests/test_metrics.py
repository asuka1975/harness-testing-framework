"""software-factory の指標レジストリ。

- 文書の指標の単体テスト
- フィクスチャと実在の指標の整合: 各ステージの各変種（上流は goal の変種）に、ワークフロー定義のそのステージの goal の
  指標を実際にかけ、落ちる指標が tests/stochastic.yaml の metrics_fail と一致する（goal の変種は全部通る）。印のクラスが
  goal なのに指標が落ちると、MarkerClassifier の答えが選択肢に無く unknown になるので、この整合が分布テストの前提になる
- 各フェーズのゲートの指標が、goal の変種を重ねた成果物で全部通る
- 測れない時は MetricError、ツールの結果は内容で覚える
"""

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from software_factory import metrics
from software_factory.metrics import REGISTRY
from software_factory.stages.deterministic import FIXTURES, inputs
from software_factory.stages.probabilistic import TABLE, fixture_dir

from harness_testing_framework.contract import JSONValue, MetricError
from harness_testing_framework.schema import load_workflow_document

WORKFLOW = Path(__file__).resolve().parents[1] / "workflow.yaml"
DOC: Any = load_workflow_document(WORKFLOW)
PHASES = DOC["workflow"]["phases"]
STAGES = {s["id"]: s for p in PHASES for s in p["stages"]}
ORDER = list(STAGES)


class DictView:
    def __init__(self, files: Mapping[str, bytes], base: "DictView | None" = None) -> None:
        self.files = dict(files)
        self.base = base

    def exists(self, path: str) -> bool:
        return path in self.files

    def read_bytes(self, path: str) -> bytes:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def read_text(self, path: str) -> str:
        return self.read_bytes(path).decode("utf-8")

    def list_files(self, prefix: str = "") -> Sequence[str]:
        return sorted(p for p in self.files if p.startswith(prefix))

    def memory(self, name: str) -> JSONValue:
        return None

    def baseline(self) -> "DictView | None":
        return self.base


def _tree(directory: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()
    }


def _variant_files(stage: str, variant: str, family: str) -> tuple[dict[str, bytes], list[str]]:
    spec = TABLE["variants"][stage][variant]
    if "by_family" in spec:
        spec = spec["by_family"][family]
        name = spec["fixture"]
    else:
        name = variant
    return _tree(fixture_dir(stage, name)), list(spec.get("metrics_fail", []))


def _passes(criterion: Mapping[str, Any], value: bool | float) -> bool:
    if "equals" in criterion:
        return bool(value == criterion["equals"])
    low, high = (
        float(criterion.get("min", float("-inf"))),
        float(criterion.get("max", float("inf"))),
    )
    return low <= value <= high


def _failing(quantitative: Mapping[str, Any], view: DictView) -> list[str]:
    failing = []
    for name, criterion in quantitative.items():
        try:
            ok = _passes(criterion, REGISTRY.measure(name, view, criterion.get("args", {})))
        except MetricError:
            ok = False
        if not ok:
            failing.append(name)
    return sorted(failing)


GOAL_IMPL = {"rounds_total": "ok", "correct": "ok_fixed"}
CASES = [
    (stage, variant, family)
    for stage in ORDER
    for variant in TABLE["variants"][stage]
    for family in (GOAL_IMPL if stage == "unit_test" else ["rounds_total"])
]


@pytest.mark.parametrize(("stage", "variant", "family"), CASES)
def test_variant_fails_exactly_the_designed_metrics(stage: str, variant: str, family: str) -> None:
    before = inputs()
    for upstream in ORDER[: ORDER.index(stage)]:
        name = GOAL_IMPL[family] if upstream == "implement" else "ok"
        before |= _tree(fixture_dir(upstream, name))
    files, expected = _variant_files(stage, variant, family)
    view = DictView(before | files, DictView(before))
    assert _failing(STAGES[stage]["goal"]["quantitative"], view) == sorted(expected)


@pytest.mark.parametrize("family", list(GOAL_IMPL))
def test_gates_pass_on_goal_artifacts(family: str) -> None:
    files = inputs()
    for phase in PHASES:
        start = DictView(files)
        for stage in phase["stages"]:
            name = GOAL_IMPL[family] if stage["id"] == "implement" else "ok"
            files = files | _tree(fixture_dir(stage["id"], name))
        assert _failing(phase["goal"]["quantitative"], DictView(files, start)) == [], phase["id"]


def test_names_match_implementations() -> None:
    used = {name for s in STAGES.values() for name in s["goal"]["quantitative"]}
    used |= {name for p in PHASES for name in p["goal"]["quantitative"]}
    assert used <= set(REGISTRY.names())


REQUIREMENTS = (FIXTURES / "analyze" / "ok" / "requirements.md").read_bytes()


def test_requirement_metrics() -> None:
    view = DictView({"requirements.md": REQUIREMENTS})
    assert REGISTRY.measure("requirement_count", view, {"path": "requirements.md"}) == 4
    assert REGISTRY.measure("requirements_with_criteria", view, {"path": "requirements.md"}) == 1
    partial = "## 要件\n- REQ-1: a\n  - 受け入れ基準: b\n- REQ-2: c\n"
    view = DictView({"requirements.md": partial.encode()})
    assert REGISTRY.measure("requirements_with_criteria", view, {"path": "requirements.md"}) == 0.5


def test_unanswered_questions() -> None:
    text = "## 質問と回答\n- Q: 誰\n  A: 購入者\n- Q: 上限\n  A:\n- Q: 無効\n\n## 制約\n"
    view = DictView({"intake.md": text.encode()})
    assert REGISTRY.measure("unanswered_questions", view, {"path": "intake.md"}) == 2
    with pytest.raises(MetricError):
        REGISTRY.measure("unanswered_questions", DictView({"intake.md": b"# x\n"}), {})


def test_verified_and_changelog_coverage() -> None:
    verification = "| REQ-1 | t | 合格 |\n| REQ-2 | t | 不合格 |\n| REQ-3 | t | 合格 |\n"
    view = DictView(
        {
            "requirements.md": REQUIREMENTS,
            "verification.md": verification.encode(),
            "CHANGELOG.md": "# Changelog\n\n## 0.2.0\n- REQ-1、REQ-2、REQ-4\n".encode(),
        }
    )
    assert REGISTRY.measure("verified_requirements", view, {}) == 0.5
    assert REGISTRY.measure("changelog_covers_requirements", view, {}) == 0.75


def test_requirement_ids_followed_by_japanese_are_counted() -> None:
    """id の直後に日本語の文が続いても数え、REQ-10 は REQ-1 と数えない。CHANGELOG.md は最新の版の変更の行だけを数える。"""
    design = "## 対応\n- REQ-1は Discount.apply\n- REQ-2の分岐\n- REQ-30 と REQ-4\n"
    changelog = (
        "# Changelog\n\n## 0.2.0\n- 百分率の割引（REQ-1）\n- REQ-2として定額\n未対応: REQ-3\n\n"
        "## 0.1.0\n- REQ-4 の古い変更\n"
    )
    view = DictView(
        {
            "requirements.md": REQUIREMENTS,
            "design.md": design.encode(),
            "CHANGELOG.md": changelog.encode(),
        }
    )
    assert REGISTRY.measure("design_covers_requirements", view, {}) == 0.75
    assert REGISTRY.measure("changelog_covers_requirements", view, {}) == 0.5
    with pytest.raises(MetricError):
        REGISTRY.measure(
            "changelog_covers_requirements",
            DictView({**view.files, "CHANGELOG.md": b"- REQ-1\n"}),
            {},
        )


def test_out_of_scope_changes_counts_additions_changes_and_deletions() -> None:
    tasks = b"tasks:\n  - id: T1\n    paths: [repo/src/a.py, repo/src/pkg/]\n    tests: []\n"
    before = DictView({"tasks.yaml": tasks, "repo/src/a.py": b"1", "repo/src/b.py": b"1"})
    after = {
        "tasks.yaml": tasks,
        "repo/src/a.py": b"2",
        "repo/src/pkg/c.py": b"",
        "repo/src/d.py": b"",
    }
    view = DictView(after, before)
    # a.py の変更と pkg/ の下の追加は範囲内、b.py の削除と d.py の追加は範囲外
    assert REGISTRY.measure("out_of_scope_changes", view, {}) == 2
    with pytest.raises(MetricError):
        REGISTRY.measure("out_of_scope_changes", DictView(after), {})


def test_version_bumped() -> None:
    package = b'__version__ = "0.1.0"\n'
    for version, bumped in (("0.2.0", True), ("0.1.0", False), ("0.0.9", False)):
        view = DictView(
            {
                "release.json": json.dumps({"version": version}).encode(),
                "repo/src/shopcart/__init__.py": package,
            }
        )
        assert REGISTRY.measure("version_bumped", view, {}) is bumped


def test_measurement_failure_raises_metric_error() -> None:
    view = DictView({"review.json": b"not json", "tasks.yaml": b"tasks: 1\n"})
    with pytest.raises(MetricError):
        REGISTRY.measure("blocking_findings", view, {"path": "review.json"})
    text_blocking = json.dumps({"findings": [{"path": "a", "blocking": "false", "comment": "c"}]})
    with pytest.raises(MetricError):
        REGISTRY.measure("blocking_findings", DictView({"review.json": text_blocking.encode()}), {})
    with pytest.raises(MetricError):
        REGISTRY.measure("task_paths_valid", view, {"tasks": "tasks.yaml"})
    with pytest.raises(MetricError):
        REGISTRY.measure("tests_pass", view, {})
    with pytest.raises(MetricError):
        REGISTRY.measure("no_such_metric", view, {})


def test_tool_results_are_remembered_by_content() -> None:
    files = inputs()
    view = DictView(files)
    metrics._RESULTS.clear()
    assert REGISTRY.measure("lint_errors", view, {"paths": ["src"]}) == 0
    assert len(metrics._RESULTS) == 1
    assert REGISTRY.measure("lint_errors", DictView(dict(files)), {"paths": ["src"]}) == 0
    assert len(metrics._RESULTS) == 1
    broken = files | {"repo/src/shopcart/extra.py": b"import os\n"}
    assert REGISTRY.measure("lint_errors", DictView(broken), {"paths": ["src"]}) == 1
    assert len(metrics._RESULTS) == 2


@pytest.mark.parametrize("name", ["build_passes", "tests_pass", "line_coverage"])
@pytest.mark.parametrize("returncode", [-9, 3, 4])
def test_abnormal_tool_exit_is_an_error_and_is_not_remembered(
    name: str, returncode: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ツールが異常に終わった時（シグナル、意味の決まっていない終了コード）は MetricError で、結果を覚えない。"""

    def crashed(command: list[str], cwd: Path, src: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, returncode, "", "killed")

    metrics._RESULTS.clear()
    monkeypatch.setattr(metrics, "_run", crashed)
    with pytest.raises(MetricError):
        REGISTRY.measure(name, DictView(inputs()), {})
    assert metrics._RESULTS == {}


def test_collection_error_means_the_tests_do_not_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """pytest の中断（終了コード 2）は、テストの収集が失敗した時だけ「通らない」として覚える。"""

    def collection_error(
        command: list[str], cwd: Path, src: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 2, "Interrupted: 1 error during collection", "")

    metrics._RESULTS.clear()
    monkeypatch.setattr(metrics, "_run", collection_error)
    assert REGISTRY.measure("tests_pass", DictView(inputs()), {}) is False
    assert len(metrics._RESULTS) == 1
