import streamlit as st
from engine.narrate import narrate, narrate_hidden
from ui_contracts import state_for_case

case = st.session_state.get("current_case")
st.header("盤面")
if not case:
    st.info("請先到「起卦」建立一則卦例。")
else:
    state = state_for_case(case)
    derived, calendar, relations = state["chart"], state["calendar"], state["relations"]
    st.session_state.current_relation_state = relations
    st.subheader(f"{derived['name']} · {derived['palace']}宮 · {derived['palace_element']}")
    st.write(f"世：{derived['shi']}　應：{derived['ying']}　起卦時刻：{case['cast_datetime']}")
    empty_text = "、".join(relations["empty_branches"])
    break_branch = relations["month_break_branch"]
    break_positions = relations["month_break_positions"]
    if break_positions:
        break_text = "{}（第{}爻）".format(break_branch, "、".join(map(str, break_positions)))
    else:
        break_text = "{}（本卦無{}爻）".format(break_branch, break_branch)
    st.caption(
        "年柱：{}　月建：{}　日辰：{}　旬空：{}　月破：{}".format(
            calendar["year_ganzhi"], calendar["month_ganzhi"], calendar["day_ganzhi"],
            empty_text, break_text,
        )
    )
    rows = []
    relation_by_position = {row["position"]: row for row in relations["lines"]}
    for row in reversed(derived["lines_detail"]):
        position = row["position"]
        relation_row = relation_by_position[position]
        rows.append({"爻位": position, "本卦爻象": "陽" if case["lines"][position - 1] else "陰", "地支": row["branch"], "五行": row["element"], "六親": row["six_relative"], "旺衰": relation_row["seasonal_state"], "旬空": "空" if relation_row["empty"] else "", "月破": "破" if relation_row["month_break"] else "", "世／應": "世" if row["shi"] else "應" if row["ying"] else "", "動／變": "動" if position in case.get("moving_positions", []) else "", "六神": "未實作（原典待核）"})
    st.table(rows)
    if derived["hidden"]:
        st.subheader("伏神／飛神")
        for item in narrate_hidden(derived["hidden"]):
            with st.container(border=True):
                st.write(item["text"])
                st.caption("規則：{}；伏神能否為用仍待 R-L1-08b 核實。".format(item["rule_id"]))
    else:
        st.caption("本卦六親俱現，沒有伏神記錄。")
    st.subheader("逐爻推導")
    for line_row in reversed(derived["lines_detail"]):
        position = line_row["position"]
        with st.expander("{}爻 {}{}".format(position, line_row["branch"], line_row["element"]), expanded=True):
            narrative = narrate(semantics={"line": position, "hidden": derived["hidden"], "tracks": {}},
                                relations=relations)
            for step in narrative["derivation"]:
                text = "第 {} 步：{}".format(step["step"], step["text"])
                if step.get("template_missing"):
                    st.warning(text)
                else:
                    st.write(text)
    st.info("六神未實作（R-L1-07 原典待核）；本頁不填入通行說法。")
