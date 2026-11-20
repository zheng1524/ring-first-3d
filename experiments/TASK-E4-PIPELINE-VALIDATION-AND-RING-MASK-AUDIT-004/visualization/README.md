# 可视化说明（静态 PNG）

**目录：** `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004/visualization/figures/`
本审计**不生成 HTML**。所有图均由冻结实验数据直接绘制，无示意数据。
数据来源与复算脚本见上级目录 `code/`，数值表见上级目录 `*.csv`。

| 图 | 文件 | 数据来源 | 展示了什么 | 如何读 |
|---|---|---|---|---|
| 1 | `fig1_G05_ring_mask_components.png` | `audit/SELECTED_VIEWS.json` 的该视角 cache + `CAMERA_RESULT.json` | G05/005 `raw00404` 的五个面板：原 RGB、连通域着色、原始标签、仅主连通域、CAD Ring 投影与主分量叠加 | 左 3 面板看"孤立块在哪"（右上角绿色短条，20×4 px，63 px）；第 4 面板绿色=只保留主环后的观测；第 5 面板黄色点=CAD 环投影，绿色=主环像素，二者基本重合，说明主环本身是好的 |
| 2 | `fig2_ring_residual_decomposition.png` | `RING_COMPONENT_COMPARISON.csv` | 左：同一固定相机下 4 种观测集合的 Ring MAE 与点数；右：4 个多分量视角的 M1−M0 差值 | 左图看"主环 0.724 px vs 孤立块 75.19 px vs 全边界 0.745/76.05 px"，即 9.45 px 的来源；右图红色=最大连通域反而变差（G02 两例），说明不能全局启用 |
| 3 | `fig3_multicase_ring_masks.png` | 同上 | 6 个代表性视角的掩膜：绿=主分量、灰=被弃分量、蓝=息肉 | 看被弃分量的位置与大小；标题给出 `components / discarded px / M0→M1`。只有 G05 那格是大幅改善，其余为小幅正/负 |
| 4 | `fig4_G03_camera_branch.png` | `CAMERA_BODY_GAUGE_DIAGNOSTICS.csv` + `CAMERA_BRANCH_DIAGNOSTICS.csv` | 左：G03/005 8 个视角在三种相机下的 **INITIAL Body** 投影 IoU；右：v0 与 v1 的旋转差 | 左图：v1（绿）稳定 0.82–0.85，v0（红）在 6 个视角只有 0.13–0.16；final（蓝）≈v0 且略差。右图：8 个视角都在 174°–179°，即两个"互为翻转"的规范。**结论：Ring 通过但 Body 不投影，是规范选错，不是 Ring 解错** |
| 5 | `fig5_gates_and_coverage.png` | `GATE_SENSITIVITY.csv` + `VIEW_COVERAGE_MATRIX.csv` | 左：Ring MAE 分布与 3/5/10 px 线；中：三个阈值下的通过视角数；右：10 个实例的 FIT 相机覆盖率 | 左：分布集中在 1–2 px，只有 1 个点远离；中：3 px 与 5 px 通过数相同（77/78），放宽无收益；右：只有 G05/005 是 6/8 |
| 6 | `fig6_hero_and_body_health.png` | `HERO_HEALTH.csv` + `BODY_UPDATE_HEALTH.csv` | 左：HERO 深度中位 vs 相机到环心距离（对数纵轴，带 1×/3×/10× 参考线）；右：10 个 body arm 的最大顶点位移（对数） | 左：绝大多数点落在 1×–2× 带内；两个红色三角在 6× 与 25×，即 G03/005 的 raw00402/raw00373，标 `SUSPECT` 但未拒绝；右：红柱=位移 <1e-3 mm 的停滞实例（G02/005、G06/005 各两臂），绿柱=真实更新 |

## 复核建议

1. 先看 Figure 4（相机规范）与 Figure 1（Ring 掩膜），它们分别对应两类主要失败机制。
2. 再看 Figure 2 与 Figure 5，确认"最大连通域"和"Ring 门限"都不是普适问题。
3. 最后看 Figure 6，注意左图的异常点与右图的停滞实例都只是 `SUSPECT`/`STAGNATION` 标记，**不是**已判定的失败结论。

## 复现

```bash
cd /home/liu/ring_first_3d_workspace/experiments/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004/code
PYTHONPATH=/home/liu/ring_first_3d_workspace/src:. \
  /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python make_figures.py
```

全部脚本只读输入，不写回任何冻结产物。
