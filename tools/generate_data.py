"""Generate the L1 data files from the rules in SPEC_LIUYAO_v0.2.md."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Bits are in 初爻 -> 上爻 order.  These are the eight canonical trigrams,
# used as input atoms; the 64-hexagram table itself is never hand enumerated.
TRIGRAMS = {
    "乾": (1, 1, 1), "兌": (1, 1, 0), "離": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}
IMAGES = {"乾": "天", "兌": "澤", "離": "火", "震": "雷",
          "巽": "風", "坎": "水", "艮": "山", "坤": "地"}
PALACE_ORDER = ("乾", "坎", "艮", "震", "巽", "離", "坤", "兌")
ELEMENTS = {"乾": "金", "兌": "金", "震": "木", "巽": "木",
            "坎": "水", "離": "火", "艮": "土", "坤": "土"}
POSITIONS = ("本宮", "一世", "二世", "三世", "四世", "五世", "遊魂", "歸魂")
SHI = (6, 1, 2, 3, 4, 5, 4, 3)


def flip(lines: tuple[int, ...], index: int) -> tuple[int, ...]:
    result = list(lines)
    result[index] ^= 1
    return tuple(result)


def palace_sequence(palace: str) -> list[tuple[int, ...]]:
    """R-L1-02 sequence, including the two non-linear final steps."""
    pure = TRIGRAMS[palace] * 2
    result = [pure]
    current = pure
    for index in range(5):
        current = flip(current, index)
        result.append(current)
    current = flip(current, 3)  # 遊魂: fourth line back to original polarity
    result.append(current)
    current = tuple(TRIGRAMS[palace]) + tuple(TRIGRAMS[palace])
    # 歸魂 is the 游魂 lower trigram changed back to the palace lower trigram.
    result.append(tuple(TRIGRAMS[palace]) + tuple(result[-1][3:]))
    return result


def trigram_name(bits: tuple[int, ...]) -> str:
    return next(name for name, value in TRIGRAMS.items() if value == bits)


def hexagram_name(lines: tuple[int, ...]) -> str:
    lower, upper = trigram_name(lines[:3]), trigram_name(lines[3:])
    if lower == upper:
        return f"{lower}為{IMAGES[lower]}"
    return f"{IMAGES[upper]}{IMAGES[lower]}"


def generate_bagong() -> list[dict]:
    records = []
    hexagram_id = 1
    for palace in PALACE_ORDER:
        for lines, position, shi in zip(palace_sequence(palace), POSITIONS, SHI):
            records.append({
                "hexagram_id": hexagram_id,
                "name": hexagram_name(lines),
                "lines": list(lines),
                "palace": palace,
                "palace_element": ELEMENTS[palace],
                "position": position,
                "shi": shi,
                "ying": ((shi - 1 + 3) % 6) + 1,
            })
            hexagram_id += 1
    return records


NAJIA_STARTS = {
    "乾": {"inner": ("甲", "子"), "outer": ("壬", "午")},
    "坎": {"inner": ("戊", "寅"), "outer": ("戊", "申")},
    "艮": {"inner": ("丙", "辰"), "outer": ("丙", "戌")},
    "震": {"inner": ("庚", "子"), "outer": ("庚", "午")},
    "巽": {"inner": ("辛", "丑"), "outer": ("辛", "未")},
    "離": {"inner": ("己", "卯"), "outer": ("己", "酉")},
    "坤": {"inner": ("乙", "未"), "outer": ("癸", "丑")},
    "兌": {"inner": ("丁", "巳"), "outer": ("丁", "亥")},
}
YANG = {"乾", "坎", "艮", "震"}
BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")


def najia_branch_sequence(start: str, yang: bool) -> tuple[str, ...]:
    step = 2 if yang else -2
    start_index = BRANCHES.index(start)
    return tuple(BRANCHES[(start_index + step * i) % 12] for i in range(3))


def generate_najia() -> list[dict]:
    rows = []
    for trigram, sides in NAJIA_STARTS.items():
        for side in ("inner", "outer"):
            stem, start = sides[side]
            for line, branch in enumerate(najia_branch_sequence(start, trigram in YANG), 1):
                rows.append({"trigram": trigram, "side": side, "line": line,
                             "stem": stem, "branch": branch,
                             "used_in_relations": False})
    return rows


def generate_changsheng() -> dict:
    # The non-earth tracks are intentionally kept structurally identical.
    single = {
        "金": {"track_A": {"長生": "巳", "墓": "丑", "source": "spec §7 (single track)", "rule_id": "R-CS-金-A"}},
        "水": {"track_A": {"長生": "申", "墓": "辰", "source": "spec §7 (single track)", "rule_id": "R-CS-水-A"}},
        "木": {"track_A": {"長生": "亥", "墓": "未", "source": "spec §7 (single track)", "rule_id": "R-CS-木-A"}},
        "火": {"track_A": {"長生": "寅", "墓": "戌", "source": "spec §7 (single track)", "rule_id": "R-CS-火-A"}},
    }
    rules = {**single, "土": {
        "track_A": {"長生": "申", "墓": "辰", "source": "卜筮正宗（通行說）", "rule_id": "R-CS-土-A"},
        "track_B": {"長生": "寅", "墓": "戌", "source": "火土同源說，散見卜筮全書／易冒", "rule_id": "R-CS-土-B"},
    }}
    return rules


def dump(name: str, value: object) -> None:
    path = DATA / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    dump("mechanical/bagong_64.json", generate_bagong())
    dump("mechanical/najia.json", generate_najia())
    dump("doctrinal/changsheng_12gong.json", {
        "source_book": "multiple",
        "doctrinal_status": "multiple_schools",
        "semantic_status": "structured_only_no_effects_implemented",
        "conflicts_with": ["C5"],
        "rules": generate_changsheng(),
    })
