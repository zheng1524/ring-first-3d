# 使用

先打开visualization/index.html，第一张主图为全部真实Mesh切面；sections_all.html含52组合及失败的四列切面；multisurface_3d.html可逐视频/逐视角显示完整三角面。SVG/Canvas线段来自实际三角面求交，没有平均轮廓。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/TASK.yaml --run-dir experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001/runs/MULTISURFACE_001
```

check校验固定输入/源码；run --stage指定阶段，前置门禁不可跳过；accept只验收执行与产物，科学结论等待人工。Body初始几何为用户授权的已核验GT-free E1/E2复用，DXY未改也未重跑。原始每片RGB/Mask/轴向深度、独立Mesh、所有未融合Mesh、完整Ownership候选保留在本地runs；Git保存冻结配置、代码、小表、精选PNG和可离线查看全部完整曲面的JS/HTML。
