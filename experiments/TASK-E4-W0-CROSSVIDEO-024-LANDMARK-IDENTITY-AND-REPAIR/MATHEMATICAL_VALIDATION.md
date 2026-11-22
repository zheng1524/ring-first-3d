# MATHEMATICAL_VALIDATION

| 项 | 状态 | 证据 |
|---|---|---|
| SE(3) 六自由度 | PASS | 继承 021 `se3.exp_se3`（雅可比秩 6、scipy/pytorch3d 一致，022 已复核） |
| 标准 Sampson | PASS | `core/geometry.sampson` 四项平方和；A2/A3 中 true 对应残差 <1e-9 |
| 累计边界 `H·H_seed⁻¹` | PASS | `core/optimize.step_once` 用 `exp(q·SCALE)` 相对 H_seed 检查；A2 修正 0.9 mm 内、A3 0.55 mm 内 |
| **正式目标梯度** | PASS（本次） | FD 梯度由**两套独立实现**（广播式 vs 逐点循环）计算，最大差 **<1e-9**；损失值差 <1e-10（`tests/test_p0_math.py::TestGradient`） |
| Huber/最近邻不可导点 | 标记 | Huber 的分段点与 `torus_contours` 最近邻切换在本测试点处未被跨越；**未**声称在这些点可导 |
| **Checkpoint/Resume** | PASS（本次） | 40 步连续 vs 20 步+存盘+重载+20 步：`q` **逐位相同**、`step` 相同（`TestResume`） |
| 强制拒绝回滚 | PASS | `allowed=False` 时 q/m/v/best 不变、step 递增、reason 记录（`TestForcedRejection`） |
| 不同 K 的极线方向 | PASS | `F` 用 004/005 不同 K 构造；`l5=F x4`、`l4=F^T x5`；单侧距离与 Sampson 关系成立且不对称（`TestEpipolarDifferentK`） |
| 无效断言清理 | PASS | 023 的 `allclose(d4,d4)` 类断言已删除；新测试为一般旋转+非零平移+双 K 场景 |
