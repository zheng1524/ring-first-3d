# MINIMAL_FIX_PLAN（023 的最小改动）

按依赖排序；每项给出 owner、最小 diff、测试、退出条件。

| # | 修复 | owner file/function | 最小 diff 方向 | 测试 | 失败即退出 |
|---|---|---|---|---|---|
| F1 | 正式目标与 autograd 一致 | `core/torch_objective.py` | 镜像 `shared_se3.objective`：加 `W_RING*ring_term`、`W_EPI=0.02`、相同归一；或用 torch 重写 Ring（对固定曲线点可微） | 同数据同 q 的 total 与逐项梯度，autograd vs FD ≤1e-6 相对 | 不一致 → 停 |
| F2 | checkpoint + 真 resume | `core/shared_se3.py::optimize` | 返回 `(q, m, v, step, best, hist)`；新增 `resume=` 参数 | 跑 20 步存盘→重载→跑 20 步 == 连续 40 步（逐位） | 不可复现 → 停 |
| F3 | 回滚测试非空 | `tests/test_optimizer_corrective.py` | 注入确定性失败损失（如返回 +inf 的末步）并观测 m/v 不变 | 强制拒绝 1 步，断言 q/m/v 不变 | 无法观测 → 停 |
| F4 | per-view K + 真 SHA | `core/run_corrective.py`、`core/w0_adapter.py` | 用 `v['K']` 替换硬编码；`source_sha=sha256(file)` | K 改为 980 时应失败/改变结果；sha 长度=64 | 仍硬编码 → 停 |
| F5 | n_raw 统计 | `core/cross_video_matches.py` | `n_raw=len(ka)*len(kb)` | 单测：两图 6000/5000 → 3e7 | - |
| F6 | 双侧留出 | `core/run_corrective.py` | 004/005 各自排序切分 + 地标级/时间簇冻结 | 004 视角不得同时出现在两侧 | 泄漏 → 停 |
| F7 | 多视角地标 + `L_F` | 新适配 `019/features019`、`020/features020` | 先 005（16 ACCEPT）建地标，再 004（6 ACCEPT）2D-3D | `L_F` 非零、双向重投影、3D 中位误差 | 无 3D 身份 → 保持 BLOCKED |
| F8 | Ring 目标语义 | `core/ring_objective.py`（新文件，复用 `ring020` 逻辑） | M/I/C/O + 可见弧；或证明与 `torus_contours` 等价 | 与 RingRenderer 在同相机/同观测上的逐项对照 | 不等价 → 标 NOT_EQUIVALENT |
| F9 | 受控实验重写 | `tests/test_controlled.py` | A2 观测由 H_true 生成；A3 断言 R/t 误差阈值；A6 固定观测只变模型 | 已知 GT 恢复，阈值事先锁定 | 不恢复 → 报失败（不调阈值） |
| F10 | 配置哈希前置 | `core/run_corrective.py` | 运行前 `config_sha` 必须非空；写入 run manifest | 断言 sha 长度 64 | 为空 → 停 |

## 不做

不重写 W0/DXY/Ring CAD/HERO/Body；不在 023 调权重；不因为 G01/G05 未过门限而改阈值。
