import json
from pathlib import Path


DATA = Path(__file__).parents[1] / "data" / "yimao_rules.json"


def load_data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_yimao_set_01_has_complete_ordinals():
    data = load_data()
    items = next(group["items"] for group in data["sets"] if group["set_id"] == "YM_SET_01")
    assert len(items) == 18
    assert [item["item_ordinal"] for item in items] == list(range(1, 19))


def test_yimao_set_01_severity_bands():
    data = load_data()
    items = next(group["items"] for group in data["sets"] if group["set_id"] == "YM_SET_01")
    bands = [item["severity_band"] for item in items]
    assert bands.count("全吉") == 8
    assert bands.count("半吉") == 3
    assert bands.count("凶陷") == 7


def test_yimao_item_17_has_exception():
    data = load_data()
    items = next(group["items"] for group in data["sets"] if group["set_id"] == "YM_SET_01")
    item_17 = next(item for item in items if item["item_ordinal"] == 17)
    assert item_17["exception_original"] is not None


def test_yimao_definitions_are_nonempty():
    data = load_data()
    for group in data["sets"]:
        for item in group["items"]:
            assert item["definition_original"]


def test_yimao_semantic_status_is_structured_only():
    data = load_data()
    assert data["semantic_status"] == "structured_only_no_effects_implemented"
