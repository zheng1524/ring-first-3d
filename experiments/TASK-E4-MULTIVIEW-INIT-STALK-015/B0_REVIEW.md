# B0_REVIEW

本轮不把数值输出、Mask IoU或刚性对齐后的全体尺寸等同于B0通过。章程要求Ip具有合理头柄连接与空间延伸，且几何不能有严重自交/薄片/拓扑错误。以下是全部11组的原始证据。判定不使用GT选择预测。

| 病例 | 冻结路线 | FIT/HOLDOUT IoU | HERO覆盖 | 自交/连通分量 | Ring密集穿透mm | B0证据状态 |
|---|---|---|---|---|---|---|
|G01|Stalk-C|0.9209 / 0.9192|1.0000|0 / 1|0.000000|STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION|
|G02|Stalk-C|0.9167 / 0.9208|1.0000|0 / 1|0.000000|STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION|
|G03|Stalk-C|0.8479 / 0.8549|0.8906|0 / 1|0.006162|STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION|
|G07|Init-A|0.8633 / 0.8588|0.9570|0 / 1|0.000967|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G04|Init-A|0.8543 / 0.8472|0.9922|0 / 1|0.000000|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G05|Init-A|0.9628 / 0.9628|1.0000|0 / 1|0.008370|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G06|Init-A|0.9506 / 0.9527|1.0000|0 / 1|0.001085|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G08|Init-A|0.9046 / 0.9064|0.9766|0 / 1|0.000000|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G09|Init-A|0.8512 / 0.8366|1.0000|0 / 1|0.000000|REQUIRES_VISUAL_STRUCTURE_AND_STABILITY_REVIEW|
|G10|Stalk-C|0.8995 / 0.8932|1.0000|0 / 1|0.000000|STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION|
|G11|Stalk-C|0.8830 / 0.8680|1.0000|0 / 1|0.000000|STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION|

**全11组B0：尚未证明通过（NOT_CONFIRMED）**。这是保守的证据判断，不代表整条路线科学失败。Ip的中心线种子是轮廓代理，不能自动当作真实柄部；需要结合保存的三维和留出轮廓检查。非Ip若形态、尺寸与初始化稳定性已足够，不继续增加局部更新复杂度。可提出单视频HERO—主体适配候选，但本轮不自动执行。

数值细节、三种方法全部失败与成功输出均保留。对已有微小CAD接触与新增穿透分开解释；一个密集采样标记不能自动冒充严重物理错误真值。真实坐标的绝对GT误差缺独立标定，ICP后指标只能描述形状。人工审阅后可对具体组确认B0，不用再无限延长主体优化。

## 实际图片审核后的结论

全组结论为 **B0_NOT_PASSED_THIS_RUN**，而不只是等待自动指标。G03 是明确反例：Stalk-A 不更新，B 为扁平翼状突出，C 无可信长柄，均不能提供章程所需的头柄空间骨架。G01/G02/G10/G11 保留 STALK_SPATIAL_SKELETON_REQUIRES_VERIFICATION，未凭全体尺寸或 Mask 指标升级。六个 Is/IIa 为人工可审阅的连续粗主体候选，保留表中 Ring 与初始化稳定性限制，不追加本轮局部优化，也不声称获得测量认证。该判断不改变任何冻结输出或 FIT-only 选择。
