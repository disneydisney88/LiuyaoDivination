"""Generate TASK 18 axis-aware decision-table data without the pending A corpus."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.semantics import calculate_coverage


TABLES = ROOT / "data" / "decision_tables"
C1_PATH = TABLES / "C1_chong_san.json"
C15_PATH = TABLES / "C15_dongjing_axis.json"


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def different_axis_cell() -> dict:
    return {
        "book_id": "huangjin_ce",
        "status": "different_axis",
        "verdict": None,
        "axis_note": "本書明文以動靜軸判沖（行 40「別衰旺以明剋合，辨動靜以定刑沖」），本表五格全繫於衰旺軸。其立場見 C15 決策表",
        "axis_original": "別衰旺以明剋合，辨動靜以定刑沖",
        "axis_source": "千金賦 40",
        "cross_reference": "C15",
    }


def update_c1() -> dict:
    data = json.loads(C1_PATH.read_text(encoding="utf-8"))
    for row in data["rows"]:
        for index, cell in enumerate(row["cells"]):
            if cell["book_id"] == "huangjin_ce":
                row["cells"][index] = different_axis_cell()
                break
        else:
            row["cells"].append(different_axis_cell())
        row.update(calculate_coverage(row, books_total=len(data["books"])))
    write_json(C1_PATH, data)
    return data


def c15_cell(book_id: str, *, verdict: str, original: str, source: str, rule_id: str) -> dict:
    return {
        "book_id": book_id,
        "status": "addressed",
        "verdict": verdict,
        "original": original,
        "source": source,
        "rule_id": rule_id,
    }


def write_c15(c1: dict) -> None:
    tripartite = {
        "空爻遇沖": ("有用", "空逢沖而有用", "千金賦 30", "R-HJ-C15-R1"),
        "靜爻遇沖": ("暗興", "靜得沖而暗興", "千金賦 34", "R-HJ-C15-R2"),
        "動爻遇沖": ("事散", "動逢沖而事散", "千金賦 76", "R-HJ-C15-R3"),
    }
    rows = []
    for index, condition in enumerate(tripartite, start=1):
        cells = []
        for book in c1["books"]:
            book_id = book["book_id"]
            if book_id == "huangjin_ce":
                verdict, original, source, rule_id = tripartite[condition]
                cells.append(c15_cell(book_id, verdict=verdict, original=original,
                                      source=source, rule_id=rule_id))
            else:
                cells.append({"book_id": book_id, "status": "not_collected"})
        row = {
            "row_id": f"C15-R{index}",
            "condition": condition,
            "cells": cells,
        }
        row.update(calculate_coverage(row, books_total=len(c1["books"])))
        rows.append(row)
    write_json(C15_PATH, {
        "table_id": "C15",
        "title": "沖之判定（動靜軸）",
        "conflict_ids": ["C15", "C11", "C12", "C14"],
        "books": c1["books"],
        "rows": rows,
    })


def main() -> None:
    c1 = update_c1()
    write_c15(c1)


if __name__ == "__main__":
    main()
