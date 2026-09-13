import json
from pathlib import Path

from engine.build import build
from tools.generate_data import IMAGES, POSITIONS, SHI, TRIGRAMS, generate_bagong, generate_changsheng

ROOT = Path(__file__).resolve().parents[1]


def test_64_hexagrams_generated_and_complete():
    rows = generate_bagong()
    assert len(rows) == 64
    assert len({tuple(row["lines"]) for row in rows}) == 64
    assert [row["hexagram_id"] for row in rows] == list(range(1, 65))
    # No supplied published golden file is present; human comparison remains pending.
    print("待人手核對：未提供已出版《八宮世應圖》對照檔")


def test_乾坤_palace_pairs_are_opposites():
    """Sourced external constraint: each paired 乾/坤 palace hexagram is 旁通."""
    rows = generate_bagong()
    qian = [r for r in rows if r["palace"] == "乾"]
    kun = [r for r in rows if r["palace"] == "坤"]
    assert all(all(a + b == 1 for a, b in zip(x["lines"], y["lines"])) for x, y in zip(qian, kun))


def test_derived_opposite_palace_pairs():
    """Derived, not sourced: the other three trigram-opposite pairs behave likewise."""
    rows = generate_bagong()
    for left, right in (("震", "巽"), ("坎", "離"), ("艮", "兌")):
        a = [r for r in rows if r["palace"] == left]
        b = [r for r in rows if r["palace"] == right]
        assert all(all(x + y == 1 for x, y in zip(p["lines"], q["lines"])) for p, q in zip(a, b))


def test_tian_feng_gou_sourced_najia_case():
    """Sourced hexagram/najia case; six-relative and hidden values are rule-derived."""
    result = build([0, 1, 1, 1, 1, 1])
    assert result["palace"] == "乾"
    assert result["palace_element"] == "金"
    assert result["position"] == "一世"
    assert result["shi"] == 1 and result["ying"] == 4
    assert [(x["branch"], x["element"]) for x in result["lines_detail"]] == [
        ("丑", "土"), ("亥", "水"), ("酉", "金"),
        ("午", "火"), ("申", "金"), ("戌", "土")]
    assert [x["six_relative"] for x in result["lines_detail"]] == [
        "父母", "子孫", "兄弟", "官鬼", "兄弟", "父母"]
    assert result["hidden"] == {
        "六親": "妻財", "branch": "寅", "element": "木", "position": 2,
        "flying_branch": "亥", "flying_element": "水", "rule_id": "R-L1-08a",
        "伏神能否為用": "TODO: pending R-L1-08b verification"}


def test_bagong_structural_invariants():
    """Self-consistency constraints, not external textual evidence."""
    rows = generate_bagong()
    assert all(sum(r["lines"]) >= 0 for r in rows)
    for palace in ("乾", "坎", "艮", "震", "巽", "離", "坤", "兌"):
        group = [r for r in rows if r["palace"] == palace]
        assert len(group) == 8
        assert tuple(group[0]["lines"][:3]) == tuple(group[0]["lines"][3:])
        assert tuple(group[7]["lines"][:3]) == tuple(TRIGRAMS[palace])
        assert sum(a != b for a, b in zip(group[5]["lines"], group[6]["lines"])) == 1
    assert len({tuple(r["lines"]) for r in rows}) == 64


def test_shi_ying_formula_for_all_eight_positions():
    rows = generate_bagong()
    for position, shi in zip(POSITIONS, SHI):
        row = next(r for r in rows if r["position"] == position)
        assert row["shi"] == shi
        assert row["ying"] == ((shi - 1 + 3) % 6) + 1


def test_najia_round_trip_for_sample_hexagrams():
    rows = generate_bagong()
    for row in (rows[0], rows[7], rows[16], rows[31], rows[63]):
        result = build(row["lines"])
        assert [line["branch"] for line in result["lines_detail"]]
        assert result["palace"] == row["palace"]
        assert tuple(result["lines"]) == tuple(row["lines"])


def test_changsheng_earth_has_two_tracks():
    table = generate_changsheng()
    assert set(table["土"]) == {"track_A", "track_B"}
    assert table["土"]["track_A"]["墓"] == "辰"
    assert table["土"]["track_B"]["墓"] == "戌"


def test_generated_files_have_expected_cardinality():
    assert len(json.loads((ROOT / "data" / "mechanical" / "bagong_64.json").read_text(encoding="utf-8"))) == 64
    assert len(json.loads((ROOT / "data" / "mechanical" / "najia.json").read_text(encoding="utf-8"))) == 48
