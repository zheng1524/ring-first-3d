# PIPELINE_ERROR_AUDIT

| 环节 | 问题 | 修复 | 证据 |
|---|---|---|---|
| 数据入口 | `adm.get(i,'ACCEPT')` 缺字段默认通过；适配器硬编码 G03 | `w0_adapter.load_views(group, video)` fail-closed | `test_data_contract.py` 4/4 |
| SIFT | 协议 6000/.01，代码 4000 | 对齐 | G03 FIT 匹配 2003 条（旧 482 条） |
| 切分 | 先全量优化再做留出 | 优化前冻结 `SPLIT.json` | FIT 2003 / HOLDOUT 1746，只评价一次 |
| 状态 | 单一 `RUN_STATE.json` 被最后一组覆盖 | `audit/<G>/RUN_STATE.json` 原子写 | 三组各自独立 |
| 复现 | 旧的 fixtures 是 4000 特征时期的 | 运行期导出 `runs/G03/MATCHES.npz` | 离线复现 fit 4.63696 / holdout 4.53832 与在线一致 |
