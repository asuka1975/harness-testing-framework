"""tests/scenarios/ のシナリオの YAML を作る。

各シナリオの期待する実行記録の要約（trace）は、下の Run の呼び出しで遷移を一つずつ手で並べる（実装より先に書く）。
inputs と expect.starts のファイルは、フィクスチャへの参照（`{from: パス}`。ディレクトリは鍵と from を / で終える）で
書く。内容は load_scenario が読む時にフィクスチャから取るので、フィクスチャの中身を変えても作り直さなくてよい
（ok のフィクスチャのファイルを足したり消したりした時は作り直す）。

    python -m software_factory.scenarios   # tests/scenarios/*.yaml を書き直す

tests/test_scenarios.py が、コミットした YAML とここで作るものが一致することを確かめる。
"""

from typing import Any

import yaml

from software_factory.personas import AFTER, INVALID, KINDS, PERSONAS, QUESTIONS, REUSE, WHO
from software_factory.stages.deterministic import FIXTURES as FX
from software_factory.stages.deterministic import SCENARIOS as OUT
from software_factory.stages.probabilistic import TABLE, WORKFLOW_MODEL

GENERATED: dict[str, str] = {}


class Dumper(yaml.SafeDumper):
    pass


def _str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


Dumper.add_representer(str, _str)


def ref(rel: str) -> dict[str, str]:
    """フィクスチャのファイルかディレクトリ（/ で終える）への参照。シナリオのファイルからの相対パス。"""
    return {"from": f"../{FX.name}/{rel}"}


def refs(rel: str) -> dict[str, Any]:
    """フィクスチャのディレクトリの下の各ファイルを、作業領域の同じ相対パスに置く参照。"""
    root = FX / rel
    return {
        str(p.relative_to(root)): ref(f"{rel}/{p.relative_to(root)}")
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


# ワークフローの inputs: 依頼と、変更前のコードベース（ディレクトリごと）
INPUTS = {"feature_request.md": ref("inputs/feature_request.md"), "repo/": ref("inputs/repo/")}
GOAL = {"choice": "goal", "confidence": 0.9}


def cls(choice: str | None, confidence: float = 0.9) -> dict[str, Any]:
    return {"choice": choice, "confidence": confidence}


ORDER = [
    "intake",
    "analyze",
    "design",
    "plan_tasks",
    "implement",
    "unit_test",
    "acceptance",
    "review",
    "release",
]
FIX = {s: f"{s}/ok" for s in ORDER}
# 偽の本体は、訪問のたびに memory_out のすべての項目を書く（adopting.md 第2.1節）。台本が書かない項目は、goal の変種
# （tests/stochastic.yaml の ok）の値を書く。書かないと、持ち帰った前の値が状態文書に残る
MEMORY_OUT = {s.id: s.memory_out for s in WORKFLOW_MODEL.stages}
OK_MEMORY: dict[str, dict[str, Any]] = {
    s: dict(TABLE["variants"][s]["ok"].get("memory", {})) for s in ORDER
}
OK_VISIT = {s: {"fixture": f, "classify": GOAL} for s, f in FIX.items()}


def with_memory_out(stage: str, spec: dict[str, Any]) -> dict[str, Any]:
    """台本に、書いていない memory_out の項目を goal の変種の値で足す（例外で終わる訪問はそのまま）。"""
    if "raise" in spec or not MEMORY_OUT[stage]:
        return spec
    return {**spec, "memory": OK_MEMORY[stage] | dict(spec.get("memory", {}))}


def ok_memory(*stages: str) -> dict[str, Any]:
    """各ステージの goal の訪問が順に書いた記憶（開始時スナップショットに残る上流の記憶）。"""
    out: dict[str, Any] = {}
    for s in stages:
        out |= OK_MEMORY[s]
    return out


PHASE_OF = {
    "intake": "discovery",
    "analyze": "discovery",
    "design": "architecture",
    "plan_tasks": "architecture",
    "implement": "construction",
    "unit_test": "construction",
    "acceptance": "assurance",
    "review": "assurance",
    "release": "delivery",
}
LAST = {"analyze", "plan_tasks", "unit_test", "review", "release"}


def ok_files(*stages: str) -> dict[str, Any]:
    """inputs に、各ステージの ok のフィクスチャを重ねた範囲内のファイル（repo/ は変更前のまま）。"""
    out: dict[str, Any] = dict(INPUTS)
    for s in stages:
        added = refs(FIX[s])
        assert not any(k.startswith("repo/") for k in added), s
        out |= added
    return out


def ok_files_by_file(*stages: str) -> dict[str, Any]:
    """ok_files と同じ範囲を、inputs の repo/ もファイルごとに展開して書く。implement の ok のフィクスチャのように repo/ の
    下のファイルを置き換えるステージを重ねられる（ディレクトリの参照と、その下のファイルの参照を混ぜない）。"""
    out = refs("inputs")
    for s in stages:
        out |= refs(FIX[s])
    return out


class Run:
    def __init__(self) -> None:
        self.trace: list[str] = []
        self.count: dict[str, int] = {}
        self.visits: dict[str, Any] = {}
        self.gates: dict[str, Any] = {}

    def start(self, stage: str, spec: dict[str, Any] | None = None) -> str:
        self.count[stage] = self.count.get(stage, 0) + 1
        key = f"{stage}#{self.count[stage]}"
        self.trace.append(f"start {key}")
        self.visits[key] = with_memory_out(stage, spec if spec is not None else OK_VISIT[stage])
        return key

    def eval(self, stage: str, outcome: str) -> None:
        self.trace.append(f"eval stage {stage} = {outcome}")

    def gate(self, stage: str, outcome: str = "goal", spec: dict[str, Any] | None = None) -> None:
        phase = PHASE_OF[stage]
        self.gates[f"{phase}#{self.count[stage]}"] = spec if spec is not None else GOAL
        self.trace.append(f"eval phase {phase} = {outcome}")

    def line(self, *lines: str) -> None:
        self.trace += lines

    def advance(self, stage: str) -> None:
        """goal の後: 最終ステージならゲート、次へ（最後なら完了）。"""
        if stage in LAST:
            self.gate(stage)
            self.line(f"gate_pass {stage}")
        i = ORDER.index(stage) + 1
        self.line(f"next {stage} -> {ORDER[i]}" if i < len(ORDER) else "complete")

    def goal(self, stage: str, spec: dict[str, Any] | None = None) -> None:
        self.start(stage, spec)
        self.eval(stage, "goal")
        self.advance(stage)

    def through(self, first: str, last: str = "release") -> None:
        for s in ORDER[ORDER.index(first) : ORDER.index(last) + 1]:
            self.goal(s)
        if last == "release":
            self.line("end completed")


def write(name: str, description: str, run: Run, expect: dict[str, Any], **extra: Any) -> None:
    doc: dict[str, Any] = {
        "scenario": name,
        "description": description,
        "workflow": "../../workflow.yaml",
        "seed": 11,
        "inputs": INPUTS,
        "visits": run.visits,
        "gates": run.gates,
        **extra,
        "expect": {"status": expect.pop("status", "completed"), "trace": run.trace, **expect},
    }
    GENERATED[f"{name}.yaml"] = yaml.dump(
        doc, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=100
    )


Q_BASE = list(QUESTIONS)
OPEN_Q = [AFTER, REUSE]
UNCLEAR = {
    "fixture": "analyze/unclear",
    "memory": {"intake_questions": OPEN_Q},
    "classify": cls("needs_unclear"),
}

# --- 1. 正常系と、回答の保留による中断と再開 ---
r = Run()
r.line("start intake#1", "suspend intake", "end suspended", "resume intake")
r.goal("intake", {**OK_VISIT["intake"], "ask": Q_BASE})
r.through("analyze")
write(
    "happy_path_user_suspend",
    "intake が依頼者に三つ尋ね、二つ目の回答の保留で中断し、回答を得て再開する（一つ目の回答は再生する）。"
    "その後は全ステージが一回で goal に達し、5 つのゲートを通って完了する（next、中断と再開）",
    r,
    {},
    user=[
        {"answer": PERSONAS[0].answer(WHO)},
        {"defer": True},
        {"answer": PERSONAS[0].answer(KINDS)},
        {"answer": PERSONAS[0].answer(INVALID)},
    ],
)

# --- 2. 要件を決められず、問いを持ち帰って依頼者に尋ね直す ---
r = Run()
r.goal("intake")
r.start("analyze", UNCLEAR)
r.eval("analyze", "needs_unclear")
r.line("rollback analyze -> intake [needs_unclear 1]")
r.goal("intake", {**OK_VISIT["intake"], "ask": OPEN_Q})
r.through("analyze")
write(
    "needs_unclear_asks_again",
    "analyze が intake.md の回答から要件を決められず、問いを記憶 intake_questions に書いて intake に戻る。"
    "intake は持ち帰った問いを依頼者に尋ね、analyze が要件を決める（rollback と carry、ユーザー回答待ちのステージへの戻り）",
    r,
    {
        "starts": {
            "intake#2": {"files": INPUTS, "memory": {"intake_questions": OPEN_Q}, "gates": []}
        },
        # 問いが解けた analyze#2 は空の一覧を書くので、持ち帰った問いは最後の記憶に残らない
        "memory": {"intake_questions": []},
    },
    user=[{"answer": PERSONAS[0].answer(q)} for q in OPEN_Q],
)

# --- 3. 設計が要件の不足を見つけ、フェーズ境界を越えて analyze に戻る ---
GAPS = ["REQ-3 と REQ-4: コードを Cart のどの操作で受け取るかが決まっていない"]
r = Run()
r.through("intake", "analyze")
r.start(
    "design",
    {
        "fixture": "design/gap",
        "memory": {"requirement_gaps": GAPS},
        "classify": cls("requirements_gap"),
    },
)
r.eval("design", "requirements_gap")
r.line("rollback design -> analyze [requirements_gap 1] crossing")
r.through("analyze")
write(
    "design_gap_crosses_phase",
    "design が要件の曖昧さを見つけ、記憶 requirement_gaps を持ってフェーズ境界を越えて analyze に戻る。"
    "discovery のゲートは未通過に戻り、analyze が再び goal に達した時に評価し直す（フェーズ境界越え、ゲートの再評価）",
    r,
    {
        "starts": {
            "analyze#2": {
                "files": ok_files("intake"),
                "memory": {"requirement_gaps": GAPS},
                "gates": [],
            }
        },
        # design#2 と acceptance が空の一覧を書くので、持ち帰った食い違いは最後の記憶に残らない
        "memory": {"requirement_gaps": []},
    },
)

# --- 4. 検証が要件の不合格を見つけ、フェーズ境界を越えて実装に戻る ---
UNMET = [
    "REQ-1: 小計 333 円に PCT10 を適用すると支払額が 299 円になる（割引額の 1 円未満を切り捨てれば 300 円）。"
    "repo/src/shopcart/discount.py の Discount.apply が支払額を切り捨てている"
]
r = Run()
r.through("intake", "unit_test")
r.start(
    "acceptance",
    {
        "fixture": "acceptance/unmet",
        "memory": {"unmet_requirements": UNMET, "requirement_gaps": []},
        "classify": cls("requirement_unmet"),
    },
)
r.eval("acceptance", "requirement_unmet")
r.line("rollback acceptance -> implement [requirement_unmet 1] crossing")
r.through("implement")
write(
    "acceptance_unmet_crosses_phase",
    "acceptance が REQ-1 の不合格を見つけ、記憶 unmet_requirements を持って assurance から construction の implement に戻る。"
    "construction のゲートを評価し直し、単体テストもやり直す（フェーズ境界越え、ゲートの再評価、実在の指標による再評価）",
    r,
    {
        "starts": {
            "implement#2": {
                "files": ok_files("intake", "analyze", "design", "plan_tasks"),
                "memory": ok_memory("intake", "analyze", "design", "plan_tasks")
                | {"unmet_requirements": UNMET},
                "gates": ["discovery", "architecture"],
            }
        },
        "memory": {"unmet_requirements": []},
    },
)

# --- 5. 実装の lint 違反で自分自身に戻り、単体テストの不足で自分自身に戻り、欠陥で実装に戻る ---
VIOL = ["lint: repo/src/shopcart/discount.py に使っていない import と長すぎる行がある"]
GAPS_T = ["REQ-1、REQ-2、REQ-3 の受け入れ基準にテストが無い"]
FAILING = [
    "test_percent_discount_rounds_the_discount_down: 333 円の PCT10 が 299 円になる（期待 300 円）"
]
r = Run()
r.through("intake", "plan_tasks")
r.start(
    "implement",
    {
        "fixture": "implement/lint",
        "memory": {"impl_violations": VIOL},
        "classify": cls("quality_violation"),
    },
)
r.eval("implement", "quality_violation")
r.line("rollback implement -> implement [quality_violation 1]")
r.goal("implement")
r.start(
    "unit_test",
    {
        "fixture": "unit_test/thin",
        "memory": {"coverage_gaps": GAPS_T, "failing_tests": []},
        "classify": cls("tests_insufficient"),
    },
)
r.eval("unit_test", "tests_insufficient")
r.line("rollback unit_test -> unit_test [tests_insufficient 1]")
r.start(
    "unit_test",
    {
        "fixture": "unit_test/defect_found",
        "memory": {"failing_tests": FAILING, "coverage_gaps": []},
        "classify": cls("impl_defect"),
    },
)
r.eval("unit_test", "impl_defect")
r.line("rollback unit_test -> implement [impl_defect 1]")
r.goal("implement", {"fixture": "implement/ok_fixed", "classify": GOAL})
r.start("unit_test", {"fixture": "unit_test/defect_passed", "classify": GOAL})
r.eval("unit_test", "goal")
r.advance("unit_test")
r.through("acceptance")
before_impl = ok_files("intake", "analyze", "design", "plan_tasks")
write(
    "construction_rollbacks",
    "implement の lint 違反（実在の ruff）で自分自身に戻り、unit_test のカバレッジ不足（実在の coverage）で自分自身に戻り、"
    "unit_test のテストの失敗（実在の pytest）で implement に戻る。直した実装で同じテストが通る（rollback、自分自身への rollback、carry の積み重ね）",
    r,
    {
        "starts": {
            "implement#2": {
                "files": before_impl,
                "memory": ok_memory("intake", "analyze", "design", "plan_tasks")
                | {"impl_violations": VIOL},
                "gates": ["discovery", "architecture"],
            },
            "implement#3": {
                "files": before_impl,
                # implement#2 の開始時スナップショット（持ち帰った impl_violations を含む）に failing_tests を重ねる
                "memory": ok_memory("intake", "analyze", "design", "plan_tasks")
                | {"impl_violations": VIOL, "failing_tests": FAILING},
                "gates": ["discovery", "architecture"],
            },
        },
        "memory": {"failing_tests": [], "impl_violations": []},
    },
)

# --- 6. 要件の不明が三回続いて max を超え、運用者が goal 到達扱いで続行する ---
r = Run()
r.goal("intake")
for n in (1, 2):
    r.start("analyze", UNCLEAR)
    r.eval("analyze", "needs_unclear")
    r.line(f"rollback analyze -> intake [needs_unclear {n}]")
    r.goal("intake")
r.start("analyze", UNCLEAR)
r.eval("analyze", "needs_unclear")
r.line("escalation analyze max_exceeded -> continue_as_goal")
r.gate("analyze")
r.line("gate_pass analyze", "next analyze -> design")
r.through("design")
write(
    "needs_unclear_max_exceeded",
    "analyze の needs_unclear が三回続いて辺の max（2）を超え、運用者が goal 到達扱いで続行する。analyze は discovery の"
    "最終ステージなのでゲートを評価し、三つの要件のまま後のフェーズの実在の指標を通る（max 超過、goal 到達扱い）",
    r,
    {"annotations": 1},
    operator=[
        {"kind": "continue_as_goal", "note": "未決事項は次の版で決める", "by": "プロダクトオーナー"}
    ],
)

# --- 7. レビューの分類の確信度が低く unknown になり、運用者が再実行する ---
r = Run()
r.through("intake", "acceptance")
r.start("review", {"fixture": "review/ok", "classify": cls("goal", 0.3)})
r.eval("review", "unknown")
r.line("escalation review unknown -> rerun")
r.through("review")
write(
    "review_low_confidence_rerun",
    "review の分類の確信度が閾値（0.5）未満で unknown になり、運用者が再実行を選ぶ。review は新しい訪問としてやり直す（unknown、再実行）",
    r,
    {},
    operator=[{"kind": "rerun"}],
)

# --- 8. リリースが判断できず、運用者がレビューの指摘を持たせて実装に戻す ---
FINDINGS = ["（修正を要しない）parse_code の docstring にコードの形式の例があると読みやすい"]
r = Run()
r.through("intake", "acceptance")
r.goal(
    "review", {**OK_VISIT["review"], "memory": {"review_findings": FINDINGS, "design_issues": []}}
)
r.start("release", {"fixture": "release/unknown", "classify": cls(None, 0.0)})
r.eval("release", "unknown")
r.line(
    "escalation release unknown -> rollback", "rollback release -> implement [operator] crossing"
)
r.through("implement")
write(
    "release_unknown_operator_rollback",
    "release の成果物の版が上がっておらず（実在の指標で goal が選択肢から外れる）、分類器が答えず unknown になる。運用者は"
    "記憶 review_findings を持たせて implement へ戻す（運用者のロールバック、フェーズ境界越え）",
    r,
    {
        "starts": {
            "implement#2": {
                "files": before_impl,
                "memory": ok_memory("intake", "analyze", "design", "plan_tasks")
                | {"review_findings": FINDINGS},
                "gates": ["discovery", "architecture"],
            }
        },
        "options": {"stage:release#1": ["notes_incomplete", "unknown"]},
        # review#2 も goal の時に修正を要しない指摘を書く
        "memory": {"review_findings": FINDINGS, "design_issues": []},
    },
    operator=[{"kind": "rollback", "stage": "implement", "carry": ["review_findings"]}],
)

# --- 9. 実装の本体が例外で終わり、運用者が中止する ---
r = Run()
r.through("intake", "plan_tasks")
r.start("implement", {"raise": "stage_error"})
r.line(
    "error implement#1 stage_error",
    "escalation implement stage_error -> abort",
    "abort",
    "end aborted",
)
write(
    "implement_error_abort",
    "implement の本体が例外で終わり、評価をせずに escalate する。運用者が中止を選ぶ（unknown（本体の例外）、中止）",
    r,
    {"status": "aborted"},
    operator=[{"kind": "abort"}],
)

# --- 10. assurance のゲートが修正を要しない指摘から実装の修正を求め、実装に戻る ---
r = Run()
r.through("intake", "acceptance")
r.start(
    "review", {**OK_VISIT["review"], "memory": {"review_findings": FINDINGS, "design_issues": []}}
)
r.eval("review", "goal")
r.gate("review", "changes_requested", cls("changes_requested"))
r.line("rollback review -> implement [changes_requested 1] crossing")
r.through("implement")
write(
    "assurance_gate_rolls_back",
    "review は goal に達するが、assurance のゲートの分類が、修正を要しない指摘と verification.md を合わせて changes_requested "
    "（review の end_state のフェーズ全体の条件）を選び、goal の時に書いた review_findings を持って implement に戻る（ゲートからの rollback）",
    r,
    {
        "options": {"phase:assurance#1": ["goal", "design_flaw", "changes_requested", "unknown"]},
        "memory": {"review_findings": FINDINGS},
    },
)

# --- 11. 実装がタスクの曖昧さを見つけ、フェーズ境界を越えてタスク分割に戻る ---
TASK_Q = ["T2: 割引を小計に適用するのか、商品ごとに適用するのかが tasks.yaml から決められない"]
r = Run()
r.through("intake", "plan_tasks")
r.start(
    "implement",
    {
        "fixture": "implement/unclear",
        "memory": {"task_questions": TASK_Q},
        "classify": cls("task_unclear"),
    },
)
r.eval("implement", "task_unclear")
r.line("rollback implement -> plan_tasks [task_unclear 1] crossing")
r.through("plan_tasks")
write(
    "task_unclear_crosses_phase",
    "implement がタスクの曖昧さを記憶 task_questions に書き、construction から architecture の plan_tasks に戻る。"
    "architecture のゲートを評価し直す。実在の指標はすべて通るが、記述の優先（goal に優先）で task_unclear に分類される（フェーズ境界越え）",
    r,
    {
        "starts": {
            "plan_tasks#2": {
                "files": ok_files("intake", "analyze", "design"),
                "memory": ok_memory("intake", "analyze", "design") | {"task_questions": TASK_Q},
                "gates": ["discovery"],
            }
        },
        "options": {"stage:implement#1": ["goal", "task_unclear", "quality_violation", "unknown"]},
    },
)

# --- 12. レビューが設計の欠陥を見つけ、二つのフェーズを越えて設計に戻る ---
ISSUES = ["割引の種類を Discount の分岐で表しており、種類を足すたびに apply を直すことになる"]
r = Run()
r.through("intake", "acceptance")
r.start(
    "review",
    {
        "fixture": "review/design_flaw",
        "memory": {"design_issues": ISSUES, "review_findings": []},
        "classify": cls("design_flaw"),
    },
)
r.eval("review", "design_flaw")
r.line("rollback review -> design [design_flaw 1] crossing")
r.through("design")
write(
    "review_design_flaw_crosses_phases",
    "review が設計を直さなければ解消しない指摘を見つけ、記憶 design_issues を持って assurance から architecture の design に戻る。"
    "architecture、construction、assurance のゲートを評価し直す（フェーズ境界越え）",
    r,
    {
        "starts": {
            "design#2": {
                "files": ok_files("intake", "analyze"),
                "memory": ok_memory("intake", "analyze") | {"design_issues": ISSUES},
                "gates": ["discovery"],
            }
        },
        # plan_tasks#2 と review#2 が空の一覧を書くので、持ち帰った設計の問題は最後の記憶に残らない
        "memory": {"design_issues": []},
    },
)

# --- 13. 実装が宣言に無いファイルを変えて契約違反になり、運用者が再実行する ---
r = Run()
r.through("intake", "plan_tasks")
r.start(
    "implement",
    {
        "fixture": "implement/ok",
        "files": {"requirements.md": "書き換えた要件\n"},
        "classify": GOAL,
    },
)
r.line("error implement#1 contract_violation", "escalation implement contract_violation -> rerun")
r.through("implement")
write(
    "implement_contract_violation_rerun",
    "implement が writes に無い requirements.md を書き換えて契約違反になり、評価をせずに escalate する。運用者が再実行を選ぶ"
    "（unknown（契約違反）、再実行）",
    r,
    {},
    operator=[{"kind": "rerun"}],
)

# --- 14. リリースの記録に要件が欠け、自分自身に戻る ---
MISSING = ["REQ-3"]
r = Run()
r.through("intake", "review")
r.start(
    "release",
    {
        "fixture": "release/incomplete",
        "memory": {"missing_notes": MISSING},
        "classify": cls("notes_incomplete"),
    },
)
r.eval("release", "notes_incomplete")
r.line("rollback release -> release [notes_incomplete 1]")
r.goal("release", {**OK_VISIT["release"], "memory": {"missing_notes": []}})
r.line("end completed")
write(
    "release_notes_self_rollback",
    "release の CHANGELOG.md に REQ-3 が無く（実在の指標で goal が選択肢から外れる）、記憶 missing_notes を持って自分自身に戻る。"
    "二回目の release は持ち帰った記憶を受けて書き直す（自分自身への rollback と carry）",
    r,
    {
        "options": {
            "stage:release#1": ["notes_incomplete", "unknown"],
            "stage:release#2": ["goal", "notes_incomplete", "unknown"],
        },
        "memory": {"missing_notes": []},
    },
)


# --- 15. 検証が要件と依頼の食い違いを見つけ、三つのフェーズ境界を越えて analyze に戻る ---
MISREAD = TABLE["variants"]["acceptance"]["misread"]["memory"]["requirement_gaps"]
r = Run()
r.through("intake", "unit_test")
r.start(
    "acceptance",
    {
        "fixture": "acceptance/misread",
        "memory": {"requirement_gaps": MISREAD, "unmet_requirements": []},
        "classify": cls("requirement_misread"),
    },
)
r.eval("acceptance", "requirement_misread")
r.line("rollback acceptance -> analyze [requirement_misread 1] crossing")
r.through("analyze")
write(
    "acceptance_misread_crosses_phases",
    "acceptance が requirements.md と intake.md の回答の食い違い（入力されたコードの大文字と小文字）を見つけ、記憶 "
    "requirement_gaps を持って assurance から discovery の analyze に戻る（三つのフェーズ境界越え）。discovery、architecture、"
    "construction のゲートを評価し直す。analyze が食い違いを直した後は、持ち帰った食い違いは最後の記憶に残らない",
    r,
    {
        "starts": {
            "analyze#2": {
                "files": ok_files("intake"),
                "memory": {"requirement_gaps": MISREAD},
                "gates": [],
            }
        },
        "memory": {"requirement_gaps": []},
    },
)


# --- 16. 単体テストの不備（要件に反する期待）を見つけ、持ち帰って自分自身に戻る ---
DEFECTIVE = TABLE["variants"]["unit_test"]["defective"]["memory"]
r = Run()
r.through("intake", "implement")
r.start(
    "unit_test",
    {"fixture": "unit_test/defective", "memory": DEFECTIVE, "classify": cls("tests_defective")},
)
r.eval("unit_test", "tests_defective")
r.line("rollback unit_test -> unit_test [tests_defective 1]")
r.through("unit_test")
write(
    "unit_test_defective_self_rollback",
    "unit_test が、要件に反する期待のテスト（小計 300 円に OFF500 で -200 円を期待する。実在の pytest で落ちる）を不備として"
    "記憶 test_defects に書き、自分自身に戻る。テストは落ちるが期待が要件に反するので impl_defect ではない。二回目の unit_test は"
    "持ち帰った不備と不足（test_defects と coverage_gaps）を受けて書き直す（自分自身への rollback と carry。実在の指標で goal が"
    "選択肢から外れる）",
    r,
    {
        "starts": {
            "unit_test#2": {
                # unit_test#1 の開始時スナップショット（implement の goal の後）に、持ち帰った二つの記憶を重ねる
                "files": ok_files_by_file("intake", "analyze", "design", "plan_tasks", "implement"),
                "memory": ok_memory("intake", "analyze", "design", "plan_tasks", "implement")
                | {
                    "test_defects": DEFECTIVE["test_defects"],
                    "coverage_gaps": DEFECTIVE["coverage_gaps"],
                },
                "gates": ["discovery", "architecture"],
            }
        },
        "options": {
            "stage:unit_test#1": [
                "impl_defect",
                "tests_defective",
                "tests_insufficient",
                "unknown",
            ],
            "stage:unit_test#2": [
                "goal",
                "impl_defect",
                "tests_defective",
                "tests_insufficient",
                "unknown",
            ],
        },
        # unit_test#2 が空の一覧を書くので、持ち帰った不備は最後の記憶に残らない
        "memory": {"test_defects": [], "coverage_gaps": []},
    },
)

# --- 17. 構成の欠けた設計を運用者が goal 到達扱いで通し、タスク分割が設計の欠けを持って design に戻る ---
DESIGN_GAPS = TABLE["variants"]["design"]["gap"]["memory"]["requirement_gaps"]
INCOMPLETE = [
    "REQ-3 と REQ-4: design.md の「## 構成」に、コードを受け取る Cart の操作と、変えるファイル（repo/src/shopcart/cart.py）が"
    "無く、どのタスクにも割り当てられない"
]
r = Run()
r.through("intake", "analyze")
r.start(
    "design",
    {
        "fixture": "design/gap",
        "memory": {"requirement_gaps": DESIGN_GAPS},
        "classify": cls("requirements_gap", 0.3),
    },
)
r.eval("design", "unknown")
r.line("escalation design unknown -> continue_as_goal", "next design -> plan_tasks")
r.start(
    "plan_tasks",
    {
        "fixture": "plan_tasks/incomplete",
        "memory": {"design_issues": INCOMPLETE},
        "classify": cls("design_incomplete"),
    },
)
r.eval("plan_tasks", "design_incomplete")
r.line("rollback plan_tasks -> design [design_incomplete 1]")
r.through("design")
write(
    "plan_tasks_design_incomplete_rollback",
    "design が要件への問いを残すが分類の確信度が低く unknown になり、運用者が goal 到達扱いで続行する。plan_tasks は "
    "design.md の「## 構成」に REQ-3 と REQ-4 を受け持つ構成要素が無いことを記憶 design_issues に書き（実在の指標で goal が選択肢"
    "から外れる）、design に戻る。二回目の design は持ち帰った設計の問題を受けて書き直す（同じフェーズの中の rollback と carry。"
    "design の goal を正しく満たした後にも起きる経路は README にある）",
    r,
    {
        "starts": {
            "design#2": {
                "files": ok_files("intake", "analyze"),
                "memory": ok_memory("intake", "analyze") | {"design_issues": INCOMPLETE},
                "gates": ["discovery"],
            }
        },
        "options": {
            "stage:design#1": ["requirements_gap", "unknown"],
            "stage:plan_tasks#1": ["design_incomplete", "unknown"],
        },
        # plan_tasks#2 と review が空の一覧を書き、design#2 が空の requirement_gaps を書く
        "memory": {"design_issues": [], "requirement_gaps": []},
    },
    operator=[
        {
            "kind": "continue_as_goal",
            "note": "REQ-3 と REQ-4 のコードの受け取り方は、設計の中で決める",
            "by": "設計の責任者",
        }
    ],
)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.yaml"):
        old.unlink()
    for name, text in GENERATED.items():
        (OUT / name).write_text(text, "utf-8")
    print("\n".join(sorted(GENERATED)))


if __name__ == "__main__":
    main()
