# SPLIT_AND_LEAKAGE_AUDIT

| 项 | 状态 |
|---|---|
| 划分时机 | 特征提取**之前**写盘（`SPLIT.json`） |
| 004 | FIT 3（key02_raw00327, v004_raw00242, v004_raw00283） / HOLDOUT 3（v004_raw00263, v004_raw00304, v004_raw00202） |
| 005 | FIT 8（偶数位） / HOLDOUT 8（奇数位） |
| 020 身份链 | 仅 FIT 视角进入 `VIEWS`；HOLDOUT 不参与 votes/PnP/one-to-one |
| 断言 | `TestSplitIsolation`：身份证据视角 ∩ HOLDOUT = ∅（004、005 各一） |
| HOLDOUT 评价 | 独立描述子匹配 + 仅用已冻结的 H；不参与 H 选择 |
| 已知限制 | 时间簇切分未做（相邻帧可能跨 FIT/HOLDOUT）；地标三角化只用 FIT，已避免 023 的错误 |
