# TRIANGULATION_IDENTITY_VALIDATION

## 修复

`feature_id ≡ landmark_id`，每相机维护 `xy[view][landmark_id] = uv`，三角化时以 `(view, landmark_id)` 为稳定键；
**不再**从轨迹内部顺序推导特征号。

## 测试（`tests/test_triangulation_identity.py`，4/4 PASS）

| 测试 | 内容 | 结果 |
|---|---|---|
| T1/T3 | 6 台 GT 相机、12 地标、无噪声 → 三角化 vs GT | 最大误差 **< 1e-6 mm** |
| T2 | 全部 66 对地标间距离 | 与 GT 差 **< 1e-6 mm**（无串号） |
| T4 | 打乱 feature 编号并同步更新映射 | 结果逐点相同（< 1e-9） |
| T5 | 删掉某相机 3 个观测 | 其余 9 个地标位置不变（< 1e-6） |

## 产物

- `TRIANGULATION_GT_ERRORS.csv`（逐地标误差）
- 图 2：`02_triangulation_identity_check.png`
