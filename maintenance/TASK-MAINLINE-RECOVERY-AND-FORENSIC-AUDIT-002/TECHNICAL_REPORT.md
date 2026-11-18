# TASK-MAINLINE-RECOVERY-AND-FORENSIC-AUDIT-002

工程审计与证据恢复已交付；**不宣布科研主线通过，不批准删除或退役**。本轮没有算法修改、历史结果重算、训练、资产迁移、环境清理或Git对象整理。独立智能体已直接核验Git/资产/指标并保留挑战；最终复核意见见审查包。

最重要的发现：Harness/mainline的Git对象域C通过alternates借用旧科研仓库B的**15,536个对象**。三套主项目Clone不能视为三套完整独立对象库。B必须保留原路径。旧母仓库另有大对象库与未提交研究修改，不能当普通旧目录清理。

## 范围与方法

用户附件在第十一节“在独”处截断，前十节审计范围与禁止项完整；原始附件及哈希保留。本轮从73568493d127d0aead361314afcb32e11fe886f0新建独立维护分支/worktree。所有旧源目录只读；唯一预期Git元数据增量为本轮分支/worktree/提交及正常增量push。无fetch/gc/prune/repack/删除/历史重写。`polyp_research`和DXY未写入。

56个资产扫描根，含所有旧`ring_first_3d*`、未被通配符覆盖的原目录、整个polyp_research、独立HERO core和只读DXY。自引用的本轮输出工作树排除，Git元数据独立统计，目录符号链接不递归跟随；具体外部引用另审计，动态/模板路径不冒充已解析依赖。版本、归档及共享环境大小不混为可节省空间。

## 科研证据恢复

核查5个指定任务并修复实验索引；实际代码/报告/失败记录及来源分支有文件证据。原执行SHA无法充分核验时标记SOURCE_COMMIT_UNVERIFIED；发布提交或当前HEAD不充当原执行提交。Structured执行cadde3e9、Structural执行6415993f（C0为原d78cacd8恢复）、Fusion执行16489355经报告及源码字节核对。Growth是分阶段恢复，执行身份用原freeze/source hash，发布bac3fc89不冒充单一执行SHA。维护001发布73568493也不是完整重放执行SHA。

模块表**69→99**：恢复既有SU01–06、SB01–11、GR01–13 Runner合同ID，没有为凑数新拆算法。IA01明确EXACT013身份；每项记录功能/入口/输入输出/依赖/任务/源码SHA/来源提交/实际运行证据/工程与科研状态/主线身份。E1/E2没有替换EXACT013。Smooth ARAP是Graph限制的自动微分版本，不宣称论文原始无约束求解器；原Sweep未接受、G03保护失败、根部外露等科学事实保留。

18个lineage任务加维护001建立19份EVIDENCE；39份复制的报告/结果卡原始字节全部保留。共7491条Markdown/图片/HTML/JSON/代码引用分类：{"VALID": 78, "MOVED_TARGET": 479, "EXTERNAL_DEPENDENCY": 4508, "BROKEN_TARGET": 2379, "MISSING_ASSET": 44, "UNRESOLVED": 3}。MOVED_TARGET共479条通过原始复制来源上下文定位，导航可直接访问实际文件及SHA。未恢复的链接仍逐项BROKEN/MISSING/UNRESOLVED；同名候选只列候选，未凭名字冒充同一历史图。各任务CANONICAL_REPORT及REPORT_LINK_AUDIT.csv是新增映射，未改历史报告以掩盖断链。这里包含JSON运行目录相对上下文缺失等问题，不能将全部BROKEN数量解读为独有资产真实丢失。

## Git法证结果

主项目55个工作树：A39/B1/C15（含新增审计工作树）；另母仓库与HERO core独立Git根。ring_anchor目录本身继承母仓库，不是另一个clone。vendor嵌套Git与DXY独立登记为外部依赖。工作树/refs/live remotes/alternates/pack/object/reflog/dangling/LFS/submodule见独立原始JSON和关系图。

| Object owner | Worktrees | Git allocated bytes | Physical objects | Borrowed objects | Physically unique objects | Ref-reachable unique commits |
|---|---:|---:|---:|---:|---:|---:|
| /home/liu/polyp_research | 1 | 6631833600 | 4182 | 0 | 4180 | 1 |
| /home/liu/polyp_research/ring-first-3d | 1 | 663298048 | 18417 | 0 | 53 | 0 |
| /home/liu/ring-first-hero-core | 1 | 6479872 | 146 | 0 | 117 | 2 |
| /home/liu/ring_first_3d | 39 | 703135744 | 18596 | 0 | 181 | 9 |
| /home/liu/ring_first_3d_harness | 15 | 614801408 | 7968 | 15536 | 5009 | 40 |

对象唯一性按实际本地pack索引及loose枚举，与可访问的alternate对象明确区分。唯一对象的压缩表示字节不等于可释放pack字节；未发现同SHA重复pack不能推出所有Git对象无重复。五个主扫描对象域只读fsck均exit0；仅reflog可达和无refs/reflog对象均逐库列出，未删除。副项目/vendor对象独立统计不并入主项目55工作树。

4个旧根共19项tracked未提交修改：polyp母14、e3_sdf_full3、e3_sdf_multi1、structural_update1。还有大量untracked和ignored科研源码/结果，e4_sdf_localization6257项untracked/94941项ignored。母仓库远端实查失败128，同步状态UNKNOWN，不以本地tracking refs代替实时证据。其他远端可读；完整未推送/独有commit列表保持在Git审计原件。56个非审计Git工作目录两次状态完全相同。

## 文件与存储

登记**446,601**项，逻辑字节**69,168,327,484**；全局唯一inode分配**53,558,677,504**字节（约49.88GiB），不包含独立统计的.git和外部conda目录。常规文件唯一inode368,887；符号链接53,263。扫描错误0。422150次HASH_RECOMPUTED包括368887个文件inode与53263个链接文本，24451条HASH_INHERITED仅从本次稳定同inode继承，均指明来源；不把旧审计哈希当新重算。symlink哈希是链接文本，不是目标内容。

严格同字节A/B重复48,341组；逻辑重复22,204,358,652字节，其中跨不同inode相同内容逻辑量5,648,797,648字节。**这些都不是批准可释放量**。1558组不同版本/运行关系保留；不能将近似Mesh、重压缩图像或不同运行当严格重复。单路径内容179,458项不意味着全部是独有科研真值。资产价值标签是保护性扩展名/路径启发式，UNIQUE_RAW_DATA/UNIQUE_MODEL_WEIGHT不构成来源或全局唯一性认证；UNKNOWN一律保留。

完整CSV.gz可流式读取，SQLite是本地便捷查询副本、不要求上传；CSV内容/数量与数据库对照验证。原始观察、模型、失败Mesh、训练轨迹和所有环境保留。本轮删除数0，迁移数0，释放空间声明0。基线001的节省数字没有被本轮重新加算。

## ZIP与运行环境

smart_endoscope归档3,973,431,261字节，SHA256 `daff4f3ecaeba826490c5de3b352d188f115a0bc34b1abe1b0da69f31776c6e2`。实际中央目录15571成员，6388个.jpg、4619种JPG内容哈希；3985成员有本地独立字节匹配，2403没有。此前2865不是当前完整中央目录计数，原计数范围不明，按子目录清单保留差异，不伪造调和。逐成员流式哈希/CRC验证，无磁盘解压，归档保留；统计只覆盖已审计根，不声称整个/home存在性穷尽。

发现4个pyvenv配置，实际依赖3个共享conda base环境（polypseg、vpo、息肉检测），不能把两个使用vpo的入口算成两份完整环境。尺寸、Python/torch/CUDA/ABI/引用者见矩阵及SHARED_BASE_ENVIRONMENTS。主线按原bash launcher实测：Python3.12.13、torch2.7.1+cu128、CUDA12.8、PyTorch3D0.7.9、Open3D0.19.0、FCL0.7.0.11；nvdiffrast在此环境不可导入，未安装。Blender及驱动命令原始输出保留。共享base环境全payload未重算哈希，明确仅尺寸/ABI审计；项目根文件/关键已引用依赖另有完整哈希。

官方HERO/DINO/权重依赖继承并核对本地主线manifest，唯一权重不覆盖。主线仍依赖旧polyp下Open3D vendor、共享base Python、原始数据/权重与Blender绝对路径。所有资产内Python/shell静态sys.path/PYTHONPATH/importlib/exec/路径/权重/数据引用均有行号与源码SHA。动态表达式未运行，不声称依赖闭包完成。现有shell入口0644需用bash调用；首次直接exec失败及纠正记录保留。跨机器复现仍NOT_CERTIFIED。

## 指标口径与科研结论

G01独立SE3形状MAE改善但固定INITIAL→GT框架变差，且F-score/覆盖下降；全部并列，不判定哪一个历史指标“唯一正确”。固定分母/采样/单位/GT访问/对齐副本与HERO世界坐标边界见METRIC_DEFINITION_AUDIT及12项矩阵。未重算历史距离。G01仍带根部外露，G03仍PER_VIEW_PROTECTION拒绝、正式柄长NaN；本轮不改变科研结论。未来协议仅为建议，不追溯套用。

## 收敛与独立审查

建议C作为规范Git身份、mainline作为唯一活动科研工作树，先解决B alternates依赖与A/C独有对象保全，随后另行授权收敛。当前无可立即执行的退役；harness_main_ready仅候选，其他历史工作树仅冷归档提案，每项均列理由/阻断/恢复步骤。LOCAL_ONLY/外部存储/实验开结项协议见PROJECT_CONVERGENCE_PLAN和逐工作树计划。不会为目录整洁调整历史结构。

独立审查包包含实测命令、关系图、pack/object身份、dirty/untracked/ignored清单、抽查与争议。16对硬链接、32项资产独立哈希抽查匹配；审查发现SYMLINKS导出SQL错误后已修复53263条，首版空导出及IR-009仍保留。ARAP/成长科研有效性不由本轮重新认证；不存在自动将NEEDS_MORE_EVIDENCE改为ACCEPT。

## 固定审计表

|审计项目|必须汇报|
|---|---|
|目标组数|工程：56资产根、55主项目WT、5指定任务、8项原核心模块证据；无新增测量目标|
|本算法独立成功|N/A，本轮无新预测；审计范围与文件数见原始表|
|本算法失败|N/A；保留历史G03正式NaN及未解决断链/来源身份/同步状态|
|历史测量值回退|0；历史数字仅审计对照，不生成预测|
|失败组及具体原因|Growth G03保护拒绝、G01根部缺陷；本轮工程导出/入口调用错误与修复均保留|
|最终统计样本|全量审计分母，不只报告成功/重复项；真实测量误差统计N/A|
|是否使用GT选择算法|否；没有训练、参数选择或历史科研重算，仅核对冻结后评价代码/文件|

## 审计局限与未解决问题

未认证跨机重建；未获得母仓库实时远端状态；旧来源执行commit部分不明确；动态路径/部分报告相对上下文未解析；归档独有成员和全部UNKNOWN需保留；科学局限及Ring面积容差量纲解释待审；没有执行任何收敛迁移。输出的新维护分支SHA在Git提交后另行记录，不在自身文件内伪造自引用SHA。

## 最终独立复核处置

独立审查已逐项核查58行计划：12项仅接受保留建议，46项NEEDS_MORE_EVIDENCE；没有任何立即退役获得批准。新增模块30项、历史报告39份、链接36个样本、指标12项与ZIP身份均经独立核验。原始IR-009/011/012/013/014挑战和纠正链保持可见，IR-010分类语义限制及其他未决项继续保留。详见[最终独立审查](INDEPENDENT_REVIEW_PACKAGE/FINAL_INDEPENDENT_REVIEW.md)和[逐对象决策](INDEPENDENT_REVIEW_PACKAGE/FINAL_RETIREMENT_DECISIONS.csv)。17项工程一致性校验通过并不等同全面审计认证或科研成功。

Git/资产计数对应本轮初始冻结快照，最终审计提交会产生预期的新Git对象，不能把快照计数误作持续实时读数。完整CSV重复路径字段较大，Python读者需提高csv.field_size_limit；数据库为本地便捷索引，便携导出均保留。
