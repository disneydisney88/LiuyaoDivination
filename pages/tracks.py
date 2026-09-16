from pathlib import Path

import streamlit as st

from engine.narrate import narrate
from engine.semantics import (
    chong_source_for_line,
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
    "A：應期候選": ROOT / "data" / "decision_tables" / "A_yingqi.json",
    "M1：墓絕之來源": ROOT / "data" / "decision_tables" / "M1_mujue_source.json",
    "M2：隨鬼入墓位次": ROOT / "data" / "decision_tables" / "M2_suiguirumu.json",
    "M3：隨墓旺衰": ROOT / "data" / "decision_tables" / "M3_suimu_wangshuai.json",
}
TABLE_AXIS_LABELS = {
    "C1": "衰旺軸",
    "C15": "動靜軸",
    "K": "空亡狀態",
    "Y": "元神／忌神狀態",
    "A": "應期候選",
    "M1": "墓絕來源",
    "M2": "隨鬼入墓位次",
    "M3": "隨墓旺衰",
}
CHINESE_COUNTS = {0: "零", 1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八"}


def chong_source_caption(cell_context: dict[str, str], relations: dict) -> str:
    """Render only mechanical clash provenance; never a doctrinal conclusion."""
    source = cell_context["chong_source"]
    month = relations.get("month_branch", "未標明")
    day = relations.get("day_branch", "未標明")
    if source == "month":
        return f"（本爻之沖來自月建{month}，非日辰）"
    if source == "day":
        return f"（本爻之沖來自日辰{day}，非月建）"
    if source == "moving_line":
        return "（本爻之沖來自動爻，非日辰或月建）"
    return f"（本爻之沖同時來自月建{month}、日辰{day}或動爻，不是單一來源）"


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
    supporting_source = track.get("supporting_source")
    if supporting_source:
        st.caption("輔助出處：{}。{}".format(
            supporting_source.get("source", "來源未標明"),
            supporting_source.get("note", ""),
        ))
        with st.expander("輔助原文（預設摺疊）"):
            st.write(supporting_source.get("original", ""))
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

session_by_case = st.session_state.get("active_yongshen_by_case", {})
session_selection = session_by_case.get(case.get("case_id"), {}) if case else {}
selected_choices = (session_selection.get("choices") or case.get("yongshen_selected") or []) if case else []
saved_ids = (session_selection.get("candidate_selections") or case.get("yongshen_candidate_selections") or {}) if case else {}
selected_candidates = []
selected_analyses = []
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
    selected_analyses.append(analyze_yongshen(state, choice, candidate_id))
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
manual_override = st.toggle(
    "手動覆寫表格位", value=False,
    key="manual_condition_override_{}".format(decision_table["table_id"]),
)

if decision_table["table_id"] == "Y" and selected_analyses and not manual_override:
    locations = [
        item for analysis in selected_analyses
        for item in analysis.get("decision_table", {}).get("Y", {}).get("locations", [])
    ]
    if locations:
        st.caption("Y 表已按所選用神的元神／忌神逐爻定位；以下只並列原有材料，不輸出效果判定。")
        conditions_by_id = {row["row_id"]: row["condition"] for row in decision_table["rows"]}
        for location in locations:
            if not location.get("matches"):
                st.caption("{} 第 {} 爻 {}{}：未命中現有機械格位。".format(
                    location["role"], location["position"], location["branch"], location["element"],
                ))
            for row_id in location.get("matches", []):
                condition = conditions_by_id[row_id]
                result = semantic_for_condition(
                    line=location["position"], condition=condition,
                    hidden=chart["hidden"] if chart else [], table=decision_table,
                )
                st.subheader("{}　{}：第 {} 爻 {}{}".format(
                    row_id, condition, location["position"], location["branch"], location["element"],
                ))
                st.caption(result["coverage_label"])
                narrative = narrate(semantics=result, relations=relation_state)
                narrative_by_book = {item["book"]: item for item in narrative["tracks"]}
                for book, track in result["tracks"].items():
                    with st.expander(book, expanded=False):
                        show_track(narrative_by_book[book], track)
        for gap in (selected_analyses[0].get("decision_table", {}).get("Y", {}).get("implementation_gaps", [])):
            st.caption(gap["message"])
        st.write("Y 表無仇神格位（P-057）")
        st.markdown(decision_table.get("table_note", ""))
        st.stop()
automatic_condition = None if hidden_selected else infer_condition(
    table_id=decision_table["table_id"], relation_result=relation_state, line=line,
)
if decision_table["table_id"] == "A" and not hidden_selected:
    from engine.semantics import infer_conditions
    a_conditions = infer_conditions(table_id="A", relation_result=relation_state, line=line)
    automatic_condition = a_conditions[0] if a_conditions else None
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
    if decision_table["table_id"] in {"M1", "M2", "M3"}:
        st.caption("{}：未接入機械層（P-064）；此訊息表示本項目尚未做格位判定，不等於此爻沒有該狀況。".format(decision_table["table_id"]))
    elif decision_table["table_id"] == "Y":
        st.caption("Y 表已按元神／忌神的可見機械狀態逐爻比對；沒有命中時不補造格位。")
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
    st.markdown(decision_table.get("table_note", ""))
    st.stop()
cell_context = None
if automatic_condition in conditions and not manual_override and decision_table["table_id"] in {"C1", "C15"}:
    source = chong_source_for_line(relation_state, line)
    if source:
        cell_context = {"chong_source": source}
result = semantic_for_condition(
    line=line, condition=condition,
    hidden=chart["hidden"] if chart else [], table=decision_table,
    cell_context=cell_context,
)
st.subheader("{}　{}".format(result["row_id"], condition))
if result.get("cell_context"):
    st.caption(chong_source_caption(result["cell_context"], relation_state))
st.caption(result["coverage_label"])
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
    ingested_not_surveyed = [
        book for book in not_collected
        if tracks[book].get("collection_status") == "ingested_not_surveyed"
    ]
    not_ingested = [
        book for book in not_collected
        if tracks[book].get("collection_status") == "not_ingested"
    ]
    axis_label = TABLE_AXIS_LABELS.get(decision_table["table_id"], "本表問題")
    if ingested_not_surveyed:
        with st.expander("未就本表之問題採集：{}".format("、".join(ingested_not_surveyed)), expanded=False):
            count = CHINESE_COUNTS.get(len(ingested_not_surveyed), str(len(ingested_not_surveyed)))
            st.caption("（{}本已入庫，但未針對{}檢索）".format(count, axis_label))
            st.write("此為採集缺口，非該書無立場。")
    if not_ingested:
        with st.expander("該書尚未入庫：{}".format("、".join(not_ingested)), expanded=False):
            st.write("此為採集缺口，非該書無立場。")

st.markdown(result.get("table_note", ""))
