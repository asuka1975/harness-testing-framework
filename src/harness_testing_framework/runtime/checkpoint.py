"""スナップショット（契約 第5節）と、作業領域との行き来、restore と overlay（契約 2.1・2.3）。"""

import hashlib
import json
import os
import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from harness_testing_framework.contract import JSONValue
from harness_testing_framework.runtime.model import Stage, Workflow, covered_by

FORMAT_VERSION = "0.1"


def canonical_json(value: Any) -> bytes:
    """マニフェストの正規形（契約 第5節）。"""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


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
        digest = sha256(data)
        path = self.root / "blobs" / digest
        if not path.exists():
            path.write_bytes(data)
        return digest

    def get(self, digest: str) -> bytes:
        return (self.root / "blobs" / digest).read_bytes()

    def put_snapshot(self, snapshot: Snapshot) -> str:
        path = self.root / "snapshots" / f"{snapshot.id}.json"
        if not path.exists():
            path.write_bytes(canonical_json(snapshot.manifest()))
        return snapshot.id

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
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
    for dirpath, _, filenames in os.walk(workspace):
        for name in filenames:
            yield (Path(dirpath) / name).relative_to(workspace).as_posix()


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
    for path in sorted(_walk(workspace)):
        if covered_by(path, scope):
            files[path] = store.put((workspace / path).read_bytes())
        else:
            discarded.append(path)
    violations = [
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

    def __init__(self, snapshot: Snapshot, store: BlobStore) -> None:
        self._snapshot = snapshot
        self._store = store

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
