"""Data-backed, non-convergent N-track semantic outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"
VALID_STATUSES = frozenset({"addressed", "not_addressed", "category_negated", "not_collected"})
NO_SEMANTIC_EFFECTS = "structured_only_no_effects_implemented"


def load_decision_table(path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _validate_cell(cell: dict[str, Any]) -> None:
    status = cell.get("status")
    if status not in VALID_STATUSES:
        raise ValueError("invalid decision-table status")
    if status == "not_collected" and "verdict" in cell:
        raise ValueError("not_collected cells must not contain verdict")
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
