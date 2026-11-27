# 待研究者审阅后统一重跑全量

本轮仅执行固定6组12视频18照片小试。`FULL_PENDING_APPROVAL.json` 的 `approval_required=true` 会由唯一入口显式拒绝启动。小试已完成：R1保留原105/105目标并扩至205，R2丢失原21个目标，当前不能推广。不能用旧成功曲面复用或仅补失败组充作新全量。

科学执行快照：`dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e`。唯一入口仍是 `python -m ring_first_3d.v6_raw.full_run run --config ...`，内部仍调用 `route.py` → 冻结M2F10 → 原V5/V6/HERO。小试 R1/R2 只通过 `include_photos` 控制输入池。无物理组条件分支；R5/R10只使用真实几何参数。

## 全量输入与规则

- `evidence/ALL79_120_MANIFEST.json` 保留冻结39组、79视频、120张照片，附RAW SHA；`PHOTO_INVENTORY.csv` 保留原图尺寸、EXIF/方向及物理组。清单来自原注册表，未硬编码“每组两个视频／三张照片”。
- 照片内参依据研究者确认：与视频使用相同镜头、变焦、裁剪和畸变校正；没有独立标定。按同一成像假设将1920×1080缩至640×360，用视频工作K，原图→工作图使用像素中心变换。该假设不是标定精度证据。HERO仍按原接口到352×640，clean沿用显式原生像素映射。
- 每视频从完整原16+最多6帧池开始，再加入同组照片；先冻结原锚/B身份，再取有效原锚分量。原训练轨迹及train/held划分严格保留；照片仅通过真实匹配扩展，坐标重复导致身份不明确的连接拒绝并计数。
- 原初始化已有合法计划即保留，零计划才检查第二原初始化。最多2候选；相机/验证/中心/排序/元组整套绑定。没有HERO后验选版、深度门槛或新增BA收敛门槛。
- B不在分量时为NOT_EVALUABLE，不换帧；无跨删帧缺口或照片时间边。相机与曲面不跨视频合并。
- 所有成功视频重新解相机与运行新元组；只复用身份及算法未变的RAW选择、INIT及原SIFT输入证据。旧全量和现用clean保留只读。

## 磁盘与启动条件

预估上限1897个Target注册（原视频非诊断Target 1653，照片分视频注册 244；独立物理照片仍为120张），按每源Raw保留3.6 MB、clean证据2.5 MB估计，加1 GiB余量，小试前估算需约12.64 GB可用空间，另留约170 MB单视频瞬时导出。该估计采用小试前既有文件统计，不是保证。

小试实测正式运行树均摊每源约6.58 MB，1897个Target上限加1 GiB和170 MB瞬时余量后，修订为约13.72 GB可用空间。此均摊包括小试固定开销，属于保守外推，不能保证所有全量来源尺寸相同。

本机小试前仅约4.96 GB可用，不能把同盘移动当作释放。全量启动前必须落实足够存储（扩容／用户明确授权的其他清理或新的输出盘）；不得为腾空间删除本任务保护的原全量、配准输入或工作资产。全量目录预设为 `/home/liu/ring_first_3d_workspace/runs/v6_frontend_full_PENDING_APPROVAL`，当前未创建或启动实验。小试结束可用约2.15 GB。实测预算更新见 evidence/STORAGE_FINAL.json；按照正式R1/R2运行树每源均摊成本外推，并同时保留原保守估计，取两者较大值加余量。

**当前发布判定：R2不通过。** 若研究者选择R1视频侧修复作为下一轮统一候选，全量配置须统一设置include_photos=false，照片仍保留在120张清单中并明确本轮不处理；不得按组混用R1/R2。若要推广照片路线，先完成新的固定小试、验证原视频目标不再丢失，重新冻结版本。当前R2不能仅解除审批标记就启动。

研究者确认可推广的版本及回归结论后：固定同一源快照，复制小JSON配置到新运行根，设置真实manifest快照路径及新run_root，明确解除approval_required；不修改科学参数。以新根建立逐源计划，不复制RAW、模型或旧大Mesh。保持最少1 GiB阶段停机阈值，GPU使用既有 `/home/liu/ring_first_3d_workspace/runs/shared_gpu.lock`。

## 启动与恢复命令模板（本轮不执行）

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
SNAP=/home/liu/ring_first_3d_workspace/runs/v6_frontend_photo_pilot_001/snapshots/dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e
CONFIG=/批准后的新运行根/config/FULL.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SNAP/src" \
V6_EXECUTION_COMMIT=dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e \
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
"$PY" -m ring_first_3d.v6_raw.full_run run --config "$CONFIG"
```

后台执行可用 `nohup`/独立session并保存PID、环境、配置SHA和stdout。`logs/<case>__<stage>.log`、`states/`、`PROGRESS.json` 和每视频 `RUN_STATE.json` 为持续记录。恢复用同一命令：已DONE跳过，已冻结成功native按SHA复用；相机中断保留原attempt再重算同输入；所有资源性重试必须记录原因、次数和相同元组身份。不得对失败元组暗换Support。`full_run retry --config ... --case ...` 只在明确记录工程/资源问题后使用，科学零计划不是重试理由。

## 全量验收分母

1. 视频帧Target有非空Raw的视频/79；视频目标有输出的物理组/39；原选帧非诊断Target固定分母（含排除分量和失败）。
2. 任意视频或照片Target有非空Raw的组/39，另列，不冒充视频恢复。
3. 独立物理照片Target/120，Raw与Trusted分别按物理ID去重；同一照片分别注册到两个视频只算一张照片，关联全部保留。仅Support不算照片Target重建。
4. 非空Trusted及Raw非空、Trusted为空分别计数；仍为017四态+冻结gap+`F[state==0]`，不以clean外观代替Raw质量。
5. 对原42视频795个Target逐一对照共同身份、Support变化与几何变化；不以照片数量掩盖视频回归。不宣称GT正确率。
