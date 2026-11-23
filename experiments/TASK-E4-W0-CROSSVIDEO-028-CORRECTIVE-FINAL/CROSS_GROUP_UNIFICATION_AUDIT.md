# CROSS_GROUP_UNIFICATION_AUDIT

| 项 | 证据 |
|---|---|
| 同一入口 | `core/u028c.py --group <G>`；无 `if group ==` 分支（028-CORRECTIVE 的 contract 测试仍适用） |
| 同一视角选择器 | `select_views()`：Ring-valid 或 SIFT≥120 + 贪心角度覆盖；三组同一函数 |
| 同一 RingRenderer | 历史 `ring020_026`，每组 `R` 指向本组 replay |
| 同一特征/身份 | `features019.features/landmarks/matches` |
| 同一 H 初始化/BA | `ring_candidates` + `ba_core_r4`（M2/M3b） |
| 差异 | 仅输入路径、K、Ring CAD、选中视角、参考视频（G01/G03=005，G06=004） |
| 结论 | **UNIFIED_PIPELINE = PASS**（同一代码执行三组） |
