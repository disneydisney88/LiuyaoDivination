"""Explicit, mechanical L3 recalculation after a human choice.

This module never chooses a six-relative category.  The caller must provide
the category and, when there is more than one candidate, a candidate id.
"""
from __future__ import annotations

from typing import Any

from engine.relations import (
    BRANCH_CLASH,
    BRANCH_ELEMENT,
    CONTROLS,
    GENERATES,
    day_branch_relations,
    seasonal_state,
)
from engine.semantics import infer_condition

YONGSHEN_OPTIONS = ("父母", "官鬼", "妻財", "子孫", "兄弟", "世應")
SIX_RELATIVES = ("父母", "官鬼", "妻財", "子孫", "兄弟")


def _hidden_value(item: dict[str, Any], chinese: str, english: str) -> Any:
    return item.get(english, item.get(chinese))


def _visible_candidate(row: dict[str, Any], choice: str) -> dict[str, Any]:
    role = None
    if choice == "世應":
        role = "世" if row.get("shi") else "應" if row.get("ying") else None
    return {
        "candidate_id": f"visible:{row['position']}",
        "position": row["position"], "branch": row["branch"],
        "element": row["element"], "six_relative": row.get("six_relative"),
        "choice": choice, "role": role, "hidden": False,
    }


def candidate_options(chart: dict[str, Any], choice: str) -> list[dict[str, Any]]:
    """Return every visible and hidden candidate for one human category."""
    if choice not in YONGSHEN_OPTIONS:
        raise ValueError(f"unsupported yongshen choice: {choice}")
    visible = []
    for row in chart.get("lines_detail", []):
        if choice == "世應":
            if row.get("shi") or row.get("ying"):
                visible.append(_visible_candidate(row, choice))
        elif row.get("six_relative") == choice:
            visible.append(_visible_candidate(row, choice))
    hidden = []
    if choice != "世應":
        for index, item in enumerate(chart.get("hidden", [])):
            relative = _hidden_value(item, "六親", "six_relative")
            if relative != choice:
                continue
            hidden.append({
                "candidate_id": f"hidden:{index}",
                "position": int(_hidden_value(item, "position", "position")),
                "branch": _hidden_value(item, "branch", "branch"),
                "element": _hidden_value(item, "element", "element"),
                "six_relative": relative, "choice": choice, "role": None,
                "hidden": True,
                "flying_branch": _hidden_value(item, "flying_branch", "flying_branch"),
                "flying_element": _hidden_value(item, "flying_element", "flying_element"),
                "rule_id": _hidden_value(item, "rule_id", "rule_id") or "R-L1-08a",
            })
    return visible + hidden


def _candidate_state(candidate: dict[str, Any], relations: dict[str, Any]) -> dict[str, Any]:
    branch = candidate["branch"]
    state = {
        "position": candidate["position"], "branch": branch,
        "element": candidate["element"], "six_relative": candidate.get("six_relative"),
        "hidden": candidate.get("hidden", False), "is_yongshen": True,
        "seasonal_state": seasonal_state(candidate["element"], relations["month_element"]),
        "month_break": BRANCH_CLASH[relations["month_branch"]] == branch,
        "empty": branch in relations["empty_branches"],
        "day_relations": day_branch_relations(relations["day_branch"], branch),
        "motion": "伏" if candidate.get("hidden") else next(
            (row.get("motion") for row in relations.get("lines", [])
             if row.get("position") == candidate["position"]), "靜"
        ),
    }
    if candidate.get("hidden"):
        state["flying_branch"] = candidate.get("flying_branch")
        state["flying_element"] = candidate.get("flying_element")
        state["rule_id"] = candidate.get("rule_id", "R-L1-08a")
    return state


def _role_candidates(
    all_candidates: list[dict[str, Any]], target_element: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    yuan = [item for item in all_candidates if GENERATES[item["element"]] == target_element]
    ji = [item for item in all_candidates if CONTROLS[item["element"]] == target_element]
    yuan_elements = {item["element"] for item in yuan}
    chou = [item for item in all_candidates if any(CONTROLS[item["element"]] == element for element in yuan_elements)]
    return yuan, ji, chou


def _with_role(items: list[dict[str, Any]], role: str, relations: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in items:
        value = dict(item)
        value["role"] = role
        value["state"] = _candidate_state(item, relations)
        value["state"]["is_yongshen"] = False
        result.append(value)
    return result


def _yuan_checks(yuan: list[dict[str, Any]], relations: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for item in yuan:
        state = _candidate_state(item, relations)
        seasonal_weak = state["seasonal_state"] in {"休", "囚"}
        moving = state["motion"] not in {"靜", "伏"}
        checks.append({
            "candidate_id": item["candidate_id"],
            "rule_id": "R-L2-07",
            "checks": [
                {"id": "R-L2-07-1", "status": "confirmed" if seasonal_weak and not moving else "not_matched" if not seasonal_weak else "not_computable", "basis": "休囚不動"},
                {"id": "R-L2-07-2", "status": "confirmed" if seasonal_weak and (state["empty"] or state["month_break"]) else "not_matched", "basis": "休囚又逢自空、月破"},
                {"id": "R-L2-07-3", "status": "not_computable", "basis": "變化進退資料未另定"},
                {"id": "R-L2-07-4", "status": "not_computable", "basis": "絕之機械表未接通"},
                {"id": "R-L2-07-5", "status": "not_computable", "basis": "三墓軌資料未接通"},
                {"id": "R-L2-07-6", "status": "not_computable", "basis": "化絕／化剋／化破／化散資料未另定"},
            ],
        })
    return checks


def _moving_interactions(state: dict[str, Any], target_element: str) -> list[dict[str, Any]]:
    relations = state["relations"]
    changed = state.get("changed_chart") or {}
    changed_rows = {row["position"]: row for row in changed.get("lines_detail", [])}
    result = []
    for row in relations.get("lines", []):
        if row.get("motion") == "靜":
            continue
        changed_row = changed_rows.get(row["position"])
        result.append({
            "position": row["position"], "branch": row["branch"],
            "element": row["element"], "relation_to_yongshen": (
                "生" if GENERATES[row["element"]] == target_element else
                "剋" if CONTROLS[row["element"]] == target_element else
                "被生" if GENERATES[target_element] == row["element"] else
                "被剋" if CONTROLS[target_element] == row["element"] else "比和"
            ),
            "changed_branch": changed_row.get("branch") if changed_row else None,
            "changed_element": changed_row.get("element") if changed_row else None,
            "return_control": bool(
                changed_row and CONTROLS[changed_row["element"]] == row["element"]
            ),
            "rule_id": "R-L2-05",
        })
    return result


def analyze_yongshen(state: dict[str, Any], choice: str, candidate_id: str | None = None) -> dict[str, Any]:
    """Recalculate all available mechanical relations around one explicit candidate."""
    if choice not in YONGSHEN_OPTIONS:
        raise ValueError(f"unsupported yongshen choice: {choice}")
    chart, relations = state["chart"], state["relations"]
    options = candidate_options(chart, choice)
    if candidate_id is None and len(options) == 1:
        candidate_id = options[0]["candidate_id"]
    if candidate_id is not None and candidate_id not in {item["candidate_id"] for item in options}:
        raise ValueError("candidate_id does not belong to the selected yongshen choice")
    selected = next((dict(item) for item in options if item["candidate_id"] == candidate_id), None)
    all_candidates = []
    for candidate in (
        candidate_options(chart, relative) for relative in SIX_RELATIVES
    ):
        all_candidates.extend(candidate)
    if choice == "世應":
        all_candidates.extend(candidate_options(chart, choice))
    target_element = selected["element"] if selected else None
    yuan, ji, chou = _role_candidates(all_candidates, target_element) if target_element else ([], [], [])
    line_outputs = []
    for row in relations.get("lines", []):
        value = dict(row)
        value["is_yongshen"] = bool(selected and not selected.get("hidden") and row["position"] == selected["position"])
        line_outputs.append(value)
    hidden_outputs = []
    for item in chart.get("hidden", []):
        value = dict(item)
        item_id = f"hidden:{chart['hidden'].index(item)}"
        value["is_yongshen"] = bool(selected and selected.get("candidate_id") == item_id)
        hidden_outputs.append(value)
    own_state = _candidate_state(selected, relations) if selected else None
    decision = {"C1": None, "C15": None}
    if selected and not selected.get("hidden"):
        decision["C1"] = infer_condition(table_id="C1", relation_result=relations, line=selected["position"])
        decision["C15"] = infer_condition(table_id="C15", relation_result=relations, line=selected["position"])
    if decision["C1"] is None and decision["C15"] is None:
        decision["status"] = "此爻不觸發 C1／C15 任何條件"
    return {
        "choice": choice, "candidate_id": candidate_id,
        "candidates": [dict(item) for item in options], "selected": selected,
        "target_element": target_element, "own_state": own_state,
        "lines": line_outputs, "hidden": hidden_outputs,
        "yuan_shen": _with_role(yuan, "元神", relations),
        "ji_shen": _with_role(ji, "忌神", relations),
        "chou_shen": _with_role(chou, "仇神", relations),
        "yuan_shen_checks": _yuan_checks(yuan, relations),
        "moving_interactions": _moving_interactions(state, target_element) if target_element else [],
        "double_occurrence": len([item for item in options if not item.get("hidden")]) > 1,
        "hidden_selected": bool(selected and selected.get("hidden")),
        "decision_table": decision,
        "rule_ids": ["R-L2-01", "R-L2-02", "R-L2-03", "R-L2-05", "R-L2-07", "R-L1-08a"],
    }
