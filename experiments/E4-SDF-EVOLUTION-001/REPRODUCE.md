# 复现与恢复

正式求解为CPU，未启动GPU。原始资产只读，所有写入限本任务目录；不改历史工作树。

## 已完成的结果

工作树：`/home/liu/ring_first_3d_e4_sdf_evolution`，分支 `exp/E4-SDF-EVOLUTION-001`。

```bash
cd /home/liu/ring_first_3d_e4_sdf_evolution
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
EXP=experiments/E4-SDF-EVOLUTION-001
```

环境：Python3.12.13、NumPy1.26.4、SciPy1.15.3、Open3D0.19.0、trimesh5.1.1、python-fcl0.7.0.11；Blender5.0.1 a3db93c5b259。scikit-image0.25.2、lazy-loader0.4、imageio2.37.0、tifffile2025.5.10安装于任务runtime/packages，不修改公共环境。FCL只读复用R1/runtime/packages，Open3D复用历史vendor。依赖实际版本见metrics/ENVIRONMENT.json。

初始、每轮、中间和最终：`local_results/*/FIELD.npz`，包括φ(mm)、origin(mm)、shape、h(mm)、真实提取V/F；`BODY_mm.ply`和`BODY_m.glb`。大数组没有上传，完整绝对路径、SHA和字节见assets_index/LOCAL_RESULTS.json。迁移应保留输入和源码SHA。初版完整诊断在runtime/attempt0，见独立索引；不可将其误当最终版本。

只重新生成表格/图/报告，不优化：

```bash
"$PY" -B "$EXP/code/analyze.py"
"$PY" -B "$EXP/code/diagnose.py"
"$PY" -B "$EXP/code/figures.py"
"$PY" -B "$EXP/code/report.py"
```

## 从头复现（在新副本执行，保留当前结果）

脚本R根据__file__定位本任务根目录；在同仓库独立实验副本中复制本任务小代码/配置，再创建runtime/packages及上述依赖。上游引用仍为本地只读绝对路径，迁移时依据FROZEN_INPUTS逐一匹配SHA，不按相似文件名替换。

1. `prepare.py`读取R1保守P0，生成相同67³初始场和输入回执；固定fit/validation，不能根据输出修改角色。
2. `preflight.py`全部通过后才准正式求解。实际三线性场梯度与相机Jacobian均须通过有限差分，控制实验明确标注，不作为项目预测。
3. 优化前保存`metrics/IMPLEMENTATION_FREEZE.json`，包含精确git commit、以下正式源码及配置/协议的路径、SHA、字节：inputs.py、field.py、data.py、solver.py、run.py、preflight.py、collision.py、mesh_checks.py、blender_check.py、prepare.py、LOCKED_PROTOCOL.json、01_PROTOCOL.md、IMPLEMENTATION_CORRECTION.md。格式可参照已保存回执；仅替换新副本绝对路径，所有算法与输入SHA应匹配正式版本。
4. `"$PY" -B "$EXP/code/run.py"`。脚本拒绝在已有RUN_START上再次优化，防止覆盖。不要删除现有开始标记绕过保护；新副本才可从头运行。
5. 按上述只读后处理顺序输出指标/图/报告。四核心PNG由实际SDF提取Mesh和原RGB渲染，无平滑后处理。

完整正式代码为修正版`3a5e8bd`；首版`6b4db1a`仅诊断。修正版全部数值参数与首版相同，区别只有IMPLEMENTATION_CORRECTION中记录的合同修复，不是两个消融臂，不按外观择优。

## 限制

UNKNOWN为冻结Ring Mask/CAD并集，对目标与预测对称。3个验证视角从未反馈求解/选模，但存在历史P0依赖。无GT可读、无DXY写入、无相机更新；直径/真实体积误差NOT_EVALUABLE。FCL/Blender只对接受端点和已检查状态提供数值证据，未认证全路径CCD。不要自动追加迭代、提高分辨率、增加病例或开展消融。
