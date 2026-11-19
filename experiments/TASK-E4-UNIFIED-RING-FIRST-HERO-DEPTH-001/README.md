# 统一 Ring-First / HERO / 深度消融

先读 `report/FINAL_REPORT.md` 和 `RESULT_CARD.md`。原始 mixed-policy 诊断与正式 RF_ONLY_V1 分开保留。

使用既有环境：

```bash
bash /home/liu/ring_first_3d_workspace/mainline/scripts/python.sh experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code/run_tests.py
bash /home/liu/ring_first_3d_workspace/mainline/scripts/python.sh experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/code/check_artifacts.py
```

命令从工作空间根目录执行。已有冻结目录不应重新运行 `audit` 或 `prepare`；重现实验必须复制源码和协议到新的独立任务目录并绑定同一输入哈希，保留本轮产物。`body_stage.py GROUP B1/B2 --mode train` 在目标目录存在时拒绝覆盖。

可检查的计算入口：`pipeline.py`（输入/原始数值候选）、`rf_only.py`（来源准入）、`hero_stage.py`（正式新推理）、`body_stage.py`（历史优化器最小适配）、`evaluate_stage.py`（先freeze再GT）、`visualize_final.py`（静态图）、`report_final.py`（完整分母报告）。

代码沿用普通工程模块，未新增算法框架。所有最终图为PNG，没有HTML。权重、环境和原始数据不复制进Git；实际本机依赖见audit/ENVIRONMENT.json。

冻结预测的公制世界坐标 PLY 在 `runs/RF_ONLY_V1/G*/004/exported/B*/`，同时提供原始表面及含基底的实体面版本；`SOURCE.json` 标明基底来源和导出精度。GT 对齐副本单独位于 `evaluation/`，不得用于 HERO 或训练。

本地提交包含源码、协议、文本审计、指标和精选 PNG/Mesh；完整原生深度、全部对应缓存及运行产物保留在本机，由 `RUN_MANIFEST.json` 的实际路径与 SHA256 绑定。清单明确排除自身、提交后生成的 `DELIVERY_COMMIT.json`、仍在写入的检查器日志和运行缓存。未推送远程。
