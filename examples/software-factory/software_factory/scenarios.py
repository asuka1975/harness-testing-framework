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


Q_BASE = [
    "この機能を使うのは誰ですか",
    "配る割引コードの種類と上限は何ですか",
    "使えないコードが入力された時はどうしますか",
]
OPEN_Q = ["百分率の割引の上限は何 % ですか", "定額の割引が小計を超えた時、支払額はどうなりますか"]
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
        {"answer": "ネットショップの購入者。レジの画面でコードを入力する"},
        {"defer": True},
        {
            "answer": "PCT10 のような百分率のコードと、OFF500 のような定額のコード。百分率は 50% まで"
        },
        {"answer": "エラーにして、割引しない"},
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
    user=[{"answer": "50% まで"}, {"answer": "0 円にする。マイナスにはしない"}],
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


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.yaml"):
        old.unlink()
    for name, text in GENERATED.items():
        (OUT / name).write_text(text, "utf-8")
    print("\n".join(sorted(GENERATED)))


if __name__ == "__main__":
    main()
