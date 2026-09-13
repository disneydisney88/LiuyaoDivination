# TASK_CODEX_20 修復重跑差異

比較基準：`fbef8c9` 所提交之 `13eb522` 現況 golden snapshot。原 golden 檔頭保留 `13eb522（125 tests）` 及七項問題逐項狀態；本報告只記錄修復後差異，不把舊 golden 改寫成未發生過的狀態。

## 第一優先：L1

重跑檔：`postfix_tier1_L1.csv`。

- 組合數：4,096；例外：0。
- 修復前失敗：4,088；修復後失敗：0；修復後正常：4,096。
- 卦名缺字／只得上下卦象：修復前 3,584 組，修復後 0 組。
- 變卦六爻缺失：修復前 4,032 組，修復後 0 組。
- 兩者重疊：3,528 組（修復前分類；係同時含兩個 failure flag 的組合）。
- 4,088 行有狀態差異；其中 `hexagram_name` 變更 3,584 行、`changed_lines_complete` 變更 4,032 行、`failed_checks`／`result_class` 變更 4,088 行。

L1 變更包括：用 canonical upper/lower trigram name vocabulary 生成完整 64 卦名；`build_case_state()` 對動爻生成完整 `changed_chart`，六爻均保留地支、五行、六親。

## 第二優先：L3 用神

重跑檔：`postfix_tier3_yongshen.csv`。

- 組合數：1,728；例外：0。
- 修復前：1,728 組 `check_failed`；其中 216 行有 `equal_to_choices`。
- 修復後：1,728 組正常；`equal_to_choices` 為 0 行。
- 1,728 行輸出均有 `is_yongshen`（可見爻或伏神候選）、元神／忌神／仇神位置欄及明確 C1／C15 格位或「此爻不觸發 C1／C15 任何條件」狀態。
- 修復後仍保留 `R-L2-07` 六項條件逐項狀態；尚未能由現有資料機械判定的項目標為 `not_computable`，沒有被填成效果語義。

兩輪 Tier 3 對 golden 的差異：1,728 行均有輸出差異；`is_yongshen_positions`、元神／忌神／仇神位置、輸出簽名、輸出本體及 failure class 均更新。C1 自動格位更新 42 行，C15 更新 48 行。

## 測試

L1 新增名稱完整性及動爻變卦完整性測試；L3 新增六個用神輸出差異、妻財之元神／忌神／仇神位置、用神 marker、候選完整性測試。修復後會先比較舊 golden，再於新 code baseline 產生更新 golden；舊 golden 的差異保留於本檔供人工判斷「修復或回歸」。
