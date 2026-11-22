# TEST_AFTER_FIX

| 检查 | 修复后 | 结果 |
|---|---|---|
| T1/T3 三角化身份 | 12 地标、6 GT 相机 | 误差 < 1e-6 mm |
| T2 无串号 | 66 对距离 | < 1e-6 mm |
| T4 打乱顺序 | 同步更新映射 | < 1e-9 |
| T5 缺失观测 | 3 个地标缺 1 视角 | 其余不变 |
| L0 GT 残差 | RGB + I/C/O | 0 / 1e-13 / 1e-14 / 1e-13 |
| L1 正对照 | GT 相机 + 三角化地标 | 相机 2.7e-6°、H 1.2e-6°、地标 6.5e-15 mm、success=True |
| L2b H-only（3°） | identity 初值 | H 0.022°、0.0025 mm（success=False） |
| L2a H-only（12°） | identity 初值 | H 7.06°（收敛域外） |
