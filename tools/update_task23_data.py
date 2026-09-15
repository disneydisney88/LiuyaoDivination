"""Regenerate TASK_CODEX_23 table metadata from repository data inventory."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "data" / "decision_tables"
DOCTRINAL_DIR = ROOT / "data" / "doctrinal"
CHONG_SOURCE_NOTE = (
    "**本表格位未區分月沖、日沖。** 而《易冒》〈類總章〉688 明文分判："
    "「月沖破，日沖散」「日有隨墓助傷，而月則無也，故日尤親」。"
    "故本表之「遇沖」係本項目之合併，非各家原有。詳見待決項 P-056。"
)
TABLE_NOTES = {
    "C1": (
        "R1–R5 五個條件係本項目從《易冒》十八法與野鶴之論述反推所得之切法，"
        "非各書自身之設問方式。\n\n"
        "其他書並無義務按此五格立說。《卜筮全書》按事類編排、全書無專章體例，其「未表述」"
        "部分反映的是本表提問方式偏向《易冒》，而非該書材料貧乏。\n\n"
        + CHONG_SOURCE_NOTE
    ),
    "C15": (
        "R1–R3 三個條件源自《黃金策》千金賦行 30、34、76 之三分法（空逢沖而有用／靜得沖而暗興／"
        "動逢沖而事散），其軸向由該書行 40 明文宣告：「別衰旺以明剋合，**辨動靜以定刑沖**」。\n\n"
        "**此軸與 C1（衰旺軸）不可互譯。** 一個爻可以同時是「動」與「休囚」，兩軸對同一爻給出不同的"
        "判定路徑，各家未曾提供換算方式。\n\n"
        "**本表之提問方式偏向《黃金策》。** 清代三家皆以衰旺軸論沖，故其在本表多為「未就本表之問題採集」"
        "—— 此為採集缺口，非該書無立場。\n\n"
        + CHONG_SOURCE_NOTE
    ),
    "K": (
        "K-R1 至 K-R10 十格係本項目依各家空亡材料所擬之切法，**繫於空爻之狀態**"
        "（旺相／休囚／動／靜／遇沖／得生扶／伏／出旬／逢月破／逢絕）。\n\n"
        "**《火珠林》不依此軸**：該書判空看的是**哪個爻空**（世／應／官／財），行 991 一句之內世空、"
        "應空、世應俱空三結論各異，而全句無一字涉旺衰動靜。故其在本表標「另一軸向」。\n\n"
        "**《易冒》有兩套旬空分類**：〈旬空章第二十六〉十三法、〈類總章第四十一〉八法，名目部分重疊"
        "但不相同。本表二者並列，不合併、不擇一。\n\n"
        "K-R4（靜爻值旬空）之對應較弱 —— 各家論「靜」時多連帶其他條件（休囚安靜、有氣不動），少有單講"
        "「靜」。「靜」本身可能非各家之切分維度，本格保留但須知此事。"
    ),
    "Y": (
        "Y-R1 至 Y-R10 十格係本項目所擬之切法，**繫於單爻之狀態**（元神／忌神各自之旺相、休囚、"
        "旬空、月破、化退、入墓、動而剋）。\n\n"
        "**《易冒》不依此軸**：該書以「喜／忌」表述傾向而非結果 —— 〈類總章〉682「有用神則必有忌神，"
        "**忌則喜靜、喜衰、喜制**；有用神必有元神，**元則喜動、喜旺、喜生**」。此為應然之表述，不得"
        "對應為「旺則能生」之實然判斷。\n\n"
        "**《增刪卜易》Y-R10 不依此軸**：該書以「能克害五／不能克七」成對列舉，條件為忌神之旺衰、空破、"
        "墓、化、**同動**，未以動靜切分。941「忌神與仇神同動」、950「忌神與元神同動」之「同動」為兩爻"
        "關係，非單爻動作。\n\n"
        "**《卜筮全書》用「元辰」而非「元神」**，二者概念對應係編者判定，非原文明言。\n\n"
        "**《火珠林》明文排除第三位**：行 126「兄弟是破財之人，不為主、不為輔，何必看也」。該書為主／"
        "輔二位結構，故忌神四格標「明文排除」。所排除者是「兄弟」不是「忌神」，二者等同本項目不作。"
    ),
}


def _canonical_book_id(book_id: str) -> str:
    return book_id.replace("_", "").lower()


def ingested_book_ids() -> set[str]:
    """Read identifiers from actual rules envelopes, not a manual book list."""
    result = set()
    for path in DOCTRINAL_DIR.glob("*_rules.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        result.add(_canonical_book_id(payload["book_id"]))
    return result


def collection_status(book_id: str, ingested: set[str]) -> str:
    return "ingested_not_surveyed" if _canonical_book_id(book_id) in ingested else "not_ingested"


def update() -> list[Path]:
    ingested = ingested_book_ids()
    changed = []
    for path in sorted(TABLE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        original = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        table_id = payload.get("table_id")
        if table_id in TABLE_NOTES:
            payload["table_note"] = TABLE_NOTES[table_id]
        for row in payload.get("rows", []):
            for cell in row.get("cells", []):
                if cell.get("status") == "not_collected":
                    cell["collection_status"] = collection_status(cell["book_id"], ingested)
        if json.dumps(payload, ensure_ascii=False, sort_keys=True) != original:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed.append(path)
    return changed


if __name__ == "__main__":
    for path in update():
        print(path.relative_to(ROOT))
