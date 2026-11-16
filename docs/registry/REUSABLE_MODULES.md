# 可复用代码清单

审计固定快照 5636aaebd61a3d53b69f528692c4c7095df46508；DXY 独立仓库固定 75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95。完整源码文件 SHA256 在每卡列出，不是 commit SHA 或 AST SHA。模块条目共享文件时 SHA 相同属于正常现象。函数/类均通过 Python AST 静态核验；本任务没有导入历史 main 或运行算法。

复用标记描述命名实现及可核验的历史操作：DIRECT_REUSE=命名实现不改逻辑调用；AST_REUSE=仅抽取指定 AST 原实现，仍需提供依赖；ADAPTED_REUSE=明确改动接口/目标/输出；REIMPLEMENTED=另写数学/损失/流程，不能称原样复用。模块卡并不保证整文件及其 main 可直接执行。任务脚本普遍有绝对路径、星号导入、R/ROOT 输出副作用；实际复用必须在独立任务封装、绑定原依赖和新输出目录，不运行原 main 覆盖历史文件。本轮没有进行任何代码复制或共享模块晋升。

分支是历史来源标签；固定源码版本统一用 source_commit 精确取回。历史 tip 与快照字节匹配信息保留在 [MODULE_REGISTRY.json](MODULE_REGISTRY.json)，null 表示未单独核验 tip，不是已证实相同。renderer 快照有 camera-preview 扩展，和旧 main 不同，不能把它说成 main 原字节。

## T01 · DXY正式API

- 源码：[/home/liu/new-polyp-dxy/src/dxy_mid/pipeline.py](https://github.com/zheng1524/new-polyp-dxy/blob/75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95/src/dxy_mid/pipeline.py)；符号：`measure_files`、`measure_frame`。
- 历史分支：`main`；固定 commit：`75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`。
- 文件 SHA256：`2671739527cf8433b58dd480a6f40302c13fe0ab2ab3474d09ad318d6a45146a`；7658 bytes。
- 工程 **FROZEN**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：同帧图像/uint8类别Mask，R5/R10内径。输出：正式candidate原生像素中心/basis及质量；DXY自身另产mm。
- 调用：`measure_files(image_path, mask_path, inner_diameter_mm=10., source_id=stable_id)`。函数精确签名：`measure_files(image_path, mask_path, *, inner_diameter_mm, source_id=None, stem=None, **kwargs)`；`measure_frame(image: np.ndarray, labels: np.ndarray, *, inner_diameter_mm: float, source_id: str, stem: str | None=None, image_sha256: str='', mask_sha256: str='', config: MeasurementConfig | None=None)`。
- 修改与限制：DXY独立V9.1+Mid；75候选不认证隐藏轮廓；3D只能消费像素几何，不能用DXY mm定形。
- 实测/数值核验及失败证据：[对应记录](https://github.com/zheng1524/new-polyp-dxy/blob/75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95/README.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T02 · 冻结分割

- 源码：[/home/liu/new-polyp-dxy/src/dxy_mid/segmentation.py](https://github.com/zheng1524/new-polyp-dxy/blob/75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95/src/dxy_mid/segmentation.py)；符号：`INITSegmentation`。
- 历史分支：`main`；固定 commit：`75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`。
- 文件 SHA256：`f16b9c142894d0ef1d7e6b43f9f5d2c8cdeffdc8576e5c3e6493f7b7e60d57c4`；2445 bytes。
- 工程 **FROZEN**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：原RGB+固定INIT权重。输出：0背景/1Polyp/2Ring标签。
- 调用：`INITSegmentation(modelroot, 'cuda').predict(image_path)`。函数精确签名：类构造与方法见固定源码。
- 修改与限制：需固定权重/预处理；本任务不推理，不把Mask当真实边界GT。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/provenance/SEGMENTATION_IMPLEMENTATION.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T03 · 75来源DXY Adapter

- 源码：[experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/generate_dxy.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/generate_dxy.py)；符号：`one`。
- 历史分支：`exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`6073bd0050afdd092fa5a68d510fab72dca2b61bee9cfa8c301b766df43302b1`；3772 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：SOURCE_BINDING、匹配RGB/Mask/cache SHA。输出：只导出DXY像素geometry与quality。
- 调用：`one(source_id)  # 仅独立新副本`。函数精确签名：`one(cid)`。
- 修改与限制：73measure_files+2缓存measure_frame；沿A1 helper AST；禁止旧13来源CC直接套用。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/DXY_QUALITY_AUDIT.csv)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T04 · DXY二维几何转换

- 源码：[experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/prepare.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/prepare.py)；符号：`main`。
- 历史分支：`exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`b5b11e4f9ac73dac8ec3dd2d8262da96c692073b2f6e91009c548e31cdc153a0`；7329 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：native center c、basis B、原像素p。输出：二维椭圆区域；不直接产生3D坐标。
- 调用：`q=(p-c)@inv(B).T; target=(q*q).sum(1)<=1`。函数精确签名：`main()`。
- 修改与限制：表达式在main内；只摘取/适配该表达式，不能运行有旧CC/深度准备副作用的历史main。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NUMERICAL_CONTRACTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T05 · 统一九参数模型

- 源码：[experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py)；符号：`decode`、`sphere_mesh`。
- 历史分支：`exp/TASK-E4-A1-COARSE-BODY-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`34edacc79bfda081efb0dd29117ff5794736d2369529e336ff1c109d8551f769`；6539 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：theta9、R0；nt/nv。输出：中心/旋转/正半轴；实际V/F网格。
- 调用：`c,Q,a=decode(p,R0); U,F=sphere_mesh(96,48)`。函数精确签名：`decode(p, R0)`；`sphere_mesh(nt, nv, cut=-1.0)`。
- 修改与限制：仅统一椭球；背面推断；不得混用同文件其他形态专用bounds作为本轮统一模型。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/CODE_REUSE_MAP.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T06 · 解析椭球投影

- 源码：[experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py)；符号：`ellipse_projection`、`signed_distance`。
- 历史分支：`exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7`；4179 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：theta9、R0、K、c2w。输出：投影center/M/axes/128点曲线；Sampson近似距离。
- 调用：`ellipse_projection(p,R0,K,T)`。函数精确签名：`ellipse_projection(p, R0, K, T)`；`signed_distance(uv, center, M, axes)`。
- 修改与限制：有限前视椭圆；距离不是严格点到椭圆欧氏距离；不可替代完整GT。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NUMERICAL_CONTRACTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T07 · Mask/Ring未知二维损失

- 源码：[experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py)；符号：`target_data`、`cad_visibility`、`two_d_parts`。
- 历史分支：`exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7`；4179 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：完整目标Mask、原标签、CAD首深度。输出：双向轮廓/4x4面积池化/可见性残差块。
- 调用：`target_data(mask,labels,cad,T,K); two_d_parts(p,R0,target,K,T,ring_scene)`。函数精确签名：`target_data(mask, labels, cad, T, K)`；`cad_visibility(p, R0, rays, cad)`；`two_d_parts(p, R0, target, K, T, ring_scene)`。
- 修改与限制：Ring未知；接触轮廓剔除；4x4是求积近似；软CAD可见性可能抬高数值Jacobian秩。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/PROTOCOL_CORRECTION_v0.2.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T08 · 历史A1 TRF框架

- 源码：[experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py)；符号：`Problem.solve`。
- 历史分支：`exp/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`a58b80f81853b4e6995a93dd8135a78b0623acd68c1ec00defa68a3f2081cf33`；6825 bytes。
- 工程 **FROZEN**；科研 **MIXED**；复用 **AST_REUSE**。
- 输入：统一base/R0/界/权重及residual。输出：三初值TRF求解记录。
- 调用：`Problem.solve(start=0)  # 使用已适配Problem`。函数精确签名：`Problem.solve(self, start=0)`。
- 修改与限制：solve原样AST；历史Problem.residual另含HERO depth_parts，2D初始化不可整体调用该Problem。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T09 · 当前2D E1/E2拟合

- 源码：[experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/fitting.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/fitting.py)；符号：`Problem`、`qualified`、`main`。
- 历史分支：`exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`2e9af7fa5952b56e65c43376cbb6faf78e0b19dbaedeb8e366a0a598b91ca6d9`；5722 bytes。
- 工程 **VERIFIED**；科研 **FAILED_FOR_CURRENT_REQUIREMENT**；复用 **ADAPTED_REUSE**。
- 输入：冻结单视频FIT、DXY/完整Mask、相机/CAD。输出：收敛资格筛选后的Body-E；失败null。
- 调用：`problem=Problem(name, arm); problem.solve(start=0); qualified(problem, result)`。函数精确签名：`qualified(problem, r)`；`main(name, arm)`。
- 修改与限制：两臂4/4数值、0/4完整验收；保留36初值中2未收敛；非新正式重建主线。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NEXT_STAGE_ELIGIBILITY.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T10 · 015图像质量与方向贪心

- 源码：[experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py)；符号：`skeleton_proxy`、`main`。
- 历史分支：`exp/TASK-E4-MULTIVIEW-INIT-STALK-015`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`88e74d19f788e765818e2c77135248f315bbe0d58bc859962badb6623c445d9d`；5899 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **ADAPTED_REUSE**。
- 输入：同视频候选、原Mask/RGB、相机方向。输出：质量proxy、最多8FIT/保护HOLDOUT。
- 调用：`skeleton_proxy(mask); 选择逻辑在main内`。函数精确签名：`skeleton_proxy(m)`；`main()`。
- 修改与限制：目标是质量+角度互补，不是最大表面积；原main用旧Body中心/固定种子，当前适配用Ring原点。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/config/VIEW_SELECTION.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T11 · 016方向配额与权重

- 源码：[experiments/TASK-E4-UPDATE-CAUSALITY-016/code/prepare016.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-UPDATE-CAUSALITY-016/code/prepare016.py)；符号：`weights`、`coverage`、`main`。
- 历史分支：`exp/TASK-E4-UPDATE-CAUSALITY-016`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`bda26184b8b3ec74216fa5c5c620755a6cae7e6c50f06272fa0a3c017918ecd9`；7870 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **ADAPTED_REUSE**。
- 输入：显式direction_block、帧序、HERO anchors。输出：区块均衡选择及每块等质量权重。
- 调用：`weights(views,ids); coverage(views,ids)`。函数精确签名：`weights(vs, ids)`；`coverage(vs, ids)`；`main()`。
- 修改与限制：分区是方向簇不是时间桶；禁止隐式缺省block坍缩；固定HERO源，不能据GT重排。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-UPDATE-CAUSALITY-016/metrics/VIEW_SAMPLING_AUDIT.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T12 · MAX覆盖目标选择

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/coverage.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/coverage.py)；符号：`proxy`、`visible`、`greedy`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`156b183d0faa15847bca5fd83da151a7dcde1d7bd53bc349b161275cca51b920`；12435 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：合格相机+FIT-only来源标记surfel代理。输出：epsilon-near-greedy列表/边际代理面积。
- 调用：`greedy(vs, visibility, weight, source_filter=['004'])`。函数精确签名：`proxy(g)`；`visible(X, C, K, lab, sc, ring, tol=0.15)`；`greedy(vs, vis, weight, source_filter=None)`。
- 修改与限制：0.2mm/法向bin只是冻结表面代理；非真实未知背面，也非全局最优；不足36不凑数。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/selection_verified/G03_SELECTION.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T13 · HERO支持图单独选择

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/coverage.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/coverage.py)；符号：`support_pairs`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`156b183d0faa15847bca5fd83da151a7dcde1d7bd53bc349b161275cca51b920`；12435 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：合格target/support RGB、冻结K/C、SIFT。输出：候选支持图评分，实际3图计划。
- 调用：`support_pairs(vs,target)`。函数精确签名：`support_pairs(vs, target)`。
- 修改与限制：支持图与coverage target目标不同；G06新评分未普遍优于原支持，不能按新HERO结果选图。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/selection_verified/G06_SUPPORTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T14 · Ring-First/RGB相机候选

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/cameras.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/cameras.py)；符号：`observe`、`rf`、`yaw_resolve`、`physical`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`ba95a389fc6722841491c3f876906e0014262c8baa055637a648bc66378db95f`；8549 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：Ring typed弧/原Mask、RGB公制对应、冻结K。输出：Ring五维+RGB yaw/法向候选与物理检查。
- 调用：`rf(view,ob,rr); yaw_resolve(poses,rr,ob)`。函数精确签名：`observe(v)`；`rf(v, ob, rr)`；`yaw_resolve(poses, rr, ob)`；`physical(v, C, ob)`。
- 修改与限制：Ring旋转对称不能独立确定yaw；numerical/formal/GT不同；K固定假设有条件。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/CAMERA_QUALITY_AND_UNCERTAINTY.csv)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T15 · RGB/Ring Ceres联合候选

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/register.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/register.py)；符号：`Bundle`、`qualification`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`a5f04bbb5ec9c6ba61a3cf2ebb89b96d8c9beb2ee7f361c137ce2581c834be58`；10342 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：固定源相机/真实RGB地标、CAD弧。输出：共享SE3或完整6DoF/XYZ条件候选。
- 调用：`Bundle(group,views,mode,selected)`。函数精确签名：`qualification(v, C)`。
- 修改与限制：仅89相机联合局部更新；H/局部修正有规范冗余；默认005 PnP已依赖004地图，不是独立005 SfM。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/metrics/ACTUAL_CERES_SCOPE.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T16 · Ring公制几何投影

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/torus.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/torus.py)；符号：`curves`、`PoseCache`、`project_dC`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`904d9cae48c1cc9317454c2feb80a331908009e095683851c8e8e3c80625191d`；3903 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：固定CAD约定、C/K。输出：厚torus I/O曲线及投影导数。
- 调用：`curves(C,K,n=256)  # 参数以源码签名为准`。函数精确签名：`curves(C, K, n=1024)`；`project_dC(X, C, K, dC=None)`。
- 修改与限制：Ring必须是固定CAD；解析torus需与实际CAD核验，不得重建Ring点云充当尺度。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/metrics/CONTRACT_AND_GEOMETRY_TESTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T17 · 021共同地标BA

- 源码：[experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/ba021.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/ba021.py)；符号：`CommonPoints`、`BA`、`run`。
- 历史分支：`exp/TASK-E4-RING-ANCHORED-JOINT-BA-021`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`ced95fe580a30f5c1fbf22bdbb4724c91fc641bfe38911f16610e5d22227b0c7`；10769 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：G01同名背景轨迹、Ring CAD、固定相机。输出：视频级共享刚体+18共同XYZ候选。
- 调用：`run(arm, scope, ids, seed)`。函数精确签名：`run(arm, scope, ids, seed)`。
- 修改与限制：G01限定；FIT改善不等独立跨视频几何改善；共享刚体不能修同视频内部HERO相对关系。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T18 · 021身份核验

- 源码：[experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/identity021.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/identity021.py)；符号：`main`。
- 历史分支：`exp/TASK-E4-RING-ANCHORED-JOINT-BA-021`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`791de579b21aa82ff33b4a6438c1e7cd76ffe0d9f4bad737e19770530c6c4ac8`；2633 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：实际feature IDs/描述子/RANSAC链接。输出：553观察、547链接一致性回执。
- 调用：`main()  # R指向只读021输入，输出重定向新任务`。函数精确签名：`main()`。
- 修改与限制：全部背景，不是Polyp同名材料GT；DXY-REPAIR实际重放过，不运行BA。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/provenance/021_REPLAY/OBSERVATION_IDENTITIES_VERIFIED.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T19 · HERO官方loader/归档Mesher

- 源码：[experiments/TASK-E4-HERO-BODY-ADAPT-018/code/infer018.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-HERO-BODY-ADAPT-018/code/infer018.py)；符号：`loader`、`mesher`、`main`。
- 历史分支：`exp/TASK-E4-HERO-BODY-ADAPT-018`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`e556d77563ede58d3cb202631f1b855b9a8c0d5a8c930f9f273c2712368b2125`；5445 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：固定官方commit/权重；target+3supports及公制相机。输出：原生352x640轴向mm深度及旧360归档接口。
- 调用：`loader(); mesher()  # 仅已有环境的新任务副本`。函数精确签名：`loader()`；`mesher()`；`main()`。
- 修改与限制：39新推理+4复用；018旧建面含352到360接口，Raw FaceID不能冒充原生PixelID。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-HERO-BODY-ADAPT-018/provenance/HERO_MODEL.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T20 · MAX原生HERO建面

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/infer.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/infer.py)；符号：`loader`、`meshfn`、`one`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`c48926cb8ede2792a903436c6478f4fd44f00a8e261c9408521165db738c7049`；5617 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：固定HERO/3支持图+native K/C。输出：352网格Raw Native Mesh/原生深度。
- 调用：`model=loader(); mf=meshfn(); one(model, r, mf)`。函数精确签名：`loader()`；`meshfn()`；`one(model, r, mf)`。
- 修改与限制：区别018升采样360接口；47推理完成不证明新几何正确；不填洞/ICP/融合。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/metrics/HERO_INFERENCE_RESULTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T21 · 017四状态面证据

- 源码：[experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/analyze017.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/analyze017.py)；符号：`mapped_labels`、`get_source`、`classify`、`analyze`。
- 历史分支：`exp/TASK-E4-HERO-GEOMETRY-CLEAN-017`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`e97c8b3d2b0213d8c16a8be284330bf332c50ded12d34553adb3d6c322dd2f8b`；16009 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：Raw原面+原生格、标签、K/T和CAD。输出：TRUSTED/UNCERTAIN/REJECTED/UNKNOWN及原因。
- 调用：`analyze(source,ring_scene,thresholds)`。函数精确签名：`mapped_labels(labels, K, Kn, shape)`；`get_source(r, representation)`；`classify(f, t)`；`analyze(s, ring, t)`。
- 修改与限制：18源原报告零删面；TRUSTED仅规则标签；Raw FaceID与NATIVE_GRID FaceID独立。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T22 · 017双侧断层证据

- 源码：[experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/gap017.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/code/gap017.py)；符号：`patch_plane`、`gap_edges`。
- 历史分支：`exp/TASK-E4-HERO-GEOMETRY-CLEAN-017`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`2728185cd8311b5d24c23516e815f1c6a869e12804f0e89f969de5ee03c28f79`；8609 bytes。
- 工程 **REUSABLE_CANDIDATE**；科研 **CONDITIONAL**；复用 **AST_REUSE**。
- 输入：深度/标签/K/T及原生拓扑。输出：支持断层edge集合/证据行。
- 调用：`gap_edges(z,labels,K,T,P,F,uv,thresholds)`。函数精确签名：`patch_plane(z, lab, uv, direction, t)`；`gap_edges(z, lab, K, T, P, F, uv, t)`。
- 修改与限制：弱/掠视/PCA错误片层不保证可判；不因为零删除就放宽阈值。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/FAILURE_LEDGER.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T23 · MAX清理适配

- 源码：[experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/clean_native.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/clean_native.py)；符号：`one`。
- 历史分支：`exp/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`35676602827d8ae367d3f66927d0067e08caec291acec529c5e90ee0d380651a`；5794 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：新HERO native网格+017固定规则。输出：原V/F身份四类子集/OBS_TRUSTED。
- 调用：`one(inference_record)`。函数精确签名：`one(rec)`。
- 修改与限制：AST复用017+018 gap组合，但原生建面接口不同；清理不认证跨源一致性。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/metrics/HERO_CLEANING_RESULTS.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T24 · PyTorch3D Renderer/Ring-Aware

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/p3d.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/p3d.py)；符号：`Case`、`Case.aware`、`renderer`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`04c70090e5ee50a5345169f132ccd8a0b988c5b72c03a29745b76d04e45eef0f`；5177 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：固定K/T、归一V/F、Mask/侧界与CAD。输出：官方片元/可微轮廓/Ring未知权重。
- 调用：`case=Case(name); case.aware(fragments,cid,True)`。函数精确签名：`Case.aware(self, fr, cid, return_aux=False)`；`renderer(size)`。
- 修改与限制：不得使用根Ring-Aware软zbuf失败初版；+0.5光栅补偿、bin_size/容量需保留，mask训练不代表3D验收。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/REPRODUCE.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T25 · 011接触方向投影

- 源码：[experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/code/stable.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/code/stable.py)；符号：`active_contact_projection`、`state_equal`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-RING-AWARE-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`66c98a837f6942bece2f392b4bee7adf4040bb37d964ecbb2762cb190df9fd62`；3003 bytes。
- 工程 **REUSABLE_CANDIDATE**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：chart/guard、before、delta、active参数。输出：线性化可行方向/Adam状态相等检查。
- 调用：`active_contact_projection(ch,guard,before,direction,active)`。函数精确签名：`active_contact_projection(chart, guard, q, delta, active)`；`state_equal(a, b)`。
- 修改与限制：只是线性化QP；最终非线性guard仍必须检查；011严格重放154/155，不得标全PASS。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T26 · 011受控Adam/回滚

- 源码：[experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/code/train.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/code/train.py)；符号：`main`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-RING-AWARE-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`770568b2187214f6ed3f2c77b63b5b73c585efdde0ebc32f79561865b19f140a`；7165 bytes。
- 工程 **REUSABLE_CANDIDATE**；科研 **MIXED**；复用 **ADAPTED_REUSE**。
- 输入：chart、完整FIT目标/guard、固定预算。输出：接受/拒绝/回缩/参数与Adam矩状态恢复。
- 调用：`python train.py CASE  # 仅新副本`。函数精确签名：`main()`。
- 修改与限制：300提案不等300更新；残留接触/跨进程重放缺口保留；不是通用可安装优化器。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/CAP_REPAIR_STABLE_011/metrics/NINE_CASE_RESULTS.csv)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T27 · 自由顶点参数化

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/free_model.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/free_model.py)；符号：`FreeVertices`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`dd9ce5f9d67e4a0434e3d62041fdd28030359f172bf3d6216545362a8b83048a`；2864 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：Case原始网格与边界/底盖约束。输出：共享q到世界V/F。
- 调用：`FreeVertices(case).mesh(q)`。函数精确签名：类构造与方法见固定源码。
- 修改与限制：继承约束、初值尺度和底盖身份；自由顶点不保证长柄/拓扑/观测可达性。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T28 · 多视角分块目标/权重

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/multiview.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/multiview.py)；符号：`MultiObjective`、`weights`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`940e48d06cf9fad73128f3ab4c2a54899e36bcdbaaf843db5cd6bdf919bde0a9`；2388 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：同组共享Mesh、FIT、深度缓存及分区。输出：精确逐视角目标和梯度累加。
- 调用：`MultiObjective(c,ch).compute(q,gradient=True)`。函数精确签名：`weights(c, ids)`。
- 修改与限制：逐视角fresh graph节省显存；默认block字段须先审计，目标权重不代表独立信息。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-UPDATE-CAUSALITY-016/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T29 · 旧稀疏相对深度

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/depth_terms.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/depth_terms.py)；符号：`D2Depth`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`f9e935194efa73ecf4d3e20d185018a129ab665202f5670b58365ff156947644`；2419 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：冻结稀疏射线/点对、当前Mesh。输出：绝对/相对深度块。
- 调用：`D2Depth(c).terms(mesh,cid,'E3')`。函数精确签名：类构造与方法见固定源码。
- 修改与限制：与018 full-native不同；不能把256缓存射线称完整原生。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-UPDATE-CAUSALITY-016/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T30 · 018完整原生HERO损失

- 源码：[experiments/TASK-E4-HERO-BODY-ADAPT-018/code/hero_objective018.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-HERO-BODY-ADAPT-018/code/hero_objective018.py)；符号：`HeroDepth018`、`Objective018`。
- 历史分支：`exp/TASK-E4-HERO-BODY-ADAPT-018`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`99ca53393be1961db801c5e11e651ee74ef7c00c930cc3c09f3d3afa50001b33`；8386 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：FULL/TRUSTED原生观测及当前共享Mesh。输出：真实重心世界点恢复轴向mm深度/残差。
- 调用：`HeroDepth018(c,ch,'TRUSTED').term(mesh,cid)`。函数精确签名：类构造与方法见固定源码。
- 修改与限制：29/29原生梯度/插值门禁；未命中固定代价仍没有深度梯度；不能宣称已解决覆盖。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-HERO-BODY-ADAPT-018/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T31 · 可微真实轮廓边损失

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/contour_objective.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/contour_objective.py)；符号：`ContourDistance`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`f8966a0a304b056bc9d85338bab9a082809b1255a7e87fa5a4f9e167945629f1`；5157 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：实际世界V、原图Mask、可见轮廓边。输出：双向轮廓残差/分量记录。
- 调用：`ContourDistance(c)(world_vertices,cid)`。函数精确签名：类构造与方法见固定源码。
- 修改与限制：离散边/可见性/NN detached；并非全局光滑；Ring接触未知不当解剖边界。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T32 · Proposal Generator

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/strategy.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/strategy.py)；符号：`project_global`、`local_directions`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`130bcab31ab9d52ddddfa369dca208a79de773e17be8534530c0134b499d04ea`；1248 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：chart、before、真实完整梯度。输出：全局或局部候选delta。
- 调用：`local_directions(ch,before,grad)`。函数精确签名：`project_global(ch, before, d)`；`local_directions(ch, before, grad)`。
- 修改与限制：只生成候选；必须再过完整FIT/GeometryGuard；不能以位移大宣称形状正确。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-014/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T33 · 接触固定Sobolev提案

- 源码：[experiments/TASK-E4-UPDATE-CAUSALITY-016/code/coherent016.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-UPDATE-CAUSALITY-016/code/coherent016.py)；符号：`coherent_directions`。
- 历史分支：`exp/TASK-E4-UPDATE-CAUSALITY-016`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`1a4504d3cce342fc22db7842bd6a17effc5987209ffe90fb1e90b8c85cf42498`；1781 bytes。
- 工程 **VERIFIED**；科研 **MIXED**；复用 **DIRECT_REUSE**。
- 输入：contact faces、图邻接、原候选方向。输出：Dirichlet自由子空间平滑候选。
- 调用：`coherent_directions(ch,before,directions,guard)`。函数精确签名：`coherent_directions(ch, before, directions, guard)`。
- 修改与限制：不是非线性可行域精确投影；G03仍薄片而非可信柄；018 COH16是命名，不能说只有16自由度。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-HERO-BODY-ADAPT-018/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T34 · GeometryGuard

- 源码：[experiments/TASK-E4-PYTORCH3D-014/code/safe_geometry.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-PYTORCH3D-014/code/safe_geometry.py)；符号：`GeometryGuard`、`dense_face_distance`、`self_intersections`。
- 历史分支：`exp/TASK-E4-PYTORCH3D-014`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`5ff32cc404300406ec05f0b147f332691186ead64df88ff2ad4f69569fd715fc`；5586 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：原V/F、CAD、信赖域和候选V。输出：拒绝原因/密集Ring与反向包含/自交。
- 调用：`GeometryGuard(c,ch).inspect(V,oldV)`。函数精确签名：`dense_face_distance(rs, V, F, ringV, divisions=32, ringF=None)`；`self_intersections(V, F)`。
- 修改与限制：32阶训练/64阶独立检查有限采样；3-ray版本与后续11-ray修正区别保留；通过不等全表面无穿透。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-PYTORCH3D-014/FAILURE_LEDGER.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T35 · 冻结后最佳刚性GT评价

- 源码：[experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/best_rigid015.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/best_rigid015.py)；符号：`align`、`feret`。
- 历史分支：`exp/TASK-E4-MULTIVIEW-INIT-STALK-015`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`ff7b26a302d05f68b286b76c0faaf08a84cec10c711cd928eda7eb7a601f43b8`；12437 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：已冻结预测、固定尺度和明确身份GT。输出：只供评价的SE3/形状标量。
- 调用：`align(V, F, GV, GF, D); feret(V, n)`。函数精确签名：`align(V, F, GV, GF, D)`；`feret(V, n)`。
- 修改与限制：禁止GT配准进入预测/初始化或选模；同一最佳刚体用于全部指标，严格实体IoU需GT有效。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T36 · 实际投影/局部可辨识性

- 源码：[experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/evaluate.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/evaluate.py)；符号：`projection_metrics`、`identifiability`。
- 历史分支：`exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`61bfa908cbd2ba6deffecf30f19a0075275f24b29cec6e99598d0b3b10b15abc`；10827 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **ADAPTED_REUSE**。
- 输入：全部预测冻结后的模型/原Mask/相机CAD。输出：IoU/FN/FP/轮廓分布、无先验SVD。
- 调用：`projection_metrics(model,cid); identifiability(problem,p)`。函数精确签名：`projection_metrics(m, cid)`；`identifiability(problem, p)`。
- 修改与限制：conic-only单视角至多5维；软CAD/float32数值满秩不是准确度；HOLDOUT有上游历史依赖。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/JACOBIAN_IDENTIFIABILITY.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T37 · 完整性/公平性验证

- 源码：[experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/validate.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/code/validate.py)；符号：`main`。
- 历史分支：`exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`f13e626e52d0c80b6a3eb645de42069395bd811f69604cd2ae98caf04b5f25b0`；3589 bytes。
- 工程 **VERIFIED**；科研 **NOT_EVALUATED**；复用 **ADAPTED_REUSE**。
- 输入：冻结源码/预测/输入SHA及两臂实际记录。输出：705/705工程契约结果。
- 调用：`main()  # 仅只读检查，写验证回执`。函数精确签名：`main()`。
- 修改与限制：工程检查不是科研验收；本登记不重跑历史验证。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/VALIDATION.json)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T38 · 批准的原P0可视化

- 源码：[visualization/real_p0_renderer.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/visualization/real_p0_renderer.py)；符号：`limits`、`view`、`project_camera`、`camera_rays`。
- 历史分支：`main`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99`；5827 bytes。
- 工程 **VERIFIED**；科研 **NOT_EVALUATED**；复用 **DIRECT_REUSE**。
- 输入：真实XYZ/RGB、冻结相机或固定视角。输出：毫米等比例图、射线/相机投影。
- 调用：`limits(point_sets,ring,angle); camera_rays(uv,K,c2w)`。函数精确签名：`limits(point_sets, ring, angle=DEFAULT_ANGLE)`；`view(ax, points_mm, color, ring, bounds, angle=DEFAULT_ANGLE, title='', size=DEFAULT_POINT_SIZE, highlight=None)`；`project_camera(points_mm, K, c2w)`；`camera_rays(uv, K, c2w)`。
- 修改与限制：baseline中camera-preview不同于main的旧bytes；与完整A→B重投影内核不同；显示Ring采样不是Ring重建。
- 实测/数值核验及失败证据：[对应记录](../../visualization/README.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T39 · TSDF诊断适配

- 源码：[experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/hero_tsdf_adapter.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/hero_tsdf_adapter.py)；符号：`HEROToTSDFAdapter`、`volume`。
- 历史分支：`exp/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`23fe3cfdad39087f21b598f62e747cd5368374b02b0112e0e249d1cd6c5d3e91`；2099 bytes。
- 工程 **EXPERIMENTAL**；科研 **FAILED_FOR_CURRENT_REQUIREMENT**；复用 **ADAPTED_REUSE**。
- 输入：mm深度/native K/c2w、RGB/Mask。输出：m单位Open3D RGBD/积分体。
- 调用：`HEROToTSDFAdapter(...).rgbd()`。函数精确签名：`volume()`。
- 修改与限制：完整实验已跑；90%hit/严格单位等价门槛FAIL；仅失败回归，不推荐重试默认融合。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T40 · 官方NeuralFusion接线

- 源码：[experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/infer.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/infer.py)；符号：`run`、`instrument`。
- 历史分支：`exp/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`7957087680f84d5cbe1a0c215d2e5e4f343976183bd24831edd0254c80c5d4f0`；8257 bytes。
- 工程 **VERIFIED**；科研 **FAILED_FOR_CURRENT_REQUIREMENT**；复用 **ADAPTED_REUSE**。
- 输入：固定官方预训练权重+清理深度/metric domain。输出：extractor→net→integrator→translator→SDF Mesh。
- 调用：`run(scene, order); instrument(pipe)`。函数精确签名：`run(scene, order)`；`instrument(pipe)`。
- 修改与限制：完整官方链已经执行；G01 ref08首层73.52%→0.47%，不批准默认融合；不宣称算法从未完整跑。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T41 · MonoSDF项目适配

- 源码：[experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001/code/official_adapter.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001/code/official_adapter.py)；符号：`make_model`、`ProjectLoss`、`packet`。
- 历史分支：`exp/TASK-E3-SDF-MONOSDF-FULL-TRAINING-REVALIDATION-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`067fdb97f68c97434d8438dc0d0443c46fa4a710c4c92b9e46502c2bfa0f300f`；11055 bytes。
- 工程 **EXPERIMENTAL**；科研 **NOT_EVALUATED**；复用 **ADAPTED_REUSE**。
- 输入：官方plain模型、固定metric域/ROI、原观测。输出：M0/M1训练数据/损失接口。
- 调用：`make_model(); packet(cid,step)`。函数精确签名：`make_model()`；`packet(cid, step, N=1024)`。
- 修改与限制：是适配/修补的官方runner接线，非原样官方全算法；目标200k未完成，不能将4000步或4090提取当10倍训练。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T42 · 旧Body-E重复实现（不推荐）

- 源码：[experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/code/fit_body.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/code/fit_body.py)；符号：`body_fit`。
- 历史分支：`exp/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`244a6192c08c86c9b8708b8add6cb6b0b338c50836cffa1ae5259fd79a549960`；4770 bytes。
- 工程 **DEPRECATED**；科研 **FAILED_FOR_CURRENT_REQUIREMENT**；复用 **REIMPLEMENTED**。
- 输入：选中3视角Mask、Ring CAD；DT/AMS构造。输出：旧Body-E九参数体。
- 调用：`body_fit(g, views, ringV, ringF, output)`。函数精确签名：`body_fit(g, views, ringV, ringF, output)`。
- 修改与限制：数学族相同但重写loss/初始化，不是A1解析loss的原样复用。当前应查T04–T09，旧Body仅作历史对照，不以旧结果补新预测。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/METHOD_AND_INPUT_AUDIT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## T43 · 真实A→B源面重投影

- 源码：[experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py](https://github.com/zheng1524/ring-first-3d/blob/5636aaebd61a3d53b69f528692c4c7095df46508/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py)；符号：`render`、`evaluate`。
- 历史分支：`exp/TASK-VIEW-OBSERVABILITY-GT-EVAL-001`；固定 commit：`5636aaebd61a3d53b69f528692c4c7095df46508`。
- 文件 SHA256：`0171f5a56d08ccce6c57cac8e04839c3ca9df5c3a4be9f1053a6920181d022d1`；9544 bytes。
- 工程 **VERIFIED**；科研 **CONDITIONAL**；复用 **DIRECT_REUSE**。
- 输入：A原始XYZ/F/顶点RGB；B的K/pose；刚体H；Ring类别。输出：RGBA/轴向z/faceID/重心/有效域；随后独立比较B。
- 调用：`pred=render(P, F, C, K, pose, H, ring_kind); evaluate(pred, B, labels)`。函数精确签名：`render(P, F, C, K, pose, H, ring_kind)`；`evaluate(pred, B, labels)`。
- 修改与限制：预测函数不收B图像/Mask/GT；输入需冻结源面，图像解释不是独立几何精度；固定640×360且依赖本地io_utils/CAD。
- 实测/数值核验及失败证据：[对应记录](../../experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/TECHNICAL_REPORT.md)；原实验的环境与复现入口按[实验索引](EXPERIMENT_INDEX.csv)定位。这里只引用既有验证，不声称本次重新运行。

## 执行依赖与复用审查

DXY 必须从独立仓库导入 dxy_mid.pipeline，固定 INIT 权重/预处理；不自行替代正式 P/Q 决策。当前 adapter 的 73 个 measure_files 与 2 个 measure_frame 案例见 T03；后者先把对齐缓存 RGB 转 BGR。

T04 是 main 内的矩阵变换片段，不能假造独立公开函数；T08 仅 Problem.solve 是 AST 原样，不代表旧 Problem.residual（含 depth）也用于 repair。T09 删除 depth block、适配来源并保存资格/轨迹；T42 则是旧重写实现，保留供排查重复实现。

T24 必须使用可见性修复后的 014 版本或 RingAware 的 VISIBILITY_ORDER_REPAIR_001；不能加载 RingAware 根目录原始 soft-zbuf 失败版本。T25/T26 011 严格 replay 为 154/155，不能许诺所有状态逐 bit 重演。T28 的旧 depth block 和 T30 的原生首层 block 是不同观察模型。T33 的 COH16 在 018 中不是 16 自由度，而是 642 自由顶点上的接触/Sobolev 提案。T34 有实际 dense-CAD 与 Guard，但不是无穿透数学证明。

PyTorch3D 官方 commit e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31；版本验证来自 RingAware 报告和既有梯度/有限差分核验。HERO 官方 commit 4483e25ede3eee1b6eaf96254d2544152f935c0d、checkpoint SHA 00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d；实际环境清单见各实验 provenance/RUNTIME，不把本次文档用 Python 版本说成实验环境。

独立 GT 最佳 6DoF 配准 T35 只在预测冻结后评价形状、固定 scale，不能用于生成预测或认证相机绝对精度。T38 负责点显示/相机射线，真正 A→B 原面渲染是 T43；两者不能互相冒称。
