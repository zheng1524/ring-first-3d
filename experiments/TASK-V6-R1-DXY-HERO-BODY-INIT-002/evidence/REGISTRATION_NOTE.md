# 配准使用资格复核

本轮不重新匹配、三角化或估计 T。原 27 条评价从已审计 M4 归档 SHA 验证后复用；13 条补充边调用原 evaluate_edges / pair_view / bidirectional / ring_pixels，在原 FIT/HELD、DLT、Ring 缓存上计算。原 62 视频 T 逐值不变，新 17 视频核查；共 40 条既有关系。

状态：14 PASS_FOR_JOINT、20 FAIL_REGISTRATION、6 INCONCLUSIVE_REGISTRATION。支持不足优先记 INCONCLUSIVE，同时保留高残差等失败原因，均不允许联合。P95>30 px 是提示而非单独拒绝。

路由：79 个单视频均用本地坐标；13 个全组联合，Ip4/R5 仅 005+006 联合，007 单独。合格子集使用 inv(T_anchor) @ T_v 重锚；不沿拒绝边连接。每视频的本地 CAD 采用原 Ring 规范，进入合格子集时必须随该视频相机/地标/HERO 使用相同变换；anchor CAD可作为主拟合约束，其余CAD偏差应保留。

| 重点组 | 状态 | A→B 中位 px | B→A 中位 px | 双侧 HELD DLT |
|---|---|---:|---:|---:|
| GP_IIa_22.0mm_closed_R10_single_refY | INCONCLUSIVE_REGISTRATION | 118.877 | 112.309 | 6 |
| GP_IIa_9.5mm_closed_R5_single_refY | FAIL_REGISTRATION | 43.105 | 75.797 | 13 |
| GP_Is_14.0mm_closed_R5_single_refY | FAIL_REGISTRATION | 82.562 | 27.898 | 27 |
| GP_Is_7.0mm_closed_R5_single_refY | INCONCLUSIVE_REGISTRATION | 60.566 | 125.309 | 7 |

原 metrics2 的目标帧计数来自有限且图内投影（原定义原样保留），DLT条数按完整轨迹计；负深度、越界、DLT缺失均保留在对应源域分母。HELD在本轮用于使用资格，不是独立端到端测试。PASS仅表示满足本次下游使用判据，不能替代绝对配准精度认证。

证据：REGISTRATION_QUALIFICATION.json/.csv；runs/registration/<group>/original|supplement/EDGE_EVALUATION.json；补充边完整 M0/M1/M4 HELD 记录亦保存，包含失效观测。7项规则/真实路由回归通过。命令：bash run_python.sh code/registration.py；bash run_python.sh code/test_registration.py。
