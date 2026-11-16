# 失败、暂停与不建议重复的尝试

“暂停整条路线”与“某目标失败”不同；失败不删除代码/指标/NaN。工程状态与科研状态仍分别按[实验索引](EXPERIMENT_INDEX.csv)与[模块卡](REUSABLE_MODULES.md)读取。下面每行链接原报告，原报告给出固定分母、逐源原因、失败台账和可视化；没有用新实验覆盖历史结论。

| 路线 | 实际执行/分母 | 失败步骤与具体原因 | 可复用组件 / 不建议重复 | 原始证据 |
| --- | --- | --- | --- | --- |
| TSDF | G01/6源；SINGLE/G0/G1真实运行 | 单位gate .0020026695>.002；ref08首层一致50.22→27.98；CORE面积改善不抵消错层 | T39单位/轴向Z适配诊断可借鉴；不要称已冻结通过的adapter | [报告](../../experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/TECHNICAL_REPORT.md) |
| NeuralFusion | G01八参考/G06五参考；26前缀+reverse | 官方全链已跑；G01ref08一致73.52→.47%，多层6.44→66.43%；预处理也有孔洞损失 | T40官方接线/仪表可复用；不再以接线首跑为新结果 | [报告](../../experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/TECHNICAL_REPORT.md) |
| MonoSDF充分训练 | 目标3组；实际G01 4000步；4090新增0 | G06/G08 NOT_RUN；200k未完成；层数代理变坏；未完成充分科学评价 | T41数据/官方适配可追溯；不重述为完整训练失败 | [报告](../../experiments/TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001/TECHNICAL_REPORT.md) |
| 固定主面跨视频 | G01两视频6参考；D2执行0/1 | 5/5 GICP越Ring界；PnP备用条件性；NOT_FUSED；来源冲突及碎片仍在 | 原面来源/补片/失败显示可借鉴；叠加不是融合PASS | [报告](../../experiments/TASK-PHASED-MAIN-SURFACE-CROSSVIDEO-001/TECHNICAL_REPORT.md) |
| 四组增量补片 | 4物理组5场景9参考；仅G01多参考 | 剩余9823删除候选仍损细柄；最终全Raw；高度10/27数值；3D Dxy均NE | 保留拒绝清理记录，不把3单参考组称融合成功 | [报告](../../experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/TECHNICAL_REPORT.md) |
| 历史置信融合/拓扑 | 8物理组9视频；过滤54条件 | SOR/ROR/P4损好面；C非流形586/1993，拓扑修复碎片231/1159；B3/BPA NOT_RUN | GT ICP只Oracle；拓扑切分不修深度；不得捏造已实现固定主面优化融合器 | [报告](https://github.com/zheng1524/ring-first-3d/blob/7c961d994833a960917f9c36928559e85eb389ac/experiments/TASK-HISTORY-ASSET-AUDIT-002/TECHNICAL_REPORT.md) |
| 旧Body-E与重定位 | 4组75源×2Body=150；条件通过34 | E21/75 U13/75非全验收；旧DT/AMS不是A1原样loss；逐源H不保证视频轨迹 | T42标REIMPLEMENTED并停止推荐；保形核验可借鉴 | [报告](../../experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/TECHNICAL_REPORT.md) |
| E1/E2初始化 | 主4组，各4/4数值；各0/4验收 | 2/36未收敛；多初值/留出轮廓/Ring穿透；无GT、无A2等后续 | 复用解析数学与solver，不用历史Body或毫米测量补失败 | [报告](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/TECHNICAL_REPORT.md) |
| 原始RingAware soft-zbuf | 1真实+1虚拟case | 初始梯度1e8–1e13而FD1e−4；已修离散可见性次序 | 使用014或VISIBILITY_ORDER_REPAIR；不要加载旧根版本 | [报告](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/TECHNICAL_REPORT.md) |
| 010基底优化 | 9cases18条件 | 仅8/18完成300步，10停止 | 保留停止证据，不能称全部完整优化 | [报告](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BODY_BASE_PYTORCH3D_010/TECHNICAL_REPORT.md) |
| 011接触/回滚 | 9cases2700提案448接受 | 7/9heldIoU↑但G09 .929→.837，G02depth .014→.077，G01coverage .945→.915；replay154/155 | T25/T26为候选；G02 replay差1.64844e−6超1e−7 | [报告](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/TECHNICAL_REPORT.md) |
| 012/013自由顶点 | 013共11cases；6/11完成300accepted | G03短突起不是真柄；旧guard漏独立denseRing；012同样柄不完整 | T27参数化可用；显式闭合/柄部不得冒充可观察 | [报告](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/TECHNICAL_REPORT.md) |
| 014/015/016更新 | 014共11物理组；015/016各11 | 014仅4/11Chamfer↑，1/11denseRing非劣失败；015 B/C各4/11新Ring标志；016未解G03 sheet | T24/T27–34工程可复用；改进不全面，GT只后评价 | [报告](../../experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md) |
| 017清理候选 | 4组18源两表示 | 最终0删面；PCA/边缘/双侧gap不能稳定判错；TRUSTED可解释错平面 | T21/T22证据提取；不默认删面，不混FaceID | [报告](../../experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/TECHNICAL_REPORT.md) |
| 018原生深度更新 | 4组43来源；29FIT14held | G03缺5387命中、4789nearest落背面、新命中误差7.2mm；无miss梯度 | T30首次命中/barycentric轴向Z可复用，miss固定代价不创造梯度 | [报告](../../experiments/TASK-E4-HERO-BODY-ADAPT-018/TECHNICAL_REPORT.md) |
| 019/020/021跨视频 | 019/020 G01；021 G01 BA+4组审计 | 019劣于RoMa heldIoU；020 IoU↑而HERO支持↓；021 FIT↓但heldIoU与支持均↓ | 共同地标全背景；Schur rank6/condition497不证明绝对正确 | [报告](../../experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/TECHNICAL_REPORT.md) |
| MAX覆盖/HERO | 4组884候选；47次实际HERO | 7相机NaN；550条件可用非全部认证；G06新proxy误差.533>旧.137，G03新depth p95 16.34mm | 仅selection_verified为核验选择；surface proxy非解剖唯一面积，不自动喂Body | [报告](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/TECHNICAL_REPORT.md) |
| 相机Gate | G01五相机 | 0/5资格通过，均INSUFFICIENT_EVIDENCE；未修位姿 | 资格/对应充分性可复用，不因canonical命名认证真实pose | [报告](../../experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/TECHNICAL_REPORT.md) |

## 当前初始化逐组失败入口

以下为主004固定四组，E1/E2各0/4完整验收，数值成功均4/4。影像只展示历史已冻结结果，本任务未重绘或生成预测。完整逐源/帧候选解释见[失败台账](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/FAILURE_LEDGER.md)。

| 物理组 | E1 主要失败 | E2 主要失败 | 图像证据 |
| --- | --- | --- | --- |
| G01_004 | 留出轮廓固定源MAE 12.25px | 多初值p95 4.455mm、Ring −0.08509mm | [所有帧](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G01_004_ALL_VIEW_OVERLAYS.png)、[六方向](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G01_004_SIX_DIRECTION_BODIES.png) |
| G03_004 | 留出轮廓11.38px | 多初值2.288mm、轮廓11.93px、Ring −0.05597mm | [所有帧](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G03_004_ALL_VIEW_OVERLAYS.png)、[六方向](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G03_004_SIX_DIRECTION_BODIES.png) |
| G05_004 | 多初值10.46mm、Ring −0.5633mm | start1不收敛；多初值9.653mm、Ring −0.5487mm | [所有帧](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G05_004_ALL_VIEW_OVERLAYS.png)、[六方向](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G05_004_SIX_DIRECTION_BODIES.png) |
| G06_004 | 旋转边界、多初值3.774mm、Ring −0.2596mm | 多初值7.193mm、轮廓15.78px、Ring −0.114mm | [所有帧](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G06_004_ALL_VIEW_OVERLAYS.png)、[六方向](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/figures/G06_004_SIX_DIRECTION_BODIES.png) |

附加 G03_005 E2 start0 是另一个不收敛结果；G01_005/G03_005 两池也未过完整门槛。G01_PHOTO、G05_PHOTO、G05_005 各单源不足多视角，E1/E2 保留 null/NaN。G03 E2 Ring 值贴近有限采样/精度阈值，不能把有限射线判定当数学证书。可观察绿色Mask边界与接触未知界、隐藏椭球背面必须区分。

## 早期渐进与视角聚合的边界

- [PMGR-PROGRESSIVE](../../experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001/TECHNICAL_REPORT.md)：4物理组、80/80臂完成固定预算；1514接受/8086拒绝，4臂留出固定射线覆盖降低，科学结论MIXED。不能将重复seed/16case当独立组，也不承诺渐进解锁全面优于配平对照。
- [PMGR-FFD-002](../../experiments/TASK-E4-PMGR-FFD-002/TECHNICAL_REPORT.md)：G01/G06两组6臂实际有更新，但G06事后同尺度FD四项全失败；NUMERICAL_GATE_NOT_PASSED，P2/P3多次BLOCKED，无独立HOLDOUT。实际renderer为nvdiffrast，不能称为已执行官方PyTorch3D；禁止把已有数值端点当可靠P3或直接进入B1/B2。
- [VIEW-PARTITION-MAST3R](../../experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/TECHNICAL_REPORT.md)：4组5视频，18次官方MASt3R前向与5次HERO已实际执行；新增来源点/005覆盖改善不代表绝对精度。跨视频双向冲突约66%/70%，联合场景NOT_FUSED，照片无公制XYZ。不要重复将其描述为尚未跑过真实官方匹配。

最新Hull的已运行但未通过新PM验收身份只继承[AGENTS](../../AGENTS.md)，本轮未充分复核其全部指标，因此不新增成熟度或科学通过结论。

## 历史失败保留规则

[历史审计报告](https://github.com/zheng1524/ring-first-3d/blob/7c961d994833a960917f9c36928559e85eb389ac/experiments/TASK-HISTORY-ASSET-AUDIT-002/TECHNICAL_REPORT.md)的未运行 B3/BPA 仍为 NOT_RUN；synthetic Ring 点云配准3次失败、真实 SKIPPED，H=I 不是成功。不要凭名称添加不存在的可复用模块。早期错误“32来源缺位姿”保存在 repair 的 SUPERSEDED_PHASE0；正确资产来自原始 FINAL_CAMERA_POOL，当前 native T 全75存在。这段纠错不能被再当成相机缺失事实。
