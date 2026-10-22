"""要求の取り込みに束縛するユーザーシミュレータ（ペルソナ）。

- 三つ以上のペルソナが、intake の全ての質問（持ち帰る問いを含む）に、互いに違う空でない回答を返す
- 確率的な実行では、種からペルソナを選び、intake.md の「## 質問と回答」がそのペルソナの回答になる
- 持ち帰った問い（intake_questions）も依頼者に尋ね、回答を intake.md に書く
- 最初の質問で回答を保留すると実行は中断し、保存した状態を別のランタイムで読み戻し、ペルソナの回答で再開できる
"""

import json
from pathlib import Path

from software_factory.personas import CAP, FLOOR, PERSONAS, QUESTIONS, PersonaUser, persona_for
from software_factory.stages.probabilistic import INPUTS, run_set, runtime

from harness_testing_framework.runtime import BlobStore, RunState

ALL_QUESTIONS = [*QUESTIONS, CAP, FLOOR]


def test_personas_answer_every_question_differently() -> None:
    assert len(PERSONAS) >= 3
    assert len({p.name for p in PERSONAS}) == len(PERSONAS)
    for question in ALL_QUESTIONS:
        answers = [p.answer(question) for p in PERSONAS]
        assert all(a.strip() for a in answers)
        assert len(set(answers)) == len(PERSONAS), question
    assert [persona_for(s).name for s in range(6)] == [p.name for p in PERSONAS] * 2


def _intake_texts(runs_dir: Path, profile: str, n: int, seed: int) -> list[tuple[int, int, str]]:
    runs, store = run_set(profile, n, seed, runs_dir)
    reader = runtime(profile, runs_dir, store=store)
    out = []
    for run in runs.runs:
        for event in run.events:
            if event["event"] == "stage_end" and event["stage"] == "intake":
                snapshot = reader.snapshot(str(event["snapshot"]))
                text = store.get(snapshot.files["intake.md"]).decode("utf-8")
                out.append((run.seed, int(str(event["visit"])), text))
    return out


def test_intake_writes_the_personas_answers(tmp_path: Path) -> None:
    texts = _intake_texts(tmp_path, "markov", 30, 90000)
    asked_again = 0
    for seed, visit, text in texts:
        persona = persona_for(seed)
        for question in QUESTIONS:
            assert f"- Q: {question}\n  A: {persona.answer(question)}\n" in text
        if visit >= 2:
            asked_again += 1
            assert f"- Q: {CAP}\n  A: {persona.answer(CAP)}\n" in text
    assert asked_again > 0
    assert {persona_for(s).name for s, _, _ in texts} == {p.name for p in PERSONAS}


def test_deferred_answer_suspends_and_resumes_with_the_persona(tmp_path: Path) -> None:
    persona = PERSONAS[1]
    store = BlobStore(tmp_path / "store")
    first = runtime(
        "markov", tmp_path, store=store, user=PersonaUser(persona, defer_first=True)
    ).start(seed=0, inputs=INPUTS)
    assert first.status == "suspended"
    saved = first.state.to_json()
    question = json.loads(json.dumps(first.state.pending))["question"]["text"]
    assert question == QUESTIONS[0]

    resumed_runtime = runtime("markov", tmp_path, store=store, user=PersonaUser(persona))
    resumed = resumed_runtime.resume(RunState.from_json(saved), answer=persona.answer(question))
    assert resumed.status in ("completed", "aborted")
    kinds = [e["kind"] for e in resumed.events if e["event"] == "transition"]
    assert kinds[0] == "resume"
    final = resumed_runtime.snapshot(resumed.state.current)
    text = store.get(final.files["intake.md"]).decode("utf-8")
    for q in QUESTIONS:
        assert f"- Q: {q}\n  A: {persona.answer(q)}\n" in text
