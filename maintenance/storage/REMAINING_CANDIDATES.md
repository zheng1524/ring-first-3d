# 保留项目与后续候选

Phase 0 审计 40 个 Git 目录：ACTIVE 2、UNIQUE_RESEARCH_ASSET 38。没有任何整个 checkout 被证明 VERIFIED_REDUNDANT。逐项目 HEAD、remote、stash、未推送提交、未跟踪/ignored 数、进程、共享 Git、容量与恢复约束见 [PROJECT_WORKTREE_AUDIT.csv](PROJECT_WORKTREE_AUDIT.csv)。逐资产保留清单为 [PRESERVED_ASSETS.csv](PRESERVED_ASSETS.csv)，本轮完整复算 SHA。

| 对象 | 状态与保留理由 |
| --- | --- |
| `/home/liu/ring_first_3d_harness` | ACTIVE，新工程任务；其 Git alternates 只读依赖既有受保护对象库，不是独立历史备份 |
| `/home/liu/ring_first_3d_e4_sdf_localization` | ACTIVE，共享 P3D runtime 和真实测试输入；旧 MAX 浏览器 profile 已独立核验无任务依赖，仅清理被冻结缓存文件 |
| 其余 38 个项目目录 | UNIQUE_RESEARCH_ASSET；存在 ignored/未跟踪数据、独有结果或无可靠完整备份；远程 HEAD 相同不能证明数据可删 |
| `e3_sdf_full`、`e3_sdf_multi`、`e3n0_a3` | 有未提交修改/未跟踪失败或训练成果，完整保留 |
| 39 个历史目录共享 `/home/liu/ring_first_3d/.git` | 分支多不代表每分支独占全部对象；不删除分支、不 GC，悬空提交尚无异地可靠备份 |
| 3,169 个 checkpoint/weight，约 0.802 GB 保留资产总表的一部分 | 已逐文件哈希；身份完整，但未证明全部存在外部备份；不删唯一训练状态和失败证据 |
| 6 个 task-local packages 路径与 P3D source/build | 与现有工程/历史实验共用；没有找到可判为废弃的独立 venv（未发现 pyvenv.cfg） |
| MAX 两份大型归档、rawNPZ、深度/PNG/大型 Mesh | 可能与目录重叠，但没有逐成员/完整引用恢复证明，本轮保留 |
| 新建历史 HTTP cache 归档 102,648,027 B | ARCHIVE_REQUIRED 已完成单机精确归档；包含旧版本响应，禁止删除，尚非异地备份 |
| main-ready 发布 checkout | 本任务后续新增 ACTIVE 工程工作树；只含文档及必要入口，不纳入“旧副本已清理”统计 |

继承旧审计：15 组 SHA 精确重复的最大逻辑冗余 3,938,825 B，本轮没有删这些文件；TSDF、NeuralFusion、MonoSDF 失败/训练不足证据与被引用的旧 visualizations 全保留。未进行跨磁盘普查，也不承诺所有唯一科研资产已备份。

后续若清理整个目录，必须先建立独立可靠备份并验证代码/所有 ignored 文件/提交/失败证据/引用/活动进程，必要时迁移依赖路径后再按新的不可变清单执行。不得沿用本次 70 文件清单扩大删除范围。
