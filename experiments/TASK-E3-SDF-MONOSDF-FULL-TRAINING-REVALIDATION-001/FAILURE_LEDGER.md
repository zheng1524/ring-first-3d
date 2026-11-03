# 失败、未完成项及风险记录

本表不改变历史 FAIL，不以短测试结果判定 MonoSDF 路线失败。

|ID|状态/影响|原因与处理|证据|
|---|---|---|---|
|R01|单参考暂停已解除；三 CORE 待审|四模型原预算800k，实测推算68.58h、安排80–110h；用户选择先 ref08 M0/M1，各200k，未缩减模型训练量。不是 NaN/OOM 或算法失败|[资源报告](RESOURCE_ESTIMATE.md)、[决定](provenance/RESOURCE_DECISION.json)|
|E01|初次单参考 M0 import 失败，更新0|新创建 runtime 目录前已加入 sys.path，import finder 缓存导致找不到 utils；创建包后 invalidate_caches，恢复同种子/同参数运行|本地 runtime/benchmark_single_M0.log；成功日志 benchmark_single_M0_import_fixed.log|
|E02|早期命令包装失败，无计算结果|猜测 E0 目录名称错误、日志目标 runtime 尚不存在；改用实际 E0-COMPARE 路径、先建本任务目录。无输入覆盖/参数搜索|common.py 当前路径；runtime/prepare.log|
|E03|准备脚本首次执行前拼写修复|common.py 早期 else0 解析错误，在正式准备前改正；不算模型失败|当前源码及预注册冻结|
|C01|资源后明确原生锚点可见性防护|crop 量化射线与原始 Pixel ID 射线不是完全同一射线；锚点改为原生 XYZ 并单独核查原生 Mask/ROI/CAD，防止使用 Ring 后点。前四资源运行源码 SHA 保留，不重写为最新版本|[原生核查](metrics/NATIVE_ANCHOR_AND_COORDINATE_VALIDATION.csv)、BEFORE_BENCHMARK_*、POST_NATIVE_GUARD_GPU_VALIDATION.json|
|P01|正式训练进行中，充分训练尚未完成|资源暂停后已补齐官方 runner IO 适配、可恢复状态、原生固定分母评价及官方提取；初始化实际提取通过，正式完成状态以每臂 STATUS 为准。不得把100次资源更新或初始化当充分训练成果|[正式冻结](provenance/BEFORE_FORMAL_TRAINING.json)、运行状态 JSON|
|H01|历史 E2.7 两臂首步收缩（保留）|G01_005、固定有限采样、每臂一次 Adam；负区体积约缩小66%、零面约1mm漂移。不是本轮 G01_004 长程失败，也不是路线被否定|[E2.7 报告](../TASK-NEURAL-E2P7-BOUNDED-LEARNING-PILOT-001/TECHNICAL_REPORT.md)|
|H02|三 CORE 相机证据有限|当前统一 Camera Gate 都是 INSUFFICIENT_EVIDENCE；条件性研究入组不等于真实位姿认证，跨源矛盾归因仍不唯一|[来源表](metrics/FIXED_NATIVE_DENOMINATORS.csv)、当前 N0 Camera Gate|
|H03|HERO 参考间存在冲突|SSI 可吸收尺度/偏移，首次 gate 存在覆盖选择风险；M1 保护可能相互冲突，不能预先声称解决|E2.5、E3-C/N0历史报告；本轮冻结权重|
|H04|可靠法向不是独立真值|由同源 HERO 四邻导数估计，排除跳变和无效点；仍继承原深度误差|[法向审计](metrics/INPUT_AND_NORMAL_AUDIT.csv)|
|H05|长期硬件资源未证实|短测试峰值能容纳，不保证后期自适应查询、提取临时场或热负载；实际 OOM/数值故障须保留中断点，不称充分训练失败|[资源估算](metrics/RESOURCE_DECISION_GATE.json)|
|E04|独立CPU回放首个命令缺依赖路径|单独stdin脚本未加入既有E0 runtime/python，因此skimage导入失败；正式训练已有正确路径，未受影响。回放脚本补该只读路径，不安装/修改环境、不追加训练更新|provenance/RUNTIME_ACCEPTANCE_AUDIT.py|

没有 GT 读取、历史预测回退、相机/HERO/CAD 修改、新 HERO 推理或 DXY 修改。没有删除困难参考。长程科学问题在200k完成并审阅前保留 NOT_EVALUABLE；原始暂停回执和历史失败均保留。
