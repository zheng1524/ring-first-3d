# Failure ledger

| ID | 状态 | 失败/限制 | 证据与处理 |
| --- | --- | --- | --- |
| S01 | FAIL / STOP | V6 F0当前输入首层p95=0.935719mm＞0.20；V2 F0=1.240241mm | 两版NN_*_F0_METRICS.json、Fig1/2；F1/F2未运行，不改阈 |
| S02 | OPEN | V6 12,594面邻接Unknown，整体闭合64分量；ref084495条错层中3504落在已观测单元 | FACE_VALIDITY.csv、F0_FAILURE_DIAGNOSIS.csv、Fig3；没有删除输出面或把闭合当准确 |
| S03 | LIMITATION | 清理后固定V2分母首层MISS595→688，覆盖减少0.711个百分点 | F0_SUMMARY.csv，Fig4；不以较小分母下p95减少宣称收益 |
| S04 | FAIL_CONTROL | matched Open3D V6原生命中88.22%，V2 87.89%，未过90%；命中精度较高不能掩盖MISS | O3D_*_METRICS.json；未加细体素重试 |
| S05 | UNRESOLVED | 留出ref13/ref03深度差异、相机和HERO不确定性 | Fig2、全部原生RAYS；不当物理GT，不校正深度/相机 |
| E01 | RESOLVED_BEFORE_GPU | 保存官方training/utils.py时多一个末尾换行，Git blob合同拒绝 | 恢复官方精确字节并核SHA；无执行该训练模块 |
| E02 | RESOLVED_BEFORE_GPU | 缺scikit-image导致推理脚本在import阶段退出，未调用模型 | 仅本任务runtime/python安装0.23.2/tifffile2024.8.30；共享环境未改 |
| E03 | RESOLVED_NUMERIC | MISS为Inf时NumPy线性分位数可能Inf−Inf→NaN | 保持相同分母/阈值，将跨MISS的p95显式记Inf及状态；Open3D判断仍FAIL |
| E04 | NON_SCIENTIFIC | 新worktree sparse-checkout缺lock目录 | 未改变历史分支，保留独立工作树；没有重置或清理其他工作树 |
| E05 | RESOLVED_DISPLAY | Fig2 colorbar覆盖图像 | 移至独立边栏，CPU重绘；未再次运行模型或改数值 |
| E06 | RESOLVED_EXPORT | 初始辅助GLB坐标为毫米，glTF标准按米解释 | 从原PLY另存*_m.glb并核Face ID及尺度；未交付*_mm.glb |

无训练、无权重更新、无GT/Oracle、无新增HERO、无位姿优化。所有失败保留；本轮没有补救搜索或放宽标准。
