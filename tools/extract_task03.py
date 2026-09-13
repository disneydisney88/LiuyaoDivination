"""Create the TASK_CODEX_03 B-part source extract from the local corpus.

This is a mechanical extractor: it preserves source lines and does not
interpret, rank, or apply any empty/scatter rule.
"""
from __future__ import annotations

from pathlib import Path

CORPUS = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛")
OUT = Path(__file__).resolve().parents[1] / "corpus_extracts" / "TASK_CODEX_03_B.md"


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def section(path: Path, start: int, end: int) -> tuple[str, int]:
    data = lines(path)
    selected = data[start - 1:end]
    return "\n".join(f"{i}: {data[i - 1]}" for i in range(start, end + 1)), len("".join(selected))


def matching_paragraphs(path: Path, terms: tuple[str, ...]) -> tuple[str, int]:
    data = lines(path)
    selected = [(i, value) for i, value in enumerate(data, 1) if any(term in value for term in terms)]
    return "\n".join(f"{i}: {value}" for i, value in selected), len("".join(value for _, value in selected))


def main() -> None:
    specs = [
        ("黃金策", CORPUS / "03_黃金策" / "黃金策_千金賦.txt", [(1, 80), (1380, 1400), (1720, 1781)]),
        ("增刪卜易", CORPUS / "05_增刪卜易" / "增刪卜易_完整版_A.md",
         [(1514, 1534), (1665, 1705), (1736, 1760), (1834, 1940)]),
        ("卜筮正宗", CORPUS / "04_卜筮正宗" / "卜筮正宗_完整版_A.md",
         [(184, 210), (386, 440), (2689, 2700), (2763, 2826)]),
    ]
    out: list[str] = ["# TASK_CODEX_03 — B 部分本機原文節錄", "", "只保留原文及來源定位；未作對照、評論或規則裁決。", ""]
    for book, path, ranges in specs:
        out += [f"## {book}", f"來源：`{path}`", ""]
        for start, end in ranges:
            text, count = section(path, start, end)
            pending = (book == "黃金策" and (start, end) != (1, 80)) or (book != "黃金策" and (start, end) in {(1514, 1534), (1736, 1760), (184, 210), (386, 440)})
            out += [f"### 行號 {start}–{end}；字數（不含換行）{count}"]
            if pending:
                out += ["標註：相關性待定（保留疑似材料，未作篩選）"]
            out += ["", "```text", text, "```", ""]
        if book == "黃金策":
            text, count = matching_paragraphs(path, ("空亡", "旬空", "沖散", "冲散", "沖空", "冲空", "日傷爻", "爻傷日"))
            out += [f"### 全檔相關段落；字數（不含換行）{count}", "", "```text", text, "```", ""]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
