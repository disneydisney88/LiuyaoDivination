from datetime import datetime, timedelta, timezone

from streamlit.testing.v1 import AppTest

from engine.calendar import sexagenary_for_datetime, solar_term_utc
from engine.narrate import MISSING_TEXT, narrate
from engine.semantics import infer_condition, semantic_for_condition
from ui_contracts import make_case, state_for_case


def complete_case():
    case = make_case(
        coin_counts=[2, 1, 2, 2, 1, 2],  # 坎為水，由初爻起
        cast_datetime=datetime(2026, 9, 13, 15, 49),
        question_text="", background_text="", is_proxy=False,
    )
    case["yongshen_selected"] = ["父母"]  # 唯一對應第 4 爻申金
    return case


def test_sexagenary_reference_day_and_solar_term_year_boundary():
    assert sexagenary_for_datetime(datetime(2000, 1, 7, 12, tzinfo=timezone.utc))["day_ganzhi"] == "甲子"
    lichun = solar_term_utc(2026, 2)
    before = sexagenary_for_datetime(lichun - timedelta(minutes=1))
    after = sexagenary_for_datetime(lichun + timedelta(minutes=1))
    assert (before["year_ganzhi"], before["month_branch"]) == ("乙巳", "丑")
    assert (after["year_ganzhi"], after["month_ganzhi"]) == ("丙午", "庚寅")


def test_complete_case_connects_calendar_relations_narrative_and_five_tracks():
    case = complete_case()
    state = state_for_case(case)
    relations = state["relations"]

    assert case["hexagram_name"] == "坎為水"
    assert (case["year_ganzhi"], case["month_ganzhi"], case["day_ganzhi"]) == (
        "丙午", "丁酉", "庚寅",
    )
    assert case["xunkong"] == ["午", "未"]
    assert case["month_break_branch"] == "卯"
    assert relations["month_break_branch"] == "卯"
    assert relations["month_break_positions"] == []

    for line in range(1, 7):
        output = narrate(
            semantics={"line": line, "hidden": state["chart"]["hidden"], "tracks": {}},
            relations=relations,
        )
        assert output["template_missing"] is False
        assert output["derivation"]
        assert all(step["text"] != MISSING_TEXT for step in output["derivation"])

    assert infer_condition(table_id="C1", relation_result=relations, line=4) == "旺相之爻遇沖"
    semantics = semantic_for_condition(line=4, condition="旺相之爻遇沖")
    narrative = narrate(semantics=semantics, relations=relations)
    expressed = [
        item for item in narrative["tracks"]
        if item["status"] in {"addressed", "different_axis"}
    ]
    assert semantics["row_title"] == "三家判不散，一家判損"
    assert {item["book"] for item in expressed} == {
        "易冒", "增刪卜易", "卜筮正宗", "火珠林", "黃金策", "卜筮全書",
    }
    assert all(item["original"] and item["source_locator"] for item in expressed)


def test_streamlit_board_and_tracks_render_the_connected_case():
    case = complete_case()

    board = AppTest.from_file("pages/board.py")
    board.session_state["current_case"] = case
    board.session_state["current_relation_state"] = {}
    board.run(timeout=10)
    assert not board.exception
    assert len(board.expander) == 6
    assert not board.warning
    board_text = "\n".join(
        item.value for group in (board.caption, board.markdown) for item in group
    )
    assert "月建：丁酉" in board_text
    assert "日辰：庚寅" in board_text
    assert "旬空：午、未" in board_text
    assert "月破：卯（本卦無卯爻）" in board_text
    assert "待接入" not in board_text and "待 L2" not in board_text
    assert MISSING_TEXT not in board_text

    tracks = AppTest.from_file("pages/tracks.py")
    tracks.session_state["current_case"] = case
    tracks.session_state["current_relation_state"] = {}
    tracks.run(timeout=10)
    assert not tracks.exception
    assert any(item.label == "手動覆寫表格位" for item in tracks.toggle)
    assert any(item.value == "三家判不散，一家判損" for item in tracks.subheader)
    assert {"易冒", "增刪卜易", "卜筮正宗", "卜筮全書"} <= {
        item.label for item in tracks.expander
    }
    tracks_text = "\n".join(
        item.value for group in (tracks.caption, tracks.markdown) for item in group
    )
    assert "**黃金策**" in tracks_text
    assert "一旺一衰，则衰散而旺动" in tracks_text
    assert "大凡旺处逢冲则损" in tracks_text
    assert "現有 doctrinal 資料未提供逐字原文" not in tracks_text
