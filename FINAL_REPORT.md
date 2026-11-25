# M2F7 FINAL REPORT — HIST-V6 G01-005 and CURRENT-M2F6

**Branch:** `exp/TASK-M2F7-HIST-G01-CAUSAL-001`  
**HIST run:** `runs/m2f7_hist_g01/hist_v6/`  
**CURRENT run:** `runs/m2f7_hist_g01/current_m2f6/`

## 1. HIST-V6 是否真正从 RAW 复现？

**部分复现，但不是精确复现。** 22/22 原始 RGB/Mask 从 G01-005 重新解码后与 V6 台账哈希一致；V5 源码从这些 RAW 帧重算 original16 Ring 观测/候选；V6 原生 track005、BA、validate_select、support selection、官方 MVSAnywhere 和 Mesh 均实际执行。

实际 version 0 为 **8/22 VALIDATED**、version 1 为 **0/22**。历史记录为 15/22 与 0/22，因此 **历史 15/22 未被复现**。这不是加载历史相机造成的：Ring candidates、track005 有限值/NaN 模式、version 0/1 initial cameras 均与历史记录一致/在 3e-8 内；差异从 BA/validation center spread 开始，具体是 version 0 BA 的相机中心与 validation 的跨版本中心离散度发生变化。不能用历史 `VALIDATED` 表补结果。

## 2. M2F6 是否独立重跑？

是。使用现有 `--m2f6` 入口在新 run root 从同一 RAW 视频独立执行，未读取 V6 的相机/视角/深度/Mesh。实际得到 **8 个 HERO、21 个 A→B**，coverage median **0.918**，RGB MAE median **5.975**。旧 `formal_002` 为 7 HERO，故本次确为独立新运行。

## 3. V6 与 M2F6 的公制几何差异

- V6：22 相机；version0 held MAE median **1.454 px**，validation center-spread median **1.962 mm**，8/22 VALIDATED；version1 0/22。
- M2F6：16 个当前观测，8 HERO；其当前相机/验证状态与 V6 不共享帧身份，不能把两者的绝对平移直接比较。
- 两路线共同 RAW 分辨率/K/物理 Ring 一致；但 frame selection 不同。V6 target/support 为 459/172/57/745 等，M2F6 为 230/377/188/398 等，**交集为空**。

## 4. 仅更换相机（B）是否导致 HERO 深度变化？

**NOT_COMPARABLE。** V6 Target/Support 与 M2F6 Target/Support 没有共同四帧身份；若强行交换必须插值、邻近帧或改变 M2F6 采样，均被禁止。未运行 B，也未报告其效果。

## 5. 保持相机不变，仅改变 Target/Support（C）是否导致深度变化？

**NOT_COMPARABLE。** 原因同上。无共同 target/support，不能构造合法 C。

## 6. 哪个历史模块值得纳入正式主线？

本轮没有足以晋升为正式主线的模块。可保留为**强候选/诊断证据**的是：

- V5 源码从 RAW 重算 original16 Ring 观测/候选的路径；
- V6 的 `diverse_four`、track005、local Ring BA、validate/support 的原生顺序。

但 **validate_select 从历史 15/22 变为当前 8/22**，且 B/C 无法隔离相机与视角。因此：

- 相机几何是主要原因：`UNRESOLVED`
- HERO 深度优势来源：`UNRESOLVED`
- 历史支持视角筛选：`SUPPORTED_BUT_NOT_ISOLATED`（仅证据，不足以晋升）
- 不得将 V6 结果注册为正式生产路线。

## 4D 结论

A（V6）与 D（M2F6）是两个独立基线，不是同帧配对实验。历史 15/22 未复现，B/C 不可比，故不能证明“相机改善导致 HERO 改善”。当前唯一可确认的是：**V6 源码可在 RAW 上重新执行并产生 4 个官方 HERO，但验证结果与历史不同**。

## 交付

- `ROUTE_COMPOSITION.md`
- `HISTORICAL_REPRODUCTION_MANIFEST.md`
- `IMPLEMENTATION_PLAN.md`
- `REPRODUCTION_COMPARISON.csv`
- `CAMERA_GEOMETRY_COMPARISON.csv`
- `HERO_CONTROLLED_ABLATION.csv`
- `RUN_TRACE/`
- `VISUALIZATION_INDEX.html`
- `FINAL_REPORT.md`
