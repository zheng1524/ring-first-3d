# TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002（修订TRUSTED-only批次）

用户授权：附件PM_TASK.txt，由用户明确要求执行。基础提交2d34cc866cd175d4d770a3e09d07b31a5c3662d7，独立稀疏工作树TASK-V6-REG-CLEAN-002；虚拟001的537c2070只读。未发现旧002分支，本批次R002_001。先协议再直接执行，不等待上游。

## 组合表（先于科学代码）
|阶段|复用|适配|状态|
|---|---|---|---|
|全量身份|执行快照da92d8…FULL_RUN.json、manifest/state/完成收据|只读解析；不调用full_run/route运行函数|REUSE|
|虚拟观测/评价域|虚拟001 public/private/轨迹/原独立mesh|读取原数据；V3仅新Ring参数观测|REUSE/ADAPT|
|原M2|001 registration.solve函数AST|仅R5/R10物理半径配置|REUSE|
|M3/M4|原RGB残差、yaw-grid、SE3、SciPy|用户指定硬5DoF Ring及独立二次Ring损失|AUTHORIZED NEW COMPOSITION|
|自动轨迹/DLT|原V6 track005.main、v6_common.triangle|固定各视频6帧全对，跨完整连通轨迹mod5留出|ADAPT|
|Clean映射|surface_clean.mapped_input_for_source|绑定原depth_mesh函数，跳过route.legacy/environment/调度；原映射代码不变|ADAPT|
|Clean分类与子集|classify_native + 017/gap；trusted_subset|临时独立输出，持久化state/reason/原面ID/uv；原资产不变|REUSE|
|支持筛选|原F和working_uv|二维三角包含、固定首个观测，不读T或深度替换DLT|NEW boundary adapter|
|图与评价|原投影、真实三角截面、CPU光线投射|中文HTML，固定Raw+CAD范围；相同T的Raw/Clean|ADAPT|

## 资源契约
单进程，CPU affinity固定一个允许核心；nice19、ionice idle；OMP/OpenBLAS/MKL/NUMEXPR/VECLIB/BLIS线程1，OpenCV1，Open3D场景/查询显式1；CUDA不可见。无上游状态/锁/日志写入，无模型调用。磁盘保留3GiB（含全量最低1.5GiB及余下约20视频保守增量），本任务总运行/证据上限256MiB，源码稀疏工作树约41MiB另计。每源处理前检查资源，不足则记RESOURCE_DEFERRED并让出，不碰全量。新clean分类临时输出只在本任务scratch；保存必要小证据后清理自己的临时多套导出。

## 配准前固定选择/预算
状态与manifest一致且DONE/native_success>0/renderable>0；完整case排序选A/B前两段。逐步选5组：优先最大化新增形态数+新增Ring规格数，再新增尺寸，再已有4-source clean可复用，再group字典序；同组不因效果替换。Is无合格组如实报告。每视频帧池按ledger时间顺序等间隔6帧；全对匹配，6000 SIFT、ratio .72，原并查集整轨迹mod5留出；保留原BA held标签作依赖标记。全部已完成Raw source/tag进入固定几何对照与clean表，不能只报四个已有来源。

每侧DLT≥2观测、正深度、视差≥0.5°、训练最大重投影≤6px；FIT≥6轨迹。HOLDOUT不作上述误差筛选，源侧≥2有限观测可DLT；全量留出分母保留负深度/出界/不可三角化。不据留出选初始化/分支/参数。主留出证据≥8独立双视频轨迹、每侧≥2帧，否则INSUFFICIENT。

M0恒等；M1中心/法向，yaw未知；M2原001。M3在M1上只估yaw。M4保持sigmaRGB=.2mm、每坐标soft_l1、1/N在损失外；Ring的5维中心+法向切平面角差独立二次损失lambda1，不被soft_l1削弱。精确Ring显式退化M3。72 yaw格，初始化只FIT，最多100函数评价。

真实Sigma：仅帧池FIT Ring候选，按与冻结相机所隐含CAD方向一致的FIT候选分支选择（正负按+法向规范，训练loss作次级）；候选中心/法向转换到单视频坐标。使用两侧帧间样本均值协方差及预定最多3个等时序留一帧均值变化，合并两侧；加每侧0.1mm/0.3°系统不确定度底座（不是系统误差已消除）。若任侧少于3帧可用、最大中心sigma>2mm或法向sigma>15°记INCONCLUSIVE_RING。保护界限=同Sigma的Mahalanobis半径5，越界CONFLICT，不放宽。不重做Ring拟合或BA；真实Ring名义CAD原点为0不意味着A零误差。

受控V0/V1/V2复用原7条件（回归集）；精确Ring的M4=M3。V3五次独立流（seed基础+900000）只扰005 Ring：每轴0.1mm、rotvec每轴0.3°；预测只知道噪声分布，实际值/逆矩阵留评价。V2/V3共用同批相机和网格。评价额外固定真D^-1参考，不称下界。0.5°/0.2mm不变。

Raw/Clean支持规则：仅息肉FIT轨迹；各侧按真实帧ID顺序取首个Raw映射中原F二维包含成功且无边界状态冲突的观测（选择先不读state；发生冲突标UNKNOWN不改选）；同Target取计划次序首源。raw_support两侧有原面；clean_support两侧该面state0。背景/Ring不动，保留点的DLT坐标完全相同。无Target/边界冲突UNKNOWN，不扩邻域。其他观测支持数量另列。两支用相同Ring先验、完整未筛留出与原优化配置。没有整帧HOLDOUT。

固定留一帧敏感性：每侧按池首/中/末共6次，仅从FIT观测中去一帧重算DLT及M4；不读留出、不更改正式T。统计存活与T离散，不用敏感性选择正式解。

## 执行清单
- [x] 只读选组、选中输入前后哈希、来源与资源预算。
- [x] 单元验证：M4目标/精确Ring退化、双向投影、支持面边界、TRUSTED语义。
- [x] 冻结执行源码和外核SHA；受控12条件M0—M4及真D^-1参考实际运行。
- [x] 逐组固定自动RGB/DLT、Ring先验、逐源Clean复用/补齐，冻结后求M0—M4和两支持分支。
- [x] 双向完整留出、固定CAD Ring、FIT留一敏感性、同T Raw/Clean几何及2×2对照。
- [x] 中文HTML及逐组PNG，失败页不省略；代码审查、验证、独立分支push和SHA核验。
