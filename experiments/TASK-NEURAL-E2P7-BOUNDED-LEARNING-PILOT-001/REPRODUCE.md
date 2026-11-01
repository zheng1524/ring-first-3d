# E2.7复现与只读检查

工作树`/home/liu/ring_first_3d_neural_e2p7`，父提交a69a17099e4ed5ff34ed8e1be49157fbda329615；Python `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`。当前实验已经完成并按科学门槛停止，**不得在本轮继续或重启训练**。以下是原执行顺序，供独立复现设计/审阅，不是在当前目录重复更新的指令；train_arm会拒绝覆盖已有RUN记录。历史资产只读，GPU基础依赖沿用原环境，不下载权重。

```bash
export PYTHONDONTWRITEBYTECODE=1
PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$PYTHON" code/preregister.py
"$PYTHON" code/preflight.py
# 仅parity通过才允许原任务的以下两次调用
"$PYTHON" code/train_arm.py A
"$PYTHON" code/train_arm.py B
# 以下均为不更新参数的后处理
"$PYTHON" code/diagnose_step.py
"$PYTHON" code/check_accumulation.py
"$PYTHON" code/postprocess.py
"$PYTHON" code/visualize.py
"$PYTHON" code/report.py
"$PYTHON" code/validate.py
```

本轮两组均第一步停止；数据、密度、代码、optimizer及A/B唯一区别已冻结。实际`STOP_UNSAFE_step001.pt`与安全step0分别存档，不能把前者当通过结果，也不能把后者称已学习模型。25/50/75/100的权重不存在，禁止补造。canonical FP64 SHA与FP32 SHA有不同字节精度，均在INITIAL_MODEL记录。

单独运行`code/validate.py`只核对文件/资产/既有输出，不构造新神经实验或更新。纯可视化可从本地ignored local_results重建，无optimizer。checkpoint是state_dict-only，恢复需同一官方构造、冻结尺度和beta_min设备转移，不包含可自动续训的Adam状态。

CPU/GPU parity和128/256只在固定初始模型验证；最终可见面是实际65³零面中的观测子集，不封闭背面，支持/冲突资格来自原HERO而非GT。source-warp只从源A取色。原始输入/NPZ缓存和运行日志仅本地，SHA在DELIVERY_MANIFEST；精选PNG/PLY与7份小state_dict上传Git。
