# M2F13 最终报告

三项工作已完成：退役资产按路线归档并实际清理；补齐H004全部76个原合法Target并展示两线全部生成面源；提交三个统一Ring-First候选、推荐架构和最小验证计划。新主线没有实施，交由研究者审阅。

## 四项主交付

1. [CLEANUP_FINAL.md](CLEANUP_FINAL.md)：逐技术处置、精简归档、保留消费者、例外和清理阶段空间。
2. [HERO_ALL_VIDEOS_INDEX.html](HERO_ALL_VIDEOS_INDEX.html)＋[SOURCE_MANIFEST.csv](SOURCE_MANIFEST.csv)：固定10视频×2路线、全部原输出身份/指标/图像，附[VIDEO_SUMMARY.csv](VIDEO_SUMMARY.csv)。HTML使用相对链接，下载任务目录后可离线浏览；GitHub原文件预览不执行HTML。
3. [MAINLINE_DESIGN.md](MAINLINE_DESIGN.md)：A顺序建图、B统一观测与有限多初值、C稠密联合优化三个候选，推荐B；21个确切源码身份、阶段接口和下一轮可证伪实验。
4. 本报告：完成情况、关键证据、空间与下一步决策。

## 清理结果

沿用M2F12审计目录，刷新141个退役根，逐文件保存源身份、配置、结论、失败状态及代表证据。删除18,847个文件，错误0；23个公共Open3D重复文件与唯一权威环境共享inode，原路径/字节保持。所有E2不安全/最后安全检查点、两视频正式完整H2代表及unknown证据、RAW/GT/CAD、现用HERO模型和Graph/ARAP/Sweep保留。MapAnything缺失权重未虚算本轮收益；共享环境不因旧应用退役而卸载。

完整精简证据归档94,516,429B本地保留；源码/报告子归档5,584,207B上传。每条退役路线的已删路径/字节、剩余路径/体积/消费者及确实不明的个别例外在CLEANUP_FINAL及压缩清单中，不以“混合目录复杂”整体跳过。其他工作通过30,975个文件内容SHA和7仓库binary patches保护；没有在旧P脏main提交或清理Git历史。

同一挂载点 `/`，device=66307：

| 时点/项目 | 字节 |
|---|---:|
| 全任务开始可用 | 9,698,865,152 |
| 删除前（归档已落盘）可用 | 9,590,321,152 |
| 删除后可用 | 13,428,973,568 |
| unlink实测净释放 | 3,838,652,416 |
| Open3D重复库实测净释放 | 306,925,568 |
| 清理阶段结束可用（含归档/证据） | 13,721,907,200 |
| 清理阶段实际净增加 | **4,023,042,048（3.7467 GiB）** |
| HERO、图集及本地提交后可用 | **12,370,190,336（11.5206 GiB）** |
| 全任务至该快照可用净增加 | **2,671,325,184（2.4879 GiB）** |

最后快照见[FINAL_SPACE.json](evidence/FINAL_SPACE.json)。清理阶段收益与新增产物后的最终余量分开报告；df包含同期系统写入，不能将两时点差全部归为某个Mesh。M2F13本地run占572,600,320B、任务目录110,931,968B（包含本地未上传的大审计JSON），原V6/M12大资产直接引用。实测保留产物远低于预留2GiB输出额度；这是顺序写入、未删除中间结果的磁盘占用证据，不冒称连续采样的瞬时峰值。同盘搬家及硬链接重复名不算释放。

## HERO补齐与展示

首次新推理前冻结完整CAMERAS/SUPPORTS及每个Target唯一原3-Support组合，预算为76合法Target、7复用、69新增。7旧结果以RAW/RGB/Mask/K/C/模型等完整输入身份核验，未按名字复用。69新增全部完成，运行失败0、资源重试0；未重新解相机、重建地标、替换组合、按深度择优或改M2F12每视频1次协议。新增运行身份为 `c08ef3d292469e33469589f5268b0a0c283c42fd`。

| 物理组/视频 | H004合法/可渲染 | H004复用＋新增 | V6唯一生成组合 | V6原正式成员 |
|---|---:|---:|---:|---:|
| IIa14/R10 004 | 4 | 1＋3 | 21 | 17 |
| IIa14/R10 005 | 0 | 0＋0 | 4 | 0 |
| Ip12/R10 004 | 15 | 1＋14 | 4 | 0 |
| Ip12/R10 005 | 11 | 1＋10 | 17 | 15 |
| Ip20/R10 004 | 15 | 1＋14 | 4 | 0 |
| Ip20/R10 005 | 15 | 1＋14 | 4 | 0 |
| Ip8.8/R5 004 | 10 | 1＋9 | 14 | 12 |
| Ip8.8/R5 005 | 6 | 1＋5 | 15 | 13 |
| Is14/R5 004 | 0 | 0＋0 | 11 | 9 |
| Is14/R5 005 | 0 | 0＋0 | 4 | 0 |
| 合计 | **76** | **7＋69** | **98** | **66** |

H004覆盖7/10视频，seed基本精度通过0/10的旧事实不变。V6原正式来源覆盖5/10视频；**66成员只有14个Target自身VALIDATED，52个未VALIDATED，三Support均合格**。两线“原正式成员”均不得称为共同独立质量通过。3个H004空视频和所有V6未通过/中断尝试在固定分母与失败清单中保留。

V6收集22个既有RUN_STATE根的123条生成记录及M2F12五条原生诊断，共128条来源、98唯一完整输入组合、30别名，66正式成员核对无增减。25个同类别名原NPZ字节一致，五个跨CORE/V6别名深度数组相同但保存/原Mesh表示不同；全部204条输出分别保留自身指标。32个诊断输出原有深度但没有Mesh，本轮仅调用原V6转换定义生成Mesh：352→360线性深度插值、原Polyp Mask、三顶点轴向Z极差≤.75mm。H004保持原生352×640转换。没有将二者偷偷统一成新算法。

173张真实数据图包括：20条路线×视频各自全部数值/原正式成员的RGB及按源着色六视角；全部174个唯一面源逐源侧视图；30重复来源原输出图；按时序首/中/末选择的RGB/Mask、3 Support及资格图；相机轨迹和RAW帧号；不同V6尝试原坐标分开图；带逐视角裁切计数的补充近景。所有几何保留原毫米坐标和原三角面。六视角沿既有renderer布局适配为统一世界观察方向，没有ICP、额外缩放、形变、融合或挑面。近景不替代完整范围，黑色Ring为真实CAD，透视毫米比例尺标明中心深度。

关键图：

- [H004 Ip20/005全范围分离与长尾](figures/H004_RAW_BASELINE__GP_Ip_20.0mm_closed_R10_single_refY_005__ALL_NUMERIC__SOURCE.png)
- [H004 Ip12/004同一世界近景及裁切数](figures/H004_RAW_BASELINE__GP_Ip_12.0mm_closed_R10_single_refY_004__NEAR_GAUGE_00.png)
- [V6 Ip12/005原正式成员六视角](figures/V6__GP_Ip_12.0mm_closed_R10_single_refY_005__FORMAL__SOURCE.png)
- [H004 R5 Ip8.8/005 RGB、Mask与Ring大尾部](figures/H004_RAW_BASELINE__GP_Ip_8.8mm_closed_R5_single_refY_005__REPRESENTATIVES.png)

观察到H004 Ip20部分源Ring P95约69–74mm，5mm色标不能说明其尾部；图中同时写超标比例、最大值、MAE/P95。V6 Ip12/005同一次运行的原正式面也明显分层，Ring附近较接近不能代表整个Polyp一致。A→B的B参与HERO，只是条件一致性诊断；CAD共同覆盖依赖相机，不是独立深度有效率。未使用不同帧平均成绩宣布哪条路线更优；无部署poseGT的绝对精度、共同全链路独立有效覆盖仍为NOT_EVALUABLE。

## 验证、源码及提交身份

最终只读验证：408份输出native/Mesh完整SHA、176份科学源码、2991份M2F12冻结文件、30,975份既有工作文件均匹配；30组别名深度逐元素相同；69新增严格符合预算；20条视频×路线和204来源完整，316个HTML引用存在。清理6项边界测试、M2F12既有16项测试及Open3D真实射线/保留依赖检查通过。执行入口和环境见[REPRODUCTION.md](REPRODUCTION.md)。详细结果见[FINAL_VERIFICATION.json](evidence/FINAL_VERIFICATION.json)、[POST_CLEANUP_VALIDATION.json](evidence/POST_CLEANUP_VALIDATION.json)、[审查修订记录](evidence/REVIEW_B_AND_DESIGN.md)。

原V6正式执行为RUN_STATE中的a38d4c8，早期诊断尝试各自实际commit在CSV中。旧M2F12 HERO未记录执行commit的条目明确NOT_CAPTURED，保存原INFERENCE_STARTED路径/SHA、原源码SHA和输入SHA，不拿M2F12报告commit补填。官方权重完整SHA和协议在MODEL_RECEIPT；本次配置/完整原元组以PLANS_FROZEN.json.gz上传，RAW、模型、完整大Mesh留本地准确路径和SHA，无整套重复打包。

独立分支：`exp/TASK-M2F13-CLEANUP-HERO-VISUALIZATION-MAINLINE-DESIGN-001`。

- 清理/共享依赖提交：`f757c1ac6d451819e81dd78e2c78458ff7b53010`。
- 新HERO预算与实际执行代码：`c08ef3d292469e33469589f5268b0a0c283c42fd`。
- 全源评价与图集提交：`9975762db462ab47e1d8eb393b5649ec9461e91c`。
- 主线设计与本报告另作独立提交；其最终远端SHA在人工收尾消息给出，避免报告自引用commit循环。

沿用已授权GitHub Git-data上传方式，逐blob、tree、commit与本地SHA一致后以`force:false`更新任务分支，并重新读远端ref。此方式不冒称常规git push成功；最终发布回执保存在本地run/PUBLISH_RECEIPT.json。没有修改旧P/W主分支、合并或强推。

## 下一步决策

请研究者讨论B方案及P0–P2：固定同RAW帧、统一FIT/DEV/TEST身份、冻结地图后的40个新query；只在其提供有效证据后考虑P3同Target/Support元组的≤30次HERO。TEST评价地图独立于求解地图，DEV候选选择不读query；覆盖、合法组合与共同质量有效覆盖分开计数。推荐不等于已验证收益，更不宣称“全局最高”。本轮至设计交付停止。
