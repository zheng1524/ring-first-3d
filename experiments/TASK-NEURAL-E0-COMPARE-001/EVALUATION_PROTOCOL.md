# E0 评价协议｜PRE-REGISTERED DRAFT

状态 `PROPOSED`。P0 仅冻结协议，**本轮不计算新模型指标**。

1. **样本计数**：每行绑定 `physical_scene_id/video_id/frame_SHA/method/arm/config_sha/pose_status/HERO_origin/GT_mode/holdout_tier`。组层 4 物理组，视频层 5；G01 004+005 统计为 1 组。G01/G06 `NORMAL_CONDITIONAL` 仍须重新核定严格留出；G08 `LIMITED`、G07 `UNQUALIFIED_STRESS` 分表。
2. **分区**：模型推理/优化视角固定在测试目标之外；采用 `HOLDOUT_STRICT`（不在任何已知 HERO 多视图输入、P0、模型拟合/调参中）、`HOLDOUT_RECON_ONLY`（仅新算法未用但历史 HERO 依赖可能）、`DIAGNOSTIC_ONLY`（相机/身份不合格）。不允许混合分区后报单一“独立测试”。
3. **基线**：每场景 Raw、单参考、Historical Cleaned F1、Historical F2、All-available Cleaned F1、F3 PreJoint 与 F3 Joint。不同历史算法源帧数不同须另列 `same_input` 与 `all_available`，不能将数据增益归算法增益。
4. **共同像素**：B 真实 Mask 像素为目标完整分母；方法 X 的有效可见预测集合 (P_X)。比较 X/Y 的 RGB 误差只在 (P_X\cap P_Y\cap Mask_B) 共用像素统计，并同时报告 `|P_X|/|Mask_B|`, `|P_Y|/|Mask_B|`, `|P_X∩P_Y∩Mask_B|`、未知/遮挡/外逸。不同支持集各自 MAE 不用于胜负判定。
5. **几何**：对统一源 XYZ 审计固定 CAD 内点数/最大穿插深度、表面重复层（重叠 + 方向）、表面原面覆盖、实际多视角 Mask 轮廓、source support 与 prior-only 分别的面积代理。支持域外 SDF 闭合面不用于“可见面增益”；Map `conf` 非独立真实误差概率。
6. **不确定性**：按同一个预定义 Mask/pose/depth/occlusion 质量代理分层，对每层保留有效帧数、面积/像素分母和冲突；不可通过训练把困难层全部降低权重。
7. **绝对真值**：不存在独立部署变换时，3D 点到真实 GT 的 mm MAE/体积/背面/基底写 `NOT_EVALUABLE`，禁止以 GT 对齐结果冒充自主几何；已冻结 GT 形状标量可作为另列后验诊断但不得参与方案选择。
8. **成本/可重复**：模型权重及代码 SHA、GPU/峰显存、推理与优化总时间、依赖/下载、手动步骤、失败计数、随机种子及 smoke 是否可复现；按 P1/P2/P3 实际授权预算列。

结果矩阵每场景至少 M0–M3（不合法为 `NOT_EVALUABLE`）、S0及后续 S1（仅授权才运行）、Raw/Cleaned/F2/F3；可评价单元都要附 `n_frames`, `n_pixels`, `observed_support_fraction`, `camera_quality`, `GT_mode`, `runtime_status`。图采用固定 mm 轴六视角和严格 A→B（真实B / 预测 / 叠加 / 差异 / 未知 / 遮挡），Ring 用独立黑色 CAD。
