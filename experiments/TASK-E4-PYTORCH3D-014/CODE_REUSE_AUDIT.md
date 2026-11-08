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

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 11个独立真实物理组，不将多视频或多实验臂算成独立病例 |
| 本算法独立成功 | 11/11生成本路线FINAL014数值模型；继承人工授权011初值，数值输出不等于测量正确 |
| 本算法失败 | 数值模型失败0/11；几何验收失败或自交精度分歧3/11；另G01有Ring接触精度分歧；高度NaN 1/11，严格实体IoU NaN 9/11；逐组见FAILURE_LEDGER.md，未剔除困难病例 |
| 历史测量值回退 | 0；011/012/013仅作明确标识的初值或评价对照，没有补填014测量值 |
| 失败组及具体原因 | metrics/FAILURES.csv、逐臂运行日志、全部原始模型及核心图 |
| 最终统计样本 | 数值模型11/11；各评价项实际可计算N分别汇报，空白CSV为NaN而非0 |
| 是否使用GT选择算法 | 否；C/D/E仅用预登记FIT规则；全部模型/尺度先冻结，GT访问时间在provenance/GT_ACCESS_START.json |
