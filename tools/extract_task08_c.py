"""Collect the requested local 卜筮正宗 passages for TASK_CODEX_08."""

from collections import Counter
from pathlib import Path
import re


SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\04_卜筮正宗\卜筮正宗_完整版_A.md")
OUTPUT = Path("corpus_extracts/TASK_CODEX_08_C.md")
SPECIAL = [(2689, 2691, "〈月破論第九〉全篇"), (2697, 2699, "〈旬空論第十〉全篇"), (432, 436, "〈辟增刪卜易之謬〉暗動條全段")]


def paragraph_records(lines):
    records = []
    start = None
    current = []
    for n, line in enumerate(lines, 1):
        if line.strip():
            if start is None:
                start = n
            current.append((n, line))
        elif current:
            records.append((start, current[-1][0], current))
            start, current = None, []
    if current:
        records.append((start, current[-1][0], current))
    return records


def nearest_heading(lines, line_no):
    heading = "未標題"
    for n in range(line_no - 1, -1, -1):
        if lines[n].startswith("## "):
            heading = lines[n][3:].strip()
            break
    return heading


def main():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    terms = ("日破", "散", "沖散", "冲散")
    counts = Counter({term: sum(line.count(term) for line in lines) for term in terms})
    line_counts = Counter({term: sum(term in line for line in lines) for term in terms})
    records = []
    for start, end, block in paragraph_records(lines):
        present = [term for term in terms if any(term in line for _, line in block)]
        if present:
            records.append((start, end, present, block, nearest_heading(lines, start)))

    report = [
        "# TASK_CODEX_08 C —《卜筮正宗》日破／散術語核查",
        "",
        "來源：指定本地語料 `04_卜筮正宗/卜筮正宗_完整版_A.md`，UTF-8 讀取。以下只出原文與文本層對照，不判定歸軌，不裁決 conflict。",
        "",
        "## 字頻統計",
        "",
        "| 詞項 | 出現次數 | 含詞行數 |",
        "|---|---:|---:|",
    ]
    for term in terms:
        report.append(f"| {term} | {counts[term]} | {line_counts[term]} |")
    report.extend(["", "## 指定全篇／全段原文", ""])
    for index, (start, end, title) in enumerate(SPECIAL, 1):
        text = "".join(lines[start - 1 : end])
        report.extend([f"### {index}. {title}", "", f"行號：{start}–{end}", f"字數：{len(text)}（含標點，不含換行）", "", "```text"])
        report.extend(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
        report.extend(["```", ""])

    report.extend(["## 所有含「日破」／「散」／「沖散／冲散」之完整段落", "", f"共 {len(records)} 段；每段按空行分隔，原文逐行保留。"])
    for index, (start, end, present, block, heading) in enumerate(records, 1):
        report.extend(["", f"### 段落 {index}：{heading}", f"行號：{start}–{end}；詞項：{'、'.join(present)}", "", "```text"])
        report.extend(f"{n}: {line}" for n, line in block)
        report.append("```")

    report.extend([
        "",
        "## 文本層對照表",
        "",
        "| 項目 | 易冒所載 | 卜筮正宗所載 | 文本層是否一致 |",
        "|---|---|---|---|",
        "| 「日破」之定義 | 類總章 698：「十四曰日破，日月克伤，时令休囚，爻神被冲，破其半矣，又重于死气也」 | 暗動條 436：「休囚者……遇冲则散，名为日破」；本次全文另見所有含「日破」段落 | 卜筮正宗載有休囚遇沖名為日破；完整定義句式不同，是否同一現象待定 |",
        "| 「散」之定義 | 類總章 698：「十八曰散，谓动逢日神变动之冲而散，虽救之无从，是谓大凶」 | 暗動條 436 載「遇冲则散」；日辰條 200、410 載「冲散」作動詞；全文另有多種「散」語境 | 均出現「散」字，但本表不裁決定義是否等同 |",
        "| 休囚遇日沖之後果 | 日沖章 416：「苟非月建，则谓之散」 | 暗動條 436：「休囚者……遇冲则散，名为日破」 | 均載休囚遇沖及「散／日破」字樣；命名關係待定 |",
        "| 二者是否同一現象 | 十八法分列第 14「日破」及第 18「散」 | 卜筮正宗 436 將「遇冲则散」與「名為日破」置於同一段 | 文本並列材料；不作歸軌判定 |",
        "## 範圍說明",
        "",
        "- 已搜尋指定《卜筮正宗》全文；沒有引用其他書補充缺口。",
        "- 所有含目標詞之段落均保留；指定三處全篇／全段另行完整列出。",
    ])
    OUTPUT.write_text("\n".join(report), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
