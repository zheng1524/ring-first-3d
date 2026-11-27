# 只读复核命令

在本任务工作树执行，输出只写本任务审计目录，不发布READY清单、不删除科研资产：

```bash
cd /home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001
PYTHONDONTWRITEBYTECODE=1 python3 -u tools/v6_storage_reaudit.py
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/v6_storage_mesh_inventory.py
```

第一步记录普通文件/链接，不跟随目录符号链接；候选计算SHA，工作树副本另与HEAD blob及权威原件核验。所有计数按当时文件系统快照，之后执行前必须重新核验。第二步在不改动原文件的前提下记录几何指标，并把状态连接回两份文件表。

汇总报告为解释性文档；重跑审计后数字变化时须同步更新报告。完整库存保留本地，Git发布精确候选、几何指标、目录表及必要证据。初次审计为减少重复Git子进程做过读取性能调整，历史读取日志本地留存；它们没有执行任何删除，不计入科学实验或释放收益。
