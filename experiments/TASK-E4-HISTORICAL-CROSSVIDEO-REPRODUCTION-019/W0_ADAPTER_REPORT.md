# W0_ADAPTER_REPORT

## 接口

`adapters/w0_to_legacy020.py`

- 输入：`camera_mainline/G03/video00{4,5}/camera_result.npz`（`c2w/K/ids/raw_frames/admission`）+ `admission.csv`。
- **按 view id 关联**，不依赖数组顺序。
- 输出 019/020 需要的 `id/K/T/cache/role`，`cache` 来自 006 的 `PREPARED.json`（RGB+labels 同一 npz）。
- 图像尺寸与 K：当前缓存为 640×360，与历史一致；若不一致必须先改 K 与全部二维坐标（本适配器不静默缩放）。

## 坐标约定

`adapters/coordinate_adapter.py`：

```
H_005<-004 = inverse(H_004<-005)
T004_in_005 = H_005<-004 @ T004
X005 = H_005<-004 @ X004
```

`COORDINATE_CONVENTION_AUDIT.json` 记录 source/target frame、matrix、inverse、units=mm、handedness=right、pose=c2w。

## 测试（7/7 通过）

`test_SE3_inverse`、`test_c2w_composition`、`test_world_point_transform`、
`test_scale_and_relative_motion_preservation`、`test_ring_axis_rotation_preserves_radius`、
`test_normal_parity`、`test_pose_validity`。
