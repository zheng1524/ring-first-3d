# COORDINATE_AND_GAUGE_AUDIT

## 约定（经代码核对）

- W0 相机为 **c2w**（`camera_result.npz['c2w']`；`project()` 用 `(X−C)·Rᵀ`）。
- 合成场景：005 相机 `C_gt = T0_005`，004 相机 `C_gt = H_gt @ T0_004`；Ring CAD 与 005 世界同原点。
- **H = H_(005←004)**：`T004_world = H @ T004_W0`，`T005_world = T005_W0`。
- Ring 损失用实际相机 `C`，增量 `H_in = C @ inv(T0)`（026-CORRECTIVE 已验证，1e-12）。

## H 是否多余？

若两段 W0 已经把 004/005 表示在同一 Ring 世界，则 H 应≈I。合成场景中 H_gt=12° yaw + 0.4 mm，
说明 **H 表示两段视频之间的残余刚体变换**（视频级配准），不是重复应用 Ring 坐标。

## 可辨识性

| 自由度 | Ring 能否约束 | 证据 |
|---|---|---|
| yaw（绕 Ring 法向） | **否**（对称） | H_CANDIDATES：Ring 0.003–0.03 平坦，不同 yaw 全部可行 |
| 倾斜 / 平移 | 部分（弱） | Ring 局部精化把候选压到 0.003–0.03 |
| yaw 绝对角 | **必须由 RGB** | 极线误差 0.09–7.3 px 随 yaw 变化 |
| 整体尺度 | 固定（CAD 公制） | 无尺度参数 |
