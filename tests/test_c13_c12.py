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


def test_c13_uses_five_system_rows_and_keeps_existing_books_not_addressed():
    data = load_json(TABLE_PATH)
    assert len(data["rows"]) == 5
    rows = data["rows"]
    for book_id in {"yimao", "zengshan", "buzhengzong"}:
        for row in rows:
            cell = next(cell for cell in row["cells"] if cell["book_id"] == book_id)
            assert cell["status"] == "not_addressed"
            assert cell["search_note"]
    for row in rows:
        quanshu = next(cell for cell in row["cells"] if cell["book_id"] == "buzhequanshu")
        assert quanshu["status"] == "addressed"


def test_c13_own_systems_do_not_align_or_translate_systems():
    data = load_json(TABLE_PATH)
    assert all(row.get("row_id") != "C13-OWN" for row in data["rows"])
    own = data["own_systems"]
    assert "coverage" not in own
    forbidden = ("相當於", "對應", "等同")
    assert own["entries"]
    for entry in own["entries"]:
        assert entry["own_system"]
        assert not any(word in entry["own_system"] for word in forbidden)


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
