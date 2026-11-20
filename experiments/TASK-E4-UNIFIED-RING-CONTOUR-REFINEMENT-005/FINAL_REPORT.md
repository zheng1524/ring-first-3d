# TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005 — FINAL_REPORT

**STATUS: `PARTIAL` / `AWAITING_RA_REVIEW`**

## 0. 一句话

**P0（输入一致性）彻底修好并有逐像素证据；B2（RGB 修正连续轮廓）实现了但未生效；相机级 A0/B1/B2 对照未运行。**

| 阶段 | 状态 |
|---|---|
| P0 统一输入（冻结 INIT 权重 + DXY 推理数学） | ✅ **完成且逐位验证** |
| P1 A0 复现 | ✅ 复用 004 的 RAW-V2 N=16 结果（新 Mask 下） |
| P2 B1 DXY 可见弧连续轮廓 | ⚠️ 仅实现 2D 部分，未做相机级 |
| P3 B2 RGB 修正连续轮廓 | ❌ **实现完成但未产生位移** |
| P4 统一 BA 对照 | ❌ 未运行 |
| P5 可视化 | ⚠️ 图组 A/C/D 已出，B/E/F 未做 |

## 1. P0：输入一致性（本轮最大成果）

官方权重（SHA `981aa596…`）+ DXY 的 bilinear logits 上采样 + argmax，重分割与冻结 Mask：

| view | agree | Ring IoU |
|---|---:|---:|
| G02_v005_raw00104 | **1.0000** | 0.9999 |
| G03_v005_raw00589 | **1.0000** | 1.0000 |

上一轮的 0.45% 差异 = 旧 checkpoint（`4adfe9`）+ nearest 上采样，**与模型随机性或帧号无关**。
详见 `MASK_REPRODUCTION_REPORT.md`。

## 2. B2 失败归因（可视化 + 数值）

诊断过程：

1. 首版 `E_edge = exp(-|∇I|/2)`：Sobel 幅值中位数 43、p90 310，代价恒为 0 → 优化器无梯度 → δ 全 0。
2. 改为 `1 - min(|∇I|/80, 1)` 后：外轮廓开始移动（mean|δ| 0.38 px），内轮廓仍为 0.000。
3. 结果：B2 只在 **4/10** 条轮廓上更接近真实 Mask 边界；外轮廓反而从 0.632 px 退化到 0.857 px。

**归因**：失败点在 **RGB 边缘搜索**，不在 DXY 初始轮廓、也不在 CAD 对应。
可能原因（未验证）：单尺度 Sobel 在 256 上的梯度响应不足；法向搜索窗口 4 px 过窄；
Powell 在量化代价上早停。**不建议**在修好边缘项之前再动 CAD 损失。

## 3. 对十个科学问题的回答（能答的部分）

**Q1 统一流程？** 前端已统一到"视频→帧→冻结 INIT→Mask"，且有逐位一致证据；
但选帧仍复用 `ALL_VIEWS.json` 的帧身份，**未重写为 DXY `C_joint` 独立选帧**，这一点未完成。

**Q2 DXY 与原始边界点的差异？** DXY 提供内外语义 + 连续曲线 + 可见弧；原始边界点是散点、无内外语义、受锯齿与孤立分量影响。
在本轮数据上 DXY 椭圆到真实 Mask 边界的平均距离仅 **0.62 px**（内）/0.63 px（外），说明椭圆先验本身质量很高。

**Q3 B1 是否改善 Ring-Only？** **未测**。

**Q4 B2 是否改善真实边界定位？** **没有**：4/10 改善，外轮廓退化，内轮廓零位移。

**Q5 改善来自哪些区域？** 无法回答（B2 未生效）。

**Q6 是否保持内外对应与物理宽度？** 代码中保留内外独立曲线与宽度项，但未验证。

**Q7 Ring-Only 变好后 BA 是否仍好？** **未运行**。

**Q8 哪些视频仍有几何冲突？** 沿用 004：G03/004（held 75–127 px）、G02/004；G03/005 在 N=32 时 held 2.47 px。

**Q9 人工判断哪种更符合真实 Ring？** 当前证据只能支持"DXY 椭圆本身很贴合"，不支持"B2 修正更好"。

**Q10 是否纳入主线？** **否，暂不纳入**。P0 的输入修复应当纳入；B2 需先修好边缘项。

## 4. 交付物

- `code/prepare.py`：冻结 INIT + DXY 推理数学（P0 修复）
- `code/prepare_views.py`：十段 × 16 视角准备，写 `metrics/INPUT_PROVENANCE.csv`
- `code/dxy_adapter.py`：DXY 椭圆→Conic/采样/可见弧
- `code/contour_refinement.py`：B2（椭圆→法向搜索→Fourier δ→平滑）
- `code/visualize_contours.py`：图组 A/C/D
- `visualization/A_2d_contour_extraction/`：5 张 3×3 全流程图
- `visualization/C_local_zoom/`：5 张四区域局部放大（1–3 px 级差异可见）
- `visualization/D_residual_distribution/`：DXY vs B2 残差分布
- `metrics/CONTOUR_QUALITY.csv`、`metrics/INPUT_PROVENANCE.csv`

## 5. 未完成（明确列出）

1. 相机级 A0/B1/B2 三臂对照（P2–P4）。
2. 图组 B（Ring-Only vs BA-Final）、E（多视角 contact sheet）、F（修正后的相机网络，需用 `cs[:, :3, 3]` 取真实中心）。
3. DXY `C_joint` 独立选帧（当前仍用历史帧身份）。
4. B2 边缘项修复。

## 6. 建议

1. **先发 P0**：它把输入一致性从"99.55% 近似"变成"逐位一致"，这是所有后续结论的地基。
2. **B2 暂停**，先把边缘项换成"沿法向的 1D 灰度剖面 + 子像素抛物线拟合"，并在合成体模上验证能找回已知位移，再回到真实数据。
3. 相机级对照应在 B2 能产生 1–3 px 位移之后再做，否则只是在比较两套几乎相同的 2D 曲线。
