# 复现和本地数据索引

父目录与旧结果只读。本记录为 `runs/SAME_KERNEL_BIDIRECTIONAL_001`，两个独立case，不复写父FINAL。请在另一个运行记录副本复现；当前prepare/fit已有防覆盖断言，不能通过删除标记覆盖现有结果。

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
PAIR=experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001
BLENDER=/home/liu/blender/blender-5.0.1-linux-x64/blender
```

按assets_index恢复父实验BASE_FIELD、CAMERAS、RING_CAD的原字节到各case inputs，并复制原LOCKED_PROTOCOL全部数值参数。GT生成位置复用父audit_only/TARGET_GT中的先前预登记位置，绝不能读取父FINAL的中心。生成源记录和控制SHA在CONTROL_FREEZE.json。

每组指定独立环境变量（必须为cases直属子目录）：

```bash
export E4_CURRENT_RUN="$PWD/$PAIR/cases/A_expansion"
"$PY" -B "$PAIR/code/prepare.py"
"$BLENDER" --factory-startup --background --threads 2 --python-exit-code 2 --python "$PAIR/code/render_blender.py"
"$PY" -B "$PAIR/code/projection_gate.py"
```

B以 `cases/B_contraction` 同样执行。**两组控制、协议、投影门禁和输入SHA须在任一组拟合前冻结**。实现回执格式见case metrics/IMPLEMENTATION_FREEZE.json：共享code/vendor文件、PROTOCOL.md、各自inputs文件和LOCKED_PROTOCOL均绑定git commit及SHA；不包括audit_only GT。新副本必须记录其真实绝对路径，不能照抄回执冒充新冻结。

然后每组执行一次：

```bash
"$PY" -B "$PAIR/code/fit.py"
```

fit.py/model.py/renderer.py/projection_gate.py与父版本逐字节一致；common.py只改R/REPO路由。正式源码提交fceeef8；12轮/500函数评价/原目标/原Powell/原初始化，不准改半径或按GT重启。优化进程禁止audit_only及.blend读取，脚本自动做拒读测试。

每组完成后：

```bash
"$PY" -B "$PAIR/code/evaluate.py"
"$PY" -B "$PAIR/code/boundary_audit.py"
```

evaluate.py先冻结预测SHA再读取GT；用原fit.py AST中的同一个evaluate函数代入GT/最终/起点，不启动新优化。每轮保存真实几何误差、粗糙度、FCL间隙及连通；初始/GT/最终另用原Blender EXACT检查器。同法线未命中存NaN，主表GT与预测均使用相同最近面距离变化。

两组均审计后生成并列图及报告（不导入case写入钩子）：

```bash
"$PY" -B "$PAIR/code/figures.py"
"$PY" -B "$PAIR/code/report.py"
"$PY" -B "$PAIR/code/validate_delivery.py"
```

完整原场、GT、逐轮Mesh/GLB/NPZ、本轮投影和位移数组保留本地，见assets_index/LOCAL_DATA_INDEX.json。PLY/mm、GLB/m，Blender 1BU=1mm。只上传小型代码、配置、审计和四图。

最后的完整性检查只重算SHA、检查JSON/源码语法、交付链接与已保存的门禁记录；不再次拟合，不改预测。结果见 `assets_index/DELIVERY_VALIDATION.json`。科学结论仍为扩张幅度失败、收缩通过本次控制门槛；交付完整性通过不等于两组科学成功。

依赖保持：Python3.12、Torch2.7.1、SciPy1.15.3、NumPy1.26.4、Open3D0.19、trimesh5.1.1、python-fcl0.7.0.11、Blender5.0.1。官方Kaolin standalone源码commit ee8b7eca1e56b1b9fd1509fc406f8d8ccbc9240b保留Apache许可及原字节；不安装PyTorch3D、不运行GPU训练。

所有其他组、其他幅度/位置、多核或其他优化器均未运行；完成即停止。
