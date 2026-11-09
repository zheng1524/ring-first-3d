# E4 关键技术候选 v0.20：多视角初始化与 Ip 柄部更新

状态：AWAITING_HUMAN_REVIEW；不替换正式主线。分支 `exp/TASK-E4-MULTIVIEW-INIT-STALK-015`。

[技术摘要](../experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/TECHNICAL_REPORT_SUMMARY.md)；[核心图与模型索引](../experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/RESULT_INDEX.md)。继承同视频 Ring-First、原生 HERO、Mask、Ring CAD；11组固定8FIT，保护35个原HOLDOUT。无新HERO、跨视频修正或相机更新，DXY只读。

33条初始化路线和15条Ip路线完成。Init-B提升留出轮廓，但4/11组新增密集Ring穿入标记；Init-C同为4/11。冻结FIT/几何规则保留Init-A。Stalk-B改善G03残差覆盖并产生4.8904mm最大位移，但形成薄片状突出；Stalk-C仍未恢复可信长柄。冻结FIT-only候选为C，尚未成为科学推荐主线。全组B0本轮不通过，Is/IIa粗主体可交人工作为适配候选，不自动推进。

研究者追加允许逐预测固定尺度最佳6DoF ICP，全部81模型和尺度先冻结后GT评价。无镜像/缩放/非刚性修正。Chamfer跨组均值：Init-A/B/C FINAL为0.4829/0.4591/0.4592mm；五例Ip Stalk-A/B/C为0.5191/0.4816/0.5192mm。该评价仅描述姿态排除后的形状，不是端到端定位精度；不以Dxy接近掩盖G03缺柄。

| 审计项目 | 必须汇报 |
|---|---|
| 目标组数 | 11个独立真实物理组；Ip5、Is3、IIa3 |
| 本算法独立成功 | 33/33及15/15路线有数值输出；81/81初始/最终模型完成形状评价，不等于几何正确 |
| 本算法失败 | 无缺失模型；G03长柄恢复失败，B/C初始化新增Ring标记、G02初始及三个最终梯度加法FAIL保留；局部柄部精度与部分高度/严格实体IoU不可评价 |
| 历史测量值回退 | 0；继承起点明确标识，未用旧测量值补填 |
| 失败组及具体原因 | [失败台账](../experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/FAILURE_LEDGER.md)及全部路线日志 |
| 最终统计样本 | 初始化每路线11/11；Ip每路线5/5；逐指标另报有效N及NaN，不剔除失败组 |
| 是否使用GT选择算法 | 否；模型、选择与尺度冻结后才开放GT；源码/预测哈希及首次访问记录完整保留 |

下一步等待人工判断局部种子/可见性控制实验或部分主体适配；不追加本轮权重搜索，不自动替换主线。
