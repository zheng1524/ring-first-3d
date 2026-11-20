# 可视化说明（静态 PNG）

目录：`visualization/figures/`。本任务不生成 HTML。全部图由冻结运行产物绘制。

| 图 | 文件 | 展示内容 | 读法 |
|---|---|---|---|
| 1 | `fig1_ring_vs_cad.png` | 每个物理组取一个 FIT 视角：真实 RGB + Ring 观测点（青）+ CAD Ring 投影点（黄），标题给出该视角 Ring MAE | 青黄重合=Ring 拟合好；可见环被遮挡处青点应缺失 |
| 2 | `fig2_rgb_matches.png` | G01/005 与 G03/005 的跨视角 SIFT 训练轨迹（左右两图拼接，连线为同一 track） | 连线多且分布均匀=匹配充分；集中在局部=覆盖不足 |
| 3 | `fig3_camera_layout.png` | 10 个实例各自的 FIT 相机在世界坐标（Ring 系）中的 x–z 分布，星号为环心 | 点围绕环心成弧=正常绕环观察；孤立点=该视角相机可能异常 |
| 4 | `fig4_consistency_and_status.png` | 左：每视角 Ring MAE vs 独立 held RGB MAE；右：每实例 VALIDATED / USABLE_WITH_CAUTION 堆叠 | 左上角=Ring 好但 RGB 差（需谨慎）；右下=两者都差（INVALID） |
| 5 | `fig5_vs_history.png` | 本轮统一 BA 相机与 002/001 历史相机的旋转差与中心差 | 约 180°/113° 的差异是**全局规范**不同，不是错误；15–23° 才是同规范下的真实修正 |
| 6 | `fig6_g03_g05_status.png` | G03/005 与 G05/005 逐视角 Ring MAE 与 held RGB MAE | 对应报告中"修复后仍存在的失败案例" |

## 复核建议

1. 先看图 4：它同时给出"Ring 通过"和"RGB 是否一致"，是本轮状态分级的主证据。
2. 再看图 1、图 2：确认 Ring 观测与 RGB 轨迹都是真实数据。
3. 图 5 只用于说明"跨任务绝对位姿不可直接比较"，不能用于判断谁更准。
4. 图 6 是失败案例，不要用它反推整体质量。

## 复现

```bash
cd <ws>/experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code
PYTHONPATH=<ws>/src:. /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python make_figures.py
```
