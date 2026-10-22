"""要求の取り込み（intake）に束縛するユーザーシミュレータ。依頼者のペルソナごとに決まった回答を返す。

UserIO.ask は質問しか受け取らない（実行の種や文脈を受け取らない）ので、実行ごとにペルソナを変えるには、種から
ペルソナを選んでランタイムを組み立て直す（persona_for と probabilistic.runtime）。分布テストの実行では回答を保留しない。
中断と再開を確かめる時だけ defer_first で最初の質問を保留する。
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

from harness_testing_framework.contract import AwaitingAnswer, Question

WHO = "この機能を使うのは誰ですか"
KINDS = "配る割引コードの種類と上限は何ですか"
INVALID = "使えないコードが入力された時はどうしますか"
QUESTIONS = (WHO, KINDS, INVALID)
# analyze の変種 unclear が記憶 intake_questions に書く問い（tests/stochastic.yaml）
CAP = "百分率の割引の上限は何 % ですか"
FLOOR = "定額の割引が小計を超えた時、支払額はどうなりますか"


@dataclass(frozen=True)
class Persona:
    name: str
    description: str
    answers: Mapping[str, str]
    fallback: str

    def answer(self, question: str) -> str:
        return self.answers.get(question, self.fallback)


PERSONAS = (
    Persona(
        "precise_pm",
        "具体的なプロダクトマネージャ。上限や境界の値まで答える",
        {
            WHO: "ネットショップの購入者。レジの画面でコードを入力する",
            KINDS: "PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで",
            INVALID: "エラーにして、割引しない",
            CAP: "50% まで",
            FLOOR: "0 円にする。マイナスにはしない",
        },
        "仕様書のとおりにしてください",
    ),
    Persona(
        "vague_founder",
        "曖昧な創業者。方向は示すが、値は決めていない",
        {
            WHO: "お客さん全般かな",
            KINDS: "いい感じに割り引けるもの。上限はまだ決めていない",
            INVALID: "うまくやってほしい",
            CAP: "常識的な範囲で",
            FLOOR: "そこはお任せします",
        },
        "そのへんはお任せします",
    ),
    Persona(
        "terse_engineer",
        "簡潔な技術者。記号と数だけで答える",
        {
            WHO: "購入者",
            KINDS: "PCTnn と OFFnnn。nn は 1〜50",
            INVALID: "ValueError",
            CAP: "50",
            FLOOR: "0 円で止める",
        },
        "要件の文書を見て",
    ),
)


def persona_for(seed: int) -> Persona:
    """実行の種からペルソナを選ぶ（種の順に巡る）。"""
    return PERSONAS[seed % len(PERSONAS)]


@dataclass
class PersonaUser:
    """ペルソナに従ってその場で答える UserIO。defer_first なら最初の質問だけ回答を保留する。"""

    persona: Persona
    defer_first: bool = False
    asked: list[str] = field(default_factory=list)

    def ask(self, question: Question) -> str:
        self.asked.append(question.text)
        if self.defer_first and len(self.asked) == 1:
            raise AwaitingAnswer(question)
        return self.persona.answer(question.text)
