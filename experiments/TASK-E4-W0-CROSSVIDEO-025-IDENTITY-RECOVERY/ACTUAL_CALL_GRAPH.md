# ACTUAL_CALL_GRAPH

```
run_cross_video_registration.py --group G --stage identity-validation
 ├─ core/p1_020_chain.py
 │    ├─ features019.landmarks(fit4,'CROSS_004')        [历史源码，实际调用]
 │    ├─ features019.cross(fit4,fit5,lm4,'CROSS')       [历史源码，实际调用]
 │    ├─ features019.landmarks(fit5,'INDEPENDENT_005')  [历史源码，实际调用]
 │    └─ features020.make('CROSS',fit5,fit4,'REVERSE','INDEPENDENT_005')
 │           └─ features019.cross(fit5,fit4,lm5,'REVERSE')  [反向 PnP]
 ├─ core/p2_validate.py
 │    ├─ landmark_consistency.check(..., seeds=0..4)    [024 模块，Open3D RANSAC，无尺度]
 │    ├─ Ring 检查：torus_contours(H·C4) / H⁻¹·C5 vs W0 q_train
 │    └─ HOLDOUT：批次描述子匹配 → 真实像素 → H / H⁻¹ 投影
 └─ core/p6_visuals.py（只读，不写身份状态）
```

`common.py` 的唯一改动：`REPO = Path('/home/liu/ring_first_3d_workspace')`。
