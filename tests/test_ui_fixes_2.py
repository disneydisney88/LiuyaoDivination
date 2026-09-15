"""TASK_CODEX_24 regressions: cross-page selection, four gods, Y, and sweep."""
from __future__ import annotations

from datetime import datetime

from streamlit.testing.v1 import AppTest

from engine.relations import BRANCH_ELEMENT, build_relation_graph
from engine.semantics import chong_source_for_line, framework_for_book_id, semantic_for_condition
from engine.yongshen import analyze_yongshen, candidate_options
from tools.sweep import _tier3_time_samples
from ui_contracts import make_case, state_for_case


def acceptance_case():
    return make_case(
        coin_counts=[1, 2, 2, 2, 3, 3],
        cast_datetime=datetime(2026, 9, 15, 22, 26),
        question_text="", background_text="", is_proxy=False,
    )


def acceptance_state():
    return state_for_case(acceptance_case())


def selected(state, choice, candidate_id):
    return analyze_yongshen(state, choice, candidate_id)


def test_tracks_uses_cross_page_session_selection_as_its_default_line():
    case = acceptance_case()
    state = state_for_case(case)
    sixth = next(item for item in candidate_options(state["chart"], "兄弟") if item["position"] == 6)
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = case
    app.session_state["active_yongshen_by_case"] = {
        case["case_id"]: {"choices": ["兄弟"], "candidate_selections": {"兄弟": sixth["candidate_id"]}}
    }
    app.run(timeout=10)
    assert not app.exception
    assert any(widget.value == 6 for widget in app.selectbox)


def test_yongshen_page_writes_manual_lock_to_cross_page_session_state():
    case = acceptance_case()
    app = AppTest.from_file("pages/yongshen.py")
    app.session_state["current_case"] = case
    app.session_state["cases"] = [case]
    app.run(timeout=10)
    app.pills[0].set_value(["兄弟"]).run(timeout=10)
    app.radio[0].set_value(app.radio[0].options[1]).run(timeout=10)
    saved = app.session_state["active_yongshen_by_case"][case["case_id"]]
    assert saved == {"choices": ["兄弟"], "candidate_selections": {"兄弟": "visible:6"}}


def test_tracks_shows_no_selection_only_when_session_has_no_yongshen():
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = acceptance_case()
    app.run(timeout=10)
    text = "\n".join(item.value for group in (app.caption, app.markdown) for item in group)
    assert "未選用神" in text


def test_six_ingested_frameworks_are_data_backed_chinese_labels():
    expected = {
        "yimao": "看用神十八法",
        "zengshan": "二值判定 + 條件枚舉",
        "buzhengzong": "真假二分",
        "buzhequanshu": "按事類編排、無專章",
        "huangjin_ce": "賦體對句",
        "huozhulin": "主／輔二位，事類定身份、旺衰定效力",
    }
    assert {book_id: framework_for_book_id(book_id) for book_id in expected} == expected
    tracks = semantic_for_condition(line=6, condition="旺相之爻遇沖")["tracks"]
    assert all(track["framework"] not in {None, "未提供"} for track in tracks.values() if track["book_id"] in expected)


def test_four_gods_are_deduplicated_and_retain_shi_ying_annotations():
    state = acceptance_state()
    brother_six = next(item for item in candidate_options(state["chart"], "兄弟") if item["position"] == 6)
    output = selected(state, "兄弟", brother_six["candidate_id"])
    assert [item["position"] for item in output["chou_shen"]] == [3, 4]
    assert next(item for item in output["chou_shen"] if item["position"] == 3)["is_shi"] is True

    third = candidate_options(state["chart"], "三爻")[0]
    output = selected(state, "三爻", third["candidate_id"])
    assert [item["position"] for item in output["ji_shen"]] == [2, 6]
    assert next(item for item in output["ji_shen"] if item["position"] == 6)["is_ying"] is True
    for role in ("yuan_shen", "ji_shen", "chou_shen"):
        positions = [item["position"] for item in output[role]]
        assert len(positions) == len(set(positions))


def test_y_locator_handles_visible_and_hidden_four_gods_without_effects():
    state = acceptance_state()
    brother_six = next(item for item in candidate_options(state["chart"], "兄弟") if item["position"] == 6)
    output = selected(state, "兄弟", brother_six["candidate_id"])
    locator = output["decision_table"]["Y"]
    assert locator["located"] is True
    locations = {(item["role"], item["position"]): item for item in locator["locations"]}
    assert locations[("元神", 1)]["matches"] == ["Y-R1"]
    assert locations[("忌神", 3)]["hidden"] is True
    assert locations[("忌神", 3)]["matches"] == ["Y-R7"]
    assert locator["chou_shen_note"] == "Y 表無仇神格位（P-057）"


def test_tracks_renders_each_automatically_located_y_row():
    case = acceptance_case()
    state = state_for_case(case)
    sixth = next(item for item in candidate_options(state["chart"], "兄弟") if item["position"] == 6)
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = case
    app.session_state["active_yongshen_by_case"] = {
        case["case_id"]: {"choices": ["兄弟"], "candidate_selections": {"兄弟": sixth["candidate_id"]}}
    }
    app.run(timeout=10)
    app.selectbox[0].set_value("Y：元神／忌神狀態材料").run(timeout=10)
    assert not app.exception
    text = "\n".join(item.value for group in (app.caption, app.markdown, app.subheader) for item in group)
    assert "Y-R1" in text and "Y-R7" in text and "Y 表無仇神格位（P-057）" in text


def test_independent_tier3_time_sampling_and_all_chong_sources_are_representable():
    samples = _tier3_time_samples()
    assert len(samples) == 24
    assert len({month for month, _ in samples}) == 12
    assert any(month != day[1] for month, day in samples)

    def source(month, day, target, moving=()):
        rows = [
            {"position": 1, "branch": target, "element": BRANCH_ELEMENT[target], "six_relative": "兄弟"},
            {"position": 2, "branch": "午", "element": "火", "six_relative": "子孫"},
        ]
        relation = build_relation_graph(
            line_rows=rows, month_element=BRANCH_ELEMENT[month], month_branch=month,
            day_stem="甲" if "子寅辰午申戌".find(day) >= 0 else "乙",
            day_branch=day, moving_positions=moving, changing_positions=moving,
        )
        return chong_source_for_line(relation, 1)

    assert source("酉", "辰", "卯") == "month"
    assert source("子", "酉", "卯") == "day"
    assert source("酉", "酉", "卯") == "multiple"
    assert source("子", "子", "子", moving=(2,)) == "moving_line"
