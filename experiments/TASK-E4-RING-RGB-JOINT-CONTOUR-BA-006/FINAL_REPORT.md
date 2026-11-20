# TASK-E4-RING-RGB-JOINT-CONTOUR-BA-006 — FINAL_REPORT

**STATUS: `PARTIAL` / `AWAITING_RA_REVIEW`**

## 0. 一句话

**输入与损失设计已冻结并有实现与测试；合成验证暴露了一个比权重更重要的问题——Ring 的 180° 对称性使任何未对齐的旋转误差指标失效；相机级 A0/A1/A2 对照未运行。**

## 1. 已完成

### P0 统一输入

- 冻结 INIT 权重（SHA `981aa596…`）+ DXY 推理数学，Mask 逐位一致（上一轮已证）。
- 十段 × 16 视角 = **160 个视角**，全部由 `prepare_views.py` 从原始视频生成。
- 用**新 Mask** 重新导出 DXY：**160/160 valid**（`metrics/DXY_OBSERVATIONS/`），未与旧 JSON 混用。

### P1 联合损失设计

`JOINT_LOSS_DESIGN.md` 明确了：观测来源、柔性容差 `d̃=max(0,d−τ)`、按弧长/点数归一化（采样密度不改变强度）、内外等权、可见弧权重 1.0/0.25、τ=1.0 px（由 DXY 实测残差 0.62–0.63 px 支撑）、退化解与防护。

实现：
- `ring_contour_observation.py`：DXY 内外折线 + 可见弧（以真实 Ring 边界点为证据）。
- `cad_contour_correspondence.py`：按面积分内外（不假设顺序）+ 缓存 KD-tree 的折线距离。
- `joint_loss.py`：归一化后的 2 值 Ring 块 + 冻结尾部残差。
- 单测 4/4 通过（容差内为零、扰动单调、采样数不变性、残差长度固定）。

### P2 合成验证（重要负面发现）

在合成 Torus 投影 + 系统偏移/遮挡上扫描 τ ∈ {0,1,2} 与 λ_rgb ∈ {0,1}：

| 现象 | 数值 |
|---|---|
| Ring-Only（λ=0）旋转误差 | **177°** |
| 联合（λ=1）旋转误差 | 145–153° |
| 平移误差 | 8.7–34 mm |

**这不是优化失败，而是圆环的 180° 对称性**：环的投影在对称翻转下几乎不变。
因此：**在 RGB 尚未消歧之前，用旋转误差挑选 τ 是无效的**。
τ 保持预注册值 1.0 px，不依据该扫描更改。

## 2. 未完成

| 项 | 原因 |
|---|---|
| P3 A0/A1/A2 相机对照 | 需 3 臂 × 10 段 × 16 视角 BA，时间不足 |
| 图 B/D/E/F | 依赖 P3 结果 |
| Ring–RGB 真实数据权衡图 | 依赖 P3 |

## 3. 九个科学问题（能答的部分）

**Q1 可靠 DXY 轮廓能否提高 Ring 观测质量？** 观测层面：能——DXY 内外轮廓到真实 Mask 边界仅 0.62/0.63 px，且 160/160 有效。**相机层面未验证。**

**Q2 允许合理偏差能否换来更好的 RGB 一致性？** **未验证**（P3 未跑）。

**Q3 Ring/RGB 权重关系？** 设计已给（归一化后等权 + λ_rgb 预注册扫描），但**没有实验证据**。

**Q4 不确定性归一化是否更稳？** 设计上避免了"采样变密→Ring 变强"，单测证明采样数不变；**稳定性未在真实 BA 中验证**。

**Q5/Q6/Q7** 未验证。

**Q8 新 CAD 投影是否仍合理解释真实 Ring？** 合成图上 CAD 与 4% 尺度误差的拟合椭圆差异清晰可见（图 A），说明 τ=1 px 的柔性带足以容纳该量级模型误差；真实图像结论待 P3。

**Q9 是否足够进入 Body？** 见 `BODY_READINESS_RECOMMENDATION.md`：维持 004 结论，G06/005 可进入受控初始化，G02/004、G02/005、G03/004 仍需修相机。

## 4. 交付物

- `JOINT_LOSS_DESIGN.md`、`EXPERIMENT_PROTOCOL.md`、`DXY_OBSERVATION_CONTRACT.md`、`BODY_READINESS_RECOMMENDATION.md`
- `code/{ring_contour_observation,cad_contour_correspondence,joint_loss,dxy_export_newmasks,synthetic_validation}.py`
- `tests/test_joint_loss.py`（4/4）
- `metrics/{DXY_OBSERVATIONS/,SYNTHETIC_SWEEP.csv}`
- `visualization/A_method_comparison/figA_synthetic.png`、`visualization/C_loss_tradeoff/figC_tradeoff.png`
- `RUN_MANIFEST.json`（本地大文件索引）

## 5. 建议

1. **先做对称对齐后的合成验证**：在评价旋转误差前，把估计位姿按环对称群（绕环轴 180° × 法向翻转）对齐，否则任何 τ/λ 选择都不可信。
2. 用 RGB 消歧后再跑 P3，否则 Ring-Only 的 177° 会污染对照。
3. 在 P3 之前不要再调 τ；τ=1.0 有实测依据。
