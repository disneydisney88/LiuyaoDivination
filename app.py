import streamlit as st

from ui_contracts import load_cases

st.set_page_config(page_title="LiuyaoDivination", page_icon="☯", layout="wide")
st.session_state.setdefault("current_case", None)
st.session_state.setdefault("cases", load_cases())
st.session_state.setdefault("yongshen_selections", [])
pages = [
    st.Page("pages/cast.py", title="起卦"),
    st.Page("pages/board.py", title="盤面"),
    st.Page("pages/yongshen.py", title="用神"),
    st.Page("pages/tracks.py", title="多軌"),
    st.Page("pages/search.py", title="原文檢索"),
    st.Page("pages/records.py", title="記錄／匯出"),
]
page = st.navigation(pages, position="top")
st.title("LiuyaoDivination")
st.caption("本機計算紙：機械裝卦交由工具，專業判斷留返畀人。")
page.run()
