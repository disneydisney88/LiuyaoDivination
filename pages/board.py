import streamlit as st
from engine.build import build
from engine.narrate import narrate, narrate_hidden

case = st.session_state.get("current_case")
st.header("盤面")
if not case:
    st.info("請先到「起卦」建立一則卦例。")
else:
    derived = build(case["lines"])
    st.subheader(f"{derived['name']} · {derived['palace']}宮 · {derived['palace_element']}")
    st.write(f"世：{derived['shi']}　應：{derived['ying']}　起卦時刻：{case['cast_datetime']}")
    st.caption(f"月建：{case['month_branch']}　日辰：{case['day_branch']}　旬空：待接入日干曆法　月破：待 L2 語義層")
    rows = []
    for row in reversed(derived["lines_detail"]):
        position = row["position"]
        rows.append({"爻位": position, "本卦爻象": "陽" if case["lines"][position - 1] else "陰", "地支": row["branch"], "五行": row["element"], "六親": row["six_relative"], "世／應": "世" if row["shi"] else "應" if row["ying"] else "", "動／變": "動" if position in case.get("moving_positions", []) else "", "六神": "未實作（原典待核）"})
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
                                relations=st.session_state.get("current_relation_state", {}))
            for step in narrative["derivation"]:
                st.write("第 {} 步：{}".format(step["step"], step["text"]))
    st.info("六神未實作（R-L1-07 原典待核）；本頁不填入通行說法。")
