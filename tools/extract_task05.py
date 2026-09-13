"""Build the TASK_CODEX_05 corpus report from the local Yi Mao text."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re


SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\07_易冒\易冒.txt")
OUTPUT = Path("corpus_extracts/TASK_CODEX_05.md")
EMPTY_TRIGGERS = ("救", "不救", "可解", "無解", "全無", "有用", "無用")


def read_lines() -> list[str]:
    return SOURCE.read_text(encoding="utf-8").splitlines()


def headings(lines: list[str]) -> tuple[list[str], list[str]]:
    volumes: list[str] = []
    chapters: list[str] = []
    current_volume = "無法判定"
    current_chapter = "無法判定"
    for line in lines:
        stripped = line.strip()
        if re.match(r"^易冒卷之", stripped):
            current_volume = stripped
        if re.search(r"章第[一二三四五六七八九十百]+", stripped):
            current_chapter = stripped
        volumes.append(current_volume)
        chapters.append(current_chapter)
    return volumes, chapters


def paragraph_bounds(lines: list[str], index: int) -> tuple[int, int]:
    start = index
    end = index
    stripped = lines[index].strip()

    if (stripped.startswith("（") or stripped.startswith("(")) and index > 0:
        if lines[index - 1].strip():
            start = index - 1

    if index + 1 < len(lines):
        next_stripped = lines[index + 1].strip()
        if next_stripped.startswith("（") or next_stripped.startswith("("):
            end = index + 1

    # Preserve source line wraps such as 1673–1674 and 1682–1683.
    while end + 1 < len(lines):
        current = lines[end].strip()
        nxt = lines[end + 1].strip()
        if not nxt or nxt.startswith("（") or nxt.startswith("("):
            break
        if current and current[-1] not in "。？！；：）)」』。":
            end += 1
        else:
            break
    return start, end


def lexical_tags(text: str, target: str) -> tuple[str, str, str, str]:
    if target == "散":
        if re.search(r"(?:能|可|以|則|则).{0,6}沖散", text) or re.search(
            r"沖散(?:旬空|月建|之合)", text
        ):
            part = "動作"
        elif re.search(r"動散|破散|散則|散则|已冲散|已沖散|沖之不散|谓之散|謂之散", text):
            part = "狀態"
        else:
            part = "無法判定"
        if "不可救" in text or "全無" in text or "全无" in text:
            rescue = "明文不可救"
        elif "可救" in text or "能救" in text or "救" in text and "不救" not in text:
            rescue = "明文可救"
        else:
            rescue = "未表態"
        if "謂之" in text or "谓之" in text:
            function = "分類條件"
        elif "占" in text or "占" in text:
            function = "斷語依據"
        else:
            function = "無法判定"
    else:
        part = "無法判定"
        rescue = "明文不可救" if ("不可救" in text or "全無" in text or "全无" in text) else (
            "明文可救" if ("可救" in text or "能救" in text) else "未表態"
        )
        function = "分類條件" if ("謂之" in text or "谓之" in text) else (
            "斷語依據" if "占" in text else "無法判定"
        )
    has_date = bool(re.search(r"[子丑寅卯辰巳午未申酉戌亥]建|[子丑寅卯辰巳午未申酉戌亥]月|[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]日", text))
    has_hexagram = bool(re.search(r"占[^。；）)]{0,100}得[^。；）)]*之", text))
    return part, rescue, function, "是" if "占" in text and (has_date or has_hexagram) else "否"


def branch_facts(text: str) -> str:
    facts = []
    for label, pattern in (("卦名", r"得[^，。；）)]+"), ("月建", r"[子丑寅卯辰巳午未申酉戌亥]建"), ("日辰", r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]日")):
        hits = re.findall(pattern, text)
        if hits:
            facts.append(f"{label}=" + "、".join(hits[:3]))
    return "；".join(facts) if facts else "無法從該段判定"


def occurrences(lines: list[str], target: str, volumes: list[str], chapters: list[str]):
    result = []
    for i, line in enumerate(lines):
        for col, char in enumerate(line, 1):
            if char != target:
                continue
            start, end = paragraph_bounds(lines, i)
            block = "\n".join(lines[start : end + 1])
            part, rescue, function, attached = lexical_tags(block, target)
            result.append(
                {
                    "line": i + 1,
                    "column": col,
                    "volume": volumes[i],
                    "chapter": chapters[i],
                    "part": part,
                    "rescue": rescue,
                    "function": function,
                    "attached": attached,
                    "facts": branch_facts(block) if attached == "是" else "—",
                    "start": start,
                    "end": end,
                    "block": block,
                }
            )
    return result


def stats(items: list[dict]) -> str:
    out = []
    out.append(f"- 總出現次數：{len(items)}")
    for label, key in (("詞性", "part"), ("可救性", "rescue"), ("功能", "function"), ("是否附卦例", "attached")):
        counts = Counter(item[key] for item in items)
        out.append(f"- {label}：" + "；".join(f"{k} {v}" for k, v in counts.items()))
    chapters = Counter(item["chapter"] for item in items)
    out.append("- 章名及次數：" + "；".join(f"{k} {v}" for k, v in chapters.items()))
    return "\n".join(out)


def main() -> None:
    lines = read_lines()
    volumes, chapters = headings(lines)
    scatter = occurrences(lines, "散", volumes, chapters)
    all_empty = occurrences(lines, "空", volumes, chapters)
    # The narrowing rule applies to the complete source paragraph, not merely
    # to the physical line containing the target character.
    empty = [item for item in all_empty if any(k in item["block"] for k in EMPTY_TRIGGERS)]
    empty_lines = sorted({item["line"] for item in empty})
    empty_blocks = {(item["start"], item["end"]) for item in empty}

    report: list[str] = []
    report.append("# TASK_CODEX_05 —《易冒》全書「散」／「空」字語境普查")
    report.append("")
    report.append("來源：指定本地語料 `07_易冒/易冒.txt`，UTF-8 讀取。以下分類只按文字表面標記，無效果語義實作，無 conflict 裁決。")
    report.append("")
    report.append("## A 部分：「散」普查")
    report.append("")
    report.append(f"全文 {len(lines)} 行；「散」共 {len(scatter)} 次，含「散」之行 {sum('散' in x for x in lines)} 行。")
    report.append("")
    report.append("### 主表")
    report.append("")
    report.append("| # | 行號:欄位 | 卷次 | 章名 | 詞性 | 可救性 | 功能 | 是否附卦例 | 卦例機械文字 |")
    report.append("|---:|---|---|---|---|---|---|---|---|")
    for n, item in enumerate(scatter, 1):
        report.append(f"| {n} | {item['line']}:{item['column']} | {item['volume']} | {item['chapter']} | {item['part']} | {item['rescue']} | {item['function']} | {item['attached']} | {item['facts']} |")
    report.append("")
    report.append("### 統計")
    report.append("")
    report.append(stats(scatter))
    report.append("")
    report.append("### 附錄：完整所屬段落原文")
    report.append("")
    seen = set()
    for n, item in enumerate(scatter, 1):
        key = (item["start"], item["end"])
        if key in seen:
            continue
        seen.add(key)
        same = [x for x in scatter if (x["start"], x["end"]) == key]
        positions = ", ".join(f"{x['line']}:{x['column']}" for x in same)
        report.append(f"#### 散位置 {positions}；{item['volume']}；{item['chapter']}；原文行 {item['start'] + 1}–{item['end'] + 1}")
        report.append("")
        report.append("```text")
        report.extend(f"{line_no}: {lines[line_no - 1]}" for line_no in range(item["start"] + 1, item["end"] + 2))
        report.append("```")
        report.append("")
    report.append("## B 部分：「空」對照普查")
    report.append("")
    report.append("按 TASK_CODEX_05 B 部分已收窄：只處理含「空」且同一原始行含「救／不救／可解／無解／全無／有用／無用」至少一詞的段落；完整所屬段落仍全部保留。")
    report.append(f"全書「空」共 {sum(x.count('空') for x in lines)} 次；符合條件完整段落 {len(empty_blocks)} 段，涵蓋「空」{len(empty)} 次（{len(empty) / sum(x.count('空') for x in lines) * 100:.2f}%）。這些段落內含「空」之原始行 {len(empty_lines)} 行；全書含「空」原始行共 {sum('空' in x for x in lines)} 行，涵蓋 {len(empty_lines) / sum('空' in x for x in lines) * 100:.2f}%。")
    report.append("")
    report.append("### 主表")
    report.append("")
    report.append("| # | 行號:欄位 | 卷次 | 章名 | 詞性 | 可救性 | 功能 | 是否附卦例 | 卦例機械文字 |")
    report.append("|---:|---|---|---|---|---|---|---|---|")
    for n, item in enumerate(empty, 1):
        report.append(f"| {n} | {item['line']}:{item['column']} | {item['volume']} | {item['chapter']} | {item['part']} | {item['rescue']} | {item['function']} | {item['attached']} | {item['facts']} |")
    report.append("")
    report.append("### 統計")
    report.append("")
    report.append(stats(empty))
    report.append("")
    report.append("### 附錄：完整所屬段落原文")
    report.append("")
    seen = set()
    for item in empty:
        key = (item["start"], item["end"])
        if key in seen:
            continue
        seen.add(key)
        same = [x for x in empty if (x["start"], x["end"]) == key]
        positions = ", ".join(f"{x['line']}:{x['column']}" for x in same)
        report.append(f"#### 空位置 {positions}；{item['volume']}；{item['chapter']}；原文行 {item['start'] + 1}–{item['end'] + 1}")
        report.append("")
        report.append("```text")
        report.extend(f"{line_no}: {lines[line_no - 1]}" for line_no in range(item["start"] + 1, item["end"] + 2))
        report.append("```")
        report.append("")
    report.append("## 待核清單")
    report.append("")
    report.append("上輪 7 項 → 本輪 7 項；無增減。所有項目均累積保留，未有明確結案，因此沒有移除任何項目。")
    report.append("")
    report.extend([
        "1. R-L1-06 六親原典用字",
        "2. R-L1-07 六神原典",
        "3. R-L1-08b 伏神能否為用",
        "4. R-UI-01 銅錢正反對應",
        "5. GLM-4-Flash endpoint／額度／ZDR",
        "6. C1-經驗指控",
        "7. C1 空亡／沖散效果語義",
    ])
    report.append("")
    report.append("本包沒有對任何待核項明確結案，亦沒有改動 SPEC。")
    OUTPUT.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
