"""Deterministic civil datetime to sexagenary year/month/day pillars.

Year and month boundaries follow the twelve solar ``jie`` terms.  Solar-term
instants use the standard 1900 epoch/minute-offset approximation; a naive
datetime is interpreted in the host's local timezone before comparison.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
DAY_REFERENCE = date(2000, 1, 7)  # 甲子日
YEAR_REFERENCE = 1984  # 甲子年
SOLAR_TERM_EPOCH = datetime(1900, 1, 6, 2, 5, tzinfo=timezone.utc)
TROPICAL_YEAR_MILLISECONDS = 31_556_925_974.7
SOLAR_TERM_MINUTES = (
    0, 21208, 42467, 63836, 85337, 107014,
    128867, 150921, 173149, 195551, 218072, 240693,
    263343, 285989, 308563, 331033, 353350, 375494,
    397447, 419210, 440795, 462224, 483532, 504758,
)
JIE_TERM_INDICES = tuple(range(0, 24, 2))


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.astimezone().astimezone(timezone.utc)
    return value.astimezone(timezone.utc)


def solar_term_utc(year: int, term_index: int) -> datetime:
    if term_index not in range(24):
        raise ValueError("term_index must be from 0 to 23")
    elapsed = timedelta(
        milliseconds=TROPICAL_YEAR_MILLISECONDS * (year - 1900)
        + SOLAR_TERM_MINUTES[term_index] * 60_000
    )
    return SOLAR_TERM_EPOCH + elapsed


def sexagenary_for_datetime(value: datetime) -> dict[str, str]:
    """Return sexagenary pillars without assigning any divinatory effect."""
    utc_value = _as_utc(value)
    local_date = value.date()

    lichun = solar_term_utc(value.year, 2)
    pillar_year = value.year if utc_value >= lichun else value.year - 1
    year_index = (pillar_year - YEAR_REFERENCE) % 60
    year_stem_index = year_index % 10
    year_branch_index = year_index % 12

    boundaries = []
    for boundary_year in (value.year - 1, value.year, value.year + 1):
        for term_index in JIE_TERM_INDICES:
            instant = solar_term_utc(boundary_year, term_index)
            if instant <= utc_value:
                boundaries.append((instant, term_index))
    if not boundaries:
        raise RuntimeError("unable to determine the latest solar-term boundary")
    month_boundary, term_index = max(boundaries)
    month_branch_index = (term_index // 2 + 1) % 12
    month_offset_from_yin = (month_branch_index - 2) % 12
    yin_month_stem_index = (year_stem_index % 5 * 2 + 2) % 10
    month_stem_index = (yin_month_stem_index + month_offset_from_yin) % 10

    day_index = (local_date - DAY_REFERENCE).days % 60
    day_stem_index = day_index % 10
    day_branch_index = day_index % 12

    year_stem, year_branch = STEMS[year_stem_index], BRANCHES[year_branch_index]
    month_stem, month_branch = STEMS[month_stem_index], BRANCHES[month_branch_index]
    day_stem, day_branch = STEMS[day_stem_index], BRANCHES[day_branch_index]
    return {
        "year_stem": year_stem,
        "year_branch": year_branch,
        "year_ganzhi": year_stem + year_branch,
        "month_stem": month_stem,
        "month_branch": month_branch,
        "month_ganzhi": month_stem + month_branch,
        "day_stem": day_stem,
        "day_branch": day_branch,
        "day_ganzhi": day_stem + day_branch,
        "month_boundary_utc": month_boundary.isoformat(),
    }
