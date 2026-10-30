# Phase E Failure Ledger（初始审计状态）

状态 `PROPOSED`。既有历史失败不是 E0 模型失败；P0/P1 之后应按行追加原始证据，保留旧行。

|ID|来源|分类|证据|E0 处理|
|---|---|---|---|---|
|H-01|边界生长 G01_004|`ALGORITHM_NOT_PROVEN`（旧 F3）|S0→Joint 同像素 RGB MAE 22.813→24.155；CAD 旧点穿插额外19|保留为 SDF/Map 必须击败的反例；不提前宣布新方法能解决|
|H-02|边界生长 G01_005|`ALGORITHM_NOT_PROVEN`（旧 F3）|00860 同像素 19.634→22.809；00611 8.842→10.941；CAD 旧点穿插额外21|两个独立目标不能选择性只呈现一个|
|H-03|分区 MASt3R G01 跨视频|`REGISTRATION_UNVERIFIED`|双向轴向冲突 65.90%/70.40%；跨视频 GLB 仅候选|004/005 不联合、不将 H 作 GT|
|H-04|分区 MASt3R|`HOLDOUT_LEAKAGE_RISK`|004 两个旧HERO/P0源帧曾在HOLDOUT；G08无预冻结独立留出|P0 必须做 RGB/HERO 多图输入 SHA 级资格表|
|H-05|边界生长 video005|`RUNTIME_BLOCKED`|2/24 新 HERO 尝试失败；`cur_image.to(device)` unspecified launch failure；新进程 CUDA 检查失败|P0 只读硬件复查；不得算几何拒绝或用 CPU 极慢运行掩盖|
|H-06|G07 Is/R5|`DATA_INELIGIBLE_FOR_NORMAL_SUCCESS`|冻结相机 `UNQUALIFIED_CAMERA_STRESS`，旧 Ring 穿插 287 点|压力结论独立；不换组隐藏失败|
|H-07|G01 photo001–003|`DATA_INELIGIBLE_FOR_METRIC_RECON`|K490/pose 未认证，无可信照片 HERO 深度|只作图像候选，不补造公制 XYZ|
|H-08|四组形状 GT|`ABSOLUTE_3D_NOT_EVALUABLE`|部署世界变换/组织切面未独立认证|GT 密封，只后验非 Oracle 指标可用|
|E0-S|Arm S|`NOT_RUN`|仅官方可行性研究|静态可行并非 smoke 成功|
|E0-M|Arm M|`NOT_RUN`|仅官方接口研究|静态可行并非模型输出成功|

新增失败行最少包含 `time, task, group, video, source_shas, arm, config_sha, code_commit, attempted_stage, type, raw_error_or_metric, physical_denominator, disposition, next_approval_required`。严禁只留下成功样本。
