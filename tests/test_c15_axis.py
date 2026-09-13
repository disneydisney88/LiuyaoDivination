import json
from pathlib import Path

import pytest

from engine.semantics import VALID_STATUSES


ROOT = Path(__file__).resolve().parents[1]
C1_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"
C15_PATH = ROOT / "data" / "decision_tables" / "C15_dongjing_axis.json"
HUANGJINCE_PATH = ROOT / "data" / "doctrinal" / "huangjince_rules.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def nested_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def test_five_status_values_are_mutually_exclusive_and_complete():
    c1 = load_json(C1_PATH)
    statuses = {cell["status"] for row in c1["rows"] for cell in row["cells"]}
    assert statuses == set(VALID_STATUSES)
    assert all(isinstance(cell["status"], str) for row in c1["rows"] for cell in row["cells"])


def test_different_axis_cells_require_axis_evidence_and_null_verdict():
    c1 = load_json(C1_PATH)
    cells = [cell for row in c1["rows"] for cell in row["cells"] if cell["status"] == "different_axis"]
    assert len(cells) == 5
    for cell in cells:
        assert cell["verdict"] is None
        assert cell["axis_note"]
        assert cell["axis_original"]
        assert cell["axis_source"]


def test_c1_coverage_counts_include_different_axis():
    c1 = load_json(C1_PATH)
    for row in c1["rows"]:
        coverage = row["coverage"]
        assert (
            coverage["books_addressed"]
            + coverage["books_not_addressed"]
            + coverage["books_category_negated"]
            + coverage["books_different_axis"]
            + coverage["books_not_collected"]
            == coverage["books_total"]
        )


def test_different_axis_has_its_own_coverage_count():
    c1 = load_json(C1_PATH)
    for row in c1["rows"]:
        coverage = row["coverage"]
        assert coverage["books_different_axis"] == 1
        assert "books_addressed_or_different_axis" not in coverage
        assert coverage["books_addressed"] == sum(
            cell["status"] == "addressed" for cell in row["cells"]
        )


def test_c15_is_three_rows_by_eight_books():
    c15 = load_json(C15_PATH)
    assert len(c15["rows"]) == 3
    assert all(len(row["cells"]) == 8 for row in c15["rows"])
    assert [row["condition"] for row in c15["rows"]] == ["空爻遇沖", "靜爻遇沖", "動爻遇沖"]


def test_c15_existing_books_remain_not_collected():
    c15 = load_json(C15_PATH)
    existing_books = {"yimao", "zengshan", "buzhengzong", "buzhequanshu"}
    for row in c15["rows"]:
        cells = {cell["book_id"]: cell for cell in row["cells"]}
        assert {cells[book_id]["status"] for book_id in existing_books} == {"not_collected"}


def test_c1_and_c15_have_no_cross_axis_mapping_fields():
    forbidden = {"axis_mapping", "converted_verdict", "equivalent_in_c1", "derived_from"}
    for path in (C1_PATH, C15_PATH):
        assert forbidden.isdisjoint(nested_keys(load_json(path)))


def test_c1_huangjin_ce_is_different_axis_without_verdict():
    c1 = load_json(C1_PATH)
    for row in c1["rows"]:
        cell = next(cell for cell in row["cells"] if cell["book_id"] == "huangjin_ce")
        assert cell["status"] == "different_axis"
        assert cell["verdict"] is None
        assert cell["cross_reference"] == "C15"


def test_huangjince_corpus_path_is_ancient_copy_when_a_is_delivered():
    if not HUANGJINCE_PATH.exists():
        pytest.skip("A 部分待黃金策_千金賦_古本.txt 交付")
    data = load_json(HUANGJINCE_PATH)
    assert data["corpus_path"].endswith("03_黃金策/黃金策_千金賦_古本.txt")


def test_huangjince_provenance_is_weak_when_a_is_delivered():
    if not HUANGJINCE_PATH.exists():
        pytest.skip("A 部分待黃金策_千金賦_古本.txt 交付")
    data = load_json(HUANGJINCE_PATH)
    assert data["provenance_strength"] == "weak"
    assert "不成立" in data["provenance_note"]


def test_huangjince_tripartite_items_share_one_set_when_a_is_delivered():
    if not HUANGJINCE_PATH.exists():
        pytest.skip("A 部分待黃金策_千金賦_古本.txt 交付")
    data = load_json(HUANGJINCE_PATH)
    items = [
        (source_set, item)
        for source_set in data["sets"]
        for item in source_set["items"]
        if item.get("line") in {30, 34, 76}
    ]
    assert len(items) == 3
    assert len({source_set["set_id"] for source_set, _ in items}) == 1
    source_set = items[0][0]
    assert source_set["is_tripartite_group"] is True
