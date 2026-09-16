"""TASK_CODEX_26 actual Streamlit page smoke and text-boundary checks."""
from __future__ import annotations

from datetime import datetime

from streamlit.testing.v1 import AppTest

from engine.text_guard import find_forbidden_terms
from engine.yongshen import candidate_options
from ui_contracts import make_case, state_for_case


def sample_case() -> dict:
    return make_case(
        coin_counts=[1, 2, 2, 2, 3, 2], cast_datetime=datetime(2026, 9, 15, 23, 30),
        question_text="", background_text="", is_proxy=False,
    )


def app_text(app: AppTest) -> str:
    groups = (
        app.title, app.header, app.subheader, app.caption, app.markdown, app.info,
        app.warning, app.error, app.success, app.text, app.code,
    )
    values = [str(item.value) for group in groups for item in group]
    values.extend(str(item.value) for item in app.table)
    values.extend(str(item.label) for item in app.expander)
    return "\n".join(values)


def _run_page(path: str, case: dict | None = None) -> AppTest:
    app = AppTest.from_file(path)
    app.session_state["cases"] = [] if case is None else [case]
    app.session_state["current_case"] = case
    app.session_state["current_relation_state"] = {}
    app.run(timeout=10)
    assert not app.exception
    assert app_text(app).strip(), "{} rendered no user-visible text".format(path)
    return app


def test_all_six_pages_load_and_keep_their_applicable_text_boundaries():
    case = sample_case()
    pages = {
        "pages/cast.py": None,
        "pages/board.py": case,
        "pages/yongshen.py": case,
        "pages/tracks.py": case,
        "pages/search.py": None,
        "pages/records.py": case,
    }
    for path, current_case in pages.items():
        app = _run_page(path, current_case)
        text = app_text(app)
        assert not find_forbidden_terms(text, layer="streamlit"), path
        if path in {"pages/board.py", "pages/yongshen.py"}:
            for layer in ("L1", "L2", "L3", "narrate.derivation"):
                assert not find_forbidden_terms(text, layer=layer), "{} / {}".format(path, layer)


def test_cast_then_yongshen_then_tracks_keeps_the_human_selection_across_pages():
    case = sample_case()  # Deterministic equivalent of a completed cast form.
    state = state_for_case(case)
    parent = next(item for item in candidate_options(state["chart"], "父母") if not item["hidden"])

    yongshen = _run_page("pages/yongshen.py", case)
    yongshen.pills[0].set_value(["父母"]).run(timeout=10)
    assert not yongshen.exception
    selection = yongshen.session_state["active_yongshen_by_case"][case["case_id"]]
    assert selection == {"choices": ["父母"], "candidate_selections": {"父母": parent["candidate_id"]}}

    tracks = AppTest.from_file("pages/tracks.py")
    tracks.session_state["current_case"] = case
    tracks.session_state["cases"] = [case]
    tracks.session_state["active_yongshen_by_case"] = {case["case_id"]: selection}
    tracks.run(timeout=10)
    tracks.selectbox[0].set_value("C15：沖之判定（動靜軸）").run(timeout=10)
    assert not tracks.exception
    text = app_text(tracks)
    assert "已由人手所選用神定位" in text
    assert "C15" in text
