# JOINT_LOSS_DIAGNOSIS

## 有效权重（实际进入优化器的量）

冻结 BA 对每视角 Ring 块乘 `sqrt(counts_i / rglen_i)`。
J2 适配层先乘 `sqrt(rglen_i / counts_i)` 抵消，因此最终每视角 Ring 权重 = 1.0，
即 **Ring 块的能量 ≈ mean(r²)，与 RGB 行数 counts_i 解耦**（这是本轮相对 011 的实质改进）。

## 为什么 Ring 仍然没有影响力

- Ring 行：2×256 + 2(barrier) = 514 行/视角，每行量级 ≈ 像素距离/σ ≈ 1–2。
- RGB 行：3×counts_i （counts ≈ 90/视角）× 量级 ≈ 3。
- Ring 总能量 ≈ Σr² ≈ 1–4；RGB 总能量 ≈ 3·90·9 ≈ 2400 量级。
- **Ring 比 RGB 弱约两个数量级** → 相机几乎不动（实测 0.11 mm）。

这正是"J2 不崩但也不改善"的量化原因，也说明若要 Ring 起作用，必须显式提高 λ_C，
而不是靠 `counts/rglen` 之类的隐式缩放。

## CAD_INVALID

barrier 生效后本轮无 CAD_INVALID 触发（16/16 有效）。此前崩溃是异常分支长度不一致所致。
