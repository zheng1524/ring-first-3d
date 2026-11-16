"""Correct Phase 0: exact predecessor source/cache binding and native K transport."""
from common import *
from collections import Counter

def main():
    assert not (R/'provenance/ALL_PREDICTIONS_FROZEN.json').exists()
    # Preserve the earlier incomplete audit verbatim before superseding it.
    arc=R/'provenance/SUPERSEDED_PHASE0'
    if not arc.exists():
        arc.mkdir()
        for name in ['01_PROTOCOL.md','METHOD_AND_INPUT_AUDIT.md','CODE_REUSE_MAP.md','VIEW_INVENTORY.csv','provenance/PHASE0_INPUT_FILES.json','provenance/PHASE0_SOURCE_BINDING.json','code/phase0_audit.py']:
            (arc/Path(name).name).write_bytes((R/name).read_bytes())
    guard('prepare')
    poolpath=ASSETS/'TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/config/FINAL_CAMERA_POOL.json'
    pool=load(poolpath);ss=load(OLD/'config/SOURCES.json');rows=[];bound=[];files=[]
    assert len(ss)==75
    for s in ss:
        meta=load(s['source']);cc=[v for v in pool if v['id']==s['view_id'] or s['view_id'] in v.get('aliases',[])]
        exact=[v for v in cc if v.get('RGB_SHA256')==meta.get('target_SHA')];cc=exact or cc
        assert len(cc)==1,s['id']
        v=cc[0];cache=s.get('target_cache') or v['cache'];a=np.load(cache)
        # Deliberately access K/T only, never X/z/normal from the HERO observation.
        o=np.load(s['obs']);rgb=a['RGB'];lab=a['labels'];h,w=lab.shape;nh,nw=map(int,o['native_shape'])
        A=np.diag([w/nw,h/nh,1.]);A[:2,2]=np.array([w/nw,h/nh])*.5-.5;K=A@o['K'];C=o['T'].copy()
        assert rgb.dtype==lab.dtype==np.uint8 and rgb.shape==(360,640,3) and lab.shape==(360,640)
        assert set(np.unique(lab))=={0,1,2};assert np.isfinite(C).all() and abs(np.linalg.det(C[:3,:3])-1)<1e-6
        assert np.max(abs(K-a['K']))<1e-7
        rc=load(ASSETS/'TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs'/s['group']/'CASE.json')
        ring=rc['ring'];diam={'R5':5.,'R10':10.}[ring]
        # The 29 OLD018 observations intentionally retain their original frozen pose.
        # The final pool is a qualification/binding reference, not an authorization to update it.
        dc=None if v.get('C') is None else float(np.linalg.norm(C[:3,3]-np.array(v['C'])[:3,3]))
        polyp=lab==1;dt=distance_transform_edt(polyp);sk=skeleton_proxy(polyp)
        sharp=float(cv2.Laplacian(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),cv2.CV_64F).var())
        complete=1-float(np.r_[polyp[0],polyp[-1],polyp[:,0],polyp[:,-1]].mean())
        thin=float((sk&(dt<max(2.,float(dt.max())*.25))).sum()/max(1,np.sqrt(polyp.sum())))
        ringfree=1-float((lab==2).sum()/max(1,(lab>0).sum()));direction=C[:3,3]/np.linalg.norm(C[:3,3])
        rgbsha=hashlib.sha256(rgb.tobytes()).hexdigest();masksha=hashlib.sha256(lab.tobytes()).hexdigest()
        file_rgb=Path(v['RGB_source']);file_mask=Path(v['Mask_source']);bgr=cv2.imread(str(file_rgb));fm=cv2.imread(str(file_mask),cv2.IMREAD_UNCHANGED)
        same_files=bgr is not None and fm is not None and np.array_equal(bgr[:,:,::-1],rgb) and np.array_equal(fm,lab)
        r=dict(source_id=s['id'],view_id=s['view_id'],group=s['group'],video=s['video'],capture_type=v['capture_type'],role=s['role'],cache=asset(cache),RGB_source=asset(file_rgb),Mask_source=asset(file_mask),RGB_content_SHA=rgbsha,Mask_content_SHA=masksha,binding='view_id+target_SHA' if exact else 'unique_view_id+verified_cache',labels=[0,1,2],shape=[h,w],K=K,C=C,K_native=o['K'],native_shape=[nh,nw],native_to_cache=A,pose_origin=asset(s['obs']),pose_fields_read=['K','T','native_shape'],pool_C=v.get('C'),pool_status=v.get('status'),pool_formal=v.get('formal',False),pool_pose_delta_mm=dc,ring=ring,inner_diameter_mm=diam,ring_source=asset(ASSETS/'TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs'/s['group']/'RING.npz'),DXY_entrypoint='measure_files' if same_files else 'measure_frame',sharpness=sharp,mask_complete_proxy=complete,thin_structure_visibility_proxy=thin,Ring_free_fraction=ringfree,direction=direction,coordinate_pool=s['group']+'_'+s['video'],geometry_status='CONDITIONAL_FROZEN_CAMERA_NOT_GROUND_TRUTH',raw_metadata=v)
        bound.append(r)
        np.savez_compressed(R/'inputs'/(s['id']+'.npz'),RGB=rgb,labels=lab,K=K,T=C)
        rows.append({k:r[k] for k in ['source_id','view_id','group','video','capture_type','binding','RGB_content_SHA','Mask_content_SHA','shape','K','C','native_to_cache','pool_status','pool_formal','pool_pose_delta_mm','ring','inner_diameter_mm','DXY_entrypoint','sharpness','mask_complete_proxy','thin_structure_visibility_proxy','Ring_free_fraction','direction','coordinate_pool']})
        files.extend([r['cache'],r['RGB_source'],r['Mask_source'],r['pose_origin'],r['ring_source']])
    save('config/SOURCE_BINDING.json',bound);table('VIEW_INVENTORY.csv',rows)
    save('provenance/INPUT_SHA.json',list({x['path']:x for x in files}.values()))
    save('provenance/PHASE0_CORRECTION.json',dict(epoch=time.time(),error='Previous audit looked only in the cloned Git checkout and used RAW initial_pose. FINAL_CAMERA_POOL exists in original asset workspace; all75 have native K/T.',final_pool=asset(poolpath),sources=asset(OLD/'config/SOURCES.json'),camera_policy='unchanged OBS_TRUSTED K/T transported by exact predecessor half-pixel affine; pool_C disagreements logged not overwritten',counts=Counter(x['group'] for x in ss),GT_read=False,HERO_XYZ_read=False,history_fallback=0))
    save('provenance/CODE_REUSE_FUNCTIONS.json',REUSE)
    print('PREPARED',len(bound),'all frozen native poses',Counter(x['DXY_entrypoint'] for x in bound),flush=True)

if __name__=='__main__':main()
