"""Generate the four TASK_CODEX_27 decision tables from collected materials."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "decision_tables"

BOOKS = [
    ("yimao", "易冒"), ("zengshan", "增刪卜易"),
    ("buzhengzong", "卜筮正宗"), ("huozhulin", "火珠林"),
    ("huangjin_ce", "黃金策"), ("buzhequanshu", "卜筮全書"),
    ("jing_shi_yizhuan", "京氏易傳"), ("yiyin", "易隱"),
]
BOOK_NAMES = dict(BOOKS)
INGESTED = {book_id for book_id, _ in BOOKS if book_id not in {"jing_shi_yizhuan", "yiyin"}}


def base_cell(book_id: str, status: str, **fields):
    cell = {"book_id": book_id, "status": status}
    if status == "not_collected":
        cell["collection_status"] = "ingested_not_surveyed" if book_id in INGESTED else "not_ingested"
    cell.update(fields)
    return cell


def addressed(book_id, verdict, original, source, *, quality="clean", rule_id=None, partial_note=None, **extra):
    cell = base_cell(book_id, "addressed", verdict=verdict, original=original, source=source,
                     match_quality=quality, candidate_type=extra.pop("candidate_type", None), **extra)
    if rule_id:
        cell["rule_id"] = rule_id
    if quality == "partial":
        cell["partial_note"] = partial_note or "原文範圍只部分覆蓋本格條件。"
    return cell


def candidate(book_id, verdict, original, source, rule, **kwargs):
    return addressed(book_id, verdict, original, source, candidate_rule=rule,
                     candidate_type="conditional", **kwargs)


def not_addressed(book_id, note):
    return base_cell(book_id, "not_addressed", verdict=None, search_note=note)


def different_axis(book_id, note, original, source, cross_reference=None):
    return base_cell(book_id, "different_axis", verdict=None, axis_note=note,
                     axis_original=original, axis_source=source, cross_reference=cross_reference)


def category_negated(book_id, original, source, category, note):
    return base_cell(book_id, "category_negated", verdict=None,
                     negation_original=original, negation_source=source,
                     negation_category=category, absence_note=note)


def concept_absent(book_id, note):
    return base_cell(book_id, "concept_absent", verdict=None, absence_note=note)


def table(table_id, title, rows, note, *, axis_note=None, unmapped_items=None):
    result = {
        "table_id": table_id, "title": title,
        "axis_note": axis_note or "只記錄材料與機械格位，不輸出效果語義。",
        "books": [{"book_id": book_id, "name": name} for book_id, name in BOOKS],
        "table_note": note, "rows": rows,
    }
    if unmapped_items:
        result["unmapped_items"] = unmapped_items
    return result


def rows_for(table_id, conditions, matrix):
    rows = []
    for row_id, condition in conditions:
        cells = [matrix[row_id][book_id] for book_id, _ in BOOKS]
        counts = {status: sum(cell.get("status") == status for cell in cells)
                  for status in ("addressed", "not_addressed", "not_collected", "category_negated",
                                 "concept_absent", "explicit_exclusion", "different_axis")}
        collected = len(cells) - counts["not_collected"]
        parts = []
        labels = (("addressed", "本有表述"), ("category_negated", "本否定範疇"),
                  ("concept_absent", "本無此概念"), ("explicit_exclusion", "本明文排除角色"),
                  ("not_addressed", "本未表述"), ("different_axis", "本用另一軸"))
        for status, label in labels:
            if counts[status]: parts.append(f"{counts[status]}{label}")
        coverage = {
            "books_total": len(cells), "books_collected": collected,
            "books_addressed": counts["addressed"], "books_not_addressed": counts["not_addressed"],
            "books_category_negated": counts["category_negated"], "books_concept_absent": counts["concept_absent"],
            "books_explicit_exclusion": counts["explicit_exclusion"], "books_different_axis": counts["different_axis"],
            "books_not_collected": counts["not_collected"],
        }
        label = (
            f"已採 {collected} 本"
            + (("：" + "、".join(parts)) if parts else "")
            + ((f"；另 {counts['not_collected']} 本未採") if counts["not_collected"] else "")
        )
        pair = {cell["book_id"]: cell.get("status") for cell in cells}
        if "addressed" in (pair.get("huangjin_ce"), pair.get("buzhequanshu")) and all(
            status in {"addressed", "different_axis"} for status in (pair.get("huangjin_ce"), pair.get("buzhequanshu"))
        ):
            label += "\n\n註：《黃金策》與《卜筮全書》文本重疊 89.4%（被收錄者與收錄者），二者之一致不構成兩個獨立證據。"
        rows.append({
            "row_id": row_id, "condition": condition,
            "cells": cells, "coverage": coverage,
            "coverage_label": label,
        })
    return rows


def a_table():
    conditions = [(f"A-R{i}", text) for i, text in enumerate((
        "用神安靜", "用神發動", "用神旺相", "用神休囚",
        "用神旬空", "用神月破", "用神逢合", "用神入墓",
    ), 1)]
    matrix = {row_id: {} for row_id, _ in conditions}
    for row_id, _ in conditions:
        matrix[row_id]["huozhulin"] = concept_absent(
            "huozhulin", "該書無應期、刻期、期、何日、何時命中（TASK_27 §四）。"
        )
        for book_id in ("jing_shi_yizhuan", "yiyin"):
            matrix[row_id][book_id] = base_cell(book_id, "not_collected")
    ym = {
        "A-R3": ("以墓乃收", "用爻旺而墓乃收", "易冒 類總章第四十一 700", "用神之墓支", "partial"),
        "A-R4": ("得生而病康", "用神困矣，得生而病康", "易冒 疾病章 1052", "生用神之支", "partial"),
        "A-R5": ("得實而病愈", "用神空矣，得實而病愈", "易冒 疾病章 1052", "填實用神之支", "partial"),
        "A-R6": ("逾日月而可保", "用神破散，逾日月而可保", "易冒 疾病章 1052", "出破之月日", "partial"),
        "A-R8": ("墓開而疾退", "墓開而疾退", "易冒 疾病章 1052", "沖開用神之墓支", "partial"),
    }
    for row_id, (verdict, original, source, rule, quality) in ym.items():
        matrix[row_id]["yimao"] = candidate(
            "yimao", verdict, original, source, rule, quality=quality,
            partial_note="原文在『問病日期／疾病』情境中表述，非一般應期總注。"
            if row_id != "A-R3" else "原文以旺而墓乃收表述，未逐字使用『旺相』。",
        )
    for row_id in ("A-R1", "A-R2", "A-R7"):
        matrix[row_id]["yimao"] = not_addressed("yimao", "TASK_26 §8.1：已錄材料未見本格之一般應期條文。")
    zs = {
        "A-R1": ("值逢沖", "静而逢值逢冲；如主事爻临子水不动，后逢子日午日而应之，余仿此。", "增刪卜易 2002–2003", "用神之支或沖用神之支"),
        "A-R2": ("值逢合", "动而逢值逢合；如主事爻临子水发动，后遇子日丑日而应之，余仿此。", "增刪卜易 2004–2005", "用神之支或合用神之支"),
        "A-R3": ("逢墓逢沖", "太旺者，逢墓逢冲。", "增刪卜易 2006", "用神之墓支或沖用神之支"),
        "A-R4": ("遇生遇旺", "衰绝者，遇生遇旺。", "增刪卜易 2009", "生用神之支或用神旺支"),
        "A-R5": ("填沖", "旬空最爱填冲。", "增刪卜易 2019", "填實或沖用神之支"),
        "A-R6": ("填合", "月破喜逢填合。", "增刪卜易 2016", "填實或合用神之支"),
        "A-R7": ("沖開", "遇六合，亦宜相击。", "增刪卜易 2013–2014", "沖開用神之合"),
        "A-R8": ("沖開三墓", "入三墓，俱喜冲开。", "增刪卜易 2011–2012", "沖開用神之墓支"),
    }
    for row_id, (verdict, original, source, rule) in zs.items():
        quality = "partial" if row_id in {"A-R3", "A-R4"} else "clean"
        matrix[row_id]["zengshan"] = candidate("zengshan", verdict, original, source, rule, quality=quality,
            partial_note="原文條件為『太旺』，範圍窄於本格旺相。" if row_id == "A-R3" else
                         "原文以衰絕為條件，未完全等同休囚。" if row_id == "A-R4" else None)
    bz = {
        "A-R1": ("以沖用神之日為應期", "用神安静，以冲用神之日为应期", "卜筮正宗 各門類應期總注第十四 386", "沖用神之支"),
        "A-R2": ("以合用神之日為應期", "用神发动，以合用神之日为应期", "卜筮正宗 各門類應期總注第十四 386", "合用神之支"),
        "A-R3": ("以墓庫之日為應期", "用神太旺，以墓库之日为应期", "卜筮正宗 各門類應期總注第十四 388", "用神之墓支"),
        "A-R4": ("以生旺之日為應期", "用神休囚，以生旺之日为应期", "卜筮正宗 各門類應期總注第十四 388", "生用神之支"),
        "A-R5": ("以出旬之日為應期", "用神旬空，以出旬之日为应期", "卜筮正宗 各門類應期總注第十四 390", "出旬"),
        "A-R6": ("以出月或填實之日為應期", "用神月破，以出月或填实之日为应期", "卜筮正宗 各門類應期總注第十四 390", "出月或填實用神之支"),
        "A-R7": ("以合住之日為應期", "动应合住", "卜筮正宗 各門類應期總注第十四 392", "合住之支"),
    }
    for row_id, (verdict, original, source, rule) in bz.items():
        quality = "partial" if row_id == "A-R7" else "clean"
        matrix[row_id]["buzhengzong"] = candidate("buzhengzong", verdict, original, source, rule, quality=quality,
            partial_note="原文主語是變化之爻應於合住之日，非用神逢合之一般條件。" if quality == "partial" else None,
            layer="summary")
    matrix["A-R8"]["buzhengzong"] = not_addressed("buzhengzong", "TASK_26 §8.1：388、392之墓庫為旺爻應期之日，未立『用神入墓』格。")
    for row_id in ("A-R1", "A-R2"):
        matrix[row_id]["huangjin_ce"] = different_axis("huangjin_ce", "本書斷人之動靜，非斷應期之日。其出處不是日期候選。", "主象交重身已動，用爻安靜未思歸", "黃金策 行人章 1633")
    for row_id in ("A-R3", "A-R4", "A-R5", "A-R6", "A-R7", "A-R8"):
        matrix[row_id]["huangjin_ce"] = not_addressed("huangjin_ce", "TASK_26 §8.1：未見以此條件推日期之條文。")
    for row_id in ("A-R1", "A-R2", "A-R4", "A-R7"):
        matrix[row_id]["buzhequanshu"] = not_addressed("buzhequanshu", "TASK_26 §8.1：已錄材料未立本格之一般應期條文。")
    for row_id, original, verdict, rule in (
        ("A-R3", "用爻旺相，後逢生旺月日斷之。", "以生旺之月日為候選", "用神旺支"),
        ("A-R5", "用爻旺空，或空而逢沖、逢并、逢動者，則以過旬斷之。", "以過旬為候選", "出旬"),
        ("A-R6", "用爻合住，則以沖破之日斷之。", "以沖破之日為候選", "沖破用神之合"),
        ("A-R8", "若用爻入墓，則以破墓月日斷之。", "以破墓月日為候選", "破用神之墓"),
    ):
        matrix[row_id]["buzhequanshu"] = candidate("buzhequanshu", verdict, original, "卜筮全書 5660–5661", rule, quality="partial" if row_id == "A-R3" else "clean", partial_note="原文置於事類及期日段，未按本格完整拆分。" if row_id == "A-R3" else None)
    note = "應期只輸出候選條件，不展開實際日期；《卜筮正宗》386–392屬第一層摘要層。"
    return table("A", "應期候選", rows_for("A", conditions, matrix), note,
                 axis_note="依用神狀態列出候選條件；本表不定單一應期、不輸出實際日期。")


def m1_table():
    conditions = [("M1-R1", "用神入日墓"), ("M1-R2", "用神入月墓"), ("M1-R3", "用神入動爻之墓"), ("M1-R4", "用神化墓"), ("M1-R5", "用神入飛爻之墓"), ("M1-R6", "用神絕於日"), ("M1-R7", "用神絕於月"), ("M1-R8", "用神化絕")]
    matrix = {row_id: {} for row_id, _ in conditions}
    for row_id, _ in conditions:
        for book_id in ("huozhulin", "jing_shi_yizhuan", "yiyin"):
            matrix[row_id][book_id] = base_cell(book_id, "not_collected")
    ym = {
        "M1-R1": addressed("yimao", "墓于日", "本命臨鬼而墓于日為命墓，世爻臨鬼而墓于日為世墓。", "易冒 隨墓章 520–521", quality="partial", partial_note="明文主語為命、世，非一般用神。", soil_original="五行家以陰陽分長生，殊不知五行之氣，原無二致。", soil_track_note="474 行明文將分陰陽之說歸五行家，並自述不採；本表只列雙軌資料，不替《易冒》另選軌。"),
        "M1-R2": category_negated("yimao", "日有隨墓助傷，而月則無也，故日尤親。", "易冒 類總章第四十一 688", "月有隨墓助傷", "明文否定月有隨墓助傷；不延伸為一般月墓。"),
        "M1-R3": addressed("yimao", "用入墓，喜刑喜沖", "死墓之法……墓而有刑，如擊如發，墓而無沖，為匿為藏；凡用入墓，喜刑喜沖。", "易冒 長生章第三十一 468–469", quality="partial", partial_note="論入墓通則，未按日／月／動來源分條。"),
        "M1-R4": addressed("yimao", "化爻隨鬼入墓", "化爻隨鬼入墓，與命墓世墓無差等，而有真偽。", "易冒 隨墓章第三十五 526", rule_id="R-YM-M1-R4"),
        "M1-R5": different_axis("yimao", "本書按所墓者位次分五類，非按飛爻來源分格。", "夫隨墓有五：一曰命墓，二曰世墓，三曰化爻墓，四曰卦身墓，五曰世身墓。", "易冒 隨墓章第三十五 520", "M2 位次軸"),
        "M1-R6": addressed("yimao", "生絕于日辰特重", "用爻生絕于日辰之上者特重，生絕于月建之上者有分。", "易冒 長生章第三十一 470"),
        "M1-R7": addressed("yimao", "生絕于月建有分", "用爻生絕于日辰之上者特重，生絕于月建之上者有分。", "易冒 長生章第三十一 470"),
        "M1-R8": addressed("yimao", "動爻生絕于變", "動爻生絕于變，其法猶類日也，然有真偽之辯焉。", "易冒 長生章第三十一 472"),
    }
    matrix.update({row_id: {**matrix[row_id], "yimao": cell} for row_id, cell in ym.items()})
    zs = {
        "M1-R1": addressed("zengshan", "隨鬼入日墓", "古有日墓、動墓、化墓，謂之三墓。", "增刪卜易 隨鬼入墓章第三十 2569"),
        "M1-R3": addressed("zengshan", "入動墓", "未土爻動者，謂之入動墓。", "增刪卜易 生旺墓絕章第二十六 1951"),
        "M1-R4": addressed("zengshan", "化墓", "動而變出未土者，謂之化墓。", "增刪卜易 生旺墓絕章第二十六 1953"),
        "M1-R5": different_axis("zengshan", "本書明文另立位次軸，非以飛爻來源切分。", "又有世爻隨鬼入墓、本命隨鬼入墓、卦身隨鬼入墓、世身隨鬼入墓。", "增刪卜易 隨鬼入墓章第三十 2569", "M2 位次軸"),
        "M1-R6": addressed("zengshan", "絕於巳", "土雖絕于巳，必須休囚無氣，又逢巳爻，謂之絕也。", "增刪卜易 生旺墓絕章第二十六 1961", quality="partial", partial_note="立絕於某支並附旺衰條件，未分日絕與月絕。"),
        "M1-R7": addressed("zengshan", "絕於巳", "土雖絕于巳，必須休囚無氣，又逢巳爻，謂之絕也。", "增刪卜易 生旺墓絕章第二十六 1961", quality="partial", partial_note="立絕於某支並附旺衰條件，未分日絕與月絕。"),
        "M1-R8": addressed("zengshan", "化絕", "動而變出申金者，謂之化絕。", "增刪卜易 生旺墓絕章第二十六 1953"),
    }
    for row_id, cell in zs.items(): matrix[row_id]["zengshan"] = cell
    matrix["M1-R2"]["zengshan"] = not_addressed("zengshan", "2569列日墓、動墓、化墓三墓，未列月墓；古法轉述不作明文排除。")
    bz = {
        "M1-R1": addressed("buzhequanshu", "日辰帶墓爻", "以日時看……若遇日辰帶墓爻，謂隨官入墓。", "卜筮全書 幽明兩墓 7104、7062", quality="partial", partial_note="主語為身、命、世，非一般用神。"),
        "M1-R4": addressed("buzhequanshu", "發動而化入墓", "若主象發動而化入者，不問公私大小之事，皆主不成。", "卜筮全書 5571–5572"),
        "M1-R5": different_axis("buzhequanshu", "本書以隨官入墓之位次及幽明切分，非以飛爻來源切分。", "隨官入墓，其目有三：有身隨鬼入墓，有世隨鬼入墓，有命隨鬼入墓。", "卜筮全書 3097", "M2 位次軸"),
        "M1-R8": addressed("buzhequanshu", "發動而化入墓", "用爻變動，忌遭死墓絕空；若主象發動而化入者，皆主不成。", "卜筮全書 5571–5572"),
    }
    for row_id, cell in bz.items(): matrix[row_id]["buzhequanshu"] = cell
    for row_id, _ in conditions:
        matrix[row_id].setdefault(
            "buzhequanshu",
            not_addressed("buzhequanshu", "TASK_26 §8.2：已錄材料未見本格之直接條件。"),
        )
    hj = {row_id: addressed("huangjin_ce", "四者併言", "死墓絕空，乃是泥犁之地。", "黃金策 總斷千金賦 14", quality="partial", partial_note="墓與死、絕、空並列，未分本格來源。", direction_note="本書墓絕材料與死、空並列，未單立來源格；本表不把並列句改寫為單一方向。") for row_id in ("M1-R1", "M1-R2", "M1-R3", "M1-R4", "M1-R8")}
    for row_id, cell in hj.items(): matrix[row_id]["huangjin_ce"] = cell
    for row_id in ("M1-R5", "M1-R6", "M1-R7"): matrix[row_id]["huangjin_ce"] = not_addressed("huangjin_ce", "TASK_26 §8.2：已錄材料未見本格之直接條件。")
    for row_id in conditions:
        row_id = row_id[0]
        for book_id in ("buzhengzong",):
            matrix[row_id][book_id] = not_addressed(book_id, "TASK_26 §8.2：已錄材料未見本格之直接條件。")
    matrix["M1-R4"]["buzhengzong"] = addressed("buzhengzong", "官鬼發動化未土", "用神或世爻隨官鬼入墓者，主凶。如世爻為寅木，官鬼發動化未土，未為木之墓。", "卜筮正宗 隨鬼入墓 244", rule_id="R-BZ-M1-R4")
    matrix["M1-R5"]["buzhengzong"] = addressed("buzhengzong", "用神或世爻隨官鬼入墓", "用神或世爻隨官鬼入墓者，主凶。如世爻為寅木，官鬼發動化未土。", "卜筮正宗 隨鬼入墓 244", quality="partial", partial_note="主語含用神或世爻，來源例限於化墓。")
    note = "本表格位以「墓絕之來源」切分，不預設墓絕為凶。各家對墓之吉凶取向不一，見各 cell。土爻墓位須並列軌 A（隨水說，墓辰）與軌 B（火土同源說，墓戌）；本表不替 scope_unclear 之書選軌。本表尚未接入機械層（P-064）。格位條件所需之入墓、絕之判定，L2 未實作，故本表現階段不會觸發。材料已入庫，可供原文檢索頁查閱。"
    result = table("M1", "墓絕之來源（爻層）", rows_for("M1", conditions, matrix), note,
                   axis_note="M1 為來源軸；M2 位次軸與 M3 旺衰軸另表並存。")
    result["soil_tracks"] = {
        "track_A": {"track_id": "track_A", "長生": "申", "墓": "辰", "source": "SPEC §7", "rule_id": "R-L1-05"},
        "track_B": {"track_id": "track_B", "長生": "寅", "墓": "戌", "source": "SPEC §7", "rule_id": "R-L1-05"},
    }
    return result


def m2_table():
    conditions = [("M2-R1", "命隨鬼入墓"), ("M2-R2", "世爻隨鬼入墓"), ("M2-R3", "卦身隨鬼入墓"), ("M2-R4", "世身隨鬼入墓"), ("M2-R5", "化爻隨鬼入墓")]
    matrix = {row_id: {} for row_id, _ in conditions}
    for row_id, _ in conditions:
        for book_id in ("jing_shi_yizhuan", "yiyin"): matrix[row_id][book_id] = base_cell(book_id, "not_collected")
    for row_id, subject in zip(("M2-R1", "M2-R2", "M2-R3", "M2-R4", "M2-R5"), ("命墓", "世墓", "卦身墓", "世身墓", "化爻墓")):
        matrix[row_id]["yimao"] = addressed("yimao", subject, "夫隨墓有五：一曰命墓，二曰世墓，三曰化爻墓，四曰卦身墓，五曰世身墓。", "易冒 隨墓章第三十五 520", rule_id="R-YM-M2")
    for row_id, subject in zip(("M2-R1", "M2-R2", "M2-R3", "M2-R4"), ("本命", "世爻", "卦身", "世身")):
        matrix[row_id]["zengshan"] = addressed("zengshan", subject + "隨鬼入墓", "又有世爻隨鬼入墓、本命隨鬼入墓、卦身隨鬼入墓、世身隨鬼入墓。", "增刪卜易 隨鬼入墓章第三十 2569", rule_id="R-ZS-M2")
    matrix["M2-R5"]["zengshan"] = not_addressed("zengshan", "2569列位次軸四項，未列化爻隨鬼入墓。")
    for row_id, subject in zip(("M2-R1", "M2-R2", "M2-R3"), ("命", "世", "身")):
        matrix[row_id]["buzhequanshu"] = addressed("buzhequanshu", subject + "隨鬼入墓", "隨官入墓，其目有三：有身隨鬼入墓，有世隨鬼入墓，有命隨鬼入墓。", "卜筮全書 隨官入墓 3097", rule_id="R-BQ-M2")
    for row_id in ("M2-R4", "M2-R5"): matrix[row_id]["buzhequanshu"] = not_addressed("buzhequanshu", "3097之專章只列身、世、命三項，未列本格項目。")
    matrix["M2-R2"]["buzhengzong"] = addressed("buzhengzong", "世爻隨官鬼入墓", "用神或世爻隨官鬼入墓者，主凶。", "卜筮正宗 隨鬼入墓 244", quality="partial", partial_note="原文另含用神角色；本格只取世爻項。")
    for row_id in ("M2-R1", "M2-R3", "M2-R4", "M2-R5"): matrix[row_id]["buzhengzong"] = not_addressed("buzhengzong", "244只明文涉及用神或世爻，未列本格其他位次。")
    for row_id in conditions:
        row_id = row_id[0]
        matrix[row_id]["huangjin_ce"] = not_addressed("huangjin_ce", "TASK_29：『隨墓／隨鬼入墓／隨官入墓』全檔 0 命中；已錄墓材料未立本表位次。")
        matrix[row_id]["huozhulin"] = different_axis("huozhulin", "本書另有『卦有三墓：宮墓、鬼墓、財墓』，不是隨鬼入墓位次軸。", "卦有三墓：宮墓、鬼墓、財墓。", "火珠林 41·占疾病 768", "火珠林三墓分類")
    note = "本表之材料曾因檢索主詞而幾乎漏收。『隨墓』與『隨鬼入墓／隨官入墓』須並搜；卜筮全書、卜筮正宗各有專章。項數不等，未為對齊而補項。此為 S10.1 所列位次軸；不將不同項數補成相同清單。本表尚未接入機械層（P-064）。格位條件所需之入墓、絕之判定，L2 未實作，故本表現階段不會觸發。材料已入庫，可供原文檢索頁查閱。"
    unmapped = [{"book_id": "buzhengzong", "items": [{"name": "用神隨官鬼入墓", "source": "卜筮正宗 244"}], "count_declared": 2, "count_actual": 2}]
    return table("M2", "隨鬼入墓（位次軸）", rows_for("M2", conditions, matrix), note,
                 axis_note="M2 與 M1 並存；增刪 2569 明文以『又有』並列來源軸與位次軸。",
                 unmapped_items=unmapped)


def m3_table():
    conditions = [("M3-R1", "旺相之爻隨墓"), ("M3-R2", "休囚被剋之爻隨墓")]
    matrix = {row_id: {} for row_id, _ in conditions}
    for row_id, _ in conditions:
        for book_id, _ in BOOKS:
            if book_id == "zengshan":
                continue
            matrix[row_id][book_id] = base_cell(book_id, "not_collected")
    matrix["M3-R1"]["zengshan"] = addressed("zengshan", "旺相者非真", "此三墓者，自占看世爻，旺相者非真；代占看用神，旺相者非真。", "增刪卜易 隨鬼入墓章第三十 2622–2624", rule_id="R-ZS-M3-R1")
    matrix["M3-R2"]["zengshan"] = addressed("zengshan", "休囚被克而入墓始見凶危", "惟世爻、用神休囚被克，而又入墓者，是也。", "增刪卜易 隨鬼入墓章第三十 2623", rule_id="R-ZS-M3-R2")
    note = "野鶴原文：『諸書竟不言及旺衰，隨墓概以不吉斷。』此為該書明文批評，只記錄，不據此判定其餘各書；其餘七本均 not_collected。本表尚未接入機械層（P-064）。格位條件所需之入墓、絕之判定，L2 未實作，故本表現階段不會觸發。材料已入庫，可供原文檢索頁查閱。"
    return table("M3", "隨墓之旺衰（旺衰軸）", rows_for("M3", conditions, matrix), note,
                 axis_note="M3 只收已採集之增刪卜易材料；不把批評句轉成他書狀態。")


def main():
    for payload in (a_table(), m1_table(), m2_table(), m3_table()):
        path = OUT / {
            "A": "A_yingqi.json", "M1": "M1_mujue_source.json",
            "M2": "M2_suiguirumu.json", "M3": "M3_suimu_wangshuai.json",
        }[payload["table_id"]]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
