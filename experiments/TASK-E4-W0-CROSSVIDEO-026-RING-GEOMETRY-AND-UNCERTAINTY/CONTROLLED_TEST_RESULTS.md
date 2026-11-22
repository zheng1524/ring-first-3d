# CONTROLLED_TEST_RESULTS

| 测试 | 结果 | 证据 |
|---|---|---|
| Ring 拒绝明显错误位姿 | PASS | H025: E_Ring 0.242 → **178.7** |
| Ring yaw 不可辨识性 | PASS | 0°→1° 仅 0.260→0.560；45° 才 54.2 |
| 共同刚体扰动不改变点间距离 | PASS | 1° 共同旋转：位移 0.35 mm，距离变化 7e-7 mm |
| 相对相机扰动改变点间距离 | PASS | 0.5° 单相机：距离变化 3.4–19.3 mm |
| 三角化代码为历史 019 | PASS | `features019.landmarks` 实跑 8 次（基线与 7 组扰动） |
| 冻结划分一致 | PASS | SPLIT.json SHA 与 025 相同 |
| 10 类可视化全部真实数据 | PASS | `runs/G03/FIGURES/` |

## 未完成

- 共享 H 联合优化：**未执行**（Gate C）。
- 单视频相机精化（BA）：未授权。
