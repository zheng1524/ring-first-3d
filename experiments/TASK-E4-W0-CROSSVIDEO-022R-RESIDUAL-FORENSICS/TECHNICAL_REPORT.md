# TASK-E4-W0-CROSSVIDEO-022R — G03 真实残差取证（只读）

**基准**：`audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT` @ `af906677`；优化程序 021 @ `bfd9c622`。
**性质**：可视化取证，不是 023 修复；未改动 H、W0、匹配、门限、目标函数。

---

## 0. 结论摘要（先给答案）

1. **数值完全可复现**：96 对、3749 点、median **4.593439877 px**、p95 **156.10182 px**、`>50 px` **0.16617765**，
   与 022 记录逐位一致（`runs/G03/SUMMARY.json`）。
2. **`raw00114` 不是异常帧**。按该帧匹配总数归一：n=**301**（16 帧中最多）、median 3.64 px、
   `>50 px` **14.6%**、排名 **12/16**；参照帧 00099 为 7.8%、00128 为 11.8%、00142 为 15.4%。
   022 里"raw00114 出现 4 次"是**点级** top-5，不是帧级异常；不能据此判帧坏。
3. **长尾的主要来源是跨视频几何（相机/H），不是单段相机，也不是纯匹配噪声**：
   同一批匹配用 `F_pose`（W0 + 021 H）中位 **4.66 px**，用图像自估 `F_img`（MAGSAC）中位 **0.82 px**；
   **96/96 对**都是 `F_img` 更好，78.3% 的点在 `F_img` 下更小。
   而这些帧的单段 W0 质量都很好（held median 0.96–1.69 px，全部 ACCEPT）。
4. **匹配确有质量问题**：重新提取 SIFT 后，存储匹配中只有 **46–68%** 是双向 mutual；
   MAGSAC 内点率中位 **0.62**（即约 38% 不属于任何单一 F）。这解释了 >200 px 的极端点。
5. **低视差被排除**：96 对基线 15.6–29.6 mm，没有 <5 mm 的对；基线与 `>50 px` 比例正相关（+0.53），
   与"视差越小越差"的预期相反。

---

## 1. S0 输入与校验

| 输入 | SHA256（前 16） |
|---|---|
| `021/runs/G03/MATCHES.npz` | `05e05327f86b98ec` |
| `021/runs/G03/RESULTS.json` | `f0dffc578550af81` |
| `021/runs/G03/SPLIT.json` | `42a07a4418d8982b` |
| `camera_mainline/G03/video004/camera_result.npz` | `56fbdaee0e718e86` |
| `camera_mainline/G03/video005/camera_result.npz` | `ba8b1f83376e17eb` |
| `PREPARED G03_004` / `G03_005` | `a4e4f0bcc663ca9c` / `8688f4c01399d9ba` |

脚本在 `F_pose` 重建后会与 021 官方 `shared_se3.sampson_px` 逐点比对，若差 >1e-5 直接报错（实际未触发）。

## 2. S1 逐点重算

`point_residuals.csv`（3749 行）：004/005 view、两端 (u,v)、官方 Sampson、两端点到极线距离、FIT/HOLDOUT、误差分层。
`pair_residuals.csv`（96 行）：每对 n/median/p90/p95/max/`>50`/`<3` 比例、基线、MAGSAC 内点率。
`frame_residuals.csv`：逐帧（004/005）统计；`frame_residuals_normalised_005.csv` 增加匹配数与排名。

说明：`frame_residuals.csv` 的 `video` 列被 pandas 读成整数 4/5（CSV 写成 `004/005`），仅编码问题，不影响数值。

## 3. S2 四类真实图（均已实际生成，非模板）

| 文件 | 内容 | 关键读数 |
|---|---|---|
| `01_pair_error_heatmap.png` | 96 对：左=每对中位误差，右=`>50 px` 比例 | 高误差分散在多数 004×005 组合，非个别帧 |
| `02_residual_distribution.png` | 全 3749 点长尾分布（保留到最大） | 中位 4.59、p95 156.1、>50 占 16.6% |
| `03_epipolar_examples.png` | 4 个误差等级各 1 个真实点，双图 + 极线 + 垂足 | 单侧点线距离与 Sampson 不同量 |
| `04_error_spatial_overlay_005.png` | 6 个 005 帧的真实 RGB + 误差分级散点 | 高误差点散布，未见单一区域聚集 |
| `05_Fpose_vs_Fimg_epipolar.png` | 4 对焦点：青=`F_pose`、洋红虚线=`F_img` | 两族极线明显不重合 |
| `pair_montages/*.png` | 6 对真实匹配连线（颜色=误差分层） | 线长≠误差，仅表示匹配身份 |

图非空白已用像素统计核验（std 46–104，unique rows 286–216 k）。

## 4. S3 四类独立对照

### A. 匹配本身（`mutual_consistency.csv`）

| 004 ↔ 005 | 存储匹配 | mutual 比例 | 重提取后的 mutual 数 |
|---|---:|---:|---:|
| raw00242 ↔ raw00114 | 42 | 59.5% | 31 |
| raw00263 ↔ raw00114 | 45 | 53.3% | 32 |
| raw00304 ↔ raw00114 | 41 | 68.3% | 34 |
| raw00242 ↔ raw00099 | 44 | 59.1% | 31 |
| raw00242 ↔ raw00128 | 54 | 50.0% | 35 |
| key02_raw00327 ↔ raw00215 | 35 | 45.7% | 23 |

→ 约 **1/3–1/2** 的存储匹配不是双向 mutual；`cross_video_matches.py` 只做 ratio+Mask，没有 mutual。

### B. 相机几何（`F_pose_vs_F_img.csv`）

| 指标 | 值 |
|---|---:|
| 每对 `F_pose` 中位的中位 | **4.664 px** |
| 每对 `F_img` 中位的中位 | **0.818 px** |
| `F_img` 更好的对数 | **96 / 96** |
| 点在 `F_img` 下更小的比例（中位） | **78.3%** |
| MAGSAC 内点率（中位） | **0.617** |
| 基线与 `>50 px` 相关 | +0.53 |
| 基线与中位误差相关 | +0.32 |

**必须同时说明反证**：`F_img` 是在同一批点上拟合的（7 DoF + 稳健剔除），天然比固定 6-DoF 的 H 更贴合，
所以 0.82 px **不能**当作"真值"。但它证明：这些匹配**能够**由单一 F 以亚像素解释，
而 `F_pose` 不能 —— 因此把长尾全部归因于"SIFT 错配"是不成立的。

### C. 退化/遮挡

- 基线 15.6–29.6 mm，**无低基线对**；无纯旋转退化。
- 空间叠加图（04）显示高误差点分散，未见集中于 Ring/息肉边界的单一区域；Mask 标签未参与定量归因 → 该项 `PARTIAL`。
- 最大误差点多在图像边缘/低纹理区（见 pair montages），与 SIFT 边缘响应一致。

### D. 是否单帧问题（`frame_residuals_normalised_005.csv`）

| 005 帧 | n | median | p95 | `>50` | 排名 |
|---|---:|---:|---:|---:|---:|
| raw00186 | 222 | 6.22 | 251.5 | **29.3%** | 1 |
| raw00287 | 133 | 4.80 | 173.7 | 25.6% | 2 |
| raw00215 | 201 | 5.03 | 184.8 | 22.4% | 3 |
| **raw00114** | **301** | 3.64 | 192.0 | **14.6%** | **12** |
| raw00099 | 309 | 2.66 | 83.2 | 7.8% | 16 |
| raw00128 | 330 | 3.95 | 121.6 | 11.8% | 13 |

→ `raw00114` 匹配最多、比例居中，**不是坏帧**。

### E. W0 质量对照（`W0_quality_crosscheck.csv`）

焦点帧全部 `ACCEPT`，单段 held median 0.96–1.69 px、held p95 2.7–7.8 px。
**单段相机好、跨段误差大** —— 指向跨视频几何而不是单段相机。

## 5. 根因分类（证据 + 反证）

| 类别 | 证据 | 反证/限制 | 判定 |
|---|---|---|---|
| **CAMERA_GEOMETRY / CROSS_VIDEO_H** | `F_img` 0.82 vs `F_pose` 4.66 px；96/96 对；单段 held 1–2 px | `F_img` 同数据拟合，非真值；未定位是 H 的旋转还是 004 局部位姿 | **主因（高置信）** |
| **MATCHING_ERROR** | mutual 仅 46–68%；MAGSAC 内点 62%；>200 px 极端点 | 极端点只占少数，解释不了 4–15 px 的系统偏移 | **次因（确定存在）** |
| **LOW_PARALLAX_OR_DEGENERACY** | — | 基线全部 ≥15.6 mm；基线与误差正相关 | **排除** |
| **MASK_OR_OCCLUSION** | 未做 Mask 标签定量归因 | 空间图未见明显聚集 | **PARTIAL / UNRESOLVED** |
| **IMPLEMENTATION_OR_PROVENANCE** | 022 已证实 004 侧留出泄漏、K 硬编码（本数据 K 相同） | 不直接产生长尾 | **与残差无直接因果** |
| **UNRESOLVED** | 3–15 px 系统偏移的确切来源（H 的旋转分量？两段视频时间/场景不对应？） | 需要 023 的双向 3D 地标才能定位 | **保留** |

## 6. 对 023 的建议（仅建议，未实施）

1. 用 mutual + MAGSAC 重筛匹配（**只用于诊断对照**，不回填 021），再比较 `F_pose` 与 `F_img` 的差距是否缩小。
2. 优先核查 `H` 的旋转分量：3–15 px 的系统偏移在小基线下对旋转极敏感；用 023 的多视角 3D 地标给出独立约束。
3. 复核 004 与 005 的**时间/场景对应**（两段视频是否是同一静态场景的同一时刻），这是 `F_img` 与 `F_pose` 系统不一致的另一种可能。
4. 保留长尾：不得为提高指标删除 >50 px 点。

## 7. 复现

```bash
cd /home/liu/ring_first_3d_workspace
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
$PY experiments/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS/tools/inspect_epipolar_residuals.py \
   --root /home/liu/ring_first_3d_workspace --group G03 \
   --out experiments/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS/runs/G03
$PY experiments/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS/tools/forensic_extra.py
```
