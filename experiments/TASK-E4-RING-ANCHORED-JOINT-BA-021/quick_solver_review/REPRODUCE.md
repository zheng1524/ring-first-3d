# 快速复核复现

工作目录 `/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/quick_solver_review`；沿用021当前分支，旧021冻结结果只读。Python为 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python -B`，未安装新框架/下载模型。原始大型JPG/Mask/旧视频/权重保留本地并索引。

```bash
PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
Q21=/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/quick_solver_review
# 已有FINAL时续优化和照片拟合跳过，不覆盖历史。全新回放先使用独立目录并配置qcommon.Q；先恢复同SHA原始资产。
$PY -B "$Q21/code/solver_review.py"
$PY -B "$Q21/code/evaluate_review.py"
$PY -B "$Q21/code/gradient_isolation.py"
# 照片资产必须显式raw20260805，禁止用同名旧照片。
$PY -B "$Q21/code/photo_assets.py"
$PY -B "$Q21/code/photo_registration.py"
$PY -B "$Q21/code/photo_2d_geometry.py"
$PY -B "$Q21/code/photo_audit.py"
$PY -B "$Q21/code/hero_prepare.py"
$PY -B "$Q21/code/figures_review.py"
$PY -B "$Q21/code/report_review.py"
$PY -B "$Q21/code/verify_review.py"
```

协议见config/SOLVER_PLAN、PHOTO_POSE_PROTOCOL、PHOTO_RGB2D_ADDENDUM；旧sourceSHA见021原始冻结清单及本目录provenance。当前photo_assets为正确批次源码，旧错误尝试全保留但不属于正式输入。正式同批源JPG的完整SHA/Mask与原图绑定见manifest和inputs/*/IDENTITY.json。准入由当前PHOTO_HELD与几何记录决定，不使用旧历史标签阻塞。

所有新文件限定本quick目录；不运行原021准备/优化脚本，不修改DXY/原相机/HERO。HERO清理/官方前向本轮没有执行；hero_prepare只核验和准备，绝不隐式启动推理。大数组/原件/隔离失败产物在本地SHA索引，不宣称全部上传。
