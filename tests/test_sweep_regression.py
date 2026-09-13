import difflib

from tools.sweep import GOLDEN_DIR, run_tier1, strip_golden_header


def test_tier1_matches_current_state_golden_snapshot(tmp_path):
    """Current-state regression only: a diff may be a repair or a regression."""
    actual_path = tmp_path / "tier1_L1.csv"
    run_tier1(actual_path)
    actual = actual_path.read_text(encoding="utf-8").splitlines(keepends=True)
    expected = strip_golden_header(
        (GOLDEN_DIR / "tier1_L1.csv").read_text(encoding="utf-8")
    ).splitlines(keepends=True)
    if actual != expected:
        first_twenty = list(difflib.unified_diff(
            expected, actual, fromfile="golden/tier1_L1.csv", tofile="actual/tier1_L1.csv",
        ))[:20]
        raise AssertionError(
            "Tier 1 與現況 golden snapshot 不同。差異可能是修復，亦可能是回歸，須人手判斷。\n"
            + "".join(first_twenty)
        )
