# 复现本次进度图

本次只有已完成训练的读取/提取/展示，新增optimizer.step=0；没有启动云端训练控制器。

本地工作树：`/home/liu/ring_first_3d_e3_sdf_4090`。任务目录：`experiments/TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001`。完整4000步检查点SHA及来源在provenance/LOCAL_M1_HANDOFF.json，当前图/原始Mesh索引在provenance/ACTUAL_PROGRESS_DELIVERY.json。

1. `code/build_bundle.py`说明如何仅以选定9源的原始RGB/Mask/原生HERO/冻结相机/CAD及当前派生输入构建SHA绑定数据包；不含视频、HERO权重、GT或融合预测。
2. `code/install_port.py`生成路径/恢复/运行步数IO端口；网络、损失、采样、优化调度和单位逐项检查不变。实际迁移代码保存在code/portable_training，原官方13份源码在vendor/official_exact。
3. 远端独立环境实际为`/root/ringfirst_monosdf_4090/env`，实验目录`/root/ringfirst_monosdf_4090/experiment`。该环境安装完成。认证由用户本机终端处理，主机指纹人工确认；未保存密码/私钥/令牌，始终StrictHostKeyChecking=yes。
4. 已执行的`remote_bootstrap.py`验证数据/官方代码SHA并完整绑定本地4000步模型/Adam/调度器/RNG；再次执行有禁止覆盖守卫，当前不要重新初始化。
5. `cloud_snapshots.py`只将2000/4000步已有参数用官方get_surface_trace在256³网格提取，验证参数逐项不变，未创建或调用优化器。原始SDF/Mesh已回传本地bundle/groups/G01_004/local_results。
6. 0/1000步使用同一既有训练记录的原导出，全阶段Mesh都是实际神经SDF iso0，未作几何平滑/组件删除/补洞。

当前本机绘图命令（无需GPU/优化器）：

```bash
cd /home/liu/ring_first_3d_e3_sdf_4090
TASK=experiments/TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001
PYTHONPATH=/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor:/home/liu/ring_first_3d_neural_e0/experiments/TASK-NEURAL-E0-COMPARE-001/runtime/python \
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B "$TASK/bundle/code/render_actual_progress.py"
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B "$TASK/code/finalize_progress.py"
```

`bundle`、原场、checkpoint只本地，不进GitHub。若在另一机器复现，需要恢复已登记的数据资产并重映射根目录，不得改其数组内容。环境版本见provenance/REMOTE_ENVIRONMENT.json；固定raw SDF CPU/GPU差3.43323e−5mm，不承诺跨CUDA构建bitwise一致。

最终四图在figures，原始毫米Mesh在local_results/G01_M1_step004000_raw_mm.ply。原始字段、逐原生ID首交点及面标签仍在bundle/groups/G01_004/local_results/single_M1_step004000。视图使用同一Ring世界毫米窗口，黑色为实际CAD，不把正交展示相机当独立验证视角。

`cloud_controller.py`是中断前编写、尚未发布/联调的候选。不能凭其存在声称4090性能测试或20k训练已执行。任何继续训练应保留4000完整状态并做启动验证，不能重新初始化冒充续训。
