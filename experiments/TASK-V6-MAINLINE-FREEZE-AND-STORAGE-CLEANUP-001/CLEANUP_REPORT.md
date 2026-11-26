# 受保护的V6方法冻结与清理报告

完成方法身份记录，并按新冻结清单实际删除 **4942个普通叶文件，回收 1.0009 GiB 分配空间**。13条退役运行均已处置；没有运行算法优化或全量clean。独立执行提交 `1d3fe256`，逐文件身份、理由、状态见 [CLEANUP_MANIFEST.csv.gz](CLEANUP_MANIFEST.csv.gz)，本地另有同名未压缩CSV。

## 当前采用的方法

人工认可、当前固定、等待全量确认：V6 HIST `da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`；clean分类执行 `e30ac479e6b555cbe906bd516d09c4849e4b8cbd`、交付 `2d34cc866cd175d4d770a3e09d07b31a5c3662d7`、历史规则 `62c286fcbf39cbba9ec5adb148bd50ba9dc94093`。方法为原V6 Raw及真实映射→017四态→冻结gap→018 `F[state==0]`；原坐标和Face/Vertex ID不变。协议、适配和展示SHA分别见 [METHOD_FREEZE](METHOD_FREEZE.json)。四例名单不是全量入口，四例脚本不是已完成的全量clean运行器。可信孤片残留、开放边界收缩及无GT限制保留。

## 实际清理及保留

| 退役运行 | 删除叶数 | 回收分配MiB | 剩余库存MiB |
|---|---:|---:|---:|
| m2e_historical_method_integration | 1 | 0.33 | 6.79 |
| m2f10_v6_multiview | 2160 | 299.83 | 2048.12 |
| m2f12_historical004 | 96 | 25.33 | 205.00 |
| m2f13_hero_all | 789 | 439.70 | 105.22 |
| m2f1_strict_restoration | 1 | 0.64 | 3.18 |
| m2f1_w0_admission_restoration | 1 | 0.47 | 10.31 |
| m2f2_root_cause_corrective | 25 | 1.02 | 4.11 |
| m2f3_admission_convergence | 19 | 0.40 | 6.44 |
| m2f5_unified | 53 | 0.53 | 7.90 |
| m2f7_hist_g01 | 723 | 70.09 | 21.18 |
| m2f8_v6_general | 348 | 60.18 | 5.96 |
| m2f9_v6_general | 701 | 122.37 | 20.05 |
| m2f_metric_depth_diagnosis | 25 | 3.97 | 5.41 |

库存按各根唯一inode统计，跨根可能共享，不能把库存简单相加当物理总量。删除回收仅以每次unlink前的末链接分配块计算；本轮最终4942个候选均为独立inode，无硬链接重复计量。没有递归删除父目录，空目录可保留。

- M2F10：清理未采用SMOKE、旧FORMAL-01及诊断重复深度／Mesh／抽帧和图集；FORMAL-02约0.915GiB是当前基线协议及正式面源池，完整保护。M2F11的9个部分运行/审计子目录独立保护，没有按M2F10父目录整树清理。
- H004：删除M2F13扩展曲面和旧重复评价转换；M2F12只删明确无消费者的派生项，保留004相机／地标、完整小指标和代表输入闭包。旧H004方法及本轮未采纳结论仍可追溯；不重新推理或重新选相机。
- M2F7/8/9：清理退役参考帧／相机策略专属缓存、重复抽帧、分割、SIFT／BA派生数组和HERO输出；保留真实失败记录、原配置、输入身份和按原路径顺序选定的少量原生深度／同源Mesh代表。
- M2E、M2F1/2/3/5及深度诊断：只处理现存遗漏派生文件。R5/R10共享CAD完整保留；源码、配置、CSV/JSON指标、日志、patch和原先精简归档没有再次清理。

逐子目录字节与消费者见 [CHILD_DISPOSITION.csv](CHILD_DISPOSITION.csv)，逐根见 [ROOT_DISPOSITION.csv](ROOT_DISPOSITION.csv)。逐保留叶原因见 [RETAINED_LEAVES.csv.gz](RETAINED_LEAVES.csv.gz)；`IMAGE_ORIGIN_NOT_CONFIRMED`、`EXTERNAL_OR_PROTECTED_HARDLINK_ALIAS`及非普通文件单项留存，不阻断其他清理。

源码与版本保留在所有原工作树/Git历史、原RUN_STATE/配置/输入身份文件及M2F13现有归档。现有 `RETIRED_FINAL_EVIDENCE.tar.gz` **94,516,429 B**，完整SHA重新核验等于 `97c894d00be9e93ba9cfdc3471c4a90eb4183a47996039a7527aee68b5fa26c0`，位置未变；没有再复制或压缩整套大目录，也未重复计算M2F13历史释放量。

## 后台与保留资产验证

[PROTECTED_PATHS](PROTECTED_PATHS.json)按消费者及真实目标列保护范围；[代表闭包](evidence/REPRESENTATIVE_CLOSURE.json)追踪链接和manifest依赖。复核在删除前发现并保护9个代表依赖，随后568条保护链接、完整代表JSON与候选0冲突。删除器9项边界检查通过，逐路线批前检查全部静态文件，批内每64叶刷新fd/mmap。没有移动、改名、换链接或更改活动权限，没有暂停/重启后台，没有git clean、历史清洗、环境卸载或系统缓存清扫。

**36,430项静态保留文件检查通过，79段原始视频可读。** 原始视频/大模型只核既有身份与stat，没有重新全盘哈希。所有现用科学源码、协议、参数、CAD、clean输入与实际输出内容核验；仅4个全量协议回执允许运行器同内容原子重写，SHA必须相同。旧HIST池完整静态保全，最新四源clean的Raw/分类/排除集/映射/图与完整回执保留。虚拟配准RUN_001的748文件及RETAIN_DEPENDENCIES祖先均保全，g01_multisurface/g01_sim_rev1实体根和全部assets不动。官方HERO权重、分割权重、P共享环境、V3 Open3D、DXY不在删除允许根内。

前后 **V6 PID185164、Ring+SIFT PID212960的启动ticks、命令、cwd、exe一致**。全量面源从 646 增至 750，runner.log继续推进；SIFT保持 `WAITING_FOR_A`，更新时间随原30秒轮询推进，未抢GPU。完整进程/子进程/fd/maps在压缩前后回执；摘要见 [BACKGROUND_HEALTH.json](BACKGROUND_HEALTH.json)。

2026-11-26T16:55:19.864753+08:00（北京时间），固定 **39组79视频**。阶段状态：正常结束且有输出 **39**，正常结束无输出 **22**，失败 **7**，运行 **1**，待运行 **10**。已有 **39/79视频（49.37%）、27/39组（69.23%）、750个非空HERO面源**。这些是输出覆盖，不是几何正确率。

当前阶段见BACKGROUND_HEALTH的active；最近日志 `/home/liu/ring_first_3d_workspace/runs/v6_full_run_001/logs/GP_Is_6.5mm_closed_R10_single_refY_005__camera.log`，mtime_ns `1795683291454498413`。失败仍在79分母。7例失败中6例为Ring pose graph disconnected；Is18/R5/005的两候选BA完成后，旧validate_select因None与整数比较抛TypeError。记录的7例均发生在实际删除前，没有文件缺失报错；本轮没有修改失败状态或旧验证算法，见 [失败回执](evidence/CAMERA_FAILURES_AFTER.json)。

## 同挂载点空间

全部位于 `/dev/nvme0n1p3`、挂载 `/`、st_dev=66307；普通用户可用空间如下。

| 时点/量 | 字节 | GiB |
|---|---:|---:|
| 审计开始可用 | 4892319744 | 4.5563 |
| 实际删除前可用 | 4402159616 | 4.0998 |
| 实际删除后可用 | 5489274880 | 5.1123 |
| 末链接分配空间回收 | 1074655232 | 1.0009 |
| 删除时段df净增加 | 1087115264 | 1.0125 |
| 交付检查时可用 | 5335560192 | 4.9691 |
| 审计开始至交付净变化 | 443240448 | 0.4128 |

删除时段：2026-11-26T16:51:07.158413+08:00 → 2026-11-26T16:51:41.686744+08:00。df净变化比末链接块数多 11.88 MiB，这是同期其他磁盘活动/元数据统计净差，未归因且不计本轮删除收益。审计期间全量持续写入，新清单、日志及工作树也占空间，因此整个审计时段净变化与删除量不同；以字节回执为准。当前任务证据 40.97 MiB，本地审计/删除回执 69.43 MiB；新完整资产归档0字节。工作树初次checkout再稀疏的临时释放、同盘移动均不计收益。

本地审计及删除回执：`/home/liu/ring_first_3d_workspace/runs/v6_freeze_storage_cleanup_001`；原大资产留在原位，Git只交方法、工程守卫、清单和报告。当前图集继续使用 http://127.0.0.1:8957/index.html ，四源clean展示仍为 http://127.0.0.1:8959/index.html 。本轮到此停止，不自动全量clean或改变科学主线。

## 交付前补充快照

2026-11-26T17:03:42.967018+08:00（北京时间）：V6与Ring+SIFT父进程身份继续一致；V6已结束65段（40段有输出、25段无输出），相机失败8段、运行1段、待运行5段。固定79视频/39组分母，已有40/79视频（50.63%）、28/39组（71.79%）、768个HERO面源。Ring+SIFT继续WAITING_FOR_A。此处为阶段快照，队列仍在自行推进。

较16:55检查新增Is7/R5/005相机失败，两初始化候选均报Ring pose graph disconnected，后续validate_select的available断言失败；日志没有缺文件异常。未更改算法或失败记录。79个RAW仍可读，8,163条代表资产引用均存在；两可视化URL均返回HTTP 200。详细证据：[DELIVERY_CHECK.json](evidence/DELIVERY_CHECK.json)、[VIDEOS_DELIVERY.csv](evidence/VIDEOS_DELIVERY.csv)。该时点可用空间5255311360 B（4.8944 GiB）；实际删除回收量保持1.0009 GiB。
