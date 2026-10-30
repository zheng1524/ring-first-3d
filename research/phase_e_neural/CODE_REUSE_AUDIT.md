# Phase E｜CODE_REUSE_AUDIT（PM 静态索引）

状态：`PROPOSED / READ_ONLY_VERIFIED_FROM_GITHUB`。来源为分区任务 `CODE_REUSE_AUDIT.md`、该任务 `REPRODUCE.md`、边界生长 `CODE_REUSE.json` 和 `REPRODUCE.md`；**未在实验机运行源码或核验 LOCAL_ONLY 依赖**。历史源码中的绝对路径是溯源线索，不表示新 Codex 可以直接从 GitHub 单独运行。

|E0 需要|现有复用入口 / 依据|新实现界限|
|---|---|---|
|真实帧/缓存身份|旧 `match12.py` 的 `cv2.VideoCapture` / cached ledger；视角评价 `inventory.py:camera_frame_inventory`|复用缓存与 RGB SHA，不新增第二套视频解码；G01 004 原视频 raw 帧号未独立精确绑定|
|冻结 Ring-First `K/c2w`|`TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/common.py:source,target_source`；分区任务 `provenance/CAMERA_IDENTITY.json`|记录候选/条件相机等级；不修改原位姿，不把模型候选标为 GT|
|冻结 HERO/native Z-depth|旧 `run_mvs_adapter3.py:load_official`；分区任务 `hero_new.py`；`HERO_NEW_INPUTS_FROZEN.json`|E0 首轮只读取已有深度；不重新训练或重推 HERO；记录每个预测来源输入集|
|深度反投影及开放原面|旧 `ring_first_v1/scripts/common.py:unproject,depth_mesh`|只作数据格式适配；核对 352×640 → 640×360 适配及 `K`，禁止另写不一致反投影|
|Cleaned/来源/保护细柄|`TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/cleaning.py`；分区 `cleaned`、边界生长 `assets.py/geometry.py`|使用原始点/面 ID、UV、面法向、清理标志；不把 Cleaned 当绝对真值|
|MASt3R/匹配与候选刚体|本地官方 MASt3R `AsymmetricMASt3R.from_pretrained`；`match12.py`；分区任务 `matching.py/registration.py`|仅作历史观测/候选约束，不允许让未认证跨视频 H 悄然并入监督|
|真实 A→B、相同像素比较|Phase-D `geometry.py:projection,metric,common_metric`；边界生长 `evaluate.py/surface_support_audit.py`；更早 Phase-C `reprojection.py`|沿用冻结的真实目标帧/遮挡/未知/有效像素定义；新增 SDF / Map 输出 adapter|
|固定 Ring CAD 穿插|边界生长 `cad_audit.py` 与 `metrics/CAD_penetration_diagnostic.json`|独立几何安全审计；CAD 是固定实体，不重建为训练 Ring 表面|
|渲染/六视角/五面板|`visualization/real_p0_renderer.py` v1.0.0、`SameCameraScene`、`pointcloud_audit_renderer.py`；分区 `render_d.py`，边界生长 `render.py`|统一点大小、RGB 来源、mm 范围、Ring CAD 与同相机；只增输入 adapters，不重写渲染器|
|GLB/来源索引|分区 `ownership.py` / `GLB_INDEX.csv`、边界生长 `growth_lineage.json` / `OUTPUT_ASSET_INDEX.csv`|保存 SDF 零水平集的观测支持标签，Map per-pixel confidences 和原源身份；GLB 不是精度认证|

## 资产存在性与冲突

- GitHub `main` 仅有治理文件和渲染器，不含完整 Ring-First/HERO 模型运行闭包。实验分支含派生代码、清单和精选 PNG；大型输入及 GLB 只存本地。`CODE_REUSE_AUDIT` 不能代替执行机的 `sha256sum`/`stat`。
- `G01_004`、`G01_005` 属于相同物理组而各在 `LOCAL_RING_MM` 坐标。不能预设 c2w 共享世界系；`G01_photo001–003` 的 K/位姿未认证。
- 三个等级的 hash 需要区分：Git commit SHA（文档/代码）、源 RGB/mask/native depth 的 SHA256（数据身份）、外部权重 SHA256（依赖）；不要交叉使用。
- 把 `input_manifest` 作为单一读取入口，记录 `source_id`, `source_sha`, `used_by_HERO`, `K`, `c2w`, `xyz_unit`, `depth_type`, `pose_quality`, `holdout_role`, `GT_access=DENY`；任何缺项可判 `NOT_EVALUABLE`，不能虚构。

## 必须由 Codex 静态补证的内容

1. 逐文件检查实际本地存在性、大小与 SHA（尤其 14 历史参考 + 22 新增参考；不是 36 份互相独立真值）；归并别名相同、输入重合的 HERO 预测。
2. 遍历所有已知 HERO 推理的**输入图像集合**，而不只是其参考帧；给每一个拟留出帧提供 RGB SHA 级去重、旧源污染和 GT 隔离断言。
3. 验证裁剪、undistort、resize 的实际投影数值：`depth_z` 为光轴 Z，`c2w` 平移与深度单位必须同步 mm↔m；由冻结相机投影已知 Ring CAD 得到正常深度次序。
4. 环境只读检查 GPU 驱动、PyTorch/CUDA 最小张量、显存/磁盘/权重缓存、license；不能更改 NVIDIA 驱动或静默 CPU 回退。
