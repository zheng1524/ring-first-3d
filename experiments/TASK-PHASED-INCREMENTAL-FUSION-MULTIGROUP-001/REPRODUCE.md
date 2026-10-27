# 本地复现

解释器：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，Python 3.12；实际依赖见 [RUNTIME](provenance/RUNTIME.json)。默认读取此前核验的冻结 P0、源RGB/Mask、深度与相机、密度字段；这些完整资产并未公开。

核验当前结果：

```bash
cd /home/liu/ring_first_3d_incremental
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/code/reproduce.py verify
```

查看阶段计划：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/code/reproduce.py plan
```

若需要重新计算，使用全新目录。已有目录会拒绝覆盖，所有旧科研工作区保持只读：

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/code/reproduce.py replay --destination /home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/runtime/replay_01/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001
```

本轮各阶段已逐段实际执行；未为验证包装入口而再做一遍完整科研流程。数值与拓扑不受点大小/图片排版影响；跨机器Open3D与浮点平台不承诺GLB/PNG字节一致。

主要入口：`prepare.py` 审计/冻结；`pipeline.py A/B` 清理复用与有来源原面细分融合；`metric_geometry.py` 复用/拟合基底与严格投影原型；`feret_definition_audit.py` 保留原严格结果后的后验定义审计；`review_assets.py` 本地GLB与声明视角的一致性评价；`visualize.py` 真实原XYZ与解析基底几何；`index_results.py` 本地HTML和完整资产清单。

正式Dxy项目没有被导入、调用或改写。3D Feret函数仅在本任务中，解析3–4–5矩形测试通过；本轮所有可评价Dxy值仍为NaN。初始80%凸包填充条件不是用户所定义观测区域直径的必要条件，因此另作透明的定义审计，并检查极值端点的原始观测支持；原严格81条件、原模型、原端点与阈值均未覆盖，后验审计也没有产生可评价成功。

本轮可视化入口与绝对路径：

- [打开可视化文件夹](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/)
- [打开 index.html](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/index.html)
- [本地GLB目录](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/)

若客户端不允许打开本地链接，复制以上绝对路径到文件管理器或本机浏览器即可。HTML使用相对链接，完整本地目录移动后仍可一并浏览；公开GitHub只保留四张组级审查图及小型来源/指标表，完整PNG、XYZ、Mesh、GLB和缓存保留本地。
