import streamlit as st
from engine.build import build

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
    if derived.get("hidden"):
        st.subheader("伏神／飛神")
        st.json(derived["hidden"])
    else:
        st.caption("本卦六親俱現，沒有伏神記錄。")
    st.info("六神未實作（R-L1-07 原典待核）；本頁不填入通行說法。")
