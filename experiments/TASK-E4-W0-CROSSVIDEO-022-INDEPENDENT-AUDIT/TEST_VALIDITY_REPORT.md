# TEST_VALIDITY_REPORT — 每个"通过"到底证明了什么

| 测试 | 断言内容 | 证明力 | 证据 |
|---|---|---|---|
| `test_se3_corrective::test_jacobian_rank_six` | 6 列差分雅可比秩=6 | **有效**（证明 6 参数独立） | T2 同源差分；秩=6 |
| `...::test_pure_translation/rotation` | R 不变 / t=0 | **有效** | 数值 1e-12 |
| `...::test_scipy / test_pytorch3d` | 与成熟实现一致 | **有效** | 1e-12 / 1e-9 |
| `test_ring::test_ring_yaw_symmetry` | 同时旋转相机+观测后 loss 不变 | **无效**（恒等成立） | T5：0.0 by construction |
| `test_gradient::test_autograd_matches_finite_difference` | torch 函数 autograd vs FD | **无效用于正式目标** | T1：该 torch 函数不是正式目标 |
| `test_optimizer::test_resume_equals_uninterrupted` | 两次从头运行结果相同 | **无效**（无 checkpoint，等于重复同一调用） | T3：无 state 参数 |
| `test_optimizer::test_adam_rejection_restores_state` | 拒绝后恢复 | **条件性**，仅 acc==0 时断言；m/v 不可观测 | T3 |
| `test_optimizer::test_cumulative_*` | 累计边界 | **有效** | 0.163 mm / 3.546° < 1.2/10 |
| `test_data_contract::test_unknown_status_not_accepted` | 只检查 ACCEPT 集合 | **部分有效**（未构造 UNKNOWN 输入） | 代码审查 |
| `controlled.py A2` | 平移 0.008 mm | **无效**：观测在 identity 生成，data 中无 H_true | T5：L(identity)=0 |
| `controlled.py A3` | 记录 5.98° | **无断言**（只记录） | 代码审查 |
| `controlled.py A6` | Ring 对 yaw 不变 | **无效**（同 §test_ring） | T5 |

## 结论

19/19 "通过"里只有 **SE(3) 参数化、Sampson 定义、累计边界、数据 fail-closed** 四类真正有证明力；
关于"梯度已由 autograd 验证"、"resume 可复现"、"Ring 对称性已验证"、"A2/A6 受控实验通过"的表述**不成立**。
