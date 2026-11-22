# TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE — 技术报告

```
Gate A Ring 数据正确:        PASS（22/22 真实 centerline；C 1.8339→0.1397）
Gate B 位姿数学正确:         PASS（T1–T6，矩阵差 7.1e-15；端到端损失等价 ≤1.2e-5）
Gate C 三角化身份正确:       PASS（稳定键；存活率 41–100%；负对照 1e-6 mm）
Gate D 真实 G03 复验:        PASS（22 视角 Ring、H025 重评、身份/距离、026 结论逐条裁定）
JOINT_OPTIMIZATION:          NOT_EXECUTED（只有 BLOCKED 记录，无优化）
CROSS_VIDEO_GEOMETRY_ACCEPT: NO
BODY_CROSS_VIDEO_ADMISSION:  NO
```

## 1. 四个缺陷都已修复并有用例

| 缺陷 | 旧行为 | 新行为 | 测试 |
|---|---|---|---|
| D1 centerline=inner | C 中位 1.8339 | C 中位 **0.1397**，22/22 视角 C≠I | `TestCenterline` |
| D2 重复施加 H | H025 Ring **178.7** | 传增量；H025 Ring **1.0349** | T1–T6 + 端到端损失等价 |
| D3 扰动方向 | 世界轴 45° → 54.2（实为局部旋转） | 世界轴 0–45° 恒 **0.1632** | `TestPerturbationDirection` |
| D4 行号错配 | 0.5° → 10–38 mm | 稳定键 p50 **0.99 mm**、p90 7.52 | `TestTrackIdentity` |

`tests/test_defects.py` **4/4 通过**；每个测试都显式复现旧行为并断言其失败方式。

## 2. 修复后的真实数值

**Ring（22 个 ACCEPT 视角，配置 A：MIO）**：M 0.0927、I 0.1001、C 0.1397、O 0.2845 → **MIO 0.1617**；
配置 B（MICO）0.1691。

**H025**：MIO **1.0349**（004 1.1379 / 005 1.0269），基线 0.1617 → 6.4×。
旧 178.7 标记 `INVALIDATED_BY_POSE_COMPOSITION_BUG`。

**可辨识性**：世界 Ring 轴旋转 0–45° MIO 恒 0.1632（严格对称）；
相机局部 yaw 1°→0.236、5°→0.661、15°→1.908、45°→5.701。

**三角化**：共同模式 100% 存活、距离变化 ~1e-6 mm；005 独立 0.5° 存活 **41%**、
位移 p50 **0.99 mm**、p90 7.52、max 45.8；12 身份中 3/12 仍可评价（3 对）。

**66 对距离**：中位 3.896、p90 6.694、max 9.792 mm（三角化，非真值）。

## 3. 十个问题

**Q1** 因为适配器把 `centerline` 写成 `inner`（语义重复），C 变成"再测一次 Inner"且被 CAD 中心线惩罚；
修复后 C 中位 **1.8339 → 0.1397**。

**Q2** 是。真实 I/O 下 M 0.093 / I 0.100 / O 0.285（Huber/3），对应亚像素级真实距离；
H025 使其升到 I 1.29 / O 1.55，仍能区分正确与错误位姿。

**Q3** **1.0349**（MIO），不是 178.7。旧值由重复施加 H 产生，已撤回。

**Q4** 世界 Ring 轴旋转：**完全不变**（0.1632，0–45°）；相机局部旋转：5° 约 4×、45° 约 35×；
平移 0.1–0.5 mm 见 CSV（亚毫米即有明显响应）。必须区分两者——026 把局部旋转当成了 Ring 法向 yaw。

**Q5** 修复身份后，0.5° 独立相对扰动使同轨迹三维位置位移 **中位 0.99 mm、p90 7.5 mm、max 45.8 mm**，
并导致 **59% 轨迹被质量门拒绝**；单相机扰动只影响观测到它的轨迹（p50=0 是正确的）。

**Q6** 3.90 mm 中位差**不能**由 0.5° 解释（那只到 ~1 mm），需要约 1–2° 的相对误差量级；
p90 7.5 mm 与之同量级。因此：部分可解释，**仍有一部分未解释**，且当前无证据把它归因于身份错误。

**Q7** 仍成立：Ring 对 0.5–1° 相对误差不敏感；相对误差会显著扰动三角化；H025 与 Ring 不相容；
3.9 mm 不能靠共享 H 消除。必须撤回：178.7、"yaw 45° 差 54 倍"、10–38 mm、C 偏大是观测问题。

**Q8** **是**：证据指向单视频内部相对位姿；0.5–1° 即产生毫米级形变，建议下一步做单视频 BA（需人工批准）。

**Q9** **是**：`NO_VALIDATED_CANDIDATE_FOUND` 只表示"尚未找到"，不表示不存在；
H025 差 6.4× 但并非灾难性，值得在 BA 之后重试。

**Q10** 无新主线：Ring 用历史 `RingRenderer`（2 行路径补丁）、三角化用历史 `features019`、
一致性用 024 模块；未引入第二套算法。未修改 W0/DXY/HERO/Body/CAD；未覆盖 025/026 结果。
本轮已知不足：`scikit-image` 为新装依赖；`p4_tracks.py` 复用 026 已生成的地标（未重新三角化），
因此实验 A 只在"共同有效轨迹"上报告，且 004 侧仅有共同模式扰动可用。

## 4. 十类图

`runs/G03/FIGURES/`：`01_historical_io_actual_overlay.png`、`02_w0_analytic_vs_mask.png`、
`03_centerline_source_audit.png`、`04_corrected_H_ring_projection.png`、`05_corrected_pose_identifiability.png`、
`06_track_aligned_triangulation.png`、`07_landmark_survival.png`、`08_corrected_pairwise_distances.png`、
`09_ring_vs_triangulation_sensitivity.png`（明确标注非配对）、`10_corrective_audit_summary.png`。

## 5. 复现

```bash
K=experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PYTHONPATH=$K/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY $K/run_cross_video_registration.py --group G03 --stage full-corrective
PYTHONPATH=$K/core:/home/liu/ring_first_3d_workspace/runtime/p3d:src $PY -m unittest discover -s $K/tests -v
```
