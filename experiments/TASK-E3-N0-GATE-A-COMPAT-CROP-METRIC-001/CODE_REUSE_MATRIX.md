# Actual code reuse matrix

| Original source | Actual function/interface | Reuse / thin adaptation | Duplicate implementation | File SHA256 |
| --- | --- | --- | --- | --- |
| /home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v1/scripts/common.py | unproject | exact AST extraction; bind task-local IO/whitelist only | No | 12e9eab72765877219191aa9a26bf37d3ffb0c7deb7b55125c4b5d5864201e1e |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | source | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | mesh_scene | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | cast | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | distance | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | ringmesh | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/common.py | ringscene | exact AST extraction; bind task-local IO/whitelist only | No | a5dc4f7872a339f9b488ee9137f7d337254ad33ae0af03f5becfab10eca3d8a2 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/code/hero_tsdf_adapter.py | HEROToTSDFAdapter | exact AST extraction; bind task-local IO/whitelist only | No | 23fe3cfdad39087f21b598f62e747cd5368374b02b0112e0e249d1cd6c5d3e91 |
| /home/liu/ring_first_3d_e3n0/visualization/real_p0_renderer.py | scaled_intrinsics | direct import unchanged | No | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 |
| /home/liu/ring_first_3d_e3n0/visualization/real_p0_renderer.py | project_camera | direct import unchanged | No | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 |
| /home/liu/ring_first_3d_e3n0/visualization/real_p0_renderer.py | camera_rays | direct import unchanged | No | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 |
| /home/liu/ring_first_3d_e3n0/visualization/real_p0_renderer.py | basis | direct import unchanged | No | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 |
| /home/liu/ring_first_3d_e3n0/visualization/real_p0_renderer.py | configure | direct import unchanged | No | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 |
| /home/liu/ring_first_3d_e3n0/visualization/same_camera_scene.py | SameCameraScene.cast/ring_image/scale_bar | direct unchanged | No | fdd64599676bd88f659f6f9b7317835d43c6db2176e9fb9fce8849c25b807cf1 |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/VIEW_COVERAGE_SELECTION.csv | historical View Partition | read inherited block IDs; fixed new order | No | 643d6f3cb898c19ab0c156bdef22037d04391b7968ac2ebab2b45cf74099b89c |
| /home/liu/ring_first_3d_e3n0/experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv | Camera Gate | read only, retain INSUFFICIENT_EVIDENCE | No | cca5c1d70d68d58216c7c5e64cf7a0d17b7468d4707b83ac29c8e4a5e4bdf969 |

Only new geometry is the explicit per-view crop affine / identity sampler (crop.py). Existing source loader, native K, inverse projection, pinhole projection and CAD raycasting are executed unchanged. No D0 module main is imported, avoiding writes to D0 or its model-import guard. Original Raw Mesh is only a comparison/domain diagnostic, never a pseudo-depth input.
