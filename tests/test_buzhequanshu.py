import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "data" / "doctrinal" / "buzhequanshu_rules.json"
C1_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"
C13_PATH = ROOT / "data" / "decision_tables" / "C13_kongwang_scope.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_buzhequanshu_has_task14_envelope():
    data = load_json(RULES_PATH)
    required = {
        "book_id", "source_book", "era", "author", "attribution_status", "framework_type",
        "framework_note", "enumeration_style", "doctrinal_status", "semantic_status",
        "conflicts_with", "corpus_path", "sets",
    }
    assert required <= set(data)
    assert data["book_id"] == "buzhequanshu"
    assert data["attribution_status"] == "compiled"


def test_buzhequanshu_framework_and_enumeration_style():
    data = load_json(RULES_PATH)
    assert data["framework_type"] == "by_topic_no_chapters"
    assert data["enumeration_style"] == "none"


def test_buzhequanshu_items_are_editorial_and_undeclared():
    data = load_json(RULES_PATH)
    assert data["sets"]
    for source_set in data["sets"]:
        assert source_set["count_declared"] is None
        assert source_set["count_actual"] == len(source_set["items"])
        assert source_set["count_mismatch"] is None
        assert source_set["definition_original_full"]
        for item in source_set["items"]:
            assert item["enumeration_source"] == "editorial"
            assert item["line"]
            assert item["chapter"]
            assert item["definition_original"]
            assert item["rule_id"].startswith("R-BQ-")


def test_five_void_systems_are_independent_sets():
    data = load_json(RULES_PATH)
    void_sets = [source_set for source_set in data["sets"] if "void_system_id" in source_set]
    assert {source_set["void_system_id"] for source_set in void_sets} == {
        "liujia_kongwang", "tiandi_kongwang", "sidakong_kongwang", "jielu_kongwang", "wu_kong",
    }
    assert len(void_sets) == 5
    assert all(isinstance(source_set["void_system_id"], str) for source_set in void_sets)


def test_non_liujia_void_systems_have_no_qing_equivalence():
    data = load_json(RULES_PATH)
    for source_set in data["sets"]:
        if source_set.get("void_system_id") == "liujia_kongwang":
            assert source_set["equivalent_to_qing_term"] == "旬空"
        elif "void_system_id" in source_set:
            assert source_set["equivalent_to_qing_term"] is None
            assert "未見對應術語" in source_set["equivalence_note"]


def test_buzhequanshu_uses_clean_corpus_path():
    data = load_json(RULES_PATH)
    assert data["corpus_path"].endswith("卜筮全書_古本.txt")
    assert not data["corpus_path"].endswith("卜筮全書.txt")


def test_c13_keeps_existing_three_books_not_addressed():
    data = load_json(C13_PATH)
    assert len(data["books"]) == 8
    assert len(data["void_systems"]) == 5
    assert len(data["rows"]) == 9
    assert all(len(row["cells"]) == 5 for row in data["rows"] if row.get("row_id") != "C13-OWN")
    existing_books = {"yimao", "zengshan", "buzhengzong"}
    for row in data["rows"]:
        if row.get("row_id") == "C13-OWN":
            continue
        if row["book_id"] in existing_books:
            assert {cell["status"] for cell in row["cells"]} == {"not_addressed"}
            assert all(cell["search_note"] for cell in row["cells"])
    quanshu = next(row for row in data["rows"] if row["book_id"] == "buzhequanshu")
    assert {cell["status"] for cell in quanshu["cells"]} == {"addressed"}


def test_c1_quanshu_r2_r5_not_addressed_have_search_notes():
    data = load_json(C1_PATH)
    quanshu_cells = {
        row["row_id"]: next(cell for cell in row["cells"] if cell["book_id"] == "buzhequanshu")
        for row in data["rows"]
    }
    assert quanshu_cells["C1-R1"]["status"] == "addressed"
    assert quanshu_cells["C1-R1"]["verdict"] == "損"
    for row_id in ("C1-R2", "C1-R3", "C1-R4", "C1-R5"):
        assert quanshu_cells[row_id]["status"] == "not_addressed"
        assert quanshu_cells[row_id]["search_note"]


def test_c1_r1_is_not_consensus_and_keeps_distinct_verdict_note():
    data = load_json(C1_PATH)
    row = next(row for row in data["rows"] if row["row_id"] == "C1-R1")
    assert row["row_title"] == "三家判不散，一家判損"
    assert "consensus" not in row
    cell = next(cell for cell in row["cells"] if cell["book_id"] == "buzhequanshu")
    assert cell["verdict_note"]
    assert "損" in cell["verdict_note"] and "散" in cell["verdict_note"]
    assert cell["line"] == ["5080–5081", "5500–5505", "5403–5408"]


def test_c1_r3_r4_preserve_related_material_without_alignment():
    data = load_json(C1_PATH)
    cells = {
        row["row_id"]: next(cell for cell in row["cells"] if cell["book_id"] == "buzhequanshu")
        for row in data["rows"]
    }
    assert cells["C1-R3"]["status"] == "not_addressed"
    assert len(cells["C1-R3"]["related_material"]) == 3
    assert cells["C1-R4"]["status"] == "not_addressed"
    assert len(cells["C1-R4"]["related_material"]) == 4
