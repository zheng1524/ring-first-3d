# 本轮实际代码复用

既有权重和核心实现只读；下表均绑定源码SHA。新代码仅组织分区、匹配、派生配准和聚合。

|功能|实际入口 / 函数|复用|最小适配|
|---|---|---|---|
|视频读取/取帧|/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v12_pose_matching_audit/scripts/match12.py : cv2.VideoCapture / cached ledger|是|reuse cached frames; no new video decoder|
|图像/Mask|/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/inventory.py : camera_frame_inventory|是|source SHA and labels unchanged|
|Ring-First读取|/home/liu/ring_first_3d_grazing/experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/common.py : source / target_source|是|exact frozen K/c2w|
|HERO推理|/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1/scripts/run_mvs_adapter3.py : load_official|是|AST exact function, path globals rebound only|
|XYZ/开放原面|/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py : unproject / depth_mesh|是|AST exact original mesh function; no second backprojector|
|清理|/home/liu/ring_first_3d_grazing/experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/cleaning.py : original fields / cohorts|是|T2 + original connectivity and stalk protection; no angle optimization|
|MASt3R|/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v8_registration_narrow_baseline/vendor/mast3r/mast3r/model.py : AsymmetricMASt3R.from_pretrained|是|official frozen local implementation|
|匹配接口|/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v12_pose_matching_audit/scripts/match12.py : loss_of_one_batch / fast_reciprocal_NNs|是|full-image and explicit ROI adapters|
|A→B|/home/liu/ring_first_3d_grazing/experiments/TASK-PHASED-GRAZING-SELECTIVE-AGGREGATION-001/code/geometry.py : projection / metric / common_metric|是|exact bounded module reuse|
|XYZ/GLB|/home/liu/ring_first_3d_view_partition/visualization/real_p0_renderer.py : draw_rgb_points / SameCameraScene|是|existing style; no new rendering system|
