# TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001

工程运行完成，科学结果为部分验证及重要负结果，等待人工审阅。

| 指标 | Initial → Deform+Grow |
| --- | --- |
| C0 GT双向MAE mm | 0.380925 → 0.278727 |
| C0 HOLDOUT IoU | 0.876567 → 0.955210 |
| C0结构生长 | 13视角/双视频支持，19新顶点；完整长柄仍缺失 |
| 真实G01 GT MAE mm | 0.351000 → 0.398401，恶化 |
| 真实G03/G05 | 几何保护下实质停滞，无接受生长 |
| HERO | 相比M0更集中；新Body没有比初始锚点提供一致额外收益；绝对3D精度NOT_EVALUABLE |

186测试通过；13阶段全PASS；历史测量回退0。原始工程错误、封盖修复、负结果和GT隔离证据均保留。

科学实现：6415993f4c6aa2370e80841d1803ed701b257bee；C0原始预测d78cacd86b095ade5c4753537e216f900a018bcd，非封盖路径证明后恢复，未重跑C0。

详见[技术报告](TECHNICAL_REPORT.md)、[实际PNG/完整Mesh](visualization/index.html)和[失败台账](FAILURE_REGISTRY.json)。
