# Ring+SIFT / SIFT-only 对照协议 v1（运行前冻结）

任务授权：人工附件 TASK_RING_SIFT_VS_SIFT_COMPARISON_001.txt，2026-11-26。基于 115e41fe5e57deff2898258d2ee836c83d686982；任务 A 与 HIST 输入只读。无 GT：本任务只比较覆盖、观测解释和一致性，不评价绝对精度。全协议适用 5 物理组/10 视频；本次固定两个独立物理组各一视频：GP_Ip_12.0mm_closed_R10_single_refY_005、GP_Ip_20.0mm_closed_R10_single_refY_004。

## 组成清单（先于实现）

| 能力 | 既有实现/入口 | 输入→输出 | 处置/验证 |
|---|---|---|---|
| RAW/INIT/SIFT | v6_raw/route.prepare；V6 track005.main；已完成 HIST 快照 | RAW→22帧原Mask、tracks005/pairs005 | REUSE 哈希核验，不重复分割 |
| Ring候选 | M2F10 build_ring，HIST ring_candidates005 与观测 | 真实Ring→候选 | REUSE 完成快照及内核锁 |
| R 相机 | route.legacy/bind；M2F10 invoke_adapted_v6；local_ring_sfm.main | 共同训练匹配+Ring候选→两初始化BA | ADAPT 仅任务目录重绑定；首成功版本；重跑 |
| S 相机 | pycolmap 4.2.1 数据库、estimate_calibrated_two_view_geometry、incremental_mapping | 同训练点/原匹配边→独立SfM | ADAPT 数据库格式/原frame与track ID映射，冻结K |
| 预测检验 | V6 v6_common.triangle / project | 支持观测→query投影 | ADAPT 新任务评价与固定支持清单，避免query拟合 |
| HERO | M2F10 adapt_supported_hero_schedule；V6 run_mvs005_supported.main | 冻结同四帧/权重→原生深度 | REUSE 入口；共享GPU锁；最多8次 |
| 原始曲面 | V6 v6_common.depth_mesh | 原深度+原Mask→Mesh | REUSE 既有0.75单位邻域跳变建面定义，无新增clean |
| 对比报告 | 既有深度诊断概念、matplotlib | 共区域指标/真实数据→小表/中文图 | ADAPT 任务专属统计与可视化，新增评价获附件授权 |

registry/routes.yaml 存在，但未登记新版 HIST；以附件指定提交与 KERNEL_LOCK 作为本次复用依据，不修改主线。没有新SfM或HERO实现。

## 共同输入与划分

沿用快照 tracks005.npz 中保存的 SIFT 轨迹坐标与 pairs005.npz 中原始匹配边；不重提特征，不补全隐含track clique。训练轨迹为原 held=False；原 held=True 按轨迹ID // 5 偶数→validation、奇数→test。这保留 HIST 训练输入，允许隔离测试读取；旧 held 曾用于历史门控，因此本次 test 是 B 内隔离的留出轨迹测试，**不是历史上完全未消费的盲测**。不得声称整张图像独立留出。两臂同一训练集合，内部鲁棒筛选允许不同并记录。

全部测试query按每条轨迹的每个可见帧枚举；支持为其余可见帧按索引均匀选最多3个（至少2）。在相机运行前固定，不因缺相机而换支持。仅支持用于三角化；query坐标只用于最终误差。validation同规则；test不能参与门控、Support选择、初始化选择或参数选择。分类沿用原INIT轨迹背景0/息肉1。

两段各2 Target：只按训练轨迹共视图选总共视最多的Target（索引破同分）；其3 Support按共视数降序/索引排序，每边至少15；第二Target需与第一有至少15条共同训练轨迹，并优先第一个组合中的帧。所有选择在求解前落盘。两臂共用组合，失败保留，不按相机或深度换组合。

## 软件与接口

使用历史 Python 3.12.13 环境；pycolmap 4.2.1，固定随机种子20261126、CPU两线程。COLMAP PINHOLE共享相机，(fx,fy,cx,cy)=(490,490,320,180)，输入原OpenCV轨迹加(0.5,0.5)；导出还原K=(490,490,319.5,179.5)。所有BA和绝对位姿的焦距/主点/额外参数优化关闭。使用既有训练匹配做官方二视图验证，记录 matches 与 two_view_geometries 数量。数据库特征ID是原track身份的单帧重编号，另存映射；描述子不再需要，禁止重新匹配。

S采用官方默认增量策略（最小模型10；初始化100内点、16度；官方自带自动初始化放宽保留），禁止读R位姿或Ring几何。多分量均保留，覆盖用注册集合并集，连通规模分别列；配对HERO仅最大分量（相同规模按模型ID），不拼不同尺度分量。相机导出明确 cam_from_world 为w2c，逆矩阵为c2w；检查SO(3)、正深度和K不变。

依据：[数据库](https://colmap.github.io/database.html)、[FAQ](https://colmap.github.io/faq.html)、[教程](https://colmap.github.io/tutorial.html)。

## 指标与分母

- 恢复：全22帧数值相机/注册并集、各连通分量大小；共同RGB检查只使用validation：至少8可预测query、MAE≤3px、P95≤6px、固定query总数中正深度可预测比例≥0.95。不以Ring门槛淘汰S。列全体、两臂交集、R-only、S-only。列全训练图可组成3 Support的Target及固定2组合的四相机完整性。生产HIST Q0/Q1单列为历史诊断。
- 留出：按息肉/背景及共同可预测query分别统计残差median/P95(px)、可预测数/固定query总数、≤3px成功数/固定query总数。缺支持/缺query相机、三角化退化、负深度均保留原因；无预测为NOT_EVALUABLE而非删除。
- 稳定性：预算内不安排训练扰动重跑；明确 NOT_EXECUTED。HIST两初始化分歧仅诊断，不能替代两臂配对扰动。
- 尺度：S求解后，利用两臂同ID训练3D点一次全视频正尺度、无反射最小二乘Sim(3)对齐；至少6点，秩不足2拒绝。保留S原任意尺度与R原毫米。变换作用于所有S相机/点，HERO前冻结；单位称“R尺度归一单位（R中1单位=1mm）”，不是S独立公制恢复，也不把R当GT。无可靠共点则HERO标NOT_EVALUABLE。
- HERO：四个组合每臂最多一次，总≤8。原352×640/3 Support/refine1/FP16/fastFalse/权重00878bab…，无clean。每视频两Target的两个方向：源深度正向投影到目标，z-buffer取最近层；目标原INIT息肉Mask及有限正深度限定支持。报告两臂共同像素交集上的有向绝对深度差median/P95（归一单位），同时报告各自/共同有效像素、全目标息肉像素分母；深度明显位于目标表面之后的点按固定 max(0.5单位,1%目标深度) 标为可能遮挡，分开列全部投影交集及双方非遮挡交集，不能只报告剔除后的值。无GT遮挡无法完全判定，不能将排除误差当改善。深度指标不回馈任何选择或删面。

## 资源与交付

输出 runs/ring_sift_comparison_001；源码/报告在独立分支。GPU非阻塞获取 /home/liu/ring_first_3d_workspace/runs/shared_gpu.lock，获取后再检查GPU进程；A优先，忙则登记NOT_EXECUTED_GPU_BUSY，不抢占。原始深度/Mesh本地完整保留；Git只提交源码、配置、CSV、相机小证据与中文对照页。实际完成/失败/未执行分别登记，不外推两视频为全数据结论。
