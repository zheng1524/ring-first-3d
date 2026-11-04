"""Freeze metadata and expanded observations before any formal optimization."""
from inputs import *
from mesh_basis import build
def farthest(uv,count):
    best=np.full(len(uv),np.inf);chosen=[];ix=int(np.argmin(((uv-uv.mean(0))**2).sum(1)))
    for _ in range(min(count,len(uv))):
        chosen.append(ix);best=np.minimum(best,((uv-uv[ix])**2).sum(1));best[chosen]=-1;ix=int(np.argmax(best))
    return np.array(chosen)
def main():
    assert not(R/'config/LOCKED_PROTOCOL.json').exists(),'Already frozen'
    sc=load(A1/'config/PROTOCOL.json')['scenes']
    pr=dict(task=R.name,parent_commit='4a09aedc669092d264f070ccac4fd12851097dd1',date='2026-11-04 Asia/Shanghai',scenes=sc,initials=['E1','E2'],seeds=[0,1],seed_meaning='same frozen A-selected E1/E2 P0; common deterministic optimizer gradient subsampling schedule',arms=['PMGR','C1_DIRECT_HIGH_DOF','C2_FREQ_ONLY_PROGRESSIVE'],supplemental=['C1_count_matched','C2_count_matched'],mesh=dict(icosphere_subdivisions=3,vertices=642,faces=1280,constant_template=True,P0_parameters_frozen=True),budgets=[12,44,128],steps_per_stage=40,total_gradient_evaluations=120,renderer='NVlabs/nvdiffrast 253ac4fcea7de5f396371124af597e6cc957bfae; CUDA; actual triangle silhouettes. Native axial first-depth via Open3D face selection and differentiable exact ray/triangle plane.',render_size=[320,180],depth_pool=512,depth_pairs=256,gradient_pairs=128,gradient_anchors=256,loss=dict(M=1.,D=1.,H=.1,Base=0.,Reg=.02,depth_sigma_mm=.25,hero_sigma_mm=.5,hero_bound_mm=2.,mask='balanced squared foreground fraction residual plus contour-distance-weighted silhouette residual; all source pixels pooled with conditional Ring-known mass',depth='native axial pair differences; censored rows unknown, never zero-as-valid; fixed denominator and coverage guard',H_definition='bounded closest-visible-triangle distance to same HERO source; not independent of D',frequency='squared normalized eigenvalue coefficient L2',unknown='4x P0 displacement regularization on initially unobserved vertices; identical all arms'),optimizer=dict(method='Adam proposal with exact accepted-state rollback; lr in coefficient mm',lr_mm=.02,betas=[.9,.999],line_search_trials=7,backtrack=.5,global_tolerance=1e-7,view_relative_tolerance=.05,view_absolute_tolerance=.01),trust=dict(tau_over_equivalent_diameter=.0125,tau_clip_mm=[.075,.2],max_total_displacement_over_diameter=.25,coverage_drop_absolute=.02,coverage_relative_to='both P0 and last accepted per-source',max_H_MAE_increase_mm=.1,min_face_area_ratio=.1,max_P0_normal_flip_dot=0.,ring_penetration_tolerance_mm=.01,ring_penetration='P0 collisions explicitly reported; allow no deeper existing penetration and no new vertex penetration; triangle collision proxy separately reported; cannot certify all continuous contacts',self_intersection='non-adjacent triangle intersection test at accepted candidates'),gate=dict(whitened_fd_mm=.01,fd_consistency_mm=.005,rank_relative_singular=1e-3,geometric_rank_relative=1e-8,independent_J_ratio_min=.05,visible_energy_fraction_min=.05,source_gradient_conflict_max=.35,minimum_J_norm=.01,single_view='allow with explicit low-confidence label; same unknown prior all arms',P0_tangent_in_J=True),P0_gate=dict(hard_agreement_min=.99,depth_p95_mm_max=.15,analytic_depth_p95_mm_max=.3,analytic_iou_min=.97,archive_native_roundtrip_px_max=1e-8,finite_nonzero_gradient=True),evaluation=dict(A_B_frozen=True,B_used_for_training=False,B_identity='CONDITIONAL_UPSTREAM_GATE_SELECTION',fixed_original_pixel_denominator=True,common_ray_paired=True,GT='NOT_EVALUABLE'),base='OFF all scenes: no currently qualified same-coordinate background/source chain; never Ring plane',no_class_dispatch=True,no_GT=True,no_camera_update=True,no_cleanup=True,no_neural=True,no_mode_search=True,stopping='fixed budget; retain last safe geometry even if rejected; hard coordinate/numerical/intersection failures stop affected arm only',comparison='primary candidate-matched; supplemental count-matched only posthoc counts, frequency prefix, no B selection')
    save('config/LOCKED_PROTOCOL.json',pr);manifest=[];audit=[]
    for scene,x in sc.items():
        for cid in x['A']+x['B']:
            n=cleaned(cid);s=source(cid);z=n['depth'];h,w=z.shape;mask=n['native_labels']==1
            dt=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE);jump=np.zeros(z.shape)
            for axis in [0,1]:
                for step in [-1,1]:jump=np.maximum(jump,abs(z-np.roll(z,step,axis)))
            safe=n['valid']&mask&(dt>2)&(jump<=.75)&(n['native_RGB'].min(2)<245);v,u=np.nonzero(safe);uv=np.c_[u,v];cad=cast(ringscene(scene),uv,n['Kn'],s['T'])[0];keep=z[v,u]<=cad+.05;uv=uv[keep];available=len(uv);uv=uv[farthest(uv,512)];zz=z[uv[:,1],uv[:,0]].astype(float)
            pairs=np.c_[np.arange(len(uv)//2),np.arange(len(uv)//2)+len(uv)//2];X=unproject(zz,s['T'],uv,n['Kn'])
            full=s['labels']==1;known=s['labels']!=2;known_mass=known.reshape(180,2,320,2).mean((1,3));fg_mass=(full&known).reshape(180,2,320,2).mean((1,3));target=fg_mass/np.maximum(known_mass,1e-15)
            weights=.5*fg_mass/max(1,fg_mass.sum())+.5*(known_mass-fg_mass)/max(1,(known_mass-fg_mass).sum())
            boundary=contour(full);adj=cv2.dilate((~known).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool);boundary=boundary[~adj[boundary[:,1].astype(int),boundary[:,0].astype(int)]]
            dm=np.ones(full.shape,np.uint8);dm[boundary[:,1].astype(int),boundary[:,0].astype(int)]=0;distance=cv2.distanceTransform(dm,cv2.DIST_L2,cv2.DIST_MASK_PRECISE);distance=cv2.resize(distance,(320,180),interpolation=cv2.INTER_AREA)
            np.savez_compressed(R/'inputs'/(cid+'.npz'),uv=uv,pixel_id=uv[:,1]*w+uv[:,0],z=zz,X=X,pairs=pairs,delta=zz[pairs[:,0]]-zz[pairs[:,1]],Kn=n['Kn'],K=s['K'],T=s['T'],target=target,known_mass=known_mass,weights=weights,contour_weight=np.minimum(distance/3,4)**2,cad=cast(ringscene(scene),uv,n['Kn'],s['T'])[0])
            au=dict(source=cid,scene=scene,role='A'if cid in x['A']else'B',tier=x['tier'],camera=GATE[cid]['qualification'],native_size=[w,h],original_size=[640,360],eligible_before_pool=available,pool_N=len(uv),pairs_N=len(pairs),cleanup=n['cleanup_state'],base='BASE_UNCERTAIN_OFF',full_mask_N=int(full.sum()),known_mask_N=int(known.sum()))
            audit.append(au)
            for key in ['RGB','Mask','pack','camera_file','source_points','mesh']:
                a=asset(CC[cid][key]);assert a['sha256']==CC[cid]['files'][key]['sha256'];manifest.append(a)
            manifest.extend([asset(CC[cid]['E1_actual_native']['path']),asset(CC[cid]['Ring_CAD']['path'])])
            if n['cleanup_path']:manifest.append(asset(n['cleanup_path']))
            print('POOL',cid,available,len(uv),flush=True)
        for initial in ['E1','E2']:
            b=build(p0(scene,initial));np.savez_compressed(R/'inputs'/f'{scene}_{initial}_basis.npz',**b);print('BASIS',scene,initial,'orth',float(b['raw_orth']),'overlap',float(b['tangent_overlap']),flush=True)
    table('metrics/INPUT_QUALIFICATION.csv',audit);save('assets_index/LOCAL_DATA_SOURCES.json',manifest);save('metrics/PURE_SOURCE_EXTRACTION.json',EXTRACTED);save('metrics/INPUT_AUDIT.json',audit)
    save('metrics/INITIAL_CONDITIONS.json',p0s());save('metrics/INPUT_FREEZE.json',dict(protocol=asset(R/'config/LOCKED_PROTOCOL.json'),inputs=[asset(p)for p in sorted((R/'inputs').glob('*.npz'))],initials=asset(A1/'metrics/PRIMARY_A_ONLY.json'),GT_reads=0))
if __name__=='__main__':main()
