# JOINT_BA_VALIDATION

- 变量：M3b 参数 = 6 (H) + 3N (X)，`n_params` 记录于 `evaluation/OLD_VS_NEW.csv`；
- 但 `success=false`（M2 与 M3b 各 20 nfev，预算内未满足容差）→ **不能宣称收敛**；
- H/X 初值与终值保存在 `ba/old.npz|new.npz`（`H_initial/H/X/X_init`）；
- Ring 能量在 BA 前后记录于 `OLD_VS_NEW.csv`（G03 0.474/0.386；G06 0.231/0.170）。
