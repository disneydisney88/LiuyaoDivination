from engine.build import build
from engine.relations import build_relation_graph, classify_motion, seasonal_state, xunkong
from engine.semantics import semantics_from_relations


def sample_rows():
    return [
        {"position": 1, "branch": "子", "element": "水"},
        {"position": 2, "branch": "寅", "element": "木"},
        {"position": 3, "branch": "辰", "element": "土"},
        {"position": 4, "branch": "午", "element": "火"},
        {"position": 5, "branch": "申", "element": "金"},
        {"position": 6, "branch": "戌", "element": "土"},
    ]


def test_day_month_edges_are_one_way():
    """Sourced R-L2-04 assertion: no yao -> day/month edge exists."""
    graph = build_relation_graph(line_rows=sample_rows(), month_element="土", month_branch="辰",
                                 day_stem="甲", day_branch="子")
    assert all(edge["target"] not in {"日辰", "月建"} for edge in graph["edges"])


def test_changing_edges_are_scoped_to_own_moving_line():
    """Sourced R-L2-05 assertion: changed-line outgoing scope is local."""
    graph = build_relation_graph(line_rows=sample_rows(), month_element="土", month_branch="辰",
                                 day_stem="甲", day_branch="子", moving_positions={2},
                                 changing_positions={2})
    changed_out = [e for e in graph["edges"] if e["source"] == "變爻:2"]
    assert [e["target"] for e in changed_out] == ["動爻:2"]
    assert all(not (e["source"].startswith("變爻:") and e["target"] != "動爻:2")
               for e in graph["edges"])


def test_seasonal_state_is_mechanical_only():
    """Self-consistency: the five R-L2-01 labels are calculable."""
    assert seasonal_state("土", "土") == "旺"
    assert seasonal_state("金", "土") == "相"
    assert seasonal_state("火", "土") == "休"
    assert seasonal_state("木", "土") == "囚"
    assert seasonal_state("水", "土") == "死"


def test_month_break_is_mechanical_marker():
    """R-L2-03: month branch clash marks 月破 without assigning an effect."""
    graph = build_relation_graph(line_rows=sample_rows(), month_element="土", month_branch="子",
                                 day_stem="甲", day_branch="子")
    by_position = {row["position"]: row for row in graph["lines"]}
    assert by_position[1]["branch"] == "子"
    assert by_position[1]["month_break"] is False
    assert by_position[4]["branch"] == "午"
    assert by_position[4]["month_break"] is True


def test_xunkong_is_mechanically_derived():
    """Self-consistency: 甲子旬 gives 戌亥空 without an effect judgment."""
    assert xunkong("甲", "子") == ("戌", "亥")


def test_empty_then_clash_is_full_motion_not_scatter():
    """Sourced R-L2-09 ordering: empty is checked before 日辰冲."""
    assert classify_motion(moving=True, empty=True, day_branch="午", line_branch="子") == "全動"
    assert classify_motion(moving=True, empty=False, day_branch="午", line_branch="子") == "散"


def test_multiple_hidden_entries_pass_through_relations_and_semantics():
    derived = build([0, 0, 1, 1, 1, 1])
    graph = build_relation_graph(
        line_rows=derived["lines_detail"], hidden=derived["hidden"],
        month_element="土", month_branch="辰", day_stem="甲", day_branch="子",
    )
    assert graph["hidden"] == derived["hidden"]
    semantics = semantics_from_relations(graph, line=1, condition="旺相之爻遇沖")
    assert semantics["hidden"] == derived["hidden"]
