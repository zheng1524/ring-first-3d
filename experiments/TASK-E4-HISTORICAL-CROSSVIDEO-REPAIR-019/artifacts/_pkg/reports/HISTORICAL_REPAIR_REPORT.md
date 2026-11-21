# HISTORICAL_REPAIR_REPORT

```
HISTORICAL_SOURCE_RECOVERED:      PASS
HISTORICAL_LANDMARKS_VERIFIED:    PASS (file identity + 153 landmarks; per-observation check BLOCKED)
HISTORICAL_3D_RANSAC_REPRODUCED:  PASS  (5/18, identical to history)
HISTORICAL_RING_GRADIENT_VALID:   BLOCKED (pytorch3d absent)
HISTORICAL_RGB_GRADIENT_VALID:    BLOCKED (pytorch3d absent + feature npz missing)
HISTORICAL_OBJECTIVE_REPRODUCED:  BLOCKED
HISTORICAL_SE3_OPTIMIZATION_EXECUTED: BLOCKED
G03_ACTUAL_020_MODULES_EXECUTED:  BLOCKED (stop condition)
CODE_AUDIT_PACKAGE_COMPLETE:      COMPLETE
```

## 1. 纠正上一轮的三个错误

### E1 提交确实存在

`git fetch origin 5636aaebd61a3d53b69f528692c4c7095df46508` 成功，`git cat-file -t` = `commit`，
`ls-remote` 命中。**上一轮"该提交不存在"的说法是错的**——本地仓库只有 38 个提交且从未 fetch 过这个对象。
正确表述应为"当前本地工作树未包含该对象"。

### E2 软链接已恢复

历史 `020/landmarks/CROSS_004.npz` 在 git 里是 **mode 120000 的符号链接**（115 字节），
指向已删除的 `/home/liu/ring_first_3d_e4_sdf_localization/.../019/landmarks/CROSS_004.npz`。

在隔离回放目录 `historical/replay_G01/` 中恢复为相对链接：

```
020/landmarks/CROSS_004.npz -> ../../TASK-E4-RING-POLYP-REGISTRATION-019/landmarks/CROSS_004.npz
```

验证：`resolve()` 相同、SHA256 相同（`1839a9fc8f948b79…`）、**153 个地标**、`des (153,128)`、`covariance (153,3,3)`。
**没有重新三角化，没有伪造输入。**

### E3 5/18 与 2/18 的口径不同 —— 已分别执行

| 变换 | <0.75 mm | <1 mm | 中位 mm | 中心 mm | 倾角° |
|---|---:|---:|---:|---:|---:|
| **历史 3D RANSAC**（`named_candidate020`，256 次三点采样） | **5/18** | 6 | 1.627 | 2.160 | 4.852 |
| 冻结 R0（RoMa） | 2/18 | 3 | 2.916 | 0.115 | 2.536 |
| 冻结 R3 | 2/18 | 3 | 3.012 | 0.108 | 2.275 |

**历史 5/18 被完整复现**（同一份地标、同一份 18 对身份、同一 RNG 种子 20261111）。
上一轮的 2/18 用的是冻结 R0/R3 变换，与 5/18 不是同一个估计器 —— 那个"MISMATCH"是我比较错了。

## 2. 真实执行到的历史代码（`ACTUAL_020_EXECUTION_TRACE.json`）

| 步骤 | 脚本 | 状态 | 证据 |
|---|---|---|---|
| 1 | `setup_inputs020.py` | BLOCKED | `common.py` 的 REPO 指向已删除工作区 |
| 2 | `validate_landmarks020.py` | FAIL | `features/G01_004_ref08.npz` 缺失（逐视角 SIFT npz 未入库） |
| 3 | **`named_candidate020.py`** | **PASS** | 输出 `NAMED_3D_PROPOSAL 18 5 2.1602 4.8522 False` |
| 4 | `gate020.py` | BLOCKED | `ModuleNotFoundError: pytorch3d` |
| 5 | `feature_gate020.py` | BLOCKED | 同上 + feature npz 缺失 |
| 6 | `objective020.py` | BLOCKED | 依赖 `p3d` |
| 7 | `optimize020.py` | BLOCKED | 依赖 `objective020` |
| 8 | `evaluate020.py` | NOT_RUN | 触发停止条件 |

**pytorch3d 在所有本机 python 环境（含 polyp venv 的 torch 2.7.1+cu128）中都不存在**，
而 `ring020.py` → `p3d.py` 第 3 行就 `from pytorch3d.structures import Meshes`。
这是硬阻断，不是"读源码代替执行"。

## 3. 停止条件

按任务 §6：历史 objective 无法重算 → **停止 G03 迁移**。
`ACTUAL_G03_MODULE_CALL_GRAPH.json` 明确记录：本轮 G03 未执行任何 020 模块；
并声明上一轮 G03 只用了 018-REPAIR 的 yaw 求解器，**那不是 020 迁移**。

## 4. 下一步恢复所需（具体到可操作）

1. 安装 pytorch3d（源码编译，匹配 torch 2.7.1+cu128）——这是唯一能解锁 gate/objective/optimize 的路径；
2. 逐视角 SIFT 特征 npz（`020/features/G01_*.npz`）需要从 019 的 `features019.py` 重新生成，
   或从历史外部工作区残片按 SHA 找回；`validate_landmarks020.py` 依赖它们做逐观测核验。
