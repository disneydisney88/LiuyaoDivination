"""Render and verify TASK_CODEX_26 user-visible text snapshots.

The text renderer is intentionally presentation-oriented: it consumes the
same deterministic chart, relation, L3, narration, and multi-track functions
that back the Streamlit pages, but never serializes their internal objects.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.narrate import narrate, narrate_flying_hidden, narrate_hidden  # noqa: E402
from engine.pipeline import build_case_state  # noqa: E402
from engine.semantics import load_decision_table, semantic_for_condition  # noqa: E402
from engine.text_guard import find_forbidden_terms  # noqa: E402
from engine.yongshen import (  # noqa: E402
    LINE_POSITION_OPTIONS,
    SIX_RELATIVE_OPTIONS,
    analyze_yongshen,
    candidate_options,
)


SNAPSHOT_DIR = ROOT / "snapshots"
CASE_DIR = SNAPSHOT_DIR / "cases"
GOLDEN_DIR = SNAPSHOT_DIR / "golden"
CHECKSUMS_PATH = SNAPSHOT_DIR / "CHECKSUMS.txt"
CONFIRMATION = "REGENERATE TEXT SNAPSHOT GOLDEN"
TABLE_PATHS = (
    ROOT / "data" / "decision_tables" / "C1_chong_san.json",
    ROOT / "data" / "decision_tables" / "C15_dongjing_axis.json",
    ROOT / "data" / "decision_tables" / "K_kongwang_effect.json",
    ROOT / "data" / "decision_tables" / "Y_yuanshen_jishen.json",
    ROOT / "data" / "decision_tables" / "A_yingqi.json",
    ROOT / "data" / "decision_tables" / "M1_mujue_source.json",
    ROOT / "data" / "decision_tables" / "M2_suiguirumu.json",
    ROOT / "data" / "decision_tables" / "M3_suimu_wangshuai.json",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.strip()


def pending_item_count() -> int:
    spec = (ROOT / "SPEC_LIUYAO_v0.2.md").read_text(encoding="utf-8")
    match = re.search(r"待核清單項數：.*?本輪\s+(\d+)\s+項", spec)
    if not match:
        raise ValueError("cannot determine §11.1 pending-item count")
    return int(match.group(1))


def load_cases() -> list[dict[str, Any]]:
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(CASE_DIR.glob("*.json"))]
    if len(cases) != 12:
        raise ValueError("TASK_CODEX_26 requires exactly twelve snapshot cases")
    ids = [case.get("case_id") for case in cases]
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("snapshot case ids must be non-empty and unique")
    for case in cases:
        if len(case.get("lines", [])) != 6 or any(value not in (0, 1) for value in case["lines"]):
            raise ValueError("snapshot case lines must be six yin/yang values")
        datetime.fromisoformat(case["cast_datetime"])
    return cases


def state_for_definition(case: dict[str, Any]) -> dict[str, Any]:
    return build_case_state(
        lines=case["lines"], cast_datetime=case["cast_datetime"],
        moving_positions=case.get("moving_positions", []),
    )


def _state_text(state: dict[str, Any]) -> str:
    return "；".join((
        "旺衰：{}".format(state["seasonal_state"]),
        "旬空：{}".format("旬空" if state["empty"] else "非旬空"),
        "月破：{}".format("月破" if state["month_break"] else "非月破"),
        "日辰關係：{}".format("、".join(state["day_relations"]) or "無"),
        "動靜：{}".format(state["motion"]),
    ))


def _candidate_text(candidate: dict[str, Any]) -> str:
    position = candidate["position"]
    hidden = "（伏神）" if candidate.get("hidden") else ""
    role = " {}".format(candidate["role"]) if candidate.get("role") else ""
    return "第 {} 爻 {}{}{}{}".format(
        position, candidate["six_relative"], candidate["branch"], candidate["element"], role + hidden,
    )


def _four_god_text(name: str, rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["{}：無候選。".format(name)]
    lines = ["{}：".format(name)]
    for row in rows:
        state = row["state"]
        marker = "；世" if row.get("is_shi") else "；應" if row.get("is_ying") else ""
        lines.append("- {}；{}{}".format(_candidate_text(row), _state_text(state), marker))
    return lines


def render_board(case: dict[str, Any], state: dict[str, Any]) -> str:
    chart, calendar, relations = state["chart"], state["calendar"], state["relations"]
    relation_by_position = {row["position"]: row for row in relations["lines"]}
    break_branch = relations["month_break_branch"]
    break_positions = relations["month_break_positions"]
    break_text = (
        "{}（第{}爻）".format(break_branch, "、".join(map(str, break_positions)))
        if break_positions else "{}（本卦無{}爻）".format(break_branch, break_branch)
    )
    lines = [
        "盤面",
        "{} · {}宮 · {}".format(chart["name"], chart["palace"], chart["palace_element"]),
        "世：{}　應：{}　起卦時刻：{}".format(chart["shi"], chart["ying"], case["cast_datetime"]),
        "年柱：{}　月建：{}　日辰：{}　旬空：{}　月破：{}".format(
            calendar["year_ganzhi"], calendar["month_ganzhi"], calendar["day_ganzhi"],
            "、".join(relations["empty_branches"]), break_text,
        ),
        "六爻表：",
    ]
    for row in reversed(chart["lines_detail"]):
        relation = relation_by_position[row["position"]]
        role = "世" if row["shi"] else "應" if row["ying"] else ""
        changed = "動" if row["position"] in case.get("moving_positions", []) else "靜"
        lines.append(
            "第 {} 爻：{} {}{} {}；{}；世應：{}；動變：{}".format(
                row["position"], "陽" if case["lines"][row["position"] - 1] else "陰",
                row["branch"], row["element"], row["six_relative"], _state_text(relation), role or "無", changed,
            )
        )
    if chart["hidden"]:
        lines.append("伏神／飛神：")
        for item in narrate_hidden(chart["hidden"]):
            lines.append("- {} 規則：{}；伏神能否為用仍待 R-L1-08b 核實。".format(item["text"], item["rule_id"]))
    else:
        lines.append("本卦六親俱現，沒有伏神記錄。")
    lines.append("逐爻推導：")
    for row in reversed(chart["lines_detail"]):
        output = narrate(semantics={"line": row["position"], "hidden": chart["hidden"], "tracks": {}}, relations=relations)
        lines.append("第 {} 爻 {}{}：".format(row["position"], row["branch"], row["element"]))
        lines.extend("- 第 {} 步：{}".format(step["step"], step["text"]) for step in output["derivation"])
    lines.append("六神未實作（R-L1-07 原典待核）；本頁不填入通行說法。")
    return "\n".join(lines)


def _analysis_text(analysis: dict[str, Any]) -> list[str]:
    if analysis["status"] == "pending_selection":
        lines = ["候選未由使用者指定；四神推導暫不執行。"]
        lines.extend("- {}".format(_candidate_text(item)) for item in analysis["candidates"])
        return lines
    selected = analysis["selected"]
    lines = ["已指定用神：{}；{}".format(_candidate_text(selected), _state_text(analysis["own_state"]))]
    for title, rows in (("元神", analysis["yuan_shen"]), ("忌神", analysis["ji_shen"]), ("仇神", analysis["chou_shen"])):
        lines.extend(_four_god_text(title, rows))
    relation = analysis.get("flying_hidden_relation")
    if relation:
        lines.append("飛伏關係：{} —— 屬《易冒》飛伏五態之「{}」。".format(
            narrate_flying_hidden(relation)["text"], relation["doctrinal_label"],
        ))
        lines.append("原文：{}；出處：{}。{}；其餘各書：未採集。".format(
            relation["original"], relation["source_locator"], relation["doctrinal_status"],
        ))
    decision = analysis["decision_table"]
    lines.append("格位判定：")
    for table_id in ("C1", "C15", "K"):
        value = decision.get(table_id)
        lines.append("- {}：{}".format(table_id, value or "此爻不觸發任何條件"))
    a_conditions = decision.get("A") or []
    display_a = [condition.replace("用神安靜", "用神靜態") for condition in a_conditions]
    lines.append("- A（應期候選）：{}".format("、".join(display_a) if display_a else "此爻不觸發任何應期候選條件"))
    if a_conditions:
        a_table = load_decision_table(ROOT / "data" / "decision_tables" / "A_yingqi.json")
        for condition in a_conditions:
            result = semantic_for_condition(line=selected["position"], condition=condition,
                                            hidden=analysis.get("hidden", []), table=a_table)
            for book, track in result["tracks"].items():
                if track.get("status") == "addressed":
                    partial = "（部分對應 —— {}）".format(track.get("partial_note")) if track.get("match_quality") == "partial" else ""
                    lines.append("  {}：{}{}；候選規則：{}".format(book, track.get("verdict"), partial, track.get("candidate_rule", "未提供")))
    for table_id in ("M1", "M2", "M3"):
        lines.append("- {}：未接入機械層（P-064）；此訊息不等於此爻沒有該狀況。".format(table_id))
    y_locator = decision["Y"]
    lines.append("- Y（元神／忌神狀態）：")
    for item in y_locator["locations"]:
        matches = "、".join(item["matches"]) if item["matches"] else "未命中現有機械格位"
        lines.append("  {} 第 {} 爻 {}{}：{}。".format(
            item["role"], item["position"], item["branch"], item["element"], matches,
        ))
    lines.extend("- {}".format(gap["message"]) for gap in y_locator["implementation_gaps"])
    lines.append("- {}".format(y_locator["chou_shen_note"]))
    return lines


def render_yongshen(case: dict[str, Any], state: dict[str, Any]) -> str:
    del case
    lines = [
        "用神",
        "兩組選擇各自平權呈現；工具不預選、不建議、不排序、不評分。",
        "按六親選與按爻位選之所有可見選項：",
    ]
    for choice in SIX_RELATIVE_OPTIONS + LINE_POSITION_OPTIONS:
        options = candidate_options(state["chart"], choice)
        lines.append("{}：".format(choice))
        if not options:
            lines.append("- 本卦未見可列候選。")
            continue
        if len(options) > 1 or all(item.get("hidden") for item in options):
            lines.append("- 候選須由使用者指定；不作自動取捨。")
        for option in options:
            lines.append("- 人手選擇 {}：".format(_candidate_text(option)))
            lines.extend("  {}".format(value) for value in _analysis_text(
                analyze_yongshen(state, choice, option["candidate_id"]),
            ))
        if len(options) > 1:
            lines.append("- 未指定候選時：")
            lines.extend("  {}".format(value) for value in _analysis_text(analyze_yongshen(state, choice)))
    return "\n".join(lines)


def _track_text(track: dict[str, Any], rendered: dict[str, Any]) -> list[str]:
    lines = ["- {}：{}".format(rendered["book"], rendered["verdict_plain"])]
    if rendered.get("implication"):
        lines.append("  說明：{}".format(rendered["implication"]))
    lines.append("  框架：{}".format(track.get("framework") or "未提供"))
    if rendered.get("source_locator"):
        lines.append("  出處：{}".format(rendered["source_locator"]))
    if rendered.get("original"):
        lines.append("  原文：{}".format(rendered["original"]))
    for key, label in (("verdict_note", "判語註記"), ("search_note", "檢索註記"), ("axis_note", "軸向註記"), ("term_note", "術語註記")):
        if rendered.get(key):
            lines.append("  {}：{}".format(label, rendered[key]))
    if track.get("collection_status"):
        lines.append("  採集狀態：{}".format(track["collection_status"]))
    return lines


def render_tracks(case: dict[str, Any], state: dict[str, Any]) -> str:
    lines = ["多軌", "按資料狀態分組；不作跨軌裁決、多數決或加權。"]
    focus_options = candidate_options(state["chart"], case["focus_choice"])
    focus_line = focus_options[0]["position"] if focus_options else 1
    for path in TABLE_PATHS:
        table = load_decision_table(path)
        lines.extend(("", "{}：{}".format(table["table_id"], table.get("title", "多軌表")), table.get("table_note", "")))
        for row in table["rows"]:
            semantics = semantic_for_condition(
                line=focus_line, condition=row["condition"], hidden=state["chart"]["hidden"], table=table,
            )
            rendered = narrate(semantics=semantics, relations=state["relations"])
            rendered_tracks = {item["book"]: item for item in rendered["tracks"]}
            lines.append("{}　{}".format(semantics["row_id"], row["condition"]))
            lines.append("覆蓋率：{}".format(semantics["coverage_label"]))
            for book, track in semantics["tracks"].items():
                lines.extend(_track_text(track, rendered_tracks[book]))
    return "\n".join(lines)


def render_plain_derivation(state: dict[str, Any]) -> str:
    lines = ["白話推導"]
    for row in state["chart"]["lines_detail"]:
        result = narrate(
            semantics={"line": row["position"], "hidden": state["chart"]["hidden"], "tracks": {}},
            relations=state["relations"],
        )
        lines.append("{}".format(result["header"]))
        lines.extend("- 第 {} 步：{}".format(step["step"], step["text"]) for step in result["derivation"])
    return "\n".join(lines)


def render_sections(case: dict[str, Any]) -> dict[str, str]:
    state = state_for_definition(case)
    return {
        "board": render_board(case, state),
        "yongshen": render_yongshen(case, state),
        "tracks": render_tracks(case, state),
        "derivation": render_plain_derivation(state),
    }


def render_snapshot_body(case: dict[str, Any]) -> str:
    sections = render_sections(case)
    return "\n\n".join((
        "=== 盤面 ===\n" + sections["board"],
        "=== 用神（逐一六親 × 逐一爻位）===\n" + sections["yongshen"],
        "=== 多軌（逐表 × 逐格）===\n" + sections["tracks"],
        "=== 白話推導 ===\n" + sections["derivation"],
    )) + "\n"


def mechanical_text(case: dict[str, Any]) -> str:
    """Return only sections to which the mechanics blacklist applies."""
    sections = render_sections(case)
    return "\n".join((sections["board"], sections["yongshen"], sections["derivation"]))


def _header(case: dict[str, Any]) -> str:
    return "\n".join((
        "# TASK_CODEX_26 text snapshot",
        "# case_id={}".format(case["case_id"]),
        "# generated_commit={}".format(_git("rev-parse", "--short", "HEAD")),
        "# pending_items={}".format(pending_item_count()),
        "# status=text_presentation_baseline",
        "---",
        "",
    ))


def render_snapshot(case: dict[str, Any]) -> str:
    return _header(case) + render_snapshot_body(case)


def _body(value: str) -> str:
    marker = "---\n"
    if marker not in value:
        raise ValueError("snapshot lacks metadata separator")
    return value.split(marker, 1)[1]


def snapshot_path(case: dict[str, Any]) -> Path:
    return GOLDEN_DIR / "{}.txt".format(case["case_id"])


def compare_golden() -> list[str]:
    mismatches = []
    for case in load_cases():
        path = snapshot_path(case)
        if not path.exists():
            mismatches.append("{}: golden is missing".format(case["case_id"]))
            continue
        expected = _body(path.read_text(encoding="utf-8"))
        actual = render_snapshot_body(case)
        if expected != actual:
            diff = list(difflib.unified_diff(
                expected.splitlines(), actual.splitlines(), fromfile="golden", tofile="current", lineterm="",
            ))[:50]
            mismatches.append("{}:\n{}\n差異可能是修復，亦可能是回歸，須人手判斷。".format(
                case["case_id"], "\n".join(diff),
            ))
    return mismatches


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regenerate_golden() -> None:
    print("Type exactly: {}".format(CONFIRMATION))
    if input("> ").strip() != CONFIRMATION:
        raise SystemExit("Text snapshot regeneration cancelled: confirmation did not match.")
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for case in load_cases():
        snapshot_path(case).write_text(render_snapshot(case), encoding="utf-8")
    checksums = [
        "TASK_CODEX_26 text snapshots",
        "baseline_commit={}".format(_git("rev-parse", "--short", "HEAD")),
        "pending_items={}".format(pending_item_count()),
        "status=text_presentation_baseline",
        "",
    ]
    checksums.extend("{}  {}".format(_sha256(snapshot_path(case)), snapshot_path(case).name) for case in load_cases())
    CHECKSUMS_PATH.write_text("\n".join(checksums) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--regenerate-golden", action="store_true")
    args = parser.parse_args()
    if args.regenerate_golden:
        regenerate_golden()
        return
    mismatches = compare_golden()
    if mismatches:
        raise SystemExit("\n\n".join(mismatches))
    print("12 text snapshots match their golden bodies.")


if __name__ == "__main__":
    main()
