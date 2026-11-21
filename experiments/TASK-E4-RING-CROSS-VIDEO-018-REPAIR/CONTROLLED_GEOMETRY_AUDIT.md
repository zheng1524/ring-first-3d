# CONTROLLED_GEOMETRY_AUDIT

## 合法相机（P0.1）

`geometry.look_at(C)`：`z_c = normalize(target−C)`，`x_c = normalize(z_c×up)`，`y_c = z_c×x_c`，`R=[x_c,y_c,z_c]`。
断言：`RᵀR=I`、`det(R)=+1`、所有场景点 `Z_c>0.2 mm`。
`test_mirrored_camera_rejection` 证明 det=−1 的镜像矩阵会被拒绝（018 的 `rig()` 正是这种）。

## 受控结果（3 seeds × 9 cases，`metrics/SYNTHETIC_RESULTS.csv`）

| case | 中位误差 | 最大误差 | 状态 |
|---|---:|---:|---|
| S0 | 0.000° | 0.000° | IDENTIFIABLE |
| S1 | 0.042° | 0.043° | IDENTIFIABLE |
| S2 | 0.140° | 0.156° | IDENTIFIABLE |
| S3 | 0.028° | 0.057° | IDENTIFIABLE |
| S4 | 0.081° | 0.095° | IDENTIFIABLE |
| S5 | 0.035° | 0.038° | IDENTIFIABLE（**未产生退化，见下**） |
| S6 | 0.000° | 0.000° | IDENTIFIABLE |
| S7 | 122.6° | 165.9° | **DEGENERATE（正确拒绝）** |
| S8 | 0.000° | 0.000° | IDENTIFIABLE |

## S5 的坦白

按任务要求把基线从 b/Z=0.22 缩到 0.007 **并没有**造成退化：绕 Ring 圆心的旋转本身带弦长平移，
所以任何 θ≠0 都自带基线；Sampson 距离又对 E 的尺度不变，于是中位误差始终 ~0.33 px。
真正的纯旋转退化条件是**相机中心落在旋转轴上**。本轮未重构该用例，标 `DESIGN_FLAW`，
不把 S5 计为"退化检测通过"。
