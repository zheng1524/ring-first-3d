# Reproduce

解释器：`/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`。官方commit/config/checkpoint及24份冻结输入SHA见provenance；原始私人数据需在对应路径可用，不复制大型模型/视频。CPU Open3D0.19来自已审计vendor，Torch2.7.1+cu128来自现有环境；task-local依赖仅scikit-image0.23.2与tifffile2024.8.30。

原执行依次为：prepare.py → infer.py V6 F0 → infer.py V2 F0；matched_open3d.py分别V6 F0/V2 F0；diagnose.py → figures.py → finalize.py。所有文件位于code/。推理脚本严格拒绝覆盖已有RUN，不可在本轮目录直接重复运行。F0失败后F1/F2会被明确拒绝。旧3px不检查。

实际官方model/translator未改，get_translation仅AST提取。下载可读helper时必须使用官方固定commit的training/utils.py，并校验Git blob997c7e67c5f3167fd6c084478ead72f2bdeaaf5e。隔离依赖安装命令见runtime要求；不得pip升级共享环境。

只读复核可运行：
```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B /home/liu/ring_first_3d_e3n0_gate_b/experiments/TASK-E3-N0-GATE-B-NEURALFUSION-F0-F2-001/code/verify_delivery.py
```
该命令只检查已冻结输入、代码与模型SHA、原始资产保护、指标算术、PLY/GLB单位和阶段停止，不调用神经模型，不重新融合。

若需复跑，应在独立输出副本中保留相同source/crop/域/参数并移开副本的旧RUN结果；不能覆盖本目录或历史实验。数值来源与正式GPU执行前的代码哈希见provenance/BEFORE_NN_*.json。物理GT未读取，所有深度/面积指标只与同源HERO原观测比较，不是形状准确率。

PLY单位mm，标准GLB单位m；完整latent/count、两通道输出、known mask、逐像素和逐Face数组在local_results，仅本地保存。`sdf_raw`的未观测0必须和known共同解释，绝不能当零面。正式导出使用官方+0.04哨兵，Unknown邻接面完整保留并单独标记。

隔离复跑布局已通过CPU输入核验，无需改动已执行代码：

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B code/prepare_replay.py
```

此命令在本任务runtime/replays内复制小型派生输入/源码并只读链接既有可视化与元数据；不初始化Git、不调用模型。它先核验24份SHA和V6原生身份，然后打印独立F0命令，绝不自动运行GPU。当前目录仍不允许直接覆盖重跑。正式复跑后依然必须通过同一F0门槛才能新增视角。

首次准备新环境时，task-local依赖安装命令为：

```bash
PIP_NO_CACHE_DIR=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B -m pip install --no-deps --no-compile --target runtime/python scikit-image==0.23.2 tifffile==2024.8.30
```

只读helper来自官方commit固定路径，必须保持官方Git blob SHA；当前主机已留存核验过的精确字节。离开该主机需按manifest提供已授权的私人源资产及Gate A官方runtime；数据缺失则明确报错，不用其他模型或历史融合补齐。
