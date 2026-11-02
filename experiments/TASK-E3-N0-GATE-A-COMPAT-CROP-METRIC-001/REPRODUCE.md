# 安全复现（CPU，Gate A only）

父提交d69ade170352d1b5a1e46239f9516ab38c575648；全部源文件/原点身份、相机和SHA见SOURCE_AND_CROP_MANIFEST.json。数据路径沿用本机历史资产；另机需同身份/同SHA数据映射，不能用其他预测补齐。官方源码/两权重与EasyDict1.9仅在runtime本地，config/OFFICIAL_ARTIFACTS.json记录固定URL、Git blob和SHA256。

代码入口：preregister.py→checkpoint_compat.py→build_crops.py→cross_view.py→metric_domain.py→verify_contracts.py。人工查看human_review_figures.py的两张图后，用户新增授权projective_cleanup.py一次；随后recheck_cleaned_inputs.py、finish_scope_update.py保持相同裁剪/阈值重核并选全包候选。figures.py输出四核心图。禁止把未执行的F0–F5或matched Open3D加进复现链。

在已有交付目录**安全重放到全新目录**，不覆盖本轮数据：

```bash
cd /home/liu/ring_first_3d_e3n0/experiments/TASK-E3-N0-GATE-A-COMPAT-CROP-METRIC-001
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/fetch_official.py
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/replay_geometry.py --output runtime/replay_review_01 --include-authorized-cleanup
```

fetch_official仅获取缺失的固定资产/核验已有SHA，不执行模型。replay_geometry在新的task/runtime子目录绑定同一源码函数与IO；重放原始crop、24关系、两个候选域、同一55点规则、派生crop和24关系，按原分母比较原CSV。它不是重新搜索/另做科学清理，也不触及原始资产。若runtime/replay_review_01已存在，换新目录名，脚本拒绝覆盖。模型静态严格加载结果可审阅CHECKPOINT_COMPATIBILITY_MATRIX.csv及config细节，不需要运行任何forward来复核状态键/形状。

需要独立重新strict CPU检查时，使用同固定官方源码、EasyDict1.9和TorchCPU加载路径；代码checkpoint_compat.py禁止training/GT/forward。该脚本默认写本任务结果，历史交付请在独立新工作树副本中检查，勿覆盖冻结统计。无需安装Lightning/graphics/官方旧完整环境，本轮只构造纯模块；兼容性不延伸至GPU或正式融合。

相同native像素的解析XYZ阈值1e-5mm；连续投影阈值1e-4px；r14宽度代理2<3保留FAIL。原始42PASS/2FAIL不是“全过”。完整本地逐点数组、depth/crop/身份、24关系和派生副本SHA见LOCAL_RESULTS_INDEX.json；权重/全深度和重放中间文件不进Git。docs中的两行Markdown双空格来自PM原文的换行，原字节保留，未篡改源规范。

主要依赖：Python3.12、Torch2.7.1、NumPy1.26.4、历史Open3D0.19 vendor、OpenCV、trimesh、Pillow、Matplotlib、PyYAML；无新模型推理、无GPU、无optimizer.step、无新TSDF。N0停止于Gate A，所有后续门禁仍需研究者单独授权。
