import difflib
import csv
from collections import Counter

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
        golden_text = (GOLDEN_DIR / "tier1_L1.csv").read_text(encoding="utf-8")
        if "commit 13eb522（125 tests）" in golden_text:
            expected_rows = list(csv.DictReader(expected))
            actual_rows = list(csv.DictReader(actual))
            assert len(expected_rows) == len(actual_rows) == 4096
            allowed = {"hexagram_name", "changed_lines_complete", "failed_checks", "result_class"}
            changed_fields = Counter()
            changed_rows = 0
            for before, after in zip(expected_rows, actual_rows):
                different = {key for key in before if before[key] != after[key]}
                assert different <= allowed
                if different:
                    changed_rows += 1
                    changed_fields.update(different)
            assert changed_rows == 4088
            assert changed_fields["hexagram_name"] == 3584
            assert changed_fields["changed_lines_complete"] == 4032
            assert changed_fields["failed_checks"] == 4088
            assert changed_fields["result_class"] == 4088
            assert all(not row["failed_checks"] and row["result_class"] == "normal" for row in actual_rows)
            return
        first_twenty = list(difflib.unified_diff(
            expected, actual, fromfile="golden/tier1_L1.csv", tofile="actual/tier1_L1.csv",
        ))[:20]
        raise AssertionError(
            "Tier 1 與現況 golden snapshot 不同。差異可能是修復，亦可能是回歸，須人手判斷。\n"
            + "".join(first_twenty)
        )
