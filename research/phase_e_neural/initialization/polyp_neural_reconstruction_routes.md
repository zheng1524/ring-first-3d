# 面向执行模型的技术路线提示词：NeRF / NeuS / 3DGS 在带参照环息肉三维重建中的应用

## 任务背景

当前项目是一个带参照橡胶圈的消化道息肉三维重建与硬尺度恢复任务。已有数据包括：

- 有环数据：息肉 + 橡胶圈固定不动，多视角图片或视频关键帧；
- 无环数据：部分息肉在无橡胶圈遮挡条件下采集；
- 已完成的 2D 分割结果：`polyp mask`、`ring mask`；
- 已完成或正在完善的橡胶圈椭圆拟合、ring scale 恢复和 ring pose 估计；
- 对应的 Blender / mesh / voxel / SDF 类三维 GT；
- 当前 supervised SDF / voxel 模型中出现明显的浮空、上下断裂、层状碎片、遮挡区域缺失、mesh 多面体感等问题。

核心判断：当前问题不是单纯训练不足，而是“橡胶圈遮挡 + 粗 GT + 缺少真实多视角表面约束”共同导致的。因此，应尝试引入 NeRF / NeuS / VolSDF / 3D Gaussian Splatting 等多视角神经重建技术，作为 per-capture-group 的真实三维 teacher 或数据质量诊断工具。

---

## 0. 总体目标

请执行模型围绕以下目标开展工作：

1. 对每个 `capture_group` 单独进行多视角神经重建实验；
2. 比较 COLMAP/MVS、NeRF、NeuS/VolSDF、3DGS/Splatfacto 等不同方法；
3. 优先解决当前预测中的“浮空”“上下断裂”“遮挡导致缺失”问题；
4. 将橡胶圈作为尺度与遮挡先验，而不是简单背景；
5. 将无环数据用于学习完整形态，将有环数据用于学习遮挡补全；
6. 最终输出息肉 mesh、点云或 SDF，并恢复到毫米坐标系；
7. 生成可反向监督主模型的高质量 teacher GT。

---

## 1. 方法定位

不要把 NeRF 系列简单看成“替代当前模型”的方法。在本任务中，推荐将不同方法定位如下：

```text
COLMAP / OpenMVG / MVS
    → 传统几何基线，相机位姿、点云、尺度诊断

Nerfacto / vanilla NeRF
    → 图像一致性 teacher，新视角渲染验证

NeuS / VolSDF / SDFStudio
    → 表面重建主路线，适合生成 mesh 和毫米指标

3D Gaussian Splatting / Splatfacto
    → 快速重建预览与数据质量筛查

SuGaR / 2DGS
    → 从 Gaussian Splatting 进一步提取 mesh 的补充路线

pixelNeRF / few-view NeRF
    → 后期跨样本泛化模型，不建议当前最先做
```

---

## 2. 数据准备要求

### 2.1 每个 capture_group 至少应包含

```text
capture_group/
├── views/
│   ├── v000_anchor.jpg
│   ├── v001_kf01.jpg
│   ├── v002_kf02.jpg
│   └── ...
├── masks_polyp/
│   ├── v000_polyp.png
│   └── ...
├── masks_ring/
│   ├── v000_ring.png
│   └── ...
├── masks_unknown/
│   ├── v000_unknown.png
│   └── ...
├── ring_fit/
│   ├── v000_ring_ellipse.json
│   └── ...
├── camera/
│   ├── intrinsics.json
│   ├── distortion.json
│   ├── colmap_sparse/
│   └── transforms.json
├── gt/
│   ├── mesh_clean.obj
│   ├── fixed64_mm64.npz
│   ├── tight64_pad10.npz
│   ├── sdf_samples.npz
│   ├── metrics_gt.json
│   └── gt_meta.json
└── group_meta.json
```

### 2.2 输入图像建议

每个 `capture_group` 推荐使用：

```text
1 张高质量 anchor photo + 3~7 张视频关键帧
```

关键帧筛选条件：清晰度高、息肉主体完整、橡胶圈可见且拟合稳定、相邻视角有重叠但不过度冗余、高光/模糊/遮挡较少、`ring mask` 与 `polyp mask` 质量较高。

### 2.3 坐标与尺度要求

所有重建结果最终必须恢复到：

```text
canonical_mm_space
```

尺度来源优先级：

```text
1. 橡胶圈几何恢复的 scale；
2. 多视角 BA 后的全局 scale；
3. Blender GT scale；
4. 模型 scale head 预测。
```

所有导出的 mesh / point cloud / SDF 均应带有单位说明：`unit = mm`。

---

## 3. Route 1：COLMAP / OpenMVG + MVS 传统几何基线

### 3.1 目标

建立传统几何基线，用于检查关键帧重叠、求解相机位姿、生成稀疏/稠密点云、为 NeRF / NeuS / 3DGS 提供初始相机位姿、检查尺度恢复是否稳定，并对失败样本进行诊断。

### 3.2 推荐流程

```text
关键帧筛选
→ 图像去畸变
→ COLMAP feature extraction
→ sequential matching 或 exhaustive matching
→ sparse reconstruction
→ ring scale alignment
→ optional dense MVS
→ point cloud / mesh export
```

### 3.3 输入

```text
views/
intrinsics.json
distortion.json
ring_fit/*.json
polyp_mask，可选
ring_mask，可选
```

### 3.4 输出

```text
camera/colmap_sparse/
camera/transforms.json
recon_colmap/sparse.ply
recon_colmap/dense.ply，可选
recon_colmap/scale_aligned.ply
```

### 3.5 成功标准

```text
1. 大部分图像注册成功；
2. 相机轨迹合理；
3. 稀疏点云覆盖息肉和周围区域；
4. ring 尺度对齐后，点云尺度合理；
5. 重投影误差不过大；
6. 失败样本可以被自动标记。
```

---

## 4. Route 2：Nerfacto / NeRF 图像一致性 teacher

### 4.1 目标

使用 NeRF / Nerfacto 检查多视角图像是否能被一个连续三维场景解释。它主要用于新视角渲染和图像一致性验证，不建议直接作为最终毫米级 mesh 测量方法。

### 4.2 推荐流程

```text
COLMAP poses 或 transforms.json
+ views
+ masks，可选
+ ring scale
    ↓
Nerfacto / NeRF 训练
    ↓
novel view rendering
    ↓
渲染质量评估
    ↓
可选 density-to-mesh
```

### 4.3 注意事项

NeRF 的密度场不是天然干净表面。直接从 density 提取 mesh 可能出现雾状密度、厚壳、浮空、碎片、表面不清晰。因此，NeRF 更适合作为图像一致性 teacher，而不是最终表面测量主方案。

### 4.4 输出

```text
recon_nerf/
├── renders/
├── train_log.json
├── eval_metrics.json
├── density_field，可选
└── mesh_from_density.obj，可选
```

---

## 5. Route 3：NeuS / VolSDF / SDFStudio 表面重建主路线

### 5.1 目标

这是当前最推荐的神经重建主路线。原因是：目标是显式恢复连续表面，更适合导出 mesh，更适合计算体积、直径、表面积，可与 SDF GT 对接，也比 vanilla NeRF 更适合医学形态测量。

### 5.2 推荐输入

```text
views/
transforms.json 或 COLMAP poses
intrinsics.json
polyp masks
ring masks
unknown masks
ring scale
optional ring pose
optional Blender / SDF GT
```

### 5.3 关键设计：masked / occlusion-aware NeuS

训练时应区分：

```text
visible_polyp
visible_background
visible_ring
unknown_occluded_by_ring
```

其中：

```text
visible_background 可以作为负样本；
unknown_occluded_by_ring 不作为 background 负样本；
ring 区域不应强迫 polyp shape 为空。
```

### 5.4 推荐流程

```text
每个 capture_group
    ↓
准备 transforms.json
    ↓
准备 polyp mask / ring mask / unknown mask
    ↓
训练 NeuS / VolSDF / SDFStudio
    ↓
导出 SDF mesh
    ↓
ring scale 对齐到 mm space
    ↓
计算形态指标
    ↓
与 Blender GT / supervised model 结果对比
```

### 5.5 输出

```text
recon_neus/
├── mesh_raw.obj
├── mesh_scale_aligned.obj
├── sdf_field.npz，可选
├── render_eval/
├── metrics_mm.json
├── component_stats.json
└── preview/
```

### 5.6 评价指标

```text
1. 是否单连通；
2. num_components；
3. largest_component_ratio；
4. floating_component_volume_ratio；
5. max_diameter_error_mm；
6. volume_error_mm3；
7. surface_area_error_mm2；
8. Chamfer distance，可选；
9. surface distance，可选；
10. novel view PSNR / SSIM / LPIPS，可选。
```

---

## 6. Route 4：3D Gaussian Splatting / Splatfacto 数据质量筛查

### 6.1 目标

使用 3DGS / Splatfacto 快速判断每组数据是否适合三维重建。它适合快速预览、数据质量筛查、新视角可视化和粗几何检查，不建议直接作为最终体积测量方法。

### 6.2 推荐流程

```text
COLMAP poses
+ views
    ↓
Splatfacto / 3DGS 训练
    ↓
novel view rendering
    ↓
检查是否存在碎片、高斯漂浮、视角不一致
    ↓
标记数据质量
```

### 6.3 如果 Splatfacto 失败，优先检查

```text
1. COLMAP 位姿是否错误；
2. 关键帧是否太少；
3. 视角跨度是否太小或太大；
4. 图像是否模糊；
5. 高光是否严重；
6. ring 是否遮挡过强；
7. 背景是否变化；
8. 同组内物体是否真的固定不动。
```

### 6.4 输出

```text
recon_3dgs/
├── splat.ply
├── renders/
├── eval_metrics.json
├── data_quality_score.json
└── preview.mp4
```

---

## 7. Route 5：SuGaR / 2DGS 从 Gaussian 到 mesh

### 7.1 目标

如果 3DGS 渲染效果很好，但缺少可测量 mesh，可以进一步尝试 SuGaR 或 2D Gaussian Splatting，从 Gaussian 表示中提取更适合几何测量的表面。

### 7.2 推荐流程

```text
3DGS / Splatfacto 训练结果
    ↓
SuGaR 或 2DGS
    ↓
mesh extraction
    ↓
ring scale alignment
    ↓
形态指标计算
```

### 7.3 输出

```text
recon_sugar/
├── mesh_raw.obj
├── mesh_scale_aligned.obj
├── metrics_mm.json
└── component_stats.json
```

---

## 8. Route 6：few-view NeRF / pixelNeRF 后期泛化路线

### 8.1 定位

不建议当前最先实现。这类方法更适合在已有大量高质量 teacher 后，再训练跨样本的 feed-forward 模型。

### 8.2 使用条件

只有当满足以下条件后再尝试：

```text
1. 已经有足够多 capture_group；
2. 每组已有可靠 NeuS / VolSDF / 3DGS teacher；
3. 数据 split 已按 specimen 分组，避免泄漏；
4. 每个样本已有统一 canonical mm space；
5. 有足够多不同分型、大小、形态的数据。
```

### 8.3 目标

```text
输入：1 anchor + 3~7 keyframes
输出：SDF / mesh / tight shape + scale
监督：teacher mesh / Blender GT / SDF samples
```

---

## 9. 推荐实验优先级

### 优先级 1：COLMAP + ring scale 基线

目标：验证相机位姿和尺度恢复是否可靠。

交付：`transforms.json`、稀疏/稠密点云、scale alignment、注册成功率报告、失败样本列表。

### 优先级 2：Splatfacto 快速数据质量筛查

目标：快速判断哪些 `capture_group` 适合多视角神经重建。

交付：每组 novel view preview、每组 `data_quality_score`、失败原因分析、推荐进入 NeuS 的 group 列表。

### 优先级 3：Masked NeuS / VolSDF 主实验

目标：生成可测量的连续 polyp mesh。

交付：`scale_aligned mesh`、毫米指标、浮空组件统计、与 GT/当前模型的对比图、是否解决浮空问题的结论。

### 优先级 4：有环 / 无环 teacher consistency

目标：利用无环数据补全有环遮挡区域。

交付：ring-free teacher mesh、ring-present masked teacher mesh、二者在 canonical mm space 下的 shape distance、diameter / volume / surface area consistency、是否能作为有环训练监督的判断。

### 优先级 5：SuGaR / 2DGS mesh 补充路线

目标：在 3DGS 渲染良好的样本上尝试提取 mesh。

交付：SuGaR / 2DGS mesh、与 NeuS mesh 对比、与 Blender GT 对比、是否适合作为 teacher 的判断。

---

## 10. 与现有 supervised 模型的融合方式

神经重建结果不应孤立使用，而应反过来增强当前主模型。

推荐融合方式：

```text
Blender GT
    提供完整形状、绝对指标、分型先验

NeuS / VolSDF teacher
    提供真实拍摄条件下的连续表面

3DGS / Splatfacto
    提供数据质量筛查和快速可视化

ring geometry
    提供硬尺度和遮挡解释

ring-free data
    提供无遮挡完整形态先验

ring-present data
    提供真实任务输入条件
```

主模型训练时可使用：

```text
L_total =
L_blender_shape
+ L_teacher_shape
+ L_scale_ring
+ L_ring_free_consistency
+ L_connectivity
+ L_smooth
```

---

## 11. 输出指标规范

所有路线都应尽量输出统一指标。

### 11.1 几何质量

```text
num_components
largest_component_ratio
floating_component_count
floating_component_volume_ratio
hole_count，可选
surface_smoothness，可选
```

### 11.2 尺度误差

```text
max_diameter_error_mm
volume_error_mm3
surface_area_error_mm2
planar_major_error_mm
planar_minor_error_mm
```

### 11.3 与 GT 的形状距离

```text
voxel IoU
Dice
Chamfer distance
normal consistency，可选
surface distance，可选
```

### 11.4 图像重建质量

```text
PSNR
SSIM
LPIPS
render_mask_iou，可选
```

### 11.5 有环/无环一致性

```text
diameter_diff_ring_vs_free
volume_diff_ring_vs_free
surface_area_diff_ring_vs_free
shape_distance_ring_vs_free
```

---

## 12. 推荐最终落地版本

如果只实现一个版本，优先实现：

```text
COLMAP + ring scale
→ Splatfacto 数据质量筛查
→ Masked NeuS / VolSDF 表面重建
→ ring-free / ring-present consistency
→ teacher mesh 反向监督主模型
```

简写为：

```text
Route-NeuS-Teacher-v1
```

---

## 13. 执行模型需要交付的文件

请生成以下内容：

```text
1. prepare_colmap_inputs.py
2. run_colmap_and_scale_align.py
3. prepare_nerfstudio_or_sdfstudio_data.py
4. generate_unknown_masks_from_ring.py
5. run_splatfacto_quality_check.sh 或 .py
6. run_neus_or_volsdf_reconstruction.sh 或 .py
7. export_scale_aligned_mesh.py
8. compute_mesh_metrics_mm.py
9. compute_component_stats.py
10. compare_ring_free_and_ring_present_teachers.py
11. build_teacher_manifest.py
12. README.md
```

---

## 14. 最终结论

对于本任务，可以尝试辐射神经场，但不建议优先使用 vanilla NeRF 作为最终测量方法。更推荐的路线是：

```text
Masked NeuS / VolSDF
    作为可测量表面重建主路线；

Splatfacto / 3DGS
    作为快速数据质量筛查和可视化路线；

SuGaR / 2DGS
    作为 Gaussian-to-mesh 补充路线；

COLMAP + ring scale
    作为位姿与尺度基线；

Blender GT + 无环数据
    作为完整形态先验；

有环数据 + ring unknown mask
    作为真实任务遮挡条件。
```

一句话概括：

> 不要把 NeRF 当成单纯替代体素模型的黑箱；应把 NeuS/VolSDF/3DGS 作为每个 capture group 的真实多视角 teacher 生成器，用它们补足 Blender GT 的生硬感，并结合橡胶圈尺度与无环数据，解决有环遮挡导致的浮空和断裂问题。
