"""Generate the deterministic data artifacts for TASK_CODEX_22.

The script reads settled source-backed material already in the repository and
writes only derived JSON.  Y-R10 and the seven-status cardinality are fixed
by the recorded human decisions, including its explicit null cross-reference.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.semantics import calculate_coverage


DOCTRINAL = ROOT / "data" / "doctrinal"
TABLES = ROOT / "data" / "decision_tables"
FHL_PRIMARY = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\02_火珠林\火珠林.txt")

BOOKS = [
    {"book_id": "yimao", "name": "易冒"},
    {"book_id": "zengshan", "name": "增刪卜易"},
    {"book_id": "buzhengzong", "name": "卜筮正宗"},
    {"book_id": "huozhulin", "name": "火珠林"},
    {"book_id": "huangjin_ce", "name": "黃金策"},
    {"book_id": "buzhequanshu", "name": "卜筮全書"},
    {"book_id": "jing_shi_yizhuan", "name": "京氏易傳"},
    {"book_id": "yiyin", "name": "易隱"},
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def corpus_line(lines: list[str], number: int) -> str:
    return lines[number - 1].rstrip()


def corpus_block(lines: list[str], start: int, end: int) -> str:
    return "\n".join(corpus_line(lines, number) for number in range(start, end + 1)).strip()


def cell(book_id: str, status: str, *, verdict: str | None = None,
         source: str | None = None, original: str | None = None,
         rule_id: str | None = None, search_note: str | None = None,
         cell_note: str | None = None, axis_note: str | None = None,
         axis_original: str | None = None, axis_source: str | None = None,
         cross_reference: str | None = None, absence_note: str | None = None,
         exclusion_original: str | None = None, exclusion_source: str | None = None,
         term_note: str | None = None,
         include_null_cross_reference: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"book_id": book_id, "status": status}
    if status in {
        "addressed", "not_addressed", "category_negated", "concept_absent",
        "explicit_exclusion", "different_axis",
    }:
        result["verdict"] = verdict
    for key, value in {
        "source": source,
        "original": original,
        "rule_id": rule_id,
        "search_note": search_note,
        "cell_note": cell_note,
        "axis_note": axis_note,
        "axis_original": axis_original,
        "axis_source": axis_source,
        "absence_note": absence_note,
        "exclusion_original": exclusion_original,
        "exclusion_source": exclusion_source,
        "term_note": term_note,
    }.items():
        if value is not None:
            result[key] = value
    if cross_reference is not None or include_null_cross_reference:
        result["cross_reference"] = cross_reference
    return result


def fhl_k_axis_cell() -> dict[str, Any]:
    return cell(
        "huozhulin", "different_axis",
        axis_note="本書判空看世／應／官／財等爻位，非空爻之旺相、休囚、動靜等狀態；爻位軸空亡表未建（P-050）。",
        axis_original="世应空亡，主和；世空我军弱；应空征兵退。",
        axis_source="火珠林 991",
        cross_reference="P-050",
    )


def fhl_chong_axis_cell() -> dict[str, Any]:
    return cell(
        "huozhulin", "different_axis",
        axis_note="散由獨發與世動生，非由沖生。",
        axis_original="子孙独发，为退为散；",
        axis_source="火珠林 262；752",
        cross_reference="C1／C15",
    )


def not_collected(book_id: str) -> dict[str, Any]:
    return cell(book_id, "not_collected")


def k_table() -> dict[str, Any]:
    """Build the settled 10×8 K table from TASK_23 material."""
    rows = [
        (
            "K-R1", "旺相之爻值旬空", [
                cell("yimao", "addressed", verdict="有用", source="旬空章第二十六 400（十三法）", original="旺相之爻值空，为旺相空。", rule_id="R-YM-10-04"),
                cell("zengshan", "addressed", verdict="不為空", source="旬空章第二十六 1844", original="旺不为空。", rule_id="R-ZS-VOID-01"),
                cell("buzhengzong", "addressed", verdict="到底有用", source="旬空論第十 2699", original="如旺相旬空……此等旬空到底有用。", rule_id="R-BZ-02-P-01"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="不空", source="千金賦 36", original="带旺匪空。", rule_id="R-HJ-K-01"),
                cell("buzhequanshu", "addressed", verdict="可用", source="總斷千金賦 5558", original="空中不受伤克，反有可成之机。", rule_id="R-BQ-02-01", cell_note="原文不單列旺相為條件，保留其與本格範圍不同。"),
            ],
        ),
        (
            "K-R2", "休囚之爻值旬空", [
                cell("yimao", "addressed", verdict="不全填實", source="旬空章第二十六 400（十三法）", original="若遇休囚伤克，乃谓不全填实也。", rule_id="R-YM-10-03"),
                cell("zengshan", "addressed", verdict="空", source="旬空章第二十六 1845", original="有气不动亦为空。", rule_id="R-ZS-VOID-02", cell_note="原文以有氣／不動連帶切分，非單列休囚。"),
                cell("buzhengzong", "addressed", verdict="真空到底空", source="旬空論第十 2699", original="休囚安静……谓之真空到底空矣！", rule_id="R-BZ-02-N-01", cell_note="原文連帶安靜條件。"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="可吉", source="千金賦 38", original="有助有扶，衰弱休囚亦吉。", rule_id="R-HJ-K-02", cell_note="原文連帶有助有扶。"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 已以休囚、空亡、旬空交叉檢索；未定位以休囚為本格直接條件之原文。"),
            ],
        ),
        (
            "K-R3", "動爻值旬空", [
                cell("yimao", "addressed", verdict="反為動", source="旬空章第二十六 400（十三法）", original="动爻值空，谓动空，不惟不空，反为动也。", rule_id="R-YM-10-02"),
                cell("zengshan", "addressed", verdict="不為空", source="旬空章第二十六 1844", original="动不为空。", rule_id="R-ZS-VOID-03"),
                cell("buzhengzong", "addressed", verdict="到底有用", source="旬空論第十 2699", original="或休囚发动……此等旬空到底有用。", rule_id="R-BZ-02-P-02"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="凶咎", source="千金賦 32", original="自空化空，必成凶咎。", rule_id="R-HJ-K-03", cell_note="原文為自空化空，保留其比本格多出『化』的條件。"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 已檢索動、空亡、旬空；未定位單以動爻值旬空為條件的直接原文。"),
            ],
        ),
        (
            "K-R4", "靜爻值旬空", [
                cell("yimao", "not_addressed", search_note="TASK_23 於旬空章、類總章、日沖章交叉檢索動、靜、旬空，未定位直接條件。"),
                cell("zengshan", "addressed", verdict="空", source="旬空章第二十六 1845", original="有气不动亦为空。", rule_id="R-ZS-VOID-04"),
                cell("buzhengzong", "addressed", verdict="真空到底空", source="旬空論第十 2699", original="休囚安静……谓之真空到底空矣！", rule_id="R-BZ-02-N-01"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "not_addressed", search_note="TASK_23 全文交叉檢索動、靜、空亡、旬空，未定位直接條件。"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 定位六爻空亡歌按爻位列空亡，未另立靜爻分類。"),
            ],
        ),
        (
            "K-R5", "空爻遇日辰沖", [
                cell("yimao", "addressed", verdict="實", source="日沖章第二十七 415；旬空十三法 400", original="空爻遇冲谓之实。", rule_id="R-YM-09-03"),
                cell("zengshan", "addressed", verdict="沖空則實", source="日辰章 1246–1247", original="爻遇旬空，日辰冲起而有用，谓之冲空则实。", rule_id="R-ZS-VOID-05"),
                cell("buzhengzong", "not_addressed", search_note="TASK_23 檢索出旬、空爻遇沖、沖空、日辰沖，未定位直接對應原文。"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="有用", source="千金賦 30", original="空逢冲而有用。", rule_id="R-HJ-K-05"),
                cell("buzhequanshu", "addressed", verdict="不空", source="總斷千金賦 5461–5463", original="空亡……被日辰冲动，定有雨。", rule_id="R-BQ-05-02"),
            ],
        ),
        (
            "K-R6", "空爻得日月動爻生扶", [
                cell("yimao", "addressed", verdict="有用／不死", source="旬空章第二十六 400（十三法）", original="动爻日辰来生空爻，乃谓援空；日月动爻皆不来克空爻，乃谓安空。", rule_id="R-YM-10-07", cell_note="同書十三法之建空、援空、安空均與本格相關。"),
                cell("zengshan", "addressed", verdict="不為空", source="旬空章第二十六 1844", original="有日建动爻生扶者亦不为空。", rule_id="R-ZS-VOID-06"),
                cell("buzhengzong", "addressed", verdict="到底有用", source="旬空論第十 2699", original="日辰生扶、动爻生扶……此等旬空到底有用。", rule_id="R-BZ-02-P-03"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="亦吉", source="千金賦 38", original="有助有扶，衰弱休囚亦吉。", rule_id="R-HJ-K-06"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 保留日月動爻傷克與避凶空材料，未定位日月動爻生扶空爻的直接條件。"),
            ],
        ),
        (
            "K-R7", "伏神值旬空", [
                cell("yimao", "addressed", verdict="不現", source="旬空章第二十六 407–408", original="空在伏爻则不现。", rule_id="R-YM-VOID-07"),
                cell("zengshan", "addressed", verdict="出空之日則出", source="伏神章 2181–2188", original="凡伏神旺相而遇旬空，出空之日则出矣。", rule_id="R-ZS-VOID-07"),
                cell("buzhengzong", "addressed", verdict="到底有用／真空到底空", source="旬空論第十 2699", original="伏而旺相……此等旬空到底有用；爻克伏而被克……谓之真空到底空。", rule_id="R-BZ-02-P-06"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "addressed", verdict="事與願違／易於引拔", source="千金賦 44–48", original="伏居空地，事与愿违……空下伏神易于引拔。", rule_id="R-HJ-K-07", cell_note="同段對伏居空地與空下伏神有不同句式，並列保留。"),
                cell("buzhequanshu", "addressed", verdict="伏藏不論空亡", source="用爻空亡訣 3398", original="空在旁宫不断空，（即伏藏不论空亡也。）", rule_id="R-BQ-VOID-07"),
            ],
        ),
        (
            "K-R8", "出旬之後", [
                cell("yimao", "addressed", verdict="旬外實", source="類總章第四十一 692（八法）", original="日月生扶，谓之旺相空，旬内空而旬外实。", rule_id="R-YM-06-06"),
                cell("zengshan", "addressed", verdict="出旬而不空／到底之空", source="旬空章第二十六 1846–1847", original="卦吉者，许之出旬而不空；卦凶者，许之空矣。", rule_id="R-ZS-VOID-08"),
                cell("buzhengzong", "addressed", verdict="待出旬", source="旬空論第十 2699", original="此等旬空到底有用，不过待其出旬……", rule_id="R-BZ-02-P-01"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "not_addressed", search_note="TASK_23 搜尋出旬、出空、旬外及全文空亡材料，未定位直接原文。"),
                cell("buzhequanshu", "addressed", verdict="過旬即成", source="總斷千金賦 5560", original="即是不坏，但目下略阻，过旬即成。", rule_id="R-BQ-02-04"),
            ],
        ),
        (
            "K-R9", "空而逢月破", [
                cell("yimao", "addressed", verdict="所戒", source="旬空章第二十六 402（十三法）", original="月破值空，谓破空。", rule_id="R-YM-10-09"),
                cell("zengshan", "addressed", verdict="空", source="旬空章第二十六 1845", original="月破为空。", rule_id="R-ZS-VOID-09"),
                cell("buzhengzong", "addressed", verdict="真空到底空", source="旬空論第十 2699", original="静逢月破值此旬空者，谓之真空到底空矣！", rule_id="R-BZ-02-N-04"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "not_addressed", search_note="TASK_23 未定位空而逢月破的直接條件。"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 搜尋月破、空亡與旬空，未定位本格直接原文。"),
            ],
        ),
        (
            "K-R10", "空而逢絕", [
                cell("yimao", "addressed", verdict="所戒", source="旬空章第二十六 402（十三法）", original="绝于月为绝空。", rule_id="R-YM-10-10"),
                cell("zengshan", "not_addressed", search_note="TASK_23 未定位空而逢絕的直接條件；不以伏神墓絕材料頂替。"),
                cell("buzhengzong", "not_addressed", search_note="TASK_23 未定位空而逢絕的直接條件。"),
                fhl_k_axis_cell(),
                cell("huangjin_ce", "not_addressed", search_note="TASK_23 未定位空而逢絕的直接條件。"),
                cell("buzhequanshu", "not_addressed", search_note="TASK_23 未定位空而逢絕的直接條件。"),
            ],
        ),
    ]
    output_rows = []
    for row_id, condition, cells in rows:
        cells.extend(not_collected(book_id) for book_id in ("jing_shi_yizhuan", "yiyin"))
        row = {"row_id": row_id, "condition": condition, "cells": cells}
        if row_id == "K-R4":
            row["row_note"] = (
                "本格保留為本項目提問，但各書多連帶其他條件："
                "《增刪卜易》為『有氣不動』；《卜筮正宗》為『休囚安靜』；"
                "《卜筮全書》按爻位論空亡；《易冒》與《黃金策》未定位單列靜爻。"
                "『靜』本身可能非各家之切分維度。"
            )
        row.update(calculate_coverage(row, books_total=len(BOOKS)))
        output_rows.append(row)
    return {
        "table_id": "K",
        "title": "空亡之狀態材料",
        "axis_note": "單表：各家同以空之狀態為材料，但粒度不同；不作跨書效果裁決。",
        "books": BOOKS,
        "rows": output_rows,
    }


def update_yimao() -> None:
    path = DOCTRINAL / "yimao_rules.json"
    data = load_json(path)
    sets = {item["set_id"]: item for item in data["sets"]}
    thirteen = sets["YM_SET_10"]
    thirteen["source"] = "易冒"
    thirteen["chapter"] = "旬空章第二十六"
    valences = ("useful",) * 6 + ("not_dead",) * 2 + ("guarded_against",) * 5
    for item, valence in zip(thirteen["items"], valences, strict=True):
        item["valence"] = valence
    eight = sets["YM_SET_06"]
    eight["source"] = "易冒"
    eight["chapter"] = "類總章第四十一"
    if "YM_SET_12" not in sets:
        data["sets"].append({
            "set_id": "YM_SET_12", "set_name": "元忌喜忌", "source": "易冒",
            "chapter": "類總章第四十一", "line": 682,
            "count_declared": None, "count_actual": 2, "count_mismatch": None,
            "topic": "元神忌神傾向",
            "items": [
                {"item_ordinal": 1, "item_name": "忌", "definition_original": "有用神则必有忌神，忌则喜静、喜衰、喜制。", "rule_id": "R-YM-Y-01", "line": 682},
                {"item_ordinal": 2, "item_name": "元", "definition_original": "有用神必有元神，元则喜动、喜旺、喜生。", "rule_id": "R-YM-Y-02", "line": 682},
            ],
        })
    if "YM_SET_13" not in sets:
        data["sets"].append({
            "set_id": "YM_SET_13", "set_name": "絕生之法", "source": "易冒",
            "chapter": "絕生章第三十三", "line": 498,
            # The source contains two adjacent authorial groups (five and
            # three), not one author-declared eight-item list.
            "count_declared": None, "count_actual": 8, "count_mismatch": None,
            "topic": "絕處逢生",
            "note_original": "原文分『絕生之法有五』與『其不能生者有三』，兩組分立保存，未併入 Y 表。",
            "items": [
                {"item_ordinal": 1, "group": "絕生之法有五", "definition_original": "用神受日月之克，遇动爻之生，一也。", "rule_id": "R-YM-ABSOLUTE-01", "line": 500},
                {"item_ordinal": 2, "group": "絕生之法有五", "definition_original": "受动爻之克，遇变爻之生，一也。", "rule_id": "R-YM-ABSOLUTE-02", "line": 500},
                {"item_ordinal": 3, "group": "絕生之法有五", "definition_original": "受变爻之克，遇动爻之生，一也。", "rule_id": "R-YM-ABSOLUTE-03", "line": 500},
                {"item_ordinal": 4, "group": "絕生之法有五", "definition_original": "伏用受日月之克，遇飞爻动爻之生，一也。", "rule_id": "R-YM-ABSOLUTE-04", "line": 500},
                {"item_ordinal": 5, "group": "絕生之法有五", "definition_original": "伏用受飞爻动爻之克，遇日月之生，一也。", "rule_id": "R-YM-ABSOLUTE-05", "line": 500},
                {"item_ordinal": 6, "group": "其不能生者有三", "definition_original": "用神自受破散，不能生者一。", "rule_id": "R-YM-ABSOLUTE-06", "line": 501},
                {"item_ordinal": 7, "group": "其不能生者有三", "definition_original": "飞爻动爻生我者受破散，不能生者二。", "rule_id": "R-YM-ABSOLUTE-07", "line": 501},
                {"item_ordinal": 8, "group": "其不能生者有三", "definition_original": "变爻生我者受破绝，不能生者三。", "rule_id": "R-YM-ABSOLUTE-08", "line": 501},
            ],
        })
    absolute = next(item for item in data["sets"] if item["set_id"] == "YM_SET_13")
    # Preserve the source's two authorial lists rather than inventing a
    # single declaration of eight.
    absolute["count_declared"] = None
    absolute["count_actual"] = len(absolute["items"])
    absolute["count_mismatch"] = None
    write_json(path, data)


def update_y_material_catalogues() -> None:
    bz_path = DOCTRINAL / "buzhengzong_rules.json"
    bz = load_json(bz_path)
    if not any(item["set_id"] == "BZ_SET_YUAN_JI_01" for item in bz["sets"]):
        bz["sets"].append({
            "set_id": "BZ_SET_YUAN_JI_01", "set_name": "原忌仇神論第四",
            "chapter": "原忌仇神論第四", "line": 2625,
            "count_declared": None, "count_actual": 5, "count_mismatch": None,
            "enumeration_source": "editorial",
            "definition_original_full": (
                "凡占卦要知原神，先看用神何爻，生用神之爻即是原神也，如用神旬空、月破、衰弱，或伏藏不现，"
                "得原神动来生之，或日辰月建作原神生之，必待用爻出旬出破，得令值日，所求必遂矣。"
                "如用神旺相，原神休囚不动，或动而变墓变绝、变克、变破、变退，或被日辰月建克制，皆不能生用是用神根蒂被伤矣。\n\n"
                "凡占卦要知忌神，亦先看用神。克用神之爻即是忌神也，如忌神动来克用，而用爻出现不空则受克也……"
                "如日辰月建生扶忌神，或忌神叠叠克用，即使用神避空伏藏者，至出空出透时，便受其毒难免其究也。"
            ),
            "segmentation_note": "按原文中原神與忌神狀態連帶條件分項；不改寫原用語『原神』。",
            "items": [
                {"item_ordinal": 1, "line": 2627, "definition_original": "原神休囚不动", "rule_id": "R-BZ-Y-01", "enumeration_source": "editorial"},
                {"item_ordinal": 2, "line": 2627, "definition_original": "或动而变墓变绝、变克、变破、变退", "rule_id": "R-BZ-Y-02", "enumeration_source": "editorial"},
                {"item_ordinal": 3, "line": 2627, "definition_original": "或被日辰月建克制", "rule_id": "R-BZ-Y-03", "enumeration_source": "editorial"},
                {"item_ordinal": 4, "line": 2629, "definition_original": "如忌神动来克用，而用爻出现不空则受克也", "rule_id": "R-BZ-Y-04", "enumeration_source": "editorial"},
                {"item_ordinal": 5, "line": 2629, "definition_original": "如日辰月建生扶忌神，或忌神叠叠克用", "rule_id": "R-BZ-Y-05", "enumeration_source": "editorial"},
            ],
        })
    write_json(bz_path, bz)

    bq_path = DOCTRINAL / "buzhequanshu_rules.json"
    bq = load_json(bq_path)
    if not any(item["set_id"] == "BQ_SET_YUANCHEN_01" for item in bq["sets"]):
        bq["sets"].append({
            "set_id": "BQ_SET_YUANCHEN_01", "set_name": "元辰與忌神材料",
            "chapter": "碎金賦／用爻空亡訣", "line": 3350,
            "count_declared": None, "count_actual": 3, "count_mismatch": None,
            "enumeration_source": "editorial",
            "term_note": "本書用「元辰」，清代三家用「元神」。二者概念對應係編者判定，非原文明言。",
            "definition_original_full": (
                "看卦先须看忌神，忌神宜静不宜兴；忌神急要逢冲克，若遇生扶用受刑。"
                "（忌爻若遇生扶，用爻便受刑克。）\n\n"
                "元辰出现志扬扬，用伏藏兮也不妨。须要生扶兼旺相，最嫌冲克及刑伤。\n\n"
                "空在旁宫不断空，（即伏藏不论空亡也。）空如出现却为空；忌神最喜逢空吉，用与元辰不可空。"
            ),
            "items": [
                {"item_ordinal": 1, "line": 3350, "chapter": "卷四·用忌神訣", "definition_original": "看卦先须看忌神，忌神宜静不宜兴；忌神急要逢冲克，若遇生扶用受刑。", "rule_id": "R-BQ-Y-01", "enumeration_source": "editorial"},
                {"item_ordinal": 2, "line": 3355, "chapter": "卷四·元辰訣", "definition_original": "元辰出现志扬扬，用伏藏兮也不妨。须要生扶兼旺相，最嫌冲克及刑伤。", "rule_id": "R-BQ-Y-02", "enumeration_source": "editorial"},
                {"item_ordinal": 3, "line": 3398, "chapter": "卷四·用爻空亡訣", "definition_original": "忌神最喜逢空吉，用与元辰不可空。", "rule_id": "R-BQ-Y-03", "enumeration_source": "editorial"},
            ],
        })
    for source_set in bq["sets"]:
        if source_set["set_id"] == "BQ_SET_YUANCHEN_01":
            chapters = ("卷四·用忌神訣", "卷四·元辰訣", "卷四·用爻空亡訣")
            for item, chapter in zip(source_set["items"], chapters, strict=True):
                item["chapter"] = chapter
    write_json(bq_path, bq)


def fhl_set(*, set_id: str, set_name: str, chapter: str, lines: list[str],
            locations: list[int], items: list[tuple[str, int]],
            note: str | None = None, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "set_id": set_id,
        "set_name": set_name,
        "source": "火珠林",
        "chapter": chapter,
        "line": locations[0],
        "count_declared": None,
        "count_actual": len(items),
        "count_mismatch": None,
        "enumeration_source": "editorial",
        "definition_original_full": "\n\n".join(corpus_line(lines, number) for number in locations),
        "items": [
            {"item_ordinal": ordinal, "line": number, "chapter": chapter,
             "definition_original": corpus_line(lines, number),
             "rule_id": f"R-FHL-{set_id.removeprefix('FHL_SET_')}-{ordinal:02d}",
             "enumeration_source": "editorial"}
            for ordinal, (_, number) in enumerate(items, 1)
        ],
    }
    if note is not None:
        result["note"] = note
    result.update(extra)
    return result


def huozhulin_rules() -> dict[str, Any]:
    lines = FHL_PRIMARY.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1349:
        raise ValueError(f"unexpected 火珠林 primary corpus line count: {len(lines)}")
    sets = [
        fhl_set(set_id="FHL_SET_01", set_name="主輔二位", chapter="〈3·財官輔助〉", lines=lines,
                locations=list(range(52, 70)), items=[("用有輔助", 56), ("主輔與旺衰", 59), ("四季旺相休囚死", 62), ("四季旺相休囚死", 64), ("四季旺相休囚死", 66), ("四季旺相休囚死", 68)]),
        fhl_set(set_id="FHL_SET_02", set_name="明文排除第三位", chapter="〈6·公私用事〉", lines=lines,
                locations=list(range(115, 130)), items=[("設問", 125), ("拒絕", 126), ("方法界限", 128), ("方法界限", 129)],
                note="設問、拒絕及方法界限三要件的完整章段依原行保留。"),
        fhl_set(set_id="FHL_SET_03", set_name="亂動取旺爻", chapter="〈4·獨發亂動〉", lines=lines,
                locations=[94], items=[("亂動取旺爻", 94)]),
        fhl_set(set_id="FHL_SET_04", set_name="官用取官、私用取私", chapter="〈4·獨發亂動〉", lines=lines,
                locations=[97], items=[("取用", 97)], note="行 97 以『上篇』回指；其與〈3·財官輔助〉的文本連接仍為 P-052。"),
        fhl_set(set_id="FHL_SET_05", set_name="散由獨發與世動", chapter="散憂相關段", lines=lines,
                locations=[262, 752], items=[("獨發", 262), ("世動", 752)]),
        fhl_set(set_id="FHL_SET_06", set_name="空之爻位判準", chapter="各占例", lines=lines,
                locations=[523, 759, 914, 991], items=[("財爻空亡", 523), ("世空官鬼空", 759), ("官鬼空亡", 914), ("世應空亡", 991)],
                note="同書以世／應／官／財等爻位論空，非以空爻之旺衰動靜分格。"),
        fhl_set(set_id="FHL_SET_07", set_name="卦有三墓", chapter="墓例", lines=lines,
                locations=[768, 772, 773, 775, 777, 779], items=[("宮墓", 775), ("鬼墓", 777), ("財墓", 779)],
                note="行 768 主檔異文作『封有三墓：宫基、鬼墓』；三項依 772–779 問答保存，不校補正文。"),
        fhl_set(set_id="FHL_SET_08", set_name="八宗", chapter="〈63·易道心性〉", lines=lines,
                locations=[1315], items=[("克", 1315), ("合", 1315), ("刑", 1315), ("害", 1315), ("墓", 1315), ("旺", 1315), ("空", 1315), ("沖", 1315)],
                note="『克、合、刑、害、墓、旺、空、沖』為全書收束語；空與沖在此並列同級。", is_closing_summary=True),
        fhl_set(set_id="FHL_SET_09", set_name="凡祭賽有三", chapter="〈40·占祭賽〉", lines=lines,
                locations=[715], items=[("祀上帝", 715), ("神堂", 715), ("家廟", 715)]),
        fhl_set(set_id="FHL_SET_10", set_name="六親五件加卦身", chapter="〈2·六親根源〉", lines=lines,
                locations=[38, 39], items=[("父母", 38), ("兄弟", 38), ("妻財", 38), ("子孫", 38), ("官鬼", 38), ("卦身", 39)]),
        fhl_set(set_id="FHL_SET_11", set_name="書有三而異用", chapter="古注", lines=lines,
                locations=[14], items=[("連山", 14), ("歸藏", 14), ("周易", 14)]),
        fhl_set(set_id="FHL_SET_12", set_name="排除《元龜》卦身起法", chapter="〈2·六親根源〉", lines=lines,
                locations=[41, 42, 43, 44], items=[("元龜月卦起法", 42)],
                note="此為卦身起法之明文排除，不屬本包各決策表格位。", explicit_exclusion=True),
    ]
    return {
        "book_id": "huozhulin",
        "source_book": "火珠林",
        "era": "宋",
        "author": "託名麻衣道者",
        "attribution_status": "attributed",
        "framework_type": "two_role_category_then_strength",
        "framework_note": "主／輔二位，明文排除第三位（行 126）。取用兩步：事類定身份（官用父輔、財用子輔），旺衰定效力（值旺相為有氣，休囚為無氣）。散由獨發與世動生，非由沖生。空之判準為爻位（世／應／官／財），非爻之狀態",
        "enumeration_style": "none",
        "doctrinal_status": "single_school",
        "conflicts_with": ["C1", "C13", "C15", "K", "Y"],
        "semantic_status": "structured_only_no_effects_implemented",
        "corpus_path": "02_火珠林/火珠林_古本.txt",
        "corpus_cleaned": True,
        "cleaning_status": None,
        "provenance_strength": "weak",
        "provenance_note": "三方來源矛盾（P-037）：sidecar 稱衍生自維基文庫、CATALOG 稱出自 GitHub repo、檔內自稱 divinehere.com／mingtianji.com。三者互不相符，本項目禁止上網故未判定。主檔為 火珠林.txt（三檔中文字最完整：19 處多出、0 處脫文，且唯一有 sidecar）。已分離維基樣板 19 行",
        "variant_editions": {
            "note": "本書為八本中唯一有三個獨立版本可互校者",
            "cross_check": "三檔正文 90.3% 逐字相同，190 個差異區間。差異集中於〈占鬼神〉一篇（19 處多出中之 15 處）",
            "known_variants": "33 處用字相異已記入 sidecar，正文不動、不校補",
        },
        "sets": sets,
    }


def update_chong_tables() -> None:
    for filename in ("C1_chong_san.json", "C15_dongjing_axis.json"):
        path = TABLES / filename
        table = load_json(path)
        for row in table["rows"]:
            if filename == "C1_chong_san.json" and row["row_id"] == "C1-R2":
                # The former C1 cell only had a reference; retain the full
                # original in the cell so every ``addressed`` cell conforms
                # to the shared evidence schema.
                row["cells"] = [entry for entry in row["cells"] if entry["book_id"] != "zengshan"]
                row["cells"].append(cell(
                    "zengshan",
                    "addressed",
                    verdict="不散（休囚者間有沖散）",
                    original=(
                        "予屢試之，旺相者，沖之不散；有氣者，沖之不散；"
                        "休囚者，間有沖散，亦千百中之一二也。"
                    ),
                    source="《增刪卜易》〈動散章第二十三〉1673–1674",
                    cell_note="原文同時記錄旺相、有氣與休囚三種情況；本格保留其完整條件。",
                ))
            row["cells"] = [item for item in row["cells"] if item["book_id"] != "huozhulin"]
            row["cells"].insert(3, fhl_chong_axis_cell())
            for entry in row["cells"]:
                if entry["status"] == "not_addressed" and not entry.get("search_note"):
                    entry["search_note"] = (
                        "既有採集材料未定位本格之直接條件；"
                        "此狀態保留原有『已讀但未表述』判定。"
                    )
            row.update(calculate_coverage(row, books_total=len(table["books"])))
        write_json(path, table)


def _set_by_id(data: dict[str, Any], set_id: str) -> dict[str, Any]:
    return next(item for item in data["sets"] if item["set_id"] == set_id)


def update_c13() -> None:
    """Add TASK_27 concept-absence cells and repair legacy addressed evidence."""
    path = TABLES / "C13_kongwang_scope.json"
    table = load_json(path)
    bq = load_json(DOCTRINAL / "buzhequanshu_rules.json")
    fhl_note = (
        "TASK_27 全檔檢索『六甲空亡』『天地空亡』『四大空亡』『截路空亡』『五空』均 0 見；"
        "8 處『空亡』均未建立分系統概念，且無明文排除語。"
    )
    for row in table["rows"]:
        set_id = {
            "liujia_kongwang": "BQ_SET_VOID_01",
            "tiandi_kongwang": "BQ_SET_VOID_02",
            "sidakong_kongwang": "BQ_SET_VOID_03",
            "jielu_kongwang": "BQ_SET_VOID_04",
            "wu_kong": "BQ_SET_VOID_05",
        }[row["void_system_id"]]
        source_set = _set_by_id(bq, set_id)
        for index, current in enumerate(row["cells"]):
            if current["book_id"] == "buzhequanshu":
                item = source_set["items"][0]
                row["cells"][index] = cell(
                    "buzhequanshu", "addressed", verdict="立目",
                    source=f"{source_set['chapter']} {item['line']}",
                    original=item["definition_original"], rule_id=item["rule_id"],
                )
            elif current["book_id"] == "huozhulin":
                row["cells"][index] = cell(
                    "huozhulin", "concept_absent", absence_note=fhl_note,
                )
        row.update(calculate_coverage(row, books_total=len(table["books"])))
    write_json(path, table)


def _y_different_axis(book_id: str, *, note: str, original: str, source: str,
                      cross_reference: str | None) -> dict[str, Any]:
    return cell(
        book_id, "different_axis", axis_note=note, axis_original=original,
        axis_source=source, cross_reference=cross_reference,
        include_null_cross_reference=cross_reference is None,
    )


def y_table() -> dict[str, Any]:
    """Build the settled 10×8 Y table, including the ruled Y-R10 axis cell."""
    yimao_note = "本書以『喜／忌』表述元神、忌神之傾向（喜動／旺／生，喜靜／衰／制），非『能／不能』結果切分；Y2 傾向表未建（P-049）。"
    yimao_original = "有用神则必有忌神，忌则喜静、喜衰、喜制；有用神必有元神，元则喜动、喜旺、喜生。"
    fhl_role_note = "本書為主／輔二位結構，取用先按事類定身份，再按旺衰定效力；不把『輔』對齊為『元神』。"
    fhl_role_original = "用官鬼以父母辅之，用妻财以子孙辅之；值旺相为有气，休囚为无气。"
    zeng_r10_note = "本書以『能克害／不能克』成對列舉，條件為忌神之旺衰、空破、墓、化、同動，未以動靜切分。941『忌神與仇神同動』、950『忌神與元神同動』之『同動』為兩爻關係，非單爻動作"
    zeng_r10_original = "忌神旺相，或临日月，或遇日月动爻生扶者一也。"
    bq_term = "本書用「元辰」，清代三家用「元神」。二者概念對應係編者判定，非原文明言。"
    exclusion_original = "兄弟是破财之人，不为主、不为辅，何必看也？"
    exclusion_source = "〈6·公私用事〉 125–129（拒絕語 126）"
    not_addressed = lambda book, note: cell(book, "not_addressed", search_note=note)
    rows = [
        ("Y-R1", "元神旺相", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="能生", source="元神忌神衰旺章第十 907", original="元神旺相，或临日月，或得日月动爻生扶者，一也。", rule_id="R-ZS-01-01"),
            not_addressed("buzhengzong", "TASK_24 已搜原神、旺相、生扶、有力；未定位『原神旺相』的直接條件。"),
            _y_different_axis("huozhulin", note=fhl_role_note, original=fhl_role_original, source="〈3·財官輔助〉 59", cross_reference=None),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、旺相、生扶、扶；未定位原神旺相條件。"),
            cell("buzhequanshu", "addressed", verdict="須要生扶兼旺相", source="元辰訣 3355", original="元辰出现志扬扬，用伏藏兮也不妨。须要生扶兼旺相，最嫌冲克及刑伤。", rule_id="R-BQ-Y-02", term_note=bq_term),
        ]),
        ("Y-R2", "元神休囚", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能生", source="元神忌神衰旺章第十 926", original="元神休囚不动，或动而休囚又被伤克者一也。", rule_id="R-ZS-02-01"),
            cell("buzhengzong", "addressed", verdict="不能生用", source="原忌仇神論第四 2627／3294", original="如用神旺相，原神休囚不动……皆不能生用。", rule_id="R-BZ-Y-01"),
            _y_different_axis("huozhulin", note=fhl_role_note, original=fhl_role_original, source="〈3·財官輔助〉 59", cross_reference=None),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、休囚、衰；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 已搜元辰、休囚、衰、無力；未定位元辰休囚的直接條件。"),
        ]),
        ("Y-R3", "元神旬空", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能生", source="元神忌神衰旺章第十 927", original="元神休囚又逢旬空、月破二也。", rule_id="R-ZS-02-02"),
            not_addressed("buzhengzong", "TASK_24 已搜原神、旬空、空；未定位原神旬空的直接條件。"),
            _y_different_axis("huozhulin", note=fhl_role_note, original=fhl_role_original, source="〈3·財官輔助〉 59", cross_reference=None),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、空、旬空；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 有『用與元辰不可空』，但未限定旬空；不按近義補填。"),
        ]),
        ("Y-R4", "元神月破", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能生", source="元神忌神衰旺章第十 927", original="元神休囚又逢旬空、月破二也。", rule_id="R-ZS-02-02"),
            cell("buzhengzong", "addressed", verdict="不能生用", source="原忌仇神論第四 2627／3294", original="如用神旬空、月破、衰弱……", rule_id="R-BZ-Y-03", cell_note="TASK_24 採集報告列為本格材料，保留原句主詞『用神』。"),
            cell("huozhulin", "concept_absent", absence_note="TASK_27 全檔『月破』『日破』均 0 見；『破』9 見皆非月破義，無明文排除語。"),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、月破、破；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 已搜元辰、月破、破；未定位元辰月破的直接條件。"),
        ]),
        ("Y-R5", "元神動而化退神", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能生", source="元神忌神衰旺章第十 928", original="元神休囚动化退神三也。", rule_id="R-ZS-02-03"),
            cell("buzhengzong", "addressed", verdict="不能生用", source="原忌仇神論第四 2627／3294", original="或动而变墓变绝、变克、变破、变退……皆不能生用。", rule_id="R-BZ-Y-02"),
            cell("huozhulin", "concept_absent", absence_note="TASK_27 全檔『退神』『進神』均 0 見；『進』『退』字不構成進神／退神術語，無明文排除語。"),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、退神、動、化；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 已搜元辰、退神、動、化；未定位元辰動化退神條件。"),
        ]),
        ("Y-R6", "元神入墓", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能生", source="元神忌神衰旺章第十 930", original="元神入三墓五也。", rule_id="R-ZS-02-05"),
            cell("buzhengzong", "addressed", verdict="不能生用", source="原忌仇神論第四 2627／3294", original="或动而变墓变绝、变克、变破、变退……皆不能生用。", rule_id="R-BZ-Y-02"),
            _y_different_axis("huozhulin", note=fhl_role_note, original=fhl_role_original, source="〈3·財官輔助〉 59", cross_reference=None),
            not_addressed("huangjin_ce", "TASK_24 已搜原神、入墓、墓；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 已搜元辰、入墓、墓；未定位元辰入墓的直接條件。"),
        ]),
        ("Y-R7", "忌神旺相", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="能克害", source="元神忌神衰旺章第十 934", original="忌神旺相，或临日月，或遇日月动爻生扶者一也。", rule_id="R-ZS-03-01"),
            not_addressed("buzhengzong", "TASK_24 保留日月生扶忌神材料，但未直列『旺相』，不作對齊。"),
            cell("huozhulin", "explicit_exclusion", exclusion_original=exclusion_original, exclusion_source=exclusion_source, cell_note="① 排除者是兄弟，非忌神；不作等同。② 限財官二用語境。③ 兄弟在他篇仍論及（280／399／445），排除的是位次不是爻。④ 仇神為 concept_absent。"),
            not_addressed("huangjin_ce", "TASK_24 痘疹段有『鬼旺忌興』，未按本格的忌神旺相直接立說。"),
            not_addressed("buzhequanshu", "TASK_24 保留忌神生扶材料，但未直列『忌神旺相』，不作對齊。"),
        ]),
        ("Y-R8", "忌神休囚", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能克", source="元神忌神衰旺章第十 944", original="忌神休囚不动，或动而休囚又被日月动爻克者一也。", rule_id="R-ZS-04-01"),
            not_addressed("buzhengzong", "TASK_24 已搜忌神、休囚、衰；未定位忌神休囚的直接條件。"),
            cell("huozhulin", "explicit_exclusion", exclusion_original=exclusion_original, exclusion_source=exclusion_source, cell_note="① 排除者是兄弟，非忌神；不作等同。② 限財官二用語境。③ 兄弟在他篇仍論及（280／399／445），排除的是位次不是爻。④ 仇神為 concept_absent。"),
            not_addressed("huangjin_ce", "TASK_24 已搜忌神、休囚、衰；未定位直接條件。"),
            not_addressed("buzhequanshu", "TASK_24 有『忌神宜靜不宜興』，未直列休囚；不作對齊。"),
        ]),
        ("Y-R9", "忌神旬空", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            cell("zengshan", "addressed", verdict="不能克", source="元神忌神衰旺章第十 945", original="忌神静临空破二也。", rule_id="R-ZS-04-02"),
            not_addressed("buzhengzong", "TASK_24 已搜忌神、旬空、空；未定位直接條件。"),
            cell("huozhulin", "explicit_exclusion", exclusion_original=exclusion_original, exclusion_source=exclusion_source, cell_note="① 排除者是兄弟，非忌神；不作等同。② 限財官二用語境。③ 兄弟在他篇仍論及（280／399／445），排除的是位次不是爻。④ 仇神為 concept_absent。"),
            not_addressed("huangjin_ce", "TASK_24 已搜忌神、旬空、空；未定位直接條件。"),
            cell("buzhequanshu", "addressed", verdict="喜逢空", source="用爻空亡訣 3398", original="忌神最喜逢空吉，用与元辰不可空。", rule_id="R-BQ-Y-03", term_note=bq_term),
        ]),
        ("Y-R10", "忌神動而剋用神", [
            _y_different_axis("yimao", note=yimao_note, original=yimao_original, source="類總章第四十一 682", cross_reference="Y2（未建）"),
            _y_different_axis("zengshan", note=zeng_r10_note, original=zeng_r10_original, source="元神忌神衰旺章第十 933–950", cross_reference=None),
            cell("buzhengzong", "addressed", verdict="受克", source="原忌仇神論第四 2629", original="如忌神动来克用，而用爻出现不空则受克也。", rule_id="R-BZ-Y-04"),
            cell("huozhulin", "explicit_exclusion", exclusion_original=exclusion_original, exclusion_source=exclusion_source, cell_note="① 排除者是兄弟，非忌神；不作等同。② 限財官二用語境。③ 兄弟在他篇仍論及（280／399／445），排除的是位次不是爻。④ 仇神為 concept_absent。"),
            not_addressed("huangjin_ce", "TASK_24 痘疹段僅稱『次究忌神動靜』，未直列動而剋用神。"),
            cell("buzhequanshu", "addressed", verdict="用受刑", source="用忌神訣 3350", original="看卦先须看忌神，忌神宜静不宜兴；忌神急要逢冲克，若遇生扶用受刑。", rule_id="R-BQ-Y-01", term_note=bq_term),
        ]),
    ]
    output_rows = []
    for row_id, condition, cells in rows:
        cells.extend(not_collected(book_id) for book_id in ("jing_shi_yizhuan", "yiyin"))
        row = {"row_id": row_id, "condition": condition, "cells": cells}
        row.update(calculate_coverage(row, books_total=len(BOOKS)))
        output_rows.append(row)
    return {
        "table_id": "Y", "title": "元神忌神之狀態材料",
        "axis_note": "保留各書的結果、傾向及主輔結構，不將其互譯。",
        "books": BOOKS, "rows": output_rows,
    }


def main() -> None:
    write_json(TABLES / "K_kongwang_effect.json", k_table())
    update_yimao()
    update_y_material_catalogues()
    write_json(DOCTRINAL / "huozhulin_rules.json", huozhulin_rules())
    update_chong_tables()
    update_c13()
    write_json(TABLES / "Y_yuanshen_jishen.json", y_table())


if __name__ == "__main__":
    main()
