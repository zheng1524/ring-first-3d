# 清理后审计

只清理python-fcl0.7.0.11的HTTP下载缓存2个文件（清单逐路径），逻辑字节4,660,487；安装版本及环境完全保留。恢复命令见CLEANUP_MANIFEST.csv。无科研唯一结果删除。

操作前free=6486990848；操作后free=6491652096；即时df差=4661248bytes（后台写入影响实得值）。

free_after_cleanup=6.046GiB；estimated_peak_need=0.8GiB（小型源码/现有CUDA缓存/6实验臂阶段mesh和图）；safety_reserve=4GiB。剩余空间满足轻量路径，禁止安装PhysicsNeMo/PyTorch3D/libigl/IPC等大框架。

保留所有旧实验worktree/代码、独有最终模型/检查点及3–4张核心证据，尤其A1/R1安全P0。只读引用原生样本池，不复制RGB/深度。每臂只存阶段、BEST/LAST_SAFE和少量失败提案。
