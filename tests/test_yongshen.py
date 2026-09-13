import json
from datetime import datetime

from engine.yongshen import analyze_yongshen, candidate_options
from streamlit.testing.v1 import AppTest
from ui_contracts import make_case, state_for_case


def sample_state():
    case = make_case(
        coin_counts=[2, 1, 2, 2, 1, 2],
        cast_datetime=datetime(2026, 9, 13, 15, 49),
        question_text="", background_text="", is_proxy=False,
    )
    return state_for_case(case)


def selected(state, choice):
    options = candidate_options(state["chart"], choice)
    assert options, f"test fixture has no candidate for {choice}"
    return analyze_yongshen(state, choice, options[0]["candidate_id"])


def test_same_case_different_yongshen_outputs_are_not_equal():
    state = sample_state()
    outputs = [selected(state, choice) for choice in ("父母", "官鬼", "妻財", "子孫", "兄弟", "世應")]
    signatures = {json.dumps(output, ensure_ascii=False, sort_keys=True) for output in outputs}
    assert len(signatures) == 6


def test_caicai_yongshen_derives_yuanshen_and_jishen_with_positions():
    output = selected(sample_state(), "妻財")
    assert output["yuan_shen"]
    assert output["ji_shen"]
    assert all(item["six_relative"] == "子孫" and item["position"] for item in output["yuan_shen"])
    assert all(item["six_relative"] == "兄弟" and item["position"] for item in output["ji_shen"])
    assert all(item["position"] for item in output["chou_shen"])


def test_selected_yongshen_candidate_has_marker_and_mechanical_state():
    output = selected(sample_state(), "妻財")
    assert output["selected"]["candidate_id"]
    marked_lines = [line for line in output["lines"] if line["is_yongshen"]]
    marked_hidden = [item for item in output["hidden"] if item["is_yongshen"]]
    assert len(marked_lines) + len(marked_hidden) == 1
    assert output["own_state"]["seasonal_state"] in {"旺", "相", "休", "囚", "死"}
    assert len(output["yuan_shen_checks"][0]["checks"]) == 6


def test_candidate_listing_preserves_duplicate_and_hidden_choices():
    state = sample_state()
    for choice in ("父母", "官鬼", "妻財", "子孫", "兄弟", "世應"):
        options = candidate_options(state["chart"], choice)
        assert all(item["candidate_id"] for item in options)
        if len(options) > 1:
            assert len({item["candidate_id"] for item in options}) == len(options)


def test_yongshen_page_renders_recalculated_output():
    case = make_case(
        coin_counts=[2, 1, 2, 2, 1, 2],
        cast_datetime=datetime(2026, 9, 13, 15, 49),
        question_text="", background_text="", is_proxy=False,
    )
    state = state_for_case(case)
    case["yongshen_selected"] = ["妻財"]
    case["yongshen_candidate_selections"] = {
        "妻財": candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    }
    app = AppTest.from_file("pages/yongshen.py")
    app.session_state["current_case"] = case
    app.session_state["cases"] = [case]
    app.run(timeout=10)
    assert not app.exception
    text = "\n".join(item.value for group in (app.caption, app.markdown) for item in group)
    assert "元神" in text or "忌神" in text
