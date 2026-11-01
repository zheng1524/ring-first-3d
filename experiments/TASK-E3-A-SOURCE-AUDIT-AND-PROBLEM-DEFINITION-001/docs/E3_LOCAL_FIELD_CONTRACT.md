# E3 局部观测场合同（规范；本轮未实现 LocalField）

依据已完整阅读的 RA v1.1、v1.2 和本轮明确授权，局部对象定义为 `F_i=(phi_i,Omega_i,w_i,P_i)`。`P_i` 必须能反查实际 HERO 全部输入 RGB SHA、参考、原生深度、K/c2w、原顶点/三角面/UV、同源家族、清理标签以及派生关系。它不是五份 Raw/Cleaned/F1/F2/F3 证据。

## 坐标和距离种类

所有源使用冻结的同视频 Ring 世界坐标、毫米。`T_i=c2w`，世界点投影使用现存 `real_p0_renderer.project_camera`；反投影使用原 `unproject`。`camera_rays` 的方向不单位化，故 `t_hit` 是相机轴向 Z（毫米），不是沿射线欧氏弧长；若改用单位方向，必须显式转换。原生深度尺寸与 640×360 包装尺寸分别记录，禁止以显示尺寸替代原生索引。

| field_kind | 合法数值语义 | 符号范围 / 不允许事项 |
|---|---|---|
| EUCLIDEAN_SDF | 距已认证物体边界的欧氏最短距离，约定外正内负 | 需要闭合内外关系或独立符号证据；现有开放 Mesh 未获此资格 |
| PROJECTIVE_AXIAL | `delta_i(X)=Z_i(pi_i(X))-z_i(X)`；可在明确窄带内截断 | 朝相机一侧为正，仅局部视线次序；不能当欧氏 SDF、不能直接施加 Eikonal |
| ORIENTED_LOCAL | `(X-Y) dot n_i(Y)`，Y 为合法最近原面点，n 局部朝相机 | 仅有局部法向一致性及唯一最近面证据的窄带；不推出全局物体内部 |
| UNSIGNED_DISTANCE | 到合法原始三角面的最短距离，非负 | 零表示来源曲面位置；不包含内外信息 |
| SURFACE_ONLY | `(source,face,UV,X)` 的表面位置约束 | 没有可用标量符号时仍合法；不得补出内外 |

毫米单位相同不能使这些量具有相同物理意义。法向有向距离、轴向差和 UDF 不能直接加权平均后称全局 SDF。清理标签是风险/保护代理，不会把开放面变成实体。

## 四类域和优先关系

`Omega_surf`：与有效原深度/原面有可追溯关系、在视场和同物体 Mask 内、可见性无已知矛盾的窄带。边界、断裂、掠视、最近面多解处须降为局部无符号或仅表面约束，不得跨孔洞扩张符号。

`Omega_free`：来源相机与**合格可信首表面**之间有明确可见性依据的子段。源深度有误、前方物体身份不明、正 Mask 与 CAD 次序矛盾时不认证。不得假设 ROI 入口位于息肉外部；无深度的 Polyp 像素不能写整条空射线。首表面之后超过局部窄带为未知，不推出 inside。

`Omega_occ`：固定 CAD 首交比查询点更近的射线后段，或具有同等资格的已知前景代理遮挡。只表示该来源不能观察点，不是 Polyp 不存在的负票。几何点在 CAD 实体内部和点位于 CAD 后方是不同问题。本轮未认证新的背景遮挡实体。

`Omega_unknown`：没有合法有效表面/自由空间信息的其余域，包括域外投影、无有效深度、开放边界无符号区、对应关系未决等。Unknown 不等于正值、背景、物体内部或不存在。局部 CAD 遮挡和未知理由可同时记录；单一来源的输出主状态按 `INVALID_CAMERA/INPUT → CAD_OCCLUDED → CONFLICT/AMBIGUOUS → SURFACE_BAND → CONDITIONAL_FREE → UNKNOWN` 解释。跨来源状态不按此顺序强制覆盖，保留证据列表。

```python
# 仅接口规范；无对应可执行类
LocalField.query(X_mm) -> {
  "value": float_or_NaN, "field_kind": enum,
  "valid_surface": bool, "valid_free": bool,
  "occluded": bool, "unknown": bool,
  "source_id": str, "source_family": str,
  "reliability_proxy": {"camera": ..., "connectivity": ...,
                         "incidence": ..., "Type2": ..., "visibility": ...},
  "reason": [reason_codes],
  "original_face_id": int_or_null, "source_UV": uv_or_null,
  "native_depth_id": str, "camera_SHA256": str,
  "distance_unit": "mm", "sign_status": enum
}
```

无有效标量值时返回 NaN 和理由，不借其他路线、照片或历史测量补齐。`w_i` 是未校准质量代理，记录各因子，不能称正确概率。共享 RGB 祖先形成来源家族；家族计数限制重复证据，不能据此删掉互补单视角面。角色 CORE/BRIDGE/RESERVED 也不是质量真值。

## 八项资格测试及本轮证据边界

| 测试 | 后续必须成立的断言 | E3-A 状态 |
|---|---|---|
| 原始合法面 | 原面重心 UDF≈0，原始身份和像素往返闭合 | 36 源 ×3 点共108次查询；重心/±0.05mm 数值结果见 `E3_CONTRACT_QUERIES.csv`；不是全局符号验证 |
| 开放边界 | 不外推闭合内外；边缘最近面多解显式不确定 | 已统计原面开放边，合同冻结；完整 field 测试 NOT_RUN |
| Ring 遮挡 | 真 CAD 首交截断，后方不产生不存在负票 | 36 源实射线次序与定位记录；正 Mask 矛盾单列 |
| 深度断裂 | 原面身份/断裂阈值不重写；跨断裂不建立可信窄带 | 使用现存原面；长边仅代理；field 测试 NOT_RUN |
| 两个错误重叠层 | 不平均出不存在的第三层，允许冲突 | 有实际投影错层候选；“两层都错”无真值，NOT_EVALUABLE |
| 两个真实不同表面 | 不因距离近强制合并，遮挡保留 | CAD 前后次序可核查；息肉双真实表面身份 UNKNOWN |
| 单视角真实细柄 | 无第二视角不是反对票；保留独有支持及保护来源 | 已冻结 possible_stalk/Ring 代理；缺人工真实细柄标签，NOT_EVALUABLE |
| 无观测空间 | Unknown 不变 inside/outside/背景 | 两个固定121×121切片作有限原面距离/投影审计；没有构建 LocalField |

本轮 `.002 mm` 是既有渲染器的浮点首交排序余量；诊断错层阈值 `max(.5 mm,3Z/f)`、切片 `.25 mm`、点查询 `.05 mm` 只用于暴露证据，不是未来统一真面保护/修正预算。完整资格实验留待 PM 决定 E3-B 候选后执行。
