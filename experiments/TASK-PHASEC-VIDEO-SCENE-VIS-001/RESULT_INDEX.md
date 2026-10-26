# 结果索引｜004同视角样图

状态：004_SAMPLE_READY / DISPLAY_ONLY / WAIT_FOR_HUMAN_REVIEW。只有G01 video004、004_ref03/raw303；005和批量保持暂停。早先试图保留本地，不作为本次交付。

| 文件 | 对应 |
| --- | --- |
| [原始真实帧](figures/G01_004_same_camera/Selected_Real_Frame.png) | 原始1280×720，raw303，0-based |
| [同相机三维场景](figures/G01_004_same_camera/Local_3D_Scene.png) | 24,343原P0＋30,336局部RGB背景点＋实体黑色CAD |
| [左右比较](figures/G01_004_same_camera/Real_vs_3D.png) | 同K/c2w，原尺寸并列，无独立缩放 |
| [轮廓叠加](figures/G01_004_same_camera/Projection_Overlay.png) | 仅展示投影检查，非三维精度 |

[唯一技术报告](TECHNICAL_REPORT.md) · [配置](config.json) · [场景元数据](metrics/SCENE004.json) · [32项核验](metrics/VALIDATION004.json) · [输入SHA](provenance/INPUT004.json) · [四图SHA](provenance/FIGURE004_MANIFEST.json) · [公开文件清单](provenance/PUBLICATION004.json)。

原点和背景三维缓存：[本地资产哈希清单](provenance/LOCAL004_ASSETS.json)，完整文件未上传。代码入口：[scene004.py](code/scene004.py)，相机绘图：[real_p0_renderer.py](../../visualization/real_p0_renderer.py)。

实际代码提交`2dffe90cf2300ac9182401dbf4e194059c6a6d37`；四图提交`d54f1b672b054a35e7388e90bda19c70712766d7`；最终报告提交以本文件所在commit及交付消息为准。main基础模块独立提交`02dee8092dce9f89d050bccca35aa51768988645`，不包含任何点云清理算法。
