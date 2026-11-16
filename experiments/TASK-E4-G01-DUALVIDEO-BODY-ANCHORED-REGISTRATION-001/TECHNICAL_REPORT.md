# TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001

状态：**STOPPED_AT_G0 / NOT_ACCEPTED**。本次没有完成主体初始化、对应映射或多表面配准。

冻结后经现有 Policy Runner 执行，Preflight、Contracts、65 项回归通过；真实 G01 场景门禁失败后停止。没有修改科学算法，没有注入误差，也没有执行 G1–G4。

实现提交：`8bd150ab7870db42c11942d385242910e2daff00`。运行冻结指纹：`b8a88ced6363c6558f68cbc0ffdd243323ba37a22a7dbb10b277076476ed2132`。
TASK SHA256：`f1d5998fbc6e38b1c385c0f13679d7c73467284e6c37bd85159412351ea44a05`。来源清单 SHA256：`1ad55dd2823ce5f316e5594841e092cd89ba4fb955b4c00ac787a0d2ad12fd33`。

[可视化首页](visualization/index.html) · [真实独立坐标系完整网格/相机](visualization/scene.html) · [RESULT_CARD](RESULT_CARD.md) · [运行及交付清单](RUN_MANIFEST.json) · [逐帧指标](FRAME_AUDIT.csv) · [全部指标](metrics.json) · [候选 Failure Registry](FAILURE_REGISTRY.json)

## 实测结果与停止原因

| 视频 | 冻结帧数 | FIT通过 | HOLDOUT通过 | Support@2px中位数 | 边界p95的跨帧中位数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 004 | 22 | 0/17 | 0/5 | 0.978243 | 5.830952 px |
| 005 | 11 | 4/8 | 0/3 | 0.979277 | 3.162278 px |

全部 33 帧的 RGB、类别 Mask、Ring 和原生 Camera-to-Ring 来源文件及矩阵绑定通过校验；004/005使用各自来源，未复制轨迹。这只是冻结的33帧审计子集，不是两段视频所有原始帧的认证。来源相机属于既有Ring-First/静态背景重建的原生候选，不能宣称为原始Blender真值轨迹。两个视频保持独立Ring坐标系，CAD相同并不认证共同世界坐标。

`RING_PROJECTION_GATE`：预先冻结观察Ring像素≥20、2px支撑率≥0.95、观察边界到完整CAD边界p95≤3px；29/33帧未同时满足。该结果证明门限未通过，**不能仅凭此认定相机位姿错误**。真实遮挡切边、Mask离散误差也可能影响边界p95；本轮没有据结果调参、替换相机或重新拟合。所有未匹配区域保留在图中，完整CAD IoU仅作诊断。

`BODY_RING_POSE_UNCERTIFIED`：原始Blender仅包含“球体”Mesh，1857顶点/3710三角面，没有Ring、相机和自定义部署凭据。按历史导出器的双精度运算，新导出的真实G01形状与注册缓存逐面、逐顶点匹配；但没有可追溯的固定Body-to-Ring变换，也没有004/005共同世界认证。因此真实形状可信，部署位姿仍为NOT_EVALUABLE。不能使用作者矩阵、历史Oracle刚体拟合或上一轮GT克隆控制Body来补齐该变换。

[Blender场景原始清单](visualization/BLENDER_SCENE_INVENTORY.json) · [固定部署凭据核验](visualization/BODY_RING_POSE_CERTIFICATE_AUDIT.json) · [失败逐项及关联图](visualization/G0_SCENE_METRICS.json)

## 冻结条件与未执行范围

| 条件 | 目标视频 | 误差类型 | Ry / tx | 实测状态 |
| --- | --- | --- | --- | --- |
| S0 | 无 | 无扰动 | 0° / 0mm | NOT_RUN |
| S1 | 004整段 | 共同坐标系 | 2° / 0.5mm | NOT_RUN |
| S2 | 004整段 | 共同坐标系 | 3° / 0.3mm | NOT_RUN |
| S3 | 004 | Camera-to-Ring局部 | 2° / 0.5mm | NOT_RUN |
| S4 | 005 | Camera-to-Ring局部 | 3° / 0.3mm | NOT_RUN |

共同坐标系条件要求同一左乘SE(3)同时作用于相机、Ring和完整局部Mesh，保持段内相对机位与Camera-to-Ring不变。局部条件单独定义为Ring局部共享左乘，Ring固定；两类不混合。以上为冻结计划，未实际注入或验证其数值。当前只注册了DV01场景门禁；G1–G4算法Handler没有伪装成已实现或已验证。

正式DXY E1/完整Mask E2、九参数Body、二维→三维候选区域映射、完整局部Mesh配准均未运行。未生成粗Body、未替换观测点、未优化Body、未增加逐帧自由度。无GT选参；GT只由G0真实性审计角色读取。没有预测冻结后的评价结果，也没有Oracle成功指标。

| 方法/指标 | 不修正 | Robust ICP | 二维主体锚定联合优化 |
| --- | --- | --- | --- |
| 执行状态 | NOT_RUN | NOT_RUN | NOT_RUN |
| 相对位姿误差/GT曲面误差/覆盖率/HOLDOUT表现 | NaN | NaN | NaN |

## 执行与工程验证

回归共 **65项通过，0失败/0错误**：原有35项、既有合成对应15项、本轮新增15项。新增拒绝案例包括错误毫米单位、来源SHA、跳过G0、GT Body替代、GT越权读取、投影缺失和可视化缺失。独立Contracts阶段仍运行既有契约套件；原有阶段A行为保留。

G0实际逐帧渲染复用T24/PyTorch3D相机约定，无新科学算法。最终运行耗时30.131s；预算1800s、单阶段300s、产物300MB。失败门禁没有被绕过，Runner的artifacts阶段未越过失败G0；交付整理仅复制和核验已生成的证据，不将任务标为验收成功。

四次工程运行完整保留在本地runs，摘要和原始文本在[evidence](evidence/G0_AUTHENTICITY_004/RUN_MANIFEST.json)。首次受限回归暴露公开SHA检查顺序问题；第二次G0适配器未识别MAST3R的pose键；第三次新适配器使用float32世界变换导致2.327114057×10⁻⁷mm差异。相应修复仅为格式与历史双精度导出一致性，未放宽容差。初始YAML别名问题保留[原始冻结](initial_freeze/TASK.yaml)及修订收据。工程错误和场景不可评价分别记录，所有新Failure Memory项均为候选，未经人工审查不得晋升永久规则。

离线交付保留全部33张真实原图/CAD投影图、橙色未匹配观察区域、固定毫米尺度三维场景和来源ID/SHA。004、005、Blender作者坐标系分别展示。交付场景只将视口从12改为8px/mm，使相机在默认视图完整可见；原始Runner场景、输入、网格、相机与数值指标保持不变。交付HTML已用本地Chrome执行检查，无CDN或联网依赖。没有提供虚构的配准前后、二维Body对应或误差修正图。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | G01：1；两视频；33帧（25 FIT / 8 HOLDOUT） |
| 本算法独立成功 | Body初始化/完整多表面配准0/1；只有4/33帧满足G0投影门限 |
| 本算法失败 | G01不可评价；G1–G4未运行，预测和误差NaN |
| 历史测量值回退 | 0 |
| 失败组及具体原因 | G01固定部署凭据缺失；29帧未满足冻结投影门限，逐帧见下表 |
| 最终统计样本 | 配准独立成功0/1；MAE、中位绝对相对误差、p95、最大误差和配对比较N/A |
| 是否使用 GT 选择算法 | 否；TASK/来源/源码在核验前冻结，GT只用于G0来源核验 |

## 逐帧审计与失败可视化

| Source ID | Split | Gate | Support@2px | Boundary p95 px | 实际原图/CAD证据 |
| --- | --- | --- | ---: | ---: | --- |
| MAX__G01_v004_raw00049 | FIT | FAIL | 0.979113 | 6.000000 | [图](visualization/figures/G01_v004_raw00049.png) |
| MAX__G01_v004_raw00158 | FIT | FAIL | 0.939557 | 8.056032 | [图](visualization/figures/G01_v004_raw00158.png) |
| MAX__G01_v004_raw00282 | FIT | FAIL | 0.952011 | 8.485281 | [图](visualization/figures/G01_v004_raw00282.png) |
| MAX__G01_v004_raw00341 | FIT | FAIL | 0.978364 | 7.000000 | [图](visualization/figures/G01_v004_raw00341.png) |
| MAX__G01_v004_raw00499 | FIT | FAIL | 0.986834 | 5.830952 | [图](visualization/figures/G01_v004_raw00499.png) |
| MAX__G01_v004_raw00657 | FIT | FAIL | 0.980801 | 4.242641 | [图](visualization/figures/G01_v004_raw00657.png) |
| MAX__G01_v004_raw00813 | FIT | FAIL | 0.979927 | 5.000000 | [图](visualization/figures/G01_v004_raw00813.png) |
| MAX__G01_v004_raw01093 | FIT | FAIL | 0.974699 | 4.242641 | [图](visualization/figures/G01_v004_raw01093.png) |
| MAX__G01_v004_raw01264 | FIT | FAIL | 0.970773 | 5.000000 | [图](visualization/figures/G01_v004_raw01264.png) |
| MAX__G01_v005_raw00104 | FIT | FAIL | 0.978089 | 3.605551 | [图](visualization/figures/G01_v005_raw00104.png) |
| MAX__G01_v005_raw00185 | FIT | PASS | 0.976042 | 3.000000 | [图](visualization/figures/G01_v005_raw00185.png) |
| MAX__G01_v005_raw00439 | FIT | PASS | 0.983948 | 2.828427 | [图](visualization/figures/G01_v005_raw00439.png) |
| MAX__G01_v005_raw00562 | FIT | PASS | 0.990122 | 2.828427 | [图](visualization/figures/G01_v005_raw00562.png) |
| MAX__G01_v005_raw00694 | FIT | FAIL | 0.975116 | 3.162278 | [图](visualization/figures/G01_v005_raw00694.png) |
| MAX__G01_video005_v005_00000 | FIT | FAIL | 0.967264 | 5.956857 | [图](visualization/figures/G01_video005_v005_00000.png) |
| MAX__G01_video005_v005_00326 | FIT | PASS | 0.993989 | 2.236068 | [图](visualization/figures/G01_video005_v005_00326.png) |
| MAX__G01_video005_v005_00860 | FIT | FAIL | 0.977533 | 3.162278 | [图](visualization/figures/G01_video005_v005_00860.png) |
| OLD018__G01_004_new_r00 | FIT | FAIL | 0.967468 | 6.324555 | [图](visualization/figures/G01_004_new_r00.png) |
| OLD018__G01_004_ref03 | FIT | FAIL | 0.985340 | 6.000000 | [图](visualization/figures/G01_004_ref03.png) |
| OLD018__G01_004_ref08 | FIT | FAIL | 0.971649 | 5.000000 | [图](visualization/figures/G01_004_ref08.png) |
| OLD018__G01_004_ref13 | FIT | FAIL | 0.980415 | 4.000000 | [图](visualization/figures/G01_004_ref13.png) |
| OLD018__G01_v004_raw00152 | FIT | FAIL | 0.941304 | 7.615773 | [图](visualization/figures/G01_v004_raw00152.png) |
| OLD018__G01_v004_raw00412 | FIT | FAIL | 0.979302 | 6.000000 | [图](visualization/figures/G01_v004_raw00412.png) |
| OLD018__G01_v004_raw00852 | FIT | FAIL | 0.978121 | 5.000000 | [图](visualization/figures/G01_v004_raw00852.png) |
| OLD018__G01_video004_004_15 | FIT | FAIL | 0.957573 | 5.000000 | [图](visualization/figures/G01_video004_004_15.png) |
| HELD__G01_004_growth_r04 | HOLDOUT | FAIL | 0.983009 | 6.000000 | [图](visualization/figures/G01_004_growth_r04.png) |
| HELD__G01_004_growth_r06 | HOLDOUT | FAIL | 0.978558 | 4.123106 | [图](visualization/figures/G01_004_growth_r06.png) |
| HELD__G01_004_growth_r10 | HOLDOUT | FAIL | 0.981579 | 5.000000 | [图](visualization/figures/G01_004_growth_r10.png) |
| HELD__G01_video004_004_09 | HOLDOUT | FAIL | 0.959818 | 5.830952 | [图](visualization/figures/G01_video004_004_09.png) |
| HELD__G01_v004_raw00334 | HOLDOUT | FAIL | 0.960176 | 7.615773 | [图](visualization/figures/G01_v004_raw00334.png) |
| HELD__G01_005_new_r04 | HOLDOUT | FAIL | 0.987578 | 3.154164 | [图](visualization/figures/G01_005_new_r04.png) |
| HELD__G01_v005_raw00509 | HOLDOUT | FAIL | 0.980633 | 4.000000 | [图](visualization/figures/G01_v005_raw00509.png) |
| HELD__G01_v005_raw00668 | HOLDOUT | FAIL | 0.979277 | 4.000000 | [图](visualization/figures/G01_v005_raw00668.png) |

下一步必须先补充真实源场景中Body-to-Ring固定部署变换及两视频轨迹凭据，并独立诊断原生Ring投影差异；由人工审阅决定是否修订协议、新建冻结任务。当前停止，不扩展扰动矩阵或开始Body优化。
