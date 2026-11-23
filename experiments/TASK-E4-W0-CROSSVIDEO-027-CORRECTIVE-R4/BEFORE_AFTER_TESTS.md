# BEFORE_AFTER_TESTS

| 测试 | 修复前（R3） | 修复后（R4） |
|---|---|---|
| 联合路径是否使用指定 `rgb_mode` | 否（`P.residuals` 硬编码 Huber） | 是（`residual_vector(..., rgb_mode)`） |
| 大残差 Huber vs 平方 | 无法区分 | 能量差 >1e-3 |
| 小残差 Huber vs 平方 | — | 相对差 <1e-6 |
| `E_terms == 0.5‖r‖²` | 不成立（只取 `[0]`） | **<1e-9**（21 runs） |
| Ring I/C/O 计数 | 把相机 ID 当类别 | 按数组长度，均 >0 |
| 初始化扫描是否改 GT | **改 GT** | 固定 GT，只改 `H_init`/相机/地标 |
| 预算 | 每调用不同 | M2=200、M1/M3=60，逐次记录 |
| 每次运行独立目录 | 是（R3 已修） | 是（`runs/controlled_error_ablation/<group>/<tag>/`） |

全部测试：`tests/test_r4_contracts.py` **4/4 PASS**。
