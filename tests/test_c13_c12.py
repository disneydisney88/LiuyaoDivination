import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "data" / "decision_tables" / "C13_kongwang_scope.json"
ZENGSHAN_PATH = ROOT / "data" / "doctrinal" / "zengshan_rules.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_c12_has_exactly_five_types_and_parallel_handling():
    text = (ROOT / "SPEC_LIUYAO_v0.2.md").read_text(encoding="utf-8")
    section = text.split("### C12", 1)[1].split("### C13", 1)[0]
    rows = re.findall(r"^\| \*\*[一二三四五]、[^\n]+$", section, flags=re.MULTILINE)
    assert len(rows) == 5
    parallel = next(row for row in rows if "五、平行體系" in row)
    assert "不可對齊" in parallel
    assert "不可互譯" in parallel


def test_c13_collected_books_are_not_addressed_for_all_five_systems():
    data = load_json(TABLE_PATH)
    rows = {row["book_id"]: row for row in data["rows"] if row.get("row_id") != "C13-OWN"}
    for book_id in {"yimao", "zengshan", "buzhengzong"}:
        cells = rows[book_id]["cells"]
        assert len(cells) == 5
        assert {cell["status"] for cell in cells} == {"not_addressed"}
        assert all(cell["search_note"] for cell in cells)


def test_c13_own_systems_do_not_align_or_translate_systems():
    data = load_json(TABLE_PATH)
    own = next(row for row in data["rows"] if row.get("row_id") == "C13-OWN")
    forbidden = ("相當於", "對應", "等同")
    addressed = [cell for cell in own["cells"] if cell["status"] == "addressed"]
    assert len(addressed) == 3
    for cell in addressed:
        assert cell["own_system"]
        assert not any(word in cell["own_system"] for word in forbidden)


def test_zengshan_provenance_is_weak_and_explained():
    data = load_json(ZENGSHAN_PATH)
    assert data["provenance_strength"] == "weak"
    assert data["provenance_note"]


def test_zengshan_comparison_edition_is_explicitly_not_a_book_id():
    data = load_json(ZENGSHAN_PATH)
    comparison = data["comparison_edition"]
    assert comparison["role"] == "對照本。不另開 book_id，不入決策表"


def test_decision_tables_have_no_traditional_zengshan_book_id():
    def book_ids(value):
        if isinstance(value, dict):
            found = []
            if "book_id" in value:
                found.append(value["book_id"])
            for child in value.values():
                found.extend(book_ids(child))
            return found
        if isinstance(value, list):
            found = []
            for child in value:
                found.extend(book_ids(child))
            return found
        return []

    for path in (ROOT / "data" / "decision_tables").glob("*.json"):
        for book_id in book_ids(load_json(path)):
            assert not re.search(r"zengshan[_-].*(trad|繁)|zengshan_trad", book_id, re.IGNORECASE)
