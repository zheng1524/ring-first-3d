# 历史三维科研资产：冻结后增量迁移验收表

状态：**NOT_AUTHORIZED_TO_IMPORT**；只有用户对具体快照清单批准后才能开始。

旧现场：`/home/liu/polyp_research/ring_anchor_3d`（不在旧Git HEAD中）；历史点云、Hull等共39实验目录，约22GiB。旧`polyp-resarch` HEAD仅为旧宿主版本。DXY-MID在另一仓库且禁止写入。

在Git导入任何旧源码前，先审：
1. 本地源文件清单、SHA256、源路径与被哪个脚本调用；特殊导入和外部硬编码路径。
2. 哪一组结果已经真实复现、哪一组只有日志；冻结RGB/Mask/K/c2w/depth来源和mm单位。
3. 单份历史TECHNICAL_REPORT及少量关键PNG/小型GLB的目录映射与人工预览。
4. 已使用的GT模式：独立形状GT、Oracle对齐诊断、GT模板辅助；存在真实姿态未知与G04缺GT。
5. 依赖资产LOCAL_ONLY、准确哈希、建议外部存储方案；不冒充Git可复现全部22GiB。
6. 一次只迁移一个模块/一个实验的允许文件，经过git diff --cached --stat及再现验证后提交；人工确认后再冻结正式`BASELINE-3D-001` tag。
