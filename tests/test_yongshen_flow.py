import json
from datetime import datetime

from streamlit.testing.v1 import AppTest

from engine.pipeline import build_case_state
from engine.yongshen import (
    LINE_POSITION_OPTIONS,
    SIX_RELATIVE_OPTIONS,
    analyze_yongshen,
    candidate_options,
)
from ui_contracts import make_case, state_for_case


def example_state():
    return build_case_state(
        lines=[1, 0, 1, 0, 1, 0],
        cast_datetime=datetime(2026, 9, 14, 13, 30),
        moving_positions=[3],
    )


def example_case():
    return make_case(
        coin_counts=[1, 2, 3, 2, 1, 2],
        cast_datetime=datetime(2026, 9, 14, 13, 30),
        question_text="", background_text="", is_proxy=False,
    )


def _all_keys_and_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _all_keys_and_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_keys_and_values(item)
    else:
        yield str(value)


def test_yongshen_page_has_separate_relative_and_line_choice_groups():
    app = AppTest.from_file("pages/yongshen.py")
    app.session_state["current_case"] = example_case()
    app.session_state["cases"] = [app.session_state["current_case"]]
    app.run(timeout=10)
    assert not app.exception
    labels = [widget.label for widget in app.pills]
    assert "按六親選" in labels and "按爻位選" in labels
    assert len(app.pills[labels.index("按六親選")].options) == 5
    assert len(app.pills[labels.index("按爻位選")].options) == 8


def test_two_occurrences_are_pending_and_have_no_preference_fields():
    state = example_state()
    output = analyze_yongshen(state, "官鬼")
    assert output["status"] == "pending_selection"
    assert [item["position"] for item in output["candidates"]] == [2, 5]
    forbidden = {"default", "recommended", "selected", "suggested"}
    assert not any(key in forbidden for key in output)
    assert all(not forbidden.intersection(item) for item in output["candidates"])


def test_two_occurrences_do_not_run_four_god_recalculation_before_selection():
    output = analyze_yongshen(example_state(), "官鬼")
    assert output["status"] == "pending_selection"
    assert not any(key in output for key in ("yuan_shen", "ji_shen", "chou_shen"))


def test_absent_relative_requires_explicit_hidden_choice():
    state = example_state()
    output = analyze_yongshen(state, "妻財")
    assert output["status"] == "pending_selection"
    assert output["hidden_available"] is True
    hidden_id = output["candidates"][0]["candidate_id"]
    chosen = analyze_yongshen(state, "妻財", hidden_id)
    assert chosen["status"] == "selected"
    assert chosen["hidden_selected"] is True
    assert chosen["selected"]["position"] == 3


def test_four_god_entries_have_eight_mechanical_fields():
    state = example_state()
    candidate_id = candidate_options(state["chart"], "父母")[0]["candidate_id"]
    output = analyze_yongshen(state, "父母", candidate_id)
    required = {"position", "branch", "element", "six_relative", "seasonal_state", "empty", "month_break", "motion"}
    for role in ("yuan_shen", "ji_shen", "chou_shen"):
        assert output[role]
        assert all(required <= set(item["state"]) for item in output[role])
    assert required <= set(output["own_state"])


def test_flying_line_is_retained_and_marked_when_hidden_yongshen_is_selected():
    state = example_state()
    hidden_id = candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    output = analyze_yongshen(state, "妻財", hidden_id)
    flying = [item for item in output["ji_shen"] if item["is_flying_of_yongshen"]]
    assert flying and flying[0]["position"] == 3


def test_hidden_yongshen_has_yimao_only_flying_hidden_relation():
    state = example_state()
    hidden_id = candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    relation = analyze_yongshen(state, "妻財", hidden_id)["flying_hidden_relation"]
    assert relation["source_book"] == "易冒"
    assert relation["doctrinal_status"] != "通則"
    assert relation["doctrinal_label"] == "飛克伏者滅"
    assert relation["source_locator"] == "類總章第四十一 686"
    assert relation["other_books_status"] == "not_collected"


def test_l3_contains_no_doctrinal_strength_judgement_fields():
    state = example_state()
    candidate_id = candidate_options(state["chart"], "父母")[0]["candidate_id"]
    output = analyze_yongshen(state, "父母", candidate_id)
    text = "\n".join(_all_keys_and_values(output))
    assert "元神無力" not in text
    assert "元神有力" not in text
    assert "忌神能剋" not in text
    assert all(check["status"] == "deferred_to_multi_track" for item in output["yuan_shen_checks"] for check in item["checks"])


def test_tracks_defaults_to_the_selected_yongshen_position():
    case = example_case()
    state = state_for_case(case)
    hidden_id = candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    case["yongshen_selected"] = ["妻財"]
    case["yongshen_candidate_selections"] = {"妻財": hidden_id}
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = case
    app.run(timeout=10)
    assert not app.exception
    assert app.selectbox[1].value == 3 or app.selectbox[0].value == 3


def test_tracks_exposes_coverage_gap_when_no_condition_is_triggered():
    case = example_case()
    state = state_for_case(case)
    hidden_id = candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    case["yongshen_selected"] = ["妻財"]
    case["yongshen_candidate_selections"] = {"妻財": hidden_id}
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = case
    app.run(timeout=10)
    assert not app.exception
    text = "\n".join(item.value for group in (app.caption, app.markdown, app.subheader) for item in group)
    assert "覆蓋缺口" in text or "尚未有對應決策表" in text


def test_acceptance_case_has_nonduplicated_c1_c15_lines_and_flying_relation():
    case = example_case()
    state = state_for_case(case)
    hidden_id = candidate_options(state["chart"], "妻財")[0]["candidate_id"]
    case["yongshen_selected"] = ["妻財"]
    case["yongshen_candidate_selections"] = {"妻財": hidden_id}
    app = AppTest.from_file("pages/yongshen.py")
    app.session_state["current_case"] = case
    app.session_state["cases"] = [case]
    app.run(timeout=10)
    assert not app.exception
    text = "\n".join(item.value for group in (app.caption, app.markdown, app.subheader) for item in group)
    assert "飛伏關係" in text
    assert "格位判定" in text
    assert text.count("C1（衰旺軸）") == 1
    assert text.count("C15（動靜軸）") == 1
