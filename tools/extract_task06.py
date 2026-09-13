"""Produce TASK_CODEX_06 chapter material and append explicit corrections to TASK_05."""

from __future__ import annotations

from pathlib import Path
import re

SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\07_易冒\易冒.txt")
A_OUTPUT = Path("corpus_extracts/TASK_CODEX_06_A.md")
B_OUTPUT = Path("corpus_extracts/TASK_CODEX_05.md")
CHAPTER_START = 671
CHAPTER_END = 704


def source_lines() -> list[str]:
    return SOURCE.read_text(encoding="utf-8").splitlines()


def scatter_contexts(lines: list[str]) -> list[tuple[int, int, str]]:
    result = []
    number = 0
    for line_no in range(CHAPTER_START, CHAPTER_END + 1):
        line = lines[line_no - 1]
        for column, char in enumerate(line, 1):
            if char != "散":
                continue
            number += 1
            left = max(0, column - 1 - 30)
            right = min(len(line), column - 1 + 1 + 30)
            result.append((number, line_no, f"{line[left:right]}"))
    return result


def severity_lines(lines: list[str]) -> list[tuple[int, str]]:
    terms = re.compile(r"重|輕|轻|較重|较重|不及|勝|胜|尤|全吉|半吉|大凶|吉之半")
    return [(n, lines[n - 1]) for n in range(CHAPTER_START, CHAPTER_END + 1) if terms.search(lines[n - 1])]


def eighteen_laws(lines: list[str]) -> list[tuple[int, str, str]]:
    text = lines[697]
    # The source gives the entire closed list in one paragraph. Keep each
    # numbered item verbatim, including the source's repeated "八者" wording.
    matches = list(re.finditer(r"([一二三四五六七八九十]+)曰", text))
    result = []
    for index, match in enumerate(matches):
        ordinal = match.group(1)
        body_end = matches[index + 1].start() if index + 1 < len(matches) else text.find("，谓动逢", match.end())
        if body_end < 0:
            body_end = len(text)
        body = text[match.end() : body_end].rstrip("；，")
        result.append((698, ordinal, f"{ordinal}曰{body}"))
    return result


def append_corrections() -> None:
    original = B_OUTPUT.read_text(encoding="utf-8")
    marker = "\n## TASK_CODEX_06 修正附錄\n"
    if marker in original:
        original = original.split(marker, 1)[0].rstrip() + "\n"

    corrections = """
## TASK_CODEX_06 修正附錄

本節保留上方 TASK_CODEX_05 原主表及原統計；以下只追加本輪修正，不覆蓋原標記。修正按完整所屬段落之字面處理。

### B1 可救性修正

| 位置 | 原標 | 修正 | 理由（原文） |
|---|---|---|---|
| 370:37 | 明文可救 | 明文不可救 | 「日散月破而不相救也」 |
| 698:368 | 明文可救 | 明文不可救 | 「十八曰散……虽救之无从，是谓大凶」 |
| 698:380 | 明文可救 | 明文不可救 | 同一完整段落：「虽救之无从，是谓大凶」 |
| 744:9 | 明文可救 | 未表态 | 「应空破散，则无周急之情」；段内「救」字不构成对“散”之救否明文表述 |
| 744:38 | 明文可救 | 未表态 | 同一完整段落；无针对“散”之救否明文表述 |
| 1034:69 | 明文可救 | 明文可救 | 「遇日月动变有一能救者，危而复安」 |
| 1035:7 | 明文可救 | 明文可救 | 同一完整段落：「以上七法系大凶，得日月动变有一能救者，则反观之」 |
| 1051:108 | 明文可救 | 兩可 | 同段同时出现「元神遭破散之际」及其他例句「其病可痊」／「似可救」与「是夕遂卒」 |
| 1051:339 | 明文可救 | 兩可 | 同一完整段落同时含「似可救」「其病可痊」及「冲散元神，是夕遂卒」 |
| 1293:41 | 明文可救 | 明文不可救 | 「倘占时原属破散，失救援」 |
| 1525:33 | 明文可救 | 未表态 | 「空散不为我而遘求」为不利表述，但该处没有对“散”明言救之可否；段内「救火」属另一比喻 |

修正後 11 個原「明文可救」位置：明文不可救 4、明文可救 2、兩可 2、未表態 3。

### B2 「動作」詞性複查

全文檢查《易冒》含「散」之 196 個位置。唯一明確符合「施事＋沖散＋對象」字面結構者為：

| 位置 | 原標 | 修正 | 原文 |
|---|---|---|---|
| 1051:339 | 狀態 | 動作 | 「次日庚申，冲散元神，是夕遂卒」 |

其餘含「冲散／沖散」者未逐字明列對象，或用作狀態／分類語句；本輪不推測，保留原標或標「無法判定」。

## TASK_CODEX_06 待核清單更新

上輪 7 項 → 本輪 8 項。新增 1 項；原有 7 項全部累積保留，沒有任何結案移除：

1. R-L1-06 六親原典用字
2. R-L1-07 六神原典
3. R-L1-08b 伏神能否為用
4. R-UI-01 銅錢正反對應
5. GLM-4-Flash endpoint／額度／ZDR
6. C1-經驗指控
7. C1 空亡／沖散效果語義
8. 易冒「空」字普查未全量（TASK_CODEX_05 B 部分只涵蓋 10.52%）
"""
    B_OUTPUT.write_text(original.rstrip() + "\n" + corrections.strip() + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    lines = source_lines()
    chapter = lines[CHAPTER_START - 1 : CHAPTER_END]
    chars = sum(len(line) for line in chapter)
    contexts = scatter_contexts(lines)
    severity = severity_lines(lines)
    laws = eighteen_laws(lines)

    report: list[str] = [
        "# TASK_CODEX_06 A —〈類總章第四十一〉全章及機械標記",
        "",
        "來源：指定本地語料 `07_易冒/易冒.txt`，UTF-8 讀取。以下只出原文及機械定位／分類材料，不改 SPEC，不裁決 conflict，不實作效果語義。",
        "",
        "## 章名、行號範圍、字數",
        "",
        f"- 章名：類總章第四十一",
        f"- 原文行號：{CHAPTER_START}–{CHAPTER_END}（下一章章首為 705 行〈国事章第四十二〉）",
        f"- 字數：{chars}（含標點，不含換行）",
        "",
        "## 全章原文",
        "",
        "```text",
    ]
    report.extend(f"{n}: {lines[n - 1]}" for n in range(CHAPTER_START, CHAPTER_END + 1))
    report.extend(["```", "", "## 凶陷十八法清單", "", "| 序數（原文） | 名稱／定義原文 | 行號 |", "|---|---|---:|"])
    for line_no, ordinal, body in laws:
        report.append(f"| {ordinal} | {body} | {line_no} |")
    report.extend([
        "",
        "原文在「七曰動生」後直接寫「八曰安」及「八者用神全吉之象也」，其後由「九曰」續至「十八曰」；本表保留該原文序數，沒有補齊或改寫。",
        "",
        "## 21 處「散」字：行號及前後約 30 字",
        "",
        "| # | 行號 | 前後約 30 字原文窗口 |",
        "|---:|---:|---|",
    ])
    for number, line_no, context in contexts:
        report.append(f"| {number} | {line_no} | {context} |")
    report.extend(["", "## 嚴重度比較語句", "", "| 行號 | 原文 |", "|---:|---|"])
    for line_no, text in severity:
        report.append(f"| {line_no} | {text} |")
    report.extend([
        "",
        "## 範圍及保留說明",
        "",
        "- 全章由章首 671 行至下一章章首前 704 行完整保留，正文及夾註均在內。",
        "- 「散」按字元位置計數，21 處全部列出；同一行多個位置分開列出。",
        "- 嚴重度比較語句按明示比較字樣／排序字樣列出，未將其轉換為效果規則。",
    ])
    A_OUTPUT.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    append_corrections()


if __name__ == "__main__":
    main()
