"""TASK_CODEX_26 layer-scoped forbidden-text checks."""
from __future__ import annotations

from engine.text_guard import find_forbidden_terms, load_forbidden_terms
from tools.snapshot import load_cases, mechanical_text, render_sections


def test_blacklist_is_audited_and_explicitly_layer_scoped():
    entries = load_forbidden_terms()
    assert len(entries) >= 45
    assert all(entry["added_by"] and entry["reason"] for entry in entries)
    assert all(entry["layer_forbidden"] for entry in entries)
    scatter = next(entry for entry in entries if entry["term"] == "散")
    assert "易冒" in scatter["reason"] and "野鶴" in scatter["reason"]
    assert {"L1", "L2", "L3", "narrate.derivation"} <= set(scatter["layer_forbidden"])
    assert {"tracks.book_verdict", "tracks.original"} <= set(scatter["layer_allowed"])


def test_twelve_mechanical_snapshot_segments_contain_no_forbidden_text_or_json_syntax():
    for case in load_cases():
        text = mechanical_text(case)
        for layer in ("L1", "L2", "L3", "narrate.derivation"):
            assert not find_forbidden_terms(text, layer=layer), "{} / {}".format(case["case_id"], layer)


def test_multitrack_text_remains_exempt_so_original_wording_is_not_edited():
    text = render_sections(load_cases()[0])["tracks"]
    assert "散" in text
    assert not find_forbidden_terms(text, layer="tracks.original")
