# 本机复现

此实验绑定已审计的本机只读资产绝对路径，不含原始视频/模型。需先恢复INPUT_MANIFEST.json中列出的文件并逐项校验SHA；不能以相似文件替换。当前环境Python3.12、numpy/scipy/OpenCV、trimesh、Open3D0.19及matplotlib；不需要torch/GPU。大型原始资产不上传，不声称离开这些资产即可无条件复现。

```bash
cd /home/liu/ring_first_3d_pose_depth
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/experiment_a.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/experiment_b.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/validate_and_supplement.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/figures.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/local_geometry_diagnostic.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-RING-FIRST-POSE-DEPTH-IDENTIFIABILITY-001/code/deliver.py
```

现有PROTOCOL已冻结，**不重复运行preflight.py重新选择或初始化**；其代码仅说明首次冻结如何由历史清单生成。以上命令只重建本任务派生输出，不改历史数据。源码哈希与冻结绑定若不一致必须停止，不能跳过检查。不同机器的绝对路径迁移应只改只读资产根，并保留旧冻结和路径映射、新源码SHA；不得顺带改科学参数。

完整本地A预测：local_results/A；B对应/J/SVD：local_results/B。每个C3_JACOBIAN_SVD.npz含完整归一J、未数量平衡J、参数名/尺度、r(0)、Vt及物理/归一梯度。metrics/jacobians同步六个完整C3矩阵；C1/C2依据B_SVD_RESULTS中行数按PROTOCOL的C3块顺序切片，用numpy.linalg.svd(full_matrices=False)重算。参数顺序严格由npz parameter_names给出。

SIFT固定种子，缓存优先级及方向逆转均记录origin。新增匹配也保留原始点索引。未知区域不补深度。旧模型/GT/融合输出访问被审计hook拒绝；CUDA_VISIBLE_DEVICES为空。
