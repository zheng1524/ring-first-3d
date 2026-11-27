# R1全量运行交接

**状态：RUNNING；不是全量完成。** 现场核验时间：2026-11-27T20:32:40.677363+08:00。PID `54355` 存活；单runner锁生效。首段已实际完成新HERO→clean→图表，第二段已从prepare推进到相机求解。

## 实际运行身份

- 科学基线：R1 dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e。
- 本轮执行源码：`29874fe61f59c429fb83d2377ab707c847992ef8`，含统一缓存、固定clean与清理后共享导入修复。
- 运行快照：`/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001/snapshots/29874fe61f59c429fb83d2377ab707c847992ef8`。
- 实际配置：`/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001/snapshots/29874fe61f59c429fb83d2377ab707c847992ef8/experiments/TASK-V6-R1-MAINLINE-AND-FULL-RUN-B-001/config/FULL_RUN.json`。
- 实际配置SHA256：`c16895ee69d0a965f5f1e18b88fa42e714dd47231721f103438e32b07a93bb54`。
- 输入清单SHA256：`d414c797d66cdce88f5edf6793b10709cd74cfa0fe9e15a6dd2b977df2770515`。
- `include_photos=false / reuse_old_results=false / approval_required=false`。
- 新根：`/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001`；规范缓存：`/home/liu/ring_first_3d_workspace/cache/v6_r1`。
- 后续报告提交不改变正在执行的冻结快照。

## 本地页面与证据

- [实时首页](http://127.0.0.1:8961/)
- [首段IIa4.5/R10组页面](http://127.0.0.1:8961/groups/GP_IIa_4.5mm_closed_R10_single_refY.html)
- [实时PROGRESS](http://127.0.0.1:8961/PROGRESS.json)
- [首段Raw六视图](figures/FIRST_R1_RAW.png)
- [完整链及第二段推进验收](evidence/FIRST_CHAIN_VERIFY.json)

首页、组页、PNG、PROGRESS已HTTP 200实测。仅绑定本机127.0.0.1:8961，服务PID见运行根HTTP_PID.json。图沿用旧renderer的HIST标签作为固定显示键；实际算法为本页标明的R1。图为Raw近景，不是Trusted拼合；六视角出画计数和毫米比例尺保留，首段13源全部送入renderer。

## 当前计数（阶段值）

固定39物理组、79注册视频、1653原选帧非诊断Target。失败/零输出/待运行均留在分母。120照片本轮未处理。

- 当前状态计数：`{"CAMERA_RUNNING": 1, "DONE": 1, "PENDING": 77}`。
- 新native成功 13，非空Raw 13，非空Trusted 13。
- Raw非空而Trusted为空 0。
- 首段`GP_IIa_4.5mm_closed_R10_single_refY_005`：13合法元组、13新推理、13非空Raw、13完成clean、13非空Trusted；零资源重试，首段原native与所有回执SHA核验通过。
- 已逐源核验Trusted导出恰为原`F[state==0]`，原V和FaceID保持。
- 第二段`GP_Ip_8.8mm_closed_R5_single_refY_005`已实际执行Ring观测/相机流程；不是仅创建空目录或PID。

这些数量只是输出覆盖，不能称几何正确率、有效表面积或最终覆盖率。首页与CSV继续由runner自动更新，终态自动写FINAL_COVERAGE_REPORT.md及BASELINE_COMPARISON.json，无需另起人工报告脚本。三个105/205/795集合重叠，分别对照，不相加。

## 空间、清理与工程失败

启动持maintenance.lock核验已发布批次均COMPLETE且release/receipt SHA匹配，新运行根/缓存根/源码树受保护。见STARTUP_CHECK。

- 保守新增预算：13160722848字节（约13.16GB）；全部1653Target假定产出，含缓存/相机/峰值/1GiB余量。
- 正式恢复启动可用：15324127232字节。
- 本次交接现场可用：15258812416字节（约15.26GB）。
- 每阶段保留至少1GiB加该阶段峰值；低盘自动暂停。

cb20a728首次启动在相机导入时暴露已删除退役示例相机依赖，3次camera失败，无任何HERO推理。已完整归档`engineering_failed_launch/cb20a728`，修复并以两例重解证明相机/轨迹/13与21元组逐位等价后恢复。没有用旧成品补齐，也未把工程失败伪装成科学零输出。详见IMPORT_DEPENDENCY_REPAIR及FAILED_LAUNCH证据。

## 恢复与监测

命令见[REPRODUCE.md](REPRODUCE.md)，从本运行SNAPSHOT.json取真实Python、代码、环境和config。同快照恢复校验父子及产物身份；DONE验证后跳过，已有成功native不再推理。

日志`/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001/logs/runner.log`；分阶段`logs/<case>__<stage>.log`；逐次`stage_receipts/`、`attempts/`、每视频RUN_STATE/CAMERA_COMPLETE/PLAN_FROZEN/HERO_COMPLETE/CLEAN_COMPLETE均保留。资源失败只允许同元组有界重试，未解决工程/资源异常保留FAILED。科学零计划不换种子重跑。
