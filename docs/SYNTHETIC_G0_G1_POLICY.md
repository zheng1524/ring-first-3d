# G0–G1 科学阶段的增量政策

在 fc63df35 的 Research Policy Runner 上增加 schema 2，本次只授权 TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001。schema 1 的字段、阶段、GT 拒绝策略与原 35 个回归保持不变。新的角色/阶段由注册代码决定，TASK.yaml 不接受任意 handler 或角色覆盖。

真实资产包括 G01 原始 Blender、原导出与来源身份、Ring CAD、原冻结相机；缺任一真实来源为 NOT_EVALUABLE，SHA/单位错误拒绝。Blender 的 evaluated-world 数学块采用原源码 AST，禁用 Blender 自动脚本；仅写本任务新目录。

三方隔离：generator 导出真实 GT，生成 C0/C1/C3 合成观测和受控初始 Body；predictor 只读公开 Body、CAD、受扰深度/受扰相机，不得读取 GT、真相机缓存或已有评价；evaluator 在对应预测全部 SHA 冻结后才读取私有 GT/真相机计算误差和 Oracle。Oracle 不进入实用预测。代码路径哈希、输入身份、FIT/HOLDOUT 与参数在每阶段前后核验。

必须先通过原 35 项及新增回归，再运行最小 C0 科学 Smoke，随后完整 C0、代表 C1、C3。C1 固定轴向 Z+1 mm，保持原生像素射线；它不是等长射线距离偏移，也不是所有点沿同一个世界向量平移。C3 是相机右局部 Ry=2°、tx=0.5 mm。真正误差由独立 evaluator 复算，不信任注入声明字段。

源相机 640×360 经精确半像素传输得到 320×180 工作图，PyTorch3D 的 raster center 单独补 +0.5。Body/Ring/相机平移为毫米，GT 单位来自原 Blender METRIC scale_length=1 m，×1000，不使用文件名直径定标。GT 的真实部署位姿未认证，本实验 canonical_from_blender=I，是明确的合成场景，不做 GT→历史 Body 对齐。

所有未命中维持 NaN 和全像素分母，Face ID=-1；有限数值输出不等于对应正确。共享三角边界的栅格缺口不能被排除出分母，观测分母来自独立全图射线。C0 检查有限对应误差 <0.001 mm 和最低实际样本数，仍单列未匹配；C1/C3 按固定算法原样报告，不因 GT 结果调整参数。评价含覆盖、误差中位数/MAE/p95/max、相对真深度误差与共同成功点配对。

G1 输出实际数据驱动的九张精选图、完整 Face/重心/XYZ 点位审计、全组/逐帧指标及本地离线 index.html。色标固定 0–2+ mm，超过范围的实际最大误差保留在数值表，未匹配用洋红色显示。图像只是对应关系诊断，不证明错误已经修正；本轮 Body 更新为 0。

在仓库根目录，使用本任务 TASK.yaml：

```bash
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py run --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml --run-dir /absolute/project/experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/runs/new-name --stage all
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml --run-dir /absolute/project/experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/runs/new-name
```

工程产物验收后科学状态仍为 AWAITING_HUMAN_REVIEW。不执行 G2、Body 更新、HERO 训练或跨视频 BA；扩大扰动矩阵需要后续人工批准。
