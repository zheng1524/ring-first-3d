# 本地存储清理回执

任务 TASK-RESEARCH-HARNESS-STORAGE-001，2026-11-16；所有字节按十进制 GB 解释，GiB 另注明。只清理本地 HTTP 缓存，没有清理 GitHub 历史。

| 时间/口径 | 可用空间 bytes | 可用 GB |
| --- | ---: | ---: |
| Phase 0 冻结 | 7,201,165,312 | 7.201165312 |
| 完成备份、紧邻 unlink 前 | 6,844,403,712 | 6.844403712 |
| unlink 后同步文件系统 | 7,069,904,896 | 7.069904896 |
| unlink 窗口实测 df 增量 | 225,501,184 | 0.225501184 |

df 受到其他进程和本任务检出/代码/归档/报告写入影响，不能把整个任务前后 df 差值当作本次清理收益。

| 可归因文件账目 | bytes | GB |
| --- | ---: | ---: |
| 删除 70 个缓存文件，逻辑大小 | 225,352,767 | 0.225352767 |
| 删除文件已分配块（stat） | 225,529,856 | 0.225529856 |
| 新增精确归档，逻辑大小 | 102,648,027 | 0.102648027 |
| 新归档已分配块 | 102,649,856 | 0.102649856 |
| 净逻辑减少 | 122,704,740 | 0.122704740 |
| **扣除归档后净分配块减少** | **122,880,000** | **0.122880000** |

净分配块减少约 0.11444 GiB；该净额未扣代码/文档与新 Git 对象的必要工程开销。没有声称释放多个 GB。

逐项路径/SHA/恢复理由见 [DELETE_MANIFEST.csv](DELETE_MANIFEST.csv)、[DELETION_LOG.csv](DELETION_LOG.csv)。五个 `runtime/chrome*/Default/Cache/Cache_Data` 目录保留空目录；删除目录数为 0，checkout 删除数为 0。39 个既有项目目录和本任务 checkout 完整保留。

检查发现 11 个缓存响应含旧版本 GLB/HTML/JSON，与现有源不同，不能直接视为当前源的重复文件。已将这 11 个完整缓存文件压缩归档至本任务 `local_only/historical_http_cache.tar.gz`，每个成员完整读回并比对原 SHA。位置、archive SHA、成员 SHA 与恢复方法见 [CACHE_BACKUP_MANIFEST.json](CACHE_BACKUP_MANIFEST.json)。这是 LOCAL_ONLY 可靠单机副本，不是异地备份，必须保留；禁止再将该归档当作可丢弃缓存。

其余缓存为源响应的完全重复/浏览器索引/可再生成浏览器资源。删除前复核路径真实位置、非符号链接、inode/device/mtime/大小/SHA、无活动 Chromium profile、所有原源资产和归档；按单文件 unlink、逐项 fsync 回执，不递归删目录。恢复证据见 [CACHE_RECOVERY_PROOF.json](CACHE_RECOVERY_PROOF.json)，其中初审不满足项由独立备份证明补齐，初审文件保持不变。

删除后 3,173 个已登记保留资产 SHA 未变，包含 3,169 个 checkpoint/weight 文件；20 个响应源文件仍可访问。39 个旧目录 HEAD 与 Git 状态签名未变，悬空提交 `3da9852b25fd82f4f158299a264d9a433aa572da` 仍在。详见 [POST_CLEANUP_CHECKS.json](POST_CLEANUP_CHECKS.json)。全部真实 Smoke 与契约重测通过。受保护的两个目录没有写入/清理操作；未修改/删除远程分支，无 GC、clean、reset、force push。
