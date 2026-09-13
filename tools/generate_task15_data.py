"""Generate TASK 15 doctrinal data from the cleaned 卜筮全書 corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DOCTRINAL = ROOT / "data" / "doctrinal"
TABLES = ROOT / "data" / "decision_tables"
DEFAULT_SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\06_卜筮全書\卜筮全書_古本.txt")


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 10462:
        raise ValueError(f"unexpected corpus line count: {len(lines)}")
    return lines


def line(lines: list[str], number: int) -> str:
    return lines[number - 1].strip()


def block(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[number - 1].rstrip() for number in range(start, end + 1)).strip()


def item(lines: list[str], *, line_no: int, chapter: str, rule_id: str,
         text: str | None = None, ordinal: int = 1) -> dict:
    original = line(lines, line_no) if text is None else text
    if text is not None and text not in line(lines, line_no):
        raise ValueError(f"item fragment is not verbatim at line {line_no}: {text}")
    return {
        "item_ordinal": ordinal,
        "line": line_no,
        "chapter": chapter,
        "definition_original": original,
        "rule_id": rule_id,
        "enumeration_source": "editorial",
    }


def make_set(lines: list[str], *, set_id: str, set_name: str, chapter: str,
             full_ranges: Iterable[tuple[int, int]], items: list[dict],
             void_system_id: str | None = None,
             equivalent_to_qing_term: str | None = None,
             equivalence_note: str | None = None) -> dict:
    result = {
        "set_id": set_id,
        "set_name": set_name,
        "chapter": chapter,
        "line": items[0]["line"],
        "count_declared": None,
        "count_actual": len(items),
        "count_mismatch": None,
        "enumeration_source": "editorial",
        "definition_original_full": "\n\n".join(block(lines, start, end) for start, end in full_ranges),
        "segmentation_note": "編者按採集報告之原文並列結構分 item；原書無項數宣告。",
        "items": items,
    }
    if void_system_id is not None:
        result["void_system_id"] = void_system_id
        result["equivalent_to_qing_term"] = equivalent_to_qing_term
        result["equivalence_note"] = equivalence_note
    return result


def build_rules(lines: list[str]) -> dict:
    sets: list[dict] = []

    sets.append(make_set(
        lines, set_id="BQ_SET_VOID_MENTIONED", set_name="四條空亡立目",
        chapter="卷四·闡奧歌章上", full_ranges=[(3314, 3317), (3378, 3381), (3396, 3398), (3406, 3410)],
        items=[
            item(lines, line_no=3316, chapter="卷四·四 世應生克動靜空亡訣", rule_id="R-BQ-VOID-MENTION-01", ordinal=1),
            item(lines, line_no=3380, chapter="卷四·十四 用爻不上卦或落空亡訣", rule_id="R-BQ-VOID-MENTION-02", ordinal=2),
            item(lines, line_no=3398, chapter="卷四·十七 用爻空亡訣", rule_id="R-BQ-VOID-MENTION-03", ordinal=3),
            item(lines, line_no=3408, chapter="卷四·十九 六神空亡訣", rule_id="R-BQ-VOID-MENTION-04", ordinal=4),
        ],
    ))

    sets.append(make_set(
        lines, set_id="BQ_SET_02", set_name="總斷千金賦論空",
        chapter="卷八·總斷千金賦", full_ranges=[(5557, 5561)],
        items=[
            item(lines, line_no=5558, chapter="卷八·總斷千金賦", rule_id="R-BQ-02-01", text="夫空之一字，极有玄妙；若执真空，便失先天之旨。盖百物自空中来，无中生有，还归于空。空中不受伤克，反有可成之机。", ordinal=1),
            item(lines, line_no=5559, chapter="卷八·總斷千金賦", rule_id="R-BQ-02-02", text="如六爻安静，用爻无故自空，此为真空，万事无成。", ordinal=2),
            item(lines, line_no=5559, chapter="卷八·總斷千金賦", rule_id="R-BQ-02-03", text="若被日辰动爻刑冲克害于用爻，而用爻在空，此为避凶而空。", ordinal=3),
            item(lines, line_no=5560, chapter="卷八·總斷千金賦", rule_id="R-BQ-02-04", ordinal=4),
            item(lines, line_no=5561, chapter="卷八·總斷千金賦", rule_id="R-BQ-02-05", ordinal=5),
        ],
    ))

    song_items = [
        "子落空亡忧远行", "病值空亡宜作福", "久病空亡身【下亡】", "财若空亡难把捉",
        "鬼遇空亡官事停", "妻值空亡妻有孕", "空女空亡有外情", "宅值空亡急作福",
        "父母空亡忧病生", "兄弟空亡不得力", "子孙空亡主伶仃",
    ]
    sets.append(make_set(
        lines, set_id="BQ_SET_03", set_name="斷易通玄賦六親空亡歌訣",
        chapter="卷四·二 斷易通玄賦", full_ranges=[(3268, 3270)],
        items=[item(lines, line_no=3270, chapter="卷四·二 斷易通玄賦", rule_id=f"R-BQ-03-{n:02d}", text=text, ordinal=n)
               for n, text in enumerate(song_items, 1)],
    ))

    travel_items = [
        (4909, "五位逢空，路上凄凉无旅店"),
        (4909, "六爻临鬼，地头寂寞有忧愁"),
        (4910, "初爻空亡无脚子"), (4910, "二爻空亡身有阻"),
        (4910, "三爻空亡伴侣稀"), (4910, "四爻空亡难出户"),
        (4910, "五爻若也值空亡，旅店荒凉受辛苦"),
        (4910, "更看六爻若逢空，地头寂寞无人住"),
        (4910, "六爻俱不落空亡，任意挥鞭千里去"),
        (4911, "凡吉神空则凶，凶神空则吉"),
    ]
    sets.append(make_set(
        lines, set_id="BQ_SET_04", set_name="六爻空亡歌",
        chapter="卷六·九 出行章", full_ranges=[(4909, 4912)],
        items=[item(lines, line_no=line_no, chapter="卷六·九 出行章", rule_id=f"R-BQ-04-{n:02d}", text=text, ordinal=n)
               for n, (line_no, text) in enumerate(travel_items, 1)],
    ))

    sets.append(make_set(
        lines, set_id="BQ_SET_05", set_name="總斷千金賦空亡諸節",
        chapter="卷八·總斷千金賦", full_ranges=[(5458, 5470), (5488, 5490), (5574, 5578)],
        items=[
            item(lines, line_no=5459, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-01", ordinal=1),
            item(lines, line_no=5462, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-02", ordinal=2),
            item(lines, line_no=5463, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-03", ordinal=3),
            item(lines, line_no=5470, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-04", ordinal=4),
            item(lines, line_no=5489, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-05", ordinal=5),
            item(lines, line_no=5490, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-06", ordinal=6),
            item(lines, line_no=5578, chapter="卷八·總斷千金賦", rule_id="R-BQ-05-07", ordinal=7),
        ],
    ))

    void_note = "清代三家未見對應術語，是否棄用未查（見 C13）"
    sets.extend([
        make_set(lines, set_id="BQ_SET_VOID_01", set_name="六甲空亡", chapter="卷十四", full_ranges=[(10429, 10431)], void_system_id="liujia_kongwang", equivalent_to_qing_term="旬空", equivalence_note="清代三家所稱之旬空，對應本書之六甲空亡。此對應為編者判定，非原文明言。", items=[
            item(lines, line_no=10430, chapter="卷十四·六甲空亡", rule_id="R-BQ-VOID-01-01", ordinal=1),
            item(lines, line_no=10431, chapter="卷十四·六甲空亡", rule_id="R-BQ-VOID-01-02", ordinal=2),
        ]),
        make_set(lines, set_id="BQ_SET_VOID_02", set_name="天地空亡", chapter="卷十一·墳墓", full_ranges=[(8416, 8420)], void_system_id="tiandi_kongwang", equivalent_to_qing_term=None, equivalence_note=void_note, items=[
            item(lines, line_no=8417, chapter="卷十一·墳墓·天地空亡", rule_id="R-BQ-VOID-02-01", ordinal=1),
            item(lines, line_no=8419, chapter="卷十一·墳墓·天地空亡", rule_id="R-BQ-VOID-02-02", text="壬子乃天地空亡。", ordinal=2),
            item(lines, line_no=8419, chapter="卷十一·墳墓·天地空亡", rule_id="R-BQ-VOID-02-03", text="甲子天干日从乾上起，顺飞至乾，乾遇得癸。地支子从坎上类起，顺飞至坎，遇金住。天干乃遇乾，地支遇坎，乃乾中有壬，坎中有子，壬子乃天地空亡。", ordinal=3),
            item(lines, line_no=8420, chapter="卷十一·墳墓·天地空亡", rule_id="R-BQ-VOID-02-04", text="甲申，甲午为天地空亡。", ordinal=4),
            item(lines, line_no=8420, chapter="卷十一·墳墓·天地空亡", rule_id="R-BQ-VOID-02-05", text="命见乙酉，穴见己丑，亦是天地空亡也。", ordinal=5),
        ]),
        make_set(lines, set_id="BQ_SET_VOID_03", set_name="四大空亡", chapter="卷十一·墳墓", full_ranges=[(8416, 8420)], void_system_id="sidakong_kongwang", equivalent_to_qing_term=None, equivalence_note=void_note, items=[
            item(lines, line_no=8416, chapter="卷十一·墳墓·四大空亡", rule_id="R-BQ-VOID-03-01", ordinal=1),
            item(lines, line_no=8418, chapter="卷十一·墳墓·四大空亡", rule_id="R-BQ-VOID-03-02", text="四位：如四大空亡。", ordinal=2),
            item(lines, line_no=8420, chapter="卷十一·墳墓·四大空亡", rule_id="R-BQ-VOID-03-03", text="甲子旬中见水为四大空亡。", ordinal=3),
        ]),
        make_set(lines, set_id="BQ_SET_VOID_04", set_name="截路空亡", chapter="卷十四", full_ranges=[(10433, 10435)], void_system_id="jielu_kongwang", equivalent_to_qing_term=None, equivalence_note=void_note, items=[
            item(lines, line_no=10434, chapter="卷十四·截路空亡", rule_id="R-BQ-VOID-04-01", ordinal=1),
            item(lines, line_no=10435, chapter="卷十四·截路空亡", rule_id="R-BQ-VOID-04-02", ordinal=2),
        ]),
        make_set(lines, set_id="BQ_SET_VOID_05", set_name="五空", chapter="卷十一·墳墓", full_ranges=[(8422, 8423)], void_system_id="wu_kong", equivalent_to_qing_term=None, equivalence_note=void_note, items=[
            item(lines, line_no=8423, chapter="卷十一·墳墓·五空", rule_id="R-BQ-VOID-05-01", ordinal=1),
        ]),
    ])

    month_items = [
        (3173, "出现怕临月破。（假如正月建寅，用爻是申，为月破也。）", "卷三·斷易總論"),
        (3173, "伏藏不论旬空，（旬空者：甲子旬中戌亥空之类）出现怕临月破。", "卷三·斷易總論"),
        (3184, None, "卷三·斷易總論"), (8061, None, "卷十一·家宅"), (8062, None, "卷十一·家宅"),
        (8240, None, "卷十一"), (8323, None, "卷十一·墳墓"), (8465, None, "卷十一"),
        (9804, None, "卷十三"), (9892, None, "卷十三"), (9991, None, "卷十三"),
    ]
    sets.append(make_set(
        lines, set_id="BQ_SET_MONTH_BREAK", set_name="月破相關散見材料",
        chapter="卷三、卷十一、卷十三", full_ranges=[(3173, 3173), (3184, 3184), (8061, 8062), (8240, 8240), (8323, 8323), (8465, 8465), (9804, 9804), (9892, 9892), (9991, 9991)],
        items=[item(lines, line_no=line_no, chapter=chapter, rule_id=f"R-BQ-MONTH-{n:02d}", text=text, ordinal=n) for n, (line_no, text, chapter) in enumerate(month_items, 1)],
    ))

    dark_items = [
        (78, None, "目錄·卷三·五 逢沖暗動"), (3117, None, "卷三·五 逢沖暗動"),
        (3119, "若日辰相冲，名曰暗动。", "卷三·五 逢沖暗動"),
        (3119, "暗动者，有吉有凶，各有所用，不可一概而论。", "卷三·五 逢沖暗動"),
        (3119, "若遇凶煞暗动,伤身克世，件件皆非所宜。吉神暗动，合世生身，事事无不为吉。", "卷三·五 逢沖暗動"),
        (3121, None, "卷三·五 逢沖暗動"), (4411, None, "卷六·啟蒙／卦爻呈象"),
        (4435, "爻虽安静，见冲则为暗动，动爻遇冲则散，空亡遇冲则不空。", "卷六·二 身命章"),
        (5226, None, "卷七·天玄賦下"), (5227, None, "卷七·天玄賦下"),
        (5483, None, "卷八·總斷千金賦"), (5860, None, "卷八·總斷千金賦"),
        (6175, None, "卷九·黃金策二"), (6176, None, "卷九·黃金策二"),
        (6723, None, "卷九·黃金策二"),
        (9808, "鬼临初位暗兴，宅有伏尸古煞；", "卷十三"),
        (9808, "官遇六爻暗动，匠工作弊为殃。", "卷十三"),
    ]
    sets.append(make_set(
        lines, set_id="BQ_SET_DARK_MOVE", set_name="暗動相關散見材料",
        chapter="卷三、卷六、卷七、卷八、卷九、卷十三", full_ranges=[(3117, 3128), (4435, 4435), (5226, 5227), (5483, 5483), (5860, 5860), (6175, 6176), (6723, 6723), (9808, 9808)],
        items=[item(lines, line_no=line_no, chapter=chapter, rule_id=f"R-BQ-DARK-{n:02d}", text=text, ordinal=n) for n, (line_no, text, chapter) in enumerate(dark_items, 1)],
    ))

    closed = [
        ("BQ_SET_CLOSED_01", "隨官入墓其目有三", "卷三·四 隨官入墓", [(3095, 3111)], [(3097, "有身随鬼入墓"), (3097, "有世随鬼入墓"), (3097, "有命随鬼入墓")]),
        ("BQ_SET_CLOSED_02", "貴人有二", "卷六·五 求仕章", [(4680, 4680)], [(4680, "有天乙贵人"), (4680, "有福星贵人")]),
        ("BQ_SET_CLOSED_03", "青龍其動有三", "卷六·五 求仕章", [(4682, 4683)], [(4683, "年建青龙"), (4683, "月建青龙"), (4683, "日建青龙")]),
        ("BQ_SET_CLOSED_04", "陰陽得位有兩端", "卷六·三 伉儷章", [(4533, 4534)], [(4533, "有封象外阴内阳"), (4533, "有应阴世阳")]),
        ("BQ_SET_CLOSED_05", "生扶拱合以上四者", "卷八·總斷千金賦", [(5378, 5383)], [(5379, None), (5380, None), (5381, None), (5382, None)]),
        ("BQ_SET_CLOSED_06", "克害刑沖以上四者", "卷八·總斷千金賦", [(5385, 5390)], [(5386, None), (5387, None), (5388, None), (5389, None)]),
        ("BQ_SET_CLOSED_07", "死墓絕空四者", "卷八·總斷千金賦", [(5395, 5401)], [(5396, None), (5397, None), (5398, None), (5399, None)]),
        ("BQ_SET_CLOSED_08", "沖之三分法（卷八）", "卷八·總斷千金賦", [(5647, 5648)], [(5648, "如空爻逢冲则实"), (5648, "动爻逢冲则散，又谓冲脱"), (5648, "静逢冲则动，又谓冲起")]),
        ("BQ_SET_CLOSED_09", "沖之三分法（卷六）", "卷六·二 身命章", [(4431, 4435)], [(4435, "爻虽安静，见冲则为暗动"), (4435, "动爻遇冲则散"), (4435, "空亡遇冲则不空")]),
        ("BQ_SET_CLOSED_10", "旺／絕／空逢沖三分法", "卷七·六畜章", [(5077, 5081)], [(5081, "旺处逢冲则损"), (5081, "绝处逢冲则散"), (5081, "空处逢冲则不空")]),
        ("BQ_SET_CLOSED_11", "太歲前十二神煞", "卷十四·神煞歌例", [(10298, 10300)], [(10300, "太岁剑锋伏尸同"), (10300, "二曰太阳并天空"), (10300, "三是丧门主孝服"), (10300, "四为勾绞贯索凶"), (10300, "五位官符兼五鬼"), (10300, "六曰死符小耗攻"), (10300, "七是栏干并大耗"), (10300, "八为暴败天厄中"), (10300, "九是飞廉同白虎"), (10300, "十为褔德卷舌从"), (10300, "十一天狗并吊客"), (10300, "十二病符切莫逢")]),
        ("BQ_SET_CLOSED_12", "退神四支", "卷六·十 行人章", [(4947, 4947)], [(4947, "丁丑"), (4947, "丁未"), (4947, "壬辰"), (4947, "壬戌")]),
        ("BQ_SET_CLOSED_13", "五空", "卷十一·墳墓", [(8422, 8423)], [(8423, "乾：壬申，戌亥"), (8423, "兑：丁酉"), (8423, "艮：丙丑，寅"), (8423, "离：巳午"), (8423, "坎：戊子"), (8423, "坤：乙未，申"), (8423, "震：寅卯"), (8423, "巽：辰巳")]),
    ]
    for set_id, name, chapter, ranges, fragments in closed:
        sets.append(make_set(lines, set_id=set_id, set_name=name, chapter=chapter, full_ranges=ranges,
                             items=[item(lines, line_no=line_no, chapter=chapter, rule_id=f"R-BQ-{set_id[9:]}-{n:02d}", text=text, ordinal=n)
                                    for n, (line_no, text) in enumerate(fragments, 1)]))

    sets.append(make_set(
        lines, set_id="BQ_SET_BODY", set_name="世身法",
        chapter="卷一·十六 安身訣／十七 起月卦身訣", full_ranges=[(575, 585)],
        items=[
            item(lines, line_no=577, chapter="卷一·十六 安身訣", rule_id="R-BQ-BODY-01", ordinal=1),
            item(lines, line_no=584, chapter="卷一·十七 起月卦身訣", rule_id="R-BQ-BODY-02", ordinal=2),
            item(lines, line_no=585, chapter="卷一·十七 起月卦身訣", rule_id="R-BQ-BODY-03", ordinal=3),
        ],
    ))

    return {
        "book_id": "buzhequanshu",
        "source_book": "卜筮全書",
        "era": "明",
        "author": "姚際隆刪補",
        "attribution_status": "compiled",
        "framework_type": "by_topic_no_chapters",
        "framework_note": "無專章體例。以事類編排，術語散見占斷之中。以相關術語立目者僅四條，全部用「空亡」。「空亡」為複數概念，含六甲空亡、天地空亡、四大空亡、截路空亡、五空",
        "enumeration_style": "none",
        "doctrinal_status": "single_school",
        "semantic_status": "structured_only_no_effects_implemented",
        "conflicts_with": ["C1", "C11", "C12", "C13"],
        "corpus_path": "06_卜筮全書/卜筮全書_古本.txt",
        "corpus_note": "以古本為準。原檔含現代編校者注解 164 行及《易經》增補 642 行，已分離，不得入庫",
        "provenance_gap": "本檔取得網址／版次未曾記錄（待核項 P-015）",
        "sets": sets,
    }


def update_c1() -> None:
    path = TABLES / "C1_chong_san.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for book in data["books"]:
        if book["book_id"] == "bushi_quanshu":
            book["book_id"] = "buzhequanshu"
    for row in data["rows"]:
        for cell in row["cells"]:
            if cell["book_id"] != "bushi_quanshu" and cell["book_id"] != "buzhequanshu":
                continue
            cell["book_id"] = "buzhequanshu"
            if row["row_id"] == "C1-R1":
                cell.update({"status": "addressed", "verdict": None, "source": "採集報告 R1-a 5080–5081、R1-b 5500–5505、R1-c 5403–5408", "original": "大凡旺处逢冲则损，绝处逢冲则散，空处逢冲则不空。", "rule_id": "R-BQ-C1-R1"})
            elif row["row_id"] == "C1-R2":
                cell.update({"status": "not_addressed", "verdict": None, "search_note": "以『有气／得地／得时／当令／得令／月令／有力』分别與『冲／散／空亡』交叉搜尋；覆蓋古本全檔 10,462 行；命中 0。"})
                for key in ("source", "original", "rule_id", "evidence_strength"):
                    cell.pop(key, None)
            elif row["row_id"] == "C1-R3":
                cell.update({"status": "addressed", "verdict": None, "source": "採集報告 R3-a 5515–5516、R3-b 7801–7803、R3-c 5410–5414", "original": "虽见刑冲克害，不能挫其势。", "rule_id": "R-BQ-C1-R3"})
            elif row["row_id"] == "C1-R4":
                cell.update({"status": "addressed", "verdict": None, "source": "採集報告 R4-a 3119、R4-b 4435、R4-c 3170–3173、R4-d 5568–5569", "original": "动爻遇冲则散。", "rule_id": "R-BQ-C1-R4"})
            elif row["row_id"] == "C1-R5":
                cell.update({"status": "not_addressed", "verdict": None, "search_note": "搜尋『散＋救／解／复／仍／还』、『不散／难散／未散／虽散／既散／已散／冲脱／冲起』；覆蓋古本全檔 10,462 行，並逐一檢視 120 處『散』上下文；命中 15 句，無一回答散後可否救。"})
                for key in ("source", "original", "rule_id", "evidence_strength"):
                    cell.pop(key, None)
    write_json(path, data)


def write_c13() -> None:
    books = [
        {"book_id": "yimao", "name": "易冒"}, {"book_id": "zengshan", "name": "增刪卜易"},
        {"book_id": "buzhengzong", "name": "卜筮正宗"}, {"book_id": "huozhulin", "name": "火珠林"},
        {"book_id": "huangjin_ce", "name": "黃金策"}, {"book_id": "buzhequanshu", "name": "卜筮全書"},
        {"book_id": "jing_shi_yizhuan", "name": "京氏易傳"}, {"book_id": "yiyin", "name": "易隱"},
    ]
    systems = [
        {"void_system_id": "liujia_kongwang", "name": "六甲空亡"},
        {"void_system_id": "tiandi_kongwang", "name": "天地空亡"},
        {"void_system_id": "sidakong_kongwang", "name": "四大空亡"},
        {"void_system_id": "jielu_kongwang", "name": "截路空亡"},
        {"void_system_id": "wu_kong", "name": "五空"},
    ]
    searched_books = {"yimao", "zengshan", "buzhengzong"}
    search_note = "TASK_17 於該書全檔逐行檢索，命中 0 次。檢索詞：天地空亡、四大空亡、截路空亡、五空、六甲空亡。三本合計 17,742 行"
    own_systems = {
        "yimao": {
            "own_system": "旬空章十三法（建空、動空、填空、旺空、相空、半空、援空、安空、破空、絕空、真空、克空、傷空）；另類總章八法",
            "source": "旬空章第二十六 399–402；類總章第四十一 692",
        },
        "zengshan": {
            "own_system": "轉述「諸書」十四項：真空、假空、動空、沖空、填空、援空、無故自空、有故而空、散空、墓空、絕空、害空、安空、破空；野鶴另有自述條例",
            "source": "旬空章第二十六 1842–1844",
        },
        "buzhengzong": {
            "own_system": "不立名目清單，以四句立條例",
            "source": "旬空論第十",
        },
    }
    rows = []
    for book in books:
        rows.append({
            "row_id": f"C13-{book['book_id']}",
            "book_id": book["book_id"],
            "cells": [
                {
                    "void_system_id": system["void_system_id"],
                    "status": (
                        "addressed" if book["book_id"] == "buzhequanshu"
                        else "not_addressed" if book["book_id"] in searched_books
                        else "not_collected"
                    ),
                    **({"search_note": search_note} if book["book_id"] in searched_books else {}),
                }
                for system in systems
            ],
        })
    rows.append({
        "row_id": "C13-OWN",
        "condition": "該書自有之空亡分類系統",
        "note": "此列不與上方五套對齊。各家名目互不重疊，屬 C12 類型五",
        "cells": [
            {
                "book_id": book["book_id"],
                "status": "addressed" if book["book_id"] in own_systems else "not_collected",
                **own_systems.get(book["book_id"], {}),
            }
            for book in books
        ],
    })
    write_json(TABLES / "C13_kongwang_scope.json", {
        "table_id": "C13",
        "title": "空亡之所指範圍",
        "conflict_ids": ["C13", "C11", "C12"],
        "books": books,
        "void_systems": systems,
        "rows": rows,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    lines = load_lines(args.source)
    write_json(DOCTRINAL / "buzhequanshu_rules.json", build_rules(lines))
    update_c1()
    write_c13()


if __name__ == "__main__":
    main()
