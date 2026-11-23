# FIGURE_STATUS（如实）

| 图 | 状态 | 原因 |
|---|---|---|
| 1 三组 W0 与 Ring（真实 RGB + 轮廓） | **NOT_EXECUTED** | 时间预算耗尽；Ring 数值（M/I/C/O）已存 `runs/<G>/RING_SCORES.csv` |
| 2 三组真实背景匹配 | **NOT_EXECUTED** | 身份表 `IDENTITIES.csv` 已生成，未渲染连线图 |
| 3 旧/新 H 初始化 | **NOT_EXECUTED** | H 初始化阶段未运行 |
| 4 共同三角化 | **NOT_EXECUTED** | 三角化阶段未运行 |
| 5 二维重投影 | **NOT_EXECUTED** | 同上 |
| 6 Ring/RGB 联合评价 | **NOT_EXECUTED** | 同上 |
| 7 三组相机结果 | **NOT_EXECUTED** | 同上 |
| 8 统一主线审计流程图 | **NOT_EXECUTED** | 以 `TECHNICAL_REPORT.md` 表格代替 |

**不生成空白/示意图片。** 已保存的原始数值（Ring 分数、landmark 数、身份数、FIT/HOLDOUT 划分）足以在下一轮直接出图。
