import streamlit as st
from ui_contracts import RECORD_FIELDS, csv_bytes, save_cases


# The record schema is intentionally more detailed than the user-facing summary.
# Keep implementation-only field names out of the page; the full local JSONL and
# CSV export remain available to the record owner.
_FIELD_LABELS = {
    "case_id": "卦例識別碼",
    "cast_datetime": "起卦時間",
    "lines": "六爻陰陽",
    "is_proxy": "是否代占",
    "hexagram_name": "卦名",
    "palace": "卦宮",
    "palace_element": "卦宮五行",
    "shi": "世爻位置",
    "ying": "應爻位置",
    "year_ganzhi": "年干支",
    "month_ganzhi": "月干支",
    "day_ganzhi": "日干支",
    "xunkong": "旬空",
    "month_break_branch": "月破地支",
    "month_break": "月破爻位",
    "hidden": "伏神資料",
    "yongshen_selected": "所選用神",
    "yongshen_selected_by": "用神選擇方式",
    "yongshen_candidates": "用神候選",
    "yingqi_candidates": "應期候選",
    "actual_outcome": "事後實際結果",
    "actual_outcome_date": "應驗日期",
    "verified": "已驗證",
    "verification_note": "事後備註",
}
_INTERNAL_SUMMARY_FIELDS = {
    "year_stem", "year_branch", "month_stem", "month_branch",
    "day_stem", "day_branch", "yongshen_candidate_selections",
    "narration_template_ids", "template_missing",
}


def _display_label(key):
    if key.startswith("track_") and key.endswith("_verdict"):
        return "各書材料格位"
    return _FIELD_LABELS.get(key, key)


def _display_value(value):
    """Summarise record fields without exposing a raw JSON object in the UI."""
    if value is None or value == "":
        return "未填"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (list, tuple)):
        return "{} 項".format(len(value))
    if isinstance(value, dict):
        return "{} 欄".format(len(value))
    return str(value)

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
    st.subheader("目前卦例欄位")
    st.table([
        {"欄位": _display_label(key), "內容": _display_value(case.get(key))}
        for key in RECORD_FIELDS
        if key not in {"question_text", "background_text", *_INTERNAL_SUMMARY_FIELDS}
    ])
    st.warning("此檔包含問題與背景之原文。請自行保管，不要上傳至任何線上服務。")
    st.download_button("匯出 CSV", data=csv_bytes(cases), file_name="liuyao_cases.csv", mime="text/csv")
