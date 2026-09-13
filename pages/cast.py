from datetime import datetime
import streamlit as st
from ui_contracts import make_case, save_cases, state_for_case

st.header("起卦")
st.caption("由初爻起輸入背數；工具不代搖、不作時間起卦或報數起卦。")
with st.form("cast_form"):
    counts = [st.selectbox(f"第 {position} 爻（由初爻起）", [0, 1, 2, 3], index=None, key=f"coin_{position}") for position in range(1, 7)]
    cast_datetime = st.datetime_input("起卦時刻", value=datetime.now().replace(second=0, microsecond=0))
    question_text = st.text_input("問題（選填；只存本機）")
    background_text = st.text_area("背景（選填；只存本機）")
    is_proxy = st.checkbox("代占")
    submitted = st.form_submit_button("建立卦例", type="primary")
if submitted:
    if any(value is None for value in counts):
        st.error("請完成六爻輸入。")
    else:
        case = make_case(coin_counts=counts, cast_datetime=cast_datetime, question_text=question_text, background_text=background_text, is_proxy=is_proxy)
        st.session_state.current_case = case
        st.session_state.current_relation_state = state_for_case(case)["relations"]
        st.session_state.cases.append(case)
        save_cases(st.session_state.cases)
        st.success(f"已建立卦例：{case['case_id']}")
        st.info("問題與背景只寫入本機記錄，沒有傳入 engine 或外部服務。")
