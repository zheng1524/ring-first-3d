# 失败与限制台账

| 项目 | 实际机制与处理 | 证据 |
| --- | --- | --- |
| G01新几何未通过推广 | 方向增多但新旧深度差MAE1.19mm；RGB/Mask合格不代表HERO可靠；保留18来源不改图不反选 | Figure4、HERO_PER_NATIVE_PAIR.csv |
| G03错层与片层扩大 | 新旧共同深度差MAE4.10/P9516.34mm；旧长柄可见，新层不能宣称可信侧面；相机/场景/深度原因尚不可完全区分 | Figure6、G03_Ring_Near_Local_Detail.png |
| G05弱005与照片 | 005仅2个条件相机，1张照片条件通过；新预测仍有约0.96mm差，不能直接拼接 | ALL_CAMERA_CANDIDATES.csv、Figure7 |
| G06新支持策略反例 | 同一目标/相机及共同19560观测对，几何评分三图差0.533mm，原三图0.137mm；可能共享上游RGB，不能作GT胜负 | E4_FIXED_COMMON_NATIVE_PIXEL_COMPARISON.json |
| 数值相机无解7例/弱候选 | 逐候选NaN/特征少/独立误差偏高/Ring不足，非缺失整组；全部保留 | metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv |
| 12照片未全部可用 | 数值10/12、条件4/12；照片K假设、yaw多解、观测弱。未定位不合入世界 | PHOTO_REGISTRATION_REPORT.md |
| 第一次覆盖实现失败 | selfMISS误计visible；evaluation_only旧005误入代理；E0误取重筛子集。新HERO前修复，第一轮selection/保留供诊断而非结论 | config/VISIBILITY_FIX.json、selection_verified/ |
| G01初轮遗漏005地图 | 004-only初始化漏用既有980005真实地标；单独扩充输入，同阈值/目标，旧预测不覆盖 | native005_extension.py、registration/G01/NATIVE005_EXTENSION |
| 014留出别名 | 初始新raw池未继承全部UPDATE_HOLDOUT；复核无一参与共享BA。恢复25留出；单图诊断不作独立留出pose，评估改用旧冻结相机＋共享H | provenance/PROTECTED_014_ALIAS_REPAIR.json |
| 005留出地图坐标 | 非共名005留出点需随H动，真实共名004点固定；纠正后正式成员变化0，不换位姿 | metrics/G01_HELD_MAP_GAUGE_CORRECTION.json |
| 相机对照输入口径 | 旧004-only初轮和补005地图候选不能冒充同输入对照；正式表已用补齐地图初值及各候选H重算；旧表留档不用于收益宣称 | provenance/CAMERA_EVALUATION_CORRECTION.json |
| Ceres完整目标差异 | 内层typed I/O＋RGB，V5完整Mask区域是外层接受目标；不能冒称原020所有残差都在内层。少数内层到预算NO_CONVERGENCE，不称充分收敛 | register.py、optimization/ |
| H/local规范 | 完整6D分解有冗余，靠先验；等价规范化不改预测，不能把Schur条件rank当绝对位姿认证 | EXACT_SOURCE_GAUGE_CANONICALIZATION.json |
| 预检查与事后rank | 10内点为实际前置；89/89 rank6为冻结后追溯，明确实现差异 | ACTUAL_RELEASED_CAMERA_INITIAL_RANKS.json |
| 研发运行错误 | discover语法/None帧映射、画图语法、控制点越界均有原日志；修复不改科研阈值 | runtime/logs与provenance/CONTROL_FIXTURE_INITIAL_FAILURE.json |
| 未知解剖区和未观测背面 | 不从Body猜头柄基底，不插值补洞，不输出假面积 | Figure5/6及各source UNKNOWN面 |
| 覆盖范围有限 | 完整帧清单7650，但仅884候选实际处理；没有证明两采样时间间隔内绝无遗漏方向 | RAW_VIDEO_FRAME_TIMELINE.csv |
| GT及绝对精度 | 本轮无GT，所有绝对3D精度、MAPE/尺寸真值误差NOT_EVALUABLE | 所有报告固定审计表 |

所有原始资产、旧失败记录和Body只读；没有因失败修改阈值、重复调支持图、删面美化或改相机解释新深度。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个独立物理组；8视频+12照片；7650原始视频帧，实际处理884候选 |
| 本算法独立成功 | 877/884产生数值相机（含弱/留出）；550/884条件性验证；4/4组完成新HERO；47/47真实推理+分类 |
| 本算法失败 | 7/884相机无数值（NaN）；其余弱候选和25留出不作正式目标；新增几何未达到可直接Body适配结论 |
| 历史测量值回退 | 0；新HERO推理47次均reused=false；历史相机/原生几何为明确授权的输入及对照 |
| 失败组及具体原因 | 全四组逐来源/逐相机见FAILURE_LEDGER.md与metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv；G03错层、G06支持图反例见Figure6/E4 |
| 最终统计样本 | 全体分母保留：4组、884候选、47推理；几何共同有效N和固定native-pair像素N分别列出，不能以条件MAE代替覆盖 |
| 是否使用 GT 选择算法 | 否；无GT/Oracle数据读取；各组相机和HERO计划freeze早于首次新HERO；旧相机/地图/Body的历史留出依赖不宣称独立 |
