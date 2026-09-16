"""TASK_CODEX_26 golden text snapshot regressions."""
from __future__ import annotations

import hashlib

from engine.semantics import chong_source_for_line
from engine.yongshen import analyze_yongshen, candidate_options
from tools.snapshot import (
    CHECKSUMS_PATH,
    compare_golden,
    load_cases,
    render_sections,
    snapshot_path,
    state_for_definition,
)


def _focused(case, state):
    option = candidate_options(state["chart"], case["focus_choice"])[0]
    return option, analyze_yongshen(state, case["focus_choice"], option["candidate_id"])


def test_twelve_snapshot_cases_cover_the_required_boundaries():
    cases = {case["case_id"]: case for case in load_cases()}
    assert len(cases) == 12
    states = {case_id: state_for_definition(case) for case_id, case in cases.items()}
    assert states["01_qian_pure_static"]["chart"]["position"] == "本宮"
    assert not cases["01_qian_pure_static"]["moving_positions"]
    assert states["02_youhun"]["chart"]["position"] == "遊魂"
    assert states["03_guihun"]["chart"]["position"] == "歸魂"
    assert len(states["04_all_relatives_present"]["chart"]["hidden"]) == 0
    assert len(states["05_jiji_single_hidden"]["chart"]["hidden"]) == 1
    assert len(states["06_two_hidden"]["chart"]["hidden"]) == 2
    assert any(
        len(candidate_options(states["07_yi_double_occurrence"]["chart"], choice)) >= 2
        for choice in ("父母", "官鬼", "妻財", "子孫", "兄弟")
    )

    for case_id, required_source in (("09_month_chong", "month"), ("10_day_chong", "day")):
        option, _ = _focused(cases[case_id], states[case_id])
        assert chong_source_for_line(states[case_id]["relations"], option["position"]) == required_source
    option, selected = _focused(cases["08_empty_yongshen"], states["08_empty_yongshen"])
    assert selected["own_state"]["empty"] is True and selected["decision_table"]["K"]
    option, selected = _focused(cases["11_tun_hidden_yongshen"], states["11_tun_hidden_yongshen"])
    assert option["hidden"] is True and selected["flying_hidden_relation"]
    _, selected = _focused(cases["12_dead_y_state"], states["12_dead_y_state"])
    assert any(item["seasonal_state"] == "死" for item in selected["decision_table"]["Y"]["locations"])


def test_every_snapshot_has_the_four_user_text_sections():
    for case in load_cases():
        sections = render_sections(case)
        assert set(sections) == {"board", "yongshen", "tracks", "derivation"}
        assert all(value.strip() for value in sections.values())
        assert "六爻表" in sections["board"]
        assert "格位判定" in sections["yongshen"]
        assert "覆蓋率" in sections["tracks"]
        assert "第 1 步" in sections["derivation"]


def test_text_snapshot_bodies_match_golden_with_human_review_message():
    mismatches = compare_golden()
    assert not mismatches, "\n\n".join(mismatches)


def test_snapshot_checksums_match_the_twelve_full_text_files():
    declared = {
        name: digest for digest, name in (
            line.split("  ", 1) for line in CHECKSUMS_PATH.read_text(encoding="utf-8").splitlines()
            if "  " in line
        )
    }
    assert len(declared) == 12
    for case in load_cases():
        path = snapshot_path(case)
        assert path.name in declared
        assert hashlib.sha256(path.read_bytes()).hexdigest() == declared[path.name]
