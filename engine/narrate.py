"""Deterministic, source-preserving narrative templates.

This module only renders supplied mechanical relation state and semantic track
records.  It does not calculate effects, choose a use-god, or converge tracks.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_PATH = ROOT / "data" / "narrative_templates.json"
DOCTRINAL_PATH = ROOT / "data" / "doctrinal"
MISSING_TEXT = "（此情況未有對應模板）"


def narrate_hidden(hidden: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Render every mechanical R-L1-08a entry without assigning an effect."""
    narratives = []
    for item in hidden:
        relative = item.get("six_relative", item.get("六親", ""))
        entry = dict(item)
        entry["text"] = "{}{}{}，伏於第{}爻{}{}之下（飛神{}{}）。".format(
            relative, item.get("branch", ""), item.get("element", ""),
            item.get("position", ""), item.get("flying_branch", ""),
            item.get("flying_element", ""), item.get("flying_branch", ""),
            item.get("flying_element", ""),
        )
        narratives.append(entry)
    return narratives


def narrate_flying_hidden(relation: dict[str, Any]) -> dict[str, Any]:
    """Render the 易冒 flying/hidden wording with its original grammatical subject."""
    templates = _load_templates()
    text, template_id = _render(relation["template_id"], relation, templates)
    return {"text": text, "template_id": template_id, "template_missing": template_id is None}


def _load_templates() -> dict[str, dict[str, Any]]:
    return json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))


def _load_sources() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_rule: dict[str, dict[str, Any]] = {}
    negated: dict[str, dict[str, Any]] = {}
    for path in sorted(DOCTRINAL_PATH.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for source_set in data.get("sets", []):
            for item in source_set.get("items", []):
                rule_id = item.get("rule_id")
                if rule_id:
                    by_rule[rule_id] = item
                original = item.get("original")
                category = item.get("negated_category")
                if original and category:
                    negated[category] = item
    return by_rule, negated


def _render(template_id: str, slots: dict[str, Any], templates: dict[str, dict[str, Any]]) -> tuple[str, str | None]:
    template = templates.get(template_id)
    if template is None:
        return MISSING_TEXT, None
    try:
        text = template["pattern"].format(**slots)
    except (KeyError, ValueError):
        return MISSING_TEXT, None
    return text, template_id


def _missing_step(step: int) -> dict[str, Any]:
    return {"step": step, "text": MISSING_TEXT, "rule_id": None, "template_missing": True}


def _derivation(relation_result: dict[str, Any], line: int, templates: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    row = next((item for item in relation_result.get("lines", []) if item.get("position") == line), None)
    if row is None:
        return [_missing_step(1)], True
    steps: list[dict[str, Any]] = []
    template_missing = False
    month = relation_result.get("month_branch")
    seasonal = row.get("seasonal_state")
    if month is None or seasonal is None:
        steps.append(_missing_step(len(steps) + 1))
        template_missing = True
    else:
        text, template_id = _render("T-SEASONAL-01", {
            "branch": row.get("branch"), "element": row.get("element"),
            "month": month, "state": seasonal,
        }, templates)
        steps.append({"step": len(steps) + 1, "text": text,
                      "rule_id": templates[template_id]["rule_id"] if template_id else None,
                      "template_id": template_id, "template_missing": template_id is None})
        template_missing |= template_id is None
    relations = row.get("day_relations")
    day_branch = relation_result.get("day_branch")
    if relations and day_branch:
        for relation in relations:
            if relation in {"沖", "合"}:
                text, template_id = _render("T-DAY-RELATION-01", {
                    "day_branch": day_branch, "branch": row.get("branch"), "relation": relation,
                }, templates)
                steps.append({"step": len(steps) + 1, "text": text,
                              "rule_id": templates[template_id]["rule_id"] if template_id else None,
                              "template_id": template_id, "template_missing": template_id is None})
                template_missing |= template_id is None
    elif row.get("day_relations") is None:
        steps.append(_missing_step(len(steps) + 1))
        template_missing = True
    marker_specs = (("empty", "T-EMPTY-01"), ("month_break", "T-MONTH-BREAK-01"), ("motion", "T-MOTION-01"))
    for field, template_id in marker_specs:
        value = row.get(field)
        if value is None:
            steps.append(_missing_step(len(steps) + 1))
            template_missing = True
            continue
        if field in {"empty", "month_break"} and not value:
            continue
        slots = {"motion": value} if field == "motion" else {}
        text, rendered_id = _render(template_id, slots, templates)
        steps.append({"step": len(steps) + 1, "text": text,
                      "rule_id": templates[rendered_id]["rule_id"] if rendered_id else None,
                      "template_id": rendered_id, "template_missing": rendered_id is None})
        template_missing |= rendered_id is None
    if row.get("motion") == "動" and "沖" in (row.get("day_relations") or []):
        text, rendered_id = _render("T-DAY-CHONG-MULTI-TRACK-01", {}, templates)
        steps.append({"step": len(steps) + 1, "text": text,
                      "rule_id": templates[rendered_id]["rule_id"] if rendered_id else None,
                      "template_id": rendered_id, "template_missing": rendered_id is None})
        template_missing |= rendered_id is None
    return steps, template_missing


def _track_text(book: str, track: dict[str, Any], templates: dict[str, dict[str, Any]]) -> tuple[str, str, str | None]:
    if track.get("category_negated"):
        template_id = "T-NEGATED-01"
        template = templates[template_id]
        implication = template["implication"].format(
            author="《{}》".format(book), category=track.get("negation_category", "散"),
        )
        return template["verdict_plain"], implication, template_id
    if track.get("not_collected"):
        return _render("T-TRACK-NOT-COLLECTED-01", {}, templates)[0], "", "T-TRACK-NOT-COLLECTED-01"
    if track.get("not_addressed"):
        text, template_id = _render("T-TRACK-NOT-ADDRESSED-01", {}, templates)
        return text, "", template_id
    if track.get("concept_absent"):
        return "此書體系中未見此概念。", "", None
    if track.get("explicit_exclusion"):
        return "此書明文排除此角色。", "", None
    if track.get("different_axis"):
        text, template_id = _render("T-TRACK-DIFFERENT-AXIS-01", {}, templates)
        implication, _ = _render("T-TRACK-IMPLICATION-DIFFERENT-AXIS-01", {}, templates)
        return text, implication, template_id
    if track.get("match_quality") == "partial":
        verdict, verdict_id = _render("T-TRACK-VERDICT-01", {"verdict": track.get("verdict")}, templates)
        note = track.get("partial_note") or "原文只部分覆蓋本格條件。"
        return verdict, "部分對應 —— " + note, verdict_id
    if track.get("rule_id") == "R-YM-01-18":
        verdict, verdict_id = _render("T-TRACK-YM-18", {}, templates)
        implication, _ = _render("T-TRACK-IMPLICATION-YM", {}, templates)
        return verdict, implication, verdict_id
    verdict, verdict_id = _render("T-TRACK-VERDICT-01", {"verdict": track.get("verdict")}, templates)
    implication, _ = _render("T-TRACK-IMPLICATION-GENERIC", {}, templates)
    return verdict, implication, verdict_id


def _source_fields(book: str, track: dict[str, Any], by_rule: dict[str, dict[str, Any]], negated: dict[str, dict[str, Any]]) -> tuple[str | None, str | None]:
    item = by_rule.get(track.get("rule_id"))
    if item:
        original = item.get("definition_original") or item.get("original")
        if original:
            return original, original
    if track.get("category_negated"):
        original = track.get("negation_original")
        if original:
            return original, track.get("negation_source")
    if track.get("explicit_exclusion"):
        original = track.get("exclusion_original")
        if original:
            return original, track.get("exclusion_source")
    if track.get("concept_absent"):
        return track.get("absence_note"), None
    if track.get("different_axis"):
        return track.get("axis_original"), track.get("axis_source")
    original = track.get("original")
    if original:
        return original, original
    return None, None


def narrate(*, semantics: dict[str, Any], relations: dict[str, Any]) -> dict[str, Any]:
    """Render one semantic cell with only supplied relation state."""
    templates = _load_templates()
    by_rule, negated = _load_sources()
    hidden = semantics.get("hidden") or relations.get("hidden") or []
    if not isinstance(hidden, list):
        raise ValueError("hidden must be a list")
    hidden_rows = [dict(item) for item in hidden]
    line = semantics.get("line")
    relation_row = next((item for item in relations.get("lines", []) if item.get("position") == line), {})
    header = "{}爻 {}{} {}".format(line, relation_row.get("branch", ""), relation_row.get("element", ""), relation_row.get("six_relative", ""))
    derivation, missing = _derivation(relations, line, templates)
    tracks: list[dict[str, Any]] = []
    for book, track in semantics.get("tracks", {}).items():
        verdict, implication, verdict_template = _track_text(book, track, templates)
        original, citation = _source_fields(book, track, by_rule, negated)
        entry = {
            "book": book, "status": track.get("status"), "verdict_plain": verdict, "original": original,
            "citation": citation,
            "source_locator": (
                track.get("source") or track.get("axis_source")
                or track.get("negation_source") or track.get("exclusion_source")
            ),
            "implication": implication, "rule_id": track.get("rule_id"),
        }
        for key in ("verdict_note", "line", "related_material", "search_note",
                    "axis_note", "axis_original", "axis_source", "cross_reference", "term_note",
                    "match_quality", "partial_note", "candidate_type", "candidate_rule",
                    "soil_original", "soil_track_note", "direction_note"):
            if key in track:
                entry[key] = track[key]
        if verdict_template:
            entry["template_id"] = verdict_template
        if track.get("category_negated"):
            entry["category_negated"] = True
        if track.get("concept_absent"):
            entry["concept_absent"] = True
        if track.get("explicit_exclusion"):
            entry["explicit_exclusion"] = True
        if track.get("evidence_strength"):
            entry["evidence_strength"] = track["evidence_strength"]
        tracks.append(entry)
    template_ids = [step["template_id"] for step in derivation if step.get("template_id")]
    template_ids.extend(track["template_id"] for track in tracks if track.get("template_id"))
    return {"line": line, "header": header, "derivation": derivation,
            "hidden": hidden_rows, "hidden_narratives": narrate_hidden(hidden_rows),
            "tracks": tracks, "template_ids": template_ids,
            "template_missing": missing}
