import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


def load_rules():
    records = []
    for path in sorted((ROOT / "data" / "doctrinal").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for group in data.get("sets", []):
            for item in group.get("items", []):
                if item.get("rule_id"):
                    records.append({"rule_id": item["rule_id"], "source": data.get("source_book"), "chapter": item.get("chapter", group.get("chapter")), "line": item.get("line", group.get("line")), "definition_original": item.get("definition_original", "")})
    return records


st.header("原文檢索")
rules = load_rules()
query = st.text_input("輸入 rule_id 或原文關鍵字")
matches = [item for item in rules if not query or query in item["rule_id"] or query in item["definition_original"]]
st.caption(f"本地結構化資料命中 {len(matches)} 條；原文段落來源於 corpus_extracts。")
for item in matches[:100]:
    with st.container(border=True):
        st.markdown(f"**{item['rule_id']}** · {item['source']} · {item['chapter']} · 行 {item['line']}")
        st.write(item["definition_original"])
