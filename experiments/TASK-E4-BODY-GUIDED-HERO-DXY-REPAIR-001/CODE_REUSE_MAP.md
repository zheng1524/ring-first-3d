# 实际代码复用审计

| 新实验模块 | 历史代码 | 直接复用 / 修改 | 修改原因及实际调用 |
| --- | --- | --- | --- |
| DXY输入 | A1 generate_dxy.py + 官方pipeline | 官方API直接调用；A1 guard/sha/asset/clean AST原样执行；仅输入映射适配 | 75当前来源替代旧13来源CC；不读毫米输出 |
| 二维几何转换 | A1 prepare.py:22 | 原表达式逐字沿用 | q=(alluv-center)@inv(basis).T；75个basis roundtrip已检验 |
| 九参数模型 | A1 COARSE models.py | decode/sphere_mesh直接AST | 没有形态分支或新参数 |
| 解析椭球投影 | A1 losses.py | ellipse_projection/signed_distance直接AST | 未修改公式 |
| 二维损失 | A1 losses.py | target_data/cad_visibility/two_d_parts等直接AST | 未修改公式；保留全部Mask和Ring未知 |
| 优化框架 | A1 fitting.py:Problem.solve | solve方法AST原样挂载；Problem输入/residual适配 | 原solve不可直接构造旧CC，因此适配75视角，只拼2D+原prior，不调用depth_parts；新增资格选择器 |
| 稳定性评价 | A1 analyze.py | geom/sample_mesh/surface_distance/canonical_orientation/difference直接AST | 原样计算实际网格距离及等价旋转 |
| 多视角选择 | 015 prepare.py | skeleton_proxy直接AST；评分/贪心表达式复用到当前池 | 原main含历史Body中心及固定名单，不能直接执行；改Ring原点方向和独立源池，不读取旧Body |
| 跨视频身份审计 | 021 identity021.py:main | AST原样执行，输出重定向本任务 | 实际核验553观察/547链接；prepare021/geometry021只读审阅其坐标约定，不运行BA/变换 |
| 来源完整性 | A1 validate.py检查思路 | 当前格式检查适配 | 逐输入SHA、冻结、主解资格、实际初值公平性和固定分母均复核 |

求解/损失/投影函数保持原AST，无新旧数学差异；接口不同使历史main不能整体import（会创建旧目录并读旧CC/深度）。采用受限AST抽取只执行所列成熟函数，调用与原文件行号一致。335项数值契约包含native basis roundtrip、解析投影与实际网格射线深度、完整Mask保留、E1/E2同设置。来源binding/K仿射严格沿用旧prepare；跨视频新配准未执行。

所有直接调用函数的完整源码SHA256、AST SHA和行号如下；本轮源码冻结另见SOLVER_CODE_FREEZE.json。

| function | source | line | SHA256 | AST_SHA256 | direct |
| --- | --- | --- | --- | --- | --- |
| decode | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py | 8 | 34edacc79bfda081efb0dd29117ff5794736d2369529e336ff1c109d8551f769 | cc4d233ed192a7d2db7804d12d593620af74729249393f236d30d7315d4a3191 | YES: compile unmodified AST |
| sphere_mesh | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-COARSE-BODY-001/code/models.py | 12 | 34edacc79bfda081efb0dd29117ff5794736d2369529e336ff1c109d8551f769 | 843740922332f7e6c2af2a0c99c320a8774dfbb7f684c812d78747dcf26ee751 | YES: compile unmodified AST |
| contour | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/common.py | 62 | 43c14d95fe848cf6af22e94149aaf75755d8edb86cfee1c5300125b9858f0147 | 69b8c209fe875b8d975dc85f2472d8cae46e68da1d409ad145c41acab5a79b50 | YES: compile unmodified AST |
| mesh | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/common.py | 75 | 43c14d95fe848cf6af22e94149aaf75755d8edb86cfee1c5300125b9858f0147 | d2a9ba0691d7a60dd05acd0b97185a7f9f3517e8274de23a0921b54550752789 | YES: compile unmodified AST |
| ray_components | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/common.py | 77 | 43c14d95fe848cf6af22e94149aaf75755d8edb86cfee1c5300125b9858f0147 | 8ada7fd4e6b21084b2991f80c71eb7d34f087eb5e715e57aacaad5fee00545b5 | YES: compile unmodified AST |
| first_depth | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/common.py | 80 | 43c14d95fe848cf6af22e94149aaf75755d8edb86cfee1c5300125b9858f0147 | 5ff016470f07f33bc6d2dcf5c00a31e789b23bdc18c37a9b6b1175c6f42ef15b | YES: compile unmodified AST |
| camera_rays | /home/liu/polyp_research/ring-first-3d/visualization/real_p0_renderer.py | 98 | 16bbff24b353402f56833c87de19041c05c3f2482682d35ee8e24a36fea64f99 | 51e85fd4c5a9437abcdbd8eb1c10b72adadb5612bc29cae904074028319fd81a | YES: compile unmodified AST |
| camera_frame | /home/liu/ring_first_3d_e4_a1/experiments/TASK-E4-A1-COARSE-BODY-001/code/common.py | 87 | 0b8be9484b393ded060321f0990f609c4d3d3292bdeac46590de1d8b631dd28a | fea0382e19e10bc86c4d5858e4171ed745ae5a2d95ba7731c6ea3ae974074adc | YES: compile unmodified AST |
| mesh_scene | /home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/common.py | 106 | aa0c473057af6aa4e461fc8ec7ce56edf5c4340317f06c35620b9918ed4e491f | f4f4ea33cd11861aa57deef159437cb79a572d8918833058febffc5898db2475 | YES: compile unmodified AST |
| cast | /home/liu/ring_first_3d_e3n0_eight/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/code/common.py | 113 | aa0c473057af6aa4e461fc8ec7ce56edf5c4340317f06c35620b9918ed4e491f | e2f2132080035ee5968159129572620ebb9432b43da2807f43ce9ee219457f13 | YES: compile unmodified AST |
| robust | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 4 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | daba27d436fb5e792d90c46d24e4361e46638e9c73fa7c22281415c9ea5f988b | YES: compile unmodified AST |
| ellipse_projection | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 5 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | 975586f12991b3745fd654c7b72fd37408fab67b7d85aaafee4f184a7cd5f96a | YES: compile unmodified AST |
| signed_distance | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 12 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | b78e7233a901f32990514e2d269c8bebea795d64b6096afd1a358b6586fd4497 | YES: compile unmodified AST |
| field_sample | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 15 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | 227b44a75a8e135c501abcfe22864f170bc41d47e65d8a7e966c1be82c3dbc2a | YES: compile unmodified AST |
| distance_field_sample | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 17 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | a6b7186ca32159a73ea069942cfb46ff60caec9b5c600652c2acfebc25c9e8b7 | YES: compile unmodified AST |
| target_data | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 19 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | b15c3c39643b81c63a2c35a7efbb9f6c36a65383d54741d6b5b520837141c342 | YES: compile unmodified AST |
| cad_visibility | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 34 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | 2c71dae7d43457c4fe82b505798dc41edd5155a2312247fee1d237bc11476129 | YES: compile unmodified AST |
| two_d_parts | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/losses.py | 39 | 780e7148670bc41c044d9ba2fc7e72324eca571643a3dbe2e1ef4aaf6cb7d4d7 | 333e99558c56ff6ad08febcada4f9e0b533ed12edcbb0bf502ec5793dea852fa | YES: compile unmodified AST |
| skeleton_proxy | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py | 8 | 88e74d19f788e765818e2c77135248f315bbe0d58bc859962badb6623c445d9d | a0e7a8e00ba0987269d1f2c82efc94d240c8b80fd4f705165cbd2c02d1006f1a | YES: compile unmodified AST |
| Problem.solve | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py | 34 | a58b80f81853b4e6995a93dd8135a78b0623acd68c1ec00defa68a3f2081cf33 | 93b4629cb334c7560036c9c8e733540076dd24f9bf03f198201e0af39a2aed86 | YES: compile unmodified AST |
| geom | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/analyze.py | 4 | d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d | 641c0ee773150f6783710b4cb6768af3548c64f1e6d2135d3462706c2e43637a | YES: compile unmodified AST |
| sample_mesh | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/analyze.py | 5 | d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d | f48f7e8ba58ad249437d004d2c276ba354a085d47a967a583789f566c5148385 | YES: compile unmodified AST |
| surface_distance | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/analyze.py | 7 | d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d | 990e901c19027532af1f5983f5f0730f792b061d8a3da4cf0c4372553fbc438a | YES: compile unmodified AST |
| canonical_orientation | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/analyze.py | 9 | d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d | c145d7dcc3d967dec3a081513b0f2ef0ff3eff94defe27a1ad62afe602d9d0c6 | YES: compile unmodified AST |
| difference | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/analyze.py | 13 | d3db0b4c112d805373f27eff660bdc51f4162a07b5466f13f9ddfdace89feb7d | 8f872f8f7c43a38ae93fa637eda65db496c50bcc4a147e70bde03689b98fe6b5 | YES: compile unmodified AST |
| sha | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py | 7 | 121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e | 3d6744d313854ed7399df0b5e7098c44345b6c92ff94dd815f2e448dffc055d7 | YES: compile unmodified AST |
| asset | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py | 8 | 121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e | dd7be15251dda478d2e403fdbcab7417f745231a51ef04c268fc22eb6ff89031 | YES: compile unmodified AST |
| clean | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py | 10 | 121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e | 805d68485ffa72a516ac13b452b875e914760a1dc6fb7dd749d88f37c3470a61 | YES: compile unmodified AST |
| guard | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py | 17 | 121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e | 891c1d12c885e1d64c27d5f08586591a9bd31a3145d7f88a3102e37a9207b435 | YES: compile unmodified AST |
| main | /home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/identity021.py | 4 | 791de579b21aa82ff33b4a6438c1e7cd76ffe0d9f4bad737e19770530c6c4ac8 | 3b6de0deffe249fc688b5987d242a62fef0ba59add6ac89e6d9ff8b35499082f | YES: compile unmodified AST |


## 适配的整文件源码SHA

| file | SHA256 |
| --- | --- |
| experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py | 121db446359b633ef8f4edb9018ce82fcfa575b6898dadef397758d25239128e |
| experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/prepare.py | b5b11e4f9ac73dac8ec3dd2d8262da96c692073b2f6e91009c548e31cdc153a0 |
| experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/fitting.py | a58b80f81853b4e6995a93dd8135a78b0623acd68c1ec00defa68a3f2081cf33 |
| experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/validate.py | 119074ad2fb960d52efe6fed9b24d430854ce20f533ab4dc54f65b5b9c15dfd0 |
| experiments/TASK-E4-MULTIVIEW-INIT-STALK-015/code/prepare.py | 88e74d19f788e765818e2c77135248f315bbe0d58bc859962badb6623c445d9d |
| experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/prepare021.py | 44e71b172ee94723e9f4c10ad3d55b5619f1978f86d86dd242194c1e87d1b505 |
| experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/geometry021.py | d50f2a061d03bf57c486d25b8476d2e6706703721e8fc95cdb95759f495d6942 |
| experiments/TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/code/prepare.py | e90e06ef0cda4764ad162bc5c112198623403be9d5ca5f71365348c4ccad6390 |
