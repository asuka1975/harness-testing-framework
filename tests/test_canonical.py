"""マニフェストの正規形（契約 第5節）。

他の言語の実装が同じスナップショットの id を出せるようにする。数の書き方は
ECMAScript の Number::toString（RFC 8785 第3.2.2.3節）に従う。数の例は RFC 8785 の付録 B から。
"""

import hashlib
import json
from pathlib import Path

import pytest

from harness_testing_framework.runtime import Snapshot, canonical_json

ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads((ROOT / "contract/conformance/manifests.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("bits", "text"),
    [
        ("0000000000000000", "0"),
        ("8000000000000000", "0"),
        ("0000000000000001", "5e-324"),
        ("8000000000000001", "-5e-324"),
        ("7fefffffffffffff", "1.7976931348623157e+308"),
        ("4340000000000000", "9007199254740992"),
        ("c340000000000000", "-9007199254740992"),
        ("4430000000000000", "295147905179352830000"),
        ("44b52d02c7e14af5", "9.999999999999997e+22"),
        ("44b52d02c7e14af6", "1e+23"),
        ("444b1ae4d6e2ef50", "1e+21"),
        ("444b1ae4d6e2ef4f", "999999999999999900000"),
        ("3eb0c6f7a0b5ed8d", "0.000001"),
        ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
        ("41b3de4355555555", "333333333.3333333"),
    ],
)
def test_rfc8785_numbers(bits: str, text: str) -> None:
    value = _from_bits(bits)
    assert canonical_json(value) == text.encode()


def _from_bits(bits: str) -> float:
    import struct

    result: float = struct.unpack(">d", bytes.fromhex(bits))[0]
    return result


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        canonical_json(value)


def test_integers_and_integral_floats_print_alike() -> None:
    assert canonical_json(1) == canonical_json(1.0) == b"1"
    assert canonical_json([True, False, None]) == b"[true,false,null]"


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_manifest_vectors(vector: dict[str, object]) -> None:
    manifest = vector["manifest"]
    assert isinstance(manifest, dict)
    canonical = canonical_json(manifest)
    assert canonical.decode("utf-8") == vector["canonical"]
    assert hashlib.sha256(canonical).hexdigest() == vector["id"]
    assert Snapshot.from_manifest(manifest).id == vector["id"]


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (2**53, "9007199254740992"),
        (2**53 + 1, "9007199254740992"),
        (10**21, "1e+21"),
        (-(10**22), "-1e+22"),
    ],
)
def test_large_integers_print_like_numbers(value: int, text: str) -> None:
    assert canonical_json(value) == text.encode()
