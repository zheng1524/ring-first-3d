from common import *
def main():
    assert not(R/'config/GATE_A_PREREGISTERED.json').exists(),'DO_NOT_OVERWRITE_PREREGISTRATION'
    save('config/PROTECTED_START.json',protected_state());docs=[]
    for name in ['PM_E3N0_FEASIBILITY_AUDIT.md','PM_E3N0_PREREGISTRATION.md','CODEX_TASK_E3N0_GATE_A_DRAFT.md','PM_E3N0_GATE_BC_PREVIEW.md']:
        p=Path('/home/liu/下载')/name;assert p.exists(),name;docs.append(asset(p));(R/'docs'/name).write_bytes(p.read_bytes())
    task=Path('/home/liu/.codex/attachments/f8099439-be62-4ecc-a3bd-286ac47e79f4/Pasted text.txt');(R/'TASK.md').write_bytes(task.read_bytes())
    save('config/AUTHORIZATION_AND_DOCUMENTS.json',dict(user_task=asset(task),PM_documents=docs,user_approval='latest pasted user request explicitly grants Gate A; overrides DRAFT_NOT_APPROVED status only for A',B_C_D='NOT_APPROVED',new_environment_policy='task-local dependency target allowed; no main environment changes',GT=False))
    c=dict(task=R.name,parent_commit='d69ade170352d1b5a1e46239f9516ab38c575648',frozen_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),dtype='FP64 for analytic geometry; inherited FP32 Open3D raycast for CAD; output depth FP32',sources=IDS,CORE_directed_pairs=[[a,b]for a,b in [(CORE[0],CORE[1]),(CORE[1],CORE[0]),(CORE[0],CORE[2]),(CORE[2],CORE[0]),(CORE[1],CORE[2]),(CORE[2],CORE[1])]],conditional_pairs=[[a,b]for n in IDS[3:]for core in CORE for a,b in [(n,core),(core,n)]],point_protocol='ALL original native legal Polyp depth pixels, every identity retained; exceeds1000/source and covers all geometry strata',
        crop=dict(fraction_margin_each_side=.2,minimum_margin_native_px=16,output_WH=[320,240],aspect='smallest integer4k x3k virtual rectangle enclosing expanded bbox',frame_outside='virtual padding, never clip ROI',nearest='floor(inverse_affine_output_center+0.5), explicit original source pixel ID; no depth interpolation',pixel_affine="u'=a(u-u0+0.5)-0.5; v'=a(v-v0+0.5)-0.5; K'=A K",a_per_source=True),
        thresholds=dict(analytic_XYZ_max_mm=1e-5,analytic_target_projection_max_px=1e-4,Ring_roundtrip_max_mm=1e-5,CAD_order_epsilon_mm=.002,minimum_points_per_source=1000,minimum_thin_width_output_px=3,ROI_bbox_loss_max_N=0,invalid_depth_nonzero_max_N=0),
        thin_proxy='all local8-neighbour maxima of cv2 distance transform, width=2*DT; no connected component removed; proxy not certified anatomy; native predicted width and actual output width separately',
        metric_candidates=dict(N=128,n_features=17,count_shape=[128,128,128],margin='max(2mm, 10% of max source extent) each side, then cube',A='all native Polyp depths plus Ring CAD',B_DIAGNOSTIC_ONLY='native points within1mm of own original Raw Mesh, inherited D0 native/Raw disagreement criterion; no input removed',selection='NO automatic selection if far-point cube inflation or thin footprint problem; mark REQUEST_RESEARCHER_ROI_DECISION',inflation_diagnostic='compare all vs B cube side; >1.5x is an explicit warning proxy, not anatomical truth'),
        output_policy='No volume inference, no forward, no GT database; empty-shape/reset checks only; no fullROI dense scientific model',official_commit=NF_COMMIT,primary='shapenet_noise_005',backup='tanks_and_temples STATIC_ONLY',prohibited=dict(GPU=0,NeuralFusion_forward=0,Translator_forward=0,training=0,new_HERO=0,camera_changes=0,new_TSDF=0,GT=False))
    save('config/GATE_A_PREREGISTERED.json',c)
    # Verify only the inherited six-source files, not a new global asset audit.
    for r in MANIFEST['sources']:
        for a in r['assets'].values():assert sha(a['path'])==a['sha256'],a['path']
    save('config/REUSED_FUNCTIONS.json',REUSE)
    entries=[('historical View Partition','D0/VIEW_COVERAGE_SELECTION.csv','read inherited block IDs; fixed new order',D0/'VIEW_COVERAGE_SELECTION.csv'),('Camera Gate','CAMERA_QUALIFICATION.csv','read only, retain INSUFFICIENT_EVIDENCE',REPO/'experiments/TASK-CAMERA-GATE-G01-004-PILOT-001/CAMERA_QUALIFICATION.csv')]
    out=['# Actual code reuse matrix','', '| Original source | Actual function/interface | Reuse / thin adaptation | Duplicate implementation | File SHA256 |','| --- | --- | --- | --- | --- |']
    for r in REUSE:out.append('| '+r['path']+' | '+r['name']+' | exact AST extraction; bind task-local IO/whitelist only | No | '+r['file_SHA256']+' |')
    for n in ['scaled_intrinsics','project_camera','camera_rays','basis','configure']:
        p=REPO/'visualization/real_p0_renderer.py';out.append(f'| {p} | {n} | direct import unchanged | No | {sha(p)} |')
    p=REPO/'visualization/same_camera_scene.py';out.append(f'| {p} | SameCameraScene.cast/ring_image/scale_bar | direct unchanged | No | {sha(p)} |')
    for title,path,mode,p in entries:out.append(f'| {p} | {title} | {mode} | No | {sha(p)} |')
    out+=['','Only new geometry is the explicit per-view crop affine / identity sampler (crop.py). Existing source loader, native K, inverse projection, pinhole projection and CAD raycasting are executed unchanged. No D0 module main is imported, avoiding writes to D0 or its model-import guard. Original Raw Mesh is only a comparison/domain diagnostic, never a pseudo-depth input.','']
    (R/'CODE_REUSE_MATRIX.md').write_text('\n'.join(out));save('config/BEFORE_FORMAL_CALCULATION.json',dict(protocol=asset(R/'config/GATE_A_PREREGISTERED.json'),D0_manifest=asset(D0/'HERO_TSDF_INPUT_MANIFEST.json'),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],GT=False))
    print('GATE_A_PROTOCOL_FROZEN',flush=True)
if __name__=='__main__':main()
