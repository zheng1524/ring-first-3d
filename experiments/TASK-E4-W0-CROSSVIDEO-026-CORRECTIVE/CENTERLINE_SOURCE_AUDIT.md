# CENTERLINE_SOURCE_AUDIT

## 历史 020 的 Centerline 是什么

`ring020.evidence()` 读取 `R/ring/<view>.json` 的 `centerline` 椭圆，生成 720 点 `mid`，
再用 `mid_weight`（inner+outer 覆盖相位）加权。该 JSON 由**019**的 `ring019.py` 生成：

```python
report, payload = recover(a['labels'], a['RGB'][:,:,::-1], 10.)   # dxy_mid._engine.ring_component
save('ring/'+v['id']+'.json', report)   # 含 inner / outer / centerline
```

即 Centerline 是 DXY 例程对**管截面中心线投影**的二维辅助拟合，不是 Inner，也不是 Inner/Outer 平均。

## 026 的错误

026 用 011 的 `DXY_OBSERVATIONS`（只有 inner/outer）适配，缺失 centerline 时写成
`centerline = inner` → C 项在语义上重复 Inner。

## 本轮修复

用**历史同一例程** `recover(labels, RGB, 10.)` 在 22 个 G03 ACCEPT 视角重新生成，
写入新命名空间 `replay/ring_corrective/`（不覆盖 026 的 `ring/`）。

| 检查 | 结果 |
|---|---|
| 视角数 | 22 |
| `centerline == inner` | **0 / 22** |
| centerline 缺失 | 0 / 22 |
| DXY report `valid` | 22 / 22 |

## 影响

| 指标 | 026（假 C） | 本轮（真 C） |
|---|---:|---:|
| E_C 中位 | 1.8339 | **0.1397** |
| MIO | — | **0.1617** |
| MICO（含 C） | 0.2416 | **0.1691** |

两者分别命名为 `MIO`（诊断配置 A）与 `MICO`（完整历史配置 B），不混称。
