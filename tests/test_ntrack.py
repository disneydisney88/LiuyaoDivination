import copy
import json
from pathlib import Path

from engine.semantics import VALID_STATUSES, load_decision_table, semantic_for_condition


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENVELOPE = {
    "book_id", "source_book", "era", "author", "attribution_status", "framework_type",
    "enumeration_style", "framework_note", "doctrinal_status", "semantic_status", "conflicts_with", "corpus_path", "sets",
}


def test_all_doctrinal_rule_files_have_uniform_envelope():
    for path in (ROOT / "data" / "doctrinal").glob("*_rules.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert REQUIRED_ENVELOPE <= set(data)
        assert data["attribution_status"] in {"attested", "attributed", "compiled"}
        assert data["enumeration_style"] in {"authorial_ordinal", "authorial_count", "none"}
        if data["attribution_status"] == "attributed":
            assert "題" in data["author"] or "託名" in data["author"]


def test_buzhengzong_is_structured_from_task08_extract():
    data = json.loads((ROOT / "data" / "doctrinal" / "buzhengzong_rules.json").read_text(encoding="utf-8"))
    assert len(data["sets"]) == 6
    assert sum(len(source_set["items"]) for source_set in data["sets"]) == 23
    weak_set = next(source_set for source_set in data["sets"] if source_set["set_id"] == "BZ_SET_03")
    weak = weak_set["items"][0]
    assert weak["evidence_strength"] == "weak"
    assert "非其體例章節" in weak["evidence_note"]
    assert data["sets"][0]["definition_original_full"].startswith("凡卦中月破之爻，乃关因之所现也")
    assert data["sets"][2]["definition_original_full"].startswith("凡卦中爻遇旬空，乃神机发现于此也")
    assert "虽遇冲而不散" in weak["definition_original"]
    yuan_ji = next(source_set for source_set in data["sets"] if source_set["set_id"] == "BZ_SET_YUAN_JI_01")
    assert "原神休囚不动" in yuan_ji["definition_original_full"]
    for source_set in data["sets"]:
        assert source_set["count_declared"] is None
        assert source_set["count_mismatch"] is None
        assert source_set["count_actual"] == len(source_set["items"])
        assert source_set["definition_original_full"]
        assert source_set["segmentation_note"]
        assert all(item["enumeration_source"] == "editorial" for item in source_set["items"])


def test_none_enumeration_style_is_explicitly_editorial():
    for path in (ROOT / "data" / "doctrinal").glob("*_rules.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["enumeration_style"] == "none":
            assert all(item.get("enumeration_source") == "editorial"
                       for source_set in data["sets"] for item in source_set["items"])
            assert all(source_set["count_declared"] is None for source_set in data["sets"])


def test_decision_table_is_eight_books_by_five_rows():
    table = load_decision_table()
    assert len(table["books"]) == 8
    assert len(table["rows"]) == 5
    assert all(len(row["cells"]) == 8 for row in table["rows"])


def test_seven_status_values_are_exhaustive_and_validated():
    table = load_decision_table()
    statuses = {
        cell["status"]
        for path in (ROOT / "data" / "decision_tables").glob("*.json")
        for row in json.loads(path.read_text(encoding="utf-8"))["rows"]
        for cell in row["cells"]
    }
    assert statuses == set(VALID_STATUSES)
    for row in table["rows"]:
        assert {cell["book_id"] for cell in row["cells"]} == {book["book_id"] for book in table["books"]}


def test_category_negated_has_null_verdict_and_negation_source():
    table = load_decision_table()
    cells = [cell for row in table["rows"] for cell in row["cells"] if cell["status"] == "category_negated"]
    assert cells
    assert all(cell.get("verdict") is None and cell.get("negation_original") and cell.get("negation_source") for cell in cells)


def test_not_collected_has_no_verdict_or_inferred_text():
    table = load_decision_table()
    cells = [cell for row in table["rows"] for cell in row["cells"] if cell["status"] == "not_collected"]
    assert len(cells) == 10
    assert all("verdict" not in cell for cell in cells)
    result = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    assert all("verdict" not in track for track in result["tracks"].values() if track["status"] == "not_collected")


def test_adding_fixture_book_requires_no_semantics_code_change():
    table = copy.deepcopy(load_decision_table())
    table["books"].append({"book_id": "__test_book__", "name": "測試書"})
    for row in table["rows"]:
        row["cells"].append({"book_id": "__test_book__", "status": "not_collected"})
    result = semantic_for_condition(line=3, condition="休囚之爻遇日沖", table=table)
    assert "測試書" in result["tracks"]
    assert result["tracks"]["測試書"]["status"] == "not_collected"


def test_consensus_group_does_not_swallow_category_negated():
    result = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    statuses = {track["status"] for track in result["tracks"].values()}
    assert "category_negated" in statuses
    assert "not_collected" in statuses
    assert not result.get("consensus", False)


def test_ui_has_explicit_not_collected_and_always_visible_negation_group():
    source = (ROOT / "pages" / "tracks.py").read_text(encoding="utf-8")
    assert "未採集" in source and "採集缺口" in source
    assert "未表述" in source
    negated_block = source[source.index("if negated:"):source.index("if not_addressed:")]
    assert "st.container" in negated_block
    assert "st.expander" not in negated_block
