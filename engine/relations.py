"""L2 mechanical skeleton.

This module deliberately records classifications and graph scope only.  It
does not assign any semantic effect to empty, broken, or scattered lines.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
BRANCH_ELEMENT = {"子": "水", "亥": "水", "寅": "木", "卯": "木", "巳": "火", "午": "火",
                  "申": "金", "酉": "金", "辰": "土", "戌": "土", "丑": "土", "未": "土"}
BRANCH_CLASH = dict(zip(BRANCHES, "午未申酉戌亥子丑寅卯辰巳"))
BRANCH_COMBINE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
                  "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
ROOT = Path(__file__).resolve().parents[1]
SEASONAL_STATE_CATEGORIES = json.loads(
    (ROOT / "data" / "mechanical" / "seasonal_state_categories.json").read_text(encoding="utf-8")
)


def element_relation(left: str, right: str) -> str:
    """Mechanical five-element relation, with no downstream interpretation."""
    if left == right:
        return "比和"
    if GENERATES[left] == right:
        return "生"
    if CONTROLS[left] == right:
        return "剋"
    if GENERATES[right] == left:
        return "被生"
    if CONTROLS[right] == left:
        return "被剋"
    raise ValueError(f"unknown element pair: {left}, {right}")


def seasonal_state(line_element: str, month_element: str) -> str:
    """R-L2-01 five-state label only; no effect is assigned to the label."""
    if line_element == month_element:
        return "旺"
    if GENERATES[month_element] == line_element:
        return "相"
    if GENERATES[line_element] == month_element:
        return "休"
    if CONTROLS[line_element] == month_element:
        return "囚"
    if CONTROLS[month_element] == line_element:
        return "死"
    raise ValueError(f"unknown seasonal pair: {line_element}, {month_element}")


def seasonal_state_category(state: str) -> str:
    """Return the project's editorial two-category grouping of five states."""
    try:
        return SEASONAL_STATE_CATEGORIES[state]
    except KeyError as exc:
        raise ValueError(f"unknown seasonal state: {state}") from exc


def xunkong(day_stem: str, day_branch: str) -> tuple[str, str]:
    """Return the two empty branches for a valid sexagenary day."""
    if day_stem not in STEMS or day_branch not in BRANCHES:
        raise ValueError("invalid heavenly stem or earthly branch")
    stem_i, branch_i = STEMS.index(day_stem), BRANCHES.index(day_branch)
    if stem_i % 2 != branch_i % 2:
        raise ValueError("stem and branch are not a valid sexagenary pair")
    cycle_start = (branch_i - stem_i) % 12
    return BRANCHES[(cycle_start + 10) % 12], BRANCHES[(cycle_start + 11) % 12]


def day_branch_relations(day_branch: str, line_branch: str) -> list[str]:
    relations = [element_relation(BRANCH_ELEMENT[day_branch], BRANCH_ELEMENT[line_branch])]
    if BRANCH_CLASH[day_branch] == line_branch:
        relations.append("沖")
    if BRANCH_COMBINE[day_branch] == line_branch:
        relations.append("合")
    return relations


def classify_motion(*, moving: bool) -> str:
    """Return the sole L2 motion fact, without a doctrinal classification."""
    return "動" if moving else "靜"


def build_relation_graph(*, line_rows: Iterable[dict], month_element: str,
                         month_branch: str, day_stem: str, day_branch: str,
                         moving_positions: Iterable[int] = (),
                         changing_positions: Iterable[int] = (),
                         hidden: Iterable[dict] = ()) -> dict:
    """Build only L2 labels and directed graph scope constraints.

    ``line_rows`` uses the L1 shape (position, branch, element).  No question
    text, yongshen choice, prediction, or empty/scatter effect is accepted.
    """
    rows = list(line_rows)
    hidden_rows = [dict(item) for item in hidden]
    if any(not isinstance(item, dict) for item in hidden_rows):
        raise ValueError("hidden must be an iterable of mappings")
    moving = set(moving_positions)
    changing = set(changing_positions)
    empty_branches = xunkong(day_stem, day_branch)
    if month_branch not in BRANCHES:
        raise ValueError("invalid month branch")
    states = []
    for row in rows:
        branch, element, position = row["branch"], row["element"], row["position"]
        states.append({
            **row,
            "seasonal_state": seasonal_state(element, month_element),
            "month_break": BRANCH_CLASH[month_branch] == branch,
            "empty": branch in empty_branches,
            "day_relations": day_branch_relations(day_branch, branch),
            "motion": classify_motion(moving=position in moving),
        })

    edges = []
    # R-L2-04: only day/month -> line; never line -> day/month.
    for position in range(1, len(rows) + 1):
        edges.extend([
            {"source": "日辰", "target": f"爻:{position}", "rule_id": "R-L2-04"},
            {"source": "月建", "target": f"爻:{position}", "rule_id": "R-L2-04"},
        ])
    # R-L2-05: a changing line can point only back to its own moving line;
    # incoming edges to a changing line are supplied by 日辰/月建 only.
    for position in sorted(changing):
        if position not in moving:
            raise ValueError("every changing position must also be moving")
        edges.append({"source": f"變爻:{position}", "target": f"動爻:{position}",
                      "rule_id": "R-L2-05"})
        edges.extend([
            {"source": "日辰", "target": f"變爻:{position}", "rule_id": "R-L2-05"},
            {"source": "月建", "target": f"變爻:{position}", "rule_id": "R-L2-05"},
        ])
    return {
        "rule_scope": ["R-L2-01", "R-L2-02", "R-L2-03", "R-L2-04", "R-L2-05"],
        "empty_branches": list(empty_branches), "month_branch": month_branch,
        "month_element": month_element,
        "month_break_branch": BRANCH_CLASH[month_branch],
        "month_break_positions": [row["position"] for row in states if row["month_break"]],
        "day_stem": day_stem, "day_branch": day_branch,
        "lines": states, "hidden": hidden_rows, "edges": edges,
        "semantic_effects": "NOT IMPLEMENTED: pending C1 track decision",
    }
