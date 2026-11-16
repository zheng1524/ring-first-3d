# Research Execution Harness

增量控制入口：[Task Contract 与 Policy Runner](RESEARCH_POLICY_BOOTSTRAP.md) 将现有检查组合为可恢复的授权阶段，检查来源/冻结边界与本地结果卡、manifest、可视化。原 API 和数学模型不变。

任务：TASK-RESEARCH-HARNESS-STORAGE-001，2026-11-16。共享包版本 0.1.0；这是工程验证入口，科学路线与验收状态继续以[技术注册表](registry/TECHNICAL_ROUTE_MATRIX.md)为准。

## 新任务启动

1. 查 [PROJECT_HOME](PROJECT_HOME.md)、模块卡、失败路线和坐标契约，确定技术 ID 与独立任务范围。
2. 固定输入身份、参数、源码 SHA、单位、相机及 FIT/HOLDOUT；在新任务目录调用共享接口。
3. 运行 Preflight、数学契约和三个真实 Smoke Test；缺资产/GPU须为 NOT_EVALUABLE，不得模拟通过。
4. 测试通过后才运行授权的大实验；冻结预测，再独立读 GT 评价，报告失败 NaN 和共同成功样本。
5. 改变科研目标、选用新算法、科研晋升与正式 baseline 验收均需人工批准。工程 PASS 不自动批准新实验。

在仓库根目录运行；脚本使用现有环境，不安装依赖或写入受保护目录：

```bash
bash tools/research/run.sh tools/research/preflight.py --output /tmp/preflight.json
bash tools/research/run.sh tools/research/validate_contracts.py --output /tmp/contracts.json
bash tools/research/run.sh tools/research/audit_reuse.py --output /tmp/reuse.json
bash tools/research/run.sh tools/research/smoke.py --output /tmp/smoke.json
```

`run.sh` 默认绑定本机已登记的 Python 3.12、PyTorch3D runtime、E4 evolution 的 scikit-image、PMGR-R1 的 FCL、既有 Open3D vendor。可通过 `RING_FIRST_PYTHON`、`RING_FIRST_P3D_RUNTIME`、`RING_FIRST_EXTRA_PACKAGES`、`RING_FIRST_FCL_PACKAGES`、`RING_FIRST_OPEN3D_VENDOR` 改路径；DXY 用 `DXY_ROOT`。不设置 CUDA_VISIBLE_DEVICES；DXY CPU 调用与 CUDA renderer 可在同一进程运行。其他机器需准备对应环境，版本详见测试报告。不得把未提供的真实资产当作可重建的模拟 fixture。

## 共享接口与边界

```python
from ring_first_3d.adapters.dxy import measure_pixels
geometry = measure_pixels(rgb_uint8, class_mask_uint8,
    inner_diameter_mm=10., source_id=frozen_id, dxy_root=dxy_checkout)
# geometry: available, center_px, basis_px, quality, source; 无毫米直径字段

from ring_first_3d.contracts.coordinates import ellipse_coordinates
local_uv = ellipse_coordinates(native_uv, geometry['center_px'], geometry['basis_px'])

from ring_first_3d.views.selection import select_views
chosen = select_views(fit_views, 'quality_diversity', max_views=8,
    baseline_ids=baseline, holdout_ids=holdout)

from ring_first_3d.rendering.pytorch3d_renderer import MetricRenderer
renderer = MetricRenderer(frozen_014_pack, case_name)
output = renderer.render(view_id, vertices_mm=world_mm_vertices)
contour_loss = renderer.contour_loss()
guard = renderer.geometry_guard(chart)
```

| 技术 | 调用/复用方式 | 已实测范围与约束 |
| --- | --- | --- |
| T01/T03 | 正式 DXY `measure_frame`；适配 provenance/输出 | 固定 75d58ca5，验证 55 个 Python 源文件；输入 RGB，调用时转 BGR。只消费像素几何和非公制质量，无旧测量回退 |
| T04 | `ellipse_coordinates` | 原生像素 `(uv-center) @ inv(basis).T`；基础数学契约实现，非椭圆重检测 |
| T10 | `quality_features`、`quality_diversity` | 原 AST 质量计算与质量/方向贪心；同视频、非空 baseline，历史 cap 8，max_views 是结果前缀 |
| T11 | `direction_quota` | 原 AST 方向配额、3°排重、权重；显式 direction_block 和 mandatory_ids，历史 cap 8 |
| T12 | `max_coverage` | 原 `greedy`，显式可见性矩阵和 source-tagged proxy 权重；历史 cap 36，不宣称真实解剖面积 |
| T13 | `hero_support` | 原 `support_pairs` 与三支持图排重 AST；显式 FIT target、原生 K、特征 provider 和本任务 cache_root；与覆盖策略独立 |
| T24 | `MetricRenderer` | 原 Case/renderer/aware；真实 mm Body/Ring/Cameras；固定输入 pack、固定拓扑，原生 640×360→320×180，detach 可见性 |
| T31/T34 | `contour_loss`、`geometry_guard` | 原类兼容调用；有限梯度/空位移检查/越信赖域拒绝，不迁移优化器 |

视角接口接受显式 FIT/candidateFIT 的唯一 ID。MAX 历史 G01 池有一个完全相同的重复记录；默认拒绝重复，测试中显式调用 `collapse_exact_duplicates`，只有全部元数据和可见性逐元素相同时才折叠，并记录索引。227 条→226 个唯一来源，最终 18 个历史选择与覆盖数值完全复现；不会挑选冲突身份中的“更好”结果。

DXY 测试样本为 Q-conflict 恢复、非 strict_stable；候选可数值输出不代表隐藏轮廓正确。真实 contour/guard 测试也不是科学形状验收。108 个相机输入经过核验，仅一张图实际作渲染一致性测试；T13 实测为一目标与其三个冻结支持的子集。

## 历史源码供应与轻量 main

`src/ring_first_3d/source_lock.json` 固定来源 commit 与完整文件 SHA；优先读 `RING_FIRST_SOURCE_ROOT` 下登记文件，否则 `git show` 读取固定对象。缺对象会失败，错误 SHA 不回退。只编译选定定义/语句，不执行历史星号导入、main 或目录初始化。

main-ready 不复制历史实验目录。可指向现有只读研究 checkout：

```bash
export RING_FIRST_SOURCE_ROOT=/path/to/verified/research-checkout
```

或在新的 main-ready checkout 只取回注册表固定快照的 Git 对象（不合并历史，不检出全实验）：

```bash
git fetch --no-tags --depth=1 origin fa649fa1cf20b111bfdb8489e8af20ba90339bba
```

当 5636 历史父对象未取回时，loader 可从 fa649fa1 快照读取相同路径，但仍逐文件核对同一完整 SHA。该快照包含较大历史对象；优先复用已存在的只读源码目录。数据与环境为 LOCAL_ONLY，不随轻量发布分支携带。

## 证据、存储与提交流程

冻结输入/原始 reference 位于 `tools/research/*fixture.json` 和 `frozen_reference.json`；生成脚本 `freeze_reference.py` 直接调用官方 API 和历史 AST，拒绝覆盖已有 reference。测试不会重写基准；所有容差提前固定。参考渲染和 adapter 渲染有 float32 运算次序差异，比较数值容差，保留各自完整 SHA，不要求位级一致。

`maintenance/storage` 保存独立审计、不可变删除清单、保留资产和逐项删除回执。发现旧缓存与现有源不同，先作 LOCAL_ONLY 完整压缩归档并逐文件读回 SHA 校验，才执行原清单范围内 unlink。维护工具是本任务专用，拒绝已有冻结/删除回执，不是可反复运行的通用清理器。

提交前运行 `check_payload.py` 和 `git diff --cached --check`；显式 add，不上传全量逐帧输出/NPZ/权重/GLB/环境。唯一较大文本例外是用户要求的 1.91 MB 逐 checkpoint 保留资产清单，按 Phase-0 SHA 与 2 MB 上限复核。科研数据继续 LOCAL_ONLY。参见[模块晋升政策](registry/MODULE_PROMOTION_POLICY.md)。
