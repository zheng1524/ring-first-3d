# OPTIMIZER_CONVERGENCE_REPORT

| 配置 | success | status | nfev | njev | cost(init→exit) |
|---|---|---|---:|---:|---|
| 027 B1（旧的错误变量） | **False** | 未记录 | 20 | — | — |
| 027 C（旧的错误变量） | **False** | 未记录 | 20 | — | — |
| 本轮 S1b（tri 初值） | **False** | 0（max_nfev 命中） | 80 | — | 见 CSV |
| 本轮 S1b（tri 初值，400 次） | **False** | 0 | 400 | — | 0.631 |
| 本轮 S1b（λ_R=0，400 次） | **False** | 0 | 400 | — | 0.180 |

- `ftol=xtol=gtol=1e-10`，`method='trf'`，`loss='linear'`，`x_scale='jac'`。
- 所有运行均 **未报告收敛**；不得把返回的参数数组当作成功优化。
- SciPy TRF 不暴露信赖域内部状态；**不宣称** checkpoint 可严格恢复求解器内部状态。
  本轮只保存参数/H/相机/地标/配置哈希（`BA_RUN_STATE.json` 由 027 提供，本轮未做续算实验）。
