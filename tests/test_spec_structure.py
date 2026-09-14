from pathlib import Path
import json
import re


SPEC = Path(__file__).parents[1] / "SPEC_LIUYAO_v0.2.md"


def _table_rows(text: str, heading: str, next_heading: str):
    section = text.split(heading, 1)[1].split(next_heading, 1)[0]
    return [line.split("|")[1:-1] for line in section.splitlines() if line.startswith("|") and "---" not in line]


def test_pending_items_have_structured_fields_and_no_closed_status():
    text = SPEC.read_text(encoding="utf-8")
    rows = _table_rows(text, "### §11.1 未決事項", "### §11.2 已結案")
    assert rows[0] == [" id ", " 事項 ", " 類別 ", " 阻交付 ", " 現況 "]
    for row in rows[1:]:
        assert all(cell.strip() for cell in row)
        assert "結案" not in row[4]
        assert row[2].strip() in {"原文待核", "設計決定", "技術選型", "範圍決定"}
        assert row[3].strip() in {"是", "否"}


def test_closed_items_have_closed_task_column():
    text = SPEC.read_text(encoding="utf-8")
    rows = _table_rows(text, "### §11.2 已結案", "### §11.3 已記錄之事實")
    assert rows[0] == [" id ", " 事項 ", " 結案理由 ", " 結案於 "]
    for row in rows[1:]:
        assert all(cell.strip() for cell in row)
        assert row[3].strip().startswith("TASK_")


def test_spec_ids_are_unique():
    text = SPEC.read_text(encoding="utf-8")
    pending = _table_rows(text, "### §11.1 未決事項", "### §11.2 已結案")[1:]
    closed = _table_rows(text, "### §11.2 已結案", "### §11.3 已記錄之事實")[1:]
    ids = [row[0].strip() for row in pending + closed]
    assert len(ids) == len(set(ids))


def test_six_conditions_are_not_coattributed_to_yimao_in_live_rules():
    """Historical-correction rows may quote the old attribution; live rules may not."""
    live_spec = SPEC.read_text(encoding="utf-8").split("## 附錄：判斷修正史", 1)[0]
    live_entries = re.split(r"(?m)^### ", live_spec)
    assert all(not ("六況" in entry and "易冒" in entry) for entry in live_entries)

    doctrinal_dir = SPEC.parent / "data" / "doctrinal"
    for path in doctrinal_dir.glob("*_rules.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for source_set in data["sets"]:
            entry = json.dumps(source_set, ensure_ascii=False)
            assert not ("六況" in entry and "易冒" in entry), path.name
