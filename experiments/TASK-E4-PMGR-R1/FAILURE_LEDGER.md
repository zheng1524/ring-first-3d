# 失败记录（保留负结果，不回写历史）

| ID | 环节 | 事实、原因与证据 | 处理及状态 |
|---|---|---|---|
| R1-01 | 历史P0 | G01/E2实体交集3.896047 mm³，Open3D最小顶点签距−0.460934 mm | 新P0最终间隙0.082401 mm；旧网格未改。[独立Blender](metrics/G01_004_HISTORICAL_P0_BLENDER.json) |
| R1-02 | 正式P1 | 10候选9拒绝；全部`VIEW_CONTOUR_REGRESSION`，相对新P0单源+0.5px保护触发 | GLOBAL_STOP，无参数搜索/门槛修改；接受1个0.007735mm微动。[完整提案](metrics/ALL_UPDATE_PROPOSALS.json) |
| R1-03 | G01/P2与G06 | 用户要求多数拒绝即停止；不能继续扩展 | P2、G06=NOT_RUN/NaN，不计科学成功。[CASE_RESULTS](metrics/CASE_RESULTS.json) |
| R1-04 | 指标连续性 | r06最后小提案动态轮廓+0.51360px，而固定对应−0.02586px、像素轮廓−0.01437px；110→112个样本 | 只读诊断，拒绝判定不改；未修补再试。[逐源诊断](metrics/PER_VIEW_REJECTION_ANALYSIS.csv) |
| R1-05 | Ring轮廓语义 | 观测剔除Ring邻接带、预测仅剔除Ring自身，存在不对称；r10带内19/115点占前向距离和57.4% | 实现缺陷保留，不能当真实解剖冲突。[诊断](metrics/RING_CONTOUR_ASYMMETRY_DIAGNOSTIC.json) |
| R1-06 | P0审计文件 | 可行性JSON被阶段P0同名输出覆盖；中间求解轨迹丢失 | 不补跑、不猜迭代数；端点门槛只读重算另存RECONSTRUCTED。停止后仅修输出文件名。[记录](metrics/POST_STOP_OUTPUT_FIX.json) |
| R1-07 | 相机与评价 | G01严格相机资格全部证据不足；原B转训练，没有独立留出 | 保留条件性身份，不称相机认证或几何真实成功。[资格表](metrics/VIEW_QUALIFICATION.csv) |
| R1-08 | 开发预检 | 初版float32射线量化与已知轮廓点的可见性判定引起梯度差异；早期验证失败，另有缺失导入 | 正式冻结前修复：float64交点/最近点、无更近遮挡判定；最终8项PASS。原差异数据仍留[PRE_FIX](metrics/FP32_RAY_FD_PRE_FIX_DIAGNOSTICS.json)，不能将局部PASS外推到显隐切换 |

本轮不判定真实物理几何路线失败。当前明确未通过的是“大幅、可靠、可接受的渐进更新机制”。历史实验、相机、CAD、Mask、HERO、清理记录和DXY均保留原样。
