# 标准流程补全 002

十段视频中，严格全视角 Ring-First 完成 **8/10**；全部 FIT 合格 **9/10**；正式 HERO **9/10**；PyTorch3D B1/B2 **9/10**。新增主体实例：G01/005, G02/004, G02/005, G03/005, G06/005。

G01/005 的参考图身份和原生地图坐标得到修复；G02/004 补建同视频参考库。G03/004 原失败 HOLDOUT 同参数重放仍为 3.0651759247 px，超过原 3 px 门限，预测完全保留，不能宣称因本轮得到形态改善。

G03：G03/004 原预测及失败 HOLDOUT 保持不变。 新增 G03/005 独立结果：GT MAE B0/B1/B2=1.29215/1.28866/1.30050 mm，FIT IoU=0.23761/0.24317/0.23868。这是新视频相对自身初始 Body 的配对评价，不能宣称旧 004 相机或旧缺柄问题被修复；两臂均未放宽 Sweep 生长门禁。

已修复：G01/005 图像来源与原生地图坐标、G02/004 构库，以及四段 005 的成熟原生构库入口；G02/005 再由同视频现成 FIT 补充恢复全部相机。剩余问题是 G03/004 的一个 HOLDOUT，以及 G05/005 的 Ring 标签/投影和 RGB 内点门禁，均不是“缺现成库”所致。

## 唯一标准与冻结边界

复用 G01/004 RF_ONLY_V1 的 native camera.recover、RGB yaw 消歧和来源过滤；RF_CONFIG、3px 验收、正式权重、原生 axial-Z、8 FIT 视角、支持偏移 2/4/6、EXACT013、36×3 Graph/SmoothARAP/Sweep 更新器和 HeroDepth018 参数全部相同。没有新相机算法、跨视频 BA、DXY 修改或 GT 选模。

001 的四个 004 是冻结引用，G03/004 只重放失败 HOLDOUT。新驱动的差异仅是 video 选择、实例输出路径和首次推理辅助输出保留；完整差异见 audit/driver_adapters。Body 的实际 optimizer_adapter.py 应与 001/G01 一致。

## 参考库与真实来源

G01/005：52 张历史 FIT 参考图均具实际 RGB/Mask 文件及 SHA；980 个原地标由历史明确记录的 H 逆变换恢复到原生 005 Ring 坐标。不是重新估计 H，也未认证 004/005 共同坐标。往返最大差 2.84e−14 mm，980/980 地标保留，无当前 HOLDOUT 像素混入。

G02/004：使用 7 张同视频历史 FIT 标定图，原 features019.landmarks 函数不改数值参数，得到 125 个合格地标。历史标定相机只定义参考图三角化，最终相机全部重新由 Ring-First 求解；纯 PnP 候选只保留诊断。此种历史 RGB 标定是条件标定，并非独立位姿 GT。

原先把没有现成历史参考库当作阻断是不充分的，人工指出后以 REF_BUILD_REV1 修订。四段 005 已实际调用成熟 G01 上游模块：原有 native Ring 五自由度、V6 RGB 跟踪/yaw 初始化/同视频局部标定、features019 三角化。未使用旧 PnP 相机、HERO 或 GT。全部成熟函数逐文件复制并验证原 SHA，最终相机仍执行同一 native RF_ONLY 和 3px 门限；没有跨视频 BA。详细结果见 CALIBRATION_METHODS.csv。

对于最终 FIT 相机尚不完整的实例，REF_DENSITY_REV2 一次性纳入全部现成同视频历史 FIT RGB/Mask，严格剔除当前 HOLDOUT 像素。算法、数值参数和原八个 Body FIT 不变。该补充与 G01 原库使用额外标定 FIT 的规则一致；所有 REV1 结果完整保留在 runs/REF_BUILD_REV1_RESULTS，未根据 GT/HERO 选择帧。当前确实缺失或构建失败的项目以 MISSING_ASSETS.csv 和失败台账为准，不再把“无现成库”作为最终理由。

原视频逐帧只读解码与像素 SHA 对照见 RAW_FRAME_BINDING.json。新增 G01/005 和 G02/004 的参考/目标图均找到精确原视频像素匹配。G01/004 部分历史工作图未能以本轮固定 INTER_AREA 解码获得逐字节匹配，仍只具归档图像身份，不声称重新认证其全部原始帧号；该基线未被修改。原始 ZIP 及其他资产保持只读。

| Group | Video | RGB_reference_bank | Ring_First | yaw | Ring_projection | HERO | PyTorch3D | B1 | B2 | GT_evaluation | HOLDOUT_evaluation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G01 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G01 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G02 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G02 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G03 | 004 | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | PASS | PASS | PASS | PARTIAL |
| G03 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G05 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G05 | 005 | PASS | PARTIAL | PARTIAL | PARTIAL | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |
| G06 | 004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| G06 | 005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

Ring-First PASS 要求全部冻结 FIT/HOLDOUT；FIT 完整但 HOLDOUT 失败记 PARTIAL。HERO PASS 仅覆盖冻结的 8 个 FIT 目标；HOLDOUT 不参与训练。原有参考未重训。每项 PASS 的实际路径、源码、日志见 PIPELINE_STAGE_RECORDS.csv。

## 三臂真实指标

| Group | Video | Arm | GT MAE mm | GT P95 mm | Strict IoU | Conditional IoU | FIT IoU | HOLDOUT完整IoU |
|---|---|---|---|---|---|---|---|---|
| G01 | 004 | B0 | 0.34810 | 1.08825 | 0.84972 | 0.84972 | 0.83332 | 0.82670 |
| G01 | 004 | B1 | 0.32863 | 1.08597 | 0.85858 | 0.85858 | 0.85754 | 0.83297 |
| G01 | 004 | B2 | 0.30212 | 0.95784 | 0.87126 | 0.87126 | 0.88721 | 0.86639 |
| G01 | 005 | B0 | 0.34810 | 1.08825 | 0.84977 | 0.84977 | 0.86657 | 0.87476 |
| G01 | 005 | B1 | 0.36521 | 1.13554 | 0.84161 | 0.84161 | 0.90361 | 0.90288 |
| G01 | 005 | B2 | 0.33335 | 1.12133 | 0.85857 | 0.85857 | 0.91177 | 0.90991 |
| G02 | 004 | B0 | 0.41156 | 1.65700 | NaN | 0.56671 | 0.76031 | 0.77051 |
| G02 | 004 | B1 | 0.40467 | 1.62521 | NaN | 0.56618 | 0.78609 | 0.79576 |
| G02 | 004 | B2 | 0.40518 | 1.64157 | NaN | 0.55368 | 0.79749 | 0.80805 |
| G02 | 005 | B0 | 0.41156 | 1.65700 | NaN | 0.56645 | 0.55320 | 0.54948 |
| G02 | 005 | B1 | 0.41155 | 1.65697 | NaN | 0.56655 | 0.55320 | 0.54948 |
| G02 | 005 | B2 | 0.41153 | 1.65686 | NaN | 0.56639 | 0.55320 | 0.54948 |
| G03 | 004 | B0 | 1.29215 | 8.90766 | NaN | 0.76748 | 0.85251 | NaN |
| G03 | 004 | B1 | 1.28503 | 9.06394 | NaN | 0.77374 | 0.85619 | NaN |
| G03 | 004 | B2 | 1.29215 | 8.90765 | NaN | 0.76748 | 0.85251 | NaN |
| G03 | 005 | B0 | 1.29215 | 8.90766 | NaN | 0.76702 | 0.23761 | 0.50203 |
| G03 | 005 | B1 | 1.28866 | 8.83238 | NaN | 0.76635 | 0.24317 | 0.52046 |
| G03 | 005 | B2 | 1.30050 | 9.00700 | NaN | 0.76615 | 0.23868 | 0.50572 |
| G05 | 004 | B0 | 0.65565 | 3.88565 | NaN | 0.81719 | 0.96878 | 0.95591 |
| G05 | 004 | B1 | 0.65565 | 3.88565 | NaN | 0.81719 | 0.96878 | 0.95591 |
| G05 | 004 | B2 | 0.65565 | 3.88566 | NaN | 0.81719 | 0.96878 | 0.95591 |
| G05 | 005 | B0 | NaN | NaN | NaN | NaN | NaN | NaN |
| G05 | 005 | B1 | NaN | NaN | NaN | NaN | NaN | NaN |
| G05 | 005 | B2 | NaN | NaN | NaN | NaN | NaN | NaN |
| G06 | 004 | B0 | 0.25613 | 1.22452 | NaN | 0.88150 | 0.92269 | 0.92365 |
| G06 | 004 | B1 | 0.25613 | 1.22450 | NaN | 0.88150 | 0.92269 | 0.92365 |
| G06 | 004 | B2 | 0.25613 | 1.22452 | NaN | 0.88150 | 0.92269 | 0.92365 |
| G06 | 005 | B0 | 0.25613 | 1.22452 | NaN | 0.88147 | 0.87415 | 0.86813 |
| G06 | 005 | B1 | 0.25613 | 1.22452 | NaN | 0.88147 | 0.87416 | 0.86813 |
| G06 | 005 | B2 | 0.25613 | 1.22452 | NaN | 0.88147 | 0.87416 | 0.86813 |

Strict IoU 无效保持 NaN，条件占据不冒充严格实体 IoU。GT 只在全部新预测固定终点和 SHA 冻结后读取；沿用 015 的 96 起点、尺度固定 SE(3) 及实际对齐副本。GT 对齐不回写世界坐标预测、相机或 HERO。完整 MAE/P95/最大值、覆盖率、F-score、顶点位移、深度有效分母、几何状态在逐实例 metrics 和 BODY_METRICS.csv。

## 失败、保留和解释范围

- 所有实例均走共享成熟构库和相机求解；真正未通过的 Ring/yaw/参考几何门禁停止该实例下游。初始缺库诊断和工程适配失败不被冒充科学负结果。
- G03 的 HOLDOUT 投影仍未通过，原 B1/B2 与全部失败证据保留。旧缺柄问题未因来源补全而解决。
- 原生长门禁至少要求两个视频的证据；本轮每视频独立 Body，两臂均不得擅自放宽，不能宣称新增连续柄部。
- 15 项新增契约测试曾发现实例路由适配器把原代码的两个 video 常量误计为一个；测试门禁阻断科学运行，修复记录及失败日志保留。
- 原 001 的深度改善而 GT 恶化、严格 IoU 无效及 Ring 数值容差累计漂移仍是有效负证据；没有为新病例调权重或事后修复预测。

## 固定审计表

| 审计项目 | 必须汇报 |
|---|---|
|目标组数|5 物理组、10 视频；固定 80 FIT、25 HOLDOUT|
|本算法独立成功|9/10 视频产生 B1/B2；包括明确标注的冻结同路线引用，不等于正确重建|
|本算法失败|1/10 视频无完整新路线主体输出；各臂保留 NaN|
|历史测量值回退|0；冻结同路线参考和统一 EXACT013 初始化均明确列出，非其他路线回填|
|失败组及具体原因|FAILURE_REGISTRY.json、逐阶段验收表、对应 PNG|
|最终统计样本|9 个完整 B1/B2 视频实例；始终给出总分母 10 和物理组分母 5|
|是否使用 GT 选择算法|否；预测与代码先冻结，固定 FINAL36，不以 GT/HOLDOUT 选择 checkpoint|

## 使用与交付

统一入口：`code/standard.py run --stage all`；阶段可选 audit/banks/cameras/hero/body/evaluate/report/check，参数 --group/--video/--arm。`run.py check` 核验输入和科学源码。已有冻结阶段拒绝覆盖或直接复用；更换任何输入/算法必须开新版本。

共享环境：`bash /home/liu/ring_first_3d_workspace/mainline/scripts/python.sh <入口>`；未创建环境或安装依赖。

静态图绝对目录：`/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/visualization`；索引 `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/visualization/README.md`。全部路径由交付检查器核验；没有 HTML。

## G03 的本轮独立回答

G03/004 原预测及失败 HOLDOUT 保持不变。 新增 G03/005 独立结果：GT MAE B0/B1/B2=1.29215/1.28866/1.30050 mm，FIT IoU=0.23761/0.24317/0.23868。这是新视频相对自身初始 Body 的配对评价，不能宣称旧 004 相机或旧缺柄问题被修复；两臂均未放宽 Sweep 生长门禁。

## 最终仍未通过的具体原因

参考库缺失已通过成熟构建链处理；当前失败以实际相机观测/匹配为准。CAMERA_FAILURE_DIAGNOSTICS.csv 记录各失败帧的特征、匹配和内点数；RING_COMPONENT_DIAGNOSTICS.csv 保留固定相机下的逐连通分量贡献。G05_v005_raw00404 的主环 9901 像素、113/128 观测边界点 MAE=0.72386px；离散 63 像素标签占 15/128 点，MAE=75.19221px，对原总 MAE 贡献 8.81159px。原标签全部保留，没有删分量以通过门禁。该图像证据不自动解释其他 RGB 消歧失败的物理原因。

物理组独立覆盖：5/5 至少有一段同路线 Body；视频完整 Body 覆盖 9/10。两种分母并列报告，不将物理组覆盖冒充十视频全部完成。
