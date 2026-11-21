# HISTORICAL_REGISTRATION_AUDIT

## 结论先行

**历史确实实现过 Ring 约束的跨视频配准，且是完整 SE(3)（不是纯 yaw）。**
可复用的是它的**可辨识性分析**与**跨视频身份构建方法**；不可复用的是它的**优化器与结论**（独立评价没有改善）。

## 各路线源码级证据

### 路线 1：Ring/RGB 跨来源配准（早期）

`src/ring_first_3d/mainline/lineage/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/`
- 未在本轮找到可运行的 `register.py`/`ceres_backend.py` 实体（目录内仅代码壳），
  历史报告 `MULTI_SOURCE_REGISTRATION_REPORT.md` 提到"005 相机借助 004 的 RGB 地图完成 PnP 初始化"——
  **这不是"先独立恢复再对齐"，而是 004→005 的单向引导**，不能算跨视频相对位姿求解。

### 路线 2：020 低维几何修正

历史目录/提交未在本工作树的 lineage 中找到独立可运行实体（仅有 021 报告中对 `020R2`/`020 Mask-only` 的引用与对比数字）。
→ 判定 `SOURCE_NOT_RECOVERED`（只有二手引用，无源码）。

### 路线 3：021 共同地标 BA（**找到真实实现**）

`.../TASK-E4-RING-ANCHORED-JOINT-BA-021/code/`

| 文件 | 实际内容（源码级） |
|---|---|
| `ba021.py` | `CommonPoints(scope)`：**一个共享位姿 `H`**（`exp_se3(q*scale)`，见 L42/L44）施加到 video-004 一侧相机（identifiability 中 `C = H@C if side else C`），每个跨视频身份一个三维点 `X` |
| `identifiability021.py` | Schur 消元 + 信息矩阵谱分解：`numerical_rank`、`condition_full`、`conditional_std_proxy_mm_rad`、`point_gradient_video_cosine` |
| `identity021.py`/`prepare021.py` | 18 条跨视频背景身份、553 个描述子、547 条跨图 RGB-RANSAC 链接 |

**优化自由度**：`H ∈ SE(3)`（6 DoF）+ 18×3 地标自由度；**不是纯 yaw**。

**真实指标（TECHNICAL_REPORT）**：
- B1→B2 训练目标 0.071305→0.067097（下降）
- **HOLDOUT IoU 0.897414→0.895871（下降）**
- 未参与轨迹 HOLDOUT F 1.151664→1.201915（**变差**）
- HERO 支持 34.7308%→34.3268%（下降）
- 条件 MAE 0.810128→0.801347 mm，但严格共同观测 MAE 仅 0.796258→0.795371（新增 25 584 / 丢失 35 836 有效观测）

**可辨识性**：消元后位姿信息秩 6/6、条件数 ≈497；共同点自由化把固定点位姿信息降到约 1/3；
**两视频点梯度余弦 −0.87/−0.92**（近反向）。

**失败教训（对 017 直接相关）**：
1. 训练目标下降 ≠ 独立评价改善；
2. 只有背景地标、无 Polyp 同名锚；
3. 固定相机导致 004 侧直接 pose 梯度为 0（参数化事实）；
4. 历史 R2 矩阵正交误差 5e-8 未通过 1e-9 检查——**数值身份必须严检**。

### 路线 4：014–016 近期

| 任务 | 做法 | 局限 |
|---|---|---|
| 014 | 004 沿用旧 005 相机 + 688 对 SIFT 计数 | 相机本身不合格；未做 Ring 约束 yaw |
| 015 | 统一 W0 入口；004 重恢复 6/16 ACCEPT | 未处理前段分支 |
| 016 | 诊断出 raw00181 处 119.6°/84.7 mm 分支接缝；量化背景匹配 11–17 个/对 | 仍未进入 Ring 约束的 yaw 求解 |

## 复用决策

**`REUSE_PARTIAL`**

| 复用项 | 来源 | 用途 |
|---|---|---|
| 跨视频身份构建（描述子 + RGB-RANSAC 链接） | 021 `identity021.py` | 017 的 SIFT 匹配筛选基线 |
| SE(3) 参数化尺度约定（`pose_scale`, 0.6 mm / 5°） | 021 `ba021.py` | 只作为单位约定参考，本轮为 1-DoF yaw |
| Schur/秩/条件数/梯度余弦 诊断 | 021 `identifiability021.py` | 本轮 yaw 可辨识性判据 |
| 纯 yaw 求解器 | **无历史实现** | 本轮 `IMPLEMENT_MINIMAL`（仅一维搜索，复用 cv2 求 E/Sampson） |

不复用：021 的优化器与数据（跨视频地标需重建，且其独立评价为负结果）。
