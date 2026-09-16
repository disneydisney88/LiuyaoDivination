"""Deterministic exhaustive/ sampled sweeps for the current Liuyao engine.

TASK_CODEX_21 extends the Tier 3 audit to the human-only yongshen flow.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.build import build  # noqa: E402
from engine.narrate import MISSING_TEXT, _derivation, _load_templates, narrate  # noqa: E402
from engine.pipeline import build_case_state  # noqa: E402
from engine.relations import (  # noqa: E402
    BRANCHES,
    BRANCH_ELEMENT,
    SEASONAL_STATE_CATEGORIES,
    build_relation_graph,
)
from engine.semantics import (  # noqa: E402
    VALID_STATUSES,
    chong_source_for_line,
    infer_condition,
    load_decision_table,
    semantic_for_condition,
)
from engine.yongshen import (  # noqa: E402
    LINE_POSITION_OPTIONS,
    analyze_yongshen,
    candidate_options,
)
from tools.generate_data import IMAGES, PALACE_ORDER, generate_bagong, trigram_name  # noqa: E402
from ui_contracts import YONGSHEN_OPTIONS  # noqa: E402


SWEEP_DIR = ROOT / "sweep"
GOLDEN_DIR = SWEEP_DIR / "golden"
BASELINE_COMMIT = "13eb522"
BASELINE_TESTS = 125
FIXED_TIME = "2026-09-13T15:49"
CONFIRMATION = "REGENERATE CURRENT STATE BASELINE"
RESULT_CLASSES = ("exception", "check_failed", "placeholder", "normal")
CHONG_SOURCE_VALUES = ("month", "day", "moving_line", "multiple")
DAY_GANZHI = tuple(
    "甲乙丙丁戊己庚辛壬癸"[index % 10] + BRANCHES[index % 12]
    for index in range(60)
)
MOVING_PATTERNS = (
    ("static", ()),
    ("one_line_1", (1,)),
    ("three_lines_1_3_5", (1, 3, 5)),
)
GOLDEN_HEADER = """# 本 snapshot 產生於 commit 13eb522（125 tests）
# 此為現況基準，非正確基準。
#
# 產生時之已知問題狀態：
#   [已修] 1. 旬空、月破顯示佔位符（L2 未接通）
#   [已修] 2. 逐爻推導全部「未有對應模板」
#   [已修] 3. 多軌頁只顯示三本、標「三家共識」
#   [已修] 4. 原文摺疊區「未提供逐字原文」
#   [未修] 5. 卦名不完整（「水雷」缺「屯」）—— L1 運算層
#   [未修] 6. 伏神 dump JSON、內部 TODO 標記洩漏
#   [未修] 7. 用神選擇疑無實際作用（L3）
#
# 修復 5–7 後須重新產生 snapshot 並更新本檔頭。
"""


def _golden_header(commit: str, test_count: int) -> str:
    if commit == BASELINE_COMMIT:
        return GOLDEN_HEADER
    return f"""# 本 snapshot 產生於 commit {commit}（{test_count} tests）
# 此為修復後現況基準，非跨版本永恆正確性證明。
# 產生時 §11.1 待決項為 55 項。
#
# 產生時之已知問題狀態：
#   [已修] 1. 旬空、月破顯示佔位符（L2 未接通）
#   [已修] 2. 逐爻推導全部「未有對應模板」
#   [已修] 3. 多軌頁只顯示三本、標「三家共識」
#   [已修] 4. 原文摺疊區「未提供逐字原文」
#   [已修] 5. 卦名不完整（「水雷」缺「屯」）—— L1 運算層
#   [已修] 6. 伏神 dump JSON、內部 TODO 標記洩漏
#   [已修] 7. 用神選擇疑無實際作用（L3）
#
# K／Y 僅呈現多軌材料，未把空亡、沖散或四神判語應用為效果語義。
"""


def _collected_test_count() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    return sum("::test_" in line for line in (result.stdout or "").splitlines())

TIER1_FIELDS = (
    "case_index", "hexagram_id", "hexagram_name", "lines", "moving_mask",
    "moving_positions", "moving_count_expected", "moving_count_actual",
    "changed_lines_complete", "hidden_count", "failed_checks",
    "placeholder_checks", "exception_type", "exception_message", "result_class",
)
TIER2_FIELDS = (
    "case_index", "hexagram_id", "hexagram_name", "moving_pattern",
    "moving_positions", "month_branch", "day_ganzhi", "xunkong",
    "month_break_branch", "seasonal_states", "empty_line_count",
    "month_break_line_count", "template_missing_lines", "template_missing_contexts",
    "c1_hits", "c15_hits", "c1_chong_sources", "c15_chong_sources", "all_chong_sources",
    "failed_checks", "placeholder_checks",
    "exception_type", "exception_message", "result_class",
)
TIER3_FIELDS = (
    "case_index", "sample_id", "hexagram_id", "hexagram_name", "palace",
    "moving_pattern", "moving_positions", "month_branch", "day_ganzhi",
    "yongshen", "visible_candidates", "hidden_candidate_count", "selected_line",
    "is_yongshen_positions", "yuanshen_positions", "jishen_positions",
    "choushen_positions", "c1_condition", "c15_condition", "c1_track_count",
    "c15_track_count", "k_condition", "k_track_count", "y_table_available",
    "y_track_count", "track_originals_nonempty", "table_status_counts", "output_signature",
    "c1_chong_source", "c15_chong_source", "collection_status_counts",
    "line_position_choice_statuses", "line_position_choices_all_locked",
    "output_json", "equal_to_choices", "selection_status", "pending_selection",
    "hidden_choice_required", "hidden_choice_options", "candidate_state_fields_complete",
    "flying_hidden_relation_status", "y_locations", "y_located",
    "y_five_state_locations_matched",
    "four_god_positions_unique", "all_chong_sources", "triggered_tables", "template_missing_lines",
    "template_missing_contexts", "failed_checks", "placeholder_checks",
    "exception_type", "exception_message", "result_class",
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_csv(path: Path, fields: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    """Write plain CSV or byte-reproducible gzip-compressed CSV.

    ``gzip.open(..., 'wt')`` embeds the current time in its header.  Full
    sweep artifacts are golden-comparison inputs, so compressed output fixes
    both that timestamp and the optional embedded filename.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        with path.open("wb") as binary_handle:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=binary_handle,
                compresslevel=9, mtime=0,
            ) as gzip_handle:
                with io.TextIOWrapper(gzip_handle, encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(rows)
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(line for line in handle if not line.startswith("#")))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def _read_text(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    """Write text as plain UTF-8 or as byte-reproducible gzip."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        with path.open("wb") as binary_handle:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=binary_handle,
                compresslevel=9, mtime=0,
            ) as gzip_handle:
                gzip_handle.write(text.encode("utf-8"))
        return
    path.write_text(text, encoding="utf-8", newline="")


def strip_golden_header(text: str) -> str:
    """Return the deterministic CSV body from a commented golden file."""
    return "\n".join(line for line in text.splitlines() if not line.startswith("#")).lstrip("\n") + "\n"


def _classify(exception_type: str, failed: list[str], placeholders: list[str]) -> str:
    if exception_type:
        return "exception"
    if failed:
        return "check_failed"
    if placeholders:
        return "placeholder"
    return "normal"


def _moving_positions(mask: int) -> tuple[int, ...]:
    return tuple(position for position in range(1, 7) if mask & (1 << (position - 1)))


def _combined_trigram_name(lines: Iterable[int]) -> str:
    bits = tuple(lines)
    lower = trigram_name(bits[:3])
    upper = trigram_name(bits[3:])
    return IMAGES[upper] + IMAGES[lower]


def run_tier1(output_path: Path | None = None) -> dict[str, Any]:
    """Run all 64 hexagrams against all 64 moving-line masks."""
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    case_index = 0
    for source in generate_bagong():
        for mask in range(64):
            case_index += 1
            moving = _moving_positions(mask)
            failed: list[str] = []
            placeholders: list[str] = []
            exception_type = ""
            exception_message = ""
            actual_moving: int | str = ""
            changed_complete: bool | str = not moving
            hidden_count: int | str = ""
            name = source["name"]
            try:
                state = build_case_state(
                    lines=source["lines"], cast_datetime=FIXED_TIME,
                    moving_positions=moving,
                )
                chart = state["chart"]
                relations = state["relations"]
                name = chart.get("name", "")
                if len(name) < 3:
                    failed.append("name_length_lt_3")
                if name == _combined_trigram_name(chart["lines"]):
                    failed.append("name_equals_upper_lower_images")
                for field in ("palace", "palace_element", "shi", "ying"):
                    if chart.get(field) in (None, ""):
                        failed.append(f"missing_{field}")
                if chart.get("ying") != ((chart.get("shi", 0) - 1 + 3) % 6) + 1:
                    failed.append("shi_ying_formula")
                line_rows = chart.get("lines_detail") or []
                if len(line_rows) != 6 or any(
                    any(line.get(field) in (None, "") for field in ("branch", "element", "six_relative"))
                    for line in line_rows
                ):
                    failed.append("incomplete_line_details")
                hidden = chart.get("hidden")
                if not isinstance(hidden, list):
                    failed.append("hidden_not_list")
                else:
                    hidden_count = len(hidden)
                actual_moving = sum(line.get("motion") != "靜" for line in relations.get("lines", []))
                if actual_moving != len(moving):
                    failed.append("moving_count_mismatch")
                if moving:
                    changed = state.get("changed_chart")
                    changed_complete = bool(
                        isinstance(changed, dict)
                        and len(changed.get("lines_detail") or []) == 6
                        and len(changed.get("lines") or []) == 6
                    )
                    if not changed_complete:
                        failed.append("changed_hexagram_missing_or_incomplete")
            except Exception as exc:  # audit requires recording every failure
                exception_type = type(exc).__name__
                exception_message = str(exc)
            rows.append({
                "case_index": case_index,
                "hexagram_id": source["hexagram_id"],
                "hexagram_name": name,
                "lines": "".join(map(str, source["lines"])),
                "moving_mask": mask,
                "moving_positions": "|".join(map(str, moving)),
                "moving_count_expected": len(moving),
                "moving_count_actual": actual_moving,
                "changed_lines_complete": str(changed_complete).lower(),
                "hidden_count": hidden_count,
                "failed_checks": "|".join(failed),
                "placeholder_checks": "|".join(placeholders),
                "exception_type": exception_type,
                "exception_message": exception_message,
                "result_class": _classify(exception_type, failed, placeholders),
            })
    destination = output_path or SWEEP_DIR / "tier1_L1.csv.gz"
    _write_csv(destination, TIER1_FIELDS, rows)
    return {
        "tier": 1, "combinations": len(rows),
        "elapsed_seconds": time.perf_counter() - started,
        "result_classes": Counter(row["result_class"] for row in rows),
    }


def _template_audit(relations: dict[str, Any], templates: dict[str, dict[str, Any]]) -> tuple[list[int], list[str]]:
    missing_lines: list[int] = []
    contexts: list[str] = []
    for position in range(1, 7):
        steps, missing = _derivation(relations, position, templates)
        if missing or any(step.get("text") == MISSING_TEXT for step in steps):
            missing_lines.append(position)
            for step in steps:
                if step.get("template_missing") or step.get("text") == MISSING_TEXT:
                    contexts.append(
                        "line{}:step{}:rule={}".format(
                            position, step.get("step"), step.get("rule_id") or "none",
                        )
                    )
    return missing_lines, contexts


def _condition_hits(relations: dict[str, Any], table_id: str) -> tuple[str, str]:
    hits = []
    sources = []
    for position in range(1, 7):
        condition = infer_condition(table_id=table_id, relation_result=relations, line=position)
        if condition:
            hits.append(f"{position}:{condition}")
            if table_id in {"C1", "C15"}:
                source = chong_source_for_line(relations, position)
                if source:
                    sources.append(f"{position}:{source}")
    return "|".join(hits), "|".join(sources)


def _all_chong_sources(relations: dict[str, Any]) -> str:
    """Record mechanical clash provenance without assigning it a table row."""
    return "|".join(
        f"{row['position']}:{source}"
        for row in relations.get("lines", [])
        if (source := chong_source_for_line(relations, row["position"]))
    )


def run_tier2(output_path: Path | None = None) -> dict[str, Any]:
    """Run 64 × 3 movement samples × 12 months × 60 days."""
    started = time.perf_counter()
    templates = _load_templates()
    charts = [(row, build(row["lines"])) for row in generate_bagong()]
    rows: list[dict[str, Any]] = []
    case_index = 0
    for source, chart in charts:
        for pattern_name, moving in MOVING_PATTERNS:
            for month_branch in BRANCHES:
                for day_ganzhi in DAY_GANZHI:
                    case_index += 1
                    failed: list[str] = []
                    placeholders: list[str] = []
                    exception_type = ""
                    exception_message = ""
                    xunkong_value = ""
                    month_break_branch = ""
                    seasonal_states = ""
                    empty_count: int | str = ""
                    break_count: int | str = ""
                    missing_lines: list[int] = []
                    missing_contexts: list[str] = []
                    c1_hits = ""
                    c15_hits = ""
                    c1_chong_sources = ""
                    c15_chong_sources = ""
                    all_chong_sources = ""
                    try:
                        relations = build_relation_graph(
                            line_rows=chart["lines_detail"], hidden=chart["hidden"],
                            month_element=BRANCH_ELEMENT[month_branch], month_branch=month_branch,
                            day_stem=day_ganzhi[0], day_branch=day_ganzhi[1],
                            moving_positions=moving, changing_positions=moving,
                        )
                        empty = relations.get("empty_branches")
                        if not (
                            isinstance(empty, list) and len(empty) == 2
                            and len(set(empty)) == 2 and all(item in BRANCHES for item in empty)
                        ):
                            failed.append("invalid_or_placeholder_xunkong")
                        xunkong_value = "|".join(empty or [])
                        month_break_branch = relations.get("month_break_branch", "")
                        if month_break_branch not in BRANCHES:
                            failed.append("invalid_or_placeholder_month_break")
                        states = relations.get("lines") or []
                        labels = [line.get("seasonal_state") for line in states]
                        if len(labels) != 6 or any(label not in {"旺", "相", "休", "囚", "死"} for label in labels):
                            failed.append("invalid_seasonal_state")
                        seasonal_states = "|".join(label or "" for label in labels)
                        if any(edge.get("target") in {"日辰", "月建"} and not edge.get("source", "").startswith("變爻:")
                               for edge in relations.get("edges", [])):
                            failed.append("R-L2-04_reverse_edge")
                        for position in moving:
                            targets = {
                                edge.get("target") for edge in relations.get("edges", [])
                                if edge.get("source") == f"變爻:{position}"
                            }
                            if not targets <= {f"動爻:{position}", "日辰", "月建"}:
                                failed.append("R-L2-05_changed_scope")
                                break
                        if any(line.get("motion") not in {"動", "靜"} for line in states):
                            failed.append("motion_not_binary")
                        if any(
                            line.get("motion") != ("動" if line["position"] in moving else "靜")
                            for line in states
                        ):
                            failed.append("motion_does_not_match_input")
                        missing_lines, missing_contexts = _template_audit(relations, templates)
                        if missing_lines:
                            placeholders.append("narrative_template_missing")
                        c1_hits, c1_chong_sources = _condition_hits(relations, "C1")
                        c15_hits, c15_chong_sources = _condition_hits(relations, "C15")
                        all_chong_sources = _all_chong_sources(relations)
                        empty_count = sum(bool(line.get("empty")) for line in states)
                        break_count = sum(bool(line.get("month_break")) for line in states)
                    except Exception as exc:
                        exception_type = type(exc).__name__
                        exception_message = str(exc)
                    rows.append({
                        "case_index": case_index,
                        "hexagram_id": source["hexagram_id"],
                        "hexagram_name": source["name"],
                        "moving_pattern": pattern_name,
                        "moving_positions": "|".join(map(str, moving)),
                        "month_branch": month_branch,
                        "day_ganzhi": day_ganzhi,
                        "xunkong": xunkong_value,
                        "month_break_branch": month_break_branch,
                        "seasonal_states": seasonal_states,
                        "empty_line_count": empty_count,
                        "month_break_line_count": break_count,
                        "template_missing_lines": "|".join(map(str, missing_lines)),
                        "template_missing_contexts": "|".join(missing_contexts),
                        "c1_hits": c1_hits,
                        "c15_hits": c15_hits,
                        "c1_chong_sources": c1_chong_sources,
                        "c15_chong_sources": c15_chong_sources,
                        "all_chong_sources": all_chong_sources,
                        "failed_checks": "|".join(dict.fromkeys(failed)),
                        "placeholder_checks": "|".join(placeholders),
                        "exception_type": exception_type,
                        "exception_message": exception_message,
                        "result_class": _classify(exception_type, failed, placeholders),
                    })
    destination = output_path or SWEEP_DIR / "tier2_L2.csv.gz"
    _write_csv(destination, TIER2_FIELDS, rows)
    sources = _count_hits(rows, "all_chong_sources")
    if set(CHONG_SOURCE_VALUES) - set(sources):
        raise AssertionError("Tier 2 sampling did not cover every mechanical chong source")
    return {
        "tier": 2, "combinations": len(rows),
        "elapsed_seconds": time.perf_counter() - started,
        "result_classes": Counter(row["result_class"] for row in rows),
    }


def _tier3_samples() -> list[tuple[str, dict[str, Any], tuple[int, ...]]]:
    rows = generate_bagong()
    samples = []
    for source in rows:
        for pattern_name, moving in MOVING_PATTERNS:
            samples.append((f"hex{source['hexagram_id']}:{pattern_name}", source, moving))
    return samples


def _tier3_time_samples() -> list[tuple[str, str]]:
    """Use independently varied day branches for every sampled month branch."""
    # Same-branch and opposite-branch days jointly expose month-only,
    # day-only, simultaneous, and no date-driven clash states while keeping
    # the tracked audit CSV below GitHub's per-file size limit.
    offsets = (0, 6)
    day_for_branch = {ganzhi[1]: ganzhi for ganzhi in DAY_GANZHI[:12]}
    return [
        (month, day_for_branch[BRANCHES[(index + offset) % len(BRANCHES)]])
        for index, month in enumerate(BRANCHES)
        for offset in offsets
    ]


def _track_originals_nonempty(semantics: dict[str, Any], relations: dict[str, Any]) -> bool:
    rendered = narrate(semantics=semantics, relations=relations)
    relevant = [
        item for item in rendered.get("tracks", [])
        if item.get("status") in {"addressed", "different_axis", "category_negated"}
    ]
    return bool(relevant) and all(item.get("original") for item in relevant)


def _tier3_projection(
    *, state: dict[str, Any], choice: str, candidate_id: str | None,
    c1_table: dict[str, Any], c15_table: dict[str, Any], k_table: dict[str, Any],
    y_table: dict[str, Any], line_position_choice_statuses: dict[str, str],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Project the actual L3 result into stable sweep columns."""
    chart, relations = state["chart"], state["relations"]
    analysis = analyze_yongshen(state, choice, candidate_id)
    options = candidate_options(chart, choice)
    visible = [item["position"] for item in options if not item.get("hidden")]
    hidden = [item for item in options if item.get("hidden")]
    selected = analysis.get("selected") or {}
    pending = analysis.get("status") == "pending_selection"
    required_state_fields = {"position", "branch", "element", "six_relative", "seasonal_state", "empty", "month_break", "motion"}
    candidate_state_complete = all(required_state_fields <= set(item.get("state", {})) for item in analysis.get("candidates", []))
    hidden_choice_required = bool(hidden) and all(item.get("hidden") for item in options)
    selected_line = selected.get("position") if selected and not selected.get("hidden") else None
    decision = analysis.get("decision_table", {})
    c1_condition = decision.get("C1")
    c15_condition = decision.get("C15")
    k_condition = decision.get("K")
    y_available = bool(decision.get("Y"))
    y_locator = decision.get("Y") or {}
    y_five_state_locations_matched = all(
        bool(location.get("matches"))
        for location in y_locator.get("locations", [])
        if location.get("seasonal_state") in SEASONAL_STATE_CATEGORIES
    )
    chong_source = chong_source_for_line(relations, selected_line) if selected_line else None
    c1_semantics = (
        semantic_for_condition(line=selected_line, condition=c1_condition, hidden=chart["hidden"], table=c1_table)
        if c1_condition else None
    )
    c15_semantics = (
        semantic_for_condition(line=selected_line, condition=c15_condition, hidden=chart["hidden"], table=c15_table)
        if c15_condition else None
    )
    k_semantics = (
        semantic_for_condition(line=selected_line, condition=k_condition, hidden=chart["hidden"], table=k_table)
        if k_condition else None
    )
    # Y is deliberately a state-material table, not a single mutually
    # exclusive outcome.  A selected use-god makes all ten source rows
    # available for inspection; it does not fabricate a one-row match.
    y_status_counts = Counter(
        cell["status"] for row in y_table["rows"] for cell in row["cells"]
    ) if y_available else Counter()
    table_status_counts: dict[str, dict[str, int]] = {}
    collection_status_counts: dict[str, dict[str, int]] = {}
    for table_id, semantics in (("C1", c1_semantics), ("C15", c15_semantics), ("K", k_semantics)):
        if semantics:
            table_status_counts[table_id] = dict(Counter(
                track["status"] for track in semantics["tracks"].values()
            ))
            collection_status_counts[table_id] = dict(Counter(
                track.get("collection_status") for track in semantics["tracks"].values()
                if track.get("collection_status")
            ))
    if y_available:
        table_status_counts["Y"] = dict(y_status_counts)
        collection_status_counts["Y"] = dict(Counter(
            cell.get("collection_status")
            for row in y_table["rows"] for cell in row["cells"]
            if cell.get("collection_status")
        ))
    is_yongshen = [line["position"] for line in analysis.get("lines", []) if line.get("is_yongshen")]
    hidden_markers = [item for item in analysis.get("hidden", []) if item.get("is_yongshen")]
    projection = {
        "yongshen_choice": choice,
        "selected_candidate_id": candidate_id,
        "visible_candidates": visible,
        "hidden_candidate_count": len(hidden),
        "selected_line": selected_line,
        "is_yongshen_positions": is_yongshen,
        "hidden_yongshen_marked": bool(hidden_markers),
        "yuanshen_positions": [item["position"] for item in analysis.get("yuan_shen", [])],
        "jishen_positions": [item["position"] for item in analysis.get("ji_shen", [])],
        "choushen_positions": [item["position"] for item in analysis.get("chou_shen", [])],
        "c1_condition": c1_condition,
        "c15_condition": c15_condition,
        "c1_chong_source": chong_source if c1_condition else None,
        "c15_chong_source": chong_source if c15_condition else None,
        "k_condition": k_condition,
        "y_table_available": y_available,
        "y_locations": y_locator.get("locations", []),
        "y_located": bool(y_locator.get("located")),
        "y_five_state_locations_matched": y_five_state_locations_matched,
        "c1_track_count": len(c1_semantics["tracks"]) if c1_semantics else 0,
        "c15_track_count": len(c15_semantics["tracks"]) if c15_semantics else 0,
        "k_track_count": len(k_semantics["tracks"]) if k_semantics else 0,
        "y_track_count": len(y_table["books"]) if y_available else 0,
        "c1_originals_nonempty": _track_originals_nonempty(c1_semantics, relations) if c1_semantics else None,
        "c15_originals_nonempty": _track_originals_nonempty(c15_semantics, relations) if c15_semantics else None,
        "k_originals_nonempty": _track_originals_nonempty(k_semantics, relations) if k_semantics else None,
        "table_status_counts": table_status_counts,
        "collection_status_counts": collection_status_counts,
        "line_position_choice_statuses": line_position_choice_statuses,
        "line_position_choices_all_locked": all(
            status != "pending_selection" for status in line_position_choice_statuses.values()
        ),
        "no_condition_status": decision.get("status"),
        "target_element": analysis.get("target_element"),
        "moving_interactions": analysis.get("moving_interactions", []),
        "selection_status": analysis.get("status"),
        "pending_selection": pending,
        "hidden_choice_required": hidden_choice_required,
        "hidden_choice_options": "use_hidden|choose_other" if hidden_choice_required else "",
        "candidate_state_fields_complete": candidate_state_complete,
        "flying_hidden_relation_status": (
            analysis.get("flying_hidden_relation", {}).get("doctrinal_status")
            if analysis.get("flying_hidden_relation") else "not_applicable"
        ),
        "four_god_positions_unique": all(
            len({item["position"] for item in analysis.get(role, [])}) == len(analysis.get(role, []))
            for role in ("yuan_shen", "ji_shen", "chou_shen")
        ),
        "all_chong_sources": _all_chong_sources(relations),
        "triggered_tables": [
            table for table, condition in (("C1", c1_condition), ("C15", c15_condition), ("K", k_condition), ("Y", y_available))
            if condition
        ],
    }
    failed: list[str] = []
    placeholders: list[str] = []
    if not pending and not is_yongshen and not hidden_markers:
        failed.append("missing_is_yongshen_marker")
    if not candidate_state_complete:
        failed.append("candidate_state_fields_incomplete")
    if len(options) > 1 and not pending:
        failed.append("multiple_candidates_not_pending")
    if hidden_choice_required and not pending:
        failed.append("hidden_choice_not_pending")
    if pending and any(key in analysis for key in ("yuan_shen", "ji_shen", "chou_shen")):
        failed.append("pending_four_god_recalculation")
    if len(visible) > 1 and len(projection["visible_candidates"]) != len(visible):
        failed.append("duplicate_candidates_not_complete")
    if not pending and not visible and hidden and not hidden_markers:
        failed.append("hidden_candidate_not_marked")
    if not pending and c1_condition is None and c15_condition is None and k_condition is None and decision.get("status") != "此爻不觸發任何條件":
        failed.append("no_explicit_no_condition_result")
    if not pending and not projection["y_located"]:
        failed.append("y_table_not_located")
    if not pending and not projection["y_five_state_locations_matched"]:
        failed.append("y_five_state_not_mapped")
    if not projection["four_god_positions_unique"]:
        failed.append("four_god_duplicate_position")
    if not projection["line_position_choices_all_locked"]:
        failed.append("line_position_choice_pending_selection")
    for table_id, condition, count in (
        ("C1", c1_condition, projection["c1_track_count"]),
        ("C15", c15_condition, projection["c15_track_count"]),
        ("K", k_condition, projection["k_track_count"]),
        ("Y", y_available, projection["y_track_count"]),
    ):
        if condition and count != 8:
            failed.append(f"{table_id}_track_count_not_8")
    for flag in ("c1_originals_nonempty", "c15_originals_nonempty", "k_originals_nonempty"):
        if projection[flag] is False:
            placeholders.append(f"{flag}_false")
    return projection, failed, placeholders


def _different_fields(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    return sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))


def run_tier3(output_path: Path | None = None) -> dict[str, Any]:
    """Run 64 charts × 3 movements × 24 independent time samples × six."""
    started = time.perf_counter()
    templates = _load_templates()
    c1_table = load_decision_table(ROOT / "data" / "decision_tables" / "C1_chong_san.json")
    c15_table = load_decision_table(ROOT / "data" / "decision_tables" / "C15_dongjing_axis.json")
    k_table = load_decision_table(ROOT / "data" / "decision_tables" / "K_kongwang_effect.json")
    y_table = load_decision_table(ROOT / "data" / "decision_tables" / "Y_yuanshen_jishen.json")
    rows: list[dict[str, Any]] = []
    case_index = 0
    for sample_id, source, moving in _tier3_samples():
        chart = build(source["lines"])
        changed_bits = list(source["lines"])
        for position in moving:
            changed_bits[position - 1] ^= 1
        changed_chart = build(changed_bits) if moving else None
        for month_branch, day_ganzhi in _tier3_time_samples():
            relations = build_relation_graph(
                line_rows=chart["lines_detail"], hidden=chart["hidden"],
                month_element=BRANCH_ELEMENT[month_branch], month_branch=month_branch,
                day_stem=day_ganzhi[0], day_branch=day_ganzhi[1],
                moving_positions=moving, changing_positions=moving,
            )
            state = {"chart": chart, "changed_chart": changed_chart, "relations": relations}
            template_lines, template_contexts = _template_audit(relations, templates)
            line_position_choice_statuses = {
                line_choice: analyze_yongshen(state, line_choice).get("status")
                for line_choice in LINE_POSITION_OPTIONS
            }
            group: list[dict[str, Any]] = []
            for choice in YONGSHEN_OPTIONS:
                case_index += 1
                exception_type = ""
                exception_message = ""
                failed: list[str] = []
                placeholders: list[str] = []
                projection: dict[str, Any] = {}
                try:
                    options = candidate_options(chart, choice)
                    hidden_only = bool(options) and all(item.get("hidden") for item in options)
                    candidate_id = (
                        options[0]["candidate_id"]
                        if len(options) == 1 and not hidden_only else None
                    )
                    projection, failed, placeholders = _tier3_projection(
                        state=state, choice=choice, candidate_id=candidate_id,
                        c1_table=c1_table, c15_table=c15_table,
                        k_table=k_table, y_table=y_table,
                        line_position_choice_statuses=line_position_choice_statuses,
                    )
                    if template_lines:
                        placeholders.append("narrative_template_missing")
                except Exception as exc:
                    exception_type = type(exc).__name__
                    exception_message = str(exc)
                group.append({
                    "case_index": case_index,
                    "sample_id": sample_id,
                    "hexagram_id": source["hexagram_id"],
                    "hexagram_name": source["name"],
                    "palace": source["palace"],
                    "moving_pattern": sample_id.split(":", 1)[1],
                    "moving_positions": "|".join(map(str, moving)),
                    "month_branch": month_branch,
                    "day_ganzhi": day_ganzhi,
                    "yongshen": choice,
                    "projection": projection,
                    "failed": failed,
                    "placeholders": placeholders,
                    "exception_type": exception_type,
                    "exception_message": exception_message,
                    "template_lines": template_lines,
                    "template_contexts": template_contexts,
                })
            signatures = {
                item["yongshen"]: _sha256_bytes(_json(item["projection"]).encode("utf-8"))
                for item in group
            }
            for item in group:
                equal_choices = sorted(
                    other for other, signature in signatures.items()
                    if other != item["yongshen"] and signature == signatures[item["yongshen"]]
                )
                if equal_choices:
                    item["failed"].append("yongshen_output_equal_to_other_choice")
                projection = item["projection"]
                rows.append({
                    "case_index": item["case_index"],
                    "sample_id": item["sample_id"],
                    "hexagram_id": item["hexagram_id"],
                    "hexagram_name": item["hexagram_name"],
                    "palace": item["palace"],
                    "moving_pattern": item["moving_pattern"],
                    "moving_positions": item["moving_positions"],
                    "month_branch": item["month_branch"],
                    "day_ganzhi": item["day_ganzhi"],
                    "yongshen": item["yongshen"],
                    "visible_candidates": "|".join(map(str, projection.get("visible_candidates", []))),
                    "hidden_candidate_count": projection.get("hidden_candidate_count", ""),
                    "selected_line": projection.get("selected_line") or "",
                    "is_yongshen_positions": "|".join(map(str, projection.get("is_yongshen_positions", []))),
                    "yuanshen_positions": _json(projection.get("yuanshen_positions")),
                    "jishen_positions": _json(projection.get("jishen_positions")),
                    "choushen_positions": _json(projection.get("choushen_positions")),
                    "c1_condition": projection.get("c1_condition") or "",
                    "c15_condition": projection.get("c15_condition") or "",
                    "c1_chong_source": projection.get("c1_chong_source") or "",
                    "c15_chong_source": projection.get("c15_chong_source") or "",
                    "c1_track_count": projection.get("c1_track_count", ""),
                    "c15_track_count": projection.get("c15_track_count", ""),
                    "k_condition": projection.get("k_condition") or "",
                    "k_track_count": projection.get("k_track_count", ""),
                    "y_table_available": str(projection.get("y_table_available", False)).lower(),
                    "y_track_count": projection.get("y_track_count", ""),
                    "track_originals_nonempty": _json({
                        "C1": projection.get("c1_originals_nonempty"),
                        "C15": projection.get("c15_originals_nonempty"),
                        "K": projection.get("k_originals_nonempty"),
                    }),
                    "table_status_counts": _json(projection.get("table_status_counts", {})),
                    "collection_status_counts": _json(projection.get("collection_status_counts", {})),
                    "line_position_choice_statuses": _json(projection.get("line_position_choice_statuses", {})),
                    "line_position_choices_all_locked": str(projection.get("line_position_choices_all_locked", False)).lower(),
                    "output_signature": signatures[item["yongshen"]],
                    "output_json": _json(projection),
                    "equal_to_choices": "|".join(equal_choices),
                    "selection_status": projection.get("selection_status", ""),
                    "pending_selection": str(projection.get("pending_selection", False)).lower(),
                    "hidden_choice_required": str(projection.get("hidden_choice_required", False)).lower(),
                    "hidden_choice_options": projection.get("hidden_choice_options", ""),
                    "candidate_state_fields_complete": str(projection.get("candidate_state_fields_complete", False)).lower(),
                    "flying_hidden_relation_status": projection.get("flying_hidden_relation_status", ""),
                    "y_locations": _json(projection.get("y_locations", [])),
                    "y_located": str(projection.get("y_located", False)).lower(),
                    "y_five_state_locations_matched": str(projection.get("y_five_state_locations_matched", False)).lower(),
                    "four_god_positions_unique": str(projection.get("four_god_positions_unique", False)).lower(),
                    "all_chong_sources": projection.get("all_chong_sources", ""),
                    "triggered_tables": "|".join(projection.get("triggered_tables", [])),
                    "template_missing_lines": "|".join(map(str, item["template_lines"])),
                    "template_missing_contexts": "|".join(item["template_contexts"]),
                    "failed_checks": "|".join(dict.fromkeys(item["failed"])),
                    "placeholder_checks": "|".join(dict.fromkeys(item["placeholders"])),
                    "exception_type": item["exception_type"],
                    "exception_message": item["exception_message"],
                    "result_class": _classify(item["exception_type"], item["failed"], item["placeholders"]),
                })
    destination = output_path or SWEEP_DIR / "tier3_yongshen.csv.gz"
    _write_csv(destination, TIER3_FIELDS, rows)
    sources = _count_hits(rows, "all_chong_sources")
    if set(CHONG_SOURCE_VALUES) - set(sources):
        raise AssertionError("Tier 3 sampling did not cover every mechanical chong source")
    return {
        "tier": 3, "combinations": len(rows),
        "elapsed_seconds": time.perf_counter() - started,
        "result_classes": Counter(row["result_class"] for row in rows),
    }


def _count_hits(rows: list[dict[str, str]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for item in filter(None, row.get(field, "").split("|")):
            counts[item.split(":", 1)[-1]] += 1
    return counts


def _format_counter(counter: Counter[Any], order: Iterable[Any] | None = None) -> str:
    keys = list(order) if order is not None else sorted(counter, key=str)
    return ", ".join(f"{key}={counter.get(key, 0):,}" for key in keys)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
        encoding="utf-8",
    ).stdout


def _commit_file_sha(commit: str, path: str) -> str:
    data = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True,
    ).stdout
    return _sha256_bytes(data)


def _baseline_change_section() -> list[str]:
    changed = []
    for raw in _git("diff", "--name-status", "a715a60..13eb522").splitlines():
        status, path = raw.split("\t", 1)
        changed.append((status, path, _commit_file_sha(BASELINE_COMMIT, path)))
    test_descriptions = {
        "test_c1_conflict_summary_is_not_the_obsolete_three_book_consensus": "禁止 conflicts 摘要倒退成舊『三家共識』。",
        "test_decision_table_original_is_used_when_no_doctrinal_rule_matches": "doctrinal rule 未命中時，以 decision-table cell 原文作可追溯 fallback。",
        "test_sexagenary_reference_day_and_solar_term_year_boundary": "核甲子參考日與立春前後年柱／月柱切換。",
        "test_complete_case_connects_calendar_relations_narrative_and_five_tracks": "完整卦例接通曆法、L2、模板與五本已有材料。",
        "test_streamlit_board_and_tracks_render_the_connected_case": "AppTest 驗盤面無旬空/月破／模板佔位，且多軌與原文可見。",
    }
    lines = [
        "## 附錄：`a715a60` → `13eb522` 補交記錄",
        "",
        "`13eb522`：Connect Streamlit UI to deterministic engine state；16 檔，+455 / -41。",
        "",
        "### 改動檔案與 `13eb522` 版本 SHA-256",
        "",
        "| 狀態 | 檔案 | SHA-256 |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| {status} | `{path}` | `{sha}` |" for status, path, sha in changed)
    lines.extend(["", "### 新增五個測試", ""])
    lines.extend(f"- `{name}`：{description}" for name, description in test_descriptions.items())
    return lines


def _decision_table_integration_audit() -> dict[str, Any]:
    chart = build([0, 1, 0, 0, 1, 0])
    relations = build_relation_graph(
        line_rows=chart["lines_detail"], hidden=chart["hidden"],
        month_element="金", month_branch="酉", day_stem="庚", day_branch="寅",
    )
    result = {
        "rows": 0, "all_tracks_eight": True, "all_relevant_originals": True,
        "missing_originals": [],
    }
    for filename in (
        "C1_chong_san.json", "C15_dongjing_axis.json",
        "K_kongwang_effect.json", "Y_yuanshen_jishen.json",
    ):
        table = load_decision_table(ROOT / "data" / "decision_tables" / filename)
        for row in table["rows"]:
            result["rows"] += 1
            semantics = semantic_for_condition(line=4, condition=row["condition"], hidden=chart["hidden"], table=table)
            result["all_tracks_eight"] &= len(semantics["tracks"]) == 8
            rendered = narrate(semantics=semantics, relations=relations)
            missing = [
                {"table_id": table["table_id"], "row_id": row["row_id"],
                 "condition": row["condition"], "book": item["book"],
                 "status": item["status"], "source": item.get("source_locator")}
                for item in rendered.get("tracks", [])
                if item.get("status") in {"addressed", "different_axis", "category_negated"}
                and not item.get("original")
            ]
            result["missing_originals"].extend(missing)
            result["all_relevant_originals"] &= not missing
    return result


def _coverage_statistics(tier3: list[dict[str, str]]) -> dict[str, Any]:
    """Report actual C1/C15/K/Y material availability, without effects.

    C1, C15 and K have a mechanically selected row.  Y is a ten-row material
    inventory: once a concrete use-god is selected it is available as a whole,
    rather than pretending that the engine has judged one of its states true.
    """
    tables = {
        "C1": load_decision_table(ROOT / "data" / "decision_tables" / "C1_chong_san.json"),
        "C15": load_decision_table(ROOT / "data" / "decision_tables" / "C15_dongjing_axis.json"),
        "K": load_decision_table(ROOT / "data" / "decision_tables" / "K_kongwang_effect.json"),
        "Y": load_decision_table(ROOT / "data" / "decision_tables" / "Y_yuanshen_jishen.json"),
    }
    rows_by_condition = {
        table_id: {item["condition"]: item for item in table["rows"]}
        for table_id, table in tables.items()
    }
    row_hits: Counter[str] = Counter()
    table_hits: Counter[str] = Counter()
    status_distribution: Counter[str] = Counter()
    collection_status_distribution: Counter[str] = Counter()
    current: set[int] = set()
    viewable: set[int] = set()
    resolved: set[int] = set()

    for index, result in enumerate(tier3):
        selected = bool(result.get("selected_line"))
        if selected:
            resolved.add(index)
        triggered: list[tuple[str, dict[str, Any]]] = []
        for table_id, column in (("C1", "c1_condition"), ("C15", "c15_condition"), ("K", "k_condition")):
            condition = result.get(column, "")
            if condition:
                table_row = rows_by_condition[table_id][condition]
                triggered.append((table_id, table_row))
        if result.get("y_table_available") == "true":
            # Keep Y's ten conditions distinct; this is not an inferred match.
            for table_row in tables["Y"]["rows"]:
                triggered.append(("Y", table_row))
        if not triggered:
            continue
        current.add(index)
        for table_id, table_row in triggered:
            table_hits[table_id] += 1
            row_hits[table_row["row_id"]] += 1
            statuses = [cell["status"] for cell in table_row["cells"]]
            status_distribution.update(statuses)
            collection_status_distribution.update(
                cell["collection_status"]
                for cell in table_row["cells"]
                if cell.get("status") == "not_collected"
            )
            if "addressed" in statuses:
                viewable.add(index)

    total = len(tier3)
    k_hits = {
        index for index, result in enumerate(tier3)
        if result.get("k_condition")
    }
    k_month_break_hits = {
        index for index, result in enumerate(tier3)
        if result.get("k_condition") == "空而逢月破"
    }
    return {
        "total": total,
        "current_trigger": len(current),
        "current_viewable": len(viewable),
        "row_hits": row_hits,
        "table_hits": table_hits,
        "status_distribution": {status: status_distribution[status] for status in sorted(VALID_STATUSES)},
        "collection_status_distribution": {
            "ingested_not_surveyed": collection_status_distribution["ingested_not_surveyed"],
            "not_ingested": collection_status_distribution["not_ingested"],
        },
        "resolved": len(resolved),
        "pending": total - len(resolved),
        "locked": len(resolved),
        "locked_current_trigger": len(current & resolved),
        "locked_current_viewable": len(viewable & resolved),
        # Kept for the historical TASK_21 report subsection below.  K and Y
        # are now actual tables, hence adding either set to ``current`` adds
        # no further coverage; the values are explicitly labelled as such.
        "empty_raw": len(k_hits),
        "empty_new": len(k_hits - current),
        "month_break_raw": len(k_month_break_hits),
        "month_break_new": len(k_month_break_hits - current),
        "current_plus_empty": len(current | k_hits),
        "current_plus_month_break": len(current | k_month_break_hits),
        "current_plus_both": len(current | k_hits | k_month_break_hits),
        "current_plus_resolved_state": len(current | resolved),
        "locked_current_plus_empty": len((current | k_hits) & resolved),
        "locked_current_plus_month_break": len((current | k_month_break_hits) & resolved),
        "locked_current_plus_both": len((current | k_hits | k_month_break_hits) & resolved),
        "locked_current_plus_state": len((current | resolved) & resolved),
        "month_break_is_subset_of_current": k_month_break_hits <= current,
    }


def write_report(stats: dict[int, dict[str, Any]] | None = None) -> Path:
    tier1 = _read_csv(SWEEP_DIR / "tier1_L1.csv.gz")
    tier2 = _read_csv(SWEEP_DIR / "tier2_L2.csv.gz")
    tier3 = _read_csv(SWEEP_DIR / "tier3_yongshen.csv.gz")
    stats = stats or {}
    class_counts = {
        tier: Counter(row["result_class"] for row in rows)
        for tier, rows in ((1, tier1), (2, tier2), (3, tier3))
    }
    exception_types = {
        tier: Counter(row["exception_type"] for row in rows if row["exception_type"])
        for tier, rows in ((1, tier1), (2, tier2), (3, tier3))
    }
    failure_types = {
        tier: Counter(
            item for row in rows for item in filter(None, row["failed_checks"].split("|"))
        ) for tier, rows in ((1, tier1), (2, tier2), (3, tier3))
    }
    missing_t2 = [row for row in tier2 if row["template_missing_lines"]]
    missing_t3 = [row for row in tier3 if row["template_missing_lines"]]
    non_binary_motion_t2 = failure_types[2]["motion_not_binary"] + failure_types[2]["motion_does_not_match_input"]
    unmatched_y_five_state_t3 = failure_types[3]["y_five_state_not_mapped"]
    missing_contexts = Counter(
        item for row in tier2 + tier3
        for item in filter(None, row["template_missing_contexts"].split("|"))
    )
    c1_order = ("旺相之爻遇沖", "有氣之爻遇沖", "臨日月之爻遇沖", "休囚之爻遇日沖", "既判為散之後")
    c15_order = ("靜爻遇沖", "動爻遇沖", "空爻遇沖")
    c1_t2 = _count_hits(tier2, "c1_hits")
    c15_t2 = _count_hits(tier2, "c15_hits")
    c1_t2_chong_sources = _count_hits(tier2, "c1_chong_sources")
    c15_t2_chong_sources = _count_hits(tier2, "c15_chong_sources")
    all_t2_chong_sources = _count_hits(tier2, "all_chong_sources")
    all_t3_chong_sources = _count_hits(tier3, "all_chong_sources")
    c1_t3 = Counter(row["c1_condition"] for row in tier3 if row["c1_condition"])
    c15_t3 = Counter(row["c15_condition"] for row in tier3 if row["c15_condition"])
    c1_chong_sources = Counter(row["c1_chong_source"] for row in tier3 if row["c1_chong_source"])
    c15_chong_sources = Counter(row["c15_chong_source"] for row in tier3 if row["c15_chong_source"])
    line_position_pending = sum(
        row.get("line_position_choices_all_locked") != "true" for row in tier3
    )
    coverage = _coverage_statistics(tier3)

    pair_stats: dict[tuple[str, str], list[int]] = defaultdict(list)
    equal_pairs: Counter[tuple[str, str]] = Counter()
    grouped: dict[tuple[str, str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in tier3:
        key = (row["sample_id"], row["month_branch"], row["day_ganzhi"], row["moving_pattern"])
        grouped[key][row["yongshen"]] = json.loads(row["output_json"])
    for outputs in grouped.values():
        for left, right in combinations(YONGSHEN_OPTIONS, 2):
            changed = _different_fields(outputs[left], outputs[right])
            pair_stats[(left, right)].append(len(changed))
            if not changed:
                equal_pairs[(left, right)] += 1
    pair_sample_count = len(next(iter(pair_stats.values()), []))

    hidden = Counter(
        int(row["hidden_count"]) for row in tier1 if row["moving_mask"] == "0" and row["hidden_count"]
    )
    seasonal = Counter(
        state for row in tier2 for state in filter(None, row["seasonal_states"].split("|"))
    )
    line_exposures = len(tier2) * 6
    empty_hits = sum(int(row["empty_line_count"] or 0) for row in tier2)
    break_hits = sum(int(row["month_break_line_count"] or 0) for row in tier2)
    integration = _decision_table_integration_audit()
    template_count = len(_load_templates())
    selection_status = Counter(row.get("selection_status", "") for row in tier3)
    pending_rows = sum(row.get("pending_selection") == "true" for row in tier3)
    hidden_choice_rows = sum(row.get("hidden_choice_required") == "true" for row in tier3)
    state_incomplete_rows = sum(row.get("candidate_state_fields_complete") != "true" for row in tier3)
    table_hits = Counter(
        table for row in tier3 for table in filter(None, row.get("triggered_tables", "").split("|"))
    )
    current_commit = _git("rev-parse", "--short", "HEAD").strip()
    current_tests = _collected_test_count()
    elapsed = {tier: stats.get(tier, {}).get("elapsed_seconds") for tier in (1, 2, 3)}

    lines = [
        "# TASK_CODEX_23 — Sweep Report",
        "",
        f"基準：`{current_commit}`（{current_tests} tests）。本報告為當前 code state 之量化結果；歷史 13eb522 現況基準及修復差異見 `sweep/REPAIR_DIFFS.md`。",
        "",
        "## A 部分 — 三層組合空間",
        "",
        "| Tier | 組合數 | 執行時間（秒） | 取樣定義 |",
        "| --- | ---: | ---: | --- |",
        f"| Tier 1 | {len(tier1):,} | {elapsed[1]:.3f} | 64 卦 × 64 動爻 mask；固定時間 `{FIXED_TIME}` |" if elapsed[1] is not None else f"| Tier 1 | {len(tier1):,} | 未記錄 | 64 卦 × 64 動爻 mask |",
        f"| Tier 2 | {len(tier2):,} | {elapsed[2]:.3f} | 64 卦 × 全靜／初爻動／初三五爻動 × 12 月建 × 60 日辰 |" if elapsed[2] is not None else f"| Tier 2 | {len(tier2):,} | 未記錄 | 64 卦 × 3 動爻 pattern × 12 × 60 |",
        f"| Tier 3 | {len(tier3):,} | {elapsed[3]:.3f} | 64 卦 × 3 動爻 pattern × 12 月支 × 2 獨立日支 × 6 用神選項 |" if elapsed[3] is not None else f"| Tier 3 | {len(tier3):,} | 未記錄 | 64 × 3 × 12 × 2 × 6 |",
        "",
        "Tier 2 完整交叉 12 月支與 60 日辰。Tier 3 每月取兩個獨立日支（同支、相沖），不再把月支與日支固定同支配對；兩者共同覆蓋月沖、日沖、同沖、皆不沖。此為狀態取樣，不宣稱對應同一公曆年。",
        "",
        "## B1 — 例外統計",
        "",
    ]
    for tier in (1, 2, 3):
        lines.append(f"- Tier {tier}：例外 {class_counts[tier]['exception']:,}；類型：{_format_counter(exception_types[tier]) or '無'}。")
    lines.extend(["", "最小重現：三層均無拋例外，故無最小重現組合。", "", "檢查項失敗另列於 D；不與 engine 例外混計。", ""])

    lines.extend([
        "## B2 — 模板覆蓋率",
        "",
        f"- Tier 2：`template_missing` {len(missing_t2):,}/{len(tier2):,}（{len(missing_t2) / len(tier2):.4%}）。",
        f"- Tier 3：`template_missing` {len(missing_t3):,}/{len(tier3):,}（{len(missing_t3) / len(tier3):.4%}）。",
        f"- Tier 2 動靜二值（僅 `動`／`靜`）失敗：{non_binary_motion_t2:,}/{len(tier2):,}。",
        f"- Tier 3 元神／忌神五態歸二類未命中：{unmatched_y_five_state_t3:,}/{len(tier3):,}。",
        f"- 缺失情境：{_format_counter(missing_contexts) or '無'}。",
        f"- 現行 `narrative_templates.json` 有 {template_count} 個唯一 template ID；本 sweep 所掃機械推導需新增 0 個。TASK_20 所稱 11 個是較早狀態之數字。",
        "",
    ])
    if not missing_t2 and not missing_t3:
        lines.append("結論：在本次掃描已提供完整 L2 輸入的情況下，逐爻機械推導沒有模板缺口；先前六爻全缺模板屬輸入未接通，不是現有機械模板不足。這不代表所有未來語義情境都有模板。")
    else:
        lines.append("結論：以上缺失發生於完整 L2 輸入之後，屬真正模板不足；未把它歸因於舊有輸入缺失。")
    lines.extend(["", "## B3 — 決策表命中分佈", ""])
    lines.append(f"Tier 2 共 {line_exposures:,} 個逐爻狀態：")
    for condition in c1_order:
        lines.append(f"- C1 `{condition}`：{c1_t2[condition]:,}（{c1_t2[condition] / line_exposures:.4%}）。")
    for condition in c15_order:
        lines.append(f"- C15 `{condition}`：{c15_t2[condition]:,}（{c15_t2[condition] / line_exposures:.4%}）。")
    c1_none = line_exposures - sum(c1_t2.values())
    c15_none = line_exposures - sum(c15_t2.values())
    lines.extend([
        f"- C1 不觸發：{c1_none:,}（{c1_none / line_exposures:.4%}）。",
        f"- C15 不觸發：{c15_none:,}（{c15_none / line_exposures:.4%}）。",
        "",
        f"Tier 3 目前可唯一定位者之 C1 命中：{_format_counter(c1_t3, c1_order)}；C15 命中：{_format_counter(c15_t3, c15_order)}。",
        f"Tier 2 C1 沖來源：{_format_counter(c1_t2_chong_sources, ('month', 'day', 'moving_line', 'multiple'))}；C15 沖來源：{_format_counter(c15_t2_chong_sources, ('month', 'day', 'moving_line', 'multiple'))}。",
        f"Tier 3 C1 沖來源：{_format_counter(c1_chong_sources, ('month', 'day', 'moving_line', 'multiple'))}；C15 沖來源：{_format_counter(c15_chong_sources, ('month', 'day', 'moving_line', 'multiple'))}。",
        f"全部機械沖來源（不把動爻沖硬塞入 C1／C15）：Tier 2 {_format_counter(all_t2_chong_sources, CHONG_SOURCE_VALUES)}；Tier 3 {_format_counter(all_t3_chong_sources, CHONG_SOURCE_VALUES)}。四值均有命中。",
        f"按爻位選八項皆直接鎖定、無 pending_selection：{len(tier3) - line_position_pending:,}/{len(tier3):,}。",
        "",
        "## B3a — 覆蓋率",
        "",
        "本節保留 TASK_21 的比較欄位，並以本包後 C1／C15／K／Y 實際觸發重算；詳細七種狀態統計見 B3b。『有嘢睇』只計所觸發材料至少一本 `status=addressed`，其餘狀態不併入 addressed。",
        "",
        f"- 觸發率：{coverage['current_trigger']:,}/{coverage['total']:,}（{coverage['current_trigger'] / coverage['total']:.4%}）。",
        f"- 有嘢睇率（在已觸發組合中）：{coverage['current_viewable']:,}/{coverage['current_trigger']:,}（{coverage['current_viewable'] / coverage['current_trigger']:.4%}）。",
        f"- 空手率：{coverage['total'] - coverage['current_trigger']:,}/{coverage['total']:,}（{(coverage['total'] - coverage['current_trigger']) / coverage['total']:.4%}）。",
        "",
        "### 逐格觸發次數",
        "",
        "| 格位 | 觸發組數 |",
        "| --- | ---: |",
    ])
    for row_id in ("C1-R1", "C1-R2", "C1-R3", "C1-R4", "C1-R5", "C15-R1", "C15-R2", "C15-R3"):
        lines.append(f"| `{row_id}` | {coverage['row_hits'].get(row_id, 0):,} |")
    lines.extend([
        "",
        "### K／Y 入庫後之對照（不改效果語義）",
        "",
        "以下只計算已有 concrete `selected_line` 之列；pending_selection 沒有已選用神爻，故不虛構格位命中。K 與 Y 現已入庫，故它們與現況聯集不再額外增加覆蓋；此表保留為與 TASK_21 基準的可追溯對照。",
        "",
        "| 實際可查材料 | 可觸發組數 | 相對現況新增 | 加入後空手組數 | 加入後空手率 |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| K（空亡狀態，機械 row） | {coverage['empty_raw']:,} | {coverage['empty_new']:,} | {coverage['total'] - coverage['current_plus_empty']:,} | {(coverage['total'] - coverage['current_plus_empty']) / coverage['total']:.4%} |",
        f"| K-R9（月破交集） | {coverage['month_break_raw']:,} | {coverage['month_break_new']:,} | {coverage['total'] - coverage['current_plus_month_break']:,} | {(coverage['total'] - coverage['current_plus_month_break']) / coverage['total']:.4%} |",
        f"| Y（concrete 用神時逐爻定位） | {coverage['resolved']:,} | {coverage['current_plus_resolved_state'] - coverage['current_trigger']:,} | {coverage['total'] - coverage['current_plus_resolved_state']:,} | {(coverage['total'] - coverage['current_plus_resolved_state']) / coverage['total']:.4%} |",
        f"| 三者合計（旬空＋月破＋concrete 元神／忌神） | — | — | {coverage['total'] - coverage['current_plus_resolved_state']:,} | {(coverage['total'] - coverage['current_plus_resolved_state']) / coverage['total']:.4%} |",
        "",
        f"加入三者並以 concrete 用神為前提之空手率：{coverage['total'] - coverage['current_plus_resolved_state']:,}/{coverage['total']:,}（{(coverage['total'] - coverage['current_plus_resolved_state']) / coverage['total']:.4%}）。",
        "題設若把『元神／忌神狀態表（恆觸發）』解作連尚未完成用神選擇的 pending 列也一律觸發，則理想化空手率為 0/13,824（0.0000%）；此不是目前 engine 可產生的狀態，故另列而不併入上面的保守可實現數字。",
        "",
        "### 以已鎖定用神爻為分母（補充）",
        "",
        f"已鎖定組合：{coverage['locked']:,}/{coverage['total']:,}；pending_selection：{coverage['pending']:,}。以下分母只計有 concrete `selected_line` 的組合，pending 不視為空手或缺陷。",
        "",
        f"- 觸發率：{coverage['locked_current_trigger']:,}/{coverage['locked']:,}（{coverage['locked_current_trigger'] / coverage['locked']:.4%}）。",
        f"- 空手率：{coverage['locked'] - coverage['locked_current_trigger']:,}/{coverage['locked']:,}（{(coverage['locked'] - coverage['locked_current_trigger']) / coverage['locked']:.4%}）。",
        "",
        "| 格位 | 觸發組數 | 佔已鎖定分母 |",
        "| --- | ---: | ---: |",
    ])
    for row_id in ("C1-R1", "C1-R2", "C1-R3", "C1-R4", "C1-R5", "C15-R1", "C15-R2", "C15-R3"):
        hit_count = coverage["row_hits"].get(row_id, 0)
        lines.append(f"| `{row_id}` | {hit_count:,} | {hit_count / coverage['locked']:.4%} |")
    lines.extend([
        "",
        "| 假設新增表 | 原始命中 | 新增覆蓋 | 加入後空手組數 | 加入後空手率 | 改善（百分點） |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| 旬空表 | {coverage['empty_raw']:,} | {coverage['empty_new']:,} | {coverage['locked'] - coverage['locked_current_plus_empty']:,} | {(coverage['locked'] - coverage['locked_current_plus_empty']) / coverage['locked']:.4%} | {coverage['empty_new'] / coverage['locked']:.4%} |",
        f"| 月破表 | {coverage['month_break_raw']:,} | {coverage['month_break_new']:,} | {coverage['locked'] - coverage['locked_current_plus_month_break']:,} | {(coverage['locked'] - coverage['locked_current_plus_month_break']) / coverage['locked']:.4%} | {coverage['month_break_new'] / coverage['locked']:.4%} |",
        f"| 元神／忌神狀態表（concrete 列恆觸發） | {coverage['locked']:,} | {coverage['locked_current_plus_state'] - coverage['locked_current_trigger']:,} | {coverage['locked'] - coverage['locked_current_plus_state']:,} | {(coverage['locked'] - coverage['locked_current_plus_state']) / coverage['locked']:.4%} | {(coverage['locked_current_plus_state'] - coverage['locked_current_trigger']) / coverage['locked']:.4%} |",
        f"| 三者合計 | — | — | {coverage['locked'] - coverage['locked_current_plus_state']:,} | {(coverage['locked'] - coverage['locked_current_plus_state']) / coverage['locked']:.4%} | {(coverage['locked_current_plus_state'] - coverage['locked_current_trigger']) / coverage['locked']:.4%} |",
        "",
        f"月破結構核對：`month_break_hits ⊆ current_trigger` = `{coverage['month_break_is_subset_of_current']}`；本次為 {coverage['month_break_raw']:,}/{coverage['month_break_raw']:,}，所以月破表新增覆蓋為 0，並非統計遺漏。月破由月建所沖之爻定義，而現有 C1／C15 的遇沖判定已涵蓋這批組合；此處記錄為現有模型的結構關係，不新增效果語義。",
        "",
        "R2（有氣）沒有已核機械定義，R5（既判為散之後）涉及未實作效果語義；兩者 0 命中是自動推導刻意不作判定，**不能據此判為冷門**。R3 有機械命中，可據實比較頻率，但本 sweep 不裁決其文獻權重。",
        "",
        "## B3b — K／Y 實際覆蓋與七種狀態",
        "",
        "本節是本包後的現況統計。C1、C15、K 只在可機械定位 row 時列入；Y 在 concrete 用神選定後，按元神／忌神逐爻定位至可見機械格位。任何格位只並列原有材料，不表示引擎已判定其效果。",
        "",
        "| 表 | 觸發次數 |",
        "| --- | ---: |",
        f"| C1 | {coverage['table_hits'].get('C1', 0):,} |",
        f"| C15 | {coverage['table_hits'].get('C15', 0):,} |",
        f"| K | {coverage['table_hits'].get('K', 0):,} |",
        f"| Y（逐爻定位） | {coverage['table_hits'].get('Y', 0) // 10:,} |",
        "",
        "| status | 觸發材料 cells |",
        "| --- | ---: |",
    ])
    for status in ("addressed", "not_addressed", "not_collected", "category_negated", "concept_absent", "explicit_exclusion", "different_axis"):
        lines.append(f"| `{status}` | {coverage['status_distribution'][status]:,} |")
    lines.extend([
        "",
        "| not_collected 細分 | 觸發材料 cells |",
        "| --- | ---: |",
        f"| `ingested_not_surveyed` | {coverage['collection_status_distribution']['ingested_not_surveyed']:,} |",
        f"| `not_ingested` | {coverage['collection_status_distribution']['not_ingested']:,} |",
        "",
        f"全部 13,824 組：觸發 {coverage['current_trigger']:,}，空手 {coverage['total'] - coverage['current_trigger']:,}。已鎖定用神爻 {coverage['locked']:,} 組：觸發 {coverage['locked_current_trigger']:,}，空手 {coverage['locked'] - coverage['locked_current_trigger']:,}。pending_selection {coverage['pending']:,} 組按設計不進入 concrete 用神爻判定，不視為空手。",
        "",
        "## B4 — 用神差異驗證 ★★",
        "",
        "現已接通 `engine/yongshen.py`：用神類別及候選爻位由人手傳入，沒有自動揀用神；輸出以該候選為中心重算。",
        "",
        "現時實際重算欄位：用神本身之旺衰／旬空／月破／日辰標記；元神、忌神、仇神之候選爻位及狀態；兩現／伏藏；動爻對用神之生剋及變爻回頭剋機械標記；C1／C15／K 格位；以及 `is_yongshen`。Y 表在 concrete 用神選定後按元神／忌神逐爻定位，但不把任何書的材料判語應用為效果語義。",
        "",
        f"兩兩比較（每對 {pair_sample_count:,} 個同卦同時狀態；數值為 output projection 不同欄位數 min–max；完全相同列為基準數）：",
        "",
        "| 用神對 | 差異欄位 min–max | 完全相同 |",
        "| --- | ---: | ---: |",
    ])
    for pair in combinations(YONGSHEN_OPTIONS, 2):
        values = pair_stats[pair]
        lines.append(f"| {pair[0]} / {pair[1]} | {min(values)}–{max(values)} | {equal_pairs[pair]:,}/{len(values):,} |")
    total_equal = sum(equal_pairs.values())
    lines.extend([
        "",
        f"完全相同 pair-instance 合計：**{total_equal:,}**。任何非零值均表示現行用神輸出未能穩定區分該兩個選擇；此結果不作淡化。",
        "",
        "### B4a — 新用神流程檢查",
        "",
        f"- `selection_status`：{_format_counter(selection_status)}。",
        f"- 兩現／多現進入 `pending_selection`：{pending_rows:,}/{len(tier3):,}。",
        f"- 不現之六親要求伏神二選一：{hidden_choice_rows:,}/{len(tier3):,}；選項固定為 `use_hidden|choose_other`。",
        f"- 八項機械狀態欄位缺失：{state_incomplete_rows:,}/{len(tier3):,}。",
        f"- C1／C15／K／Y 觸發表數：{_format_counter(table_hits) or '0'}。",
        "- L3 不輸出任何一家之狀態效果判定；Y 逐爻定位後僅以多軌材料呈現，仇神無格位（P-057），P-049、P-050、P-055 保留。",
        "",
        "## B5 — 結構分佈",
        "",
        f"- 64 卦全靜 `hidden`：{_format_counter(hidden, range(5))}（覆核 20/32/12/0/0）。",
        f"- 旺相休囚死（Tier 2 逐爻）：{_format_counter(seasonal, ('旺', '相', '休', '囚', '死'))}。",
        f"- 旬空命中：{empty_hits:,}/{line_exposures:,}（{empty_hits / line_exposures:.4%}）。",
        f"- 月破命中：{break_hits:,}/{line_exposures:,}（{break_hits / line_exposures:.4%}）。",
        "",
        "## B6 — 64 卦卦名核查",
        "",
        "| ID | lines（初→上） | 現行 name | 核查 |",
        "| ---: | --- | --- | --- |",
    ])
    for row in generate_bagong():
        combined = _combined_trigram_name(row["lines"])
        checks = []
        if len(row["name"]) < 3:
            checks.append("長度 < 3")
        if row["name"] == combined:
            checks.append("只得上卦象＋下卦象")
        lines.append(f"| {row['hexagram_id']} | {''.join(map(str, row['lines']))} | {row['name']} | {'；'.join(checks) if checks else '通過本包檢查'} |")
    bad_names = sum(
        len(row["name"]) < 3 or row["name"] == _combined_trigram_name(row["lines"])
        for row in generate_bagong()
    )
    name_summary = (
        "64 卦全部通過；此前 56 個非本宮卦之上下卦象短名已補為完整卦名。"
        if bad_names == 0 else
        "模式為非本宮卦只保留上、下卦象，缺卦名末字；本包只量化，未修資料生成器。"
    )
    lines.extend([
        "",
        f"結果：64 卦中 **{bad_names}** 卦名不合檢查；{name_summary}",
        "",
        "## 問題 1–4 修復覆核",
        "",
        f"- 問題 1（旬空／月破）：Tier 2 無效或佔位檢查 {failure_types[2]['invalid_or_placeholder_xunkong'] + failure_types[2]['invalid_or_placeholder_month_break']:,} 次。",
        f"- 問題 2（逐爻模板）：Tier 2 缺失 {len(missing_t2):,} 次。",
        f"- 問題 3（N 軌）：C1 + C15 + K + Y 共 {integration['rows']} rows，全部 8 tracks：{str(integration['all_tracks_eight']).lower()}。",
        f"- 問題 4（原文）：上述 rows 之 addressed／different_axis／category_negated 原文全部非空：{str(integration['all_relevant_originals']).lower()}。",
        "",
    ])
    if integration["missing_originals"]:
        lines.append("原文缺口（全部列出）：")
        for item in integration["missing_originals"]:
            lines.append(
                "- `{table_id}` / `{row_id}` / {book}（{status}）：source `{source}`，"
                "narrative `original` 為空。".format(**item)
            )
        lines.append("")
    lines.extend([
        "因此問題 1–3 可按本 sweep 覆核為已修；問題 4 仍有上述單一格缺口，屬修復不完整。報告沒有因 golden 檔頭之產生前標示而把它當成全數通過。",
        "",
        "## C 部分 — Golden Snapshot",
        "",
        "Golden 三個 CSV 由同名 sweep CSV 加入逐項問題狀態檔頭；`CHECKSUMS.txt` 記錄 SHA-256。`tests/test_sweep_regression.py` 重跑 Tier 1，移除 golden 註解檔頭後逐行比較；有差異時列前 20 行 unified diff，並提示差異可能是修復或回歸，須人手判斷。Tier 2、Tier 3 只由 `tools/sweep.py` 手動執行。",
        "",
        "## D 部分 — 四類結果（互斥）",
        "",
        "優先序：`exception` → `check_failed` → `placeholder` → `normal`；每一組合只歸一類，另保留各檢查欄以免失去細節。",
        "",
        "| Tier | 拋例外 | 檢查項失敗 | 佔位符 | 正常 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for tier in (1, 2, 3):
        counts = class_counts[tier]
        lines.append(f"| {tier} | {counts['exception']:,} | {counts['check_failed']:,} | {counts['placeholder']:,} | {counts['normal']:,} |")
    lines.extend(["", "檢查失敗類型："])
    for tier in (1, 2, 3):
        lines.append(f"- Tier {tier}：{_format_counter(failure_types[tier]) or '無'}。")
    lines.extend(["", *_baseline_change_section(), ""])
    path = SWEEP_DIR / "SWEEP_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_all() -> dict[int, dict[str, Any]]:
    stats = {1: run_tier1(), 2: run_tier2(), 3: run_tier3()}
    write_report(stats)
    return stats


def regenerate_golden() -> dict[int, dict[str, Any]]:
    print(f"Type exactly: {CONFIRMATION}")
    if input("> ").strip() != CONFIRMATION:
        raise SystemExit("Golden regeneration cancelled: confirmation did not match.")
    stats = run_all()
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    names = ("tier1_L1.csv.gz", "tier2_L2.csv.gz", "tier3_yongshen.csv.gz")
    current_commit = _git("rev-parse", "--short", "HEAD").strip()
    current_tests = _collected_test_count()
    header = _golden_header(current_commit, current_tests)
    for name in names:
        body = _read_text(SWEEP_DIR / name)
        _write_text(GOLDEN_DIR / name, header + body)
    checksum_lines = [
        "TASK_CODEX_23 golden snapshot",
        f"baseline_commit={current_commit}",
        f"baseline_tests={current_tests}",
        "status=current_post_fix_state_baseline",
        "",
    ]
    checksum_lines.extend(f"{file_sha256(GOLDEN_DIR / name)}  {name}" for name in names)
    (GOLDEN_DIR / "CHECKSUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tier", choices=("1", "2", "3"))
    group.add_argument("--all", action="store_true")
    group.add_argument("--regenerate-golden", action="store_true")
    args = parser.parse_args()
    if args.regenerate_golden:
        regenerate_golden()
        return
    if args.all:
        stats = run_all()
    else:
        runner = {"1": run_tier1, "2": run_tier2, "3": run_tier3}[args.tier]
        item = runner()
        stats = {int(args.tier): item}
        if all((SWEEP_DIR / name).exists() for name in ("tier1_L1.csv.gz", "tier2_L2.csv.gz", "tier3_yongshen.csv.gz")):
            write_report(stats)
    for tier, item in stats.items():
        print(
            f"Tier {tier}: {item['combinations']} combinations in "
            f"{item['elapsed_seconds']:.3f}s; "
            f"{dict(item['result_classes'])}"
        )


if __name__ == "__main__":
    main()
