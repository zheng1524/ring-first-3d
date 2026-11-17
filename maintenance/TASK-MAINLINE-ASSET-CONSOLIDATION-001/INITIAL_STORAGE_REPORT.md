# 初始存储盘点

来源分支与远端均核验为bac3fc89ef95db522b63cf6bb98e6914b9382864。初始df显示197G文件系统已用187G、普通用户可用0。只读扫描在首次删除之前完成，输出先写/dev/shm。

逐文件盘点 276183 个资产，逻辑字节 53,135,662,730；该数字包含重复副本，不能当物理占用。范围为所有ring_first_3d*目录、独立ring-first-hero-core及受保护宿主的科研资产；.git对象另计，虚拟环境/node_modules另作外部依赖，未删除。

大文件阈值计数：{"1000000": 7746, "10000000": 174, "100000000": 12}。完整SHA、Git跟踪状态、初始保留决策和静态引用在ASSET_INVENTORY.csv/json及DEPENDENCY_REFERENCE_GRAPH.json。初始KEEP是未审查前的默认保护，最终决策以PHASE1_DELETE_MANIFEST/CLEANUP_CANDIDATES为准。

df、du、最大200项、Git对象/分支/worktree原始输出见INITIAL_COMMANDS.json。文件系统保留块使初始f_bfree仍有10,814,566,400字节而f_bavail为0，报告分别记录。

|工作区|文件数|逻辑字节|
|---|---:|---:|
|/home/liu/ring_first_3d|575|153668907|
|/home/liu/ring_first_3d_ab_scene|595|154210878|
|/home/liu/ring_first_3d_abs_density|514|192527418|
|/home/liu/ring_first_3d_boundary_growth|7843|1200894882|
|/home/liu/ring_first_3d_camera_gate|392|71654143|
|/home/liu/ring_first_3d_contour_guided_init_a|44191|3461746767|
|/home/liu/ring_first_3d_e3_sdf_4090|2998|905691903|
|/home/liu/ring_first_3d_e3_sdf_full|2771|638488040|
|/home/liu/ring_first_3d_e3_sdf_multi|2916|957423813|
|/home/liu/ring_first_3d_e3a|220|38439821|
|/home/liu/ring_first_3d_e3b|225|28151038|
|/home/liu/ring_first_3d_e3c|486|93339340|
|/home/liu/ring_first_3d_e3d0|425|154014339|
|/home/liu/ring_first_3d_e3n0|707|348619605|
|/home/liu/ring_first_3d_e3n0_a2|326|87791903|
|/home/liu/ring_first_3d_e3n0_a3|806|311812013|
|/home/liu/ring_first_3d_e3n0_eight|3010|729659111|
|/home/liu/ring_first_3d_e3n0_gate_b|2879|426038851|
|/home/liu/ring_first_3d_e4_a1|3036|540609758|
|/home/liu/ring_first_3d_e4_e1e2|3192|565729756|
|/home/liu/ring_first_3d_e4_ffd|4146|624552498|
|/home/liu/ring_first_3d_e4_pmgr|7308|1003187358|
|/home/liu/ring_first_3d_e4_pmgr_r1|3288|598230825|
|/home/liu/ring_first_3d_e4_sdf_evolution|5098|750467907|
|/home/liu/ring_first_3d_e4_sdf_localization|70012|10244778283|
|/home/liu/ring_first_3d_g01_dualvideo|613|37662894|
|/home/liu/ring_first_3d_g01_multisurface|3402|694111582|
|/home/liu/ring_first_3d_g01_sim_rev1|1167|201345274|
|/home/liu/ring_first_3d_grazing|937|226165902|
|/home/liu/ring_first_3d_growth_recovery|4487|133809032|
|/home/liu/ring_first_3d_harness|441|118839896|
|/home/liu/ring_first_3d_harness_main_ready|76|1119991|
|/home/liu/ring_first_3d_incremental|638|264239829|
|/home/liu/ring_first_3d_multisurface_stress|3652|972365953|
|/home/liu/ring_first_3d_multivideo_init_a|6659|865620101|
|/home/liu/ring_first_3d_neural_e0|3471|151471037|
|/home/liu/ring_first_3d_neural_e1|1314|213413635|
|/home/liu/ring_first_3d_neural_e2|171|38847638|
|/home/liu/ring_first_3d_neural_e2_cpu|168|6125149|
|/home/liu/ring_first_3d_neural_e2p5|139|11625685|
|/home/liu/ring_first_3d_neural_e2p6|142|4441529|
|/home/liu/ring_first_3d_neural_e2p7|178|34541087|
|/home/liu/ring_first_3d_panel2_depth|563|114253787|
|/home/liu/ring_first_3d_phase_d|575|193992024|
|/home/liu/ring_first_3d_policy_bootstrap|433|4530347|
|/home/liu/ring_first_3d_pose_depth|3058|604421012|
|/home/liu/ring_first_3d_scene_vis|187|104244073|
|/home/liu/ring_first_3d_structural_update|26849|5837666429|
|/home/liu/ring_first_3d_structured_body_002|2361|557915336|
|/home/liu/ring_first_3d_synthetic_correspondence|1257|121582197|
|/home/liu/ring_first_3d_view_eval|514|91815500|
|/home/liu/ring_first_3d_view_partition|1098|283150209|
|/home/liu/ring-first-hero-core|419|52425570|
|/home/liu/polyp_research/ring-first-3d|15553|1427698258|
|/home/liu/polyp_research/ring_anchor_3d|25655|15300902356|
|/home/liu/.cache/mozilla|412|83954210|
|/home/liu/.cache/google-chrome-headless|95|78320203|
|/home/liu/.cache/google-chrome|1143|13124340|
|/home/liu/.cache/pip|8|922|
|/home/liu/.cache/thumbnails|389|8190586|
