"""Extract the three requested complete Yi Mao paragraphs for TASK_CODEX_07."""

from pathlib import Path


SOURCE = Path(r"G:\我的雲端硬碟\BOOK\八字\文王掛\07_易冒\易冒.txt")
OUTPUT = Path("corpus_extracts/TASK_CODEX_07_B.md")
RANGES = [
    (684, 685, "類總章第四十一：動變規則全段"),
    (686, 687, "類總章第四十一：飛伏全段"),
    (688, 689, "類總章第四十一：日月權能全段"),
]


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    report = [
        "# TASK_CODEX_07 B — 三段《易冒》原文",
        "",
        "來源：指定本地語料 `07_易冒/易冒.txt`，UTF-8 讀取。只取 TASK_CODEX_07 指定三段，未採集其他章。",
        "",
    ]
    for index, (start, end, title) in enumerate(RANGES, 1):
        block = lines[start - 1 : end]
        text = "".join(block)
        report.extend([
            f"## {index}. {title}",
            "",
            f"行號：{start}–{end}",
            f"字數：{len(text)}（含標點，不含換行）",
            "",
            "```text",
        ])
        report.extend(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
        report.extend(["```", ""])
    OUTPUT.write_text("\n".join(report), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
