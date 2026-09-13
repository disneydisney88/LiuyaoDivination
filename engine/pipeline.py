"""Pure wiring for the deterministic L1 → L2 case state."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from engine.build import build
from engine.calendar import sexagenary_for_datetime
from engine.relations import BRANCH_ELEMENT, build_relation_graph


def build_case_state(*, lines: Iterable[int], cast_datetime: datetime | str,
                     moving_positions: Iterable[int] = ()) -> dict:
    value = datetime.fromisoformat(cast_datetime) if isinstance(cast_datetime, str) else cast_datetime
    if not isinstance(value, datetime):
        raise TypeError("cast_datetime must be a datetime or ISO datetime string")
    chart = build(lines)
    calendar = sexagenary_for_datetime(value)
    relations = build_relation_graph(
        line_rows=chart["lines_detail"],
        hidden=chart["hidden"],
        month_element=BRANCH_ELEMENT[calendar["month_branch"]],
        month_branch=calendar["month_branch"],
        day_stem=calendar["day_stem"],
        day_branch=calendar["day_branch"],
        moving_positions=moving_positions,
    )
    relations.update({
        "year_ganzhi": calendar["year_ganzhi"],
        "month_ganzhi": calendar["month_ganzhi"],
        "day_ganzhi": calendar["day_ganzhi"],
    })
    return {"chart": chart, "calendar": calendar, "relations": relations}
