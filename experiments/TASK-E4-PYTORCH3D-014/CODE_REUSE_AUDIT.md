# 014历史代码复用审查

已阅读011/012/013报告、013方法/失败/逐参考数据，以及ViewPartition报告与batch_a/common/registration/matching。旧20–30视角文件只有规划，不能当作已执行资产。

|模块|路径|决定|理由|
|---|---|---|---|
|VIEW_PARTITION|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/batch_a.py|MINIMAL_ADAPTATION|reuse camera direction/complete-link/asset interfaces; drop cleaning andoldadmission conditions|
|VIEW_PARTITION|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/common.py|MINIMAL_ADAPTATION|reuse camera direction/complete-link/asset interfaces; drop cleaning andoldadmission conditions|
|VIEW_PARTITION|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/matching.py|MINIMAL_ADAPTATION|reuse SIFT mutual ratio and per-match region/holdout labeling; cachefirst, noMASt3Rsearch|
|VIEW_PARTITION|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/registration.py|REFERENCE_ONLY|reuse CV2PnP/robustSciPy formulas only; oldPolypHERO3D andperframeposegraph excluded|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/p3d.py|MINIMAL_ADAPTATION|same renderer/axialdepth/RingAware/freevertices; video weighting, split2Dterms, per-viewgradient accumulation|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/depth_terms.py|MINIMAL_ADAPTATION|same renderer/axialdepth/RingAware/freevertices; video weighting, split2Dterms, per-viewgradient accumulation|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/free_model.py|MINIMAL_ADAPTATION|same renderer/axialdepth/RingAware/freevertices; video weighting, split2Dterms, per-viewgradient accumulation|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/contour_objective.py|MINIMAL_ADAPTATION|same renderer/axialdepth/RingAware/freevertices; video weighting, split2Dterms, per-viewgradient accumulation|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/safe_geometry.py|REJECTED_FOR_014|sparse ringmaterial sampling missed faceinterior; replacecandidateguard with dense32barycentric +FCL andindependent64audit|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/best_rigid.py|DIRECT_REUSE|same96seedscale1SE3only; GTaccessafterall014predictions|
|013|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013/code/evaluate_all_rigid.py|DIRECT_REUSE|same96seedscale1SE3only; GTaccessafterall014predictions|

额外拒绝：旧按组/形态保护清理、固定历史角度阈值和资格拒绝器；不改变冻结Type2，不用HERO息肉点做相机配准，不用ICP强拉视频。历史照片缺公制位姿保留清单，不伪造相机。

成熟细分参考：[PyTorch3D SubdivideMeshes](https://pytorch3d.readthedocs.io/en/latest/_modules/pytorch3d/ops/subdivide_meshes.html)、[Blender BMesh subdivide_edges](https://docs.blender.org/api/current/bmesh.ops.html)。smooth=0，新点仅原面插值，细分先做形状不变控制；新增形状只来自后续真实监督。
