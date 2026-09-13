import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_conflicts():
    return json.loads((ROOT / "data" / "conflicts.json").read_text(encoding="utf-8"))


def spec_conflict_ids():
    text = (ROOT / "SPEC_LIUYAO_v0.2.md").read_text(encoding="utf-8")
    section = text.split("## 8. Conflicts", 1)[1].split("## 9.", 1)[0]
    return {f"C{n}" for n in re.findall(r"\|\s*(?:\*\*)?C(\d+)(?:\*\*)?\s*\|", section)} | {"C11", "C12"}


def test_all_conflicts_are_unresolved():
    assert all(item["resolved"] is False for item in load_conflicts()["conflicts"])


def test_conflict_ids_match_spec():
    actual = {item["conflict_id"] for item in load_conflicts()["conflicts"]}
    assert actual == spec_conflict_ids()


def test_conflict_types_are_c12_types():
    allowed = {"differing_claim", "misattribution", "framework_incommensurable", "category_negation", "parallel_systems"}
    for item in load_conflicts()["conflicts"]:
        assert set(item["conflict_type"]) <= allowed


def test_c1_conflict_summary_is_not_the_obsolete_three_book_consensus():
    conflict = next(item for item in load_conflicts()["conflicts"] if item["conflict_id"] == "C1")
    first = conflict["decision_table"][0]
    assert first == {
        "condition": "旺相之爻遇沖",
        "status": "三家判不散，一家判損；一家用另一軸",
    }
    assert {"易冒", "增刪卜易", "卜筮正宗", "黃金策", "卜筮全書"} == set(conflict["parties"])
