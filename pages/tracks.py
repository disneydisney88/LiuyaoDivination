from pathlib import Path

import streamlit as st

from engine.narrate import narrate
from engine.semantics import (
    COLLECTION_GAP_TEMPLATE,
    COVERAGE_NOTE,
    infer_condition,
    load_decision_table,
    semantic_for_condition,
)
from engine.yongshen import analyze_yongshen, candidate_options
from ui_contracts import state_for_case


ROOT = Path(__file__).resolve().parents[1]
DECISION_TABLES = {
    "C1：沖與散之判定": ROOT / "data" / "decision_tables" / "C1_chong_san.json",
    "C15：沖之判定（動靜軸）": ROOT / "data" / "decision_tables" / "C15_dongjing_axis.json",
    "K：空亡之狀態材料": ROOT / "data" / "decision_tables" / "K_kongwang_effect.json",
    "Y：元神／忌神狀態材料": ROOT / "data" / "decision_tables" / "Y_yuanshen_jishen.json",
}


def show_track(track_narrative, track, *, original_collapsed=True):
    st.write(track_narrative["verdict_plain"])
    if track_narrative.get("implication"):
        st.caption(track_narrative["implication"])
    if track_narrative.get("verdict_note"):
        st.caption("判語註記：{}".format(track_narrative["verdict_note"]))
    if track_narrative.get("search_note"):
        st.caption("檢索註記：{}".format(track_narrative["search_note"]))
    if track_narrative.get("axis_note"):
        st.caption("軸向註記：{}".format(track_narrative["axis_note"]))
    if track_narrative.get("cross_reference"):
        st.caption("交叉表：{}".format(track_narrative["cross_reference"]))
    if track_narrative.get("term_note"):
        st.caption("術語註記：{}".format(track_narrative["term_note"]))
    st.caption("框架：{}".format(track.get("framework", "未提供")))
    if track.get("framework_position") is not None:
        st.caption("框架位置：{}".format(track["framework_position"]))
    if track.get("evidence_strength"):
        st.caption("證據強度：{}".format(track["evidence_strength"]))
    st.caption("出處：{}".format(track_narrative.get("source_locator") or track.get("source", "未表述")))
    if track.get("concept_absent"):
        st.caption("概念缺席註記：{}".format(track.get("absence_note", "未提供")))
    else:
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
st.caption("按資料狀態分組；不作跨軌裁決、多數決或加權。")
table_label = st.selectbox("選擇決策表", list(DECISION_TABLES))
decision_table = load_decision_table(DECISION_TABLES[table_label])
case = st.session_state.get("current_case")
relation_state = {}
chart = None
if case:
    state = state_for_case(case)
    chart, relation_state = state["chart"], state["relations"]
    st.session_state.current_relation_state = relation_state

selected_choices = (case.get("yongshen_selected") or []) if case else []
saved_ids = (case.get("yongshen_candidate_selections") or {}) if case else {}
selected_candidates = []
for choice in selected_choices:
    candidate_id = saved_ids.get(choice)
    if not candidate_id and chart:
        options = candidate_options(chart, choice)
        if len(options) == 1 and not options[0].get("hidden"):
            candidate_id = options[0]["candidate_id"]
    if not candidate_id or not chart:
        continue
    selected_candidates.extend(
        item for item in candidate_options(chart, choice)
        if item["candidate_id"] == candidate_id
    )
hidden_selected = any(item.get("hidden") for item in selected_candidates)
candidate_positions = sorted({item["position"] for item in selected_candidates})
if len(candidate_positions) == 1:
    line = candidate_positions[0]
    st.caption("已由人手所選用神定位至第 {} 爻。".format(line))
    line_options = [line]
elif len(candidate_positions) > 1:
    st.caption("所選用神對應多個候選爻位，須由使用者指定；未作自動取捨。")
    line_options = candidate_positions
else:
    st.caption("未選用神，格位自動判定暫不生效。")
    line_options = list(range(1, 7))
line = st.selectbox(
    "選擇分析爻位（手動覆寫）", line_options,
    index=0, format_func=lambda value: "第 {} 爻".format(value),
)

conditions = [row["condition"] for row in decision_table["rows"]]
automatic_condition = None if hidden_selected else infer_condition(
    table_id=decision_table["table_id"], relation_result=relation_state, line=line,
)
manual_override = False
manual_override = st.toggle(
    "手動覆寫表格位", value=False,
    key="manual_condition_override_{}".format(decision_table["table_id"]),
)
if automatic_condition in conditions:
    st.caption("按當前爻之機械狀態自動定位：{}。".format(automatic_condition))
else:
    if hidden_selected:
        hidden_item = next(item for item in selected_candidates if item.get("hidden"))
        st.caption("用神爻（第 {} 爻 {}{} {}，伏）".format(
            hidden_item["position"], hidden_item["branch"], hidden_item["element"],
            hidden_item.get("six_relative", ""),
        ))
    st.caption("此爻不觸發任何可機械定位的條件。這是目前決策表之覆蓋缺口，並非此爻無事可說。")
    if decision_table["table_id"] == "Y":
        st.caption("Y 表記錄元神／忌神狀態材料；現有引擎不以它輸出效果語義，請以手動覆寫查看指定格位。")
    else:
        st.caption("可查表包括 C1、C15、K；Y 為元神／忌神狀態材料，不作效果判定。")

if automatic_condition in conditions and not manual_override:
    condition = automatic_condition
elif manual_override:
    condition = st.selectbox(
        "選擇 {} 表格位（手動覆寫）".format(decision_table["table_id"]),
        conditions,
    )
else:
    st.caption("未選擇決策表格位；如需覆寫，請開啟「手動覆寫表格位」。")
    st.stop()
result = semantic_for_condition(
    line=line, condition=condition,
    hidden=chart["hidden"] if chart else [], table=decision_table,
)
st.subheader("{}　{}".format(result["row_id"], condition))
st.caption(result["coverage_label"])
if result["coverage"]["books_not_collected"] > 0:
    st.caption(COLLECTION_GAP_TEMPLATE.format(result["coverage"]["books_not_collected"]))
narrative = narrate(semantics=result, relations=relation_state)
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
different_axis = [book for book, track in tracks.items() if track["status"] == "different_axis"]
addressed = [book for book, track in tracks.items() if track["status"] == "addressed"]
not_addressed = [book for book, track in tracks.items() if track["status"] == "not_addressed"]
not_collected = [book for book, track in tracks.items() if track["status"] == "not_collected"]
concept_absent = [book for book, track in tracks.items() if track["status"] == "concept_absent"]
explicit_exclusion = [book for book, track in tracks.items() if track["status"] == "explicit_exclusion"]

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

if different_axis:
    st.subheader("另一軸向")
    for book in different_axis:
        with st.container(border=True):
            st.markdown("**{}**".format(book))
            show_track(narrative_by_book[book], tracks[book])

if negated:
    st.subheader("否定範疇")
    for book in negated:
        with st.container(border=True):
            st.markdown("**{}**".format(book))
            show_track(narrative_by_book[book], tracks[book])

if concept_absent:
    st.subheader("概念缺席")
    for book in concept_absent:
        with st.container(border=True):
            st.markdown("**{}**".format(book))
            show_track(narrative_by_book[book], tracks[book])

if explicit_exclusion:
    st.subheader("明文排除角色")
    for book in explicit_exclusion:
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
