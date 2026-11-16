# 基线与审计范围

本任务工作目录为 ring-first-3d 独立 checkout；外层 /home/liu/polyp_research 的脏 main 和 DXY 工作区不参与提交。审计日期 2026-11-16，origin 为 zheng1524/ring-first-3d。已执行 git ls-remote，并只读 fetch main、历史审计分支等必要对象；没有 merge、reset、重写或覆盖现有分支。

| 远程分支 | 实际 SHA | 观察与处理 |
| --- | --- | --- |
| exp/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001 | 5636aaebd61a3d53b69f528692c4c7095df46508 | 已知最新科研基线；2026-11-16；用作本次 parent |
| main | 02dee8092dce9f89d050bccca35aa51768988645 | 2026-10-26；含批准 P0 renderer，未含最新科研结果 |
| exp/TASK-HISTORY-ASSET-AUDIT-002 | 7c961d994833a960917f9c36928559e85eb389ac | 2026-10-25；独立历史审计，非 repair 后继 |
| exp/TASK-FUSION-AUDIT-001 | 8852b64f1438490cd92df4923b9bf73ef4338056 | 2026-10-25；公开任务记录+精选图，不含公开完整报告 |
| exp/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001 | 492725ffd8e2fac86fe18099a87f7ef6d6d93b3b | 旧重定位结论；不覆盖 repair |

history-audit 与 repair 互不为祖先，merge-base 为 0ca219ab499b5178d3923818332bc8866288247d。未找到已核验且比 repair 更新的正式清理成果分支；完整观测到的分支名/SHA 在 [REMOTE_REFS.json](REMOTE_REFS.json)。这是当日快照，不保证今后分支不会变化。创建 exp/TASK-PROJECT-TECHNOLOGY-REGISTRY-001 于 repair SHA；本任务不合并历史审计内容，只给不可变链接。

DXY 只读 HEAD 为 75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95，main 与 origin/main 一致；V9.1 + Mid + 视频等权中位正式边界保留。

## 审计方法与覆盖

先阅读 README、AGENTS、COLLAB_STANDARD_v1.3、E4 路线图/技术版本，再按二维、视角、相机、HERO、主体/P3D、失败路线检查报告、失败台账、复用/复现文档、provenance/metrics 及相关源码；随后编写本注册体系。没有先画目录再凭实验名填状态。

- 33 项主题化重要实验条目；同一 snapshot commit 用于可重现地引用报告字节，另列各历史 branch tip。
- 43 个模块条目、41 份不同 Python 文件（含 2 份 DXY 外部源码），函数/类均静态核验并计算完整文件 SHA256。
- 82 份精选报告/指标/回执证据的哈希在 [EVIDENCE_MANIFEST.json](EVIDENCE_MANIFEST.json)。
- 基线发现的 54 份顶层 TECHNICAL_REPORT 见 [REPORT_CATALOG.json](REPORT_CATALOG.json)。DISCOVERY_ONLY 不代表做过充分科学审阅；重要嵌套 010–013 另入主题索引。
- 本轮是面向用户列出的关键技术路线的选择性审计，不是所有历史脚本/数据/资产的全量普查。未核验的条目不得继承已验证状态。

## 可复现版本解释

EXPERIMENT_INDEX 的 COMMIT_SHA 指报告所在的不可变版本；DATE 为该报告在快照中的最后提交时间（远程审计为 tip 提交时间），不是虚构的实验实际执行日。历史执行日与源码冻结以原报告/provenance 为准。HISTORICAL_BRANCH_TIP 单列，禁止把 branch tip 当作当前代码文件一定相同的证据。

所有模块卡的 source_commit 与 SHA256 要同时匹配。旧 main 的 renderer 与本快照不同，已如实记录 branch_tip_byte_match=false。独立审计分支的部分完整报告未公开：FUSION-AUDIT 只索引 PUBLIC_TASK_RECORD，不声称可下载其本地全部资产。
