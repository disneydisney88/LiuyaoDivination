import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
DOCTRINAL = ROOT / "data" / "doctrinal"
TABLES = ROOT / "data" / "decision_tables"
SPEC = ROOT / "SPEC_LIUYAO_v0.2.md"
RULE_PATHS = sorted(DOCTRINAL.glob("*_rules.json"))
FORBIDDEN_SOURCE_GAP_WORDING = (
    "無任何外部來源記錄",
    "無外部來源記錄",
    "無任何外部來源",
)
OVERLAP_WARNING = "註：《黃金策》與《卜筮全書》文本重疊 89.4%（被收錄者與收錄者），二者之一致不構成兩個獨立證據。"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_rule_envelopes_have_cleaning_and_provenance_fields():
    assert len(RULE_PATHS) == 6
    for path in RULE_PATHS:
        data = load(path)
        assert "corpus_cleaned" in data
        assert data["provenance_strength"]
        assert data["provenance_note"]


def test_uncleaned_rule_envelopes_have_cleaning_status():
    for path in RULE_PATHS:
        data = load(path)
        if data["corpus_cleaned"] is False:
            assert data["cleaning_status"]


def test_cleaned_rule_envelopes_point_to_ancient_text():
    for path in RULE_PATHS:
        data = load(path)
        if data["corpus_cleaned"] is True:
            assert "古本" in data["corpus_path"]


def test_corrected_provenance_notes_do_not_repeat_disproved_wording():
    for name in ("zengshan_rules.json", "buzhequanshu_rules.json"):
        note = load(DOCTRINAL / name)["provenance_note"]
        assert not any(wording in note for wording in FORBIDDEN_SOURCE_GAP_WORDING)


def test_huangjince_and_buzhequanshu_have_reciprocal_text_overlap():
    huangjince = load(DOCTRINAL / "huangjince_rules.json")
    buzhequanshu = load(DOCTRINAL / "buzhequanshu_rules.json")
    assert huangjince["text_overlap"][0]["with_book_id"] == "buzhequanshu"
    assert buzhequanshu["text_overlap"][0]["with_book_id"] == "huangjince"


def test_text_overlap_ratio_is_audited_value():
    for name in ("huangjince_rules.json", "buzhequanshu_rules.json"):
        assert load(DOCTRINAL / name)["text_overlap"][0]["overlap_ratio"] == 0.894


def test_jointly_expressed_rows_have_text_overlap_warning():
    checked = 0
    for path in TABLES.glob("*.json"):
        table = load(path)
        for row in table.get("rows", []):
            statuses = {cell["book_id"]: cell["status"] for cell in row.get("cells", [])}
            pair = (statuses.get("huangjin_ce"), statuses.get("buzhequanshu"))
            jointly_expressed = (
                "addressed" in pair
                and all(status in {"addressed", "different_axis"} for status in pair)
            )
            if jointly_expressed:
                checked += 1
                assert OVERLAP_WARNING in row["coverage_label"]
    assert checked > 0


def test_spec_discloses_no_image_level_verification():
    assert "無任何一本可作影像級核對" in SPEC.read_text(encoding="utf-8")


def test_huangjince_contains_unknown_source_douzhen_set():
    data = load(DOCTRINAL / "huangjince_rules.json")
    douzhen = next(source_set for source_set in data["sets"] if source_set["set_id"] == "HJ_SET_DOUZHEN")
    assert douzhen["source_unknown"] is True


def test_spec_does_not_call_bi_zhushu_17_chapters():
    assert "〈辟諸書之謬〉17 篇" not in SPEC.read_text(encoding="utf-8")


def test_spec_section_12_and_all_provenance_notes_avoid_disproved_wording():
    spec = SPEC.read_text(encoding="utf-8")
    section_12 = spec.split("## 12.", 1)[1].split("## 13.", 1)[0]
    assert not any(wording in section_12 for wording in FORBIDDEN_SOURCE_GAP_WORDING)
    for path in RULE_PATHS:
        note = load(path)["provenance_note"]
        assert not any(wording in note for wording in FORBIDDEN_SOURCE_GAP_WORDING)
