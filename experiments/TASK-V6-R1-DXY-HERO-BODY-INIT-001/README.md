# R1 DXY/HERO 粗主体初始化

正式范围与限制见 `EXECUTION_PLAN.md` 和完成后的 `TECHNICAL_REPORT.md`。任务只读 R1/M4/Clean，输出位于本任务 `runs/`。真实部署 GT 不可评价。

```bash
cd /home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-BODY-INIT-001/experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-001
bash run_python.sh code/test_contracts.py
bash run_python.sh code/supplement.py       # 补审零 HERO 视频；冻结 M4；旧 T 不变
bash run_python.sh code/control.py          # 既有虚拟 G01，含错误基底
python3 code/batch.py                       # 全 39 组，最多两个 CPU；缓存带身份验证
bash run_python.sh code/visualize.py
bash run_python.sh code/visibility.py
bash run_python.sh code/control_figure.py
bash run_python.sh code/verify.py
bash run_python.sh code/report.py
```

单组重跑：`bash run_python.sh code/pipeline.py --group GP_IIa_14.0mm_closed_R5_single_refY`。不得根据图像效果逐病例改参数。更改科学代码、配置或输入会使相应缓存失效。

在至少 4 个空闲 CPU 和 2 GiB 额外内存可用时，可同时运行 `python3 code/extra_batch.py`，增加两个低优先级 CPU 处理尚未启动的组；逐组 OS 锁防止重叠写入。默认复现无需此加速器。

本地审阅：`runs/results/index.html`。每组的 `index.html` 并列单视频和联合，失败保留在 `GROUP_RESULT.json`；每配置有 `RESULT.json`、`BASE.json`、`STAGES.json`、`EVALUATION.json`、`PARENT.npz`、`FINAL_UNCUT.npz`、`BODY.npz`。

`BODY.npz` 的 `F` 只含保留的母体三角面（模型推断，并非实测 HERO）；`F_solid` 另加闭合底盖，`inferred_base_faces` 明确标记。`VISIBILITY.npz` 另存实际拟合相机、完整图像网格下的模型可见面及 Mask 相容面，它们也不等于已测真值。弱基底的 `WEAK_BASE_CANDIDATE.npz` 仅是可逆候选，正式 BODY 保留完整母体。无背景证据时不造基底。

消费接口：`code/consume_body.py::load_configuration` 校验结果与来源；`corrected_source` 返回保持原面 ID 的可信曲面工作副本。使用 `D-b` 沿原 Target 射线校正；背景和 CAD 不动。不要把返回的完整顶点数组中的未选顶点当成可信点云。相机与尺度保持 M4 冻结值。

必要大输入仍依赖原 R1 与 M4 路径；`evidence/FULL_INPUT_INDEX.json`、归档中的 `runs/inputs/*/AUDIT.json` 和 `runs/observations/*/*/INDEX.json` 记录准确路径、哈希、帧、原始面和像素身份。禁止清理这些输入来复现实验。`evidence/SOURCE_LOCK.json` 记录真实源码提交与哈希；历史函数经 AST 原样加载，避免历史主程序副作用。

二维留出只表示没有进入本轮主体二维目标；相机/M4、HERO 模型的原 Target/Support 可能含同帧，因此不能称端到端盲测。偏置默认保守先验，不能解读为已准确恢复真实 HERO 深度误差。
