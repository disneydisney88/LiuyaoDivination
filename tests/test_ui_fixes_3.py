"""TASK_CODEX_25 acceptance tests: two-state categories and wording boundaries."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from engine.narrate import narrate, narrate_flying_hidden
from engine.pipeline import build_case_state
from engine.relations import SEASONAL_STATE_CATEGORIES
from engine.yongshen import (
    LINE_POSITION_OPTIONS,
    _flying_hidden_relation,
    analyze_yongshen,
    candidate_options,
)
from tools.generate_data import generate_bagong
from ui_contracts import make_case


ROOT = Path(__file__).resolve().parents[1]
TASK_TIME = datetime(2026, 9, 15, 23, 30)
TASK_LINES = [1, 0, 0, 0, 1, 0]  # 水雷屯；五爻動


def task_state() -> dict:
    return build_case_state(
        lines=TASK_LINES, cast_datetime=TASK_TIME, moving_positions=[5],
    )


def task_case() -> dict:
    return make_case(
        coin_counts=[1, 2, 2, 2, 3, 2], cast_datetime=TASK_TIME,
        question_text="", background_text="", is_proxy=False,
    )


def app_text(app: AppTest) -> str:
    return "\n".join(
        item.value
        for group in (app.caption, app.markdown, app.subheader, app.info, app.warning)
        for item in group
    ) + "\n" + "\n".join(item.label for item in app.expander)


def test_task25_editorial_five_state_mapping_and_table_notes_are_explicit():
    assert SEASONAL_STATE_CATEGORIES == {
        "旺": "旺相", "相": "旺相", "休": "休囚", "囚": "休囚", "死": "休囚",
    }
    required_note = (
        "本表之「旺相」涵蓋旺、相二態；「休囚」涵蓋休、囚、死三態。"
        "五態歸二類為本項目之歸併，依《易冒》688「月建以旺相休囚死之法為主」"
        "及《卜筮全書》5489「當生者旺，所生者相」。"
        "**各家是否於休、囚、死之間再作分別，未採集（P-058）。**"
    )
    for name in ("C1_chong_san.json", "C15_dongjing_axis.json", "K_kongwang_effect.json", "Y_yuanshen_jishen.json"):
        table = json.loads((ROOT / "data" / "decision_tables" / name).read_text(encoding="utf-8"))
        assert required_note in table["table_note"]


def test_task25_five_state_categories_match_y_rows_for_hidden_wife_and_fifth_line():
    state = task_state()
    wife = candidate_options(state["chart"], "妻財")[0]
    wife_output = analyze_yongshen(state, "妻財", wife["candidate_id"])
    wife_locations = {
        (item["role"], item["position"]): item
        for item in wife_output["decision_table"]["Y"]["locations"]
    }
    assert wife_locations[("元神", 2)]["seasonal_state"] == "死"
    assert "Y-R2" in wife_locations[("元神", 2)]["matches"]
    for position in (1, 6):
        assert wife_locations[("忌神", position)]["seasonal_state"] == "相"
        assert "Y-R7" in wife_locations[("忌神", position)]["matches"]

    fifth = candidate_options(state["chart"], "五爻")[0]
    fifth_output = analyze_yongshen(state, "五爻", fifth["candidate_id"])
    fifth_locations = {
        (item["role"], item["position"]): item
        for item in fifth_output["decision_table"]["Y"]["locations"]
    }
    assert fifth_locations[("元神", 3)]["seasonal_state"] == "囚"
    assert "Y-R2" in fifth_locations[("元神", 3)]["matches"]
    assert fifth_locations[("忌神", 2)]["seasonal_state"] == "死"
    assert "Y-R8" in fifth_locations[("忌神", 2)]["matches"]


def test_task25_flying_hidden_templates_keep_the_original_subject_direction():
    examples = (
        ({"flying_branch": "辰", "flying_element": "土", "branch": "寅", "element": "木"}, "伏神寅木 剋 飛神辰土"),
        ({"flying_branch": "午", "flying_element": "火", "branch": "辰", "element": "土"}, "飛神午火 生 伏神辰土"),
        ({"flying_branch": "寅", "flying_element": "木", "branch": "辰", "element": "土"}, "飛神寅木 剋 伏神辰土"),
        ({"flying_branch": "辰", "flying_element": "土", "branch": "午", "element": "火"}, "伏神午火 生 飛神辰土"),
        ({"flying_branch": "辰", "flying_element": "土", "branch": "戌", "element": "土"}, "伏神戌土 與 飛神辰土 比和"),
    )
    for raw, expected in examples:
        relation = _flying_hidden_relation({"hidden": True, **raw})
        assert narrate_flying_hidden(relation)["text"] == expected
        assert "被生" not in expected and "被剋" not in expected

    wife = candidate_options(task_state()["chart"], "妻財")[0]
    relation = _flying_hidden_relation(wife)
    assert narrate_flying_hidden(relation)["text"] == "伏神午火 生 飛神辰土"


def test_task25_l2_motion_and_day_clash_are_kept_mechanical_then_redirected():
    state = task_state()
    fifth = next(row for row in state["relations"]["lines"] if row["position"] == 5)
    assert fifth["motion"] == "動"
    assert "沖" in fifth["day_relations"]
    assert {row["motion"] for row in state["relations"]["lines"]} <= {"動", "靜"}

    narrative = narrate(
        semantics={"line": 5, "hidden": state["chart"]["hidden"], "tracks": {}},
        relations=state["relations"],
    )
    text = "\n".join(step["text"] for step in narrative["derivation"])
    assert "動靜分類：動" in text
    assert "此爻遇日辰沖（機械關係）" in text
    assert "多軌頁 C1／C15" in text
    assert not any(term in text for term in ("散", "暗動", "全動", "真空", "假空", "真破", "假破"))


def test_task25_l1_l2_l3_outputs_do_not_emit_doctrinal_motion_or_empty_labels():
    banned = ("散", "暗動", "全動", "真空", "假空", "真破", "假破")
    for source in generate_bagong():
        state = build_case_state(
            lines=source["lines"], cast_datetime=TASK_TIME, moving_positions=[1, 3, 5],
        )
        l1_l2 = json.dumps(
            {"chart": state["chart"], "relations": state["relations"]}, ensure_ascii=False,
        )
        assert not any(term in l1_l2 for term in banned)
        for choice in LINE_POSITION_OPTIONS:
            l3 = analyze_yongshen(state, choice)
            assert l3["status"] == "selected"
            assert not any(term in json.dumps(l3, ensure_ascii=False) for term in banned)


def test_task25_y_implementation_gaps_are_visible_on_both_y_interfaces():
    case = task_case()
    wife = candidate_options(task_state()["chart"], "妻財")[0]
    selection = {case["case_id"]: {"choices": ["妻財"], "candidate_selections": {"妻財": wife["candidate_id"]}}}

    yongshen = AppTest.from_file("pages/yongshen.py")
    yongshen.session_state["current_case"] = case
    yongshen.session_state["cases"] = [case]
    yongshen.session_state["active_yongshen_by_case"] = selection
    yongshen.run(timeout=10)
    assert not yongshen.exception
    yongshen_text = app_text(yongshen)
    assert "Y-R5（元神動而化退神）、Y-R6（元神入墓）" in yongshen_text
    assert "實作缺口" in yongshen_text

    tracks = AppTest.from_file("pages/tracks.py")
    tracks.session_state["current_case"] = case
    tracks.session_state["active_yongshen_by_case"] = selection
    tracks.run(timeout=10)
    tracks.selectbox[0].set_value("Y：元神／忌神狀態材料").run(timeout=10)
    assert not tracks.exception
    tracks_text = app_text(tracks)
    assert "Y-R5（元神動而化退神）、Y-R6（元神入墓）" in tracks_text
    assert "實作缺口" in tracks_text


def test_task25_board_keeps_month_break_as_a_mechanical_marker():
    board = AppTest.from_file("pages/board.py")
    board.session_state["current_case"] = task_case()
    board.run(timeout=10)
    assert not board.exception
    assert "月破：卯（本卦無卯爻）" in app_text(board)
