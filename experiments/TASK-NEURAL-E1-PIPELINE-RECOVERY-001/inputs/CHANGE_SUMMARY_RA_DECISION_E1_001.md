# CHANGE_SUMMARY_RA_DECISION_E1_001

**版本差异**：E1 PM审核包v1 → v2（2026-10-30）  
**正式裁决**：`APPROVE WITH CHANGES — C0+C1 ONLY`。来源：共享资料库 `/Research_Collab/RingFirst3D/RA_DECISION_E1_001.md`。  
**执行身份**：修订文件供用户审核、转交新Codex；未获得C2–C4或任何GPU许可。旧E0全量原始报告/失败不得覆盖。

## D1 — MonoSDF 首选不变，纠正“只查相机是否在球内”

- **计划**：冻结MonoSDF为首选底座，不静默换NeuS2；后续首个科学MVP由每视频≥3份有区别的合格参考共同优化**一个**SDF，真实RGB/Mask、多个HERO axial-Z和Eikonal进入可微图，固定CAD硬门禁；S0无HERO/S1恒权/S2来源与冲突权重，权重可复算不全零，MASt3R/CAD可微损失若未实现不得假称。
- **C1首任务**：官方真实采样/absorbing sphere规则+source相机ray/ROI/near-far/zero-crossing，负例旧E0配置`EXPECTED_FAIL_E0`，至多两种物理有理据的修复方案；不训练、不增加步数。
- **协议**：增加前景/背景有效采样分母、Ray-Z、SDF符号与analytic zero-crossing，后续逐源真实loss/梯度/支持域检查。

## D2 — 第一阶段Ring-First相机完全冻结

- 所有K、c2w、Ring CAD固定且相机**不参与优化器**；G01_004/005两独立局部系不可自动合并；三照片未认证不可制造公制样本。
- Map官方输出pose属于预测，必须与输入pose比较，**不可覆盖正式相机**；允许预声明纯刚体gauge仅作表达转换，不允许Ring/GT后验ICP、尺度拟合或相机优化获取PASS。
- C0/C1在源文件和适配器中增加K/T不变量断言，Map旧M3 CAD失败与pose残差须显式保留。

## D3 — MapAnything仍是独立竞争臂，允许充分利用局部几何

- 原生M0–M3完整保留，但**不再作为Map唯一研究范围**。正式设计增设`M-geometry-conditioned`：HERO、Raw、Cleaned、F1/F2/F3真实XYZ/已有开放三角面及有来源的邻接几何，按冻结来源K/T投影为合法`depth_z`及valid/source provenance；CAD独立作遮挡和公制评价。
- 接口必须核对**锁定官方rev**真实字段、稀疏无效值/NaN/0的处理、K resize、z-buffer与遮挡；官方没有任意PLY/GLB/confidence输入保证，不能修改内部网络或把字典未消费字段当生效。
- M4/M5暂是候选名称（非授权运行）；**同一RGB的F1/F2/F3派生先验不是额外独立观察**，若多深度不能同时合法输入则做互斥配置。所有来源DAG、共视冲突、父系相关性要在比较表揭示。
- 双路线竞争用**共同信息集比较**和**各臂最佳合法信息集比较**两张表；Map使用更多可追溯先验可以比较，但必须将信息优势与方法优势分开。

## 具体文件修订点

| 文件 | 本次主要改动 |
|---|---|
| `PM_PHASE_E_CORRECTION_PLAN.md` | 新的数据图、D2冻结相机、详细Map全几何条件、同等/最佳合法信息双表、C0+C1独立授权界限 |
| `TASK-NEURAL-E1-PIPELINE-RECOVERY-001.md` | C1.2官方采样/吸收域真ray测试；C1.3新Raw/Cleaned/F1/F2/F3→source-view axial Z+valid+provenance、官方接口门禁；四图；无GPU/不自动C2 |
| `E1_EXPERIMENT_PREREGISTRATION.md` | SDF≥3源共同优化S0/S1/S2、实际可微约束及CAD硬门禁；Map M-native+M-geometry-conditioned完整消融、严格独立性与双表 |
| `E1_ACCEPTANCE_PROTOCOL.md` | 增补Map投影/遮挡/合法条件硬门禁与相机不变断言；MonoSDF旧域负例；后续逐源梯度与公平评价；通过≠科研成功 |

## PM给RA/研究者的最终状态

- E0：`REPORTED / SCIENCE_INCONCLUSIVE`，失败不可覆盖。
- E1-C0+C1：`REVISED_PER_RA / READY_FOR_RESEARCHER_TRANSFER`，仅无训练CPU来源/几何/模型输入合同。
- E1-C2+C3+C4：`PROPOSED / NOT_AUTHORIZED`，用户需另批GPU/可微测试/模型推理。
- MonoSDF与MapAnything：两独立科学候选，**无赢家、均未被拒绝**。

**建议新Codex收到的唯一执行文件**：`TASK-NEURAL-E1-PIPELINE-RECOVERY-001.md`（同时只读参照此包其他三份文件）；若研究者尚未明确批准，则不得开始。新任务完成后须提交真实数据分母、源码SHA、3–4张固定风格图、单份TECHNICAL_REPORT和明确失败分类，由PM/RA验收。
