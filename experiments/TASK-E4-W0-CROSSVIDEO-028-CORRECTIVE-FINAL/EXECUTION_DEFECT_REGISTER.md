# EXECUTION_DEFECT_REGISTER（FINAL）

| # | 缺陷 | 影响 | 修复 | 状态 |
|---|---|---|---|---|
| D7 | `epipolar_score` 用 ref_index 过滤 fit 行 | epi 全空，H 只按 Ring | 改按行位置 + 状态字典 | 已修 |
| A2 | F 的 K 顺序颠倒 | 极线误差量纲错误 | `K_other^-T ... K_ref^-1` | 已修（T02） |
| A3 | HOLDOUT 进入优化 | 验证不独立 | FIT-only + 独立 holdout 路径 | 已修 |
| A4 | 旧路线先 H=I 共同三角化 | 旧路线定义错误 | 参考 FIT 三角化 → H-only | 已修 |
| A5 | ring_vector 缺 Centerline | 初始化与 BA 目标不一致 | 加 mid；空边 None | 已修（T05 因 D11 跳过） |
| D10 | `U` 指向旧实验目录 | 结果写入错误目录 | U→FINAL；结果迁移并在 manifest 注明 | 已修 |
| D11 | 测试与 R6 RingRenderer 全局 `R` 耦合 | T05 无法运行 | — | 未修（skip） |
| D12 | BA success=false（20 评价） | 不能称收敛 | — | 如实记录 |
| D13 | 图为 8 面板合成图而非 8 个文件 | 交付形式差异 | — | 如实记录 |
| D14 | W0 自动重放未演练 | 门控缺证据 | — | NOT_EXECUTED |
| D15 | 干净目录全量复跑未做 | 复现性 | — | PARTIAL |
