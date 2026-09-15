"""TASK_CODEX_23 regressions: direct line choices and table presentation metadata."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from engine.pipeline import build_case_state
from engine.semantics import (
    chong_source_for_line,
    collection_status_for_book_id,
    infer_condition,
    load_decision_table,
    semantic_for_condition,
    semantics_from_relations,
)
from engine.yongshen import LINE_POSITION_OPTIONS, analyze_yongshen
from tools.generate_data import generate_bagong
from tools.update_task23_data import TABLE_NOTES
from ui_contracts import make_case


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "data" / "decision_tables"
TASK_TIME = datetime(2026, 9, 15, 15, 47)
TASK_LINES = [1, 1, 0, 0, 1, 1]


def task_state():
    return build_case_state(
        lines=TASK_LINES, cast_datetime=TASK_TIME, moving_positions=[5, 6],
    )


def task_case() -> dict:
    return make_case(
        coin_counts=[1, 1, 0, 0, 3, 3], cast_datetime=TASK_TIME,
        question_text="", background_text="", is_proxy=False,
    )


def app_text(app: AppTest) -> str:
    return "\n".join(
        item.value
        for group in (app.caption, app.markdown, app.subheader)
        for item in group
    ) + "\n" + "\n".join(item.label for item in app.expander)


def test_every_direct_line_choice_locks_for_all_64_hexagrams():
    for source in generate_bagong():
        state = build_case_state(lines=source["lines"], cast_datetime=TASK_TIME)
        expected_positions = {
            "世爻": state["chart"]["shi"], "應爻": state["chart"]["ying"],
            "初爻": 1, "二爻": 2, "三爻": 3, "四爻": 4, "五爻": 5, "上爻": 6,
        }
        for choice in LINE_POSITION_OPTIONS:
            output = analyze_yongshen(state, choice)
            assert output["status"] == "selected"
            assert output["selected"]["position"] == expected_positions[choice]


def test_task23_ying_choice_directly_locks_line_one_with_six_relative():
    output = analyze_yongshen(task_state(), "應爻")
    assert output["status"] == "selected"
    assert output["selected"] == {
        "candidate_id": "visible:1", "position": 1, "branch": "巳",
        "element": "火", "six_relative": "父母", "choice": "應爻",
        "role": "應", "hidden": False,
    }
    assert output["own_state"]["seasonal_state"] == "囚"
    assert output["own_state"]["empty"] is False
    assert output["own_state"]["month_break"] is False
    assert output["own_state"]["motion"] == "靜"


def test_shi_and_ying_choices_preserve_their_six_relative_identity():
    state = task_state()
    for choice in ("世爻", "應爻"):
        output = analyze_yongshen(state, choice)
        assert output["selected"]["six_relative"]
        assert output["own_state"]["six_relative"] == output["selected"]["six_relative"]


def test_four_tables_have_exact_distinct_task23_notes():
    actual = {}
    for path in TABLE_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["table_id"] in TABLE_NOTES:
            actual[data["table_id"]] = data["table_note"]
    assert actual == TABLE_NOTES
    assert "辨動靜以定刑沖" in actual["C15"]
    assert "哪個爻空" in actual["K"]
    assert "元則喜動、喜旺、喜生" in actual["Y"]
    assert "本表格位未區分月沖、日沖" in actual["C1"]
    assert "本表格位未區分月沖、日沖" in actual["C15"]


def test_task23_line_two_records_month_clash_context_without_changing_grid():
    state = task_state()
    relations = state["relations"]
    assert infer_condition(table_id="C15", relation_result=relations, line=2) == "靜爻遇沖"
    assert chong_source_for_line(relations, 2) == "month"
    semantics = semantics_from_relations(
        relations, line=2, condition="靜爻遇沖",
        table=load_decision_table(TABLE_DIR / "C15_dongjing_axis.json"),
    )
    assert semantics["cell_context"] == {"chong_source": "month"}


def test_tracks_switches_note_and_labels_task23_month_source():
    case = task_case()
    case["yongshen_selected"] = ["二爻"]
    app = AppTest.from_file("pages/tracks.py")
    app.session_state["current_case"] = case
    app.run(timeout=10)
    assert not app.exception
    app.selectbox[0].set_value("C15：沖之判定（動靜軸）").run(timeout=10)
    assert not app.exception
    text = app_text(app)
    assert "C15-R2" in text
    assert "本爻之沖來自月建酉，非日辰" in text
    assert "辨動靜以定刑沖" in text
    assert "未就本表之問題採集：易冒、增刪卜易、卜筮正宗、卜筮全書" in text
    assert "（四本已入庫，但未針對動靜軸檢索）" in text
    assert "該書尚未入庫：京氏易傳、易隱" in text


def test_not_collected_cells_are_derived_from_real_doctrinal_inventory():
    found = 0
    for path in TABLE_DIR.glob("*.json"):
        table = json.loads(path.read_text(encoding="utf-8"))
        for row in table.get("rows", []):
            for cell in row.get("cells", []):
                if cell.get("status") == "not_collected":
                    found += 1
                    assert cell["collection_status"] == collection_status_for_book_id(cell["book_id"])
    assert found > 0


def test_collection_statuses_stay_out_of_the_seven_coverage_counts():
    table = load_decision_table(TABLE_DIR / "C15_dongjing_axis.json")
    result = semantic_for_condition(line=2, condition="靜爻遇沖", table=table)
    assert result["coverage"]["books_not_collected"] == 6
    assert result["collection_status_counts"] == {
        "ingested_not_surveyed": 4, "not_ingested": 2,
    }
