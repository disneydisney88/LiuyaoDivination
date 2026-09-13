"""Generate the source-structured Yi Mao closed-set catalogue."""

from __future__ import annotations

import json
from pathlib import Path


SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\07_易冒\易冒.txt")
OUTPUT = Path("data/doctrinal/yimao_rules.json")


def item(set_id, set_name, chapter, line, ordinal, name, definition, *, incomplete=False, shared_with=None, rank=None, band=None, comparative=None, exception=None):
    result = {
        "set_id": set_id,
        "set_name": set_name,
        "source": "易冒",
        "chapter": chapter,
        "line": line,
        "item_ordinal": ordinal,
        "item_name": name,
        "definition_original": definition,
        "severity_rank": rank,
        "severity_band": band,
        "comparative_original": comparative,
        "exception_original": exception,
        "rule_id": f"R-{set_id.replace('YM_SET_', 'YM-').replace('_', '-')}-{ordinal:02d}",
    }
    if incomplete:
        result["definition_incomplete"] = True
    if shared_with is not None:
        result["definition_shared_with"] = shared_with
    return result


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    assert "类总章第四十一" in source_text
    full_good = "全吉"
    half_good = "半吉"
    bad = "凶陷"

    sets = []

    names = [
        ("日神", "一曰日神", False, None, 2),
        ("月将", "二曰月将，言用临日月也", False, None, None),
        ("旺", "三曰旺，日月之扶也", False, None, None),
        ("相", "四曰相，日月之生也", False, None, None),
        ("生", "五曰生，生言贪生忘克，转转来生也", False, None, None),
        ("变生", "六曰变生", False, None, 7),
        ("动生", "七曰动生，变生亲而动生疏也", False, None, None),
        ("安", "八曰安，无伤而无泄也", False, None),
        ("有玷", "九曰有玷，或日克而月生，或月克而日生，吉之半也", False, "吉之半"),
        ("旺相空", "十曰旺相空，吉之又半也", False, None),
        ("安空", "十一曰安空，有生无克，求多不得而未至丧也，此用神半吉之象也", False, None),
        ("泄气", "十二曰泄气，谓日月动爻皆泄用神之气，物不生矣，重于安空，有生仅全，有克乃没", False, "重于安空"),
        ("死气", "十三曰死气，虽不遇空破，而日月动爻或一再克之，而无明暗之生，亦重于安空也", False, "亦重于安空"),
        ("日破", "十四曰日破，日月克伤，时令休囚，爻神被冲，破其半矣，又重于死气也", False, "又重于死气"),
        ("月破", "十五曰月破，破而尚存其质也", False, None),
        ("克空", "十六曰克空，日月动爻克之且空，是无救也", False, None),
        ("竟无", "十七曰竟无，谓日月飞伏变互，皆不得其用神，又重于克空矣", False, "又重于克空矣"),
        ("散", "十八曰散，谓动逢日神变动之冲而散，虽救之无从，是谓大凶", False, None),
    ]
    items = []
    for ordinal, (name, definition, incomplete, comparative, *shared) in enumerate(names, 1):
        shared_with = shared[0] if shared else None
        items.append(item("YM_SET_01", "看用神十八法", "類總章第四十一", 698, ordinal, name, definition, incomplete=incomplete, shared_with=shared_with, rank=ordinal, band=full_good if ordinal <= 8 else half_good if ordinal <= 11 else bad, comparative=comparative, exception="唯竟無若當時相，及一象來生，猶勝於死氣" if ordinal == 17 else None))
    sets.append({"set_id": "YM_SET_01", "set_name": "看用神十八法", "chapter": "類總章第四十一", "line": 698, "declared_count": 18, "actual_count": 18, "count_mismatch": False, "items": items})

    sets.append({"set_id": "YM_SET_02", "set_name": "世應十忌", "chapter": "類總章第四十一", "line": 680, "declared_count": 10, "actual_count": 10, "count_mismatch": False, "items": [
        item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 1, "有空", "空则无成"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 2, "有破", "破则多败"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 3, "有绝", "绝则多困"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 4, "有散", "散则全失"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 5, "有墓", "墓则难举"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 6, "有动", "动则多变"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 7, "有合冲", "合冲则将成而败"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 8, "有随墓", "随墓讼病之恶地"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 9, "有助伤", "助伤灾患之凶征"), item("YM_SET_02", "世應十忌", "類總章第四十一", 680, 10, "有升降进退", "进升如火之始燃，退降如木之方落"),
    ]})

    def make_set(set_id, name, line, entries, declared):
        return {"set_id": set_id, "set_name": name, "chapter": "類總章第四十一" if line in (680, 686, 690, 692) else name.split("（")[0], "line": line, "declared_count": declared, "actual_count": len(entries), "count_mismatch": declared != len(entries), "items": [item(set_id, name, "類總章第四十一", line, n, item_name, definition) for n, (item_name, definition) in enumerate(entries, 1)]}

    sets.append(make_set("YM_SET_03", "冲法有五", 690, [("相扶而冲", "相扶而冲者谓之暗动"), ("相绝而冲", "相绝而冲者谓之散，不及暗动"), ("相胎而冲", "相胎而冲者，我克为动，克我为散"), ("胎绝之冲", "胎绝之冲，旺相为动，休囚为散"), ("暗冲之散", "暗冲之散，胜动冲之散，动散无暗散敝")], 5))
    sets.append(make_set("YM_SET_04", "自冲有三", 690, [("力相敌者皆散", "力相敌者皆散"), ("临日月不散", "临日月不散"), ("一旺一衰", "一旺一衰，则衰散而旺动")], 3))
    sets.append(make_set("YM_SET_05", "合法有三", 690, [("生合", "生合吉"), ("克合", "克合凶"), ("刑合", "刑次之")], 3))
    sets.append(make_set("YM_SET_06", "旬空之法有八", 692, [("月破而空", "月破而空，谓之坏空"), ("月克而空", "月克而空，谓之全空"), ("月生日克，日生月克", "月生日克，日生月克，谓之克空"), ("无生无克", "无生无克，谓之安空"), ("日月独生", "日月独生，谓之半空"), ("日月生扶", "日月生扶，谓之旺相空，旬内空而旬外实"), ("日冲则实", "日冲则实，动空则实，月建临之则实，皆谓之填实空"), ("动空而遭破", "动空而遭破，纵动无功，空冲而遇绝散，虽冲不力")], 8))
    sets.append(make_set("YM_SET_07", "月破之法有三", 692, [("破临鬼动", "破临鬼动而凶，破临动冲而无"), ("临日", "临日不破"), ("遇时", "遇时不破")], 3))
    sets.append({"set_id": "YM_SET_08", "set_name": "飛伏五態", "chapter": "類總章第四十一", "line": 686, "declared_count": 5, "actual_count": 5, "count_mismatch": False, "items": [item("YM_SET_08", "飛伏五態", "類總章第四十一", 686, n, name, definition) for n, (name, definition) in enumerate([("伏克飞", "伏克飞者出"), ("飞生伏", "飞生伏者得"), ("飞克伏", "飞克伏者灭"), ("伏生飞", "伏生飞者没"), ("飞伏比和", "飞伏比和者拔")], 1)]})

    set09_entries = [("暗动", "日冲安旺之爻为暗动", 415), ("暗破", "日冲静衰之爻谓暗破", 415), ("实", "空爻遇冲谓之实", 415), ("散", "动爻遇冲谓之散", 415), ("墓冲", "辰戌丑未为墓冲", 418), ("胎冲", "子午卯酉为胎冲", 418), ("绝冲", "寅申巳亥为绝冲", 418), ("克冲", "克冲有三", 418)]
    sets.append({"set_id": "YM_SET_09", "set_name": "日冲四法＋墓胎克绝四法", "chapter": "日冲章第二十七", "line": 415, "declared_count": 8, "actual_count": 8, "count_mismatch": False, "items": [item("YM_SET_09", "日冲四法＋墓胎克绝四法", "日冲章第二十七", line, n, name, definition) for n, (name, definition, line) in enumerate(set09_entries, 1)]})

    set10_entries = [
        ("建空", "月建值空，谓建空，犹不空，反有用也"), ("动空", "动爻值空，谓动空，不惟不空，反为动也"), ("填空", "空爻遇冲为填空，若有旺相生扶，乃为填实，若遇休囚伤克，乃谓不全填实也"), ("旺空", "旺相之爻值空，为旺相空"), ("相空", "旺相之爻值空，为旺相空"), ("半空", "若日辰泄其气，即为半空"), ("援空", "动爻日辰来生空爻，乃谓援空"), ("安空", "日月动爻皆不来克空爻，乃谓安空"), ("破空", "月破值空，谓破空"), ("绝空", "绝于月为绝空"), ("真空", "春土夏金秋是木，三冬知火是真空"), ("克空", "得一日辰或动爻来生，即成克空"), ("伤空", "如日辰动爻或一来克，即谓伤空")
    ]
    set10_lines = [400, 400, 400, 400, 400, 400, 400, 402, 402, 402, 402, 402, 402]
    sets.append({"set_id": "YM_SET_10", "set_name": "旬空十三法", "chapter": "旬空章第二十六", "line": 399, "declared_count": 13, "actual_count": 13, "count_mismatch": False, "items": [item("YM_SET_10", "旬空十三法", "旬空章第二十六", set10_lines[n - 1], n, name, definition) for n, (name, definition) in enumerate(set10_entries, 1)]})

    sets.append({"set_id": "YM_SET_11", "set_name": "疾病七法", "chapter": "疾病章第五十五", "line": 1034, "count_declared": 7, "count_actual": 6, "count_mismatch": True, "note_original": "原文 1035 行夾註稱「以上七法系大凶」，而 1034 行實列六項：動散、月破、克空、日破、受傷無援、脫氣", "items": [item("YM_SET_11", "疾病七法", "疾病章第五十五", 1035, n, name, definition) for n, (name, definition) in enumerate([("动散", "动散"), ("月破", "月破"), ("克空", "克空"), ("日破", "日破"), ("受伤无援", "受伤无援"), ("脱气", "脱气")], 1)]})

    payload = {
        "source_book": "易冒",
        "source_file": "07_易冒/易冒.txt",
        "extraction_task": "TASK_CODEX_07",
        "semantic_status": "structured_only_no_effects_implemented",
        "warning": "排序非全序，見 YM_SET_01 item_ordinal 17 之 exception_original",
        "sets": sets,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
