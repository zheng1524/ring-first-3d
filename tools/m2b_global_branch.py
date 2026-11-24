#!/usr/bin/env python3
"""M2B discrete global branch selection over existing Ring candidates + existing BA."""
import argparse,json,sys
from pathlib import Path
import numpy as np,pandas as pd,cv2
WS=Path('/home/liu/ring_first_3d_workspace'); OUT=WS/'runs/m2b_ring_global_branch'
sys.path.insert(0,str(WS/'src')); sys.path.insert(0,str(WS/'tools')); sys.path.insert(0,str(WS/'camera_mainline/code')); sys.path.insert(0,str(WS/'experiments/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005/code'))
from ring_first_3d.mainline.native.camera import residual
import unified_camera as U5
from run_w0_camera import build_ns_and_views, stage_tracks

def rotdeg(A,B):
    return float(np.degrees(np.arccos(np.clip((np.trace(A[:3,:3].T@B[:3,:3])-1)/2,-1,1))))

def dist(A,B): return rotdeg(A,B)+np.linalg.norm(A[:3,3]-B[:3,3])

def sampson(Ci,Cj,K,pi,pj):
    R=Cj[:3,:3].T@Ci[:3,:3]; t=Cj[:3,:3].T@(Ci[:3,3]-Cj[:3,3]); S=np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]])
    F=np.linalg.inv(K).T@S@R@np.linalg.inv(K)
    a=np.c_[pi,np.ones(len(pi))]; b=np.c_[pj,np.ones(len(pj))]; Fa=a@F.T; Fb=b@F
    return np.abs(np.sum(b*Fa,axis=1)/np.sqrt(np.maximum((Fa[:,:2]**2+Fb[:,:2]**2).sum(1),1e-20)))

def select(g,v,prep_root=None,ring_radius=None):
    out=OUT/'global'/g/v; out.mkdir(parents=True,exist_ok=True); work=OUT/'global_work'/g/v; work.mkdir(parents=True,exist_ok=True)
    for x in ['observations','predictions','metrics']: (work/x).mkdir(parents=True,exist_ok=True)
    # prepared metadata
    meta=json.loads((Path(prep_root or WS/'runs/m1_final_39/prepared')/f'{g}_{v}'/'PREPARED.json').read_text())
    from ring_first_3d.mainline.native.ring_cad import params as cad_params
    R=ring_radius or cad_params(float(meta.get('ring_mm',10.0)))['centerline_radius_mm']; r=.6
    # build namespace/views and tracks
    import argparse
    ns,ordered,arrays=build_ns_and_views(g,v,meta,work,R,r)
    tr,pack,src=stage_tracks(ns,ordered,work,g,v)
    edges=ns['pair_data'](tr,pack)
    rings=U5.ring_candidates(arrays,ordered,work,R,r,'all')
    ids=[x['id'] for x in rings]
    # A1 selected poses
    a1=np.load(OUT/'g03_A1'/g/v/'camera_result.npz') if (OUT/'g03_A1'/g/v/'camera_result.npz').exists() else None
    a1map={str(i):np.asarray(c,float) for i,c in zip(a1['ids'],a1['c2w'])} if a1 is not None else {}
    # candidate matrices and ring errors
    C=[]; ring_e=[]; obs=[]
    for d in rings:
        ob=dict(np.load(work/'observations'/(d['id']+'_ring.npz')))
        obs.append(ob); cs=[np.asarray(x['c2r'],float) for x in d['candidates']]
        C.append(cs); ring_e.append([float(np.abs(residual(x,ob,arrays[d['id']]['K'],R,r)).mean()) for x in cs])
    # initial labels nearest A1 (or best ring)
    labels=[]
    for i,d in enumerate(rings):
        if d['id'] in a1map: labels.append(int(np.argmin([dist(x,a1map[d['id']]) for x in C[i]])))
        else: labels.append(int(np.argmin(ring_e[i])))
    def energy(lab):
        er=sum(ring_e[i][lab[i]] for i in range(len(lab)))
        rg=[]; te=[]
        for e in edges:
            i,j=int(e['i']),int(e['j']); rows=e['rows']; d=sampson(C[i][lab[i]],C[j][lab[j]],arrays[rings[i]['id']]['K'],rows[:,1:3],rows[:,3:5]); rg.append(float(np.median(d)))
        for i in range(len(lab)-1):
            gap=max(1,abs(int(ordered[i+1]['meta']['raw_frame'])-int(ordered[i]['meta']['raw_frame'])))
            te.append((rotdeg(C[i][lab[i]],C[i+1][lab[i+1]])+np.linalg.norm(C[i][lab[i]][:3,3]-C[i+1][lab[i+1]][:3,3]))/gap)
        return er+0.5*float(np.mean(rg) if rg else 0)+0.015*float(np.mean(te) if te else 0), er, float(np.mean(rg) if rg else 0), float(np.mean(te) if te else 0)
    e0=energy(labels); best=labels[:]; bestE=e0[0]
    for _ in range(4):
        changed=False
        for i in range(len(labels)):
            vals=[]
            for k in range(len(C[i])):
                lab=best[:]; lab[i]=k; vals.append(energy(lab)[0])
            k=int(np.argmin(vals))
            if k!=best[i]: best[i]=k; changed=True
        e=energy(best)
        if e[0]<bestE: bestE=e[0]; best=best[:]
        if not changed: break
    # candidate/selection tables
    cand_rows=[]; sel_rows=[]
    for i,d in enumerate(rings):
        for k,x in enumerate(C[i]):
            cand_rows.append(dict(group_id=g,video_id=v,frame_id=d['id'],raw_frame=ordered[i]['meta']['raw_frame'],candidate_id=k,
                ring_error=ring_e[i][k],normal_branch=x.get('normal_branch') if isinstance(x,dict) else None,
                initial=bool(k==labels[i]),selected=bool(k==best[i]),pose=[round(float(z),6) for z in x.reshape(-1)] if hasattr(x,'reshape') else None))
        sel_rows.append(dict(group_id=g,video_id=v,frame_id=d['id'],raw_frame=ordered[i]['meta']['raw_frame'],
             n_candidates=len(C[i]),initial_candidate=labels[i],selected_candidate=best[i],
             initial_ring_error=ring_e[i][labels[i]],selected_ring_error=ring_e[i][best[i]],
             energy_initial=e0[0],energy_selected=bestE))
    pd.DataFrame(cand_rows).to_csv(out/'GLOBAL_BRANCH_CANDIDATES.csv',index=False)
    pd.DataFrame(sel_rows).to_csv(out/'GLOBAL_BRANCH_SELECTION.csv',index=False)
    # init NPZ
    np.savez_compressed(out/'init_poses.npz',ids=np.array(ids),c2w=np.array([C[i][best[i]] for i in range(len(ids))]))
    # trajectory comparison A1 vs A2 selected
    tr_rows=[]
    for i,d in enumerate(rings):
        p0=a1map.get(d['id'],C[i][best[i]]); p1=C[i][best[i]]
        tr_rows.append(dict(group_id=g,video_id=v,frame_id=d['id'],raw_frame=ordered[i]['meta']['raw_frame'],
            A1_c2w=p0.reshape(-1).tolist(),A2_init_c2w=p1.reshape(-1).tolist(),rot_delta_deg=rotdeg(p0,p1),trans_delta_mm=float(np.linalg.norm(p0[:3,3]-p1[:3,3]))))
    pd.DataFrame(tr_rows).to_csv(out/'TRAJECTORY_BEFORE_AFTER.csv',index=False)
    print('GLOBAL',g,v,'candidates',len(ids),'E0',e0,'Ebest',bestE,'changed',sum(labels[i]!=best[i] for i in range(len(labels))),flush=True)
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--group',required=True); ap.add_argument('--video',required=True); a=ap.parse_args(); select(a.group,a.video)
