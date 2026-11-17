"""Freeze image-only greedy selection; audit CAD and cross-video lineage."""
from common import *
from collections import defaultdict

def verify021():
    p=ASSETS/'TASK-E4-RING-ANCHORED-JOINT-BA-021'
    ns=dict(globals(),R=p,__file__=str(p/'code/identity021.py'))
    ns['save']=lambda name,x:save('provenance/021_REPLAY/'+Path(name).name,x)
    ns['table']=lambda name,x:table('metrics/021_REPLAY_'+Path(name).name,x)
    reuse(REPO/'experiments/TASK-E4-RING-ANCHORED-JOINT-BA-021/code/identity021.py',['main'],ns)
    ns['main']()

def main():
    assert (R/'provenance/DXY_GENERATED.json').exists(),'Complete Phase1 first'
    assert not (R/'provenance/PREOPT_FREEZE.json').exists(),'Views already frozen'
    guard('prepare');ss=load(R/'config/SOURCE_BINDING.json');dxy={x['source']:x for x in load(R/'provenance/DXY_GENERATED.json')}
    verify021()
    pools=defaultdict(list)
    for s in ss:pools[s['coordinate_pool']].append(s)
    rows=[];cross=[];plan={};yy,xx=np.mgrid[:360,:640];uv=np.c_[xx.ravel(),yy.ravel()]
    for name,views in sorted(pools.items()):
        used=set();eligible=[];excluded=[]
        for s in sorted(views,key=lambda x:x['source_id']):
            cid=s['source_id'];a=source(cid);lab=a['labels'];T=a['T'];K=a['K'];cad=cast(ringscene(s['group']),uv,K,T)[0].reshape(360,640)
            ring=np.isfinite(cad);known=lab!=1;obs=lab==2;inter=int((ring&obs).sum());union=int(((ring|obs)&known).sum())
            br=contour(obs);bp=contour(ring&known);adj=cv2.dilate((lab==1).astype(np.uint8),np.ones((3,3),np.uint8))>0
            br=br[~adj[br[:,1].astype(int),br[:,0].astype(int)]];bp=bp[~adj[bp[:,1].astype(int),bp[:,0].astype(int)]]
            dist=cKDTree(bp).query(br)[0] if len(br) and len(bp) else []
            reason=''
            if s['RGB_content_SHA'] in used:reason='DUPLICATE_RGB_NOT_INDEPENDENT'
            elif not s['pool_formal']:reason='UPSTREAM_CAMERA_EXPLORATORY_NOT_FIT'
            else:eligible.append(s);used.add(s['RGB_content_SHA'])
            if reason:excluded.append(dict(source=cid,reason=reason))
            row=dict(source=cid,pool=name,group=s['group'],video=s['video'],capture_type=s['capture_type'],upstream_camera_status=s['pool_status'],pool_pose_delta_mm=s['pool_pose_delta_mm'],Ring_CAD_IoU_known=inter/max(1,union),Ring_boundary_to_CAD_px=stats(dist),RGB_K_mask_consistent=True,qualification_reason=reason or 'CONDITIONAL_NATIVE_CAMERA',role='PENDING')
            rows.append(row)
            cross.append(dict(source=cid,group=s['group'],video=s['video'],camera_native='OBS_TRUSTED T, unchanged',final_pool_status=s['pool_status'],C_version_delta_mm=s['pool_pose_delta_mm'],Ring_CAD_IoU=row['Ring_CAD_IoU_known'],Ring_source_SHA=s['ring_source']['sha256'],shared_ring_metric_unit='mm',RGB_map_evidence='MAX direct PnP in 004 map, conditional; G01 native005 supplement has021 evidence',independent_cross_video_correspondence='021 G01 ONLY' if s['group']=='G01' else 'NOT_VERIFIED_FOR_THIS_GROUP',joint_fit_permitted=False,disposition='SEPARATE_POOL_'+s['video'],reason='same CAD scale alone does not certify yaw/material identity; old/native vs final pose version differs for18sources'))
        fit=[];held=[];status='NOT_EVALUABLE_INSUFFICIENT_MULTIVIEW'
        if len(eligible)>=3:
            q=np.array([[np.log1p(s['sharpness']),s['mask_complete_proxy'],s['thin_structure_visibility_proxy'],s['Ring_free_fraction']] for s in eligible])
            q=(q-q.min(0))/np.maximum(np.ptp(q,axis=0),1e-12);scores=q@np.array([.1,.1,.1,.05]);by={s['source_id']:s for s in eligible};score=dict(zip(by,scores));nf=min(8,len(eligible)-max(1,int(np.ceil(len(eligible)/4))))
            first=max(eligible,key=lambda s:(score[s['source_id']],s['source_id']));fit=[first['source_id']]
            while len(fit)<nf:
                dirs=np.array([by[c]['direction'] for c in fit]);left=[s for s in eligible if s['source_id'] not in fit]
                win=max(left,key=lambda s:(.65*float(np.arccos(np.clip(np.asarray(s['direction'])@dirs.T,-1,1)).min())/np.pi+score[s['source_id']],s['source_id']));fit.append(win['source_id'])
            held=[s['source_id'] for s in eligible if s['source_id'] not in fit];status='FROZEN_SEPARATE_VIDEO_MULTIVIEW'
        else:held=[s['source_id'] for s in eligible]
        R0=None
        if fit:
            cams=[source(c)['T'] for c in fit];R0=camera_frame(np.mean([c[:3,3] for c in cams],axis=0)-np.array([0,0,-2]),cams[0][:3,0])
        plan[name]=dict(group=views[0]['group'],video=views[0]['video'],FIT=fit,HOLDOUT=held,excluded=excluded,status=status,R0=R0,E1_available=bool(fit) and all(dxy[c]['available'] for c in fit),E1_missing_required=[c for c in fit if not dxy[c]['available']],raw_sources=[s['source_id'] for s in views],primary=views[0]['video']=='004')
        for row in rows:
            if row['pool']==name:
                row['role']='FIT' if row['source'] in fit else 'HOLDOUT' if row['source'] in held else 'EXCLUDED_KEEP_DIAGNOSTIC'
                row['pool_status']=status
    save('config/BODY_FIT_VIEWS.json',plan);table('metrics/VIEW_QUALIFICATION.csv',rows);table('metrics/CROSS_VIDEO_FRAME_AUDIT.csv',cross)
    save('provenance/PREOPT_FREEZE.json',dict(epoch=time.time(),GT_read=False,HERO_XYZ_used=False,protocol=asset(R/'01_PROTOCOL.md'),views=asset(R/'config/BODY_FIT_VIEWS.json'),DXY=asset(R/'provenance/DXY_GENERATED.json'),inputs=asset(R/'config/SOURCE_BINDING.json'),code=[asset(p) for p in sorted((R/'code').glob('*.py'))],upstream_files=load(R/'provenance/INPUT_SHA.json')))
    print('FROZEN_VIEWS',[(k,len(v['FIT']),len(v['HOLDOUT']),v['E1_available']) for k,v in plan.items()],flush=True)
if __name__=='__main__':main()
