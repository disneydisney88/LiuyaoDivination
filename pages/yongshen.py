import streamlit as st

from engine.yongshen import analyze_yongshen, candidate_options
from ui_contracts import YONGSHEN_OPTIONS, save_cases, state_for_case

case = st.session_state.get("current_case")
st.header("用神")
st.caption("六個選項平權呈現；工具不預選、建議、排序或評分。")
if not case:
    st.info("請先到「起卦」建立一則卦例。")
else:
    selected = st.pills(
        "請由使用者自行選擇（可選最多兩項）", list(YONGSHEN_OPTIONS),
        selection_mode="multi", default=case.get("yongshen_selected") or [],
        key="yongshen_choices",
    ) or []
    state = state_for_case(case)
    candidate_selections = {}
    if len(selected) > 2:
        st.warning("最多同時展開兩個不同用神；請取消其中一項。")
    else:
        for choice in selected:
            options = candidate_options(state["chart"], choice)
            if len(options) == 1:
                candidate_selections[choice] = options[0]["candidate_id"]
                st.caption(f"{choice}：唯一候選 {options[0]['candidate_id']}（由規則列出，非用神建議）")
            elif options:
                labels = [
                    f"第 {item['position']} 爻 {item['branch']}{item['element']}"
                    + ("（伏神）" if item.get("hidden") else "")
                    for item in options
                ]
                picked = st.selectbox(
                    f"{choice}：請人手指定候選爻位", options=list(range(len(options))),
                    index=None, format_func=lambda index: labels[index],
                    key=f"yongshen_candidate_{choice}",
                )
                if picked is not None:
                    candidate_selections[choice] = options[picked]["candidate_id"]
            else:
                st.caption(f"{choice}：本卦未見可列候選。")
        if st.button("保存人手選擇"):
            case["yongshen_selected"] = selected
            case["yongshen_candidate_selections"] = candidate_selections
            case["yongshen_selected_by"] = "human"
            save_cases(st.session_state.cases)
            st.success("已保存為 human 選擇；沒有自動取用神。")
    if case.get("is_proxy"):
        st.info("《增刪卜易》：功名須要親占，代占難取用神，從不敢斷。工具不阻止你繼續。")
        st.caption("來源：增刪卜易，代占相關原文。")
    if selected:
        cols = st.columns(len(selected))
        for col, choice in zip(cols, selected):
            with col:
                with st.container(border=True):
                    st.subheader(choice)
                    candidate_id = candidate_selections.get(choice) or case.get("yongshen_candidate_selections", {}).get(choice)
                    if not candidate_id:
                        st.write("候選未由使用者指定；不自動取捨。")
                        continue
                    analysis = analyze_yongshen(state, choice, candidate_id)
                    selected_candidate = analysis.get("selected") or {}
                    st.write(
                        f"已指定：第 {selected_candidate.get('position')} 爻 "
                        f"{selected_candidate.get('branch')}{selected_candidate.get('element')}"
                        + ("（伏神）" if selected_candidate.get("hidden") else "")
                    )
                    own = analysis.get("own_state") or {}
                    st.write(
                        "用神狀態：{}、{}、{}、{}、{}。".format(
                            own.get("seasonal_state", "未有"),
                            "旬空" if own.get("empty") else "非旬空",
                            "月破" if own.get("month_break") else "非月破",
                            "；".join(own.get("day_relations", [])) or "日辰無附加標記",
                            own.get("motion", "未有"),
                        )
                    )
                    for label, key in (("元神", "yuan_shen"), ("忌神", "ji_shen"), ("仇神", "chou_shen")):
                        entries = analysis.get(key, [])
                        st.write(f"{label}：" + ("、".join(f"第{x['position']}爻" for x in entries) if entries else "未見"))
                    decision = analysis.get("decision_table", {})
                    st.write(
                        "格位：C1 {}；C15 {}。".format(
                            decision.get("C1") or decision.get("status"),
                            decision.get("C15") or decision.get("status"),
                        )
                    )
