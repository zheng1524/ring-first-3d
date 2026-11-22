# MATHEMATICAL_VALIDATION

| 项 | 状态 | 证据 |
|---|---|---|
| SE(3) 六自由度 `exp(hat((v,ω)))` | **PASS（继承 021 并复核）** | `core/se3.py` 与 021 同一 blob；雅可比秩 6、scipy/pytorch3d 一致（022 已复算） |
| 标准 Sampson | **PASS（继承）** | `core/se3.py` + `p3_objective` 使用同一公式；P0 测试验证单侧距离与 Sampson 关系 |
| 累计边界 `H·H_seed⁻¹ ≤ 1.2mm/10°` | **PASS（本轮实际生效）** | 修正 0.589 mm / 5.73°，80/80 步接受 |
| checkpoint 保存 | **PASS** | 每 10 步写 `runs/G03/P3_ckpt.npz`（q,m,v,it,best） |
| checkpoint **恢复**等价 | **NOT_DONE** | 未做"重载 vs 连续"逐位比较 |
| 正式 objective 的 autograd/FD 梯度 | **NOT_DONE** | 022 的 P0-A 缺陷仍在；本轮未补 |
| per-view K | **PASS** | 损失用 W0 `camera_result.npz` 的 K（004/005 本数据相同，但代码不再硬编码） |
| 匹配计数 `n_raw` | **PASS** | 023 不再使用 `len(ka) and len(kb)` |
| 受控 GT（A2/A3/A6 修复 + Ring+3D 正对照） | **NOT_DONE** | 见 `CONTROLLED_GT_RESULTS.md` |
