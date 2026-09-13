"""Generate the TASK_CODEX_18 A-part Huangjin Ce doctrinal envelope."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "doctrinal" / "huangjince_rules.json"
EXPECTED_LINES = 1781
REQUIRED_LINES = (30, 34, 40, 56, 76, 111, 1219, 1425)


def read_source(path: Path) -> list[str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if len(lines) != EXPECTED_LINES:
        raise ValueError(f"expected {EXPECTED_LINES} lines, got {len(lines)}")
    if text.count("□") != 1:
        raise ValueError(f"expected one □ marker, got {text.count('□')}")
    expected_terms = {"空亡": 37, "旬空": 2, "真空": 0, "假空": 0, "六甲空亡": 0}
    actual_terms = {term: text.count(term) for term in expected_terms}
    if actual_terms != expected_terms:
        raise ValueError(f"unexpected search-term counts: {actual_terms}")
    return lines


def original(lines: list[str], line: int) -> str:
    if line not in REQUIRED_LINES:
        raise ValueError(f"line {line} is not an A2 required line")
    return lines[line - 1]


def make_item(
    *,
    set_id: str,
    set_name: str,
    ordinal: int,
    line: int,
    chapter: str,
    rule_id: str,
    lines: list[str],
    context: tuple[int, int] | None = None,
) -> dict:
    item = {
        "item_ordinal": ordinal,
        "line": line,
        "chapter": chapter,
        "definition_original": original(lines, line),
        "rule_id": rule_id,
        "enumeration_source": "editorial",
    }
    if context is not None:
        start, end = context
        item["context_line_start"] = start
        item["context_line_end"] = end
        item["context_original"] = "\n".join(lines[start - 1:end])
    return item


def make_set(
    *,
    set_id: str,
    set_name: str,
    chapter: str,
    lines: list[str],
    item_specs: list[tuple[int, str, str]],
    full_lines: list[int],
    tripartite: bool = False,
) -> dict:
    items = [
        make_item(
            set_id=set_id,
            set_name=set_name,
            ordinal=index,
            line=line,
            chapter=chapter,
            rule_id=rule_id,
            lines=lines,
            context=context,
        )
        for index, (line, rule_id, context) in enumerate(item_specs, start=1)
    ]
    result = {
        "set_id": set_id,
        "set_name": set_name,
        "chapter": chapter,
        "line": item_specs[0][0],
        "count_declared": None,
        "count_actual": len(items),
        "count_mismatch": None,
        "enumeration_source": "editorial",
        "definition_original_full": "\n".join(lines[line - 1] for line in full_lines),
        "items": items,
    }
    if tripartite:
        result["is_tripartite_group"] = True
    return result


def build(lines: list[str]) -> dict:
    tripartite = make_set(
        set_id="HJ_SET_01",
        set_name="沖之三分法（空／靜／動）",
        chapter="1、總斷千金賦",
        lines=lines,
        item_specs=[
            (30, "R-HJ-01-01", None),
            (34, "R-HJ-01-02", None),
            (76, "R-HJ-01-03", None),
        ],
        full_lines=[30, 34, 76],
        tripartite=True,
    )
    general = make_set(
        set_id="HJ_SET_02",
        set_name="總斷千金賦之衰旺／動靜／神煞句",
        chapter="1、總斷千金賦",
        lines=lines,
        item_specs=[
            (40, "R-HJ-02-01", None),
            (56, "R-HJ-02-02", None),
            (111, "R-HJ-02-03", (99, 116)),
        ],
        full_lines=[40, 56] + list(range(99, 117)),
    )
    applications = make_set(
        set_id="HJ_SET_03",
        set_name="事類篇空亡／沖用例",
        chapter="21、墳墓／25、避亂",
        lines=lines,
        item_specs=[
            (1219, "R-HJ-03-01", None),
            (1425, "R-HJ-03-02", None),
        ],
        full_lines=[1219, 1425],
    )
    douzhen_original = "\n".join(lines[1534:1585])
    douzhen = {
        "set_id": "HJ_SET_DOUZHEN",
        "set_name": "新增痘疹",
        "line_range": "1535–1585",
        "provenance_note": "夾於 27失脫 與 28出行 之間，不入篇次。《卜筮全書》無痘疹章，即此章來自第三個來源，來源不明",
        "in_chapter_index": False,
        "source_unknown": True,
        "count_declared": None,
        "count_actual": 1,
        "count_mismatch": None,
        "enumeration_source": "editorial",
        "definition_original_full": douzhen_original,
        "items": [{
            "item_ordinal": 1,
            "line": 1535,
            "chapter": "新增痘疹",
            "definition_original": douzhen_original,
            "rule_id": "R-HJ-DOUZHEN-01",
            "enumeration_source": "editorial",
        }],
    }
    return {
        "book_id": "huangjince",
        "source_book": "黃金策",
        "era": "明",
        "author": "題劉基",
        "attribution_status": "attributed",
        "framework_type": "rhapsody_couplet",
        "enumeration_style": "none",
        "framework_note": "賦體，以對句立說，不立章目、不列條數。沖之判定繫於動靜軸（行 40「辨動靜以定刑沖」），與清代三家之衰旺軸不同",
        "doctrinal_status": "single_school",
        "conflicts_with": ["C1", "C11", "C12", "C14", "C15", "C16"],
        "corpus_path": "03_黃金策/黃金策_千金賦_古本.txt",
        "corpus_note": "以古本為準。原檔含現代註釋 14 行（79–91、989），已分離。行 91「用世空動逢沖」等涉沖條件句屬今注，不得作賦文用",
        "provenance_strength": "compromised",
        "provenance_note": "檔案第 6 行自述按《卜筮正宗》本全文載錄，經 TASK_21／TASK_22 核對不成立。繁簡正規化後 LCS 比對顯示，本檔 89.4% 字元見於《卜筮全書》古本行 5360–9703，2.6% 見於《卜筮正宗》，故本項目所用文本主要來自《卜筮全書》所載版本。所據紙本底本仍不明，本地無影像可核；因檔內自述已被推翻，provenance 標為 compromised。",
        "corpus_cleaned": True,
        "text_overlap": [{
            "with_book_id": "buzhequanshu",
            "overlap_ratio": 0.894,
            "method": "繁簡正規化後 LCS 字元比對",
            "overlap_range": "卜筮全書古本行 5360–9703",
            "relation": "被收錄者與收錄者",
            "source": "TASK_22 審計",
            "warning": "二軌之一致不構成兩個獨立證據",
        }],
        "main_search_term": "空亡",
        "search_term_note": "「空亡」37 次、「旬空」2 次。與《卜筮全書》同型。另：本檔用繁體「沖」112 次、簡體「冲」0 次，與《卜筮全書》相反",
        "semantic_status": "structured_only_no_effects_implemented",
        "sets": [tripartite, general, applications, douzhen],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = build(read_source(args.source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
