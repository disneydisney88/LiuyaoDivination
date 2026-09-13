"""Pure local contracts shared by the Streamlit pages."""
from __future__ import annotations

import csv
import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from engine.build import build
from engine.semantics import load_decision_table

ROOT = Path(__file__).resolve().parent
RECORDS_PATH = ROOT / "records" / "cases.jsonl"
TRACK_RECORD_FIELDS = [
    "track_{}_verdict".format(book["book_id"])
    for book in load_decision_table().get("books", [])
]
RECORD_FIELDS = [
    "case_id", "cast_datetime", "lines", "question_text", "background_text", "is_proxy",
    "hexagram_name", "palace", "palace_element", "shi", "ying", "month_branch", "day_branch",
    "xunkong", "month_break", "yongshen_selected", "yongshen_selected_by", "yongshen_candidates",
    *TRACK_RECORD_FIELDS, "yingqi_candidates", "actual_outcome", "actual_outcome_date",
    "verified", "verification_note", "narration_template_ids", "template_missing",
]
FORBIDDEN_RECORD_FIELDS = {"conclusion", "final_verdict", "prediction"}
YONGSHEN_OPTIONS = ("父母", "官鬼", "妻財", "子孫", "兄弟", "世應")
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
MONTH_BRANCHES = ("丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子")


def month_branch_for_date(value: date) -> str:
    return MONTH_BRANCHES[value.month - 1]


def day_branch_for_date(value: date) -> str:
    reference = date(2000, 1, 7)
    return BRANCHES[(value - reference).days % 12]


def make_case(*, coin_counts: Iterable[int], cast_datetime: datetime,
              question_text: str, background_text: str, is_proxy: bool) -> dict[str, Any]:
    counts = [int(value) for value in coin_counts]
    if len(counts) != 6 or any(value not in range(4) for value in counts):
        raise ValueError("coin_counts must contain six values from 0 to 3")
    lines = [1 if value in (1, 3) else 0 for value in counts]
    derived = build(lines)
    hidden = derived.get("hidden")
    cast_date = cast_datetime.date()
    return {
        "case_id": str(uuid.uuid4()), "cast_datetime": cast_datetime.isoformat(timespec="minutes"),
        "lines": lines, "question_text": question_text, "background_text": background_text,
        "is_proxy": bool(is_proxy), "hexagram_name": derived["name"], "palace": derived["palace"],
        "palace_element": derived["palace_element"], "shi": derived["shi"], "ying": derived["ying"],
        "month_branch": month_branch_for_date(cast_date), "day_branch": day_branch_for_date(cast_date),
        "xunkong": [], "month_break": [], "yongshen_selected": None,
        "yongshen_selected_by": "human", "yongshen_candidates": [hidden] if hidden else [],
        **{field: None for field in TRACK_RECORD_FIELDS},
        "yingqi_candidates": [], "actual_outcome": None, "actual_outcome_date": None,
        "verified": False, "verification_note": None,
        "narration_template_ids": [], "template_missing": False,
        "coin_counts": counts, "moving_positions": [i + 1 for i, value in enumerate(counts) if value in (0, 3)],
    }


def load_cases() -> list[dict[str, Any]]:
    if not RECORDS_PATH.exists():
        return []
    return [json.loads(line) for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_cases(cases: list[dict[str, Any]]) -> None:
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
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
