# Ring-First 3D — 当前主线入口

当前状态：**ACTIVE_RESEARCH_MAINLINE**。工程重放通过，尚非CERTIFIED_SCIENTIFIC_BASELINE。

先读 [PROJECT_HOME](docs/PROJECT_HOME.md)、[mainline README](mainline/README.md)、[PIPELINE](mainline/PIPELINE.md) 和 [MAINLINE_ASSET_MAP](mainline/manifests/MAINLINE_ASSET_MAP.json)。规范代码在src/ring_first_3d；mainline提供配置、运行入口、依赖锁和精选结果。

活动路线：EXACT013 Init-A → Deformation Graph + Smooth ARAP → 嵌入式B-spline/RMF → Boolean Union → 多视角轮廓与Ring验收。

- G01：外露1.726844mm；FIT/HOLDOUT0.932784/0.933253；自动门禁通过，但近端局部外露0.047185mm、固定INITIAL→GT框架MAE恶化。
- G03：PER_VIEW_PROTECTION；005两个视角IoU下降0.023444/0.012446，正式柄长NaN。
- 下一阶段：HERO原生深度约束、G03跨视频诊断、根部完整内藏及主体/柄部联合更新；需新TASK/源码锁和科研授权。

运行固定重放：

```bash
bash mainline/scripts/run_ring_first.sh --out /tmp/rf-replay
bash mainline/scripts/run_hero.sh --out /tmp/hero-replay
bash mainline/scripts/run_stalk_growth.sh G01 --out /tmp/stalk-replay
```

入口：[本地主线可视化](mainline/visualization/index.html) · [工程整理报告](maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/TECHNICAL_REPORT.md) · [结果一致性](maintenance/TASK-MAINLINE-ASSET-CONSOLIDATION-001/RESULT_EQUIVALENCE_REPORT.md)。原始数据、权重、官方第三方代码和环境采用LOCAL_ONLY清单，不重复分发。DXY独立只读。
