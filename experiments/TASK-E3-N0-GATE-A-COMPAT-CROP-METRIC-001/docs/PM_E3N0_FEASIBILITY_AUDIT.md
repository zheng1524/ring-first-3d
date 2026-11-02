# Phase E3-N0｜预训练 NeuralFusion 科研可行性独立审计

日期：2026-11-02；身份：Phase E3-D PM；状态：**FEASIBLE_IN_PRINCIPLE / ENGINEERING_NOT_QUALIFIED / NO_INFERENCE**。此项是与 D0、G2、G3 并行的独立候选，不覆盖历史结论。完整阅读研究者的 `01_HUMAN_EXPERIMENT_PLAN.md` v0.1（154行），并核查官方代码、配置、权重仓库树及项目阶段记录。

## 1. 审查来源与 SHA

项目 `zheng1524/ring-first-3d` 阶段 HEAD：E3-A `8f5f7ea59efb32a0f633409386431811444ee399`、E3-B `a7c6233f33f9a2ec84b4ce19f668a187bd90b9c8`、E3-C `e8feece0718fee24a1b04b5e250629820e4f8299`、Camera Gate `6423b2709d1b528124ba6cc855883ba8a437e28c`、D0 `d69ade170352d1b5a1e46239f9516ab38c575648`。审读对应 `TECHNICAL_REPORT.md`、D0 `FAILURE_LEDGER.md` / `VALIDATION_RESULTS.csv` / `TSDF_CONFIG.json` / `HERO_TSDF_INPUT_MANIFEST.json` / `code/hero_tsdf_adapter.py` / `code/evaluate.py`、E3-C `CONSENSUS_TO_GLOBAL_FIELD_CONTRACT.md`、Camera Gate 报告；沿用已核对的E3-A/B报告。官方仓库 `weders/NeuralFusion` main tree `4f0c14f67ad9d2368b68cbeb78c237a6328971e5`，核对 `README.md`、`environment.yml`、`pipeline/*`、`training/{pipeline,database}.py`、`test.py`、两套checkpoint配置。**未从用户电脑复核实际GPU/驱动/环境，也未下载或运行checkpoint**。

入口：[官方代码](https://github.com/weders/NeuralFusion)｜[论文](https://arxiv.org/abs/2011.14791)｜[D0报告](https://github.com/zheng1524/ring-first-3d/blob/exp/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/TECHNICAL_REPORT.md)。

## 2. 已有工程资产（VERIFIED reports）

| 阶段 | 资产价值 | 不可升级的宣称 |
|---|---|---|
| E3-A | G01_004 11来源；36主来源跨4组/5视频，原Face/DAG、K/c2w、固定ROI和分母 | 相机/同物理面已认证 |
| E3-B | 17来源34个B0/B1局部字段，原面与合法域 | 可直接作为NeuralFusion已训练latent/SDF |
| E3-C | V0–V3 Support/Occlusion/Free代理、来源相关性及多峰记录 | FREE_SPACE_CONFLICT为真实错误标签 |
| Camera Gate | 5相机证据；均INSUFFICIENT_EVIDENCE、0次优化 | ref08/ref13/ref03或新增相机已严格认证；r14未单独审计 |
| E3-D0 | 官方Open3D 0.19.0 SINGLE/G0/G1、完整输入清单、masked RGB-D重放、固定首层评价、GLB/四图 | 数值门禁通过、几何连续可信；D0实际24PASS/1FAIL、几何不接受 |

NeuralFusion应只消费原生HERO深度 `352×640`、真实Polyp有效Mask和冻结相机，绝不读取原Mesh作为伪深度。Raw XYZ/Face ID只能当保护/比较分母。G01_004 G0=ref03/ref08/ref13，G1再加growth_r04/new_r00/growth_r14，按先验分区固定。

## 3. NeuralFusion 官方实现审计（VERIFIED from source）

| 事项 | 代码事实 | 迁移风险/处理 |
|---|---|---|
| 输入 | [`pipeline/pipeline.py`](https://github.com/weders/NeuralFusion/blob/main/pipeline/pipeline.py) 的`forward(data)`取`input`深度、`original_mask`、`intrinsics`、`extrinsics`、`origin`、`resolution`、`volume`、`count`；仅`uncertainty=true`再用`confidence` | 不消费原始RGB；Mask既用于把深度置0，也影响积分；不得把Ring/Background设Polyp有效 |
| 图像尺寸 | `extraction['values']`/`points`硬 reshape `(1,240,320,...)`；[`pipeline/model.py`](https://github.com/weders/NeuralFusion/blob/main/pipeline/model.py) 的LayerNorm按配置固定空间尺寸 | Gate A固定 `H=240,W=320,B=1`；不可随便改LayerNorm或非等比扭曲K |
| 空间和姿态 | [`utils/geometry.py`](https://github.com/weders/NeuralFusion/blob/main/utils/geometry.py) / `pipeline/utils.py`：`points_w = extrinsics * K^-1 [uZ,vZ,Z,1]`，再`(points_w-origin)/resolution`；`eye`也如此 | `extrinsics`必须是c2w不是w2c；depth、c2w平移、origin、resolution同单位；模型网格坐标为**体素单位** |
| 体素整合 | `FusionExtractor`按相机观测提取沿射线附近latent；`FusionNet`产生更新；`FusionIntegrator`按mask写入`volume/count` | 它不是把多张深度合成一张2D深度；顺序可能影响结果，必须reset并锁定顺序 |
| 译码 | `Translator`从latent格解码SDF/occupancy；官方渲染含输出尺度与mask语义 | 不可把全部网格或Unknown的零值自动当实体；mask/计数限制必须从源码验证 |
| GT耦合 | [`training/pipeline.py`](https://github.com/weders/NeuralFusion/blob/main/training/pipeline.py) 测试batch装`gt`，`_evaluate_database`直接读取GT grid；[`training/database.py`](https://github.com/weders/NeuralFusion/blob/main/training/database.py) 按dataset取GT格建域 | 不能直接调用官方`test.py`以用户GT建DB；须独立构造固定bbox空latent/count与inference-only评价，不读取GT |
| 环境 | 官方`environment.yml`含Python3.7、Torch1.10.1、Lightning1.5.7、CUDA10.2、Open3D0.10，且`training/database.py`导入`graphics.voxelgrid`（官方当前仓库树无`graphics/`） | 与本项目Open3D0.19环境不是同一依赖集合；先核对外部RoutedFusion/graphics依赖，采用隔离环境；不得修改主环境 |

### 官方权重与配置：不是可互换候选

| Checkpoint (GitHub文件已证实存在，未本地加载) | 文件大小/Git blob SHA | 几何与网络配置 |
|---|---|---|
| `pretrained_models/shapenet_noise_005/version_0/checkpoints/best.ckpt` | 16,882,708 bytes；`3f222e0cfc3239299b95fe4957ff19613f35a9c2` | 128³ / 17 features（含count）、n_samples=3、`output_scale=0.04`、`use_count=true` |
| `pretrained_models/tanks_and_temples/version_0/checkpoints/best.ckpt` | 18,237,012 bytes；`12331ffbc0a94222e36c80a03cce7bd43218cd2d` | 64³ / 9 features、n_samples=6、`output_scale=0.06`、`use_count=false` |

官方blob SHA不是文件SHA256。Gate A要对实际落盘checkpoint单独记录SHA256，并严格比较完整`state_dict`的missing/unexpected keys、形状、模型配置，不能只`strict=False`糊弄。`config.json`需完整继承同一checkpoint的`FUSION/RENDERER/PIPELINE`超参；不得混用128³网络与64³权重。两种权重均有**训练域不匹配**的风险：ShapeNet物体深度分布和内镜近距视角不同，Tanks场景尺度及64³分辨率更粗；现阶段无推理证据证明哪个更好。

## 4. 独立技术批评：必须修改RA初稿的地方

1. **尺度不是简单mm→m。** 官方代码把world除以`resolution`得到体素坐标，数据集训练格倾向单位归一范围；若直接用米且固定`1/128`模型米/voxel，约12.4mm的环外径仅占约1.6体素！应先按有证据的物理bbox选共同`L_mm`，设`X_norm=(X_mm-O_mm)/L_mm`、`resolution_norm=1/N`，故物理体素`L_mm/N`，并将c2w平移、深度与原点一致映射。对Ring物理尺寸做逆变换校验；**具体L_mm必须在Gate A由冻结输入几何计算并在看输出前固定**，不可用GT或结果倒推。
2. **裁剪不能只靠20% bbox扩边。** Ring可能使ROI过大、细柄失去像素，且放大后最近邻会有边界锯齿。先保留 `Polyp∪visible Ring`、扩边20%或≥16原像素作为**待验默认**，计算保留率/细结构宽度、bbox碰图边、合法深度丢失、视场、CAD次序。若违反预先冻结的质量阈值，Gate A停机提出统一修订，不逐帧目测手调。
3. **分辨率与像素中心。** 352×640 native 与360×640 archived不能当同像素系；crop、等比scale、letterbox是显式仿射，输入`K'=A K`须严格依坐标约定，padding的depth=0且`valid=0`。对最近邻采样不能要求所有重采样点XYZ与任意原点逐点**精确相等**：应测试映射回原像素中心的几何公式误差，并另报重采样量化误差；二者分开设阈。
4. **GT-free实现并非改一行test.py。** 官方数据库`GT`用于分配bbox及评估，不可在用户场景中调用该构造；必须独立创建空latent/count与显式物理ROI，解码只在观测支持mask/Count范围审计，同时区分网络推断区域、真正Unknown。
5. **首层评价优先于视觉光滑。** D0已出现CORE近邻保留改善但ref08首层50.22%→27.98%退化。三维光滑、完整、真实应三列独立；真实性不能由原HERO本身当物理GT。两网络域选择不应靠看谁漂亮；建议ShapeNet**暂定主权重，仅因128³对局部小物体分辨率与物体域较贴近**，Tanks只做Gate A静态备用兼容审计、Gate B不自动运行第二权重。
6. **逆序对照不能与引入新相机混淆。** F2_REVERSE应在Gate B和F2同批受同分母测试（若Gate B获授权），这是三CORE必要对照；F5_REVERSE为Gate C另批授权。每条序列从空场重置，不允许不同前缀复用旧缓存。

## 5. 可行性结论与门禁

**VERIFIED**：官方预训练权重与代码可见；输入信息理论上可由G01 native HERO + Mask + K/c2w提供；输出是3D latent译码而非全视角二维深度。**NOT_EVALUABLE**：用户本机CUDA/PyTorch兼容、checkpoint严格加载、显存/CPU峰值、crop对真实细柄的损失、预训练域迁移表现、GT-free解码是否可在当前安装路径直接运行。**DECISION**：先Gate A（严格加载的CPU静态兼容检查、裁剪/公制几何与GT隔离），不得运行真正F0–F5融合前向或GPU。Gate A失败则只能报告和提出有界兼容修订，不能降级为自主训练或重写网络。

建议RA重点复核：模型归一尺度与体素支持范围；ShapeNet主权重选择；不能把 `mask=0` 等同网络对Unknown已学会避开；CROP细柄保护门槛。研究者批准后才可将Gate A发Codex。
