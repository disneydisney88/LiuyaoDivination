import json
import re
from pathlib import Path

from engine.semantics import calculate_coverage, load_decision_table

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "A": ROOT / "data/decision_tables/A_yingqi.json",
    "M1": ROOT / "data/decision_tables/M1_mujue_source.json",
    "M2": ROOT / "data/decision_tables/M2_suiguirumu.json",
    "M3": ROOT / "data/decision_tables/M3_suimu_wangshuai.json",
}


def row(table, row_id):
    return next(item for item in table["rows"] if item["row_id"] == row_id)


def test_task27_table_dimensions():
    assert [len(load_decision_table(TABLES[key])["rows"]) for key in TABLES] == [8, 8, 5, 2]
    assert all(len(load_decision_table(path)["books"]) == 8 for path in TABLES.values())


def test_a_addressed_cells_are_conditional_candidates():
    table = load_decision_table(TABLES["A"])
    for item in sum((r["cells"] for r in table["rows"]), []):
        if item["status"] == "addressed":
            assert item["verdict"] is not None
            assert item["candidate_type"] == "conditional"
            assert item["candidate_rule"]


def test_a_contains_no_actual_dates():
    text = json.dumps(load_decision_table(TABLES["A"]), ensure_ascii=False)
    assert not re.search(r"\d{4}-\d{1,2}-\d{1,2}|\d{4}年\S{1,3}月\S{1,3}日", text)


def test_match_quality_is_modifier():
    table = load_decision_table(TABLES["A"])
    for cell in sum((r["cells"] for r in table["rows"]), []):
        if "match_quality" in cell:
            assert cell["match_quality"] in {"clean", "partial"}
        if cell.get("match_quality") == "partial":
            assert cell.get("partial_note")


def test_match_quality_is_not_eighth_status():
    table = load_decision_table(TABLES["A"])
    assert {cell["status"] for r in table["rows"] for cell in r["cells"]} <= {
        "addressed", "not_addressed", "not_collected", "category_negated",
        "concept_absent", "explicit_exclusion", "different_axis",
    }


def test_m1_yimao_month_tomb_is_category_negated():
    cell = next(c for c in row(load_decision_table(TABLES["M1"]), "M1-R2")["cells"] if c["book_id"] == "yimao")
    assert cell["status"] == "category_negated"
    assert "月則無也" in cell["negation_original"]


def test_m1_soil_has_two_tracks():
    tracks = load_decision_table(TABLES["M1"])["soil_tracks"]
    assert set(tracks) == {"track_A", "track_B"}
    assert tracks["track_A"]["墓"] == "辰"
    assert tracks["track_B"]["墓"] == "戌"


def test_yimao_soil_cell_retains_474_position():
    cell = next(c for c in row(load_decision_table(TABLES["M1"]), "M1-R1")["cells"] if c["book_id"] == "yimao")
    assert "五行家" in cell["soil_original"]
    assert "雙說並陳未擇一" not in json.dumps(cell, ensure_ascii=False)


def test_m3_other_books_are_not_collected():
    table = load_decision_table(TABLES["M3"])
    for r in table["rows"]:
        assert sum(c["status"] == "not_collected" for c in r["cells"]) == 7


def test_m2_note_identifies_suigui_and_s101():
    note = load_decision_table(TABLES["M2"])["table_note"]
    assert "隨鬼入墓" in note
    assert "S10.1" in note


def test_m1_note_does_not_default_tomb_bad():
    assert "不預設墓絕為凶" in load_decision_table(TABLES["M1"])["table_note"]


def test_new_table_coverage_sums_to_books_total():
    for path in TABLES.values():
        table = load_decision_table(path)
        for r in table["rows"]:
            assert sum(r["coverage"][key] for key in (
                "books_addressed", "books_not_addressed", "books_not_collected",
                "books_category_negated", "books_concept_absent",
                "books_explicit_exclusion", "books_different_axis")) == r["coverage"]["books_total"]
            assert calculate_coverage(r)["coverage"]["books_total"] == 8


def test_huangjin_m1_has_direction_note():
    table = load_decision_table(TABLES["M1"])
    cells = [c for r in table["rows"] for c in r["cells"] if c["book_id"] == "huangjin_ce"]
    assert any(c.get("direction_note") for c in cells)
