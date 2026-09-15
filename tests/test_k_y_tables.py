"""TASK_CODEX_22: K/Y tables, 火珠林 envelope, and seven-status schema."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "data" / "decision_tables"
DOCTRINAL = ROOT / "data" / "doctrinal"
SPEC = ROOT / "SPEC_LIUYAO_v0.2.md"
STATUS_KEYS = (
    "books_addressed", "books_not_addressed", "books_not_collected",
    "books_category_negated", "books_concept_absent",
    "books_explicit_exclusion", "books_different_axis",
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cell(table: dict, row_id: str, book_id: str) -> dict:
    row = next(item for item in table["rows"] if item["row_id"] == row_id)
    return next(item for item in row["cells"] if item["book_id"] == book_id)


def test_k_table_is_ten_rows_by_eight_books():
    table = load(TABLES / "K_kongwang_effect.json")
    assert len(table["rows"]) == 10
    assert all(len(row["cells"]) == 8 for row in table["rows"])


def test_y_table_is_ten_rows_by_eight_books():
    table = load(TABLES / "Y_yuanshen_jishen.json")
    assert len(table["rows"]) == 10
    assert all(len(row["cells"]) == 8 for row in table["rows"])


def test_k_r4_keeps_nonempty_warning_note():
    table = load(TABLES / "K_kongwang_effect.json")
    row = next(item for item in table["rows"] if item["row_id"] == "K-R4")
    assert row["row_note"]


def test_yimao_keeps_thirteen_and_eight_empty_sets_separate():
    data = load(DOCTRINAL / "yimao_rules.json")
    sets = {item["set_id"]: item for item in data["sets"]}
    assert {"YM_SET_06", "YM_SET_10"} <= set(sets)
    assert sets["YM_SET_06"]["chapter"] != sets["YM_SET_10"]["chapter"]
    assert all(sets[set_id]["source"] == "易冒" for set_id in ("YM_SET_06", "YM_SET_10"))


def test_yimao_thirteen_empty_methods_have_only_declared_valences():
    data = load(DOCTRINAL / "yimao_rules.json")
    thirteen = next(item for item in data["sets"] if item["set_id"] == "YM_SET_10")
    assert all(item["valence"] in {"useful", "not_dead", "guarded_against"} for item in thirteen["items"])


def test_yimao_thirteen_empty_method_valence_distribution():
    data = load(DOCTRINAL / "yimao_rules.json")
    thirteen = next(item for item in data["sets"] if item["set_id"] == "YM_SET_10")
    values = [item["valence"] for item in thirteen["items"]]
    assert values.count("useful") == 6
    assert values.count("not_dead") == 2
    assert values.count("guarded_against") == 5


def test_y_table_yimao_is_different_axis_and_preserves_source_text():
    table = load(TABLES / "Y_yuanshen_jishen.json")
    entry = cell(table, "Y-R1", "yimao")
    assert entry["status"] == "different_axis"
    assert "元则喜动、喜旺、喜生" in entry["axis_original"]
    r10 = cell(table, "Y-R10", "zengshan")
    assert r10["status"] == "different_axis"
    assert r10["cross_reference"] is None
    assert "未以動靜切分" in r10["axis_note"]


def test_y_table_buzhequanshu_preserves_yuanchen_term_note():
    table = load(TABLES / "Y_yuanshen_jishen.json")
    entry = cell(table, "Y-R1", "buzhequanshu")
    assert "元辰" in entry["original"]
    assert entry["term_note"] == "本書用「元辰」，清代三家用「元神」。二者概念對應係編者判定，非原文明言。"


def test_huozhulin_envelope_uses_two_role_framework():
    data = load(DOCTRINAL / "huozhulin_rules.json")
    required = {"book_id", "framework_type", "framework_note", "enumeration_style", "conflicts_with", "sets"}
    assert required <= set(data)
    assert data["framework_type"] == "two_role_category_then_strength"


def test_huozhulin_y_r7_to_r10_are_explicit_exclusions():
    table = load(TABLES / "Y_yuanshen_jishen.json")
    for row_id in ("Y-R7", "Y-R8", "Y-R9", "Y-R10"):
        entry = cell(table, row_id, "huozhulin")
        assert entry["status"] == "explicit_exclusion"
        assert entry["exclusion_original"] and entry["exclusion_source"]


def test_huozhulin_is_different_axis_in_every_c1_and_c15_cell():
    for filename in ("C1_chong_san.json", "C15_dongjing_axis.json"):
        table = load(TABLES / filename)
        assert all(cell["status"] == "different_axis"
                   for row in table["rows"]
                   for cell in row["cells"] if cell["book_id"] == "huozhulin")


def test_huozhulin_eight_categories_set_is_closing_summary():
    data = load(DOCTRINAL / "huozhulin_rules.json")
    summary = next(item for item in data["sets"] if item["set_id"] == "FHL_SET_08")
    assert summary["is_closing_summary"] is True


def test_seven_status_coverage_counts_sum_to_books_total():
    for path in TABLES.glob("*.json"):
        for row in load(path)["rows"]:
            coverage = row["coverage"]
            assert sum(coverage[key] for key in STATUS_KEYS) == coverage["books_total"]


def test_explicit_exclusion_and_concept_absent_are_independent_counts():
    table = load(TABLES / "Y_yuanshen_jishen.json")
    assert any(row["coverage"]["books_explicit_exclusion"] for row in table["rows"])
    assert any(row["coverage"]["books_concept_absent"] for row in table["rows"])
    for row in table["rows"]:
        coverage = row["coverage"]
        assert "books_addressed_and_explicit_exclusion" not in coverage
        assert "books_addressed_and_concept_absent" not in coverage
        for entry in row["cells"]:
            if entry["status"] in {"concept_absent", "explicit_exclusion"}:
                assert "verdict" in entry and entry["verdict"] is None


def test_spec_contains_explicit_exclusion_requirements_verbatim():
    text = SPEC.read_text(encoding="utf-8")
    assert "① 設問者已提出該概念" in text
    assert "② 答者明文拒絕" in text
    assert "③ 自述方法界限" in text
