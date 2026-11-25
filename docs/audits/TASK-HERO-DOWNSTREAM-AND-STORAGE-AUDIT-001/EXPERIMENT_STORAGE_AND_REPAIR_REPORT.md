# 实验空间、依赖问题与恢复方案

任务：`TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001`；2026-11-26，Asia/Shanghai。与[模块审计](HERO_DOWNSTREAM_MODULE_AUDIT.md)共用模块/路线ID。本轮没有删除、搬迁、压缩任何实验目录，没有清理环境/权重/Git对象，没有实施修复或运行M2F11/M2F12。只交付本报告、模块报告和两张CSV。

## 1. 决策结论与真实磁盘

**当前无条件可确认释放量为0字节。** 这不是“没有重复文件”：完整哈希已确认大量重复，但其中原始数据/权重默认保护，另外很多路径仍被冻结状态、共享环境或历史证据引用。CSV明确保留了副本、inode、原路径和恢复前提，足以让研究者选择后续哪类去重审议；没有把“可以重算”当作删除许可。

2026-11-26 **01:02:33 +08:00**，本机`liu-INVALID`：

| 项 | 实测值 |
|---|---:|
| 挂载点/设备/文件系统 | `/`，`/dev/nvme0n1p3`，ext4；W、P及/tmp同盘 |
| 总字节 | 211,430,510,592 |
| 已用字节 | 194,081,726,464 |
| 普通用户可用字节 | **6,534,193,152 = 6.0854 GiB = 6.534 GB** |
| inode总数/已用/可用 | 13,180,928 / 1,616,226 / 11,564,702（13%使用） |
| 运行科研任务 | `ps -eo pid,ppid,etime,comm,args`未见M2F、训练、推理进程；仅系统Python/Serena语言服务等 |

因此研究者提到“约6.6G”对应本机根分区十进制空间量级；瓶颈是数据块，不是inode。`df`总量减已用不等于普通用户可用量，ext4保留块等开销不能混算为用户能写的余量。后续可用量会随日志/本任务文本和其他程序变化；不是静态保证。

根目录实际`du -sx -B1`与`du --apparent-size`（不跟随符号链接，每次du内部按inode去重）：

| 根目录 | 分配字节 | 逻辑字节 | 分配GiB |
|---|---:|---:|---:|
| P=`/home/liu/polyp_research` | 37,827,870,720 | 37,489,184,702 | 35.2299 |
| W=`/home/liu/ring_first_3d_workspace` | 25,398,992,896 | 25,061,176,334 | 23.6547 |
| `/home/liu/miniconda3` | 25,281,998,848 | 24,571,959,583 | 23.5457 |
| 三个M2F9/10/11 worktree父目录 | 2,190,012,416 | 2,113,516,003 | 2.0396 |
| `/home/liu/ring-first-hero-core` | 66,207,744 | 68,870,488 | 0.0617 |

上表不是可删除清单，不应跨独立du相加：不同根可能共享硬链接。CSV库存使用逐文件`st_blocks*512`和`st_size`，排除目录元数据、符号链接本身、重复inode，因而与du根合计有小差异。C逻辑量大于分配量可能涉及稀疏/压缩表达等，未逐文件证明成因；不能强行解释为去重收益。普通小文件块取整造成大部分正差。ext4本次未证明存在快照/共享块；净释放值仍需实际操作前后`df`确认。

## 2. 空间主要花在哪里

以下是逐文件块占用汇总，不重复作为候选计入释放量；具体文件/实验/模块/依赖见[EXPERIMENT_STORAGE_MAP.csv](EXPERIMENT_STORAGE_MAP.csv)的`inventory`、`protected_file`行。

| 位置 | 分配GiB | 内容与使用者 | 建议 |
|---|---:|---|---|
| W/runs | 9.5887 | 各M1/M2运行输入、相机、Mesh、日志和未提交部分结果 | 逐run、逐文件审查；不是整体删除项 |
| W/assets/protected_raw_data | 3.4451 | 内容寻址的原始/历史保护资产，包括大gz | 必须保留；不是闲置缓存 |
| W/assets/retained_sources | 1.0344 | 5,759项已重哈希，R-REPLAY/R-BODY/T30/T43真实输入 | 必须保留 |
| W/smart_endoscope_20260805 (1) | 3.7444 | 原始视频、标注、解码/传播材料；N10 RUN_STATE直接引用 | 默认保护；不能整树按副本删除 |
| W/.git | 3.6906 | 共享对象、历史分支 | 不清理；另有旧分支独有源码 |
| W/experiments | 1.4988 | 004库、历史019重放、指标/图/源快照 | 成品库与未提交成果优先保护 |
| P/ring_anchor_3d | 15.5426 | 算法、环境、权重、数据及历史输出 | 混合根，不能整体清理 |
| P/.git | 4.7985 | 原历史Git对象及已提交大资产 | 不清理；远端不是完整数据备份 |
| P/experiments | 4.5905 | DXY旧实验等 | 原只读保护；不是本任务默认清理范围 |
| P/smart_endoscope_20260805.zip | 3.7006 | 永久RAW ZIP，3,973,431,261逻辑字节 | 旧“可审议删除”意见不覆盖当前默认保护 |
| E/ring_first_v9_ring_guided_recovery | 2.7986 | 其中MASt3R权重2.755GB | 必要权重保护 |
| E/ring_first_v13_multisource | 2.5223 | DINOv2完整权重1.218GB、RoMa、CoTracker及结果 | RoMa脚本真实引用DINO；保留 |
| E/surface_fusion_v1 | 2.4544 | HERO checkpoint2.421GB+原adapter | N01/N10当前依赖 |
| E/surface_fusion_v3 | 1.3420 | Open3D/vendor与输出 | vendor由python.sh使用，不能按旧实验清理 |

E=`P/ring_anchor_3d/experiments`。工作区runs前列：

| run族 | 分配GiB | 模块/证据 |
|---|---:|---|
| m2f10_v6_multiview | 2.2929 | **混有M2F11部分运行**；N10/N11，必须下钻 |
| m2f1_w0_admission_restoration | 1.4802 | 历史准入/曲面恢复比较，当前未认证可重生成全部 |
| m2e_historical_method_integration | 1.0277 | 历史方法组合、Raw/Cleaned对照 |
| m2f6_unified | 1.0139 | N03独立路线/基准 |
| m2f9_v6_general | 0.8558 | N09身份修复与中间输出 |
| m2f5_unified | 0.4719 | N03前序组合/负结果 |
| m2f1_strict_restoration | 0.4586 | 历史恢复输入/输出 |
| m2f8_v6_general | 0.4359 | N08早期泛化 |
| m2f3_admission_convergence | 0.4127 | 准入与深度归因证据 |

`m2f10_v6_multiview`内部：正式M2F10-02占980,115,456字节（0.9128GiB）；M2F11-FULL占525,770,752字节（0.4897GiB），PAR-A/B/C分别173,559,808 / 112,189,440 / 332,238,848字节。不能因目录名M2F10把后四项误判为旧smoke。中止的M2F10-FORMAL-01占83,562,496字节，仍需保留身份变化/中止原因与最小证据；不因“中止”就删除。

### 2.1 必须分别管理的资产类别

源码以`src/mainline/{lineage,frozen_registry}`、tools、H旧实验code和分支blob定位；RAW/ZIP以真实视频身份清单定位；权重/环境以EXTERNAL_INPUTS、RUNTIME_FILES和实际PYTHONPATH定位；帧/Mask以PREPARED/INPUT_IDENTITY与raw frame id定位；相机/tracks/reference bank以RUN_STATE与019/021祖先定位；HERO/Raw/Cleaned需保存native_pixel_id/FaceID与坐标单位；主体checkpoint必须保留GRAPH/BODY/初值/split；展示只保存有解释力的原PNG/切面，缓存按真实消费者确认。CSV不会将父目录、图像副本、Git对象混为同一可释放项。

## 3. 重复文件核验与清理选择

方法：先按逻辑大小分桶，筛查**≥1MiB普通文件**，排除`.git`内部对象；相同dev/inode直接视为共享，只有多个不同inode才进行完整SHA-256。共对2,561个独立inode完整哈希，确认892个内容重复组。小于1MiB的重复尚未全查；原始数据集没有据这一步认定整目录相等。

最初按每组“保留最大块占用副本”的粗上限是6,690,127,872字节（约6.23GiB），**不能报成可释放量**。逐候选指定权威保留副本、排除已有硬链接后，CSV的条件性非原始/非权重技术上限是**2,971,889,664字节 = 2.7678GiB**。另有3,325,911,040字节（3.0975GiB）是受保护RAW/权重副本，列清单但释放列为0。

| 候选集合（筛CSV asset_kind） | 叶文件数 | 条件性技术上限 | 当前类别与决策 |
|---|---:|---:|---|
| C01 `WORKTREE_COPIES` | 243 | 709,722,112 B = 0.6610GiB | 字节冗余确认；其中238 tracked、5 untracked/ignored。可先选择核实tracked交付副本；不删除worktree混合根 |
| C02 `EVIDENCE_COPIES` | 235 | 205,918,208 B = 0.1918GiB | 重复图/表/图集，优先冷归档/保持路径引用；nlink>1项计0；关键负结果原内容仍保护 |
| C03 `RUN_COPIES` | 622 | 1,170,903,040 B = 1.0905GiB | Raw/Cleaned相同或跨run相同，但全部未跟踪/ignored。冻结输入、状态与功能不同，**暂不可直接处理** |
| C04 `OPEN3D_RUNTIME` | 23 | 306,798,592 B = 0.2857GiB | 真重复库/样例，两个运行路径都可能使用；环境保护优先，最后审议 |
| C05 `OTHER_UNVERIFIED` | 239 | 578,547,712 B = 0.5388GiB | 归属/依赖未闭合；暂不可处理，不计为可立即清理 |
| P-RAW `PROTECTED_RAW` | 142 | **0**（重复块约2.8505GiB） | 原视频/标注/NPZ/ZIP保护约定优先 |
| P-WEIGHT `WEIGHTS_PROTECTED` | 26 | **0**（重复块约0.2470GiB） | 必要模型/冻结副本保护；不自动处置 |

这里“技术上限”是保持一个既有完整副本、移除额外独立inode且不新建永久副本时的块计数。**还没有执行引用修复、独立归档和恢复测试，所以已满足全部前提的净释放量仍为0。** C01+C02合计915,640,320字节（0.8528GiB）是优先交给研究者选择的审议范围；不是已批准清理量。它们具有完整哈希、保留位置与恢复路径，依赖改写/展示链接还必须先验证。其余1.9150GiB需更深入恢复/环境审计，不承诺最终均能释放。

例如：

- D0431/D0432等M2C证据ZIP副本保留W原路径，SHA相同；原报告/命令与Git版本仍可定位。若后续停用某审计worktree，可按精确副本表收拢，不能以此为由删除其独有源码/未提交修改。
- `E/surface_fusion_v3/vendor/open3d/cpu/pybind.cpython-312-x86_64-linux-gnu.so`与`.venv/lib/python3.12/site-packages/open3d/cpu/...`完整SHA为`e99d5acb1ad93e609e83864ec69553a08b2a486e5d639241cc51e3c795e0f0d7`，各225,559,512逻辑字节、独立inode。但CUDA版802,242,736字节的两路径已经同inode/nlink=2，不能再宣称释放约0.8GB。C04仅建议后续可逆收敛，不能直接删运行库。
- Raw与Conservative_cleaned字节相同证明该次清理未改变序列化结果，不能证明“Raw无价值”；两角色和各自freeze仍须保存。可审议内容寻址+保留别名，不能把Cleaned身份写回Raw记录。

**无“已证实可完全再生成”的无条件删除批次。** Renderer源码存在不足以证明输入/环境/全部身份齐全；当前不把整个visualization/frames/runs按理论重算分类为可删。恢复成本以复制现存字节为最低成本，重新推理/训练时间未测，保留未知。

## 4. 已发现的问题与具体恢复方案

修复执行留给下一PM Task。以下列明权威来源与验证，不用替代算法冒充恢复。

| 故障ID | 当前证据与受影响入口 | 保留位置/需改路径 | 验证与回滚 |
|---|---|---|---|
| R01 旧Git宿主失效 | 多处旧`ring_first_3d_*`的`.git`指向不存在宿主；`git status/rev-parse`失败；/tmp/rf019不存在 | 首先保留现存目录全部源码/未提交文件；W/H现存Git对象仅是候选，须按原HEAD/blob核验。不能直接把旧.git指向W | 逐source SHA与候选commit对照，再用新独立恢复目录读取；原.git不动即可回滚。无法定位原对象时写未恢复 |
| R02 历史019/020重放206断链 | W `experiments/TASK-E4-HISTORICAL-CROSSVIDEO-REPAIR-019/historical/replay_G01/.../TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020/{features,ring,landmarks}`链接旧e4_sdf_localization | PATH_BINDINGS机械替换后206目标仍不存在。70项在同replay_G01的019或H的019找到普通文件候选；其余136无核实候选 | CSV L001–L206逐条列原目标、候选路径及当前SHA；尚未把候选SHA与原freeze闭合，**206项均未修复**。先匹配来源/ID/K/T/shape/hash，再仅改授权的链接；保留旧readlink文本回滚 |
| R03 004构建来源缺口 | 参考库成品在W001；N04 features019核心存在；C样本初相机存在，但全库初始公制相机→构建过程未完整闭合 | 权威是原库+原OBSERVATIONS+初相机/源图/构建源码；不能用005 V6相机或新SIFT阈值替代 | 对153地标G01库先查同源相机/原图/track身份；核对全部输入SHA。只有成品可恢复时明确“冻结启动”，RAW恢复仍未完成 |
| R04 M2F10 HTML相对路径失效 | `runs/m2f10_v6_multiview/M2F10_VISUALIZATION_INDEX.html`72个本地href/src全部不存在；文件被放在图片目录上一层 | 所有72目标加入`M2F10-FINAL-VISUAL-20261125-01/`前缀后均实际存在 | 下一轮仅修72相对URL或把入口放到正确图片目录；保存原HTML SHA/内容。验证72/72存在、图片SHA不变，回滚原HTML即可；不必重新渲染 |
| R05 Map checkpoint缺失 | B10_RESTORE_MANIFEST目标不存在；旧清理已offload约4.914GB | 官方固定revision `00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a`，SHA `fa06c0fdccefc5048e072c85935d5789b1e36b307f3859033c17f9dcb9fd5201` | 旧restore helper存在但本轮未运行；旧目标在失效树，先授权稳定新位置。下载流式到异盘临时文件，完整SHA及张量键核验后配置绑定；未下载，远端当前可达未核实，仍未恢复 |
| R06 状态文档滞后 | M2F10 FINAL_REPORT称15状态，实际16；M2F11 summary称RUNNING_PARTIAL而本机无对应进程 | 原RUN_STATE/RUN_TRACE与日志为优先证据；报告新增解释，不回填/覆盖历史记录 | N10 16状态1720引用本轮全哈希匹配；M2F11需重新读各attempt最后记录，不自动resume；保留原状态 |
| R07 官方版本口径错配 | 旧注册卡把P父仓库`4483e25...`写成HERO官方commit；native loader锁`5bd49bba...` | 以官方文件逐SHA及loader upstream为准；99注册项中T23另有已解释路径适配差异 | 修注册文字时分别列父仓库/官方源/adapter/配置；不能改旧源码使其迎合报告；原注册快照保留 |
| R08 历史路径/同名模块风险 | N10显式加载E/V5/V6，`v6_common→g5_common→v4_common→v3_common`；mainline使用sys.path/AST | `SITE.local.json`、`PATH_BINDINGS.json`、`python.sh`、N10 source_modules共同定义入口；旧002混合链独立归档 | 未来迁移先生成旧path→新path清单，逐SHA核验、静态解析与独立只读import来源审计；不复制出又一份主线。原配置/别名保留回滚 |

全扫描范围有2,977条断链，包含旧树历史遗留；W内206条集中上述历史重放，C无断链。M2F worktree父目录另207条，含历史复制链接。不能把“2,977断链”说成当前HERO全部不可运行，也不能用当前主线哈希匹配否认历史路径损坏。对默认输入闭包本轮5759/5759、外部126/126、runtime1045/1045匹配，主线HTML 15个本地链接全部存在。

R04是当前最明确、可低成本安排的后续修复；R02有部分候选副本但尚不能签发修复完成；R03/R01的原始身份缺口仍需保守处理。M2F11/M2F12均未因本审计被恢复或续跑。

## 5. 未来清理可能引入的问题与实施顺序

| 风险/候选ID | 清理前必须做到 | 权威保留/恢复办法 |
|---|---|---|
| R-DUP / C01 | 确认每个worktree文件Git blob及本地dirty状态，保留独有版本与5个未跟踪项；读取实际引用 | CSV retained_copy是已完整哈希副本；恢复到原路径并同SHA。若使用硬链接/符号链接保持路径，必须显式批准与防止写共享inode，不能偷改冻结身份 |
| R-DUP / C02 | 先归档source/config/input身份/命令/指标/失败图，再修原报告和HTML目标 | 内容寻址保护目录及H原成果；最低须保留解释失败的完整图/表，不因多副本把最后一份删掉 |
| R-DUP / C03 | 将RUN_STATE、FREEZE、pack/mesh/pixel与所有输入消费者闭合；只保留相同字节不能消除角色身份 | 同SHA源文件恢复原路径；若删除整个运行目录，摘要表远不足以恢复。暂不允许目录级处置 |
| R-DUP / C04 | 检查实际import路径/ABI/所有消费者，暂停相关任务后才可操作 | 保留同SHA完整库；最坏需额外306.8MB恢复副本。既有CUDA硬链接收益0；不升级或替换版本 |
| P-RAW/P-WEIGHT | 默认必须保留；若研究者另行改变保护约定，先做全覆盖备份验证和抽样恢复 | 原RAW/ZIP、冻结模型不靠“网上可下载”或Git远程代替备份；本轮不计释放 |
| I/U/A | 混合目录、单副本源码、归档容器 | 精确文件清单与版本映射先完成；禁止按failed/old/mainline命名整树处理 |

优先顺序：**R04链接修复 → C01中已跟踪相同交付副本 → C02重复图表归档 → C03各run身份审计 → C04环境收敛 → C05未知项**。原始输入、权重、Git对象不进入默认清理序列。减少约0.85GiB重复交付的风险一般低于动2.4GB唯一HERO权重；但不足以解决下一轮全量空间需求。

### 可执行的只读校验示例（本轮不执行后续变更）

下面验证脚本只读CSV和原文件，不导入科研模块、不运行算法，可用于未来操作前逐项复验。重复文件同时检查SHA、inode和大小；操作期间若文件发生变化应终止。

```python
import csv, hashlib, os
from pathlib import Path
root = Path('/home/liu/ring_first_3d_workspace/docs/audits/TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001')
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()
for r in csv.DictReader((root / 'EXPERIMENT_STORAGE_MAP.csv').open()):
    if r['row_type'] != 'duplicate_leaf':
        continue
    p, keep = Path(r['path']), Path(r['retained_copy'])
    assert p.is_file() and keep.is_file()
    assert sha(p) == sha(keep) == r['sha256']
    s = p.stat()
    assert s.st_size == int(r['logical_bytes'])
    print(r['candidate_id'], s.st_dev, s.st_ino, s.st_nlink)
```

**未来实施流程（本轮未执行）**：研究者选择候选ID→冻结选定文件的hash/stat及所有consumer配置→将最小证据写入已核实外部目的地→流式传输并在目的地完整SHA检查→抽样恢复到独立目录→检查输入ID/单位/K/T/Mask/FaceID与引用闭包→按精确文件清单去重/修引用→重复同一只读校验→测同挂载点df净差。任一步不匹配就从权威副本恢复原路径和原配置，保留失败回执；不得切换新算法来让旧验证通过。

对于R02：先从CSV L行候选副本与历史freeze核对SHA；匹配才允许在新恢复副本中重建链接。缺原hash时，只能称“候选恢复数据”，不能称精确恢复。对于R05：只能恢复指定revision/完整SHA，不下载相似模型替代。对于R01：先用`git cat-file -e <原commit>^{commit}`确认对象存在，再核验文件blob；不要直接用`git worktree repair`猜测错误宿主。

### 外部归档与峰值临时空间

本机没有在本轮核实可写、容量充分且允许使用的异盘/远端归档目的地；`/tmp`、W/archive及P都在同一根盘。同盘搬迁不释放空间。旧报告“云端可连/某文件已上传”不是2026-11-26完整备份证据。

未来需要外部介质时先`findmnt -T <目的地>`、`df -B1 <目的地>`，确认不是同设备，获得目标容量与访问权限；采用逐文件流式复制（内存缓冲，不在本盘生成大tar）。接收端暂存单文件的额外空间至少为最大文件大小，完成完整SHA后原子归位；若同盘保留旧、新两份再操作，还需完整额外候选大小，当前约6GiB不能默认足够。恢复演练至少覆盖一份RAW及其Mask/相机、一份native/Raw FaceID包、一份主体checkpoint与失败结果、一项最老源码/配置；权重必须完整SHA而非只抽样头部。

## 6. 既有清理建议重新核实

- 2026-10-13/16删除记录是已发生动作，不重复执行其脚本。其旧图集失效说明历史产物可能不全，不能将全部旧实验归为可再生。
- 2026-10-31 `FURTHER_SPACE_REVIEW.md`曾列2.10GiB临时Git pack。本次W `git count-objects -v`：6 packs，`garbage: 0`、`size-garbage: 0`。旧候选不计当前收益；P其他对象不因此推定无问题，仍禁清理Git。
- 旧ZIP/Git相同证明不覆盖本任务“永久原始ZIP保护”；本轮也未重读整个Git大blob证明可恢复，所以计0。
- `TASK-E4-W0-MAINLINE-CONSOLIDATION-015/cleanup/CLEANUP_DECISION.csv`明确RAW/retained_sources保留，experiments/*/runs为PENDING_REVIEW；此次仍不能自动改成可删。
- Map权重offload恢复清单存在，目标权重现在缺失；本轮保留“未恢复”。MASt3R/HERO/DINO权重不能当通用下载缓存。
- 旧cleanup003报告“工作区无.git、对象宿主原位”已不适用：W现在有真实Git仓库，旧树部分Git指针失效；本轮以实际文件为准。

## 7. M2F11下一轮磁盘峰值估算

不为估算启动实验。使用已存在M2F10正式10视频运行作为量尺：0.9128GiB，含16个attempt（10初始+6恢复），其中RAW准备/当前输入537,415,680 B，Mesh179,171,328 B，predictions70,103,040 B，其余诊断/跟踪约其余部分。按视频聚合，均值93.44MiB、最大144.78MiB；包含其已有恢复尝试。另有最终图18,427,904 B（约17.57MiB）。这是文件块量尺，不是GPU显存或只统计末端Mesh。

现存M2F11汇总目标为**39组102视频**，不能沿用M1旧79视频分母：

- 按正式10视频平均线性外推，102视频累计新增约**9.31GiB**；若保留同等强度图/表约再0.18GiB。
- 按已观测单视频最大值外推为**14.42GiB**；只能作为压力情景，不是严格上界。102视频的长度、支持数、恢复/重试和多worker并发可能不同。
- 给重试失败保留、每worker临时文件、Python/渲染缓存和不覆盖旧结果留30%余量，建议在启动前提供**至少20GiB净可用空间，25GiB较稳妥**。这包括新run保留所有证据的空间，不靠删除NaN/失败项省容量；增加完整外部权重恢复另加预算（Map约4.58GiB且不是V6必需）。
- 已存在M2F11-FULL/PAR约1.07GiB是受保护部分运行，不能先减掉作为“必可复用”。续跑只有RUN_STATE/输入/上游源码/命令/阶段身份全部匹配才可扣除已完成量；重新建run时应按上述全量追加计算。

当前约6.09GiB明显不足建议预留，即使条件性去重技术上限2.77GiB全部实现，也只有约8.85GiB且尚未计系统写入；不足以稳妥启动。优先核实外部存储或进一步受控归档，继续暂缓M2F11/M2F12。

## 8. 核查进度、未知范围与交付回执

已完成：本机df/inode/process与仓库状态；373,305条元数据、主要目录分配/逻辑大小；99注册源码和新V6/Hull/恢复版本；73本地分支树/64独有版本；32归档目录；2,561独立inode完整哈希；5,759历史输入+126外部+1,045runtime逐SHA；16份M2F10状态1,720引用；主线及M2F10展示入口检查。两张表含178模块/版本行与2,947空间/修复/保护行。

未核实：≥1MiB筛选之外全部小文件重复；未知消费者/硬编码字符串的完整动态闭包；全磁盘其他项目；旧树对象宿主恢复；所有历史日志/图链接；云端/异盘备份/恢复演练；M2F11当前全部attempt语义状态；科研质量新复验。CSV中空SHA/未知不是0风险。文件扫描无访问错误，但报告不声称每个历史算法均完成逐行审计。

本轮保留原工作树、现有进程和未提交修改。提交只包含本目录四个文本文件；指定分支为 `audit/TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001`，从审计起始W HEAD建立，不修改W当前分支与索引。本报告不内嵌自身提交SHA；最终聊天提供提交号与实测远端回执，只有远端SHA一致才标上传完成。

## 附录A：逐根Git核查快照

开始审计时采集；Git失败保持原错误身份，不伪造HEAD。untracked计数使用`git status --porcelain=v1 -uall`，包含未被Git忽略的每个文件；ignored另由元数据扫描覆盖。

| 路径 | HEAD | 分支 | tracked修改 / untracked |
|---|---|---|---|
| `/home/liu/ring_first_3d_scene_vis` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_policy_bootstrap` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_e4_e1e2` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_multivideo_init_a` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_e4_sdf_localization` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_g01_dualvideo` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_pose_depth` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_panel2_depth` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_workspace` | 8e59081600db2739ab183325bbe5354c4d1d2b4c | exp/TASK-M2F8-V6-GENERALIZATION-001 | 18 / 28075 |
| `/home/liu/ring_first_3d_abs_density` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_grazing` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_g01_sim_rev1` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_synthetic_correspondence` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_camera_gate` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_harness_main_ready` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_neural_e0` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_ab_scene` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_phase_d` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_growth_recovery` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_e4_pmgr` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_view_eval` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_view_partition` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/ring_first_3d_e4_a1` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |
| `/home/liu/polyp_research` | 4483e25ede3eee1b6eaf96254d2544152f935c0d | main | 14 / 2602 |
| `/home/liu/polyp_research/ring-first-3d` | fa649fa1cf20b111bfdb8489e8af20ba90339bba | exp/TASK-PROJECT-TECHNOLOGY-REGISTRY-001 | 0 / 0 |
| `/home/liu/ring-first-hero-core` | 72f30e7f1a2edfc4b0dcd270da217ae65c07f516 | main | 0 / 0 |
| `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F11` | 2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c | exp/TASK-M2F11-V6-FULL-DATASET-VALIDATION-001 | 0 / 0 |
| `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F10` | 2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c | exp/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001 | 0 / 3 |
| `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F9` | b791c9affa74e848f04792cb600f8b95040bba3a | exp/TASK-M2F9-V6-GENERALIZED-PIPELINE-CORRECTION-001 | 1 / 2 |
| `/tmp/rf019` | 未核实：Git宿主/目录不可达 | 未核实 | 未核实；保留实际文件 |

## 附录C：归档目录盘点

先读容器目录，再仅在内存读取ZIP源码成员计算SHA；未解包到科研目录。恢复时仍须验证具体member和来源。完整容器SHA见CSV A行。

| 归档 | 成员数 | Python成员数 |
|---|---:|---:|
| `/home/liu/ring_first_3d_workspace/assets/protected_raw_data/sha256/b4/b481685cf943e871128813f9addbbe0363e8e6b56c828dfe75f96bddc71d2b0b.zip` | 94 | 0 |
| `/home/liu/ring_first_3d_workspace/assets/protected_raw_data/sha256/5c/5c471e8fa9f01a1fc65507499622da66dff2be96f1bf8d00947f14332270a4bb.zip` | 1 | 0 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED/artifacts/TASK_E4_W0_CROSSVIDEO_028_REAL_UNIFIED_RESULT.zip` | 31 | 2 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_R2_RESULT.zip` | 44 | 11 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-UNIFIED-020/artifacts/RESULTS_AUDIT.zip` | 26 | 0 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-UNIFIED-020/artifacts/INPUT_FIXTURES.zip` | 6 | 1 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-UNIFIED-020/artifacts/SOURCE_AUDIT.zip` | 15 | 10 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/artifacts/RESULTS_AUDIT.zip` | 31 | 5 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/artifacts/INPUT_FIXTURES.zip` | 5 | 0 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/artifacts/SOURCE_AUDIT.zip` | 43 | 16 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_R3_RESULT.zip` | 87 | 12 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_R6_RESULT.zip` | 47 | 11 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_R5_RESULT.zip` | 40 | 10 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT/artifacts/TASK_E4_W0_CROSSVIDEO_027_BA_PILOT_RESULT.zip` | 49 | 8 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_R4_RESULT.zip` | 134 | 12 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE/artifacts/TASK_E4_W0_CROSSVIDEO_023_RESULT.zip` | 76 | 10 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY/artifacts/TASK_E4_W0_CROSSVIDEO_025_RESULT.zip` | 97 | 14 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-CROSS-VIDEO-018/artifacts/TASK-E4-RING-CROSS-VIDEO-018_CODE_AUDIT.zip` | 16 | 3 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE/artifacts/TASK_E4_W0_CROSSVIDEO_027_CORRECTIVE_RESULT.zip` | 45 | 10 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL/artifacts/TASK_E4_W0_CROSSVIDEO_028_CORRECTIVE_FINAL_RESULT.zip` | 28 | 7 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-RING-CROSS-VIDEO-018-REPAIR/artifacts/TASK-E4-RING-CROSS-VIDEO-018-REPAIR_CODE_AUDIT.zip` | 35 | 6 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY/artifacts/TASK_E4_W0_CROSSVIDEO_026_RESULT.zip` | 95 | 10 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019/artifacts/TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019_CODE_AUDIT.zip` | 46 | 12 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT/artifacts/TASK_E4_W0_CROSSVIDEO_022_INDEPENDENT_AUDIT_RESULT.zip` | 83 | 31 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE/artifacts/TASK_E4_W0_CROSSVIDEO_028_CORRECTIVE_RESULT.zip` | 13 | 5 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS/artifacts/TASK_022R_G03_RESIDUAL_FORENSICS_RESULT.zip` | 27 | 2 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE/artifacts/TASK_E4_W0_CROSSVIDEO_026_CORRECTIVE_RESULT.zip` | 97 | 8 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-REGISTRATION-STAGE-020/artifacts/W0_REGISTRATION_STAGE_020_AUDIT.zip` | 17 | 5 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR/artifacts/TASK_E4_W0_CROSSVIDEO_024_RESULT.zip` | 47 | 9 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-HISTORICAL-CROSSVIDEO-REPAIR-019/artifacts/HISTORICAL_019_020_REPAIR_CODE_AUDIT.zip` | 44 | 10 |
| `/home/liu/ring-first-hero-core/.local_data/G01_004_ring_first_hero_demo_v1.tar.gz` | 26 | 0 |
| `/home/liu/research_storage_cleanup/REVIEW_20261030_185843/REVIEW_BUNDLES_METADATA_ONLY.tar.gz` | 541 | 1 |

## 本轮收尾核验

2026-11-26T01:22:04+08:00：两份报告与两张CSV已交付准备；178个版本源码/可用证据SHA复核、2947条唯一资产ID、跨表模块关联、净释放求和、保留副本不与候选重叠、报告相对链接均通过。四文件合计约3.7MiB。全部原有效Git工作树的tracked/untracked状态与起始快照一致；本轮未运行科研测试或算法。仅本任务四文件将以临时Git索引提交到指定新分支，原分支和索引保留。上传是否完成以最终远端SHA实测回执为准。
