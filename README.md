# LiuyaoDivination

Local Streamlit calculation paper for deterministic Liuyao charting and
source-preserving multi-track display. Start it locally with:

```text
streamlit run app.py
```

Cases are stored only in `records/cases.jsonl`; the runtime records directory
and Streamlit secrets are ignored by git. No LLM or cloud storage is used in
this package.

The published 64-line golden reference was not supplied with the specification;
the corresponding test therefore verifies algorithmic completeness and reports
that an external human comparison is still pending.

## Data layers

`mechanical/` 內之資料由算法生成，可對已出版對照表驗證，無學派爭議。
`doctrinal/` 內之資料為各家之說，帶出處與軌別標記，彼此可能矛盾。引擎不得將 `doctrinal/` 內容視為事實，只可視為某一出處之主張。

## 語料來源限制

全庫八本目前無任何一本可作影像級核對。現有 sidecar、revision_id、缺字記錄及字元級完整性核驗，只能追溯電子文本之間的關係，不能核對電子文本與紙本／影像底本。若上游電子文本錄錯，本系統無從察覺；所有文獻 claim 的準確性上限，亦即上游電子文本的準確性。
