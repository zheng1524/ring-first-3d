# E3-C 复现

父提交：`a7c6233f33f9a2ec84b4ce19f668a187bd90b9c8`。只读复用E3-A/B已批准输入，不重新选择视角、不运行旧审计/融合main。三份E3-B场源码原样承载在本任务code目录，`__file__`仅让写入/缓存根落入新任务；代码、白名单和B场协议SHA逐一比对。大型HERO/XYZ/PLY/视频仍以原路径与SHA引用。

环境：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，CPU NumPy/SciPy/旧Open3D vendor。CUDA_VISIBLE_DEVICES为空；模型/权重/GT/Oracle/Dxy及非白名单几何读取由既有守卫拦截。`INHERITED_FLAG_BINDINGS.json`只读取E3-B独有格/本源可见性flag缓存，候选XYZ、法向和face仍来自真实原Mesh；绝不把缓存当新几何。

首次执行应从父提交另建隔离任务目录，顺序为：

```bash
E3C_ROOT=/home/liu/ring_first_3d_e3c/experiments/TASK-E3-C-VISIBILITY-CONSENSUS-001
E3C_PYTHON=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1
"$E3C_PYTHON" "$E3C_ROOT/code/context.py"
"$E3C_PYTHON" "$E3C_ROOT/code/sampling.py"
"$E3C_PYTHON" "$E3C_ROOT/code/run_consensus.py"
"$E3C_PYTHON" "$E3C_ROOT/code/depth_windows.py"
"$E3C_PYTHON" "$E3C_ROOT/code/check_consensus.py"
"$E3C_PYTHON" "$E3C_ROOT/code/ablation_audit.py"
"$E3C_PYTHON" "$E3C_ROOT/code/visualize_consensus.py"
"$E3C_PYTHON" "$E3C_ROOT/code/deliver.py"
```

`context.py`要求确切父提交，是首次冻结保护；已提交分支不要删除该检查后重跑初始化。缺失源或flag缓存必须报告缺口，不能用融合Mesh/新HERO替代。新机器可按同SHA重放E3-B已冻结flag计算，但不能改选择规则。

本次几何查询已完成后，逐行导出重复解压导致额外耗时，主进程在CSV导出段被INT停止。原部分gzip留在runtime，失败日志/SHA保留；修复为每对来源一次读入数组后，仅执行 `run_consensus.py --export-only`，不重复任何场查询、不改判据。候选/源间数组和两阶段统计未变。

首次窗口表的native模式可见性错用了候选位置的标志，改为查询native模式自己的位置；旧表保留runtime，所有mode来源/深度/区间位置均未改变并有检查。第二次window输出和第一版数值曲线一致。消融补充审计在观察后进行，明确不是新预注册假设；它固定原已冻结C0门控并检查纯通道增加，保留原结果，V3完全不变。图4含补充控制与N=0标识，不把缺少长条样本画成0%错误率。

主表：VISIBILITY_EVIDENCE每采样原面一行（53,615）。逐观察源完整数据为`metrics/OBSERVATION_SOURCE_EVIDENCE.csv.gz`（241,229行）；SOURCE_SUPPORT_MATRIX为76个同视频有向参考对。CSV采用8位有效数节省体积，**判据在未舍入数组上运行**，不要根据打印的临界分数重新打标签。未舍入数组留本地local_results，缺缓存可按原输入/代码/协议重算。

逐源gzip读取示例：

```python
import gzip,csv
with gzip.open("metrics/OBSERVATION_SOURCE_EVIDENCE.csv.gz","rt") as f:
    for row in csv.DictReader(f):
        if row["candidate_id"] == "G01_004_ref03:251":
            print(row)
```

主表分类是采样面重心证据，灰色/未采样面不是失败或不存在。原始各源Mesh一直保留；本轮不保存新融合Mesh、单一深度预测或全局场。17项语义/守恒检查和交付检查不等于真实错误检测科学目标通过。完整负面结论见TECHNICAL_REPORT与FAILURE_LEDGER。
