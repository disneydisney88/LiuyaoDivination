import json
from pathlib import Path

from engine.semantics import (
    COLLECTION_GAP_TEMPLATE,
    COVERAGE_NOTE,
    semantic_for_condition,
)


ROOT = Path(__file__).resolve().parents[1]
TABLE_PATHS = (
    ROOT / "data" / "decision_tables" / "C1_chong_san.json",
    ROOT / "data" / "decision_tables" / "C13_kongwang_scope.json",
)
COVERAGE_KEYS = {
    "books_total",
    "books_collected",
    "books_addressed",
    "books_not_addressed",
    "books_category_negated",
    "books_not_collected",
}
FORBIDDEN_KEYS = {
    "confidence", "reliability", "certainty", "majority", "consensus_ratio",
    "vote", "score", "weight", "weighted_verdict", "agreement_rate",
    "support_count",
}


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


def test_every_decision_table_row_has_complete_coverage_counts():
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            coverage = row["coverage"]
            assert set(coverage) == COVERAGE_KEYS
            assert all(coverage[key] is not None for key in COVERAGE_KEYS)


def test_coverage_counts_sum_to_books_total():
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            coverage = row["coverage"]
            assert (
                coverage["books_addressed"]
                + coverage["books_not_addressed"]
                + coverage["books_category_negated"]
                + coverage["books_not_collected"]
                == coverage["books_total"]
            )


def test_addressed_and_category_negated_are_independent_counts():
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            coverage = row["coverage"]
            assert "books_addressed_and_category_negated" not in coverage
            assert coverage["books_addressed"] == sum(
                cell["status"] == "addressed" for cell in row["cells"]
            )
            assert coverage["books_category_negated"] == sum(
                cell["status"] == "category_negated" for cell in row["cells"]
            )


def test_coverage_and_derived_outputs_have_no_forbidden_fields():
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            assert FORBIDDEN_KEYS.isdisjoint(nested_keys(row["coverage"]))
            assert FORBIDDEN_KEYS.isdisjoint(nested_keys(row))
    c1 = load_json(TABLE_PATHS[0])
    for row in c1["rows"]:
        result = semantic_for_condition(line=3, condition=row["condition"], table=c1)
        assert FORBIDDEN_KEYS.isdisjoint(nested_keys(result))


def test_ui_material_text_does_not_claim_reliability_or_majority():
    forbidden = ("厚", "薄", "材料較少", "材料充足", "材料豐富", "優", "劣",
                 "可靠", "可信", "充分", "多數", "大部分", "主流")
    texts = []
    for path in TABLE_PATHS:
        data = load_json(path)
        texts.extend(row["coverage_label"] for row in data["rows"])
        texts.extend(
            COLLECTION_GAP_TEMPLATE.format(row["coverage"]["books_not_collected"])
            for row in data["rows"] if row["coverage"]["books_not_collected"] > 0
        )
    page_source = (ROOT / "pages" / "tracks.py").read_text(encoding="utf-8")
    assert "material_depth" not in page_source
    assert not any(word in text for text in texts for word in forbidden)


def test_coverage_objects_have_no_evaluative_fields():
    forbidden = {"material_depth", "depth", "quality", "richness", "strength", "厚度", "優劣"}
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            coverage = row["coverage"]
            assert not any(
                key in forbidden or any(token in key.lower() for token in ("depth", "quality", "richness", "strength"))
                for key in coverage
            )
            assert "material_depth" not in row


def test_uncollected_rows_show_explicit_collection_gap_text():
    for path in TABLE_PATHS:
        data = load_json(path)
        for row in data["rows"]:
            if row["coverage"]["books_not_collected"] > 0:
                text = COLLECTION_GAP_TEMPLATE.format(row["coverage"]["books_not_collected"])
                assert "未採集" in text
                assert "非該書無立場" in text


def test_coverage_footer_is_fixed_and_disclaims_confidence_and_votes():
    expected = """**關於本表之切法**

R1–R5 五個條件係本項目從《易冒》十八法與野鶴之論述反推所得之切法，**非各書自身之設問方式**。

其他書並無義務按此五格立說。《卜筮全書》按事類編排、全書無專章體例，其「未表述」部分反映的是本表提問方式偏向《易冒》，而非該書材料貧乏。

**覆蓋率為材料厚度指標，不是可信度指標，更不是票數。** 三家有表述不等於該說較可信；一家否定範疇不等於該家是少數派 —— 否定範疇是拒絕進入此提問框架，不是投了反對票。"""
    assert COVERAGE_NOTE == expected
    assert "不是可信度指標" in COVERAGE_NOTE
    assert "不是票數" in COVERAGE_NOTE
