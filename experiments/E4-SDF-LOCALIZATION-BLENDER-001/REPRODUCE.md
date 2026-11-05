# 首场景复现

本轮是已知初始几何的控制实验，不是真实息肉自主重建。只执行IIa6.5_R10；Ip4/Is14待人工确认。

工作树：`/home/liu/ring_first_3d_e4_sdf_localization`；分支 `exp/E4-SDF-LOCALIZATION-BLENDER-001`。正式运行前代码提交 `e9661ed`，输入与源码SHA见metrics/IMPLEMENTATION_FREEZE.json。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
EXP=experiments/E4-SDF-LOCALIZATION-BLENDER-001
BLENDER=/home/liu/blender/blender-5.0.1-linux-x64/blender
```

不要在已完成目录重跑生成或优化。使用独立副本保全当前记录，R由脚本__file__定位；按SOURCE_AUDIT与LOCAL_RESULTS的SHA恢复本地依赖，不能按相似名字替换资产。

从头生成的顺序：

```bash
"$PY" -B "$EXP/code/audit_assets.py"
"$BLENDER" --factory-startup --background --threads 2 --python-exit-code 2 --python "$EXP/code/export_blender.py"
"$PY" -B "$EXP/code/prepare_control.py"
"$BLENDER" --factory-startup --background --threads 2 --python-exit-code 2 --python "$EXP/code/render_blender.py"
"$PY" -B "$EXP/code/projection_gate.py"
"$PY" -B "$EXP/code/audit_legacy.py"
```

投影门禁主体/Ring IoU≥0.99、轮廓p95≤1px、点投影<0.001px；不通过不得优化。原K为画幅边界坐标，OpenCV/Open3D像素中心K主点减0.5，CV→Blender轴变换固定diag(1,−1,−1,1)，长度mm。

新副本正式运行前按已保存IMPLEMENTATION_FREEZE格式记录git commit及code/*.py、code/vendor全部文件、inputs全部文件、config/LOCKED_PROTOCOL.json和01_PROTOCOL.md的路径/字节/SHA。不能把audit_only的三维GT目标放入优化器输入；已知BASE为本控制实验允许的初始条件。原样复制已完成回执到新路径不能冒充新冻结。

```bash
"$PY" -B "$EXP/code/fit.py"
```

优化器拒绝覆盖既有FIT_START，并用审计钩子禁止audit_only/.blend/旧仿真目录读取。只用Mask、初始场、相机和CAD；4参数、12轮/500函数评价上限，不改变损失或挑选有利参考。

完成预测后才独立读取GT审计：

```bash
"$PY" -B "$EXP/code/evaluate.py"
"$PY" -B "$EXP/code/physical_audit.py"
"$PY" -B "$EXP/code/figures.py"
"$PY" -B "$EXP/code/report.py"
```

evaluate.py先记录预测SHA再读GT，不反向优化；末轮不按GT或留出结果选模。正式结果保留ROUND_01–04和FINAL，原始SDF、全四面体、Mesh与GT仅保留本地，索引见assets_index/LOCAL_RESULTS.json。

环境：Python3.12、Torch2.7.1、SciPy1.15.3、NumPy1.26.4、trimesh5.1.1、Open3D0.19、Blender5.0.1。Open3D和skimage只读复用已有vendor/runtime；FCL复用R1/runtime/packages，不新增环境。Kaolin只复用官方原样torch-only marching_tetrahedra文件，commit ee8b7eca1e56b1b9fd1509fc406f8d8ccbc9240b，source SHA及Apache许可随代码保留。未安装完整Kaolin/PyTorch3D，不宣称执行SoftSilhouetteRenderer；后备为Open3D+SciPy CPU。官方文件4处尾部空白按上游原字节保留，不为格式化改变其SHA。

不得自动追加其他改动位置、凹陷、半径搜索、三类型实验或方法消融。首场景输出后暂停，等待人工审阅。
