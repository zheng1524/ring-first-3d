# Init-A多视频审阅

打开visualization/index.html。Figure1为实际GT刚体对齐后的形状，Figure2为原公制世界Mask解释，Figure3为经原Mesh/RGB核验的G02/G03失败，Figure4为完整HERO真实三角面切面，且没有融合表面遮挡。每病例GT页面可切换A0/A1/A2/A2S；HERO页面可切换M0/历史Body/重跑A1/A2/ICP及逐曲面显示。

所有精确WORLD/ALIGNED小型NPZ在review_meshes；GT变换只在ALIGNED副本，原世界模型供HERO使用。源、代码、数据版本见VERSION_SOURCES与TASK_FREEZE。130回归、13执行门禁通过；科学负结果单列。最初门禁失败与独立修复记录保留。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/TASK.yaml --run-dir experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/runs/INIT_A_002
```

check校验固定来源/科学源码；run --stage按原冻结顺序恢复；accept只验收执行产物。init_multivideo_init_a.py为首次审计草案生成器；已完成的TASK采用记录在案的评价元数据隔离修订，不重新生成或覆盖。原完整优化器、原Mesh、PLY、原RGB/Mask/深度和所有拒绝保留在本地runs，Git保存精选几何和离线审阅资产。
