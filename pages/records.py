import streamlit as st
from ui_contracts import RECORD_FIELDS, csv_bytes, save_cases

st.header("記錄／匯出")
st.caption("記錄只寫入本機 records/cases.jsonl；匯出前請注意檔案包含問題與背景原文。")
cases = st.session_state.cases
if not cases:
    st.info("尚未有卦例。")
else:
    labels = [f"{case['cast_datetime']} · {case['hexagram_name']} · {case['case_id'][:8]}" for case in cases]
    selected_index = st.selectbox("選擇卦例", range(len(cases)), format_func=lambda index: labels[index])
    case = cases[selected_index]
    with st.form("verification_form"):
        actual_outcome = st.text_area("事後實際結果", value=case.get("actual_outcome") or "")
        actual_outcome_date = st.text_input("應驗日期", value=case.get("actual_outcome_date") or "")
        verified = st.checkbox("已驗證", value=bool(case.get("verified")))
        verification_note = st.text_area("使用者備註", value=case.get("verification_note") or "")
        if st.form_submit_button("保存事後驗證"):
            case.update({"actual_outcome": actual_outcome, "actual_outcome_date": actual_outcome_date, "verified": verified, "verification_note": verification_note})
            save_cases(cases)
            st.success("已保存本機記錄。")
    st.json({key: case.get(key) for key in RECORD_FIELDS if key not in {"question_text", "background_text"}})
    st.warning("此檔包含問題與背景之原文。請自行保管，不要上傳至任何線上服務。")
    st.download_button("匯出 CSV", data=csv_bytes(cases), file_name="liuyao_cases.csv", mime="text/csv")
