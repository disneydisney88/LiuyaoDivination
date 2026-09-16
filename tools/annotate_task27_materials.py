"""Record TASK_CODEX_27 source locators in doctrinal envelopes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIALS = {
    "yimao_rules.json": [("A", "700; 1052"), ("M1", "468–472; 520; 526; 688"), ("M2", "520")],
    "zengshan_rules.json": [("A", "2001–2046"), ("M1", "1951; 1953; 1961; 2569"), ("M2", "2569"), ("M3", "2622–2624")],
    "buzhengzong_rules.json": [("A", "386–392"), ("M1", "244"), ("M2", "244")],
    "buzhequanshu_rules.json": [("A", "5660–5661"), ("M1", "5571–5572; 7104; 7062"), ("M2", "3097")],
    "huangjince_rules.json": [("A", "1633"), ("M1", "14; 50; 56; 66")],
}
for filename, entries in MATERIALS.items():
    path = ROOT / "data" / "doctrinal" / filename
    if not path.exists():
        continue
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["task27_materials"] = [{"table_id": table_id, "source": source} for table_id, source in entries]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
