"""Deterministic L1 裝卦. No UI, LLM, L2, L3, or L4 logic lives here."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from tools.generate_data import (NAJIA_STARTS, YANG,
                                 najia_branch_sequence,
                                 trigram_name)

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "data" / "mechanical" / "bagong_64.json").open(encoding="utf-8") as f:
    BAGONG = json.load(f)
with (ROOT / "data" / "mechanical" / "najia.json").open(encoding="utf-8") as f:
    NAJIA = json.load(f)

BRANCH_ELEMENT = {"子": "水", "亥": "水", "寅": "木", "卯": "木", "巳": "火", "午": "火",
                  "申": "金", "酉": "金", "辰": "土", "戌": "土", "丑": "土", "未": "土"}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}


def relation(palace_element: str, line_element: str) -> str:
    # R-L1-06 is marked [待核] in the spec; this is the requested conventional
    # implementation and must be rechecked against corpus in TASK_02.
    if palace_element == line_element:
        return "兄弟"
    if GENERATES[line_element] == palace_element:
        return "父母"
    if GENERATES[palace_element] == line_element:
        return "子孫"
    # Five-element cycle 木 -> 火 -> 土 -> 金 -> 水 -> 木.  The element
    # two steps ahead is controlled by 我; conversely it controls 我.
    cycle = ("木", "火", "土", "金", "水")
    mine, other = cycle.index(palace_element), cycle.index(line_element)
    if (other - mine) % 5 == 2:
        return "妻財"
    if (mine - other) % 5 == 2:
        return "官鬼"
    raise RuntimeError("invalid five-element relation")


def _najia_for_trigram(name: str, side: str) -> list[dict]:
    stem, start = NAJIA_STARTS[name][side]
    return [{"stem": stem, "branch": branch} for branch in
            najia_branch_sequence(start, name in YANG)]


def _line_najia(lines: tuple[int, ...]) -> list[dict]:
    lower, upper = trigram_name(lines[:3]), trigram_name(lines[3:])
    return _najia_for_trigram(lower, "inner") + _najia_for_trigram(upper, "outer")


def build(lines: Iterable[int]) -> dict:
    bits = tuple(int(x) for x in lines)
    if len(bits) != 6 or any(x not in (0, 1) for x in bits):
        raise ValueError("lines must contain exactly six values, each 0 or 1")
    record = next((row for row in BAGONG if tuple(row["lines"]) == bits), None)
    if record is None:
        raise RuntimeError("generated bagong table is incomplete")
    najia = _line_najia(bits)
    rows = []
    for index, item in enumerate(najia, 1):
        branch_element = BRANCH_ELEMENT[item["branch"]]
        rows.append({"position": index, "stem": item["stem"], "branch": item["branch"],
                     "element": branch_element, "six_relative": relation(record["palace_element"], branch_element),
                     "shi": index == record["shi"], "ying": index == record["ying"]})
    present = {row["six_relative"] for row in rows}
    palace_head = next(row for row in BAGONG if row["palace"] == record["palace"] and row["position"] == "本宮")
    palace_najia = _line_najia(tuple(palace_head["lines"]))
    palace_relatives = [relation(record["palace_element"], BRANCH_ELEMENT[item["branch"]])
                        for item in palace_najia]
    hidden = []
    for relative in ("父母", "官鬼", "妻財", "子孫", "兄弟"):
        if relative not in present:
            hidden_positions = [i for i, value in enumerate(palace_relatives) if value == relative]
            if len(hidden_positions) != 1:
                raise RuntimeError("R-L1-08a expects one palace-head position per absent six-relative")
            i = hidden_positions[0]
            hidden.append({"六親": relative, "branch": palace_najia[i]["branch"],
                           "element": BRANCH_ELEMENT[palace_najia[i]["branch"]],
                           "position": i + 1, "flying_branch": rows[i]["branch"],
                           "flying_element": rows[i]["element"], "rule_id": "R-L1-08a",
                           "伏神能否為用": "TODO: pending R-L1-08b verification"})
    return {"hexagram_id": record["hexagram_id"], "name": record["name"],
            "lines": list(bits), "palace": record["palace"],
            "palace_element": record["palace_element"], "position": record["position"],
            "shi": record["shi"], "ying": record["ying"], "lines_detail": rows,
            "hidden": hidden,
            "six_gods": None, "TODO": "pending R-L1-07 verification"}
