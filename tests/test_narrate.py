import ast
import json
from pathlib import Path

from engine.build import build
from engine.narrate import narrate
from engine.semantics import semantic_for_condition


ROOT = Path(__file__).resolve().parents[1]


def relation_state():
    return {
        "month_branch": "子",
        "day_branch": "午",
        "lines": [{
            "position": 3, "branch": "子", "element": "水",
            "seasonal_state": "旺", "day_relations": ["沖"],
            "empty": False, "month_break": False, "motion": "靜",
        }],
    }


def test_same_input_is_deterministic_for_ten_runs():
    semantics = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    outputs = [narrate(semantics=semantics, relations=relation_state()) for _ in range(10)]
    assert all(output == outputs[0] for output in outputs)


def test_templates_are_closed_and_narrate_has_no_f_strings():
    source = (ROOT / "engine" / "narrate.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))
    templates = json.loads((ROOT / "data" / "narrative_templates.json").read_text(encoding="utf-8"))
    assert templates
    assert all(item.get("template_id") == key for key, item in templates.items())


def test_category_negated_template_is_locked():
    semantics = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    track = next(item for item in narrate(semantics=semantics, relations=relation_state())["tracks"]
                 if item["book"] == "增刪卜易")
    assert track["verdict_plain"] == "此體系不處理此問題。"
    assert all(word not in track["verdict_plain"] for word in ("不散", "認為", "主張", "不適用", "無此問題"))
    assert "並非判" in track["implication"]
    assert all(word not in track["implication"] for word in ("認為", "主張", "持", "不適用", "無此問題"))


def test_category_negated_output_does_not_turn_into_a_verdict():
    semantics = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    track = next(item for item in narrate(semantics=semantics, relations=relation_state())["tracks"]
                 if item.get("category_negated"))
    assert track["verdict_plain"] == "此體系不處理此問題。"
    assert track["implication"].endswith("並非判「不散」。")


def test_original_and_citation_match_doctrinal_definition():
    semantics = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    output = narrate(semantics=semantics, relations=relation_state())
    source_files = list((ROOT / "data" / "doctrinal").glob("*.json"))
    definitions = set()
    for path in source_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        for source_set in data.get("sets", []):
            for item in source_set.get("items", []):
                if item.get("definition_original"):
                    definitions.add(item["definition_original"])
    yimao = next(item for item in output["tracks"] if item["book"] == "易冒")
    assert yimao["original"] in definitions
    assert yimao["citation"] == yimao["original"]


def test_decision_table_original_is_used_when_no_doctrinal_rule_matches():
    semantics = semantic_for_condition(line=3, condition="旺相之爻遇沖")
    output = narrate(semantics=semantics, relations=relation_state())
    quanshu = next(item for item in output["tracks"] if item["book"] == "卜筮全書")
    huangjince = next(item for item in output["tracks"] if item["book"] == "黃金策")
    assert quanshu["original"].startswith("大凡旺处逢冲则损")
    assert quanshu["source_locator"]
    assert huangjince["original"] == "別衰旺以明剋合，辨動靜以定刑沖"
    assert huangjince["source_locator"] == "千金賦 40"


def test_no_cross_track_convergence_fields():
    semantics = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    output = narrate(semantics=semantics, relations=relation_state())
    forbidden = {"summary", "comparison", "majority", "best_track", "consensus_verdict"}
    assert forbidden.isdisjoint(output)
    assert all(forbidden.isdisjoint(track) for track in output["tracks"])


def test_missing_template_is_explicit():
    semantics = {"line": 3, "tracks": {}}
    output = narrate(semantics=semantics, relations={"lines": [{"position": 3}]})
    assert output["template_missing"] is True
    assert any(step["text"] == "（此情況未有對應模板）" for step in output["derivation"])


def test_no_llm_imports_in_engine_or_pages():
    forbidden = ("openai", "zhipuai", "requests", "httpx")
    for folder in (ROOT / "engine", ROOT / "pages"):
        for path in folder.glob("*.py"):
            source = path.read_text(encoding="utf-8").lower()
            assert not any("import " + name in source or "from " + name in source for name in forbidden)


def test_multiple_hidden_entries_are_each_rendered_in_plain_language():
    hidden = build([0, 0, 1, 1, 1, 1])["hidden"]
    output = narrate(
        semantics={"line": 1, "hidden": hidden, "tracks": {}},
        relations={"lines": [{"position": 1}]},
    )
    assert output["hidden"] == hidden
    assert len(output["hidden_narratives"]) == 2
    assert [item["six_relative"] for item in output["hidden_narratives"]] == ["妻財", "子孫"]
    assert all("伏於" in item["text"] and "飛神" in item["text"] for item in output["hidden_narratives"])
