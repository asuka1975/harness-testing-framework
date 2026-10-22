"""スナップショット（契約 第5節）と、作業領域との行き来、restore と overlay（契約 2.1・2.3）。"""

import hashlib
import json
import math
import os
import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any

from harness_testing_framework.contract import JSONValue
from harness_testing_framework.runtime.model import Stage, Workflow, covered_by

FORMAT_VERSION = "0.1"


def _number(value: float) -> str:
    """ECMAScript の Number::toString（RFC 8785 第3.2.2.3節）と同じ書き方。"""
    if not math.isfinite(value):
        raise ValueError(f"有限でない数は書けない: {value}")
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    # repr は往復できる最短の桁を与える。桁 digits と、値 = 0.digits × 10^n となる n を求める
    exponent = Decimal(repr(abs(value))).normalize().as_tuple()
    digits = "".join(map(str, exponent.digits))
    assert isinstance(exponent.exponent, int)
    k, n = len(digits), exponent.exponent + len(digits)
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    mantissa = digits[0] + ("." + digits[1:] if k > 1 else "")
    e = n - 1
    return f"{sign}{mantissa}e{'+' if e > 0 else '-'}{abs(e)}"


def _encode(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        # 2^53 以上の整数は、浮動小数点数として読まれる数と同じ書き方にする
        return str(value) if abs(value) < 2**53 else _number(float(value))
    if isinstance(value, float):
        return _number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list | tuple):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, Mapping):
        items = sorted(value.items())
        return "{" + ",".join(f"{_encode(k)}:{_encode(v)}" for k, v in items) + "}"
    raise TypeError(f"JSON で表せない値: {value!r}")


def canonical_json(value: Any) -> bytes:
    """マニフェストの正規形（契約 第5節）。

    キーは符号位置の順、区切りに空白なし、文字は UTF-8 のまま（制御文字などは JSON の規則で
    エスケープ）、数は ECMAScript の Number::toString の書き方、末尾の改行なし。
    """
    return _encode(value).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Annotation:
    kind: str
    stage: str
    note: str
    by: str = ""


@dataclass(frozen=True)
class Snapshot:
    files: Mapping[str, str] = field(default_factory=dict)
    memory: Mapping[str, JSONValue] = field(default_factory=dict)
    gates: tuple[str, ...] = ()
    annotations: tuple[Annotation, ...] = ()

    def manifest(self) -> dict[str, Any]:
        annotations: list[dict[str, str]] = []
        for a in self.annotations:
            item = {"kind": a.kind, "stage": a.stage, "note": a.note}
            if a.by:
                item["by"] = a.by
            annotations.append(item)
        return {
            "format_version": FORMAT_VERSION,
            "files": dict(self.files),
            "memory": dict(self.memory),
            "gates": list(self.gates),
            "annotations": annotations,
        }

    @property
    def id(self) -> str:
        return sha256(canonical_json(self.manifest()))

    def with_gate(self, phase_id: str, phase_order: Sequence[str]) -> "Snapshot":
        gates = set(self.gates) | {phase_id}
        return replace(self, gates=tuple(p for p in phase_order if p in gates))

    def with_annotation(self, annotation: Annotation) -> "Snapshot":
        return replace(self, annotations=(*self.annotations, annotation))

    @staticmethod
    def from_manifest(manifest: Mapping[str, Any]) -> "Snapshot":
        return Snapshot(
            files=MappingProxyType(dict(manifest["files"])),
            memory=MappingProxyType(dict(manifest["memory"])),
            gates=tuple(manifest["gates"]),
            annotations=tuple(Annotation(**a) for a in manifest["annotations"]),
        )


class BlobStore:
    """内容アドレスのファイル置き場と、スナップショットのマニフェストの置き場。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "blobs").mkdir(parents=True, exist_ok=True)
        (root / "snapshots").mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes) -> str:
        """内容を置き、その SHA-256 を返す。"""
        digest = sha256(data)
        path = self.root / "blobs" / digest
        if not path.exists():
            path.write_bytes(data)
        return digest

    def get(self, digest: str) -> bytes:
        """内容を SHA-256 で読む。スナップショットのファイル（snapshot.files[パス]）も、分類器が見た状態文書
        （実行記録の evaluation、コーパスとトリアージの項目の state）も、これで読める。"""
        return (self.root / "blobs" / digest).read_bytes()

    def put_snapshot(self, snapshot: Snapshot) -> str:
        """スナップショットのマニフェストを置き、その id を返す。"""
        path = self.root / "snapshots" / f"{snapshot.id}.json"
        if not path.exists():
            path.write_bytes(canonical_json(snapshot.manifest()))
        return snapshot.id

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        """スナップショットを id で読む。"""
        manifest = json.loads((self.root / "snapshots" / f"{snapshot_id}.json").read_bytes())
        return Snapshot.from_manifest(manifest)


def initial_snapshot(store: BlobStore, inputs: Mapping[str, bytes]) -> Snapshot:
    """ワークフローの inputs を置いた最初のスナップショット。"""
    return Snapshot(files=MappingProxyType({p: store.put(d) for p, d in sorted(inputs.items())}))


def materialize(snapshot: Snapshot, store: BlobStore, workspace: Path) -> None:
    """スナップショットのファイルだけを持つ作業領域を作る。"""
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    for path, digest in snapshot.files.items():
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(store.get(digest))


def _walk(workspace: Path) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(workspace):
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            if path.is_symlink() or path.is_file():
                yield path.relative_to(workspace).as_posix()


@dataclass(frozen=True)
class Capture:
    snapshot: Snapshot
    violations: tuple[str, ...]
    discarded: tuple[str, ...]


def capture(
    workspace: Path,
    workflow: Workflow,
    stage: Stage,
    before: Snapshot,
    store: BlobStore,
    memory: Mapping[str, JSONValue],
) -> Capture:
    """作業領域を走査して終了時スナップショットを作る（契約 2.1 の 3〜5）。

    範囲外のファイルは捨てる。範囲内で、このステージの writes に無いパスの変化
    （内容の変更、新しいファイル、削除）は契約違反として報告する。
    """
    scope = workflow.scope
    files: dict[str, str] = {}
    discarded: list[str] = []
    links: list[str] = []
    for path in sorted(_walk(workspace)):
        if (workspace / path).is_symlink():
            # 作業領域の外を指しうるので、範囲の内外を問わず拒む
            links.append(f"{stage.id} が記号リンク {path} を置いた")
        elif covered_by(path, scope):
            files[path] = store.put((workspace / path).read_bytes())
        else:
            discarded.append(path)
    violations = links + [
        f"{stage.id} が writes に無い {path} を変えた"
        for path in sorted(set(files) | set(before.files))
        if files.get(path) != before.files.get(path) and not covered_by(path, stage.writes)
    ]
    snapshot = replace(
        before,
        files=MappingProxyType(files),
        memory=MappingProxyType(dict(memory)),
    )
    return Capture(snapshot, tuple(violations), tuple(discarded))


def restore_overlay(
    start: Snapshot, current: Snapshot, carry: Sequence[str]
) -> tuple[Snapshot, tuple[str, ...]]:
    """戻り先の開始時スナップショットに、現在の記憶の carry の項目だけを重ねる（契約 2.3）。

    返り値の二つ目は、現在の記憶に無かったので重ねなかった項目。
    """
    memory = dict(start.memory)
    missing: list[str] = []
    for name in carry:
        if name in current.memory:
            memory[name] = current.memory[name]
        else:
            missing.append(name)
    return replace(start, memory=MappingProxyType(memory)), tuple(missing)


class SnapshotReader:
    """読み取り専用のスナップショット（契約 7.2 の view）。"""

    def __init__(
        self, snapshot: Snapshot, store: BlobStore, baseline: Snapshot | None = None
    ) -> None:
        self._snapshot = snapshot
        self._store = store
        self._baseline = baseline

    def exists(self, path: str) -> bool:
        return path in self._snapshot.files

    def read_bytes(self, path: str) -> bytes:
        if path not in self._snapshot.files:
            raise FileNotFoundError(path)
        return self._store.get(self._snapshot.files[path])

    def read_text(self, path: str) -> str:
        return self.read_bytes(path).decode("utf-8")

    def list_files(self, prefix: str = "") -> Sequence[str]:
        return sorted(p for p in self._snapshot.files if p.startswith(prefix))

    def memory(self, name: str) -> JSONValue:
        return self._snapshot.memory.get(name)

    def baseline(self) -> "SnapshotReader | None":
        if self._baseline is None:
            return None
        return SnapshotReader(self._baseline, self._store)
