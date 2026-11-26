# V6 HIST 后台交接

已确认健康；当前RUNNING，未等待全量结束。记录时间 2026-11-26 14:48:22 CST。最新实时数字以本地PROGRESS为准，本报告快照不会随后台重写。

- 父PID：`185164`；启动方式：`setsid`独立会话、stdin=/dev/null、stdout/stderr持久日志，退出对话不终止。
- 当前执行提交：`da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`；[逐文件快照哈希](evidence/EXECUTION_SNAPSHOT.json)。报告/clean提交不改变该科学执行代码。
- 不可变快照：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`。
- 实际配置：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a/experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/config/FULL_RUN.json`。
- 精确命令与环境：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/start.sh`。
- 主日志：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/runner.log`；逐视频`logs/<真实case>__<stage>.log`。
- 进度：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/PROGRESS.json`；同目录VIDEO_RESULTS.csv、GROUP_RESULTS.csv、states/。
- 最终报告预定：`/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/FINAL_COVERAGE_REPORT.md`。未结束只写CURRENT_COVERAGE_REPORT.md；科学失败保留在全部79视频/39组分母。选帧分母未知另列。
- 最终图集及实时页：[http://127.0.0.1:8957/index.html](http://127.0.0.1:8957/index.html)，HTTP已实测200。浏览服务PID见`runs/v6_full_run_001/VIEWER.json`。

## 健康证据

[HEALTH_RECEIPT](evidence/HEALTH_RECEIPT.json)记录真实新增IIa14/R5/004：14个冻结合法组合、实际HERO起始及14个有效原生/原Mesh，随后队列进入下一视频。原生启动账本`INFERENCE_STARTS.jsonl`带元组、时刻、执行身份；[关键六视图](figures/first_new_video_near_sources.png)。截至本记录，完成视频14、可渲染来源225；后台继续变化，不把PID或缓存命中当成健康唯一证据。

## 暂停与原样续跑

安全暂停在当前阶段结束后生效，不破坏已冻结结果：

```bash
touch /home/liu/ring_first_3d_workspace/runs/v6_full_run_001/PAUSE_REQUESTED
```

检查`runner.log`出现`QUEUE_EXIT PAUSED`。恢复前移除该请求，再后台启动同一快照（单实例RUNNER.lock阻止重复队列）：

```bash
rm -f /home/liu/ring_first_3d_workspace/runs/v6_full_run_001/PAUSE_REQUESTED
nohup bash /home/liu/ring_first_3d_workspace/runs/v6_full_run_001/start.sh >> /home/liu/ring_first_3d_workspace/runs/v6_full_run_001/runner.log 2>&1 < /dev/null &
```

低空间退出为LOW_DISK_PAUSED，需恢复到1.5GiB以上再按同命令续跑；不修改已完成科学产物。资源中断可按原计划恢复。科学/工程失败不会静默循环重试；如确认需重试某个失败视频，先暂停队列，用下列入口登记旧状态后再续跑：

```bash
PYTHONPATH='/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a/src' /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -m ring_first_3d.v6_raw.full_run retry --config '/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a/experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/config/FULL_RUN.json' --case '<完整物理case>'
```

retry只重置状态并记录原因，不改变相机方法、Support或参数；已成功元组继续复用。资源性HERO重试同元组最多一次，失败不会换组合。批量错误/失败都保留，最终报告明示COMPLETE_WITH_FAILURES。

## Clean小试与本地证据

[中文简报](CLEAN_REPORT.md)；恰好三图：[Raw459](figures/clean_1.png)、[Raw458](figures/clean_2.png)、[Raw570](figures/clean_3.png)。[本地三源对比](http://127.0.0.1:8957/clean/index.html)。原坐标、原面全集、子集、映射、逐面理由、删除连通区域和恢复路径：`runs/v6_full_run_001/clean/case1`至`case3`。原Mesh与depth仍在旧HIST位置，SHA见[CLEAN_VERIFICATION](evidence/CLEAN_VERIFICATION.json)。C1未自动采用。

后续决策是人工审阅clean的73面及新增断裂；后台HIST输出保持Raw。不要启动其他路线、Body训练或跨视频融合。用户要求的持续任务已交给后台，此轮交接后停止。

## 已核实远端交付

独立分支 `exp/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001` 已逐提交上传；交付数据提交 [`865a6990b45d882700b7b7732834a894626c7ee3`](https://github.com/zheng1524/ring-first-3d/commit/865a6990b45d882700b7b7732834a894626c7ee3) 经GitHub API读回与本地SHA一致。clean提交 `8016ed9b6a8a124ff5570f50b6e498fe6dfa4699`，后台执行提交 `da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`。本段与上传回执是后续元数据提交，不改变运行快照。GitHub插件写权限403，沿用本机已授权Git-data API正常上传，未force更新。
