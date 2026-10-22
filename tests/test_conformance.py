"""契約適合テスト（contract/conformance/）を参照ランタイムで通す。

plan.md 第6節 F2 の完了条件の一部。

- 各シナリオの実行記録の要約、最後の状態、記憶、注記の数が期待どおり
- 実行記録の各出来事が contract/trace.schema.json に適合し、seq が通し番号
- スナップショットのマニフェストが contract/snapshot.schema.json に適合する
- シナリオ全体で遷移の六種（契約 3.5）をすべて通す
- 記録してから再生すると、外部を一度も呼ばずに同じスナップショットの列になる
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from harness_testing_framework.contract import Question
from harness_testing_framework.runtime.checkpoint import sha256
from harness_testing_framework.testing.harness import (
    TRANSITION_KINDS,
    ReplayOnly,
    ScenarioInvalid,
    conformance_dir,
    conformance_scenarios,
    load_scenario,
    run_scenario,
    transition_coverage,
)


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8"))


ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "contract/conformance"
SCENARIOS = sorted((CONFORMANCE / "scenarios").glob("*.yaml"))
TRACE_SCHEMA = json.loads((ROOT / "contract/trace.schema.json").read_text(encoding="utf-8"))
SNAPSHOT_SCHEMA = json.loads((ROOT / "contract/snapshot.schema.json").read_text(encoding="utf-8"))
SCENARIO_SCHEMA = json.loads((CONFORMANCE / "scenario.schema.json").read_text(encoding="utf-8"))


def _ids(paths: list[Path]) -> list[str]:
    return [p.stem for p in paths]


def test_scenario_schema_conforms_to_metaschema() -> None:
    Draft202012Validator.check_schema(SCENARIO_SCHEMA)


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids(SCENARIOS))
def test_scenario_file_is_valid(path: Path) -> None:
    doc: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(SCENARIO_SCHEMA).iter_errors(doc))
    assert not errors, [e.message for e in errors]


@pytest.mark.parametrize("path", SCENARIOS, ids=_ids(SCENARIOS))
def test_reference_runtime_passes_scenario(path: Path, tmp_path: Path) -> None:
    scenario = load_scenario(path)
    result = run_scenario(scenario, tmp_path)
    assert result.problems == []

    trace_validator = Draft202012Validator(TRACE_SCHEMA)
    for event in result.trace:
        errors = list(trace_validator.iter_errors(event))
        assert not errors, (event, [e.message for e in errors])
    assert [e["seq"] for e in result.trace] == list(range(len(result.trace)))

    snapshot_validator = Draft202012Validator(SNAPSHOT_SCHEMA)
    for snapshot in result.snapshots:
        assert not list(snapshot_validator.iter_errors(snapshot.manifest()))


def test_result_store_holds_the_state_documents_the_classifier_saw(tmp_path: Path) -> None:
    """シナリオだけが写す代表の状態文書を、結果の置き場から読める（手引き第15.1節）。"""
    states = []
    for path in SCENARIOS:
        result = run_scenario(load_scenario(path), tmp_path / path.stem)
        for event in result.trace:
            classification = event.get("classification")
            if isinstance(classification, dict) and "state" in classification:
                states.append(result.store.get(str(classification["state"])).decode("utf-8"))
    assert states
    assert all(s.startswith("# 評価: ") for s in states)


def test_scenarios_cover_every_transition_kind(tmp_path: Path) -> None:
    covered: set[str] = set()
    for i, path in enumerate(SCENARIOS):
        result = run_scenario(load_scenario(path), tmp_path / str(i))
        covered |= transition_coverage(result.trace)
    assert covered == set(TRANSITION_KINDS)


@pytest.mark.parametrize(
    "name",
    [
        "resume_replays_answers",
        "phase_crossing_rollback",
        "max_exceeded_continue_as_goal",
        "operator_defers",
        "suspend_after_rollback",
    ],
)
def test_replay_reproduces_snapshots_without_external_calls(name: str, tmp_path: Path) -> None:
    scenario = load_scenario(CONFORMANCE / f"scenarios/{name}.yaml")
    recorded = run_scenario(scenario, tmp_path / "record", record=tmp_path / "rec.jsonl")
    replayed = run_scenario(scenario, tmp_path / "replay", replay=tmp_path / "rec.jsonl")
    assert [s.id for s in replayed.snapshots] == [s.id for s in recorded.snapshots]
    assert replayed.trace == recorded.trace
    assert replayed.problems == recorded.problems == []


def test_replay_with_missing_record_fails_loudly(tmp_path: Path) -> None:
    scenario = load_scenario(CONFORMANCE / "scenarios/rollback_with_carry.yaml")
    run_scenario(scenario, tmp_path / "record", record=tmp_path / "rec.jsonl")
    lines = (tmp_path / "rec.jsonl").read_text(encoding="utf-8").splitlines()
    (tmp_path / "short.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ReplayOnly.Missing):
        run_scenario(scenario, tmp_path / "replay", replay=tmp_path / "short.jsonl")


@pytest.mark.parametrize(
    ("part", "mutate"),
    [
        ("trace", lambda e: e.update(trace=e["trace"][:-1])),
        ("status", lambda e: e.update(status="aborted")),
        ("starts", lambda e: e["starts"]["s1#2"]["memory"].update(m21="違う")),
        ("starts", lambda e: e["starts"]["s1#2"]["files"].update({"s1.txt": "余計"})),
        ("starts", lambda e: e["starts"]["s3#1"].update(gates=[])),
        ("starts", lambda e: e["starts"].update({"s9#1": e["starts"]["s1#2"]})),
        ("options", lambda e: e.update(options={"stage:s1#1": ["unknown", "goal"]})),
        ("memory", lambda e: e.update(memory={"m21": "違う"})),
        ("annotations", lambda e: e.update(annotations=3)),
    ],
)
def test_verify_reports_each_kind_of_mismatch(part: str, mutate: Any, tmp_path: Path) -> None:
    """verify が食い違いを報告すること（常に空を返す verify ではテストが通らないように）。"""
    original = yaml.safe_load((CONFORMANCE / "scenarios/rollback_with_carry.yaml").read_text())
    mutate(original["expect"])
    broken = tmp_path / "broken.yaml"
    broken.write_text(yaml.safe_dump(original, allow_unicode=True), encoding="utf-8")
    workflow = CONFORMANCE / "workflows/basic.yaml"
    scenario = dataclasses.replace(load_scenario(broken), workflow=workflow)
    result = run_scenario(scenario, tmp_path / "run")
    assert result.problems
    assert any(problem.startswith(part) for problem in result.problems), result.problems


def _scenario_with_refs(tmp_path: Path, inputs: dict[str, Any], starts: dict[str, Any]) -> Path:
    doc = {
        "scenario": "refs",
        "description": "ファイルとディレクトリの参照",
        "workflow": str(CONFORMANCE / "workflows/basic.yaml"),
        "metrics": "conformance",
        "inputs": inputs,
        "visits": {"s1#1": {"classify": {"choice": None, "confidence": 0.0}}},
        "expect": {
            "status": "awaiting_operator",
            "trace": [],
            "starts": {"s1#1": {"files": starts, "memory": {}, "gates": []}},
        },
    }
    path = tmp_path / "scenarios" / "refs.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    # 鍵の並びを保つ（重なりの規則が並びによらないことを確かめるため）
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def test_file_and_directory_references_are_read_relative_to_the_scenario(tmp_path: Path) -> None:
    files = tmp_path / "files"
    (files / "dir" / "sub").mkdir(parents=True)
    (files / "in.txt").write_text("入力", encoding="utf-8")
    (files / "dir" / "a.txt").write_text("A", encoding="utf-8")
    (files / "dir" / "sub" / "b.txt").write_text("B", encoding="utf-8")
    refs = {"in.txt": {"from": "../files/in.txt"}, "d/": {"from": "../files/dir/"}}
    scenario = load_scenario(_scenario_with_refs(tmp_path, refs, refs))
    expanded = {"in.txt": "入力", "d/a.txt": "A", "d/sub/b.txt": "B"}
    assert dict(scenario.inputs) == expanded
    assert scenario.expect.starts["s1#1"]["files"] == expanded


@pytest.mark.parametrize("reverse", [False, True])
def test_more_specific_key_wins_where_references_overlap(tmp_path: Path, reverse: bool) -> None:
    files = tmp_path / "files"
    (files / "dir" / "sub").mkdir(parents=True)
    (files / "other").mkdir()
    (files / "dir" / "a.txt").write_text("A", encoding="utf-8")
    (files / "dir" / "sub" / "b.txt").write_text("B", encoding="utf-8")
    (files / "other" / "b.txt").write_text("B2", encoding="utf-8")
    refs: dict[str, Any] = {
        "d/": {"from": "../files/dir/"},
        "d/sub/": {"from": "../files/other/"},
        "d/a.txt": "上書き",
    }
    if reverse:
        refs = dict(reversed(refs.items()))
    scenario = load_scenario(_scenario_with_refs(tmp_path, refs, refs))
    expanded = {"d/a.txt": "上書き", "d/sub/b.txt": "B2"}
    assert dict(scenario.inputs) == expanded
    assert scenario.expect.starts["s1#1"]["files"] == expanded


@pytest.mark.parametrize(
    "refs",
    [
        {"x/": {"from": "../files/in.txt"}},  # ディレクトリの鍵にファイル
        {"x": {"from": "../files/dir/"}},  # ファイルの鍵にディレクトリ
        {"x": {"from": "../files/missing.txt"}},  # 無いファイル
        {"x": {"from": "../files/dir"}},  # ディレクトリを / で終えずに指す
    ],
)
def test_bad_references_are_rejected(tmp_path: Path, refs: dict[str, Any]) -> None:
    (tmp_path / "files" / "dir").mkdir(parents=True)
    (tmp_path / "files" / "in.txt").write_text("入力", encoding="utf-8")
    with pytest.raises(ScenarioInvalid, match="from"):
        load_scenario(_scenario_with_refs(tmp_path, refs, {}))


class _Simulator:
    """その場で答えるユーザーシミュレータ。"""

    def __init__(self) -> None:
        self.asked: list[str] = []

    def ask(self, question: Question) -> str:
        self.asked.append(question.text)
        return f"シミュレータの回答: {question.text}"


def test_a_user_simulator_can_replace_the_scripted_user(tmp_path: Path) -> None:
    """run_scenario に user を与えると、台本の user の代わりにそれが尋ねられる。"""
    scenario = load_scenario(CONFORMANCE / "scenarios/suspend_resume.yaml")
    simulator = _Simulator()
    result = run_scenario(scenario, tmp_path, user=simulator)
    assert result.status == "completed"
    assert simulator.asked == ["主題は何か"]
    assert "suspend s1" not in result.summary
    final = result.final_snapshot
    assert final.files["s1.txt"] == sha256_text("シミュレータの回答: 主題は何か")


def _tree(root: Path, skip: set[str]) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.relative_to(root).as_posix() not in skip
    }


def test_packaged_conformance_matches_canonical() -> None:
    """契約適合テストのシナリオ一式は、パッケージにも同梱する（pip で入れた利用者が読めるように）。
    シナリオの形式は load_contract_schema で読めるので、写しには含めない。"""
    packaged = conformance_dir()
    assert _tree(packaged, set()) == _tree(CONFORMANCE, {"scenario.schema.json"})
    assert conformance_scenarios() == sorted((packaged / "scenarios").glob("*.yaml"))
    assert [p.name for p in conformance_scenarios()] == [p.name for p in SCENARIOS]


def test_packaged_scenarios_run(tmp_path: Path) -> None:
    for i, path in enumerate(conformance_scenarios()):
        result = run_scenario(load_scenario(path), tmp_path / str(i))
        assert result.problems == [], (path.name, result.problems)
