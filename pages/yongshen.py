import streamlit as st

from engine.yongshen import (
    LINE_POSITION_OPTIONS,
    SIX_RELATIVE_OPTIONS,
    analyze_yongshen,
    candidate_options,
)
from ui_contracts import save_cases, state_for_case


def _state_text(state: dict) -> str:
    if not state:
        return "狀態資料未提供"
    return "{}、{}、{}、{}".format(
        state.get("seasonal_state", "未有旺衰"),
        "旬空" if state.get("empty") else "非旬空",
        "月破" if state.get("month_break") else "非月破",
        "動" if state.get("motion") == "動" else state.get("motion", "靜"),
    )


def _candidate_label(item: dict) -> str:
    state = item.get("state", {})
    return "第 {} 爻 {}{} {}（{}）{}".format(
        item["position"], item["branch"], item["element"],
        item.get("six_relative", ""), _state_text(state),
        "（伏神）" if item.get("hidden") else "",
    )


def _role_line(item: dict) -> str:
    state = item.get("state", {})
    suffix = "　← 此爻即用神之飛神" if item.get("is_flying_of_yongshen") else ""
    return "第 {} 爻 {}{} {}　{}{}".format(
        item["position"], item["branch"], item["element"],
        item.get("six_relative", ""), _state_text(state), suffix,
    )


def _render_analysis(analysis: dict) -> None:
    selected = analysis["selected"]
    own = analysis["own_state"]
    st.write(
        "用神：第 {} 爻（{}）{}{} {}　{}".format(
            selected["position"], "伏" if selected.get("hidden") else "現",
            selected["branch"], selected["element"], selected.get("six_relative", ""),
            _state_text(own),
        )
    )
    for label, key in (("元神", "yuan_shen"), ("忌神", "ji_shen"), ("仇神", "chou_shen")):
        entries = analysis.get(key, [])
        st.write(label + "：" + ("；".join(_role_line(item) for item in entries) if entries else "卦中不現"))

    relation = analysis.get("flying_hidden_relation")
    if relation:
        st.write(
            "飛伏關係：飛神{}{} {} 伏神{}{} —— 屬《易冒》飛伏五態之「{}」。".format(
                relation["flying_branch"], relation["flying_element"], relation["relation"],
                relation["hidden_branch"], relation["hidden_element"], relation["doctrinal_label"],
            )
        )
        st.caption("原文：{}；出處：{}。{}；其餘各書：not_collected。".format(
            relation["original"], relation["source_locator"], relation["doctrinal_status"],
        ))

    decision = analysis.get("decision_table", {})
    st.subheader("格位判定")
    st.write("C1（衰旺軸）：{}".format(decision.get("C1") or "不觸發任何條件"))
    st.write("C15（動靜軸）：{}".format(decision.get("C15") or "不觸發任何條件"))
    st.write("K（空亡狀態）：{}".format(decision.get("K") or "不觸發任何條件"))
    st.write("Y（元神／忌神狀態）：{}".format(decision.get("Y") or "待選定用神爻"))
    if decision.get("coverage_gap_note"):
        st.caption("覆蓋缺口：" + decision["coverage_gap_note"])


case = st.session_state.get("current_case")
st.header("用神")
st.caption("兩組選擇各自平權呈現；工具不預選、不建議、不排序、不評分。")
if not case:
    st.info("請先到「起卦」建立一則卦例。")
else:
    relative_choices = st.pills(
        "按六親選", list(SIX_RELATIVE_OPTIONS), selection_mode="multi",
        key="yongshen_relative_choices",
    ) or []
    line_choices = st.pills(
        "按爻位選", list(LINE_POSITION_OPTIONS), selection_mode="multi",
        key="yongshen_line_choices",
    ) or []
    widget_choices = list(relative_choices) + list(line_choices)
    saved_choices = list(case.get("yongshen_selected") or [])
    active_choices = widget_choices or saved_choices
    if len(active_choices) > 2:
        st.warning("最多同時展開兩個不同用神；請取消其中一項。")
        active_choices = active_choices[:2]

    state = state_for_case(case)
    saved_ids = case.get("yongshen_candidate_selections") or {}
    candidate_selections = {}
    analyses = {}
    for choice in active_choices:
        options = candidate_options(state["chart"], choice)
        option_ids = {item["candidate_id"] for item in options}
        saved_id = saved_ids.get(choice)
        if saved_id in option_ids and not widget_choices:
            candidate_id = saved_id
        elif len(options) == 1 and not options[0].get("hidden"):
            candidate_id = options[0]["candidate_id"]
            st.caption(f"{choice}：卦中僅此一爻，依機械結果鎖定；非工具建議。")
        elif options and all(item.get("hidden") for item in options):
            st.write(f"{choice} → 卦中不現")
            hidden_choice = st.radio(
                "請人手決定伏神處置（必須明確選擇）",
                ["用伏神為用神", "不用，改揀其他"], index=None,
                key=f"hidden_decision_{choice}",
            )
            candidate_id = options[0]["candidate_id"] if hidden_choice == "用伏神為用神" else None
            st.caption("伏神能否為用，各家未有定論。現僅得《易冒》一方原文；其餘各書未採集 —— R-L1-08b 待核。")
        elif options:
            st.write(f"{choice} → 卦中兩現或以上，請揀其一（按爻位由上至下排列，非優劣排序）")
            labels = [_candidate_label(item) for item in options]
            picked = st.radio(
                "請人手指定候選爻位", labels, index=None,
                key=f"candidate_choice_{choice}",
            )
            candidate_id = options[labels.index(picked)]["candidate_id"] if picked else None
        else:
            st.caption(f"{choice}：本卦未見可列候選。")
            candidate_id = None

        if candidate_id:
            candidate_selections[choice] = candidate_id
        analysis = analyze_yongshen(state, choice, candidate_id) if candidate_id else analyze_yongshen(state, choice)
        analyses[choice] = analysis

    if active_choices and st.button("保存人手選擇"):
        case["yongshen_selected"] = active_choices
        case["yongshen_candidate_selections"] = candidate_selections
        case["yongshen_selected_by"] = "human"
        save_cases(st.session_state.cases)
        st.success("已保存為 human 選擇；沒有自動取捨。")

    if case.get("is_proxy"):
        st.info("《增刪卜易》：功名須要親占，代占難取用神，從不敢斷。工具不阻止你繼續。")
        st.caption("來源：增刪卜易，代占相關原文。")

    if analyses:
        cols = st.columns(len(analyses))
        for col, (choice, analysis) in zip(cols, analyses.items()):
            with col:
                with st.container(border=True):
                    st.subheader(choice)
                    if analysis.get("status") == "pending_selection":
                        st.write("候選未由使用者指定；四神推導暫不執行。")
                        for item in analysis["candidates"]:
                            st.write("○ " + _candidate_label(item))
                        continue
                    _render_analysis(analysis)
