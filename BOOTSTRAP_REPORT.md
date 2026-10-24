# BOOTSTRAP_REPORT

日期：2026-10-24（Asia/Shanghai）。任务性质：一次性独立仓库初始化，非科研Task。

**结果：本地初始化通过；创建与首次推送命令成功，但远端读回因TLS超时阻塞，不能标记REMOTE_BOOTSTRAP_PASS。** 新库只含BOOTSTRAP_ONLY治理种子，未导入三维源码、图表或大工件，未运行模型或科学实验。BASELINE-3D-001仅形成待审批迁移计划。

## 1. 实测状态

| 验收项 | 结果 |
| --- | --- |
| 本地独立目录/Git根 | `/home/liu/ring_first_3d` |
| 默认分支 | `main` |
| 首次种子提交 | `55f4bc29efa7a055acfe03546f2980b914ef0a4c` |
| 目标远端 | `https://github.com/zheng1524/ring-first-3d` |
| 创建命令 | `gh repo create zheng1524/ring-first-3d --private --source=. --remote=origin --push` |
| 目标预检查 | GitHub连接与本机gh均返回同名目标404；创建前本地目录不存在 |
| gh鉴权 | `gh auth status`成功，活动账号zheng1524，HTTPS；未输出凭据 |
| 创建/首推返回 | exit0，返回仓库URL及new branch HEAD→main |
| 可见性 | 创建命令明确使用--private且成功；独立API读回尚未完成 |
| 远端README/commit读回 | **未通过**：首次GET仓库元数据即TLS handshake timeout，后续读回未执行 |
| 本地origin/main缓存 | `55f4bc29efa7a055acfe03546f2980b914ef0a4c`，来自成功push；它不等于独立远端读回证据 |
| 总状态 | LOCAL_BOOTSTRAP_PASS / REMOTE_CREATE_PUSH_ACKNOWLEDGED / REMOTE_READBACK_BLOCKED |
| REMOTE_BOOTSTRAP_PASS | **未标记** |
| 科学基线 | BOOTSTRAP_ONLY；未创建任何baseline tag，未导入算法源码 |

失败原文：
```text
Get "https://api.github.com/repos/zheng1524/ring-first-3d": net/http: TLS handshake timeout
```

依据本次`BOOTSTRAP_OLD_CODEX.md`的“若鉴权或API失败，停止远端操作”，已停止所有后续远端调用，未通过其他连接绕行或重试创建，没有改投旧仓库公开分支、没有强推。本地后续只保存报告和计划，**本报告及计划为LOCAL_ONLY，未追加推送**。

仓库创建和push已有CLI成功回执，因此**不要立即重复创建同名空仓库**。人工最短操作：打开上方URL，确认Private标识、main及提交`55f4bc2`与11份文件；若人工确认仓库确实不存在，再按原授权创建同名空私有仓库并回传URL。网络恢复/人工复核后才补远端读回和报告增量上传。

## 2. 首次提交的11个文件

包内10项内容清单全部匹配，独立`BOOTSTRAP_OLD_CODEX.md`与包内版本逐字节相同；整个包SHA256为：
`1d3a7337cbbb6267ea94a95acd0eb8444ba43041383b32e0f268d2bbf38596e5`。

| 首次种子文件 | 字节 | SHA256（Git blob内容与包一致） |
| --- | --- | --- |
| `README.md` | 798 | `1e23ea75c07af881bc03cfa6b15c0112c0f99d9c7f5ff033107139a6e32db232` |
| `AGENTS.md` | 1111 | `2280f3e040fd5989bdf2c672bec36334a7d1080e5fe71d1ee6f65ded5b957051` |
| `COLLAB_STANDARD_v1.3.md` | 6037 | `e7663963d9a74f633c7c73853ca62c136aa17618295d409cb4a0f2dd7d62cdc3` |
| `PROMPT_RA.md` | 1322 | `66d7fe495e6983f497a76183c47d0eb29e219122db2715c4fac3f9b08d2d4a10` |
| `PROMPT_PM.md` | 1366 | `1da63ef64c4703f256cf9b61bc2402a5da2ded553edd1a4509a7db8ae5abfb06` |
| `PROMPT_CODEX.md` | 1921 | `f4f60a8392ac8de6298459460da6bc0adbcda565001c3a86bf567f0d05c2b4b5` |
| `BOOTSTRAP_OLD_CODEX.md` | 2994 | `2097603a2e7616de0af1c16ec11637c092b2cc42e5a9f4092f3ffd57795ec6d9` |
| `BASELINE_IMPORT_CHECKLIST.md` | 1141 | `25dcd83924a31302602d9e1526d525975f9209bdc71d1218840e5ec099f8707f` |
| `HANDOFF_TEMPLATE.md` | 363 | `f3b3cd518a33bfd7fd03a8e1fdf0fcb7c3832fc01fac7b0f842673042d55627f` |
| `PACKAGE_MANIFEST.json` | 1505 | `ecd24a4a55bf855e222e401085a13f46bcbff4bce8f992b1efc0746bb38b87db` |
| `.gitignore` | 349 | `db174d49903f62a4da2932ee206c03a1bc27abbb6bd56ce2bea59b0924c10d0e` |

首次种子仅这11件，不含本报告/迁移计划，更不含旧源码、PNG、GLB、视频、权重、GT或环境。包中的`PACKAGE_MANIFEST.json`原样保留，其REPO_CREATION_PENDING是输入包快照状态，不是本报告的实测状态。README明确BOOTSTRAP_ONLY，不把种子提交当算法可复现基线。

本机Git2.25.1不支持示例中的`git init -b main`；第一次命令失败后，保留已核验文件，使用等价的`git init`加`git symbolic-ref HEAD refs/heads/main`完成初始化。未删除目录、未更改包内容。提交作者沿用已有Git配置，只在新库本地配置中设置，未改旧库或全局身份。

## 3. 旧工作树和关键资产保护

| 项目 | 本轮只读复核 |
| --- | --- |
| 旧宿主Git根 | /home/liu/polyp_research |
| 旧HEAD/main | 4483e25ede3eee1b6eaf96254d2544152f935c0d |
| 旧远端 | https://github.com/zheng1524/polyp-resarch.git |
| 旧未提交 | 14个已跟踪修改、2599条按文件展开的未追踪项；不含大量ignored实验 |
| Ring-First工作区 | /home/liu/polyp_research/ring_anchor_3d；自身无独立Git；对旧宿主已跟踪数0 |
| 忽略规则 | 旧.gitignore第25行experiments/覆盖三维实验目录 |
| 原实验 | 39目录、此前约22GiB；均原位保留，不镜像、不移动 |
| DXY-MID | /home/liu/new-polyp-dxy；HEAD 75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95；只读，未修改 |
| 最新Hull | occlusion_visual_hull_20261024已执行，未通过新PM科学验收，不重跑“首次Hull” |
| 最新点云过滤 | pointcloud_surface_filter_vnext：SOR/ROR/2.5D未证明默认收益，P0原始几何保留 |

旧宿主HEAD不能代表当前LOCAL_ONLY源码。迁移计划中的51份候选源文件和14项小型引用资产已记录实际路径/字节/SHA，3份历史主报告和3张候选关键PNG也只记录来源和哈希。模型大权重只记录既有官方校验SHA与当前文件大小，未加载、未上传；原视频、完整深度、GT及虚拟环境不进Git。

最终保护核验结果由本次本地复核确认：旧宿主HEAD、索引、完整Git状态及14个原有修改文件哈希保持一致，DXY的HEAD/索引/状态保持一致；计划中的旧源文件与引用资产未变。本轮没有对任一旧仓库提交或推送。

## 4. BASELINE-3D-001迁移计划（只计划，不执行）

机器可复核的逐文件计划：[plans/BASELINE-3D-001.json](plans/BASELINE-3D-001.json)。

状态：**NOT_AUTHORIZED_TO_IMPORT**。51个候选源文件共333,214字节；清单不是已证明完整的依赖闭包，也不是授权全部复制。保留模块来源和逐文件SHA，拟按原层级放入`legacy_source_snapshot/ring_anchor_3d/...`；是否采用此路径还需审批。原文件均未复制。

| 迁移计划模块 | 候选文件数 | 本轮是否导入 |
| --- | --- | --- |
| Ring-First camera / shared identity | 10 | 否，仅清单/SHA |
| HERO and camera/depth interfaces | 5 | 否，仅清单/SHA |
| Historical independent local reconstruction and fusion | 6 | 否，仅清单/SHA |
| GT and conservative topology shared helpers | 3 | 否，仅清单/SHA |
| Latest pointcloud processing | 11 | 否，仅清单/SHA |
| Latest executed unaccepted Hull | 15 | 否，仅清单/SHA |
| Pointcloud regression tests | 1 | 否，仅清单/SHA |

依赖已只读盘点：Python3.12.13、Torch2.7.1+cu128、Torchvision0.22.1+cu128、NumPy1.26.4、SciPy1.15.3、Trimesh5.1.1、opencv-python-headless4.11.0.86。Open3D0.19.0、scikit-image0.24.0、PyMeshLab2023.12.post3分别来自既有独立vendor树，**不是仅靠基础venv就完整具备**。所有记录来自元数据，未导入模型或执行科研测试。

后续审批建议顺序：

1. 审核逐文件清单、动态`common.py`导入、`Path(__file__)`父目录假设、硬编码数据/DXY路径和第三方许可证，冻结准确源码/配置/输入身份。
2. 用户批准后，先增量纳入最小P0反投影/Mesher及HERO接口、必要配置和来源manifest；相机与HERO冻结结果仍是带哈希外部输入。DXY源码仅作为外部只读依赖，不复制进来变更。
3. 在新空输出目录做一轮有界独立重跑和原像素/坐标/三角面一致性检查。只有旧日志或重新渲染历史GLB不算独立复现。是否运行一次HERO推理另由批准任务限定。
4. 用户结合PM/RA复核批准后，才冻结正式baseline源码commit、数据manifest/GT协议并创建baseline-3d-001标签；工程可复现不等于真实三维精度已认证。
5. 再选择性纳入已批准的历史重要报告和少量真实PNG/小表。原39实验和全量工件仍LOCAL_ONLY；不将失败的过滤/Hull诊断自动变成正式默认。

计划已列三个候选关键图：点云Accuracy—Coverage失败对照、最新Hull真实三维总览、GT支持面误删证据；目前全部只登记，不复制、不上传。历史同名Blender为可信形状GT，但部署位姿UNKNOWN，G04确切GT缺失，004/005跨视频关系UNVERIFIED。上述复现命令在计划中只是待审核的历史接口，当前不执行、不承诺能从新库直接运行。

## 5. 本地报告提交与停止

首次种子提交已获得CLI创建/首推成功回执；独立读回未完成，整体不能报REMOTE_BOOTSTRAP_PASS。本报告与迁移计划将仅做本地增量提交，停止远端操作后不push，其本地提交SHA在最终消息给出。不会自动迁移科学代码、跑模型或创建科学baseline tag。

本轮只生成这份`BOOTSTRAP_REPORT.md`；包内原有治理/提示词Markdown不是新增科研报告。下一步需要人工确认远端Private与seed提交，并审批或缩减BASELINE-3D-001计划。到此停止，等待人工审核。

