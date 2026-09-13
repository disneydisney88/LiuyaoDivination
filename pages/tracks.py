import streamlit as st
from engine.semantics import semantic_for_condition
from ui_contracts import negative_category_display

st.header("多軌")
st.caption("各書保留原框架；不作綜合結論、多數決、可信度或加權。")
condition = st.selectbox("選擇 C1 決策表格位", ["旺相之爻遇沖", "有氣之爻遇沖", "臨日月之爻遇沖", "休囚之爻遇日沖", "既判為散之後"])
result = semantic_for_condition(line=3, condition=condition)
if result.get("consensus"):
    st.success("三家共識（只標示共識，不作跨軌推導）")
cols = st.columns(3)
for col, (name, track) in zip(cols, result["tracks"].items()):
    with col:
        with st.container(border=True):
            st.subheader(name)
            if track.get("category_negated"):
                st.warning(negative_category_display("CATEGORY_NEGATED"))
            elif track.get("not_addressed"):
                st.info("未表述")
            else:
                st.write(f"原框架表述：{track.get('verdict')}")
            st.caption(f"框架：{track.get('framework', '未提供')}")
            if track.get("framework_position") is not None:
                st.caption(f"看用神十八法第 {track['framework_position']} 位")
            if track.get("framework_note"):
                st.write(track["framework_note"])
            st.caption(f"出處：{track.get('source', '未表述')}")
