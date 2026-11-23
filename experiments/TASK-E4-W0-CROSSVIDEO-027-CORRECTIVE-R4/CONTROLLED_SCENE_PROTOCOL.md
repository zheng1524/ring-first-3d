# CONTROLLED_SCENE_PROTOCOL

## 实验 I（固定真值，只改初始化）

- **GT**：`r2_synth.build_scene(seed=0, nlm=12, H_rot_deg=(0.7,-0.4,12.0), H_mm=(0.4,-0.3,0.2))`
  → `H_gt`（12.03° yaw）、6 台 GT 相机（3×004、3×005）、12 个 GT 地标；
- **观测**：`rgb_observations(seed=1, noise=0)` 只生成一次；`ring_observations`（I/O/C）同样只生成一次，
  子采样 I/O 1/8、mid 1/16（受控计算预算，配置冻结）；
- **基线结构**：`baseline_X` = 005-only 三角化（历史 019 逐轨迹代码）→ 与 GT 差 **0.0 mm**；
- **所有 A–E 组共享同一份观测与 Ring**；只有初始化变量按组改变；
- **优化**：M0（不优化）、M1（仅地标）、M2（仅 H，200 次）、M3（H 30 次 → 地标 30 次）；
  M4（H+地标+释放 2 台 004）**未执行**（实现有索引 bug，已修复但时间不足，未重跑）。

## 冻结配置

`config/R4_PROTOCOL.json`：扰动幅度、种子、预算、Ring 权重、损失模式、释放集合。
每次运行把**实际使用参数**写入 `CONFIG.json`（而非只写声明值）。
