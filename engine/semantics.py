"""Data-backed, non-convergent N-track semantic outputs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_PATH = ROOT / "data" / "decision_tables" / "C1_chong_san.json"
VALID_STATUSES = frozenset({
    "addressed", "not_addressed", "not_collected", "category_negated",
    "concept_absent", "explicit_exclusion", "different_axis",
})
NO_SEMANTIC_EFFECTS = "structured_only_no_effects_implemented"
COLLECTION_GAP_TEMPLATE = "另有 {} 本在庫未採集。此為採集缺口，非該書無立場。"
TEXT_OVERLAP_WARNING = "註：《黃金策》與《卜筮全書》文本重疊 89.4%（被收錄者與收錄者），二者之一致不構成兩個獨立證據。"
COVERAGE_NOTE = """**關於本表之切法**

R1–R5 五個條件係本項目從《易冒》十八法與野鶴之論述反推所得之切法，**非各書自身之設問方式**。

其他書並無義務按此五格立說。《卜筮全書》按事類編排、全書無專章體例，其「未表述」部分反映的是本表提問方式偏向《易冒》，而非該書材料貧乏。

**覆蓋率只記錄已採集材料之範圍，不是可信度指標，更不是票數。** 三家有表述不等於該說較可信；一家否定範疇不等於該家是少數派 —— 否定範疇是拒絕進入此提問框架，不是投了反對票。"""


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
    if counts["concept_absent"]:
        parts.append(f"{counts['concept_absent']} 本無此概念")
    if counts["explicit_exclusion"]:
        parts.append(f"{counts['explicit_exclusion']} 本明文排除角色")
    if counts["not_addressed"]:
        parts.append(f"{counts['not_addressed']} 本未表述")
    if counts["different_axis"]:
        parts.append(f"{counts['different_axis']} 本用另一軸")
    label = f"已採 {books_collected} 本"
    if parts:
        label += "：" + "、".join(parts)
    if counts["not_collected"]:
        label += f"；另 {counts['not_collected']} 本未採"
    statuses = {cell.get("book_id"): cell.get("status") for cell in row.get("cells", [])}
    overlap_pair = (statuses.get("huangjin_ce"), statuses.get("buzhequanshu"))
    if (
        "addressed" in overlap_pair
        and all(status in {"addressed", "different_axis"} for status in overlap_pair)
    ):
        label += "\n\n" + TEXT_OVERLAP_WARNING
    return {
        "coverage": {
            "books_total": total,
            "books_collected": books_collected,
            "books_addressed": counts["addressed"],
            "books_not_addressed": counts["not_addressed"],
            "books_category_negated": counts["category_negated"],
            "books_concept_absent": counts["concept_absent"],
            "books_explicit_exclusion": counts["explicit_exclusion"],
            "books_different_axis": counts["different_axis"],
            "books_not_collected": counts["not_collected"],
        },
        "coverage_label": label,
    }


def _validate_cell(cell: dict[str, Any]) -> None:
    status = cell.get("status")
    if status not in VALID_STATUSES:
        raise ValueError("invalid decision-table status")
    if status == "not_collected" and "verdict" in cell:
        raise ValueError("not_collected cells must not contain verdict")
    if status == "addressed":
        if cell.get("verdict") is None:
            raise ValueError("addressed cells must have a non-null verdict")
        if not cell.get("original") or not cell.get("source"):
            raise ValueError("addressed cells require original and source")
    if status in {"not_addressed", "category_negated", "concept_absent", "explicit_exclusion"} and cell.get("verdict") is not None:
        raise ValueError("non-addressed cells must have a null verdict")
    if status == "not_addressed" and not cell.get("search_note"):
        raise ValueError("not_addressed cells require search_note")
    if status == "different_axis":
        if "verdict" not in cell or cell["verdict"] is not None:
            raise ValueError("different_axis cells must have a null verdict")
        for key in ("axis_note", "axis_original", "axis_source"):
            if not cell.get(key):
                raise ValueError("different_axis cells require axis fields")
        if "cross_reference" not in cell:
            raise ValueError("different_axis cells require cross_reference (which may be null)")
    if status == "category_negated" and not cell.get("negation_original"):
        raise ValueError("category_negated cells require negation_original")
    if status == "category_negated" and not cell.get("negation_source"):
        raise ValueError("category_negated cells require negation_source")
    if status == "concept_absent" and not cell.get("absence_note"):
        raise ValueError("concept_absent cells require absence_note")
    if status == "explicit_exclusion":
        if not cell.get("exclusion_original") or not cell.get("exclusion_source"):
            raise ValueError("explicit_exclusion cells require exclusion evidence")


def _row_for_condition(table: dict[str, Any], condition: str) -> dict[str, Any]:
    try:
        return next(row for row in table["rows"] if row["condition"] == condition)
    except StopIteration as exc:
        raise ValueError("unsupported decision-table condition") from exc


def infer_condition(*, table_id: str, relation_result: dict[str, Any], line: int) -> str | None:
    """Infer only mechanically decidable decision-table rows.

    C1's ``有氣`` and post-``散`` rows remain manual because the current engine
    has no verified mechanical definition for the former and no effect
    semantics for the latter.
    """
    row = next((item for item in relation_result.get("lines", [])
                if item.get("position") == line), None)
    if row is None:
        return None
    day_clash = "沖" in row.get("day_relations", [])
    any_clash = day_clash or bool(row.get("month_break"))
    if table_id != "K" and not any_clash:
        return None
    if table_id == "C1":
        if row.get("branch") in {
            relation_result.get("month_branch"), relation_result.get("day_branch"),
        }:
            return "臨日月之爻遇沖"
        if row.get("seasonal_state") in {"旺", "相"}:
            return "旺相之爻遇沖"
        if day_clash and row.get("seasonal_state") in {"休", "囚"}:
            return "休囚之爻遇日沖"
        return None
    if table_id == "C15":
        if row.get("empty"):
            return "空爻遇沖"
        if row.get("motion") in {"動", "散", "全動"}:
            return "動爻遇沖"
        return "靜爻遇沖"
    if table_id == "K":
        # This chooses only a mechanically observable K row.  It preserves
        # the table's source material; it does not assign any empty-line
        # effect.  The remaining K rows need inputs not yet modelled (hidden
        # use, passage of a xun, or changsheng absolute state).
        if not row.get("empty"):
            return None
        if day_clash:
            return "空爻遇日辰沖"
        if row.get("month_break"):
            return "空而逢月破"
        if row.get("motion") in {"動", "散", "全動"}:
            return "動爻值旬空"
        if row.get("seasonal_state") in {"旺", "相"}:
            return "旺相之爻值旬空"
        if row.get("seasonal_state") in {"休", "囚"}:
            return "休囚之爻值旬空"
        if "生" in row.get("day_relations", []):
            return "空爻得日月動爻生扶"
        if row.get("motion") == "靜":
            return "靜爻值旬空"
    return None


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
                "negation_original", "negation_source", "negation_category",
                "absence_note", "exclusion_original", "exclusion_source", "cell_note",
                "term_note"):
        if key in cell:
            result[key] = cell[key]
    for key in ("axis_note", "axis_original", "axis_source", "cross_reference"):
        if key in cell:
            result[key] = cell[key]
    if status == "category_negated":
        result["category_negated"] = True
    if status == "not_addressed":
        result["not_addressed"] = True
    if status == "not_collected":
        result["not_collected"] = True
    if status == "different_axis":
        result["different_axis"] = True
    if status == "concept_absent":
        result["concept_absent"] = True
    if status == "explicit_exclusion":
        result["explicit_exclusion"] = True
    return result


def semantic_for_condition(*, line: int, condition: str,
                           hidden: Iterable[dict] = (),
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
    result: dict[str, Any] = {
        "table_id": decision_table.get("table_id"),
        "line": line,
        "condition": condition,
        "hidden": [dict(item) for item in hidden],
        "tracks": tracks,
    }
    result["row_id"] = row["row_id"]
    result.update(calculate_coverage(row, books_total=len(decision_table.get("books", []))))
    if row.get("row_title"):
        result["row_title"] = row["row_title"]
    if row.get("consensus"):
        result["consensus"] = True
    return result


def build_semantics(*, line: int, condition: str, hidden: Iterable[dict] = (),
                    table: dict[str, Any] | None = None,
                    table_path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    return semantic_for_condition(line=line, condition=condition, hidden=hidden,
                                  table=table, table_path=table_path)


def semantics_from_relations(relation_result: dict[str, Any], *, line: int, condition: str,
                             table: dict[str, Any] | None = None,
                             table_path: str | Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    if "lines" not in relation_result or "edges" not in relation_result:
        raise ValueError("relation_result must be an engine.relations output")
    result = semantic_for_condition(line=line, condition=condition,
                                    hidden=relation_result.get("hidden", []),
                                    table=table, table_path=table_path)
    result["relation_scope"] = relation_result.get("rule_scope", [])
    return result
