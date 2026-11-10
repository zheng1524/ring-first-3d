# FAILURE_LEDGER

数值输出、几何验收和科学结论分开；不删除失败模型。

| 病例/条件 | 问题 | 证据 |
|---|---|---|
| G03 / S1及新机制 | 仍为片状/尖状延伸，不能作为可信柄部骨架；高IoU未解决结构 | [真实几何对照](figures/Fig4_Actual_Geometry_Update_Strategy_Comparison.png) |
| G02 / 数值 | 原默认粗分箱前向片元选择不稳定；保留015 FAIL，无分箱只做只读定位 | arms/DIAGNOSTIC/metrics/G02_BINNING_CONTROL.json |
| 虚拟初始门禁 | 原640→320最近邻target像素采样不一致，原0.97门槛失败，优化步数0；修复仅新增匹配网格Blender目标 | provenance/VIRTUAL_P3D_GATE_BEFORE_GRID_REPAIR.json、VIRTUAL_GRID_REPAIR_AMENDMENT.json |
| 工程中断 | 准备阶段空帧号、脚本语法及Blender seed超出int范围均在相关优化前修复；首次虚拟gate失败按门禁停止后再恢复；无模型覆盖 | runtime原始日志与provenance |
| 原初始化 G03/G07/G05/G06 | 初始已有穿入及B/C新恶化分类，不当作Unknown遮挡 | metrics/INITIALIZATION_COLLISION_CAUSES.csv |

## 每条新路线原始停止状态

| 病例 | 路线 | 接受/提案 | 状态 | 密集64新增/恶化面 | 深度覆盖下降 |
|---|---|---:|---|---|
|G03|MECH_COHERENT|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G01|MECH_COHERENT|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G01|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G02|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G03|S1_BALANCED|40/45|ACCEPTED_TARGET_REACHED|1/0|False|
|G07|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G04|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G05|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G06|S1_BALANCED|40/48|ACCEPTED_TARGET_REACHED|0/0|False|
|G08|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G09|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G10|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|G11|S1_BALANCED|40/40|ACCEPTED_TARGET_REACHED|0/0|False|
|virtual_Ip|V1_SINGLE|5/5|ACCEPTED_TARGET_REACHED|0/0|None|
|virtual_Ip|V3_SPREAD|5/5|ACCEPTED_TARGET_REACHED|0/0|None|
|virtual_Ip|V3_COHERENT|5/5|ACCEPTED_TARGET_REACHED|0/0|None|
