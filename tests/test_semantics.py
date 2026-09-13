from engine.semantics import semantic_for_condition


def test_disputed_cell_has_all_eight_tracks():
    result = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    assert len(result["tracks"]) == 8
    assert {"易冒", "卜筮正宗", "增刪卜易"} <= set(result["tracks"])


def test_zengshan_disputed_track_is_category_negation_without_verdict():
    track = semantic_for_condition(line=3, condition="休囚之爻遇日沖")["tracks"]["增刪卜易"]
    assert track["verdict"] is None
    assert track["category_negated"] is True


def test_semantics_has_no_cross_track_convergence_fields():
    result = semantic_for_condition(line=3, condition="休囚之爻遇日沖")
    forbidden = {"consensus_verdict", "majority", "weighted"}
    assert forbidden.isdisjoint(result)
    assert forbidden.isdisjoint(result["tracks"])


def test_framework_position_only_yimao_is_ranked():
    tracks = semantic_for_condition(line=3, condition="休囚之爻遇日沖")["tracks"]
    assert tracks["易冒"]["framework_position"] == 18
    assert tracks["卜筮正宗"]["framework_position"] is None
    assert tracks["增刪卜易"]["framework_position"] is None


def test_uncollected_books_are_explicitly_distinct():
    tracks = semantic_for_condition(line=3, condition="休囚之爻遇日沖")["tracks"]
    assert sum(track["status"] == "not_collected" for track in tracks.values()) == 3
    assert all("verdict" not in track for track in tracks.values() if track["status"] == "not_collected")


def test_r1_label_is_non_consensus_and_collected_sources_are_present():
    result = semantic_for_condition(line=3, condition="旺相之爻遇沖")
    assert "consensus" not in result
    assert result["row_title"] == "三家判不散，一家判損"
    collected = [track for track in result["tracks"].values() if track["status"] == "addressed"]
    assert all(track["source"] for track in collected)


def test_not_addressed_and_category_negated_are_distinct():
    disputed = semantic_for_condition(line=3, condition="休囚之爻遇日沖")["tracks"]["增刪卜易"]
    not_addressed = semantic_for_condition(line=3, condition="有氣之爻遇沖")["tracks"]["易冒"]
    assert disputed.get("category_negated") is True
    assert disputed.get("not_addressed", False) is False
    assert not_addressed.get("not_addressed") is True
    assert not_addressed.get("category_negated", False) is False
