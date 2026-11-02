# 复现

本目录来自 Camera Gate 父提交 6423b2709d1b528124ba6cc855883ba8a437e28c，分支 exp/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001。仅 CPU；环境 Python /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python，Open3D 0.19.0 复用 surface_fusion_v3/vendor。NumPy、OpenCV、SciPy、trimesh、Pillow、Matplotlib 沿用本机安装，无下载。

原始输入路径、SHA、K、c2w 和来源顺序见 HERO_TSDF_INPUT_MANIFEST.json、TSDF_CONFIG.json。外部资产只读；本目录代码启用原始几何白名单、网络/神经模型/GT/Dxy 拒绝和任务外写入拒绝。无需大型原视频或模型权重副本。所有 Mask 外、Ring、背景 depth=0；不集成 CAD。

在已有交付目录安全重放实际基线（目录必须尚不存在）：

```bash
cd /home/liu/ring_first_3d_e3d0/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/replay_baseline.py --name G0 --output runtime/replay_G0_review
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/replay_baseline.py --name G1 --output runtime/replay_G1_review
```

SINGLE 和 SINGLE_RESOLUTION_CONTROL 用相同 --name 接口。每次在新目录生成官方实际 Mesh 与观测带；完整官方 TSDF volume 在内存中真实构建。数值坐标输出 mm；GLB 查看器的默认米单位不代表数据已缩放。没有简化/补洞/清理。

本轮执行链（用于理解与独立新工作树复现，**不要覆盖已存在的冻结记录**）：

1. freeze_inputs.py：从已审计来源建立 6 来源清单、5区选择、参数及 SHA。存在 TSDF_CONFIG.json 时拒绝重冻。
2. run_tsdf.py single：生成 SINGLE 与官方 mm/m 对照。严格验收故意保留实际 FAIL，进程会报断言；不是假装通过的命令。
3. diagnose_single.py：保存初次失败，修正最近顶点近似为表面距离代理，运行唯一预登记 0.05 mm 对照。没有改变门槛。
4. continue_diagnostic.py：明确保存严格门槛仍 FAIL 的继续诊断决定，实际生成 G0/G1。未创建 ADAPTER_INTERFACE_FREEZE.json。不得把 run_tsdf.py multi 的正式门槛分支当成本轮通过路径。
5. evaluate.py：全原面分母距离、固定像素真实重投影、拓扑、支持/Unknown；重建完成后才读 E3-C 诊断。输出实际未删面 GLB。
6. diagnose_extensions.py：后验定位 native/Raw 表达差异及第4个远端案例。
7. figures.py：四张实际几何图。
8. verify_delivery.py：输入/工作树保护、Mask/mm合同、G0独立 Masked RGB-D 重放；预登记门槛保留1项 FAIL。
9. supplemental_metrics.py：原始 Mesh 拓扑及 Fig3 原面窗口的后验描述。
10. write_reports.py：汇总实际指标，未修改融合结果。

local_results/ 被 Git 忽略，其全部文件 SHA/大小在 LOCAL_RESULTS_INDEX.json；实际 Mesh、TSDF 观测带、RGB-D replay、全原面/真实像素查询都留在本机。GitHub 上传完整实际 Mesh+CAD 的轻量 GLB 和四张 PNG。ScalableTSDFVolume Python 没有完整权重序列化；观测带不是全状态文件，要用保存 RGB-D/原资产按固定顺序重放。此限制保留在失败账本。

VALIDATION_RESULTS.csv 中 PASS 表示具体合同成立，不等于科学验收；本轮总计 24 PASS / 1 FAIL。指标完整分母 p95=+∞ 时，JSON 以 null 加显式 infinite=true 标志保留，CSV 记录 NaN/inf。禁止把有限命中残差或 NaN 排除后指标当全体成功。
