import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_mechanical_data_has_no_doctrinal_status():
    for path in (ROOT / "data" / "mechanical").glob("*.json"):
        assert "doctrinal_status" not in read_json(path)


def test_doctrinal_data_has_required_header():
    for path in (ROOT / "data" / "doctrinal").glob("*.json"):
        data = read_json(path)
        assert data.get("source_book")
        assert data.get("semantic_status") == "structured_only_no_effects_implemented"
