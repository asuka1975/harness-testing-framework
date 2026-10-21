"""実行記録の要約（contract/conformance/README.md）と、遷移の六種の被覆（契約 3.5）。"""

from collections.abc import Mapping, Sequence
from typing import Any

# 契約 3.5 の六種
TRANSITION_KINDS = (
    "next",
    "rollback",
    "max_exceeded",
    "unknown",
    "suspend_resume",
    "phase_crossing",
)


def _summary_line(e: Mapping[str, Any]) -> str | None:
    kind = e["event"]
    if kind == "stage_start":
        return f"start {e['stage']}#{e['visit']}"
    if kind == "stage_end":
        error = e["error"]
        return f"error {e['stage']}#{e['visit']} {error['kind']}" if error else None
    if kind == "evaluation":
        target = e["stage"] if e["scope"] == "stage" else e["phase"]
        return f"eval {e['scope']} {target} = {e['outcome']}"
    if kind == "transition":
        t = e["kind"]
        if t == "next":
            return f"next {e['from']} -> {e['to']}"
        if t == "rollback":
            edge = e["edge"]
            tag = f"{edge['state']} {e['count']}" if edge else "operator"
            crossing = " crossing" if e["crosses_phase"] else ""
            return f"rollback {e['from']} -> {e['to']} [{tag}]{crossing}"
        if t in ("gate_pass", "suspend", "resume"):
            return f"{t} {e['from']}"
        if t in ("complete", "abort"):
            return str(t)
        return None
    if kind == "escalation":
        decision = e["decision"]
        chosen = decision["kind"] if decision else "pending"
        return f"escalation {e['stage']} {e['reason']} -> {chosen}"
    if kind == "warning":
        return "warning"
    if kind == "run_end":
        return f"end {e['status']}"
    return None


def summarize(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """実行記録を、出来事ごとの一行の要約にする。"""
    return [line for e in events if (line := _summary_line(e)) is not None]


def transition_coverage(events: Sequence[Mapping[str, Any]]) -> set[str]:
    """実行記録で通った遷移の種類（TRANSITION_KINDS の部分集合）。"""
    covered: set[str] = set()
    phase_of: dict[str, str] = {}
    crossed_into: list[str] = []
    suspended = False
    for e in events:
        kind = e["event"]
        if kind == "evaluation" and e["scope"] == "stage":
            phase_of[e["stage"]] = e["phase"]
        if kind == "evaluation" and e["scope"] == "phase" and e["phase"] in crossed_into:
            covered.add("phase_crossing")
        if kind == "transition":
            t = e["kind"]
            if t in ("next", "complete"):
                covered.add("next")
            if t == "rollback" and e["edge"] and not e["crosses_phase"]:
                covered.add("rollback")
            if t == "rollback" and e["crosses_phase"] and e["to"] in phase_of:
                crossed_into.append(phase_of[e["to"]])
            if t == "suspend":
                suspended = True
            if t == "resume" and suspended:
                covered.add("suspend_resume")
        if kind == "escalation":
            if e["reason"] == "max_exceeded":
                covered.add("max_exceeded")
            else:
                covered.add("unknown")
    return covered
