# TASK-E4-G01-MULTISURFACE-BODY-FUSION-001

104项测试、13阶段执行/产物门禁通过；科学结论未认定为可靠定位成功。

- 16独立深度栅格曲面，68,230材料顶点、127,691三角面；未使用GT面并集冒充观测。
- 6条件×2 Body×4方法+4消融，52模型；相机/Body冻结，DXY新调用0。
- C3/E1整体双向MAE：Body-only 0.323293→分层后融合0.303003mm；不修正融合0.201619mm更低。
- C3/E1逐视角材料MAE：不修正0.460332→分层0.514474mm；C0引入0.376231mm偏差。保留负结果。
- 高方差C4残余修正有部分改善，不能抵消低方差偏差或证明普遍恢复。

[第一张主图：真实切面](visualization/figures/01_MAIN_MULTISURFACE_SECTIONS.png) · [52组合真实切面](visualization/sections_all.html) · [完整逐视角3D](visualization/multisurface_3d.html) · [技术报告](TECHNICAL_REPORT.md) · [指标](visualization/ALL_CONDITION_METRICS.csv) · [失败台账](visualization/FAILURE_LEDGER.json) · [RUN_MANIFEST](RUN_MANIFEST.json)

实现提交：`1648935501781d6acb47a288253255134bdedb89`。GT只生成/独立后验评价，最终预测未做GT最佳刚体对齐。历史测量回退0。
