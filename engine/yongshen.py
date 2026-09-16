"""Deterministic L3 recalculation after an explicit human choice.

The module separates the five six-relative choices from direct line choices.
It never recommends a candidate and never applies any school's doctrinal
state judgement. A repeated relative or a hidden relative remains pending
until the user explicitly chooses a candidate.
"""
from __future__ import annotations

from typing import Any

from engine.relations import (
    BRANCH_CLASH,
    CONTROLS,
    GENERATES,
    day_branch_relations,
    element_relation,
    seasonal_state,
)
from engine.semantics import (
    Y_IMPLEMENTATION_GAPS,
    chong_source_for_line,
    infer_condition, infer_conditions,
    y_conditions_for_role,
)

SIX_RELATIVE_OPTIONS = ("父母", "官鬼", "妻財", "子孫", "兄弟")
LINE_POSITION_OPTIONS = ("世爻", "應爻", "初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
# Kept as the legacy six-choice export for records and older callers.
YONGSHEN_OPTIONS = SIX_RELATIVE_OPTIONS + ("世應",)
ALL_CHOICES = SIX_RELATIVE_OPTIONS + LINE_POSITION_OPTIONS + ("世應",)
LINE_LABEL_TO_POSITION = {
    "初爻": 1, "二爻": 2, "三爻": 3, "四爻": 4, "五爻": 5, "上爻": 6,
}


def _hidden_value(item: dict[str, Any], key: str, legacy: str | None = None) -> Any:
    return item.get(key) if key in item else item.get(legacy) if legacy else None


def _visible_candidate(row: dict[str, Any], choice: str) -> dict[str, Any]:
    role = None
    if choice in {"世應", "世爻", "應爻"}:
        role = "世" if row.get("shi") else "應" if row.get("ying") else None
    return {
        "candidate_id": f"visible:{row['position']}",
        "position": row["position"], "branch": row["branch"],
        "element": row["element"], "six_relative": row.get("six_relative"),
        "choice": choice, "role": role, "hidden": False,
    }


def _hidden_candidate(item: dict[str, Any], index: int, choice: str) -> dict[str, Any]:
    return {
        "candidate_id": f"hidden:{index}",
        "position": int(_hidden_value(item, "position", "position")),
        "branch": _hidden_value(item, "branch", "branch"),
        "element": _hidden_value(item, "element", "element"),
        "six_relative": _hidden_value(item, "six_relative", "六親"),
        "choice": choice, "role": None, "hidden": True,
        "flying_branch": _hidden_value(item, "flying_branch", "flying_branch"),
        "flying_element": _hidden_value(item, "flying_element", "flying_element"),
        "rule_id": _hidden_value(item, "rule_id", "rule_id") or "R-L1-08a",
        "can_be_yongshen_status": _hidden_value(
            item, "can_be_yongshen_status", "伏神能否為用",
        ) or "各家未有定論（R-L1-08b 待核，現僅得《易冒》一方原文）",
    }


def candidate_options(chart: dict[str, Any], choice: str) -> list[dict[str, Any]]:
    """Return all candidates in line order; never rank or recommend them."""
    if choice not in ALL_CHOICES:
        raise ValueError(f"unsupported yongshen choice: {choice}")
    visible = []
    for row in chart.get("lines_detail", []):
        if choice == "世應" and (row.get("shi") or row.get("ying")):
            visible.append(_visible_candidate(row, choice))
        elif choice == "世爻" and row.get("shi"):
            visible.append(_visible_candidate(row, choice))
        elif choice == "應爻" and row.get("ying"):
            visible.append(_visible_candidate(row, choice))
        elif choice in LINE_LABEL_TO_POSITION and row["position"] == LINE_LABEL_TO_POSITION[choice]:
            visible.append(_visible_candidate(row, choice))
        elif choice in SIX_RELATIVE_OPTIONS and row.get("six_relative") == choice:
            visible.append(_visible_candidate(row, choice))
    hidden = []
    if choice in SIX_RELATIVE_OPTIONS:
        for index, item in enumerate(chart.get("hidden", [])):
            if _hidden_value(item, "six_relative", "六親") == choice:
                hidden.append(_hidden_candidate(item, index, choice))
    return visible + hidden


def _candidate_state(candidate: dict[str, Any], relations: dict[str, Any]) -> dict[str, Any]:
    branch = candidate["branch"]
    position = candidate["position"]
    visible_row = next(
        (row for row in relations.get("lines", []) if row.get("position") == position),
        {},
    )
    return {
        "position": position, "branch": branch,
        "element": candidate["element"], "six_relative": candidate.get("six_relative"),
        "hidden": candidate.get("hidden", False), "is_yongshen": True,
        "seasonal_state": seasonal_state(candidate["element"], relations["month_element"]),
        "month_break": BRANCH_CLASH[relations["month_branch"]] == branch,
        "empty": branch in relations["empty_branches"],
        "day_relations": day_branch_relations(relations["day_branch"], branch),
        "motion": "伏" if candidate.get("hidden") else visible_row.get("motion", "靜"),
        "is_shi": bool(visible_row.get("shi")),
        "is_ying": bool(visible_row.get("ying")),
        "state_fields": ["position", "branch", "element", "six_relative", "seasonal_state", "empty", "month_break", "motion"],
        **({
            "flying_branch": candidate.get("flying_branch"),
            "flying_element": candidate.get("flying_element"),
            "rule_id": candidate.get("rule_id", "R-L1-08a"),
        } if candidate.get("hidden") else {}),
    }


def _role_candidates(
    all_candidates: list[dict[str, Any]], target_element: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    yuan = [item for item in all_candidates if GENERATES[item["element"]] == target_element]
    ji = [item for item in all_candidates if CONTROLS[item["element"]] == target_element]
    yuan_elements = {item["element"] for item in yuan}
    chou = [
        item for item in all_candidates
        if any(CONTROLS[item["element"]] == element for element in yuan_elements)
    ]
    return yuan, ji, chou


def _unique_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one entry per candidate while retaining its line-role metadata."""
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        unique.setdefault(item["candidate_id"], item)
    return list(unique.values())


def _with_role(
    items: list[dict[str, Any]], role: str, relations: dict[str, Any],
    selected: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    result = []
    for item in items:
        value = dict(item)
        value["role"] = role
        value["state"] = _candidate_state(item, relations)
        value["state"]["is_yongshen"] = False
        value["is_shi"] = value["state"]["is_shi"]
        value["is_ying"] = value["state"]["is_ying"]
        value["is_flying_of_yongshen"] = bool(
            selected and selected.get("hidden") and item.get("position") == selected.get("position")
            and not item.get("hidden")
        )
        result.append(value)
    return result


def _deferred_checks(yuan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reserve R-L2-07 slots without importing a school's status judgement."""
    return [
        {
            "candidate_id": item["candidate_id"],
            "rule_id": "R-L2-07",
            "checks": [
                {"id": f"R-L2-07-{number}", "status": "deferred_to_multi_track",
                 "basis": "四神狀態決策表尚未建立"}
                for number in range(1, 7)
            ],
        }
        for item in yuan
    ]


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


def _flying_hidden_relation(selected: dict[str, Any]) -> dict[str, Any] | None:
    if not selected.get("hidden"):
        return None
    flying = selected["flying_element"]
    hidden = selected["element"]
    relation = element_relation(flying, hidden)
    form = {
        "剋": ("飛克伏者滅", "T-FLYING-HIDDEN-FEI-KE-FU"),
        "生": ("飛生伏者得", "T-FLYING-HIDDEN-FEI-SHENG-FU"),
        "被剋": ("伏克飛者出", "T-FLYING-HIDDEN-FU-KE-FEI"),
        "被生": ("伏生飛者沒", "T-FLYING-HIDDEN-FU-SHENG-FEI"),
        "比和": ("飛伏比和者拔", "T-FLYING-HIDDEN-BIHE"),
    }[relation]
    return {
        "flying_branch": selected["flying_branch"], "flying_element": flying,
        "hidden_branch": selected["branch"], "hidden_element": hidden,
        "relation": relation, "doctrinal_label": form[0], "template_id": form[1],
        "source_book": "易冒", "source_locator": "類總章第四十一 686",
        "original": form[0], "rule_id": "R-L1-08b",
        "doctrinal_status": "《易冒》一家之說，非通則",
        "other_books_status": "not_collected",
        "not_collected_books": ["增刪卜易", "卜筮正宗", "卜筮全書", "黃金策", "火珠林", "京氏易傳", "易隱"],
    }


def _pending_result(choice: str, options: list[dict[str, Any]], relations: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for item in options:
        value = dict(item)
        value["state"] = _candidate_state(item, relations)
        value["is_yongshen"] = False
        candidates.append(value)
    result = {
        "choice": choice, "status": "pending_selection",
        "candidates": candidates,
        "candidate_count": len(options),
        "double_occurrence": len(options) > 1,
        "hidden_available": any(item.get("hidden") for item in options),
        "rule_ids": ["R-L1-08a", "R-L3-01"],
    }
    if result["hidden_available"]:
        result["hidden_choice_options"] = ["use_hidden", "choose_other"]
    return result


def analyze_yongshen(state: dict[str, Any], choice: str, candidate_id: str | None = None) -> dict[str, Any]:
    """Recalculate mechanical relations around one explicit candidate."""
    if choice not in ALL_CHOICES:
        raise ValueError(f"unsupported yongshen choice: {choice}")
    chart, relations = state["chart"], state["relations"]
    options = candidate_options(chart, choice)
    hidden_only = bool(options) and all(item.get("hidden") for item in options)
    if candidate_id is None and len(options) == 1 and not hidden_only:
        candidate_id = options[0]["candidate_id"]
    if candidate_id is None and (len(options) != 1 or hidden_only):
        return _pending_result(choice, options, relations)
    if candidate_id not in {item["candidate_id"] for item in options}:
        raise ValueError("candidate_id does not belong to the selected yongshen choice")
    selected = next(dict(item) for item in options if item["candidate_id"] == candidate_id)
    all_candidates = []
    for relative in SIX_RELATIVE_OPTIONS:
        all_candidates.extend(candidate_options(chart, relative))
    # Every visible line already occurs once under its six-relative.  世／應
    # are annotations on that candidate, not extra four-god candidates.
    all_candidates = _unique_candidates(all_candidates)
    target_element = selected["element"]
    yuan, ji, chou = _role_candidates(all_candidates, target_element)
    line_outputs = []
    for row in relations.get("lines", []):
        value = dict(row)
        value["is_yongshen"] = bool(not selected.get("hidden") and row["position"] == selected["position"])
        line_outputs.append(value)
    hidden_outputs = []
    for index, item in enumerate(chart.get("hidden", [])):
        value = dict(item)
        value["is_yongshen"] = bool(selected.get("hidden") and selected["candidate_id"] == f"hidden:{index}")
        hidden_outputs.append(value)
    own_state = _candidate_state(selected, relations)
    decision = {
        "A": [],
        "C1": None,
        "C15": None,
        "K": None,
        # Y locates source rows for each mechanical four-god state.  It never
        # applies a row's effect language.
        "Y": None,
        "analysis_position": selected["position"],
    }
    if not selected.get("hidden"):
        decision["A"] = infer_conditions(table_id="A", relation_result=relations, line=selected["position"])
        decision["C1"] = infer_condition(table_id="C1", relation_result=relations, line=selected["position"])
        decision["C15"] = infer_condition(table_id="C15", relation_result=relations, line=selected["position"])
        decision["K"] = infer_condition(table_id="K", relation_result=relations, line=selected["position"])
        if decision["C1"] or decision["C15"]:
            source = chong_source_for_line(relations, selected["position"])
            if source:
                decision["cell_context"] = {"chong_source": source}
    if decision["C1"] is None and decision["C15"] is None and decision["K"] is None and not decision["A"]:
        decision["status"] = "此爻不觸發任何條件"
        decision["coverage_gap_note"] = "目前沖與空亡狀態表未觸發；Y 表已按元神／忌神逐爻定位，僅不輸出效果判定。"
    candidate_listing = []
    for item in options:
        value = dict(item)
        value["state"] = _candidate_state(item, relations)
        value["is_yongshen"] = item["candidate_id"] == selected["candidate_id"]
        candidate_listing.append(value)
    yuan_output = _with_role(yuan, "元神", relations, selected)
    ji_output = _with_role(ji, "忌神", relations, selected)
    chou_output = _with_role(chou, "仇神", relations, selected)
    y_locations = []
    for role, items in (("元神", yuan_output), ("忌神", ji_output)):
        for item in items:
            located = y_conditions_for_role(role, item["state"])
            y_locations.append({
                "role": role,
                "position": item["position"],
                "branch": item["branch"],
                "element": item["element"],
                "six_relative": item.get("six_relative"),
                "hidden": item.get("hidden", False),
                "seasonal_state": item["state"]["seasonal_state"],
                "matches": located["matches"],
                "unmodelled_rows": located["unmodelled_rows"],
            })
    decision["Y"] = {
        "located": True,
        "locations": y_locations,
        "chou_shen_note": "Y 表無仇神格位（P-057）",
        "implementation_gaps": [dict(item) for item in Y_IMPLEMENTATION_GAPS],
    }
    return {
        "choice": choice, "status": "selected", "candidate_id": candidate_id,
        "selected": selected, "candidates": candidate_listing,
        "target_element": target_element, "own_state": own_state,
        "lines": line_outputs, "hidden": hidden_outputs,
        "yuan_shen": yuan_output,
        "ji_shen": ji_output,
        "chou_shen": chou_output,
        "yuan_shen_checks": _deferred_checks(yuan_output),
        "moving_interactions": _moving_interactions(state, target_element),
        "double_occurrence": len(options) > 1,
        "hidden_selected": bool(selected.get("hidden")),
        "flying_hidden_relation": _flying_hidden_relation(selected),
        "decision_table": decision,
        "rule_ids": ["R-L1-08a", "R-L1-08b", "R-L2-01", "R-L2-02", "R-L2-03", "R-L2-05", "R-L3-01"],
    }
