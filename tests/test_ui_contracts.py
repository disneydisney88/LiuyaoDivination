import ast
from pathlib import Path

from ui_contracts import FORBIDDEN_RECORD_FIELDS, RECORD_FIELDS, YONGSHEN_OPTIONS, negative_category_display

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
