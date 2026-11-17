# 本地审阅与复现

先打开visualization/index.html。首张主图为C7/E1真实完整Mesh切面：原始分散→Body视频粗定位→原阈值分层配准→统一主面。sections_all.html包括全部34个冻结仿真结果；各真实组目录包括全部4方法的切面和完整Mesh开关。correspondence_failures.html显示实际源图、正式二维主体、Body投影及拒绝/错误对应。

源码与TASK预先冻结；原Runner运行位于runs/STRESS_REAL_001，包含全部RGB/Mask/轴向深度、独立Mesh、每方法真实变换、完整Ownership和失败/回归证据。Git只保存审计表、小数据和离线查看几何，不上传原视频或模型权重。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001/TASK.yaml --run-dir experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001/runs/STRESS_REAL_001
```

check验证身份；run --stage按冻结阶段恢复，不覆盖历史；accept仅执行/产物验收。算法来自指定b16a6f8提交未改，CTF为单独预定义API组合。真实仅为原始HERO多曲面低成本Smoke，无独立GT；G03困难，G05只有一片005 FIT及无005 HOLDOUT。全部失败与4个分散/GT表面矛盾案例保留。任务局部Failure Registry均为未审查候选，未提升永久规则。
