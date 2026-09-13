import streamlit as st

from engine.narrate import narrate
from engine.semantics import (
    COLLECTION_GAP_TEMPLATE,
    COVERAGE_NOTE,
    MATERIAL_DEPTH_LABELS,
    semantic_for_condition,
)


def show_track(track_narrative, track, *, original_collapsed=True):
    st.write(track_narrative["verdict_plain"])
    if track_narrative.get("implication"):
        st.caption(track_narrative["implication"])
    if track_narrative.get("verdict_note"):
        st.caption("判語註記：{}".format(track_narrative["verdict_note"]))
    if track_narrative.get("search_note"):
        st.caption("檢索註記：{}".format(track_narrative["search_note"]))
    st.caption("框架：{}".format(track.get("framework", "未提供")))
    if track.get("framework_position") is not None:
        st.caption("框架位置：{}".format(track["framework_position"]))
    if track.get("evidence_strength"):
        st.caption("證據強度：{}".format(track["evidence_strength"]))
    st.caption("出處：{}".format(track_narrative.get("source_locator") or track.get("source", "未表述")))
    original = track_narrative.get("original") or "現有 doctrinal 資料未提供逐字原文。"
    if original_collapsed:
        with st.expander("原文（預設摺疊）"):
            st.write(original)
    else:
        st.write(original)
    related_material = track_narrative.get("related_material")
    if related_material:
        with st.expander("相關材料（保留原文）"):
            for material in related_material:
                st.caption("{}（行號 {}）".format(material.get("source", "來源未標明"), material.get("line", "未標明")))
                st.write(material.get("original", ""))


st.header("多軌")
st.caption("按資料狀態分組；不作跨軌裁決、多數決、可信度或加權。")
condition = st.selectbox("選擇 C1 決策表格位", [
    "旺相之爻遇沖", "有氣之爻遇沖", "臨日月之爻遇沖", "休囚之爻遇日沖", "既判為散之後",
])
result = semantic_for_condition(line=3, condition=condition)
st.subheader("{}　{}".format(result["row_id"], condition))
st.caption(result["coverage_label"])
st.caption(MATERIAL_DEPTH_LABELS[result["material_depth"]])
if result["coverage"]["books_not_collected"] > 0:
    st.caption(COLLECTION_GAP_TEMPLATE.format(result["coverage"]["books_not_collected"]))
narrative = narrate(semantics=result, relations=st.session_state.get("current_relation_state", {}))
st.subheader(narrative["header"])
for step in narrative["derivation"]:
    label = "推導第 {}".format(step["step"])
    if step.get("template_missing"):
        st.warning("{}：{}".format(label, step["text"]))
    else:
        st.write("{}：{}（{}）".format(label, step["text"], step.get("rule_id")))

narrative_by_book = {item["book"]: item for item in narrative["tracks"]}
tracks = result["tracks"]
negated = [book for book, track in tracks.items() if track["status"] == "category_negated"]
addressed = [book for book, track in tracks.items() if track["status"] == "addressed"]
not_addressed = [book for book, track in tracks.items() if track["status"] == "not_addressed"]
not_collected = [book for book, track in tracks.items() if track["status"] == "not_collected"]

if result.get("row_title") and addressed:
    st.subheader(result["row_title"])
    for book in addressed:
        with st.expander(book, expanded=True):
            show_track(narrative_by_book[book], tracks[book], original_collapsed=False)
elif result.get("consensus") and addressed:
    with st.expander("{} 家一致：各家均有表態（保留各家原框架）".format(len(addressed)), expanded=False):
        for book in addressed:
            show_track(narrative_by_book[book], tracks[book])
elif addressed:
    st.subheader("分歧")
    for book in addressed:
        with st.expander(book, expanded=True):
            show_track(narrative_by_book[book], tracks[book], original_collapsed=False)

if negated:
    st.subheader("否定範疇")
    for book in negated:
        with st.container(border=True):
            st.markdown("**{}**".format(book))
            show_track(narrative_by_book[book], tracks[book])

if not_addressed:
    with st.expander("未表述：{}".format("、".join(not_addressed)), expanded=False):
        st.write("已讀取之材料未表述此問題；不等於未採集。")

if not_collected:
    with st.expander("未採集：{}".format("、".join(not_collected)), expanded=False):
        st.write("此為採集缺口，非該書無立場。")

st.markdown(COVERAGE_NOTE)
