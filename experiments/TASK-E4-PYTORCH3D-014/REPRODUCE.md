# 复现

工作树：/home/liu/ring_first_3d_e4_sdf_localization；Python：/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python；Blender：/home/liu/blender/blender-5.0.1-linux-x64/blender。依赖复用，无新大模型下载。完整数据需要恢复provenance中的SHA对应路径，不能只clone代码就假设原视频/HERO/预训练INIT权重存在。

1. 在独立新副本准备TASK/config/code；保留现有014冻结结果不覆盖。
2. 依次运行code/inventory.py、prepare_views.py、expand_cameras.py、propagate_background.py、pose_correction.py、true_time_negative.py --solve、pose_audit.py、partition_views.py（--solve仅限无旧结果的新复现副本）。现有目录运行true_time_negative.py仅核对244条冻结背景观测，不重跑优化；B1仅研究候选，具体采用策略见POSE_ADOPTION_AUDIT。
3. CPU控制：code/geometry_preflight.py、depth_camera_audit.py、true_time_negative.py。正式串行GPU：code/driver014.py C，然后code/pipeline_remaining.py。后者包括工程检查点恢复、B控制、D/E及最终冻结。
4. 全部预测与尺度冻结后运行code/wait_evaluate.py：只读梯度诊断（record-only保留原加和测试FAIL，不放宽阈值）→固定原生观测→64阶几何/Blender BVH→统一最佳SE3。GT访问由显式冻结门控。
5. code/figures_A.py、figures_B.py、figures_final.py、posthoc_diagnostics.py、report014.py；最后运行validate_delivery.py。中断后已完成FINAL不重训；未完成的训练从完整ACCEPTED checkpoint恢复。旧的源码版本按SHA归档。若需逐字节重现早期C0实现，使用provenance/source_versions对应快照；后续工程加速的等价检查另列。相同种子不宣称CUDA原子运算的位级一致。

本实验的正式预测与尺度已冻结，train014.py禁止在原目录继续更新。检查点迁移必须建立新隔离运行，保持参数、优化器、RNG和原始坐标；仅加载权重不能称完整续训。除评价GT访问外，优化器路径禁止读取audit_only/evaluation_only/.blend及原始GT资产。
