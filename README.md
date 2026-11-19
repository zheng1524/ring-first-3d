# Ring-First 3D 本地科研工作空间

普通本地目录；主线算法和输入依赖已收敛，清理前后均通过 247 项回归及 8 项固定输入重放。没有重建环境或改变科学算法。

- [工作空间结构](docs/cleanup_003/WORKSPACE_STRUCTURE.md)
- [本轮最终报告与实际清理](docs/cleanup_003/FINAL_REPORT.md)
- [实测验收及哈希](docs/cleanup_003/WORKSPACE_VALIDATION.json)
- [本地依赖](manifests/LOCAL_DEPENDENCIES.json)
- [离线科学证据与新投影](visualization/index.html)
- [后续 Git 发布方案](docs/cleanup_003/GIT_PUBLICATION_PLAN.md)

```bash
cd /home/liu/ring_first_3d_workspace
bash scripts/run_pipeline.sh --out /home/liu/ring_first_3d_workspace/results/my_new_replay
bash scripts/python.sh docs/cleanup_003/code/regression.py
```

输出目录不可存在。默认是固定输入/历史状态重放，HERO 使用官方原生推理；不是重跑全部科学优化。后续科研新建 TASK 并沿用 Policy、FIT/HOLDOUT 和 GT 隔离。

G01 的局部几何缺陷与固定世界坐标误差恶化、G03 拒绝/正式 NaN 均保留。原始数据和权重为显式受保护外部依赖；本空间不再依赖已退役 Worktree。详细限制和逐项证据见最终报告。
