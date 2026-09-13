import ast
import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path

import ui_contracts
from ui_contracts import (
    FORBIDDEN_RECORD_FIELDS,
    RECORD_FIELDS,
    YONGSHEN_OPTIONS,
    csv_bytes,
    make_case,
    negative_category_display,
)

ROOT = Path(__file__).parents[1]


def python_files(*roots):
    return [path for root in roots for path in Path(root).rglob("*.py")]


def test_question_background_are_not_engine_parameters_and_no_http():
    for path in python_files(ROOT / "engine"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names = [arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)]
                assert "question_text" not in names and "background_text" not in names
    source = "\n".join(path.read_text(encoding="utf-8") for path in python_files(ROOT / "engine", ROOT / "pages") + [ROOT / "app.py"])
    assert "import requests" not in source and "import httpx" not in source


def test_yongshen_options_are_equal_plain_labels():
    assert len(YONGSHEN_OPTIONS) == 6
    assert all(isinstance(item, str) for item in YONGSHEN_OPTIONS)
    assert not any(item in {"default", "recommended", "selected", "score", "rank"} for item in YONGSHEN_OPTIONS)


def test_no_random_or_upload_apis_in_ui():
    source = "\n".join(path.read_text(encoding="utf-8") for path in python_files(ROOT / "pages") + [ROOT / "app.py"])
    assert "import random" not in source and "secrets.choice" not in source and "numpy.random" not in source
    assert "file_uploader" not in source


def test_record_schema_has_no_single_conclusion():
    assert not FORBIDDEN_RECORD_FIELDS.intersection(RECORD_FIELDS)
    assert {"case_id", "question_text", "background_text", "yongshen_selected_by", "track_yimao_verdict", "track_zengshan_verdict", "track_buzhengzong_verdict"} <= set(RECORD_FIELDS)


def test_n_tracks_and_human_only_contract():
    track_fields = {field for field in RECORD_FIELDS if field.startswith("track_") and field.endswith("_verdict")}
    assert len(track_fields) == 8
    assert {"track_yimao_verdict", "track_zengshan_verdict", "track_buzhengzong_verdict"} <= track_fields
    assert "human" in (ROOT / "ui_contracts.py").read_text(encoding="utf-8")


def test_category_negated_display_is_nonempty_and_not_not_scattered():
    text = negative_category_display("CATEGORY_NEGATED")
    assert text and "不散" not in text


def test_case_and_csv_schema_store_hidden_as_a_flat_list():
    case = make_case(
        coin_counts=[2, 2, 1, 1, 1, 1],
        cast_datetime=datetime(2026, 9, 13, 12, 0),
        question_text="", background_text="", is_proxy=False,
    )
    assert "hidden" in RECORD_FIELDS
    assert isinstance(case["hidden"], list) and len(case["hidden"]) == 2
    assert case["yongshen_candidates"] == case["hidden"]
    csv_row = next(csv.DictReader(StringIO(csv_bytes([case]).decode("utf-8-sig"))))
    assert json.loads(csv_row["hidden"]) == case["hidden"]


def test_legacy_case_without_hidden_is_normalized_on_load(tmp_path, monkeypatch):
    old_hidden = {
        "六親": "妻財", "branch": "寅", "element": "木", "position": 2,
        "flying_branch": "亥", "flying_element": "水", "rule_id": "R-L1-08a",
        "伏神能否為用": "TODO: pending R-L1-08b verification",
    }
    path = tmp_path / "cases.jsonl"
    path.write_text(json.dumps({
        "lines": [0, 1, 1, 1, 1, 1],
        "yongshen_candidates": [old_hidden],
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(ui_contracts, "RECORDS_PATH", path)
    case = ui_contracts.load_cases()[0]
    assert case["hidden"] == [old_hidden]
    assert case["yongshen_candidates"] == [old_hidden]
