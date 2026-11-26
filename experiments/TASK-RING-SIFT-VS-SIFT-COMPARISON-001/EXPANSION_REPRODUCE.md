# 扩组执行与本地队列

工作树：`/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-RING-SIFT-COMPARISON-001`

Python：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`

```bash
# 已完成的原始求解按输入/输出哈希复用；相机不会静默重跑。
PYTHONPATH=src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/ring_sift_comparison.py --cohort expanded --stage cpu-batch

# A运行时冻结/登记GPU等待；A结束时可执行剩余组合，累计至多40次。
PYTHONPATH=src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/ring_sift_comparison.py --cohort expanded --stage hero-batch

# 单次本地等待队列：30秒检查一次A调度器，最多等待24小时；不抢GPU。
# 只可启动一个；重复启动被进程锁拒绝。源码变化或执行错误使队列停止。
PYTHONPATH=src OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/ring_sift_comparison.py --cohort expanded --stage gpu-queue

# 仅刷新统计/可视化，不调用相机或神经网络。
PYTHONPATH=src /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python tools/ring_sift_comparison.py --cohort expanded --stage expanded-report
```

队列实时状态：`/home/liu/ring_first_3d_workspace/runs/ring_sift_comparison_001/EXPANSION_GPU_QUEUE.json`；日志同根`logs_expanded/gpu_queue.log`。启动PID以状态JSON为准；不能只看PID文件推断作业仍在运行。

队列完成后自动刷新本地`EXPANDED_COMPARISON.html`和技术报告，不自动提交/上传后续GPU新结果。Git提交表示当时已验证的CPU及旧HERO证据，不代表未来排队推理已完成。查看`EXPANDED_COVERAGE.csv`中的`hero_status`与`native_success`，以及`INFERENCE_STARTS.jsonl`实际启动记录。

所有新视频保留2个固定Target，每个3 Support，不能因相机或推理失败换组合。任务A优先和共享GPU锁必须同时成立。没有GT，不训练、不做clean、不把Ring满足度当R对S的胜负门槛。
