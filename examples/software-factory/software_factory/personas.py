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
# analyze の変種 unclear が記憶 intake_questions に書く問い（tests/stochastic.yaml）。どのペルソナも、尋ねられても今は決めて
# いない（回答の後も未決のまま）。最初の三つの回答は、どのペルソナも要件に要る値（利用者と入力の場所、コードの形と上限、
# 端数と下限、無効なコードの扱い）を決めている。クラスは種だけで選ぶので、analyze の goal と needs_unclear の代表は、どの
# ペルソナの intake.md と組んでも記述どおりでなければならない（README の「人間のレビューで確かめてほしいこと」）
AFTER = "キャンペーンが終わった後も、割引コードを使えるようにしますか"
REUSE = "同じ購入者が同じコードを何回でも使えるようにしますか"


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
        "具体的なプロダクトマネージャ。値と境界まで答え、先のことは決める時期を答える",
        {
            WHO: "ネットショップの購入者。レジの画面でコードを入力する",
            KINDS: (
                "PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで。"
                "割引額の 1 円未満は切り捨て、定額で小計を超えたら 0 円にする"
            ),
            INVALID: "エラーにして、割引しない",
            AFTER: "キャンペーンの結果を見て、来月の末に決める",
            REUSE: "回数の制限は、法務と相談してから決める",
        },
        "仕様書のとおりにしてください",
    ),
    Persona(
        "vague_founder",
        "くだけた創業者。言い方はくだけているが、値は決めている。先のことはまだ決めていない",
        {
            WHO: "お客さん全般かな。レジの画面でコードを打ってもらう感じ",
            KINDS: (
                "PCT10 とか OFF500 みたいなコードで、10% 引きとか 500 円引きとか。百分率は半分（50%）まで。"
                "端数は切り捨てで、引きすぎたら 0 円でいい"
            ),
            INVALID: "使えないコードはエラーにして、割引しないで",
            AFTER: "そのうち考えるよ",
            REUSE: "うーん、まだ決めてない",
        },
        "そのへんはお任せします",
    ),
    Persona(
        "terse_engineer",
        "簡潔な技術者。記号と数だけで答える",
        {
            WHO: "購入者。レジの画面で入力",
            KINDS: "PCTnn と OFFnnn。nn は 1〜50。割引額は切り捨て。下限 0 円",
            INVALID: "ValueError",
            AFTER: "未定",
            REUSE: "未定（後で決める）",
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
