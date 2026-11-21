# HISTORICAL_SOURCE_AUDIT

## 源码位置（`5636aae` 在本仓库不存在）

本仓库只有 38 个提交，`git cat-file -t 5636aae…` → `could not get object info`；`git log --all` 里也没有 019/020 的路径。
真实源码在：

```
/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code    (24 files)
/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020/code (22 files)
/home/liu/ring_first_3d_workspace/assets/retained_sources/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019
```

## 三份同名文件的哈希

```
50cd25fd8df87364…  019/code/features019.py
50cd25fd8df87364…  020/code/features019.py
50cd25fd8df87364…  021 lineage code/features019.py
```

**完全相同**。任务书 §H2 担心的"同名不同内容"未发生。

## 关键实现（源码逐条核对）

| 模块 | 实际内容 |
|---|---|
| `features019.py` | `SIFT_create(nfeatures=6000, contrastThreshold=.01)`；灰度 `12<=g<245`；三视角轨迹；`cv2.triangulatePoints` 初值 + `least_squares(loss='soft_l1', f_scale=1.5, max_nfev=30)`；质量门 `positive depth ∧ max_reproj<2px ∧ parallax>0.5° ∧ |X|<300` |
| `ring020.py` | 曲线距离用 `t=(D·v)/|v|²` 的线段投影；`x=dist/3`、Huber；Mid 权重 `1.0 / 0.25 / 0`（双覆盖/单覆盖/未知） |
| `objective020.py` | `SymmetricFeatures(scope, held)`；`Objective.transform(q,seed)=exp_se3(q*scale)@seed`；Ring 权重取 `PROTOCOL['ring_weights']` |
| `optimize020.py` | `torch.optim.Adam(lr=.01)`、80 次、每步深拷贝 Adam 状态、拒绝时回滚；`LOCAL_SE3_BOUND` 1.2 mm / 10°；逐迭代 checkpoint |

## 历史产出（020）

`results/{R0,R1,R2,R3,R3_MASK_ONLY,R3_INNER_OUTER,R4,NEGATIVE_R3}.json`、`ACTUAL_RUN_SUMMARY.csv`、`metrics/*`、
`features/CROSS_{PNP,REVERSE_PNP,NAMED_3D_TRACK_PAIRS,EPI_2D_ONLY}.json`、`landmarks/*`。

## 数据完整性

- `020/landmarks/CROSS_004.npz` → **悬空软链接**（指向已删除的 `ring_first_3d_e4_sdf_localization`）。
- `020/landmarks/INDEPENDENT_005.npz` → 真实文件（216 KB）。
- `019/landmarks/CROSS_004.npz` → 真实文件（34.7 KB），本轮以它替代。
