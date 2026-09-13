import streamlit as st
from engine.narrate import narrate
from engine.semantics import semantic_for_condition

st.header("多軌")
st.caption("各書保留原框架；不作綜合結論、多數決、可信度或加權。")
condition = st.selectbox("選擇 C1 決策表格位", ["旺相之爻遇沖", "有氣之爻遇沖", "臨日月之爻遇沖", "休囚之爻遇日沖", "既判為散之後"])
result = semantic_for_condition(line=3, condition=condition)
narrative = narrate(semantics=result, relations=st.session_state.get("current_relation_state", {}))
st.subheader(narrative["header"])
for step in narrative["derivation"]:
    label = "推導第 {}".format(step["step"])
    if step.get("template_missing"):
        st.warning("{}：{}".format(label, step["text"]))
    else:
        st.write("{}：{}（{}）".format(label, step["text"], step.get("rule_id")))
if result.get("consensus"):
    st.success("三家共識（只標示共識，不作跨軌推導）")
cols = st.columns(3)
for col, track_narrative in zip(cols, narrative["tracks"]):
    name = track_narrative["book"]
    track = result["tracks"][name]
    with col:
        with st.container(border=True):
            st.subheader(name)
            if track_narrative.get("category_negated"):
                st.warning(track_narrative["verdict_plain"])
            else:
                st.write(track_narrative["verdict_plain"])
            if track_narrative.get("implication"):
                st.caption(track_narrative["implication"])
            st.caption(f"框架：{track.get('framework', '未提供')}")
            if track.get("framework_position") is not None:
                st.caption(f"看用神十八法第 {track['framework_position']} 位")
            if track.get("framework_note"):
                st.write(track["framework_note"])
            st.caption(f"出處：{track_narrative.get('source_locator') or track.get('source', '未表述')}")
            with st.expander("原文（預設摺疊）"):
                st.write(track_narrative.get("original") or "現有 doctrinal 資料未提供逐字原文。")
