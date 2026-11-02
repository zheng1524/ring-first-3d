# Reproduce final A3 and formal V4

父提交75ba88303f5ca2e3eee362451d7a717d92506e10。需要原六源文件及Gate A/A2不可变本地缓存；config/PROTECTED_START.json、DERIVED_INPUT_MANIFEST.json、V4_DERIVED_INPUT_MANIFEST.json提供路径/SHA。没有模型下载或主环境升级。

从本分支repo根目录运行，output必须是尚不存在的本任务runtime子目录：

```bash
/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/code/replay.py --output /home/liu/ring_first_3d_e3n0_a3/experiments/TASK-E3-N0-GATE-A3-MASK-BOUNDARY-CLEANUP-001/runtime/replay_new
```

入口复制原始冻结协议和背景补充授权、精确小型分析源码，然后依次执行mask_cleanup、analyze及正式v4（V3减260）。不执行废止5px目录，不覆盖原结果。最终22份关键CSV与本轮结果逐字节核对。已实测runtime/replay_final_verified/REPLAY_VERIFY.json全部一致。

原始执行为preregister.py→mask_cleanup.py→analyze.py→audit.py；研究者背景授权前的版本已归档。正式V4单独冻结260点ID和规则，再调用原A2多视角投影循环及原分析main，执行audit_v4.py。preregister.py只用于初始父HEAD，禁止在最终提交重写历史冻结。图像由figures.py生成，不是神经重建。

源环境：Python3.12.13，NumPy1.26.4，Open3D0.19历史vendor及已有SciPy/OpenCV。CUDA不可见，Torch/训练导入与权重读取被守卫拒绝。GT/Oracle/Dxy及历史输出写入受阻；仅任务派生文件可写。LOCAL_RESULTS_INDEX记录大数组，所有原生ID/三维坐标仍可回溯到原账本；只上传小代码/配置/表和四核心PNG。
