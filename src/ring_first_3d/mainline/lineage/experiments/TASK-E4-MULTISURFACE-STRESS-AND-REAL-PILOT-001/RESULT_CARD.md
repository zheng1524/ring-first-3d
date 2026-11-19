# TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001

执行完成，科学结论等待人工审阅。仿真数值34/34；真实数值组3/3，绝对精度NOT_EVALUABLE。

[真实切面首图](visualization/figures/01_MAIN_STRESS_SECTIONS.png) · [报告](TECHNICAL_REPORT.md) · [指标](visualization/STRESS_METRICS.csv) · [真实迁移](visualization/REAL_METRICS.json) · [失败台账](visualization/FAILURE_LEDGER.json)

分散下降不自动等于正确位置；C0及GT恶化证据全部保留。

C7/E1材料加权MAE：M0 1.675696→原阈值BODY_HIER 0.869928mm→独立CTF 0.810643mm；原阈值同/跨视频分散2.303382/2.193060→0.475975/1.099380mm。位置误差仍明显。C0原Body方法引入约0.372955mm材料MAE。C4/E1反例：分散下降但GT表面MAE 0.294137→0.308335mm。

真实3/3组已运行完整原网格最小Smoke；G03改善有限，绝对精度均NOT_EVALUABLE。新DXY/HERO调用0；每组适配、独立2D初始化、4方法及融合约14–17秒。
