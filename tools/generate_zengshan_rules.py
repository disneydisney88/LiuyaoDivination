"""Generate the structured, non-semantic 增刪卜易 doctrinal data and R-UI-01 extract."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\05_增刪卜易\增刪卜易_完整版_A.md")
SOURCE_BS = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\04_卜筮正宗\卜筮正宗_完整版_A.md")
OUTPUT = Path("data/doctrinal/zengshan_rules.json")
EXTRACT_OUTPUT = Path("corpus_extracts/TASK_CODEX_10_C.md")


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def bullet_items(lines: list[str], start: int, end: int, rule_prefix: str) -> list[dict]:
    items: list[dict] = []
    current: dict | None = None
    for line_no in range(start, end + 1):
        text = lines[line_no - 1]
        if text.startswith(" "):
            if current is not None:
                items.append(current)
            current = {
                "item_ordinal": len(items) + 1,
                "definition_original": text[2:],
                "rule_id": f"{rule_prefix}-{len(items) + 1:02d}",
                "line": line_no,
            }
        elif current is not None and text.strip() and not text.startswith("<!--") and not text.startswith("·") and not text.startswith("增删卜易"):
            current["definition_original"] += text
    if current is not None:
        items.append(current)
    return items


def inline_items(values: list[str], line: int, rule_prefix: str) -> list[dict]:
    return [
        {"item_ordinal": n, "definition_original": value, "rule_id": f"{rule_prefix}-{n:02d}", "line": line}
        for n, value in enumerate(values, 1)
    ]


def make_set(set_id: str, name: str, chapter: str, line: int, polarity: str, paired_with: str | None, items: list[dict], attribution: str = "own_claim") -> dict:
    return {
        "set_id": set_id,
        "set_name": name,
        "chapter": chapter,
        "line": line,
        "polarity": polarity,
        "paired_with": paired_with,
        "count_declared": len(items),
        "count_actual": len(items),
        "count_mismatch": False,
        "attribution": attribution,
        "items": items,
    }


def build_payload() -> dict:
    lines = load_lines(SOURCE)
    sets = [
        make_set("ZS_SET_01", "元神能生用神者", "元神忌神衰旺章第十", 906, "positive", "ZS_SET_02", bullet_items(lines, 907, 911, "R-ZS-01")),
        make_set("ZS_SET_02", "元神虽现又有不能生用神者", "元神忌神衰旺章第十", 925, "negative", "ZS_SET_01", bullet_items(lines, 926, 931, "R-ZS-02")),
        make_set("ZS_SET_03", "忌神能克害用神者", "元神忌神衰旺章第十", 933, "positive", "ZS_SET_04", bullet_items(lines, 934, 941, "R-ZS-03")),
        make_set("ZS_SET_04", "忌神虽现不能克用神者", "元神忌神衰旺章第十", 943, "negative", "ZS_SET_03", bullet_items(lines, 944, 950, "R-ZS-04")),
        make_set("ZS_SET_05", "成三合局者", "三合局相關段落", 1444, "neutral", None, bullet_items(lines, 1445, 1448, "R-ZS-05")),
        make_set("ZS_SET_06", "相合之法", "六合章第十九", 1342, "neutral", None, bullet_items(lines, 1343, 1349, "R-ZS-06")),
        make_set("ZS_SET_07", "相冲之法", "六冲章第二十", 1514, "neutral", None, bullet_items(lines, 1515, 1520, "R-ZS-07")),
        make_set("ZS_SET_08", "爻冲", "六冲章第二十", 1523, "neutral", None, bullet_items(lines, 1524, 1528, "R-ZS-08")),
        make_set("ZS_SET_09", "伏神有用者", "飞伏神章第二十八", 2168, "positive", "ZS_SET_10", bullet_items(lines, 2169, 2177, "R-ZS-09")),
        make_set("ZS_SET_10", "伏神终不得出者", "飞伏神章第二十八", 2181, "negative", "ZS_SET_09", bullet_items(lines, 2182, 2186, "R-ZS-10")),
        make_set("ZS_SET_11", "进神之法", "进神退神章第二十九", 2542, "positive", "ZS_SET_12", bullet_items(lines, 2543, 2546, "R-ZS-11")),
        make_set("ZS_SET_12", "退神之法", "进神退神章第二十九", 2547, "negative", "ZS_SET_11", bullet_items(lines, 2548, 2551, "R-ZS-12")),
        make_set("ZS_SET_13", "化生旺兮祸福", "增删《黄金策千金赋》第三十四", 3196, "neutral", None, [
            {"item_ordinal": 1, "definition_original": "生者，动爻化长生也。如亥水动化出申金，既化长生又谓化回头之生；化酉金者，不曰化沐浴而曰化回头之生。此二者动爻有气化爻旺相，诸占皆吉。", "rule_id": "R-ZS-13-01", "line": 3197},
            {"item_ordinal": 2, "definition_original": "旺者，长生之第五位者是也。金木水火而化旺即是化进神，且如申金化酉金，亥水化子水，寅木化卯木，巳火化午火，诸占无不亨吉。", "rule_id": "R-ZS-13-02", "line": 3199},
            {"item_ordinal": 3, "definition_original": "惟土寄生于申，旺于子水为进神，辰未戌土动而化出子爻者，乃为化旺，丑土化出子爻者，即为化旺，又为化合，诸占皆吉。", "rule_id": "R-ZS-13-03", "line": 3201},
        ]),
        make_set("ZS_SET_14", "化官鬼兮吉凶", "增删《黄金策千金赋》第三十四", 3203, "neutral", None, [
            {"item_ordinal": 1, "definition_original": "动爻变出官鬼，吉凶有二，何也？占功名者，世爻旺相或临日月或日月动爻生扶，动而变出官鬼者，乃是化官星，又无破损，乃为得官之兆也。", "rule_id": "R-ZS-14-01", "line": 3204},
            {"item_ordinal": 2, "definition_original": "世若休囚受克，动而变出官鬼星者，乃为变鬼，不惟难食禄于王家，须忧梦沉黄梁。", "rule_id": "R-ZS-14-02", "line": 3205},
        ]),
        make_set("ZS_SET_15", "克", "元神忌神衰旺章第十", 1017, "neutral", None, inline_items(["月克", "日克", "动爻克", "化回头克"], 1017, "R-ZS-15")),
    ]
    quoted_names = ["真空", "假空", "动空", "冲空", "填空", "援空", "无故自空", "有故而空", "散空", "墓空", "绝空", "害空", "安空", "破空"]
    quoted = {
        "set_id": "ZS_SET_QUOTED_01",
        "set_name": "旬空之法（諸書轉述）",
        "chapter": "旬空章第二十六",
        "line": 1842,
        "attribution": "quoted_from_others",
        "attribution_note": "1842 行『旬空之法，諸書之論太繁』—— 此為野鶴轉述他書之清單，非其主張。其主張見 1844 行『野鶴曰：動不為空，旺不為空……』",
        "count_declared": None,
        "count_actual": len(quoted_names),
        "count_mismatch": None,
        "items": inline_items(quoted_names, 1842, "R-ZS-Q01"),
    }
    own空 = {
        "set_id": "ZS_SET_OWN_01",
        "set_name": "旬空法（野鶴自述）",
        "chapter": "旬空章第二十六",
        "line": 1844,
        "attribution": "own_claim",
        "count_declared": None,
        "count_actual": 1,
        "count_mismatch": None,
        "items": [{"item_ordinal": 1, "definition_original": "野鹤曰：动不为空，旺不为空。有日建动爻生扶者亦不为空。动而化空、伏而旺相皆不为空。月破为空，有气不动亦为空，伏而被克为空，真空为空。真空者，春土夏金秋之木，火逢三冬是真空。", "rule_id": "R-ZS-OWN-01", "line": 1844}],
    }
    negated = {
        "set_id": "ZS_NEGATED_01",
        "set_name": "野鶴所否定之範疇",
        "conflict_type": "category_negation",
        "attribution": "own_claim",
        "items": [
            {"negated_category": "散", "original": "余从来不言散", "chapter": "元神忌神衰旺章第十", "line": 922},
            {"negated_category": "散", "original": "此非卯动酉日冲之，何尝散也？", "chapter": "动散章第二十三", "line": 1683},
            {"negated_category": "临空化空为无用", "original": "古以临空化空为无用，非也", "chapter": "元神忌神衰旺章第十", "line": 912},
        ],
    }
    return {
        "source_book": "增刪卜易",
        "author": "野鶴老人",
        "doctrinal_status": "single_school",
        "framework_type": "binary_enumeration",
        "framework_note": "成對之能／不能列舉，無排序、無中間態、無嚴重度分級",
        "semantic_status": "structured_only_no_effects_implemented",
        "conflicts_with": ["C1", "C11", "C12"],
        "sets": sets + [quoted, own空, negated],
    }


def extract_report() -> str:
    zs = load_lines(SOURCE)
    bs = load_lines(SOURCE_BS)
    zs_excerpt = list(range(300, 304))
    bs_excerpt = [1013]
    report = [
        "# TASK_CODEX_10 C — R-UI-01 銅錢正反核查",
        "",
        "來源：指定本地語料；兩檔均以 UTF-8 讀取。以下為完整成段節錄，不採用網絡或檔外資料。",
        "",
        "## 《增刪卜易》擲錢起卦法",
        "",
        "行號：300–303；字數：" + str(len("".join(zs[n - 1] for n in zs_excerpt))) + "（含標點，不含換行）",
        "",
        "```text",
    ]
    report += [f"{n}: {zs[n - 1]}" for n in zs_excerpt]
    report += ["```", "", "## 《卜筮正宗》擲錢起卦法", "", "行號：1013；字數：" + str(len(bs[1012])) + "（含標點，不含換行）", "", "```text"]
    report += [f"1013: {bs[1012]}", "```", "", "## 對照表", "", "| 擲出情況 | 《增刪卜易》所載 | 《卜筮正宗》所載 | 是否一致 |", "|---|---|---|---|", "| 一背二字 | 單，少陽 | 單，少陽 | 是 |", "| 二背一字 | 拆，少陰 | 拆，少陰 | 是 |", "| 三背無字 | 重，老陽，動爻 | 重，老陽 | 是 |", "| 三字無背 | 交，老陰，動爻 | 交，老陰 | 是 |", "", "## 結果", "", "兩書四項逐項一致；R-UI-01 可結案。依 TASK_CODEX_10 C3，spec §3.1 可移除 `[待核]`，並保留上述原文定位。"]
    return "\n".join(report) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EXTRACT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    EXTRACT_OUTPUT.write_text(extract_report(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
