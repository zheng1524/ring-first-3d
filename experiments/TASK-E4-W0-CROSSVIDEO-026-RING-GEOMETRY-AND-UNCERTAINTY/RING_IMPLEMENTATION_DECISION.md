# RING_IMPLEMENTATION_DECISION

**选择：`H020_REUSED`（历史 020 的 `RingRenderer`，经最小路径适配）。**

## 代码差异（唯一改动）

`replay_020/code/ring020_026.py` 相对历史 `ring020.py`：

```diff
- r=np.load(R/'inputs/G01/RING.npz')
+ r=np.load(Path(os.environ['RING_CAD']))
- norm=load(R/'inputs/G01/NORMALIZATION.json')
+ norm=load(Path(os.environ['RING_NORM']))
```

其余 `CADCurves.segments/project/point_to_segments`、`RingRenderer.losses`、
`evidence` 的可见弧/权重逻辑**逐字节未变**。
历史目标 `E=0.25E_M+0.35E_I+0.05E_C+0.35E_O` 与 Huber(d/3) 保持一致。

## 为什么不新建

方案 A 通过受控验证（见 `RING_GEOMETRY_VALIDATION.md`、`RING_POSE_IDENTIFIABILITY.md`），
因此不允许也无需新建第二套 I/O 实现。
