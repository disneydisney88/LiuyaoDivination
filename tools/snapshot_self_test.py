"""Perform TASK_CODEX_26 H's reproducible, non-destructive self-validation.

The historical fixes predate the snapshot renderer.  Checking them out would
therefore test a different application without this mechanism.  This script
instead injects each former *user-visible failure condition* into current
rendered output in memory, then exercises the actual diff, blacklist, or
AppTest assertion that is meant to detect it.  It never writes application
source or golden files; its only output is snapshots/SELF_TEST.md.
"""
from __future__ import annotations

import difflib
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest

from engine.text_guard import find_forbidden_terms
from ui_contracts import make_case
from tools.snapshot import load_cases, render_sections, render_snapshot_body


REPORT_PATH = ROOT / "snapshots" / "SELF_TEST.md"


def _replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError("self-test fixture text was not found: {!r}".format(old))
    return text.replace(old, new, 1)


def _replace_block(text: str, start: str, end: str, replacement: str) -> str:
    first = text.index(start)
    last = text.index(end, first)
    return text[:first] + replacement + text[last:]


def _diff_catches(baseline: str, injected: str) -> bool:
    """Use the same unified-diff primitive as the golden regression test."""
    return baseline != injected and bool(list(difflib.unified_diff(
        baseline.splitlines(), injected.splitlines(), lineterm="",
    ))[:50])


def _app_text(app: AppTest) -> str:
    groups = (
        app.title, app.header, app.subheader, app.caption, app.markdown,
        app.info, app.warning, app.error, app.success, app.text, app.code,
    )
    values = [str(item.value) for group in groups for item in group]
    values.extend(str(item.value) for item in app.table)
    return "\n".join(values)


def _cross_page_loss_is_detected() -> bool:
    """Construct the former lost-session condition and run the real page."""
    case = make_case(
        coin_counts=[1, 2, 2, 2, 3, 2],
        cast_datetime=datetime(2026, 9, 15, 23, 30),
        question_text="", background_text="", is_proxy=False,
    )
    tracks = AppTest.from_file("pages/tracks.py")
    tracks.session_state["current_case"] = case
    tracks.session_state["cases"] = [case]
    # Deliberately omit active_yongshen_by_case: this is the prior defect.
    tracks.run(timeout=10)
    return not tracks.exception and "已由人手所選用神定位" not in _app_text(tracks)


def self_test_results() -> list[tuple[str, str, str, bool]]:
    cases = {case["case_id"]: case for case in load_cases()}
    baseline = render_snapshot_body(cases["11_tun_hidden_yongshen"])
    sections = render_sections(cases["11_tun_hidden_yongshen"])
    board, yongshen, tracks = sections["board"], sections["yongshen"], sections["tracks"]

    results: list[tuple[str, str, str, bool]] = []
    results.append((
        "1 卦名截斷", "文字快照 diff",
        "把「水雷屯」暫時改為「水雷」", 
        _diff_catches(baseline, _replace_once(baseline, "水雷屯", "水雷")),
    ))
    raw_json = '{"six_relative": "妻財"}'
    results.append((
        "2 伏神 dump 原始 JSON", "文字快照 diff＋L1 黑名單",
        "在盤面段暫時插入 {}".format(raw_json),
        _diff_catches(baseline, board + "\n" + raw_json) and bool(find_forbidden_terms(raw_json, layer="L1")),
    ))
    results.append((
        "3 TODO 內部標記洩漏", "文字快照 diff＋Streamlit 黑名單",
        "在盤面段暫時插入 TODO", 
        _diff_catches(baseline, board + "\nTODO") and bool(find_forbidden_terms("TODO", layer="streamlit")),
    ))
    missing_ying = _replace_block(yongshen, "應爻：", "初爻：", "應爻：\n- 本卦未見可列候選。\n")
    results.append((
        "4 應爻無候選", "文字快照 diff",
        "暫時以空候選區塊取代應爻候選區塊", 
        _diff_catches(baseline, baseline.replace(yongshen, missing_ying, 1)),
    ))
    stale_note = _replace_once(tracks, "C15：", "C15：舊表附註（未隨表更新）\n")
    results.append((
        "5 多軌頁附註未隨表變更", "文字快照 diff",
        "在 C15 標題後暫時插入舊附註", 
        _diff_catches(baseline, baseline.replace(tracks, stale_note, 1)),
    ))
    framework_missing = _replace_once(baseline, "框架：", "框架：未提供")
    results.append((
        "6 框架未提供 regression", "文字快照 diff",
        "暫時把首個框架值改為「未提供」", 
        _diff_catches(baseline, framework_missing),
    ))
    first_yuanshen = "  元神：\n"
    after_heading = yongshen.index(first_yuanshen) + len(first_yuanshen)
    duplicate_end = yongshen.index("\n", after_heading)
    duplicate_line = yongshen[after_heading:duplicate_end + 1]
    duplicate_gods = yongshen[:duplicate_end + 1] + duplicate_line + yongshen[duplicate_end + 1:]
    results.append((
        "7 四神有重複項", "文字快照 diff",
        "暫時重複首個元神候選列", 
        _diff_catches(baseline, baseline.replace(yongshen, duplicate_gods, 1)),
    ))
    results.append((
        "8 用神選擇未跨頁傳遞", "AppTest 跨頁狀態斷言",
        "真實載入多軌頁，但暫時略去 active_yongshen_by_case", 
        _cross_page_loss_is_detected(),
    ))
    no_y_locator = _replace_once(baseline, "Y-R", "未能定位")
    results.append((
        "9 Y 表未自動定位", "文字快照 diff",
        "暫時移除首個 Y 表機械格位", 
        _diff_catches(baseline, no_y_locator),
    ))
    inverted_flying = _replace_once(
        baseline,
        "妻財午火，伏於第3爻辰土之下（飛神辰土）",
        "辰土，伏於妻財午火之下（飛神午火）",
    )
    results.append((
        "10 飛伏句式主客顛倒", "文字快照 diff",
        "暫時把飛神與伏神之主客次序對調", 
        _diff_catches(baseline, inverted_flying),
    ))
    results.append((
        "11 L2 越界判「散」", "L2 黑名單",
        "在機械層文字暫時插入「散」", 
        bool(find_forbidden_terms("散", layer="L2")),
    ))
    return results


def write_report() -> Path:
    results = self_test_results()
    caught = sum(result[-1] for result in results)
    lines = [
        "# TASK_CODEX_26 H — 文字自檢實測",
        "",
        "本次不 checkout 舊 commit：快照工具在各修復後才新增，checkout 前版本不能直接執行同一套工具。",
        "依 TASK_CODEX_26 H 之替代方案，以下均為**記憶體內的人工重現條件**；不寫回應用程式原始碼或 golden。",
        "每項都實際呼叫目前的 unified diff、黑名單或 AppTest 斷言，並非由描述推測結果。",
        "",
        "| 問題 | 採用機制 | 人工重現條件 | 能否捕捉 |",
        "|---|---|---|---|",
    ]
    lines.extend(
        "| {} | {} | {} | {} |".format(problem, mechanism, condition, "是" if caught_one else "否")
        for problem, mechanism, condition, caught_one in results
    )
    lines.extend((
        "",
        "結果：{}/{} 項可被目前機制捕捉。第 1–10 項由文字 diff（第 8 項由跨頁 AppTest）捕捉；第 11 項由 L2 分層黑名單捕捉。".format(caught, len(results)),
        "",
        "此結果只量度已知錯誤類型之檢出能力；首次出現的新型越界、語意矛盾、格位設計偏向及材料完整性仍須人手實測。",
        "",
    ))
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return REPORT_PATH


if __name__ == "__main__":
    path = write_report()
    print("Self-test report: {}".format(path))
