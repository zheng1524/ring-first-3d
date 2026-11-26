# 历史 TRUSTED-only 恢复执行清单

本轮用户附件已批准历史分类、冻结gap补充和state==0导出，3–4个新来源；不增加审批环节。

| 阶段 | 既有函数/版本 | 输入→输出 | 处置与核验 |
|---|---|---|---|
| 历史方法 | 018 clean018@62c286fc、017 analyze/gap及冻结PROTOCOL | 历史源码/配置→方法和函数身份表 | REUSE；AST及参数核对，不执行Body/OBS |
| 当前进度 | 全量manifest、states、tuple账本、completion、日志 | 当前状态→北京时间进度表 | ADAPT仅只读快照；失败原因和固定分母 |
| 输入映射 | v6_raw.surface_clean.run_one输入段/native_mapping@3b7b767a | 当前Raw/原生深度及相机→mapped_input | ADAPT提取共享函数，分辨率由实际资产读取；验证原F及float32 V |
| 分类和gap | native.cleaning.classify_native + _clean_kernels + cleaning_protocol | 新mapped_input→新FACE_EVIDENCE四态 | REUSE不改分类算法/参数；禁止C1与旧标签 |
| 可信子集 | 018 trust=state==0 | 全Raw原面+四态→原面子集/排除集/ID | ADAPT工程导出；全原坐标保持，无OBS额外资格 |
| 统计与展示 | 既有topology/actual_mesh_image | 每源Raw/四态/可信子集→一张三列图与面积/连通统计 | ADAPT；最多2视角，同Raw范围，孤立无引用顶点不计分量 |

- [ ] 读历史链、锁定配置，记录方法表。
- [ ] 当前进度只读快照；观察已完成新Raw，冻结4来源及全部资产哈希。
- [ ] 提取已有输入适配，不复制分类器；验证映射与原面身份。
- [ ] 低并发CPU运行历史分类+gap+TRUSTED-only；保存四态、子集、排除面和映射。
- [ ] 每源一图并逐源判断残留/边界损失；记录四态面数/面积、主要连通分量。
- [ ] 独立检查、推送、中文报告和本地URL；不修改或重启后台全量任务。

已有总任务代码与输出目录均只读。新数据：runs/v6_trusted_clean_restore_001。本轮仅用CPU、单来源顺序处理，OMP/BLAS线程1；不申请GPU。全量任务继续按自己的不可变快照执行。
