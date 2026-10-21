"""記録再生（契約 第9節）。

外から入ってくる値（LLM の応答、ユーザーの回答、運用者の選択、分類器の結果、指標の値）は、
すべて Recorder.call を通す。記録の鍵は呼び出しの種類と、ランタイムが決める鍵（ステージ、
訪問の回数、その訪問の中での順番など）と、要求の内容のハッシュ。
"""

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from harness_testing_framework.contract import JSONValue
from harness_testing_framework.runtime.checkpoint import canonical_json, sha256

type Key = Sequence[str | int]


def request_hash(request: JSONValue) -> str:
    return sha256(canonical_json(request))


def _entry_key(kind: str, key: Key, request: JSONValue) -> str:
    return json.dumps([kind, list(key), request_hash(request)], ensure_ascii=False)


class Recorder(Protocol):
    def call(
        self, kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]
    ) -> JSONValue: ...


class Passthrough:
    """記録も再生もしない。"""

    def call(
        self, kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]
    ) -> JSONValue:
        return live()


class Recording:
    """外を呼び、応答を JSON Lines に書き足す。"""

    def __init__(self, path: Path) -> None:
        self.path = path

    def call(
        self, kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]
    ) -> JSONValue:
        response = live()
        entry = {"key": _entry_key(kind, key, request), "response": response}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return response


class ReplayOnly:
    """記録から応答を返し、外を呼ばない。記録に無い呼び出しは Missing で止める。"""

    class Missing(LookupError):
        """記録に無い呼び出し。黙って外を呼ばない。"""

    def __init__(self, path: Path) -> None:
        self._entries: dict[str, JSONValue] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                self._entries[entry["key"]] = entry["response"]

    def call(
        self, kind: str, key: Key, request: JSONValue, live: Callable[[], JSONValue]
    ) -> JSONValue:
        entry_key = _entry_key(kind, key, request)
        if entry_key not in self._entries:
            raise ReplayOnly.Missing(entry_key)
        return self._entries[entry_key]
