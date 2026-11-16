# Code reuse map — frozen before Phase 1

The following are read-only sources. The new Phase-0 adapter only binds files and computes hashes; it does not duplicate DXY or Body mathematics.

| 新实验模块 | 复用的历史代码 / SHA256 | 是否直接复用 | 是否修改 | 修改原因 |
| --- | --- | --- | --- | --- |
| DXY 输入 | A1 `code/generate_dxy.py` `121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e`; official `dxy_mid.pipeline.measure_files`, pipeline `2671739527cf8433b58dd480a6f40302c13fe0ab2ab3474d09ad318d6a45146a` | Phase 1 planned direct API call | No | Must extend A1's 13-source mapping to these 75 sources. |
| 二维几何转换 | A1 `code/prepare.py` `b5b11e4f9ac73dac8ec3dd2d8262da96c692073b2f6e91009c548e31cdc153a0`, native `basis_px` formula at lines 21–23 | Planned direct matrix convention | No | E1 must preserve DXY native center/basis; no OpenCV refit. |
| 九参数模型 | A1 COARSE `code/models.py` `34edacc79bfda081efb0dd29117ff5794736d2369529e336ff1c109d8551f769` (`decode`, `sphere_mesh`) | Planned direct import/copy with SHA receipt | No | Required unified ellipsoid model. |
| 解析椭球投影 | A1 `code/losses.py` `780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7` (`ellipse_projection`) | Planned direct reuse | No | Mature analytic conic projection. |
| 二维损失 | A1 `code/losses.py` `780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7` (`signed_distance`, `target_data`, `two_d_parts`, `cad_visibility`) | Planned direct reuse | Adapter only | Current source binding differs; mathematical functions must remain unchanged. |
| 优化框架 | A1 `code/fitting.py` `a58b80f81853b4e6995a93dd8135a78b0623acd68c1ec00defa68a3f2081cf33` (`Problem`, bounded TRF) | Planned reuse | Adapter only | Omit `depth_parts` for Body-E; reject non-success / non-finite starts before selection. |
| 稳定性评价 | A1 `code/analyze.py` `d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d` | Planned reuse | No | Need multistart/mesh/SVD reporting. |
| 多视角选择 | 015 `code/prepare.py` `88e74d19f788e765818e2c77135248f315bbe0d58bc859962badb6623c445d9d` and `config/VIEW_SELECTION.json` `ea42fd86a6d010ceb0b734d5551d5b61cd2d416043eb95d9002a140df8d850a3` | Planned reuse of scoring/diversity logic | Candidate adapter only | 015's fixed same-video names cannot be copied. |
| 跨视频身份审计 | 021 `prepare021.py` `44e71b172ee94723e9f4c10ad3d55b5619f1978f86d86dd242194c1e87d1b505`; `identity021.py` `791de579b21aa82ff33b4a6438c1e7cd76ffe0d9f4bad737e19770530c6c4ac8`; `geometry021.py` `d50f2a061d03bf57c486d25b8476d2e6706703721e8fc95cdb95759f495d6942` | Planned read-only audit reuse | No | Evidence is G01-only; it does not certify other groups. |
| Phase-0 binding | New `code/phase0_audit.py` `d08758c69c4645e67fc1c8c9882c57fb8873519abfbd62cfa7bb834beb7fdd2f` | New audit-only adapter | N/A | Required because the task's named final pool file is absent and A1's mapping only covers 13 sources. It contains no measurement or fit mathematics. |

Phase 1 must record exact copied/imported source SHA256 again after its code is frozen.
