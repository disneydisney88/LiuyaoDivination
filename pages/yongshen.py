import streamlit as st
from ui_contracts import YONGSHEN_OPTIONS, save_cases

case = st.session_state.get("current_case")
st.header("用神")
st.caption("六個選項平權呈現；工具不預選、建議、排序或評分。")
if not case:
    st.info("請先到「起卦」建立一則卦例。")
else:
    selected = st.pills("請由使用者自行選擇（可選最多兩項）", list(YONGSHEN_OPTIONS), selection_mode="multi", key="yongshen_choices")
    if len(selected) > 2:
        st.warning("最多同時展開兩個不同用神；請取消其中一項。")
    elif st.button("保存人手選擇"):
        case["yongshen_selected"] = selected
        case["yongshen_selected_by"] = "human"
        save_cases(st.session_state.cases)
        st.success("已保存為 human 選擇；沒有自動取用神。")
    if case.get("is_proxy"):
        st.info("《增刪卜易》：功名須要親占，代占難取用神，從不敢斷。工具不阻止你繼續。")
        st.caption("來源：增刪卜易，代占相關原文。")
    if case.get("yongshen_candidates"):
        st.subheader("機械候選（仍由使用者揀）")
        for candidate in case["yongshen_candidates"]:
            with st.container(border=True):
                st.write("{}伏神：第{}爻 {}{}（飛神 {}{}）".format(
                    candidate["六親"], candidate["position"], candidate["branch"],
                    candidate["element"], candidate["flying_branch"],
                    candidate["flying_element"],
                ))
    if selected:
        cols = st.columns(len(selected))
        for col, choice in zip(cols, selected):
            with col:
                with st.container(border=True):
                    st.subheader(choice)
                    st.write("此欄只顯示使用者選擇，不輸出建議、排序或判斷。")
