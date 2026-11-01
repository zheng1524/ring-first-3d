"""Identity/cache inventory and preregistration, before any metric or fitting."""
from common import *
def main():
    assert git(REPO,'merge-base',cfg['parent_commit'],'HEAD')==cfg['parent_commit']
    assert not (R/'config/BEFORE_FORMAL_RUN.json').exists(),'protocol already frozen'
    save('config/PROTECTED_START.json',protected_state())
    files=input_manifest();rows=[];legacy={v['id']:v for v in load(LEG/'inputs/views.json')}
    for cid in IDS:
        s=source(cid);c=CC[cid];T=s['T'];assert np.linalg.norm(T[:3,:3].T@T[:3,:3]-np.eye(3))<1e-8 and abs(np.linalg.det(T[:3,:3])-1)<1e-8
        if c['reference'] in legacy:
            v=legacy[c['reference']];assert v['RGB_SHA256']==sha(c['RGB']) and v['Mask_SHA256']==sha(c['Mask'])
        rows.append(dict(camera_id=cid,reference=c['reference'],frame_binding=c['frame_binding'],RGB=asset(c['RGB']),Mask=asset(c['Mask']),K=s['K'],c2w=s['T'],coordinate_frame=c['coord_frame'],raw_video_sequential_identity_certified=False,original_qualification=c['source_camera_qualified']))
    plan=[]
    for a,b in PAIRS:
        methods=[]
        for method in cfg['matching_methods_priority']:
            found=None;reverse=False
            for aa,bb in [(a,b),(b,a)]:
                p=LEG/'observations'/f'{method}_{CC[aa]["reference"]}__{CC[bb]["reference"]}.npz'
                if p.exists():found=p;reverse=aa!=a;break
            if found is None and set([a,b])==set([IDS[0],NEW[0]]) and method in ['SIFT','MASt3R']:
                p=PART/'local_results/matches'/('G01_004_adjacent_new_'+('MASt3R_FULL' if method=='MASt3R' else method)+'.npz')
                if p.exists():found=p;reverse=a!=IDS[0]
            if found:
                methods.append(dict(method=method,kind='EXISTING_RGB_MATCHES',asset=asset(found),reverse=reverse));files.append(asset(found))
            elif method=='SIFT':methods.append(dict(method=method,kind='NEW_CPU_SIFT',asset=None,reverse=False))
        plan.append(dict(A=a,B=b,pair_id=pair_id(a,b),extra_holdout=IDS[2] in [a,b],methods=methods))
    save('config/INPUT_IDENTITY.json',rows);save('config/INPUT_HASHES_BEFORE.json',files);save('config/MATCH_PLAN_FROZEN.json',plan)
    save('config/CODE_REUSE.json',REUSE+[dict(path=str(REPO/'visualization/real_p0_renderer.py'),sha256=sha(REPO/'visualization/real_p0_renderer.py'),usage='exact index-center pinhole projection and original plotting'),dict(path=str(REPO/'visualization/same_camera_scene.py'),sha256=sha(REPO/'visualization/same_camera_scene.py'),usage='exact opaque CAD cast and source camera')])
    freeze('BEFORE_FORMAL_RUN.json',dict(scope=IDS,pairs=9,new_SIFT_pairs=sum(m['kind']=='NEW_CPU_SIFT' for p in plan for m in p['methods']),fit_refs=IDS[:2],holdout=IDS[2],selection_no_pose_error=True))
    print('FROZEN',len(IDS),'cameras',len(plan),'pairs; new CPU SIFT',sum(m['kind']=='NEW_CPU_SIFT' for p in plan for m in p['methods']),flush=True)
if __name__=='__main__':main()
