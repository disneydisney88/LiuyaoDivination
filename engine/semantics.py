"""Data-backed, non-convergent N-track semantic outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"
VALID_STATUSES = frozenset({"addressed", "not_addressed", "category_negated", "not_collected"})
NO_SEMANTIC_EFFECTS = "structured_only_no_effects_implemented"
MATERIAL_DEPTH_LABELS = {
    "thick": "此格有三家以上原文可看",
    "thin": "此格材料較少",
    "none": "此格已採各本皆無表述",
}
COLLECTION_GAP_TEMPLATE = "另有 {} 本在庫未採集。此為採集缺口，非該書無立場。"
COVERAGE_NOTE = """**關於本表之切法**

R1–R5 五個條件係本項目從《易冒》十八法與野鶴之論述反推所得之切法，**非各書自身之設問方式**。

其他書並無義務按此五格立說。《卜筮全書》按事類編排、全書無專章體例，其「未表述」部分反映的是本表提問方式偏向《易冒》，而非該書材料貧乏。

**覆蓋率為材料厚度指標，不是可信度指標，更不是票數。** 三家有表述不等於該說較可信；一家否定範疇不等於該家是少數派 —— 否定範疇是拒絕進入此提問框架，不是投了反對票。"""


def load_decision_table(path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def calculate_coverage(row: dict[str, Any], books_total: int | None = None) -> dict[str, Any]:
    """Calculate material coverage only; never infer agreement or credibility."""
    counts = {status: 0 for status in VALID_STATUSES}
    for cell in row.get("cells", []):
        status = cell.get("status")
        if status not in VALID_STATUSES:
            raise ValueError("invalid decision-table status")
        counts[status] += 1
    total = len(row.get("cells", [])) if books_total is None else books_total
    if total != sum(counts.values()):
        raise ValueError("books_total must equal the number of row cells")
    books_collected = total - counts["not_collected"]
    parts = []
    if counts["addressed"]:
        parts.append(f"{counts['addressed']} 本有表述")
    if counts["category_negated"]:
        parts.append(f"{counts['category_negated']} 本否定範疇")
    if counts["not_addressed"]:
        parts.append(f"{counts['not_addressed']} 本未表述")
    label = f"已採 {books_collected} 本"
    if parts:
        label += "：" + "、".join(parts)
    if counts["not_collected"]:
        label += f"；另 {counts['not_collected']} 本未採"
    addressed = counts["addressed"]
    depth = "thick" if addressed >= 3 else "thin" if addressed in {1, 2} else "none"
    return {
        "coverage": {
            "books_total": total,
            "books_collected": books_collected,
            "books_addressed": addressed,
            "books_not_addressed": counts["not_addressed"],
            "books_category_negated": counts["category_negated"],
            "books_not_collected": counts["not_collected"],
        },
        "coverage_label": label,
        "material_depth": depth,
    }


def _validate_cell(cell: dict[str, Any]) -> None:
    status = cell.get("status")
    if status not in VALID_STATUSES:
        raise ValueError("invalid decision-table status")
    if status == "not_collected" and "verdict" in cell:
        raise ValueError("not_collected cells must not contain verdict")
    if status == "addressed" and cell.get("verdict") is None:
        raise ValueError("addressed cells must have a non-null verdict")
    if status in {"not_addressed", "category_negated"} and cell.get("verdict") is not None:
        raise ValueError("non-addressed cells must have a null verdict")
    if status == "category_negated" and not cell.get("negation_original"):
        raise ValueError("category_negated cells require negation_original")
    if status == "category_negated" and not cell.get("negation_source"):
        raise ValueError("category_negated cells require negation_source")


def _row_for_condition(table: dict[str, Any], condition: str) -> dict[str, Any]:
    try:
        return next(row for row in table["rows"] if row["condition"] == condition)
    except StopIteration as exc:
        raise ValueError("unsupported decision-table condition") from exc


def _track(cell: dict[str, Any], book_name: str) -> dict[str, Any]:
    _validate_cell(cell)
    status = cell["status"]
    result: dict[str, Any] = {
        "book_id": cell["book_id"], "book": book_name, "status": status,
        "framework_position": cell.get("framework_position"),
    }
    if status != "not_collected":
        result["verdict"] = cell.get("verdict")
    for key in ("source", "original", "rule_id", "evidence_strength", "evidence_note",
                "verdict_note", "line", "related_material", "search_note",
                "negation_original", "negation_source", "negation_category"):
        if key in cell:
            result[key] = cell[key]
    if status == "category_negated":
        result["category_negated"] = True
    if status == "not_addressed":
        result["not_addressed"] = True
    if status == "not_collected":
        result["not_collected"] = True
    return result


def semantic_for_condition(*, line: int, condition: str,
                           table: dict[str, Any] | None = None,
                           table_path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    """Return every table cell as a separate track; never infer missing books."""
    decision_table = table if table is not None else load_decision_table(table_path)
    row = _row_for_condition(decision_table, condition)
    names = {item["book_id"]: item["name"] for item in decision_table.get("books", [])}
    tracks: dict[str, dict[str, Any]] = {}
    for cell in row["cells"]:
        book_id = cell["book_id"]
        tracks[names.get(book_id, book_id)] = _track(cell, names.get(book_id, book_id))
    result: dict[str, Any] = {"line": line, "condition": condition, "tracks": tracks}
    result["row_id"] = row["row_id"]
    result.update(calculate_coverage(row, books_total=len(decision_table.get("books", []))))
    if row.get("row_title"):
        result["row_title"] = row["row_title"]
    if row.get("consensus"):
        result["consensus"] = True
    return result


def build_semantics(*, line: int, condition: str,
                    table: dict[str, Any] | None = None,
                    table_path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    return semantic_for_condition(line=line, condition=condition, table=table, table_path=table_path)


def semantics_from_relations(relation_result: dict[str, Any], *, line: int, condition: str,
                             table: dict[str, Any] | None = None,
                             table_path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    if "lines" not in relation_result or "edges" not in relation_result:
        raise ValueError("relation_result must be an engine.relations output")
    result = semantic_for_condition(line=line, condition=condition, table=table, table_path=table_path)
    result["relation_scope"] = relation_result.get("rule_scope", [])
    return result
