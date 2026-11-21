# TASK-E4-RING-CROSS-VIDEO-018 — FINAL_REPORT

```
CONTROLLED_YAW_SOLVER:  VALID
CODE_AUDIT_PACKAGE:     COMPLETE
RING_CROSS_VIDEO_ALIGNMENT: AMBIGUOUS
G03_CROSS_VIDEO:        BLOCKED
G03_004_DENSE_CAMERA:   BLOCKED (未执行)
G03_005_DENSE_CAMERA:   BLOCKED (未执行)
BODY_CROSS_VIDEO_ADMISSION: NO
```

## 0. 最重要的一句话

**017 的"loss≈22/25、所有匹配都是外点"是一个实现 bug：构建 Fundamental 矩阵时漏掉了 `F = K₂⁻ᵀ E K₁⁻¹`，直接把 E 当 F 用在像素坐标上。**
修复后受控实验 S0 的 loss **精确为 0**，真实同视频对照误差 **0.055°**。

## 1. 受控实验（`metrics/SYNTHETIC_GROUND_TRUTH.csv`）

| case | 设置 | θ_GT | θ̂ | 误差 |
|---|---|---|---:|---:|
| S0 | 无噪声 | 0 / 30 / −120 / 179 | 0 / 30 / −120 / −181 | **0.000°** |
| S1 | 0.5 px | 30 / −120 | 29.975 / −120.019 | 0.02–0.03° |
| S2 | 1.5 px | 30 / −120 | 29.972 / −120.048 | 0.03–0.05° |
| S3 | +20% 错配 | 30 / −120 | 30.022 / −120.028 | 0.02–0.03° |
| S4 | +50% 错配 | 30 / −120 | 30.012 / −120.017 | 0.01–0.02° |
| **S5** | **极小视差 0.05×** | 30 / −120 | 9.2 / −44.3 | **20.8° / 75.7°** |
| S6 | 匹配集中 | 30 / −120 | 30.000 / −120.000 | 0.000° |

S5 是**唯一失败**的用例，且求解器**正确标记 `ambiguous=True`、inlier 8%/5%**——
这正是任务要求的"退化必须被检出，而不是给一个角度"。

（S0 的 179° 返回 −181°，`wrap₁₈₀` 后误差为 0。）

## 2. 真实同视频正对照（`metrics/REAL_SAME_VIDEO_CONTROL.csv`）

用 **005 的真实 W0 相机 + 真实 SIFT 轨迹**，人为把 A 子网络旋转 α，要求解出逆变换：

| α_GT | θ̂ | 与真值误差 |
|---|---:|---:|
| 0° | −0.055° | **0.055°** |
| 30° | −30.055° | **0.055°** |
| −120° | +119.945° | **0.055°** |

**求解器在真实数据噪声下也是正确的**（误差 ≈0.06°，远好于 2° 网格，说明局部精修有效）。

## 3. 真实跨视频（`metrics/CROSS_VIDEO_RESULTS.csv`）

修正 F 后，对 16 对 004↔005 真实匹配：

| 指标 | 值 |
|---|---:|
| 最优 yaw | 46.16° |
| loss | 7.59 |
| **Sampson 中位** | **28.87 px** |
| 内点比例（<3 px） | **14%** |
| 截断饱和比例 | 77% |
| 多峰 | **是**（46/48/42/44/40° 近等价） |

**结论：即使求解器已被证明正确，真实 SIFT 匹配本身也不满足跨视频对极几何。**
这不是 yaw 不可解，而是**匹配是错的**（背景为重复纹理）。

→ `RING_CROSS_VIDEO_ALIGNMENT = AMBIGUOUS`，`G03_CROSS_VIDEO = BLOCKED`。

## 4. 回答

- **Q1 017 高损失的真实原因？** 缺 `K` 归一化：`E` 被直接当 `F` 用。修正后 S0 loss=0、真实同视频误差 0.055°。
- **Q2 受控求解器是否有效？** **VALID**（S0/S1/S2/S3/S4/S6 全部 <0.06°，S5 正确判退化）。
- **Q3 真实跨视频能否辨识 yaw？** **不能**：中位 28.9 px、内点 14%、多峰。
- **Q4 004 前段是否错误分支？** 仍**不能**由本轮证据断定（匹配无效，检验不了分支假设）。
- **Q5 能否建立统一坐标？** **否**。
- **Q6 逐帧相机？** **未执行**（跨视频未通，先做逐帧会产出无法合并的坐标系）。按任务纪律标 BLOCKED，不伪造覆盖数字。

## 5. 交付

`code/{yaw_solver,synthetic_yaw}.py`、`tests/test_yaw_solver.py`（4/4 通过）、
`metrics/{SYNTHETIC_GROUND_TRUTH, REAL_SAME_VIDEO_CONTROL, CROSS_VIDEO_RESULTS, CROSS_VIDEO_PAIRS}.csv`、
`artifacts/TASK-E4-RING-CROSS-VIDEO-018_CODE_AUDIT.zip`（源码 + 测试 + fixtures + 结果 + 复现说明）。

## 6. 下一步（唯一路径，与 017 结论一致但理由更强）

跨视频不能靠 pairwise SIFT：必须先在 005 内部建立**多视图描述子身份**（≥3 视图一致），
三角化背景点，再对 004 逐视角做 2D–3D PnP。本轮的求解器可直接用于验证 PnP 候选的 yaw 一致性。
