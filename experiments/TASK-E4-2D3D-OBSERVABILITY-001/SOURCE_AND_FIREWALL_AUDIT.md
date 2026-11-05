# 来源与GT防火墙审计

本轮为原生CAD N0，非前两轮人工法向/同核目标。仅Gate A；五视角来自一个静止Blender场景，不是五个不同原生病例。原生GT没有四参数q_GT。

|角色|路径|SHA256|单位|优化器可读|
|---|---|---|---|---|
|native CAD GT generation source|/home/liu/polyp_research/experiments/geometric_validation_v1/assets/IIa6.5.blend|5119f02ca976399a33d3dccccb8212e01489ce27605e22ae9753af7fd786aab1|source vertices meters; world vertices ×1000 then frozen rigid centering, no local edit|False|
|native target mesh|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/audit_only/NATIVE_CAD_GT.npz|d9ddcd09a07dafda8f517f22806411bd99f4bdc54110dd3a8ad71e0c8d4b0c1e|mm|False|
|independent P0 field|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE_FIELD.npz|f34fa3f21b668566ab20e2c85fc284941df96a37a5d719588ce2f86fdc845d2e|mm SDF from Ring-only ellipsoid|True|
|independent P0 mesh|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE_SOURCE_MESH.npz|34a47793aad14708c591ad453a9fc1f07d954d26b665f4b6ce33bc8ae0013058|mm, DMTet|True|
|Ring CAD|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/RING_CAD.npz|3e55938b82f88bf4f32b960c2a499d465a0d0e4a5673108bcfc105e648e9ec3a|mm|True|
|frozen cameras|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/CAMERAS.json|e7bba6fa4667902ffc8fa2a02dc1a6c1aa1b087263a28a987b51a214e99e2eb6|c2w translation mm, K pixel-center and edge conventions explicit|True|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE__IIa6.5_R10_obs00.png|b07ba096d5b65769dbb1bc5fe0161bb8a541793a7311496f0e3f2a6661cdaf34|native 640x360 pixel centers|False|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE__IIa6.5_R10_obs01.png|0711895806bb669bd886e43d8b63a1ea186f0d579a6eeea3cf57d4995a5d4ff6|native 640x360 pixel centers|False|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE__IIa6.5_R10_obs03.png|21ba250a4bb1d232cfce0c26143064cc0426abc6c266d3aec4087e4eb1b901db|native 640x360 pixel centers|False|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE__IIa6.5_R10_obs04.png|2705f0627ec2f67a9401088987e8f704dd5ba576a598c896a63ebac5ab30f790|native 640x360 pixel centers|False|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/BASE__IIa6.5_R10_obs05.png|074e636538629ccd0214f10607385e84ea225cb7e889bbe6b3cb44f51ddb8395|native 640x360 pixel centers|False|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/TARGET__IIa6.5_R10_obs00.png|daa097773b4d8160aa00921f2aeb873454b8a557e841b6b6b2151ca5b0bf3e02|native 640x360 pixel centers|True|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/TARGET__IIa6.5_R10_obs01.png|d8e23d681e5bf059a5c11bf6b19e50dc0a28fa1d9e4b5ba70cf4731fe041a776|native 640x360 pixel centers|True|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/TARGET__IIa6.5_R10_obs03.png|3ef57509ed8b0b68e91ede85431d14b8d134f327462e66afa4699a52354c65d9|native 640x360 pixel centers|True|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/TARGET__IIa6.5_R10_obs04.png|b5c65259db8e394502a1e91948e89ed02702ee71466c6800beae7addd27e7ee6|native 640x360 pixel centers|True|
|actual fixed-scene Blender emission label; not clinical RGB|/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-2D3D-OBSERVABILITY-001/inputs/TARGET__IIa6.5_R10_obs05.png|2ecc359c3460108ee5b60424851c8f37df4d64f6f309f0749b2cc2165b911df7|native 640x360 pixel centers|True|

P0为新建独立低维椭球，由Ring内半径5mm的固定比例规则产生，非原生CAD底场，非某个真实病例的跨坐标P0。九参数定义冻结初始化，优化只更新局部四参数。h=.15mm、核半径1.8mm，无半径搜索；旧1.82mm来自旧控制对象尺寸，未用于N0。

相机实际水平视场66.787223°，与名义70°不符。用户已允许选择一致实现，因此保留冻结K/c2w字节，以实际K渲染全部目标和预测。K_edge主点减0.5得到整数像素中心K；c2w_blender=c2w_cv×diag(1,-1,-1,1)，所有几何mm。BASE/TARGET×5投影和Ring门禁均通过，源原始.blend不保存。

防火墙实测拒绝本轮GT、旧GT、旧原生CAD生成BASE_FIELD及.blend，允许本轮独立P0、Ring、相机和二维标签。旧同核GT只在独立的A2诊断脚本中读取，不能在N0优化进程读取。留出目标只做逐轮评价，不进入损失或选模。

开发期旧控制诊断曾出现一个root路径适配遗漏、读到本轮目标Mask；未运行优化，错误输出已封存runtime/PREFLIGHT_WRONG_MASK_ROUTING.*，修复后增加旧GT/FINAL原损失与已冻结历史值逐项一致断言，只有通过回归的诊断才进入最终结果。N0默认root及投影门禁不受此路由遗漏影响。
