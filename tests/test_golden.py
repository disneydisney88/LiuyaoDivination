import json
from pathlib import Path
from random import Random

from engine.build import build
from engine.pipeline import build_case_state
from tools.generate_data import IMAGES, POSITIONS, SHI, TRIGRAMS, generate_bagong, generate_changsheng, trigram_name

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
    assert result["hidden"] == [{
        "six_relative": "妻財", "branch": "寅", "element": "木", "position": 2,
        "flying_branch": "亥", "flying_element": "水", "rule_id": "R-L1-08a",
        "can_be_yongshen_status": "各家未有定論（R-L1-08b 待核，現僅得《易冒》一方原文）"}]


def test_build_all_64_static_and_random_moving_samples_do_not_raise():
    rows = generate_bagong()
    for row in rows:
        assert build(row["lines"])["lines"] == row["lines"]

    # Moving/old coin values normalize to the same six yin/yang inputs accepted
    # by build().  Exercise a deterministic sample across hexagrams and masks.
    random = Random(108)
    for _ in range(256):
        row = random.choice(rows)
        moving_mask = random.randrange(1 << 6)
        coin_counts = []
        for index, line in enumerate(row["lines"]):
            moving = bool(moving_mask & (1 << index))
            coin_counts.append(3 if line and moving else 1 if line else 0 if moving else 2)
        normalized = [1 if count in (1, 3) else 0 for count in coin_counts]
        assert build(normalized)["lines"] == row["lines"]


def test_hidden_is_always_a_list_and_static_distribution_is_stable():
    lengths = [len(build(row["lines"])["hidden"]) for row in generate_bagong()]
    assert all(isinstance(build(row["lines"])["hidden"], list) for row in generate_bagong())
    assert {length: lengths.count(length) for length in range(5)} == {
        0: 20, 1: 32, 2: 12, 3: 0, 4: 0,
    }


def test_two_absent_six_relatives_each_have_hidden_and_flying_lines():
    result = build([0, 0, 1, 1, 1, 1])
    assert result["hidden"] == [
        {
            "six_relative": "妻財", "branch": "寅", "element": "木", "position": 2,
            "flying_branch": "午", "flying_element": "火", "rule_id": "R-L1-08a",
            "can_be_yongshen_status": "各家未有定論（R-L1-08b 待核，現僅得《易冒》一方原文）",
        },
        {
            "six_relative": "子孫", "branch": "子", "element": "水", "position": 1,
            "flying_branch": "辰", "flying_element": "土", "rule_id": "R-L1-08a",
            "can_be_yongshen_status": "各家未有定論（R-L1-08b 待核，現僅得《易冒》一方原文）",
        },
    ]


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


def test_all_hexagram_names_are_complete_and_not_trigram_pair_only():
    rows = generate_bagong()
    for row in rows:
        assert len(row["name"]) >= 3
        lower = trigram_name(tuple(row["lines"][:3]))
        upper = trigram_name(tuple(row["lines"][3:]))
        images = {"乾": "天", "兌": "澤", "離": "火", "震": "雷",
                  "巽": "風", "坎": "水", "艮": "山", "坤": "地"}
        assert row["name"] != images[upper] + images[lower]


def test_moving_case_has_complete_changed_hexagram_lines():
    state = build_case_state(
        lines=[0, 1, 0, 0, 1, 0], cast_datetime="2026-09-13T15:49",
        moving_positions=[1, 3, 6],
    )
    changed = state["changed_chart"]
    assert changed is not None
    assert len(changed["lines"]) == 6
    assert len(changed["lines_detail"]) == 6
    assert all(
        line.get("branch") and line.get("element") and line.get("six_relative")
        for line in changed["lines_detail"]
    )
