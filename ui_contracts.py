"""Pure local contracts shared by the Streamlit pages."""
from __future__ import annotations

import csv
import json
import uuid
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Iterable

from engine.build import build
from engine.calendar import sexagenary_for_datetime
from engine.pipeline import build_case_state
from engine.semantics import load_decision_table

ROOT = Path(__file__).resolve().parent
RECORDS_PATH = ROOT / "records" / "cases.jsonl"
TRACK_RECORD_FIELDS = [
    "track_{}_verdict".format(book["book_id"])
    for book in load_decision_table().get("books", [])
]
RECORD_FIELDS = [
    "case_id", "cast_datetime", "lines", "question_text", "background_text", "is_proxy",
    "hexagram_name", "palace", "palace_element", "shi", "ying",
    "year_stem", "year_branch", "year_ganzhi", "month_stem", "month_branch", "month_ganzhi",
    "day_stem", "day_branch", "day_ganzhi",
    "xunkong", "month_break_branch", "month_break", "hidden",
    "yongshen_selected", "yongshen_selected_by", "yongshen_candidates",
    "yongshen_candidate_selections",
    *TRACK_RECORD_FIELDS, "yingqi_candidates", "actual_outcome", "actual_outcome_date",
    "verified", "verification_note", "narration_template_ids", "template_missing",
]
FORBIDDEN_RECORD_FIELDS = {"conclusion", "final_verdict", "prediction"}
SIX_RELATIVE_OPTIONS = ("父母", "官鬼", "妻財", "子孫", "兄弟")
LINE_POSITION_OPTIONS = ("世爻", "應爻", "初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
# Legacy record/API export; the UI renders the two groups separately.
YONGSHEN_OPTIONS = SIX_RELATIVE_OPTIONS + ("世應",)


def month_branch_for_date(value: date) -> str:
    return sexagenary_for_datetime(datetime.combine(value, time(hour=12)))["month_branch"]


def day_branch_for_date(value: date) -> str:
    return sexagenary_for_datetime(datetime.combine(value, time(hour=12)))["day_branch"]


def state_for_case(case: dict[str, Any]) -> dict[str, Any]:
    state = build_case_state(
        lines=case["lines"], cast_datetime=case["cast_datetime"],
        moving_positions=case.get("moving_positions", []),
    )
    calendar, relations = state["calendar"], state["relations"]
    for key in (
        "year_stem", "year_branch", "year_ganzhi", "month_stem", "month_branch",
        "month_ganzhi", "day_stem", "day_branch", "day_ganzhi",
    ):
        case[key] = calendar[key]
    case["xunkong"] = relations["empty_branches"]
    case["month_break_branch"] = relations["month_break_branch"]
    case["month_break"] = relations["month_break_positions"]
    return state


def selected_line_positions(case: dict[str, Any], chart: dict[str, Any]) -> list[int]:
    """Return only explicitly saved visible-line candidates."""
    from engine.yongshen import candidate_options
    positions = set()
    selections = case.get("yongshen_candidate_selections") or {}
    for choice in case.get("yongshen_selected") or []:
        candidate_id = selections.get(choice)
        if not candidate_id:
            continue
        candidate = next(
            (item for item in candidate_options(chart, choice)
             if item["candidate_id"] == candidate_id), None,
        )
        if candidate and not candidate.get("hidden"):
            positions.add(candidate["position"])
    return sorted(positions)


def make_case(*, coin_counts: Iterable[int], cast_datetime: datetime,
              question_text: str, background_text: str, is_proxy: bool) -> dict[str, Any]:
    counts = [int(value) for value in coin_counts]
    if len(counts) != 6 or any(value not in range(4) for value in counts):
        raise ValueError("coin_counts must contain six values from 0 to 3")
    lines = [1 if value in (1, 3) else 0 for value in counts]
    moving_positions = [i + 1 for i, value in enumerate(counts) if value in (0, 3)]
    state = build_case_state(
        lines=lines, cast_datetime=cast_datetime, moving_positions=moving_positions,
    )
    derived, calendar, relations = state["chart"], state["calendar"], state["relations"]
    hidden = derived["hidden"]
    return {
        "case_id": str(uuid.uuid4()), "cast_datetime": cast_datetime.isoformat(timespec="minutes"),
        "lines": lines, "question_text": question_text, "background_text": background_text,
        "is_proxy": bool(is_proxy), "hexagram_name": derived["name"], "palace": derived["palace"],
        "palace_element": derived["palace_element"], "shi": derived["shi"], "ying": derived["ying"],
        "year_stem": calendar["year_stem"], "year_branch": calendar["year_branch"],
        "year_ganzhi": calendar["year_ganzhi"],
        "month_stem": calendar["month_stem"], "month_branch": calendar["month_branch"],
        "month_ganzhi": calendar["month_ganzhi"],
        "day_stem": calendar["day_stem"], "day_branch": calendar["day_branch"],
        "day_ganzhi": calendar["day_ganzhi"],
        "xunkong": relations["empty_branches"],
        "month_break_branch": relations["month_break_branch"],
        "month_break": relations["month_break_positions"],
        "hidden": hidden, "yongshen_selected": None,
        "yongshen_selected_by": "human", "yongshen_candidates": list(hidden),
        "yongshen_candidate_selections": {},
        **{field: None for field in TRACK_RECORD_FIELDS},
        "yingqi_candidates": [], "actual_outcome": None, "actual_outcome_date": None,
        "verified": False, "verification_note": None,
        "narration_template_ids": [], "template_missing": False,
        "coin_counts": counts, "moving_positions": moving_positions,
    }


def load_cases() -> list[dict[str, Any]]:
    if not RECORDS_PATH.exists():
        return []
    cases = [json.loads(line) for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    for case in cases:
        if case.get("cast_datetime"):
            state_for_case(case)
        hidden = case.get("hidden")
        if hidden is None:
            hidden = build(case["lines"])["hidden"]
        elif isinstance(hidden, dict):
            hidden = [hidden]
        elif len(hidden) == 1 and isinstance(hidden[0], list):
            hidden = hidden[0]
        normalized_hidden = []
        for item in hidden:
            if not isinstance(item, dict):
                continue
            value = dict(item)
            if "六親" in value:
                value["six_relative"] = value.pop("六親")
            if "伏神能否為用" in value:
                value["can_be_yongshen_status"] = "各家未有定論（R-L1-08b 待核，現僅得《易冒》一方原文）"
                value.pop("伏神能否為用")
            normalized_hidden.append(value)
        case["hidden"] = normalized_hidden
        candidates = case.get("yongshen_candidates")
        if candidates is None or (len(candidates) == 1 and isinstance(candidates[0], list)):
            case["yongshen_candidates"] = list(normalized_hidden)
        else:
            case["yongshen_candidates"] = [
                next((item for item in normalized_hidden
                      if item.get("position") == value.get("position")
                      and item.get("six_relative") == value.get("六親", value.get("six_relative"))), value)
                if isinstance(value, dict) else value
                for value in candidates
            ]
    return cases


def save_cases(cases: list[dict[str, Any]]) -> None:
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        hidden = case.get("hidden", [])
        if isinstance(hidden, dict):
            hidden = [hidden]
        case["hidden"] = list(hidden)
    RECORDS_PATH.write_text("\n".join(json.dumps(case, ensure_ascii=False) for case in cases) + ("\n" if cases else ""), encoding="utf-8")


def csv_bytes(cases: list[dict[str, Any]]) -> bytes:
    from io import StringIO
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=RECORD_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for case in cases:
        writer.writerow({field: json.dumps(case.get(field), ensure_ascii=False) if isinstance(case.get(field), (list, dict)) else case.get(field) for field in RECORD_FIELDS})
    return output.getvalue().encode("utf-8-sig")


def negative_category_display(verdict: str | None) -> str:
    if verdict == "CATEGORY_NEGATED":
        return "此體系不處理此問題 —— 「余從來不言散」（元神忌神衰旺章第十 922；動散章 1683）"
    return verdict or "未表述"
