# SIM_PROTOCOL_REV1交付

G0–G4全部运行；执行验收通过，科学M2位姿门限未通过。先读RESULT_CARD与TECHNICAL_REPORT。

直接离线打开`visualization/index.html`，再进入完整曲面五阶段交互。支持全部S0–S4/独立L1、M0/M1/M2/Ring/直接像素/Ring辅助方法。灰Body、黑Ring、红004、蓝005都是真实冻结网格；GT仅评价。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/TASK.yaml --run-dir experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/runs/SIM_REV1_001
```

`policy.py check`校验TASK，`run --stage 阶段名`只能按依赖执行，`accept`验收完整产物，科学结论等待人工审阅。无force/跳过门禁。原始全量RGB/Mask/轴向深度/完整Mesh/Face映射NPZ保留在本地runs；Git只提交代码、冻结配置、小表、精选PNG和包含完整曲面的离线HTML。DXY无需重跑；新提示限定其为G1/G2辅助，未开展任何DXY算法研究。
