# TEST_BEFORE_FIX

| 检查 | 修复前（027-CORRECTIVE） | 证据 |
|---|---|---|
| 特征 ID | 由轨迹顺序重推 → 同相机多观测时串号 | `controlled2.py:56` |
| 场景一致性 | Ring 用真实 G03、RGB 用合成 | Level 0 无法定义 |
| Centerline | 被 `if k[1] != 'mid'` 过滤 | BA 实际 IO |
| 可见边缘 | 用 GT H 生成 | `geometry_from(..., scene['H'] @ C)` |
| 受控恢复 | 3.0–10.6°，全部 `success=False` | `027-CORRECTIVE/CONTROLLED_BA_RESULTS.csv` |
