import json
from pathlib import Path


DATA = Path(__file__).parents[1] / "data" / "doctrinal" / "zengshan_rules.json"


def load_data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_paired_sets_mutually_reference_and_invert_polarity():
    data = load_data()
    sets = {item["set_id"]: item for item in data["sets"]}
    for group in sets.values():
        if group.get("paired_with") is None:
            continue
        pair = sets[group["paired_with"]]
        assert pair["paired_with"] == group["set_id"]
        assert {group["polarity"], pair["polarity"]} == {"positive", "negative"}


def test_fifteen_own_sets_have_matching_counts():
    data = load_data()
    own = [group for group in data["sets"] if group["set_id"].startswith("ZS_SET_") and group["set_id"] not in {"ZS_SET_QUOTED_01", "ZS_SET_OWN_01"}]
    assert len(own) == 15
    assert all(group["count_declared"] == group["count_actual"] for group in own)


def test_no_set_contains_severity_fields():
    data = load_data()
    for group in data["sets"]:
        assert "severity_rank" not in group
        assert "severity_band" not in group
        for item in group.get("items", []):
            assert "severity_rank" not in item
            assert "severity_band" not in item


def test_quoted_set_attribution():
    data = load_data()
    quoted = next(group for group in data["sets"] if group["set_id"] == "ZS_SET_QUOTED_01")
    assert quoted["attribution"] == "quoted_from_others"


def test_negated_set_type():
    data = load_data()
    negated = next(group for group in data["sets"] if group["set_id"] == "ZS_NEGATED_01")
    assert negated["conflict_type"] == "category_negation"
