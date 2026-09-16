"""Keep TASK_CODEX_26 H's demonstrated detection paths executable."""
from tools.snapshot_self_test import self_test_results


def test_all_eleven_known_failure_conditions_are_detected_in_memory():
    results = self_test_results()
    assert len(results) == 11
    assert all(result[-1] for result in results)
