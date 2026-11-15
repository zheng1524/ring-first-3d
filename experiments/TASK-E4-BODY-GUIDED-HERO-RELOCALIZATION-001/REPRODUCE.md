# 复现

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
export E4_RUN_DIR="$PWD/experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001"
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
# 输入已经冻结；以下命令读取相同本地原生资产，不能覆盖历史任务。
$PY -B "$E4_RUN_DIR/code/test_contracts.py"
# 已冻结Body-E/U和SIFT拆分可直接恢复。不要重新选择视角/重拟合以挑选更好结果。
$PY -B "$E4_RUN_DIR/code/run_real_parallel.py"
$PY -B "$E4_RUN_DIR/code/evaluate_real.py"
$PY -B "$E4_RUN_DIR/code/visualize.py"
$PY -B "$E4_RUN_DIR/code/finish_reports.py"
```

首次从输入清单重建新根时，依次调用prepare.py、fit_body.py、features.py、replay_a1.py；控制端prepare_controls.py、render_control_rgb.py（Blender命令见控制渲染日志）、assemble_controls.py、run_controls.py、evaluate_controls.py。正式冻结源和GT控制生成/审计分离，不在优化中打开audit_only。

本机包路径由code/common.py只读挂载现有环境，版本见provenance/ENVIRONMENT.json。无需下载模型或新框架。历史代码依赖来自同仓库parent commit及源码SHA。新机器需要先恢复assets_index与provenance/INPUT_SHA列出的原生资产/固定输入；仓库小型交付不包含全量原始视频、HERO及GLB。没有这些输入不能声称仅git clone即可复现实验。

run_real_parallel.py仅将相互独立的来源/Body计算分成3个CPU进程；组顺序G03→G05→G01→G06，不改变seed、目标或预算。中途恢复先核对源码/配置SHA，仅跳过已冻结的数值状态；未完成seed从原固定初值重跑。每个来源目录保存候选及每次LS residual call轨迹；轨迹不是全部“接受迭代”。全部150状态冻结后才独立评价。

原生ID映射：obs的pixel_id、mesh的original_face_id/native_pixel_id不变；REGION.npz记录每个候选的source_pixel_id、source_native_index、Body face与Q；DERIVED.npz包含全原面及派生C。accepted_H缺失时为NaN/null，数值提案仍保留但不得冒充通过。GLB每个来源、Body和Ring独立图层，根mm→m转换0.001；不叠加不同arm宣称融合。

历史29份旧网格未提供逐顶点native_pixel_id，只有归档UV/K；导出中缺失原生ID明确为-1，保留原始顶点序号/归档UV/原面ID。不得把归档360行UV冒充352行原生像素。全部区域锚仍有OBS原生PixelID。
