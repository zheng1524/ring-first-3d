# TASK-E4-RING-CROSS-VIDEO-018-REPAIR — FINAL_REPORT

```
CONTROLLED_GEOMETRY:        PASS
YAW_SOLVER:                 VALID
REAL_SAME_VIDEO_CONTROL:    PASS
CROSS_VIDEO_B_ACCEPT:       AMBIGUOUS  (consistent yaw 47.2°, MAD 1.29°, but match-level median 7.5 px)
CROSS_VIDEO_A_QUARANTINE:   UNEXPLAINED
CODE_AUDIT_PACKAGE:         COMPLETE
CROSS_VIDEO_CAMERA:         PARTIAL
BODY_CROSS_VIDEO_ADMISSION: NO
```

## 1. 修复的四个真实错误

1. **非法旋转矩阵**：018 的 `rig()` 合成出 det=−1 的镜像相机。现改为 `look_at()`（x=z×up, y=z×x, R=[x,y,z]），
   并对 3 组随机位姿断言 `RᵀR=I`、`det=+1`、所有点 `Z_c>0`。
2. **S5 控制变量顺序**：旧版先生成观测再挪相机。现在先按 bz 放置 B 组相机再投影。
3. **同视频误差符号**：改为 `e=|wrap(θ̂+α)|`，由真实脚本重算（不手改 CSV）。
4. **多解判断**：改为周期曲线 + 圆形聚类 + 分离判据 + `rise_away` 平坦度判据，
   不再把同一极小值的相邻网格点当成两个解。

## 2. 受控实验（`metrics/SYNTHETIC_RESULTS.csv`，3 seeds）

| case | 内容 | 结论 |
|---|---|---|
| S0 | 无噪声，θ=0/30/−120/179 | err = **0.000°**，status IDENTIFIABLE |
| S1 | 0.5 px | err ≤ 0.043° |
| S2 | 1.5 px | err ≤ 0.156° |
| S3 | 20% 错配 | err ≤ 0.057° |
| S4 | 50% 错配 | err ≤ 0.095° |
| S5 | 基线 b/Z 0.007–0.22 | err ≤ 0.038°，**仍可辨识**（见 §5 的坦白） |
| S6 | 匹配集中 | err = 0° |
| S7 | **法向分支错误** | err 112–166°，**status=DEGENERATE（正确拒绝）** |
| S8 | B 侧 K 翻倍 | err = 0°（每侧 K 传递正确） |

## 3. 真实同视频正对照（`metrics/REAL_SAME_VIDEO_CONTROL.csv`）

| α_GT | θ̂ | e=|wrap(θ̂+α)| | status |
|---|---:|---:|---|
| 0° | −0.055° | **0.055°** | IDENTIFIABLE |
| 30° | −30.055° | **0.055°** | IDENTIFIABLE |
| −120° | 119.945° | **0.055°** | IDENTIFIABLE |
| 179° | −179.055° | **0.055°** | IDENTIFIABLE |

负对照（打乱一侧对应）：θ=14.8°、**DEGENERATE**、inlier 3%、median 69 px → 求解器不会对错误对应给出高置信度。

## 4. 真实跨视频（`metrics/CROSS_VIDEO_RESULTS.csv`）

| 组 | 联合 θ | 每对 yaw 中位 | **MAD** | ±5° 内比例 | 匹配中位 | inlier3 |
|---|---:|---:|---:|---:|---:|---:|
| **B：004 ACCEPT ↔ 005** | 47.67° | **47.24°** | **1.29°** | **81.6%**（31/38） | 7.5 px | 21% |
| A：004 QUARANTINE ↔ 005 | 32.38° | 33.42° | 6.79° | 40% | 33.3 px | 8% |

**这是本轮的核心科学结果**：
- **B 组**：38 个独立图像对给出的 yaw 高度一致（MAD 1.29°、82% 在 ±5° 内），
  但**匹配级残差仍有 7.5 px**，说明背景匹配含大量重复纹理错配，精度受限。
  → 不是"yaw 解不出来"，而是"yaw 一致但匹配不够干净"。
- **A 组**：yaw 散乱（MAD 6.8°、仅 40% 在 ±5° 内、出现 155°/−144°/170° 的离群值），
  **不能用单一 yaw 分支解释**，前段存在更复杂的位姿错误。

## 5. 必须坦白的两点

1. **S5 的退化设计仍不成立**：绕 Ring 圆心的旋转本身产生弦长基线，缩放基线不会消除 yaw 的可辨识性；
   观测中 median 始终 ~0.33 px。真正的纯旋转退化条件是"相机中心在旋转轴上"。
   本轮没有重构该用例，标为 `DESIGN_FLAW`，不声称 S5 通过。
2. **B 组的 `status_joint=DEGENERATE`** 来自 Gate 的 `inlier3<25%` 判据；
   而 per-pair MAD 判据显示高度一致。两者不互相替代，同时报告。

## 6. 回答

- **Q1 非法旋转为何没被测试发现？** 018 的测试从未断言 det(R)=+1，只查了对极误差为零；现已加断言。
- **Q2 K 转换是否彻底修复？** 是；`geometry.fundamental` 唯一实现 `F=K₂⁻ᵀEK₁⁻¹`，S8（K 翻倍）err=0 验证。
- **Q3 正确构造的小视差会怎样？** 基线 0.007–0.22 仍可辨识（弦长基线），**未产生预期退化**——设计缺陷已记录。
- **Q4 真实同视频正对照是否通过？** **PASS**，四个角度全部 0.055°。
- **Q5 B 组是否存在一致 yaw？** **存在**：47.24° ± 1.29°（MAD），82% 的图像对支持。
- **Q6 A 组与 B 组差异？** A 组 yaw 散乱（MAD 6.8°），**不能**用单一 yaw 分支解释。
- **Q7 误差来源**：`MATCHING_ERROR`（B 组 7.5 px）+ `CAMERA_POSE_ERROR`（A 组）+ `YAW_MODEL_INSUFFICIENT`（A 组）；
  `SOLVER_ERROR` 已被受控实验排除。
- **Q8 审计包是否完整复现？** **是**：从 `/tmp/audit018` 干净解压后运行 `code/reproduce_offline.py`，
  B/A 的 yaw_median / MAD / frac 与上表逐位一致，且 `unittest` 11/11 通过。

## 7. 交付

`code/{geometry,yaw_solver,synthetic_cases,real_matches,reproduce_offline}.py`、`tests/`、
`config/experiment.json`、`fixtures/{camera_004,camera_005,same_video_matches,cross_video_*_matches}.npz`、
`metrics/*.csv`、`artifacts/TASK-E4-RING-CROSS-VIDEO-018-REPAIR_CODE_AUDIT.zip`。
