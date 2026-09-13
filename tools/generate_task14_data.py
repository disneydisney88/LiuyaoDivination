"""Generate TASK14 doctrinal envelopes and the data-backed C1 table."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.semantics import calculate_coverage


DOCTRINAL = ROOT / "data" / "doctrinal"
TABLES = ROOT / "data" / "decision_tables"

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

ENVELOPES = {
    "yimao": {
        "source_book": "易冒", "era": "清", "author": "程良玉",
        "attribution_status": "attested", "framework_type": "ordinal_18",
        "enumeration_style": "authorial_ordinal",
        "framework_note": "十八級序數排序，全吉 1–8／半吉 9–11／凶陷 12–18；帶明文遞增比較語；第 17 項有明文例外",
        "doctrinal_status": "single_school", "conflicts_with": ["C1", "C11", "C12"],
        "corpus_path": "07_易冒/易冒.txt",
        "provenance_strength": "weak",
        "provenance_note": "主檔無 .source.json；已知 11 處未宣告佔位及末 2 行《四庫全書總目提要》附綴。所據紙本底本不明，本地無影像可核（TASK_22 審計）。",
        "corpus_cleaned": False,
        "cleaning_status": "未分離。已知：11 處未宣告佔位（『（？）』『（魂？）』）、末 2 行四庫提要屬他書附綴",
        "cleaning_pending_task": "P-036",
    },
    "zengshan": {
        "source_book": "增刪卜易", "era": "清", "author": "野鶴老人",
        "attribution_status": "attested", "framework_type": "binary_enumeration",
        "enumeration_style": "authorial_count",
        "framework_note": "成對之能／不能列舉，無排序、無中間態、無嚴重度分級",
        "doctrinal_status": "single_school", "conflicts_with": ["C1", "C11", "C12"],
        "corpus_path": "05_增刪卜易/增刪卜易_完整版_A.md",
        "corpus_variant": "simplified_full",
        "provenance_strength": "weak",
        "provenance_note": "底本為簡體 `增刪卜易_完整版_A.md`。該檔本身無 `.source.json`，但 `CATALOG.md` 第 53 行已記錄來源：repo `gundamdarke398-ship-it/liuyao-divination`，授權 MIT。檔內另自述「增删卜易（古吴版）／全书共 237 页」及 237 個頁碼標記，該頁碼可由檔內自洽。\n\n**本項目 TASK_16 曾誤記此檔缺乏外部來源記錄，經 TASK_22 審計證實有誤** —— 成因為只查 `.source.json` 而未查 `CATALOG.md`。\n\n現存缺口：該 repo 所據之紙本底本不明；本地無影像可核（見 §12 全庫強度上限）。另有 606 行版面殘留未分離（見 P-032）。",
        "corpus_cleaned": False,
        "cleaning_status": "未分離。已知：606 行版面殘留（TASK_22 審計）",
        "cleaning_pending_task": "P-032",
        "comparison_edition": {
            "path": "05_增刪卜易/（33 個繁體 .txt）",
            "variant": "traditional_partial",
            "source": "維基文庫，逐檔有 wikisource_title／url／revision_id（2100290–2100780 區間，18.txt 為 2101727），fetched 2026-09-13",
            "coverage": "序＋章第一至又二十六，共 32 章；簡體本正文章題 98 條。繁體本僅約全書三分之一",
            "missing": "0 個編號卦例（簡體本 68 個）；簡體本第 2057 行以後約 6,700 行無對應",
            "role": "對照本。不另開 book_id，不入決策表",
            "known_contamination": "4 處現代編注署名「原劍」：03.txt:97–99、05.txt:26–28、09.txt:18–20、13.txt:18–20。另 3 處〈〉夾註未署名，性質未判定",
            "sidecar_gap": "sidecar 有 revision_id，但未記該維基頁面所據之紙本底本；正文亦無版本題識",
        },
    },
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_envelope(book_id: str) -> None:
    path = DOCTRINAL / (book_id + "_rules.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = ENVELOPES[book_id]
    envelope = {"book_id": book_id, **meta}
    preserved = {key: data[key] for key in ("source_file", "extraction_task", "warning") if key in data}
    envelope.update(preserved)
    envelope["semantic_status"] = data.get("semantic_status", "structured_only_no_effects_implemented")
    envelope["sets"] = data.get("sets", [])
    write_json(path, envelope)


def buzhengzong() -> dict:
    return {
        "book_id": "buzhengzong",
        "source_book": "卜筮正宗",
        "era": "清",
        "author": "王洪緒",
        "attribution_status": "attested",
        "framework_type": "true_false_binary",
        "enumeration_style": "none",
        "framework_note": "〈月破論第九〉分真破假破，〈旬空論第十〉分真空假空。真者到底無救，假者可解。無「散」之級別，無排序",
        "doctrinal_status": "single_school",
        "semantic_status": "structured_only_no_effects_implemented",
        "conflicts_with": ["C1", "C11", "C12"],
        "corpus_path": "04_卜筮正宗/卜筮正宗_完整版_A.md",
        "provenance_strength": "weak",
        "provenance_note": "主檔無 .source.json；檔內自述為網站整合本，47 行『直解』為王洪緒原注大意之轉述。所據紙本底本不明，本地無影像可核（TASK_22 審計）。",
        "corpus_cleaned": False,
        "cleaning_status": "未分離。已知：兩套重疊層、卦例重複至 6 次、47 行『直解』為轉述式無署名注（自述為原注大意）",
        "cleaning_pending_task": "P-035",
        "sets": [
            {
                "set_id": "BZ_SET_01_FALSE", "set_name": "月破論第九（假破）", "chapter": "月破論第九", "line": 2691,
                "polarity": "positive", "paired_with": "BZ_SET_01_TRUE",
                "count_declared": None, "count_actual": 5, "count_mismatch": None,
                "definition_original_full": "凡卦中月破之爻，乃关因之所现也。动者亦能生克他爻，变者亦能生克本爻，目下虽破出月不破矣！今日虽破，值日不破矣！月破最喜逢合填实，远应年月，近应日时。如破而安静再值旬空衰弱，遇动爻月建日辰克害，此等月破谓之真破，到底破矣！",
                "segmentation_note": "切分依據：『动者』、『变者』、『目下』、『今日』、『月破最喜逢合填实』。",
                "items": [{
                    "item_ordinal": 1, "definition_original": "动者亦能生克他爻", "rule_id": "R-BZ-01-F-01", "line": 2691, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 2, "definition_original": "变者亦能生克本爻", "rule_id": "R-BZ-01-F-02", "line": 2691, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 3, "definition_original": "目下虽破出月不破矣！", "rule_id": "R-BZ-01-F-03", "line": 2691, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 4, "definition_original": "今日虽破，值日不破矣！", "rule_id": "R-BZ-01-F-04", "line": 2691, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 5, "definition_original": "月破最喜逢合填实，远应年月，近应日时。", "rule_id": "R-BZ-01-F-05", "line": 2691, "enumeration_source": "editorial",
                }],
            },
            {
                "set_id": "BZ_SET_01_TRUE", "set_name": "月破論第九（真破）", "chapter": "月破論第九", "line": 2691,
                "polarity": "negative", "paired_with": "BZ_SET_01_FALSE",
                "count_declared": None, "count_actual": 2, "count_mismatch": None,
                "definition_original_full": "凡卦中月破之爻，乃关因之所现也。动者亦能生克他爻，变者亦能生克本爻，目下虽破出月不破矣！今日虽破，值日不破矣！月破最喜逢合填实，远应年月，近应日时。如破而安静再值旬空衰弱，遇动爻月建日辰克害，此等月破谓之真破，到底破矣！",
                "segmentation_note": "切分依據：『如』、『再』、『遇』、『此等月破谓之真破』。",
                "items": [{
                    "item_ordinal": 1, "definition_original": "如破而安静再值旬空衰弱", "rule_id": "R-BZ-01-T-01", "line": 2691, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 2, "definition_original": "遇动爻月建日辰克害，此等月破谓之真破，到底破矣！", "rule_id": "R-BZ-01-T-02", "line": 2691, "enumeration_source": "editorial",
                }],
            },
            {
                "set_id": "BZ_SET_02_POSITIVE", "set_name": "旬空論第十（到底有用）", "chapter": "旬空論第十", "line": 2699,
                "polarity": "positive", "paired_with": "BZ_SET_02_NEGATIVE",
                "count_declared": None, "count_actual": 6, "count_mismatch": None,
                "definition_original_full": "凡卦中爻遇旬空，乃神机发现于此也。如旺相旬空，或休囚发动，日辰生扶、动爻生扶、动爻变空、伏而旺相，此等旬空到底有用，不过待其出旬、值日、有合空、冲起、冲实、填补之法，后卷占验注明。如：休囚安静或日辰克动，爻克伏而被克，静逢月破值此旬空者，谓之真空到底空矣！",
                "segmentation_note": "切分依據：『如』、『或』、『、』、『此等旬空到底有用』。",
                "items": [{
                    "item_ordinal": 1, "definition_original": "旺相旬空", "rule_id": "R-BZ-02-P-01", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 2, "definition_original": "休囚发动", "rule_id": "R-BZ-02-P-02", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 3, "definition_original": "日辰生扶", "rule_id": "R-BZ-02-P-03", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 4, "definition_original": "动爻生扶", "rule_id": "R-BZ-02-P-04", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 5, "definition_original": "动爻变空", "rule_id": "R-BZ-02-P-05", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 6, "definition_original": "伏而旺相", "rule_id": "R-BZ-02-P-06", "line": 2699, "enumeration_source": "editorial",
                }],
            },
            {
                "set_id": "BZ_SET_02_NEGATIVE", "set_name": "旬空論第十（真空到底空）", "chapter": "旬空論第十", "line": 2699,
                "polarity": "negative", "paired_with": "BZ_SET_02_POSITIVE",
                "count_declared": None, "count_actual": 4, "count_mismatch": None,
                "definition_original_full": "凡卦中爻遇旬空，乃神机发现于此也。如旺相旬空，或休囚发动，日辰生扶、动爻生扶、动爻变空、伏而旺相，此等旬空到底有用，不过待其出旬、值日、有合空、冲起、冲实、填补之法，后卷占验注明。如：休囚安静或日辰克动，爻克伏而被克，静逢月破值此旬空者，谓之真空到底空矣！",
                "segmentation_note": "切分依據：『如：』、『或』、『、』、『者』、『谓之真空到底空』。",
                "items": [{
                    "item_ordinal": 1, "definition_original": "休囚安静", "rule_id": "R-BZ-02-N-01", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 2, "definition_original": "日辰克动", "rule_id": "R-BZ-02-N-02", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 3, "definition_original": "爻克伏而被克", "rule_id": "R-BZ-02-N-03", "line": 2699, "enumeration_source": "editorial",
                }, {
                    "item_ordinal": 4, "definition_original": "静逢月破值此旬空者，谓之真空到底空矣！", "rule_id": "R-BZ-02-N-04", "line": 2699, "enumeration_source": "editorial",
                }],
            },
            {
                "set_id": "BZ_SET_03", "set_name": "辟增刪卜易之謬（暗動條）", "chapter": "辟增刪卜易之謬", "line": 436,
                "count_declared": None, "count_actual": 1, "count_mismatch": None,
                "definition_original_full": "暗动之法，必须旺相。旺相者，如人之身强力壮，虽遇冲而不散，故名为动；休囚者，如人之衰弱疲惫，遇冲则散，名为日破。岂可谓之暗动耶？《增删》不论旺相休囚，一概以日冲为暗动，此不知旺相休囚之辨，谬之甚也。",
                "segmentation_note": "不拆分；原文為連續論戰段落，無作者序數或項數宣告。",
                "items": [{
                    "item_ordinal": 1,
                    "definition_original": "暗动之法，必须旺相。旺相者，如人之身强力壮，虽遇冲而不散，故名为动；休囚者，如人之衰弱疲惫，遇冲则散，名为日破。岂可谓之暗动耶？《增删》不论旺相休囚，一概以日冲为暗动，此不知旺相休囚之辨，谬之甚也。",
                    "rule_id": "R-BZ-03-01", "line": 436,
                    "enumeration_source": "editorial",
                    "evidence_strength": "weak",
                    "evidence_note": "出自論戰文字，非其體例章節；全書「日破」僅此一處",
                }],
            },
        ],
    }


def cell(book_id: str, status: str, *, verdict: str | None = None, source: str | None = None,
         original: str | None = None, rule_id: str | None = None,
         framework_position: int | None = None, evidence_strength: str | None = None,
         negation_original: str | None = None, negation_source: str | None = None,
         negation_category: str | None = None, axis_note: str | None = None,
         axis_original: str | None = None, axis_source: str | None = None,
         cross_reference: str | None = None) -> dict:
    result = {"book_id": book_id, "status": status}
    if status in {"addressed", "not_addressed", "category_negated", "different_axis"}:
        result["verdict"] = verdict
    if source is not None:
        result["source"] = source
    if original is not None:
        result["original"] = original
    if rule_id is not None:
        result["rule_id"] = rule_id
    if framework_position is not None:
        result["framework_position"] = framework_position
    if evidence_strength is not None:
        result["evidence_strength"] = evidence_strength
    if negation_original is not None:
        result["negation_original"] = negation_original
    if negation_source is not None:
        result["negation_source"] = negation_source
    if negation_category is not None:
        result["negation_category"] = negation_category
    if axis_note is not None:
        result["axis_note"] = axis_note
    if axis_original is not None:
        result["axis_original"] = axis_original
    if axis_source is not None:
        result["axis_source"] = axis_source
    if cross_reference is not None:
        result["cross_reference"] = cross_reference
    return result


def different_axis_cell() -> dict:
    return cell(
        "huangjin_ce", "different_axis", verdict=None,
        axis_note="本書明文以動靜軸判沖（行 40「別衰旺以明剋合，辨動靜以定刑沖」），本表五格全繫於衰旺軸。其立場見 C15 決策表",
        axis_original="別衰旺以明剋合，辨動靜以定刑沖",
        axis_source="千金賦 40", cross_reference="C15",
    )


def decision_table() -> dict:
    rows = [
        ("C1-R1", "旺相之爻遇沖", [
            cell("yimao", "addressed", verdict="不散（為動）", source="類總章 690", original="一旺一衰，则衰散而旺动", rule_id="R-YM-04-03"),
            cell("zengshan", "addressed", verdict="不散", source="六沖章第二十 1525", original="爻遇日沖為暗動。", rule_id="R-ZS-08-02"),
            cell("buzhengzong", "addressed", verdict="不散", source="辟增刪卜易之謬 436", original="暗动之法，必须旺相。旺相者，如人之身强力壮，虽遇冲而不散，故名为动；休囚者，如人之衰弱疲惫，遇冲则散，名为日破。岂可谓之暗动耶？《增删》不论旺相休囚，一概以日冲为暗动，此不知旺相休囚之辨，谬之甚也。", rule_id="R-BZ-03-01", evidence_strength="weak"),
        ]),
        ("C1-R2", "有氣之爻遇沖", [
            cell("yimao", "not_addressed"),
            cell("zengshan", "addressed", verdict="不散", source="動散章 1673"),
            cell("buzhengzong", "not_addressed"),
        ]),
        ("C1-R3", "臨日月之爻遇沖", [
            cell("yimao", "addressed", verdict="不散", source="類總章 690；日沖章 416", original="临日月不散", rule_id="R-YM-04-02"),
            cell("zengshan", "not_addressed"),
            cell("buzhengzong", "not_addressed"),
        ]),
        ("C1-R4", "休囚之爻遇日沖", [
            cell("yimao", "addressed", verdict="散", source="日沖章 416；類總章 690", original="十八曰散，谓动逢日神变动之冲而散，虽救之无从，是谓大凶", rule_id="R-YM-01-18", framework_position=18),
            cell("zengshan", "category_negated", negation_original="余从来不言散", negation_source="元神忌神衰旺章第十 922", negation_category="散"),
            cell("buzhengzong", "addressed", verdict="散（名日破）", source="辟增刪卜易之謬 436", original="暗动之法，必须旺相。旺相者，如人之身强力壮，虽遇冲而不散，故名为动；休囚者，如人之衰弱疲惫，遇冲则散，名为日破。岂可谓之暗动耶？《增删》不论旺相休囚，一概以日冲为暗动，此不知旺相休囚之辨，谬之甚也。", rule_id="R-BZ-03-01", evidence_strength="weak"),
        ]),
        ("C1-R5", "既判為散之後", [
            cell("yimao", "addressed", verdict="不可救", source="類總章第 18 法", original="十八曰散，谓动逢日神变动之冲而散，虽救之无从，是谓大凶", rule_id="R-YM-01-18", framework_position=18),
            cell("zengshan", "not_addressed"),
            cell("buzhengzong", "not_addressed"),
        ]),
    ]
    output_rows = []
    for row_id, condition, cells in rows:
        cells.extend(
            different_axis_cell() if book["book_id"] == "huangjin_ce"
            else cell(book["book_id"], "not_collected")
            for book in BOOKS[3:]
        )
        row = {"row_id": row_id, "condition": condition, "cells": cells}
        if row_id == "C1-R1":
            row["row_title"] = "三家判不散，一家判損"
        row.update(calculate_coverage(row, books_total=len(BOOKS)))
        output_rows.append(row)
    return {"table_id": "C1", "title": "沖與散之判定", "conflict_ids": ["C1", "C11", "C12"],
            "books": BOOKS, "rows": output_rows}


def main() -> None:
    update_envelope("yimao")
    update_envelope("zengshan")
    write_json(DOCTRINAL / "buzhengzong_rules.json", buzhengzong())
    c1_path = TABLES / "C1_chong_san.json"
    if not c1_path.exists():
        write_json(c1_path, decision_table())


if __name__ == "__main__":
    main()
