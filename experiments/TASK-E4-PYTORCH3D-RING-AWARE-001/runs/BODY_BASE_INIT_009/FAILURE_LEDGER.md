# 失败与限制台账

| ID / 病例 | 阶段与具体原因 | 处理及证据 |
|---|---|---|
| INPUT-DUPLICATE / 临时 IIa22 | 起初把已属于 G08 的物理标本误作新增候选，多执行了一次分割/相机/HERO 流程 | 主体拟合前排除；原始临时文件保留在 new_input_pipeline_DUPLICATE_G08_EXCLUDED；[身份记录](assets_index/DUPLICATE_IDENTITY_FAILURE.json)、[原流水结果](assets_index/DUPLICATE_CANDIDATE_PIPELINE_RESULT.json)、[路径搬迁索引](assets_index/DUPLICATE_PATH_RELOCATION.json)。实际第九例 IIa4.5 |
| PROVENANCE-SCOPE | NEW_PIPELINE_RESULT 的 existing_eight_HERO_not_rerun 只描述随后独立 G09 流程，不能概括排除候选之前的所有计算 | 保留原记录并增加 [范围更正](assets_index/PIPELINE_SCOPE_CORRECTION.json)，既有八例正式文件未被替换 |
| G01 | 低维目标有所降低，但 Mask/固定深度代价退化；弱基底、小接触不支持截断 | [详细图](figures/Fig_Ip_Detailed.png)、[逐参考表](metrics/PER_VIEW_METRICS.csv)。不宣称重拟合普遍有效 |
| G02 | C9 截断无相交但丢失轮廓解释；头/柄、接触代理与冠面表达存在冲突 | [完整图](figures/full/G02_Detailed.png)、[薄/厚区域诊断](metrics/MASK_REGION_COVERAGE.csv)。薄厚只由统一距离变换定义，不冒充解剖标注 |
| G03 | B/C 仍约 0.019953 mm CAD 样本穿入，三初值中心差 4.11 mm | [完整图](figures/full/G03_Detailed.png)、[稳定性](metrics/MULTISTART_STABILITY.json)、[Blender](metrics/BLENDER_GEOMETRY.json)。保留 NO_FEASIBLE 诊断输出 |
| G04 | 三初值都到达 nfev 上限；稳定输出不等于充分收敛；C7 轮廓及绝对深度代价退化 | [完整图](figures/full/G04_Detailed.png)、[阶段表](metrics/STAGE_PARAMETERS.csv)。没有追加搜索 |
| G05 | B/C 仍约 0.002147/0.005702 mm CAD 穿入；初值中心差 2.55 mm；弱基底不允许硬截断 | [完整图](figures/full/G05_Detailed.png)、[数值诊断](metrics/POSTERIOR_NUMERICAL_DIAGNOSIS.json) |
| G06 | B/C 约 0.006915/0.015711 mm CAD 穿入；C 的轮廓略恢复而固定深度代价退化 | [IIa 详细图](figures/Fig_IIa_Detailed.png)；仍保留碰撞失败，不用“地下体消失”制造通过 |
| G07 | B/C 约 0.010999/0.007001 mm CAD 穿入；C 降低深度覆盖，条件 MAE 与固定分母结论不同 | [Is 详细图](figures/Fig_Is_Detailed.png)、[固定观测表](metrics/FIXED_DENOMINATOR_DEPTH.csv) |
| G08 | C 无相交且深度代价降低，但轮廓与射线覆盖下降 | [完整图](figures/full/G08_Detailed.png)，保留取舍，不自动晋升 |
| G09 | 只有一个原生深度参考，基底 WEAK；弱 C 基本不动 | [完整图](figures/full/G09_Detailed.png)，多视角 Mask 可用不等于多视角深度已认证 |
| SCORE-LEGACY | 继承的 fixed_censored_relative_mm / fixed_denominator_relative_score 对高误差命中无统一上界，2.5mm 未命中代理可能奖励丢覆盖 | 原字段不删、不参与选模；新增与实际目标一致的有界代价及固定分母，见 [审计](metrics/DEPTH_SCORE_AUDIT.json)。未改优化损失或重新选模 |
| PREFLIGHT-V1 | 首次 cap γ=2 对等测试误把推断底面中心计入可见高度场，触发假不等 | 原失败文件保留 assets_index/PREFLIGHT_V1_CLOSURE_INCLUDED.json；改为同语义上表面验证通过，不改模型/标准 |
| FIGURE-V1 | 首次出图缺少 open3d 导入 | 仅修正绘图导入，原日志 runtime/FIGURES_V1_MISSING_IMPORT.log 保留；未重跑优化 |
| DIAG-V1 | 第一份冻结后数值诊断遗漏弱 C 先验项 | 原诊断存 assets_index/NUMERICAL_DIAG_WEAK_TERM_OMITTED_V1.json；最终只读完整项重算，未更新预测 |

实际 CAD 相交由独立实现共同报告；微米级样本穿入不等于整条相机或 HERO 失效，也不据此宣称数学模型不可行。完整三维真值、解剖基底及隐藏表面均未验证。数值 Jacobian 对步长敏感、有限预算和软碰撞约束仍是工程限制。本轮结束后没有继续修补失败。
