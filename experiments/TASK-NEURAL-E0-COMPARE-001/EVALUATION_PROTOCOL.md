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

## 本次实际执行补充（2026-10-30）

本次直接用户授权覆盖较早P0-only描述，见 `AUTHORIZATION_OVERRIDE.md`、`USER_STEERING.md`。G01_005固定训练/推理参考为raw00057、raw00459；P0源身份审计读取过目标00860/00611文件（SHA/尺寸、RGB解码），不作误差评价或拟合；其RGB/Mask评价只在所有模型输出冻结后开始。两目标均为HOLDOUT_RECON_ONLY，非全流程盲测。未改相机、选帧或权重来追随目标误差。

实际主表采用视角评价任务原封AST `reprojection.py:render/evaluate` 的**原三角面射线**协议；所有方法640×360同目标，源RGB重心插值，固定CAD遮挡容差0.05mm。与历史点中心覆盖明确分开，不把旧报告数值并入本表。CAD实体穿插用0.02mm容差。B Mask完整像素为覆盖分母；共同RGB仅在双方实际支持交集中计算；空集保留NaN。边界F1为2px，IoU保留外逸支持。

M0–M3各执行相同2视角，官方预处理固定280×154、patch14，Mask用同一K导出的仿射变换最近邻映射，只限制源输出Polyp域，不作为额外官方网络输入。SDF显式使用Mask损失和固定[0.25,1]深度代理权，绝对HERO Z替换MonoSDF默认scale/shift损失；两个臂Mask使用方式不同，不能称所有监督完全相同。历史F1/F2用14参考注册表相应视频子集，F3/AllAvailable用36参考子集；另列相同2输入Raw/Cleaned。

公制坐标以米送模型，输出乘1000；Map只以第一冻结相机与第一输出相机作刚体规范转换，不作尺度拟合/ICP。M0/M1的此转换仅用于评价定位，不给网络pose/depth。M2/M3的pose是冻结条件输入，网络仍会预测pose，不能说输出pose被硬锁死。公开原输出与转换矩阵。

SDF在模型输出冻结后发现输入域错误：相机在默认吸收边界球外；0观测支持面，不把灰色零水平集纳入可见面指标。Map四配置有数值输出，完整几何正确性未认证。不存在有效双臂科学对照；不选赢家。G01_004仅历史基线重投影，所有新模型NOT_RUN；其他三组只做资格审计。

不可变模型冻结：`ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION.json`（2026-10-30 15:47:11 Asia/Shanghai）。最终A→B缓存清单来自CPU重绘，已注明晚于首轮评价；重绘只改布局、未改模型预测。绝对Polyp三维/体积/测量误差及中位绝对相对误差、MAE、p95、最大误差全部NaN/NOT_EVALUABLE，无GT部署变换，不用RGB误差替代。
