# E3 实际代码复用审计

读取实际文件并AST核对入口，完整记录见 `provenance/E3_CODE_REUSE_AUDIT.json`。所有历史模块main均未调用；真实数值审计执行的入口在下表明确标注。本轮未导入MonoSDF/MapAnything/MASt3R模型、未打开checkpoint。

## native HERO adapter

文件：`/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v1/scripts/run_mvs_adapter3.py`。分支 `main`，commit `4483e25ede3eee1b6eaf96254d2544152f935c0d`，文件SHA256 `14315d808e71a136dad71877c52336473fb2431428451e0a3b3de6f894e7d481`。

入口：`load_official(size)` L7。

输入输出：RGB + fixed K/c2w -> archived native depth; no new call；单位：mm native axial Z。真实验证：STATIC_ONLY_INFERENCE_NOT_AUTHORIZED。必要输入：native packs exist for 40 sources; weights not opened。依赖本地未上传大资产：是。最小适配/限制：No inference adapter required this round。

## original geometric pipeline

文件：`/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py`。分支 `main`，commit `4483e25ede3eee1b6eaf96254d2544152f935c0d`，文件SHA256 `12e9eab72765877219191aa9a26bf37d3ffb0c7deb7b55125c4b5d5864201e1e`。

入口：`unproject(z, pose, uv, K)` L40; `depth_mesh(depth, mask, pose, K, color)` L63。

输入输出：Z,pose,UV,K -> XYZ; depth/mask/color -> original image-adjacent faces；单位：mm axial Z / world mm。真实验证：unproject executed all36; depth_mesh static only。必要输入：36 raw mesh / original UV+faces exist; cfg file present。依赖本地未上传大资产：是。最小适配/限制：Keep archived face IDs; do not retriangulate; archived .75mm jump cfg required。

## exact source-index geometry loader

文件：`/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001/code/evidence.py`。分支 `exp/TASK-NEURAL-E0-COMPARE-001`，commit `26a3f82b2b6644b78c8560650fdc319fbb30322f`，文件SHA256 `90db9e31b3f37f1a6760306c16ee90367cd914f51874ab02973ae3d9af90c6b0`。

入口：`points(cid)` L13; `combine(sid, kind, only_ids=None)` L19; `f3(sid)` L27。

输入输出：frozen source registry -> original XYZ/RGB/UV/faces; historical face subsets；单位：mm。真实验证：EXECUTED_EXACT_AST。必要输入：all36 raw/Cleaned; first14 F2; five F3 joint NPZ。依赖本地未上传大资产：是。最小适配/限制：source-only namespace; skip legacy neural/MapAnything mains。

## original face topology

文件：`/home/liu/ring_first_3d/experiments/TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001/code/run.py`。分支 `exp/TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001`，commit `3c87cf25b690c56df7607f3b3a11f70a6c3453b3`，文件SHA256 `df0ac71b18a315751b54735d80d79776c9dc571cb90a21d06e7fab210a525449`。

入口：`source_components(pack, uv)` L46; `face_components(faces)` L67; `edge_counts(faces)` L72。

输入输出：original faces -> shared-edge components/boundary counts；单位：indices; areas separately mm2。真实验证：EXECUTED_EXACT_AST。必要输入：all36 indexed original meshes。依赖本地未上传大资产：是。最小适配/限制：bind returned namespace explicitly; no topology mutation。

## historical reprojection and geometry

文件：`/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/code/geometry.py`。分支 `exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001`，commit `fa50f68f27fd1679276e3ac549322cda05fc4191`，文件SHA256 `2c6b51ca339a5d113dd52285e73a02f7293640c693f8f48c2912ca96ed3d3813`。

入口：`mesh_scene(P, F)` L11; `raymesh(P, F, t)` L15; `projection(P, C, t, ids=None, kind=None)` L18; `common_metric(pred0, pred1, t)` L29; `area(P, F)` L35; `topology(s, deleted)` L40; `direction(P, N, reliable, weights, pose)` L42。

输入输出：original XYZ/F + frozen target K/c2w -> ray hits / fixed-pixel statistics；单位：camera axial mm; area mm2。真实验证：STATIC_AUDIT_AND_MATCHED_CURRENT_WRAPPERS。必要输入：five scene meshes/cameras available。依赖本地未上传大资产：是。最小适配/限制：CID wrapper uses same Open3D BVH + existing camera_rays; full old module main prohibited。

## historical CAD audit

文件：`/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/code/cad_audit.py`。分支 `exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001`，commit `fa50f68f27fd1679276e3ac549322cda05fc4191`，文件SHA256 `044ca8c0e44468058d3e66644b59cd9df394348bb56847ae891d98c58a774006`。

入口：`main()` L3。

输入输出：fixed Ring + source geometry -> archived CAD diagnostics；单位：mm。真实验证：STATIC_ONLY_MAIN_NOT_CALLED。必要输入：Ring CAD files and old reports available。依赖本地未上传大资产：是。最小适配/限制：reuse SameCameraScene for queries; never call historical main。

## MASt3R historical matches

文件：`/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/matching.py`。分支 `exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001`，commit `4adfe3aac780bf319aebf9cdd137f42e1e0eb055`，文件SHA256 `e86159011da85f49ddb8cb3fc341deb3a45e21e0b2759a9f73274e0d1f3c610e`。

入口：`backmap(p, meta)` L37; `main()` L38。

输入输出：RGB pair + affine maps -> existing match candidate NPZ；单位：pixels; NOT metric geometry。真实验证：CACHE_ONLY_MAIN_NOT_CALLED。必要输入：matching_comparison.json, registration_edges.json, CROSSVIDEO_GATE.json exist。依赖本地未上传大资产：是。最小适配/限制：cached matches are not independent physical correspondence labels。

## historical pose qualification

文件：`/home/liu/ring_first_3d_view_partition/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001/code/registration.py`。分支 `exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001`，commit `4adfe3aac780bf319aebf9cdd137f42e1e0eb055`，文件SHA256 `d168307472f8a6418e9a084aa337d794f4afab9c5f85ad6e93f88bbf5c2cde96`。

入口：`anchors(pair, method)` L14; `qualify_independent(edges)` L58; `pose_graph(edges)` L67。

输入输出：cached matches + frozen geometry -> archived candidate transform / diagnostic checks；单位：mm。真实验证：STATIC_ONLY_NO_PNP_OR_OPTIMIZATION。必要输入：cross-video gate fusion_certified=false; photos c2w null。依赖本地未上传大资产：是。最小适配/限制：do not adopt pose_graph operational unified flag as certified registration。

## shared frozen renderer/camera

文件：`/home/liu/ring_first_3d_e3a/visualization/real_p0_renderer.py`。分支 `exp/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`，commit `fcdcefb13c00a3c940926dd2266137847eb768b6`，文件SHA256 `16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99`。

入口：`basis(angle=DEFAULT_ANGLE)` L57; `configure()` L44; `project_camera(points_mm, K, c2w)` L89; `camera_rays(uv, K, c2w)` L98。

输入输出：real XYZ,K,c2w -> projected UV and unnormalized world rays；单位：axial ray t = camera Z mm。真实验证：EXECUTED。必要输入：bundled original renderer and provenance available。依赖本地未上传大资产：是。最小适配/限制：audit figures add original triangle PolyCollection using exact basis; P0 code unchanged。

## fixed opaque CAD raycast

文件：`/home/liu/ring_first_3d_e3a/visualization/same_camera_scene.py`。分支 `exp/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001`，commit `fcdcefb13c00a3c940926dd2266137847eb768b6`，文件SHA256 `fdd64599676bd88f659f6f9b7317835d43c6db2176e9fb9fce8849c25b807cf1`。

入口：`SameCameraScene(class)` L8。

输入输出：CAD,K,c2w,image_size -> original CAD first ray intersections；单位：axial Z mm。真实验证：EXECUTED。必要输入：both Ring CAD assets exist。依赖本地未上传大资产：是。最小适配/限制：existing .002mm raster ordering epsilon, separate future uncertainty margin。

## source guard and integrity

文件：`/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001/code/common.py`。分支 `exp/TASK-NEURAL-E1-PIPELINE-RECOVERY-001`，commit `af71a6f85328f487b4a319d47e429c3606f5ca33`，文件SHA256 `0af5b736e5c99c7c021c24c6a593ca37ec7f353101cc1b032e3c057a44de9fbd`。

入口：`extract(path, names, ns=None)` L88; `guard(event, args)` L26; `protected_state()` L112。

输入输出：exact AST helpers -> scoped read-only inputs / source SHAs / worktree status；单位：N/A。真实验证：EXECUTED_EXACT_AST。必要输入：E1 registry/reuse source and all history worktrees exist。依赖本地未上传大资产：是。最小适配/限制：deny Torch/checkpoint imports and scope writes to E3-A。

## E2.7 failure lineage

文件：`/home/liu/ring_first_3d_neural_e2p7/experiments/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001/code/common.py`。分支 `exp/TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001`，commit `fcdcefb13c00a3c940926dd2266137847eb768b6`，文件SHA256 `44735851ce7f2b366d93ef6734a284be2995312b05e57b72ffb6132329a5e264`。

入口：仅报告/元数据读取，禁止导入该运行时。

输入输出：small existing report/metrics -> failed one-step pilot evidence；单位：mm; voxel volume is not physical volume。真实验证：STATIC_ONLY_NO_IMPORT。必要输入：E2.7 technical report exists。依赖本地未上传大资产：是。最小适配/限制：never import neural/GPU-authorized runtime; no E2.7 re-execution。

depth_mesh 的归档配置路径为旧 ring_first_v1/config.json，原跳变阈值0.75mm；本轮不重新三角化。所有原面直接从旧PLY/NPZ核对。薄适配只做源格式桥接、Open3D BVH查询、固定分母统计和画图；不实现第二套相机/反投影。第三方CPU几何库缓存为旧vendor，模型权重不属于本轮运行依赖。源码SHA与检查时所属commit一起给出，不能用commit替代本地实际文件哈希。
