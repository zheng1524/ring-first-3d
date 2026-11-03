# 建议云端配置

为方便延续当前单卡代码，建议 **RTX4090 24GB ×1，8 vCPU，32GB RAM，100GB持久化SSD**，SSH访问且可安装依赖。Ubuntu22.04/24.04 x86_64；Python3.12；PyTorch2.7.1+cu128；NVIDIA570或更新驱动。保留相同1024rays和M1/调度器，先做短测，不按未实测的GPU型号承诺速度倍数。

GPU24GB规格：[NVIDIA Ada官方资料](https://images.nvidia.com/aem-dam/Solutions/geforce/ada/nvidia-ada-gpu-architecture.pdf)。PyTorch2.7.1 CUDA12.8安装：[官方版本表](https://pytorch.org/get-started/previous-versions/)。例如在独立Python3.12环境中固定torch2.7.1并使用官方cu128 wheel索引，其余依赖按provenance/ENVIRONMENT.json复刻，不自动升级torch。

使用普通按量实例便于首次迁移；检查点放可在释放计算实例后保留的持久化盘。若RunPod，Network Volume与实例独立，见[官方存储说明](https://www.runpod.io/blog/where-did-my-files-go-a-straight-guide-to-runpod-storage)。不在本任务自动租机、充值、传出数据或启动云训练。

当前本地真实探针峰值分配4315.8MiB；云端速度/长期显存仍以实际短测为准。完整模型/Adam/调度器/随机数/采样状态均保留，不将仅加载参数称为无缝恢复。迁移方法见REPRODUCE.md。
