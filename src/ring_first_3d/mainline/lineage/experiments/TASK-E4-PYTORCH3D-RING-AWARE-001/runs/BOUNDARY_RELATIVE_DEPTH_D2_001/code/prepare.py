from common import *
import shutil,subprocess
PREV=R.parent/'PROGRESSIVE_HERO_001'
SIM=Path('/home/liu/polyp_research/experiments/realistic_simulation_mask_v2/scenes')
PM=Path('/home/liu/ring_first_3d_e4_pmgr/experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001')
E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001')
GATE=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001/config/CAMERA_GATE_RESULTS.json')
def main():
    manifest=[]
    def record(p):manifest.append(asset(p))
    def copy(p,q):
        q=R/q;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(p,q);record(p)
    cases=['virtual_IIa','virtual_Ip','virtual_Is','real_Ip','real_IIa','real_Is']
    cfg=dict(task='TASK-E4-D2',run=R.name,cases=cases,seed=20261106,steps=300,checkpoints=[0,25,50,75,100,150,200,250,300],arms=['B','E1','E2','E3'],optimizer=dict(name='SGD',lr=1.,momentum=.9),mode='LOCAL_VERTEX_ONLY',relative_weights=dict(edge=1.,laplacian=1.,normal=.01,unsupported=.01),depth=dict(weight=.01,sigma_mm=.5,Huber_cap_r=10.,miss_cost=9.5,min_ray_face_cosine=.001,CAD_clearance_mm=.05),boundary=dict(rule='w=0.1+0.9*(1-exp(-(d/8)^2)); d=min(distance to Background,distance to Ring) on original RGB label lattice; pixel-center EDT; no resized-mask distances',scale_px=8.,floor=.1),relative_depth=dict(weight=.01,sigma_mm=.5,Huber_cap=9.5,interior_weight_min=.5,scales_native_px=[4,16,48],max_pairs_per_scale=128,path_max_adjacent_jump_mm=.5,min_pixel_separation=2,missing_pair_cost=9.5),stop=dict(max_gradient_norm=100.,max_candidate_step_mm=2.,volume_ratio_range=[.1,10.]),GT='virtual ideal depth generation and independent projection audit only; 3D evaluation after prediction freeze',multiview_HERO='diagnostics after prediction freeze only; never optimization, weighting, selection or ranking',reuse_B=['virtual_IIa','real_Ip'],model_selection='fixed step300 only; no best checkpoint')
    save('config/PROTOCOL.json',cfg)
    protect=[asset(p)for p in sorted(PREV.rglob('*'))if p.is_file()and not any(x in p.parts for x in ['runtime','__pycache__'])]
    save('assets_index/HISTORY_PROTECTION.json',protect)
    for name,old in [('virtual_IIa','virtual'),('real_Ip','real')]:
        for p in sorted((PREV/'inputs'/old).glob('*')):
            if p.is_file():copy(p,Path('inputs')/name/p.name)
        c=load(R/'inputs'/name/'CASE.json');c.update(name=name,case_kind='virtual'if name.startswith('virtual')else'real',morphology='IIa'if name=='virtual_IIa'else'Ip');save(Path('inputs')/name/'CASE.json',c)
        for v in c['views']:copy(PREV/'depth_observations'/(v['id']+'.npz'),Path('depth_observations')/(v['id']+'.npz'))
    # New virtual cases: original static body; fixed Ring pose from obs01, archived cameras.
    audit=load(REPO/'experiments/E4-SDF-LOCALIZATION-BLENDER-001/assets_index/SOURCE_AUDIT.json')
    for name,key in [('virtual_Ip','Ip4'),('virtual_Is','Is14')]:
        src=next(x['source']for x in audit['models']if x['model']==key);assert sha(src['path'])==src['sha256'];record(src['path']);seed=load(SIM/(key+'_R10_obs01/scene.json'));views=[];cams=[]
        for i in [0,1,3,4,5]:
            a=load(SIM/(key+f'_R10_obs{i:02d}/scene.json'));record(SIM/(key+f'_R10_obs{i:02d}/scene.json'));T=np.eye(4);E=np.eye(4);E[:3]=a['world_to_camera_cv'];T=np.linalg.inv(E);Ke=np.array(a['K']);K=Ke.copy();K[:2,2]-=.5;cid=a['source_id'];role='FIT'if i in[1,3,5]else'UPDATE_HOLDOUT'
            cams.append(dict(id=cid,K_edge=Ke,K_pixel_center=K,c2w_mm=T,width=640,height=360,role=role));views.append(dict(id=cid,role=role,qualification='KNOWN_BLENDER_CAMERA',width=640,height=360))
        save(Path('config')/(name+'_SCENE.json'),dict(source=src,ring_scene='/home/liu/polyp_research/ring_anchor_3d/assets/scene.blend',ring_center_mm=seed['ring_center_mm'],cameras=cams,source_native_to_mm=1000,body_centering='XY bounding center; Z minimum0, unchanged historical export',Ring_pose_fixed_to='obs01',all_views_same_static_scene=True))
        save(Path('inputs')/name/'CASE.json',dict(name=name,case_kind='virtual',morphology='Ip'if key=='Ip4'else'Is',identity=key+'_R10',views=views,unit='mm',initialization='same generic Ring-only Gate A ellipsoid translated with Ring; no GT-dependent fitting',GT='IDEAL_GT_DEPTH_UPPER_BOUND plus posterior geometry'))
    sources={c['id']:c for c in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']};gate={c['source']:c for c in load(GATE)['sources']};record(GATE)
    for name,group,kind,fit,hold in [('real_IIa','G06_004','IIa',['G06_004_growth_r01','G06_004_growth_r03'],['G06_004_growth_r06']),('real_Is','G07_004','Is',['G07_004_ref04','G07_004_growth_r02'],['G07_004_new_r06'])]:
        out=R/'inputs'/name;out.mkdir(exist_ok=True);a=np.load(PM/'inputs'/(group+'_E2_basis.npz'));np.savez_compressed(out/'INITIAL.npz',V=a['V'],F=a['F']);record(PM/'inputs'/(group+'_E2_basis.npz'))
        s=sources[fit[0]];ring=trimesh.load(s['Ring_CAD']['path'],process=False);np.savez_compressed(out/'RING.npz',V=ring.vertices,F=ring.faces);record(s['Ring_CAD']['path']);views=[]
        for cid in fit+hold:
            s=sources[cid];g=gate[cid];assert g['admission']!='NOT_ADMITTED';assert g['Ring_pass'];
            if cid in fit:assert g['qualification']=='CONDITIONAL_USABLE'
            rgb=np.array(Image.open(s['RGB']).convert('RGB'));lab=np.array(Image.open(s['Mask']));p=np.load(s['pack']);assert np.array_equal(lab,p['labels']);T=p['pose'];K=p['K'];cache=np.load(PM/'inputs'/(cid+'.npz'));assert np.allclose(T,cache['T'])and np.allclose(K,cache['K']);np.savez_compressed(out/(cid+'.npz'),RGB=rgb,labels=lab,K=K,T=T)
            # Fixed old PMGR observation IDs; same raw depth, no cross-view filtering.
            raw=np.load(s['E1_actual_native']['path']);uv=cache['uv'];z=cache['z'];assert np.array_equal(z,raw['depth_mm'][uv[:,1],uv[:,0]]);assert np.array_equal(cache['pixel_id'],uv[:,1]*640+uv[:,0]);Kn=cache['Kn'];from evaluate import pointcast
            X=(np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T*z[:,None])@T[:3,:3].T+T[:3,3];mapped=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;mapped=mapped[:,:2]/mapped[:,2:];px=np.rint(mapped).astype(int);_,_,rz=pointcast(scene(ring.vertices,ring.faces),X,Kn,T);ok=(lab[px[:,1],px[:,0]]==1)&np.isfinite(z)&(z>0)&(z<rz-.05)
            np.savez_compressed(R/'depth_observations'/(cid+'.npz'),uv=uv[ok],pixel_id=cache['pixel_id'][ok],z=z[ok],K=Kn,T=T,weight=np.ones(ok.sum()),native_shape=raw['depth_mm'].shape)
            views.append(dict(id=cid,role='FIT'if cid in fit else'UPDATE_HOLDOUT',qualification=g['qualification'],admission=g['admission'],block=g['block'],width=640,height=360))
            for pp in[s['RGB'],s['Mask'],s['pack'],s['E1_actual_native']['path'],PM/'inputs'/(cid+'.npz')]:record(pp)
        save(Path('inputs')/name/'CASE.json',dict(name=name,case_kind='real',morphology=kind,identity=group,views=views,unit='mm',initialization='exact frozen PMGR E2 P0 V/F; update-stage holdout only',GT='NOT_EVALUABLE'))
    save('assets_index/SOURCE_MANIFEST.json',manifest);save('config/CASE_LOCK.json',[getcase(n)for n in cases])
    print('PREPARED_CASES',cases)
if __name__=='__main__':main()
