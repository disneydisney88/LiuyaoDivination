"""Data-backed guards for user-visible mechanical text.

The guard deliberately does not inspect multi-track source quotations: those
must preserve each book's original terminology, including disputed terms.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TERMS_PATH = ROOT / "data" / "forbidden_terms.json"


@lru_cache(maxsize=1)
def load_forbidden_terms() -> tuple[dict[str, Any], ...]:
    """Load audited terms; each entry carries its reason and layer scope."""
    payload = json.loads(FORBIDDEN_TERMS_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("forbidden_terms.json requires non-empty entries")
    required = {"term", "added_by", "reason", "layer_forbidden", "layer_allowed"}
    if any(not required <= set(entry) for entry in entries):
        raise ValueError("each forbidden term requires provenance and layer scope")
    if len({entry["term"] for entry in entries}) != len(entries):
        raise ValueError("forbidden terms must be unique")
    return tuple(dict(entry) for entry in entries)


def forbidden_entries_for(layer: str) -> tuple[dict[str, Any], ...]:
    """Return only terms forbidden in the requested output layer."""
    return tuple(entry for entry in load_forbidden_terms() if layer in entry["layer_forbidden"])


def find_forbidden_terms(text: str, *, layer: str) -> tuple[str, ...]:
    """Return every audited term found in one user-visible text segment."""
    return tuple(entry["term"] for entry in forbidden_entries_for(layer) if entry["term"] in text)


def assert_mechanical_text_clean(text: str, *, layer: str) -> None:
    """Fail with the exact forbidden terms, without interpreting doctrine."""
    found = find_forbidden_terms(text, layer=layer)
    if found:
        raise AssertionError("forbidden user-visible text in {}: {}".format(layer, "、".join(found)))
