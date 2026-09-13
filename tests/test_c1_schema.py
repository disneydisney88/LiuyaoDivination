import json
from pathlib import Path

from engine.semantics import semantic_for_condition


ROOT = Path(__file__).resolve().parents[1]
C1_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"


def test_c1_addressed_cells_have_non_null_verdict():
    table = json.loads(C1_PATH.read_text(encoding="utf-8"))
    addressed = [cell for row in table["rows"] for cell in row["cells"] if cell["status"] == "addressed"]
    assert addressed
    assert all("verdict" in cell and cell["verdict"] is not None for cell in addressed)


def test_c1_r1_ui_semantics_preserve_label_verdict_note_and_line():
    result = semantic_for_condition(line=3, condition="旺相之爻遇沖")
    track = result["tracks"]["卜筮全書"]
    assert result["row_title"] == "三家判不散，一家判損"
    assert track["verdict"] == "損"
    assert track["verdict_note"]
    assert track["line"] == ["5080–5081", "5500–5505", "5403–5408"]
