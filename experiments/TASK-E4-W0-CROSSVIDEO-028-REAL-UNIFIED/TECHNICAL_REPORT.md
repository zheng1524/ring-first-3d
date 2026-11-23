# TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED — TECHNICAL_REPORT

```
UNIFIED_PIPELINE:            PARTIAL（三组走同一入口与同一代码路径到 identities 阶段；H 初始化/BA 未执行）
NEW_METHOD_VALIDATION:       INSUFFICIENT_EVIDENCE（真实数据上未运行 H 对照）
G01:  W0 = camera_mainline（全 QUARANTINE）；identities = 0
G03:  W0 = camera_mainline（6+16 ACCEPT）；identities = 26（fit 18 / holdout 8）；Ring MIO 0.162
G06:  W0 = 本轮按其正式入口重算（004：8 ACCEPT；005：16 INSUFFICIENT_EVIDENCE）；identities = 8
```

## 1. 做了什么（全部同一程序 `core/u028.py --group <G>`）

| 阶段 | 实现 | G01 | G03 | G06 |
|---|---|---|---|---|
| 数据发现 | 扫描 `prepared/{G}_{video}`，视频编号无算法含义 | OK（004/005） | OK（004/005） | OK（004/005） |
| W0 | `camera_mainline` 优先；缺失则调用正式 `tools/run_w0_camera.py`（**未改 W0 主线**） | 已有（0 ACCEPT） | 已有（22 ACCEPT） | **重算**：004 8 ACCEPT / 005 0 |
| Ring 证据 | 历史 DXY `recover()` → `ring/<view>.npz|json`（019/020 同例程） | OK | OK | OK |
| Ring 渲染 | 历史 `ring020_026.RingRenderer`（只把 `R` 指向本组 replay） | OK | OK | OK |
| Ring MIO（中位） | 同一定义 | **1.014** | **0.162** | **0.117** |
| 特征/轨迹 | 历史 `features019.landmarks`（同一规则） | 38 / 154 | 476 / 469 | 99 / 69 |
| 跨视频身份 | 历史 `match_desc`（ratio .72 + mutual） | **0** | **26** | **8** |
| FIT/HOLDOUT | 统一 `rng(2028)` 70/30 身份划分 | 0/0 | 18/8 | 6/2 |
| H 初始化（旧/新） | 未执行 | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |
| 共同三角化 / BA | 未执行 | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED |

**组别唯一影响输入**（视频编号、K、Ring CAD、可用视角、W0 来源），代码路径完全相同；无 `if group==...` 分支。

## 2. 关键真实发现

1. **G06 必须重算 W0**：`camera_mainline/G06` 不存在。本轮用正式入口 `tools/run_w0_camera.py --group G06 --video 004/005 --output experiments/.../runs/G06/video*` 重算，
   结果写入本实验目录（未覆盖主线）。004 得到 8 ACCEPT，005 全部 `INSUFFICIENT_EVIDENCE`。
2. **G01 全部 QUARANTINE**（16+16）：本轮不修改准入，按同一流程运行并标记 `NOT_ADMITTED_DIAGNOSTIC`。
3. **G01 自动身份为 0**：38/154 个地标下 `match_desc` 无 mutual 匹配 → 该组在当前视角选择下无法建立跨视频身份（真实几何限制，不是跳过）。
4. **G03 Ring MIO 0.162**、G06 0.117、G01 1.014（G01 明显更差，与其 QUARANTINE 一致）。
5. 参考视频由统一规则选出：**G03→005，G01→004，G06→004**（并非固定 005）。

## 3. 未完成（阻断真实方法验证）

- **H 初始化（旧 005-only / 新 Ring+RGB）与共同三角化、BA 全部 NOT_EXECUTED**：时间预算耗尽；
  已产出可直接输入的 `IDENTITIES.csv`、`SPLIT.json`、`RING_SCORES.csv`，下一轮可从此处继续。
- 因此 `NEW_METHOD_VALIDATION = INSUFFICIENT_EVIDENCE`，**不声称新方法更优**。
- 8 类真实图仅完成数据/资产层（详见 `FIGURE_STATUS.md`）。

## 4. 十二个问题（当前证据能回答的部分）

1. **三组是否同一入口/算法？** 到 identities 阶段**是**（同一 `u028.py`，无组分支）。
2. **是否有组因冻结表被阻断？** **无**；G06 缺 W0 时按其正式入口重算。
3. **W0 定义是否统一？** 是（均为 camera_mainline 格式 c2w+K），G06 由同一 W0 入口生成。
4. **能否建立跨视频对应？** G03=26、G06=8、**G01=0**（真实限制）。
5. **各组真实困难？** G01：全 QUARANTINE + 无跨视频身份；G03：Ring 好、身份充足；G06：005 全部证据不足。
6. **新方法是否更可靠？** **NOT_EXECUTED** → 无法回答。
7. **共同三角化是否更稳？** **NOT_EXECUTED**。
8. **BA 后 FIT/HOLDOUT 谁更好？** **NOT_EXECUTED**。
9. **是否有跨组一致优势？** **无法判断**。
10. **哪些问题来自 W0/三角化/H？** G01 的 0 身份与 QUARANTINE 指向 W0/视角质量；G06 的 005 INSUFFICIENT_EVIDENCE 指向证据不足。
11. **是否有组专用修改？** **没有**（无组名分支、无组专用阈值）。
12. **是否具备推广条件？** 数据适配层已可复用；但真实 H/BA 尚未跑通，**尚不具备**。

## 5. 复现

```bash
U=experiments/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
# G06 W0（仅当 camera_mainline 缺失时）
$PY tools/run_w0_camera.py --group G06 --video 004 --stage all --output $U/runs/G06/video004
$PY tools/run_w0_camera.py --group G06 --video 005 --stage all --output $U/runs/G06/video005
for g in G01 G03 G06; do
  PYTHONPATH=$U/core:$PWD/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/core:runtime/p3d:src \
  $PY $U/core/u028.py --group $g --max-views 4
done
```
