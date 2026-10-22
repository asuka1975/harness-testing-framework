"""software-factory の指標レジストリ（契約 7.2）。

コードベースの指標（build_passes、tests_pass、line_coverage、lint_errors）は、スナップショットの repo/ を
一時ディレクトリに書き出し、実在のツール（compileall と import、pytest、coverage、ruff）をこのインタプリタで
走らせて値にする。変更パスの範囲（out_of_scope_changes）は、view.baseline() との差を tasks.yaml の
タスクの範囲と比べる。

同じ内容には同じ値を返すので、ツールの結果は、指標名、引数、ファイルの内容のハッシュで覚えておく（adopting.md 第4節）。
分布テストでは同じコードベースの状態が何千回も評価されるため。tasks.yaml の読み込みも、内容ごとに覚える。
"""

import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Collection, Mapping
from pathlib import Path
from typing import Any

import yaml

from harness_testing_framework.contract import JSONValue, MetricError, SnapshotView

type Measure = Callable[[SnapshotView, Mapping[str, JSONValue]], bool | float]

TIMEOUT = 120
LINT_RULES = "E,F,W"
LINE_LENGTH = 100
_RESULTS: dict[str, bool | float] = {}
# 外側の pytest やカバレッジの設定が、指標の中で走らせるツールに漏れないようにする
_SCRUBBED = ("COV_CORE_", "COVERAGE_", "PYTEST_")
_IMPORT_ALL = """
import importlib, pathlib, sys
src = pathlib.Path(sys.argv[1])
for path in sorted(src.rglob("*.py")):
    parts = path.relative_to(src).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if parts:
        importlib.import_module(".".join(parts))
"""


def _str(args: Mapping[str, JSONValue], key: str, default: str) -> str:
    value = args.get(key, default)
    if not isinstance(value, str):
        raise MetricError(f"{key} が文字列でない")
    return value


def _plain(value: object) -> object:
    """引数を JSON に書ける形にする（ランタイムは読み取り専用の Mapping で渡す）。"""
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


def _strs(args: Mapping[str, JSONValue], key: str, default: list[str]) -> list[str]:
    value = args.get(key, default)
    if not isinstance(value, list | tuple) or not all(isinstance(v, str) for v in value):
        raise MetricError(f"{key} が文字列の一覧でない")
    return [str(v) for v in value]


def _text(view: SnapshotView, path: str) -> str:
    if not view.exists(path):
        raise MetricError(f"{path} が無い")
    return view.read_text(path)


def _section(text: str, heading: str) -> str:
    """「## heading」の見出しから次の「## 」の見出しまで。無ければ MetricError。"""
    m = re.search(rf"^## {re.escape(heading)}[ \t]*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if m is None:
        raise MetricError(f"「## {heading}」の節が無い")
    return m.group(1)


# --- コードベースの指標（実在のツール） ---


def _tree(view: SnapshotView, root: str) -> dict[str, bytes]:
    prefix = root.rstrip("/") + "/"
    files = {p[len(prefix) :]: view.read_bytes(p) for p in view.list_files(prefix)}
    if not files:
        raise MetricError(f"{prefix} にファイルが無い")
    return files


def _remember(
    name: str,
    args: Mapping[str, JSONValue],
    files: Mapping[str, bytes],
    compute: Callable[[Path], bool | float],
) -> bool | float:
    """files を一時ディレクトリに書き出して compute を走らせる。同じ指標、引数、内容なら前の結果を返す。"""
    digest = hashlib.sha256(name.encode())
    digest.update(json.dumps(_plain(args), sort_keys=True, ensure_ascii=False).encode())
    for path in sorted(files):
        digest.update(path.encode() + b"\0" + hashlib.sha256(files[path]).digest())
    key = digest.hexdigest()
    if key not in _RESULTS:
        with tempfile.TemporaryDirectory(prefix="software-factory-") as tmp:
            root = Path(tmp) / "repo"
            for rel, data in files.items():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            _RESULTS[key] = compute(root)
    return _RESULTS[key]


def _run(command: list[str], cwd: Path, src: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(_SCRUBBED)}
    env["PYTHONPATH"] = str(cwd / src)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, timeout=TIMEOUT, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise MetricError(f"{' '.join(command[1:4])} を実行できない: {e}") from e


def _pytest(tests: str) -> list[str]:
    return ["-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:pytest_cov", tests]


def build_passes(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    """src の下のすべての .py を byte-compile でき、すべてのモジュールを import できる。"""
    root, src = _str(args, "root", "repo"), _str(args, "src", "src")

    def compute(tree: Path) -> bool:
        if _run([sys.executable, "-m", "compileall", "-q", src], tree, src).returncode != 0:
            return False
        return _run([sys.executable, "-c", _IMPORT_ALL, src], tree, src).returncode == 0

    return bool(_remember("build_passes", args, _tree(view, root), compute))


def tests_pass(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    """tests の下のテストを pytest で走らせ、一件以上あって全部通る。"""
    root, src, tests = (
        _str(args, "root", "repo"),
        _str(args, "src", "src"),
        _str(args, "tests", "tests"),
    )

    def compute(tree: Path) -> bool:
        return _run([sys.executable, *_pytest(tests)], tree, src).returncode == 0

    return bool(_remember("tests_pass", args, _tree(view, root), compute))


def line_coverage(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """tests の下のテストを coverage の下で走らせた、src の行カバレッジ（百分率）。テストの成否によらない。"""
    root, src, tests = (
        _str(args, "root", "repo"),
        _str(args, "src", "src"),
        _str(args, "tests", "tests"),
    )

    def compute(tree: Path) -> float:
        data = ["--data-file", ".software-factory-coverage"]
        _run(
            [sys.executable, "-m", "coverage", "run", *data, f"--source={src}", *_pytest(tests)],
            tree,
            src,
        )
        report = _run(
            [sys.executable, "-m", "coverage", "json", *data, "-q", "-o", "coverage.json"],
            tree,
            src,
        )
        if report.returncode != 0:
            raise MetricError(
                f"カバレッジを測れない: {report.stdout.strip()} {report.stderr.strip()}"
            )
        totals: dict[str, Any] = json.loads((tree / "coverage.json").read_text("utf-8"))["totals"]
        return float(totals["percent_covered"])

    return float(_remember("line_coverage", args, _tree(view, root), compute))


def lint_errors(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """paths の下を ruff（設定ファイルを読まない。規則 E、F、W、行の長さ 100）で検査した違反の数。"""
    root, paths = _str(args, "root", "repo"), _strs(args, "paths", ["src", "tests"])

    def compute(tree: Path) -> float:
        present = [p for p in paths if (tree / p).exists()]
        if not present:
            return 0.0
        command = [sys.executable, "-m", "ruff", "check", "--isolated", "--no-cache"]
        command += ["--select", LINT_RULES, "--line-length", str(LINE_LENGTH)]
        result = _run([*command, "--output-format", "json", *present], tree, "src")
        if result.returncode not in (0, 1):
            raise MetricError(f"ruff が失敗した: {result.stderr.strip()}")
        return float(len(json.loads(result.stdout)))

    return float(_remember("lint_errors", args, _tree(view, root), compute))


def _task_paths(view: SnapshotView, path: str, fields: list[str]) -> set[str]:
    tasks = _tasks(view, path)
    allowed: set[str] = set()
    for task in tasks:
        for field in fields:
            values = task.get(field, [])
            if not isinstance(values, list | tuple) or not all(isinstance(v, str) for v in values):
                raise MetricError(f"{path} の {task.get('id')} の {field} が文字列の一覧でない")
            allowed.update(values)
    return allowed


def out_of_scope_changes(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """基準（開始時）のスナップショットから変わった prefix の下のパスのうち、tasks.yaml のタスクの fields に無いものの数。

    fields の項目は、ファイルのパスか、/ で終わるディレクトリ。追加、変更、削除のすべてを変化として数える。
    """
    base = view.baseline()
    if base is None:
        raise MetricError("比べる基準のスナップショットが無い")
    prefix = _str(args, "prefix", "repo/")
    allowed = _task_paths(view, _str(args, "tasks", "tasks.yaml"), _strs(args, "fields", ["paths"]))
    before = {p: base.read_bytes(p) for p in base.list_files(prefix)}
    after = {p: view.read_bytes(p) for p in view.list_files(prefix)}
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}

    def covered(path: str) -> bool:
        return path in allowed or any(a.endswith("/") and path.startswith(a) for a in allowed)

    return float(sum(1 for p in changed if not covered(p)))


# --- 文書の指標 ---


def file_nonempty(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    path = args.get("path")
    return isinstance(path, str) and view.exists(path) and bool(view.read_text(path).strip())


def files_nonempty(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    return all(file_nonempty(view, {"path": p}) for p in _strs(args, "paths", []))


def unanswered_questions(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """「## 質問と回答」の「- Q:」のうち、直後に空でない「A:」の行が無いものの数。質問が一つも無ければ測れない。"""
    lines = _section(_text(view, _str(args, "path", "intake.md")), "質問と回答").splitlines()
    questions = [i for i, line in enumerate(lines) if line.startswith("- Q:")]
    if not questions:
        raise MetricError("質問が無い")

    def answered(i: int) -> bool:
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        return nxt.startswith("A:") and bool(nxt[2:].strip())

    return float(sum(1 for i in questions if not answered(i)))


def _requirements(view: SnapshotView, path: str) -> dict[str, int]:
    """requirements.md の「## 要件」の「- REQ-n:」ごとの、受け入れ基準の行の数。"""
    found: dict[str, int] = {}
    current = None
    for line in _section(_text(view, path), "要件").splitlines():
        m = re.match(r"^- (REQ-\d+)[:：]", line)
        if m:
            current = m.group(1)
            found[current] = 0
        elif current and re.match(r"^\s+- 受け入れ基準[:：]\s*\S", line):
            found[current] += 1
    return found


def _requirement_ids(view: SnapshotView, args: Mapping[str, JSONValue]) -> list[str]:
    ids = list(_requirements(view, _str(args, "requirements", "requirements.md")))
    if not ids:
        raise MetricError("要件が無い")
    return ids


def requirement_count(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    return float(len(_requirements(view, _str(args, "path", "requirements.md"))))


def requirements_with_criteria(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """要件のうち、受け入れ基準を一つ以上持つものの割合。"""
    found = _requirements(view, _str(args, "path", "requirements.md"))
    if not found:
        raise MetricError("要件が無い")
    return sum(1 for n in found.values() if n) / len(found)


def _mentioned(ids: list[str], text: str) -> float:
    return sum(1 for i in ids if re.search(rf"\b{re.escape(i)}\b", text)) / len(ids)


def design_covers_requirements(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """requirements.md の要件のうち、design.md の「## 対応」の節が挙げるものの割合。"""
    ids = _requirement_ids(view, args)
    return _mentioned(ids, _section(_text(view, _str(args, "design", "design.md")), "対応"))


@functools.lru_cache(maxsize=64)
def _load_yaml(text: str) -> Any:
    """YAML を読む。同じ内容を何度も読むので覚える（結果は読むだけで、変えない）。"""
    return yaml.safe_load(text)


def _tasks(view: SnapshotView, path: str) -> list[dict[str, Any]]:
    try:
        doc = _load_yaml(_text(view, path))
    except yaml.YAMLError as e:
        raise MetricError(f"{path} を YAML として読めない: {e}") from e
    tasks = doc.get("tasks") if isinstance(doc, dict) else None
    if not isinstance(tasks, list) or not tasks or not all(isinstance(t, dict) for t in tasks):
        raise MetricError(f"{path} にタスクの一覧が無い")
    return tasks


def tasks_cover_requirements(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """requirements.md の要件のうち、tasks.yaml のどれかのタスクの requirements にあるものの割合。"""
    ids = _requirement_ids(view, args)
    covered = {
        r
        for t in _tasks(view, _str(args, "tasks", "tasks.yaml"))
        for r in t.get("requirements") or []
    }
    return sum(1 for i in ids if i in covered) / len(ids)


def task_paths_valid(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    """各タスクが、src_prefix の下のパスを paths に、tests_prefix の下のパスを tests に一つ以上持つ。"""
    src, tests = _str(args, "src_prefix", "repo/src/"), _str(args, "tests_prefix", "repo/tests/")

    def under(values: object, prefix: str) -> bool:
        return (
            isinstance(values, list)
            and bool(values)
            and all(isinstance(v, str) and v.startswith(prefix) for v in values)
        )

    return all(
        under(t.get("paths"), src) and under(t.get("tests"), tests)
        for t in _tasks(view, _str(args, "tasks", "tasks.yaml"))
    )


def verified_requirements(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """requirements.md の要件のうち、verification.md の表の行で結果が「合格」のものの割合。"""
    ids = _requirement_ids(view, args)
    text = _text(view, _str(args, "verification", "verification.md"))
    passed = {
        m.group(1) for m in re.finditer(r"^\|\s*(REQ-\d+)\s*\|[^\n]*\|\s*合格\s*\|\s*$", text, re.M)
    }
    return sum(1 for i in ids if i in passed) / len(ids)


def blocking_findings(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    try:
        review = json.loads(_text(view, _str(args, "path", "review.json")))
        return float(sum(1 for f in review["findings"] if f["blocking"]))
    except (ValueError, KeyError, TypeError) as e:
        raise MetricError(f"review.json の形が違う: {e}") from e


def changelog_covers_requirements(view: SnapshotView, args: Mapping[str, JSONValue]) -> float:
    """requirements.md の要件のうち、CHANGELOG.md が挙げるものの割合。"""
    ids = _requirement_ids(view, args)
    return _mentioned(ids, _text(view, _str(args, "changelog", "CHANGELOG.md")))


def _semver(text: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text.strip())
    if m is None:
        raise MetricError(f"版の形が違う: {text}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def version_bumped(view: SnapshotView, args: Mapping[str, JSONValue]) -> bool:
    """release.json の version が、パッケージの __version__ より新しい。"""
    try:
        released = json.loads(_text(view, _str(args, "release", "release.json")))["version"]
    except (ValueError, KeyError, TypeError) as e:
        raise MetricError(f"release.json の形が違う: {e}") from e
    package = _text(view, _str(args, "package", "repo/src/shopcart/__init__.py"))
    m = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", package, re.M)
    if m is None or not isinstance(released, str):
        raise MetricError("版が無い")
    return _semver(released) > _semver(m.group(1))


class _Registry:
    def __init__(self, measures: Mapping[str, Measure]) -> None:
        self._measures = dict(measures)

    def names(self) -> Collection[str]:
        return self._measures.keys()

    def measure(self, name: str, view: SnapshotView, args: Mapping[str, JSONValue]) -> bool | float:
        if name not in self._measures:
            raise MetricError(f"指標 {name} は無い")
        return self._measures[name](view, args)


REGISTRY = _Registry(
    {
        "build_passes": build_passes,
        "tests_pass": tests_pass,
        "line_coverage": line_coverage,
        "lint_errors": lint_errors,
        "out_of_scope_changes": out_of_scope_changes,
        "file_nonempty": file_nonempty,
        "files_nonempty": files_nonempty,
        "unanswered_questions": unanswered_questions,
        "requirement_count": requirement_count,
        "requirements_with_criteria": requirements_with_criteria,
        "design_covers_requirements": design_covers_requirements,
        "tasks_cover_requirements": tasks_cover_requirements,
        "task_paths_valid": task_paths_valid,
        "verified_requirements": verified_requirements,
        "blocking_findings": blocking_findings,
        "changelog_covers_requirements": changelog_covers_requirements,
        "version_bumped": version_bumped,
    }
)
