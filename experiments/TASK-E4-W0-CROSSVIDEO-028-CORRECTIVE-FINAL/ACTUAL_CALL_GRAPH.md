# ACTUAL_CALL_GRAPH

```
core/u028c.py --group G
 ├─ Ctx()                       runs/<G>/{input_manifest,w0,view_selection,ring,rgb_features,identities,h_initialization,triangulation,ba,evaluation,figures}
 ├─ w0_ensure()                 camera_mainline → 或正式 tools/run_w0_camera.py --output runs/<G>/w0
 ├─ ring_evidence()             dxy_mid.recover (历史)
 ├─ select_views()              Ring/RGB 独立 + 贪心角度覆盖
 ├─ build_views()               每组独立 cache（RGB 内容 SHA256）
 ├─ features019.features/landmarks
 ├─ build_identities()          features019.matches + 地标映射 + view-pair 投票 + 一对一
 ├─ ring_candidates()           Ring 残差向量 6-DoF 精化 + epipolar_score（行位置 FIT）
 ├─ triangulate_identities / triangulate_ref_only   (历史 019 逐轨迹)
 ├─ solve_pipeline(M2/M3b)      ba_core_r4
 ├─ reproj_stats / holdout_stats / ring_energy_all
 └─ figs_final.py               每组 8 面板 + 跨组图
tests/test_final_math.py        3 PASS / 1 SKIP
```
