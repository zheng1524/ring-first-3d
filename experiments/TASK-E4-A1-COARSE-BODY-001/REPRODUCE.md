# 复现与本地结果

独立分支 `exp/TASK-E4-A1-COARSE-BODY-001`。原始源资产不可公开复制，路径与SHA见provenance/INPUT_MANIFEST.json。只在本任务/新复现工作树写派生结果，不在原始科研资产或其他工作树运行清理命令。

本机环境：Python3虚拟环境 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`，具体版本见provenance/ENVIRONMENT.json；Open3D复用既有vendor，不下载模型。CPU-only，common.py禁止神经运行时、网络、GT/权重及任务外写操作。对另一台机器需显式映射common.py中的原始资产根，并核验相同SHA，不能悄悄替换输入。

```bash
cd /home/liu/ring_first_3d_e4_a1
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
TASK_ROOT=experiments/TASK-E4-A1-COARSE-BODY-001
"$PY" -B "$TASK_ROOT/code/replay_inputs.py"
"$PY" -B "$TASK_ROOT/code/synthetic.py"
"$PY" -B "$TASK_ROOT/code/run.py" fit
"$PY" -B "$TASK_ROOT/code/run.py" jacobian
"$PY" -B "$TASK_ROOT/code/run.py" stability
"$PY" -B "$TASK_ROOT/code/audit.py"
"$PY" -B "$TASK_ROOT/code/visualize.py"
"$PY" -B "$TASK_ROOT/code/summarize.py"
"$PY" -B "$TASK_ROOT/code/validate.py"
"$PY" -B "$TASK_ROOT/code/refinement_diagnostic.py"
"$PY" -B "$TASK_ROOT/code/write_report.py"
"$PY" -B "$TASK_ROOT/code/finalize.py"
```

已有结果时run.py逐模型/初值恢复并跳过完成项。全新复现工作树缺少忽略的输入缓存时，先用 `replay_inputs.py --rebuild`；它只替换prepare.py的首次注册存在性断言，并将协议写入改成内容比较，科学数据准备语句不变、冻结代码SHA先核验，UTC外任何配置差异均拒绝。不要在已有人工结果目录删除模型来强制重跑；需要完全重跑时建独立复现工作树和目录，复制相同预注册与必要来源映射后执行。

本地目录：

- inputs/：13份固定原生射线、Mask、H点身份缓存；不上传。
- local_results/：20份实际参数三角Mesh、B像素首深度/Mask、S1控制几何。
- local_results/review/index.html：离线六视角审阅页，4份分离节点GLB和六视角PNG。
- metrics/S2_ALL_STARTS.json：60初值全部参数/优化状态/固定B指标；S2_PRIMARY为仅A目标选出的20主解。
- metrics/S4_PERTURBATIONS.json：40个原样扰动解；S4_JACOBIANS为白化观测谱。
- metrics/VISUALIZATION_INDEX.json、A2_BODY_INTERFACE_UNVALIDATED.json：本地Mesh/GLB/图路径和SHA。

PLY用导出float32保存，参数JSON为float64；validate.py比对实际参数Mesh与导出顶点/三角形，容差2e-6mm。无平滑、补面、额外删除或B RGB重上色。

失败NaN和原始元数据修正前副本均保留；来源完整性验证PASS不代表根完备性或G1通过。metrics/FINAL_ACCEPTANCE.json为最终门禁，保留S1通过与真实星凸根合同失败的区别。A2_PREPARATORY_DESIGN_ONLY.md只是下轮建议，不提供自动执行入口。
