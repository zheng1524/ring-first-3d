# BA_LOSS_SCALE_AUDIT

## 冻结 BA 的实际目标

```python
residual(x) = [ RGB rows (3*nf), ring_i * sqrt(max(1,counts[i])/max(1,rglen[i])), temporal(6*(n-1)) ]
least_squares(..., loss='soft_l1', f_scale=1.0, diff_step=1e-5)
```

- RGB：每轨迹 3 个残差（`pi(T_i,X_j)-u_ij` 的 2 个 + 正性 1 个），乘 RGB 权重（默认 1）。
- Ring：每视角 `rglen[i]` 个残差，整体乘 `sqrt(counts[i]/rglen[i])`。
- `counts[i]`：该视角可见的 RGB 轨迹数。
- `soft_l1(f_scale=1)` 作用于**所有**行，包括 Ring 行。

## 由此推导的实际权重

设第 i 视角 Ring 残差向量为 r_i（长 rglen_i），则进入 `least_squares` 的平方和为

```
Σ_k soft_l1( sqrt(counts_i/rglen_i) * r_{ik} )
```

当 `|r|` 很小时 soft_l1 ≈ r²/2，于是 Ring 总贡献 ≈ `counts_i/(2 rglen_i) * Σ_k r_ik²` = `counts_i/2 * mean_k(r_ik²)`。

**结论一：总权重 ∝ counts_i，与采样数 rglen_i 无关。** 采样 128→512 不会让 Ring 强 4 倍。
**结论二：Ring 强度被 RGB 轨迹数调制**（特征多的视角 Ring 更硬）。这是设计缺陷。
**结论三：`soft_l1` 的 f_scale 对 Ring 与 RGB 相同**，但两者的残差尺度不同（RGB 是像素重投影，Ring 也是像素距离），量级可比，因此这一点尚可接受。

## A1/A2 的差异（008 实现）

| 臂 | 边界块 | τ | λ_C | 是否绕过 counts 耦合 |
|---|---|---|---:|---|
| A0 | 原始 `r_q` | — | 1 | 否（原样） |
| A1 | DXY 内外轮廓，逐点归一化 | 0 | 1 | 否（公平对照） |
| A2 | 同上 + 柔性带 | 1.0 px | 0.5/1/2 | 否（**未完成**） |

## 未解决的耦合

要让 A2 真正独立加权，需要把 `sqrt(counts/rglen)` 换成显式的 `sqrt(λ_C)/sqrt(rglen)`，
这需要改 BA 的装配代码（允许范围内），本轮**未实现**。
