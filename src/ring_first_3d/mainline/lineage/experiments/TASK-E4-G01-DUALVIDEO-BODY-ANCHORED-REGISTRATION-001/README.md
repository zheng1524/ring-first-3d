# 使用与状态

当前真实G0门禁失败，停止于G0；只实现并注册了场景审计，不宣称G1–G4已实现。

从项目根目录运行：

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001/TASK.yaml --run-dir experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001/runs/G0_AUTHENTICITY_004
bash tools/research/run.sh -m unittest discover -s tests -v
```

Runner指定阶段的形式为`policy.py run --task TASK.yaml --run-dir 新运行目录 --stage 阶段名`；授权阶段必须依次通过。`--stage all`遇到失败自动停止。`policy.py accept`要求全部验收门禁通过，当前不可验收。不得在修复真实资产前强行运行G1。

本地双击`visualization/index.html`即可离线检查全部33帧和独立坐标系完整三角网格。报告、RESULT_CARD、RUN_MANIFEST与全部关键证据均在此目录。runs保留本地全量原始产物，Git仅保存冻结输入清单、报告、小型证据及选定33帧的审计PNG。
