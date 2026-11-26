# TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001

本轮已达到附件交接条件：全量HIST后台真实健康运行，三源clean小试完成；**全量尚未结束**，当前是RUNNING。交接记录时间：2026-11-26 14:48:22 CST。不等待全量结束，不把当前覆盖称为最终覆盖。

## 执行范围与固定策略

[DATASET_MANIFEST](evidence/DATASET_MANIFEST.json)按真实RAW逐文件SHA/ffprobe并与`/home/liu/new-polyp-dxy/validation/frozen39/inputs.csv`交叉核对。注册表与RAW一致为39组79视频（38组×2，Ip4.0/R5组×3），包含001/006/007等真实视频编号。R10为22组、R5为17组。109个MP4中另30个为未注册的分割增强池，保留路径/SHA/原因，不发明物理组映射；120张照片单列。当前没有注册视频缺失，没有按哈希发现重复注册视频。历史102视频与这两份证据不符，差额23没有可识别的注册条目，明确列作历史范围声明差异，未凑数为78或102，也未把静态照片冒充视频。

唯一科学流程仍为115e41fe所恢复的V6 HIST：全时序16+最多6历史补帧、INIT原Mask、锁定M10适配器6ad695b0…与原V5/V6 Ring+SIFT/BA、基础帧索引8锚帧/9诊断B、Q0优先三Support，Q1仅中心分散>2mm硬门槛改警告，共同FIT轨迹≥15、原排序、全部非诊断Target、每Target一个冻结三元组、官方HERO及原Mesh。Target自身资格不新增硬门控。没有H004/GRAPH/其他相机结果混入，没有GT/深度MAE门控，没有训练或跨视频融合。

[组合与执行清单](IMPLEMENTATION_PLAN.md)及注册表新增`rf-v6-hist-full@1`记录授权来源；旧5组/273协议保留为旧默认入口，新配置按清单和逐视频冻结合法组合预算运行。实际非诊断Target分母来自选中帧数及完整计划，不固定21；不足16帧维持原策略的VIDEO_TOO_SHORT失败，禁止伪造16帧。

## 已观察的实际运行

当前持久执行代码快照：`da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`，父PID `185164`。首视频相机由前一11e62596快照生成；工程暂停后切换da92d8dd，科学函数协议相同，准备/相机阶段原哈希校验复用，原执行身份仍保留。运行目录每个阶段及推理起始账本记录实际身份；退出前报告提交不修改后台快照。

[健康回执](evidence/HEALTH_RECEIPT.json)包含首个新增IIa14/R5/004的真实相机、冻结14组合、实际推理起始、14原生结果、原Mesh及[六视图](figures/first_new_video_near_sources.png)。它不属于旧10 HIST；随后队列已处理更多新增视频，日志持续推进。当前固定快照的完成视频 14/79，有输出视频 12/79，可渲染来源 225；复用/新增分项及已知Target分母见[进度快照](evidence/HANDOFF_PROGRESS.json)。这些仅为截至记录时间的输出覆盖，不能说明表面积覆盖或正确率。

[旧10视频复用核验](evidence/REUSE_VERIFICATION.json)全部通过：完整准备/相机/计划/HERO标记先检查，baseline缓存路径只读核对RAW、RGB/Mask、函数/配置/内核/模型、相机、计划、原生及Mesh输出哈希。两个合法零输出也复用。没有复制整套旧资产；仅生成新规范的近景逐源图和当前索引。

## 后台行为、恢复与资源

有界队列宽度1，每视频阶段独立进程，CPU线程4；HERO在同视频内复用一次官方模型加载。GPU为6GB RTX3060 Laptop；INIT和HERO均使用共享`runs/shared_gpu.lock`，A申请前记录优先标志，避免与任务B争显存。当前没有另开并发模型。相机/SIFT/BA是主要耗时，简单串行队列避免CPU和磁盘峰值叠加；不执行全体两两深度评价。

每个Target由PLAN_FROZEN预算授权；原生npz与推理账本原子落盘；成功tag按哈希复用，不重复推理。进程中断时保留相机旧尝试或恢复同计划；没有原生输出的中断元组最多1次有原因记录的资源性重试。科学性失败/零组合保存并推进下一个视频。显式retry入口不换Support；最终失败、待运行、原生成功和可渲染分开统计。PNG失败不抹去原生或已验证Mesh数量。外部异常有RUNNER_EXCEPTION和PARTIAL状态。

初始同盘可用8,725,172,224字节；历史样本估计69新增的平均保留产物4,267,662,413字节，历史最大单视频估计6,605,840,856字节，另单视频临时峰值见[空间预估](evidence/DISK_ESTIMATE.json)。余量低于1.5GiB在阶段边界写LOW_DISK_PAUSED，不冒充完成。此时保留所有原生深度、相机、全部原Mesh及身份。

当前可用 **7,492,685,824 字节（6.98 GiB）**；已回收本任务可再生重复点云导出/360插值surface缓存 126,515,797 字节，逐路径/字节/SHA/重建入口见[空间回执](evidence/SPACE_HANDOFF.json)。不删除历史资产；同盘快照/图表不算释放。未复制RAW/模型或全量大Mesh入Git。

## 可视化、clean与核验

本地实时页：[http://127.0.0.1:8957/index.html](http://127.0.0.1:8957/index.html)。每物理组一个索引，每视频独立；后台仅生成“近景逐源”，真实Target帧色、黑CAD、六视角、毫米尺、源数、投影出画数量。没有RGB/规则/逐Target九宫格批量附件。图只裁观察窗口，原Mesh/数量完整保留。

clean：[简报](CLEAN_REPORT.md)、[图1](figures/clean_1.png)、[图2](figures/clean_2.png)、[图3](figures/clean_3.png)，本地[三源入口](http://127.0.0.1:8957/clean/index.html)。历史基线均0删除；C1删73面/1.041mm²，其余两源0。73面中8面为历史UNKNOWN，第一源连通分量增加、长附片仍残留；不采用为自动主线。

17项策略/预算/队列/映射检查通过；另36项独立文件/索引检查通过，含原文件哈希不变、原V/F、保留/删除完整分区、派生PLY完全相同原坐标及恰好3图。独立[只读代码复核](evidence/INDEPENDENT_REVIEW.md)核对映射误差<5e-7mm并确认已记录结构风险。它们是工程验证，不是科研精度通过。

交接操作与最终报告预定路径见[RUN_HANDOFF](RUN_HANDOFF.md)。全量结束后后台自行写FINAL_COVERAGE_REPORT及最终索引；本轮聊天到交接停止，不守候全量。

## 已核实远端交付

独立分支 `exp/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001` 已逐提交上传；交付数据提交 [`865a6990b45d882700b7b7732834a894626c7ee3`](https://github.com/zheng1524/ring-first-3d/commit/865a6990b45d882700b7b7732834a894626c7ee3) 经GitHub API读回与本地SHA一致。clean提交 `8016ed9b6a8a124ff5570f50b6e498fe6dfa4699`，后台执行提交 `da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a`。本段与上传回执是后续元数据提交，不改变运行快照。GitHub插件写权限403，沿用本机已授权Git-data API正常上传，未force更新。
