"""Source-preserving L2 semantic outputs.

This module does not calculate a single fortune, severity, recommendation, or
use-god choice.  It only materialises the five C1 decision-table cells as
separate source tracks.
"""
from __future__ import annotations

from typing import Any


TRACKS = ("易冒", "卜筮正宗", "增刪卜易")
NO_SEMANTIC_EFFECTS = "structured_only_no_effects_implemented"


def _not_addressed() -> dict[str, Any]:
    return {"verdict": None, "not_addressed": True}


def _track(verdict: str | None, framework: str, source: str, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "verdict": verdict,
        "framework": framework,
        "source": source,
    }
    result.update(extra)
    return result


def semantic_for_condition(*, line: int, condition: str) -> dict[str, Any]:
    """Return the non-convergent output for one C1 decision-table cell."""
    base: dict[str, Any] = {"line": line, "condition": condition, "tracks": {}}
    if condition == "旺相之爻遇沖":
        base["consensus"] = True
        base["tracks"] = {
            "易冒": _track("不散（為動）", "看用神十八法", "類總章 690", framework_position=None),
            "卜筮正宗": _track("不散", "真假二分", "辟增刪卜易之謬 436", framework_position=None),
            "增刪卜易": _track("不散", "二值判定 + 條件枚舉", "動散章 1673", framework_position=None),
        }
        return base
    if condition == "有氣之爻遇沖":
        base["tracks"] = {
            "易冒": _not_addressed(),
            "卜筮正宗": _not_addressed(),
            "增刪卜易": _track("不散", "二值判定 + 條件枚舉", "動散章 1673", framework_position=None),
        }
        return base
    if condition == "臨日月之爻遇沖":
        base["tracks"] = {
            "易冒": _track("不散", "看用神十八法", "類總章 690；日沖章 416", framework_position=None),
            "卜筮正宗": _not_addressed(),
            "增刪卜易": _not_addressed(),
        }
        return base
    if condition == "休囚之爻遇日沖":
        base["tracks"] = {
            "易冒": _track(
                "散", "看用神十八法", "日沖章 416；類總章 690",
                framework_position=18,
                framework_note="凶陷；雖救之無從，是謂大凶",
                rule_id="R-YM-01-18",
            ),
            "卜筮正宗": _track(
                "散（名日破）", "真假二分", "辟增刪卜易之謬 436",
                framework_position=None,
                framework_note="該書體系無「散」之級別；此表述出自論戰文字",
                evidence_strength="weak",
            ),
            "增刪卜易": {
                "verdict": None,
                "category_negated": True,
                "framework": "二值判定 + 條件枚舉",
                "framework_position": None,
                "note": "此體系不處理此問題 —— 「余從來不言散」",
                "source": "元神忌神衰旺章第十 922；動散章 1683",
            },
        }
        return base
    if condition == "既判為散之後":
        base["tracks"] = {
            "易冒": _track("不可救", "看用神十八法", "日沖章；類總章第 18 法", framework_position=18),
            "卜筮正宗": _not_addressed(),
            "增刪卜易": _not_addressed(),
        }
        return base
    raise ValueError(f"unsupported C1 condition: {condition}")


def build_semantics(*, line: int, condition: str) -> dict[str, Any]:
    """Public explicit-condition API used by callers that already classified L2."""
    return semantic_for_condition(line=line, condition=condition)


def semantics_from_relations(relation_result: dict[str, Any], *, line: int, condition: str) -> dict[str, Any]:
    """Attach one explicit C1 result to a relations output without rewriting it."""
    if "lines" not in relation_result or "edges" not in relation_result:
        raise ValueError("relation_result must be an engine.relations output")
    result = semantic_for_condition(line=line, condition=condition)
    result["relation_scope"] = relation_result.get("rule_scope", [])
    return result
