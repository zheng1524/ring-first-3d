# Failure ledger

资格不足是科学结果，不用工程PASS替代。没有认证的新位姿，正式修正输出NaN，所有原始输入保留。

| 相机 | 步骤与原因 | 解释限度 | 证据 |
| --- | --- | --- | --- |
| ref03 | Ring通过；与ref08主SIFT fit/held内点41.7%/40.0%，与ref13 LightGlue fit56.3%低于70% | 有中等残差且方法依赖；不足以归因实际pose错误 | [全部方法](config/IMAGE_GEOMETRY_ALL_METHODS.csv)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| ref08 | Ring通过；与ref13通过，与ref03主方法未过 | 两视图关系不能唯一归因哪一相机错误 | [原始完整结果](config/ORIGINAL_TEST12.json)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| ref13 | Ring通过；与ref08通过，与ref03主LightGlue未过 | 历史相机非GT，额外留出未用于本轮pose拟合 | [Fig1](figures/Figure1_Ring_validation.png)、[Fig2](figures/Figure2_real_matching_geometry.png) |
| new_r00 | Ring MAE3.35/p956.71px略超容差；到ref08/ref13仅11/5 raw SIFT点；无独立F与充分覆盖 | 到ref03通过；尚未达到明确矛盾，不能宣称实际位姿错 | [匹配充分性](config/RGB_ONLY_METHOD_SELECTION.json)、[Fig1](figures/Figure1_Ring_validation.png) |
| growth_r04 | Ring及ref03/ref08通过；ref13 raw36、F相容fit26/held3，held不足8及覆盖不足 | 无明确拟合侧误差，不为取得数值而修正；保留候选 | [Fig2](figures/Figure2_real_matching_geometry.png)、[Fig3](figures/Figure3_original_HERO_projection.png) |

## 工程事件与保留记录

- ENG01：新worktree初次sparse-checkout缺少其独立git管理目录info，命令失败，无历史文件改动。建立本worktree自身info后成功，未重置或清理其他工作树。
- ENG02：初版资格reducer只检查两条关系，遗漏新增相机必须有ref13的冻结身份条件，曾临时将growth_r04记为CONDITIONAL。交付前复核发现并修复；恢复所有必需身份检查，最终INSUFFICIENT。**不是修改阈值**。保留初版文件SHA及前后状态，[实现修复记录](config/ADJUDICATION_IMPLEMENTATION_FIX.json)。所有指标、配对和优化触发均未改变，优化器仍0次，未重新搜索。
- 原始Test12结果、原始无先验秩、两次NOT_ATTEMPTED原因和初版状态均保留；历史before-correction freeze中的初版状态不能当最终资格，最终以CAMERA_QUALIFICATION.csv为准。
- 辅助匹配偏移：原HERO点只有Polyp，部分主SIFT主要落背景，N=0明确保留，不补背景融合几何。稀疏投影孔洞不补面，不将高Mask精确率当物理准确。

没有训练/模型/网络推理错误，因为本轮未调用这些功能。没有为了提高通过率更换来源、追加匹配器推理、扩大边界或修改标准。
