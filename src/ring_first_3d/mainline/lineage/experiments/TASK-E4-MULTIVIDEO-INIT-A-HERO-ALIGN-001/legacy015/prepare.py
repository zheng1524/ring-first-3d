"""Rebind audited existing single-video assets; no image/depth/pose inference."""
from common import *
from scipy.ndimage import distance_transform_edt
import shutil
P13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
PREV=REPO/'experiments/TASK-E4-SINGLE-VIDEO-013-FAST-001'

def skeleton_proxy(m):
    """Morphological skeleton, only a 2D view-quality proxy, not a 3D stalk."""
    a=m.astype(np.uint8);out=np.zeros_like(a);kernel=cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    while a.any():
        er=cv2.erode(a,kernel);out|=a-cv2.dilate(er,kernel);a=er
    return out>0

def link(a,b):
    if not b.exists():b.symlink_to(a.resolve(),target_is_directory=a.is_dir())

def main():
    assert not(R/'provenance/PREOPT_FREEZE.json').exists()
    cases=load(P13/'config/CASE_LOCK.json');ref=load(PREV/'config/REFERENCE_VIDEOS.json');selection={};inventory=[];lineage=[]
    save('config/CASE_LOCK.json',cases);save('config/REFERENCE_VIDEOS.json',ref)
    for c in cases:
        n=c['name'];src=PREV/'inputs'/n;master=load(src/'CASE.json');fit=[v for v in master['views']if v['role']=='FIT'];held=[v['id']for v in master['views']if v['role']!='FIT'];baseline=[v['id']for v in c['views']if v['role']=='FIT'];folder=R/'inputs'/n;folder.mkdir();initial=np.load(src/'INITIAL.npz');center=initial['V'].mean(0)
        for p in src.iterdir():
            if p.is_file()and p.name!='CASE.json':link(p,folder/p.name)
        qualities=[]
        for v in fit:
            a=np.load(src/(v['id']+'.npz'));lab=a['labels'];m=lab==1;dt=distance_transform_edt(m);sk=skeleton_proxy(m);border=float(np.r_[m[0],m[-1],m[:,0],m[:,-1]].mean());sharp=float(cv2.Laplacian(cv2.cvtColor(a['RGB'],cv2.COLOR_RGB2GRAY),cv2.CV_64F).var());thin=float((sk&(dt<max(2.,float(dt.max())*.25))).sum()/max(1,np.sqrt(m.sum())));ringfree=1-float((lab==2).sum()/max(1,(lab>0).sum()));D=a['T'][:3,3]-center;D/=np.linalg.norm(D);v.update(direction=D.tolist(),same_video=True,raw_pose_unchanged=True);qualities.append([np.log1p(sharp),1-border,thin,ringfree])
            inventory.append(dict(case=n,view=v['id'],video=ref[n]['reference_video'],role='candidateFIT',RGB_camera_cache=asset(src/(v['id']+'.npz')),sharpness=sharp,mask_complete_proxy=1-border,thin_structure_visibility_proxy=thin,Ring_free_fraction=ringfree,original_qualification=v.get('qualification'),direction=D.tolist()))
        Q=np.array(qualities);Q=(Q-Q.min(0))/np.maximum(np.ptp(Q,axis=0),1e-12);quality=Q@np.array([.1,.1,.1,.05]);by={v['id']:v for v in fit};scores={v['id']:float(quality[i])for i,v in enumerate(fit)};chosen=baseline.copy()
        while len(chosen)<min(8,len(fit)):
            dirs=np.array([by[x]['direction']for x in chosen]);candidates=[v for v in fit if v['id']not in chosen];win=max(candidates,key=lambda v:(.65*float(np.arccos(np.clip(np.array(v['direction'])@dirs.T,-1,1)).min())/np.pi+scores[v['id']],v['id']));chosen.append(win['id'])
        assert set(chosen).isdisjoint(held)and all(by[x]['video']==ref[n]['reference_video']for x in chosen)
        selection[n]=dict(FIT=chosen,HOLDOUT=held,stability_FIT=[x for x in chosen if x!=chosen[-1]],original013FIT=baseline,all_same_video=True)
        meta=dict(master,views=[dict(v,role='FIT'if v['id']in chosen else'UPDATE_HOLDOUT')for v in master['views']if v['id']in set(chosen+held)]);save('inputs/'+n+'/CASE.json',meta)
        for v in master['views']:
            if v['id']in held:inventory.append(dict(case=n,view=v['id'],video=ref[n]['reference_video'],role='UPDATE_HOLDOUT',original_qualification=v.get('qualification')))
        model=P13.parent/'CAP_REPAIR_STABLE_011/inputs'/n/'C_INITIAL_MODEL.json'
        if n in ['G10','G11']:model=P13/'initialization_011/inputs'/n/'C_INITIAL_MODEL.json'
        m=load(model);save('inputs/'+n+'/PARAMETRIC_START.json',dict(p=m['p'],meta=m['meta'],source=asset(model),not_refit_from_GT=True));lineage.append(dict(case=n,current_INITIAL=asset(src/'INITIAL.npz'),parametric_C_source=asset(model),frozen013_support=asset(P13/'arms/FINAL_UNIFORM/local_results'/(n+'_P0_SUPPORT.npz')),historical_initialization_text_is_ancestral=c.get('initialization')))
    for p in(PREV/'depth_observations').glob('*.npz'):link(p,R/'depth_observations'/p.name)
    save('config/VIEW_SELECTION.json',selection);save('provenance/INITIALIZATION_LINEAGE.json',lineage);save('metrics/VIEW_INVENTORY.json',inventory);table('VIEW_INVENTORY.csv',inventory)
    save('config/PROTOCOL.json',dict(seed=20261109,depth=load(P13/'arms/FINAL_UNIFORM/config/PROTOCOL.json')['depth'],phase_A=dict(initializations=['Init-A','Init-B','Init-C'],initializer_TRF_max_nfev=20,stability_TRF_max_nfev=8,downstream=dict(max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),selection='one global method, FIT only; median(1-IoU + .02*fixed_depth_cost); ineligible if more added dense-Ring/self geometry failures than Init-A; no HOLDOUT/GT ranking'),phase_B=dict(cases=[c['name']for c in cases if c['morphology']=='Ip'],methods=['Stalk-A','Stalk-B','Stalk-C'],max_proposals=80,max_accepted=40,consecutive_rejection_stop=30),loss='014 MultiObjective D0_013; original013 silhouette/FN/FP/bidirectional coefficients, independent fixed-depth normalization',guard='unchanged014 dense32/FCL/reverse/self every candidate; independent64 audit',no_cross_video_correction=True,no_new_HERO=True,no_GT_selection=True))
    old=load(PREV/'provenance/HISTORICAL_PROTECTION.json');save('provenance/HISTORICAL_PROTECTION.json',old)
    files=[asset(p)for d in ['inputs','depth_observations','code','config']for p in sorted((R/d).rglob('*'))if p.is_file()];save('provenance/PREOPT_FREEZE.json',dict(epoch=time.time(),files=files,GT_geometry_opened=False,physical_N=len(cases),Ip_N=sum(c['morphology']=='Ip'for c in cases),history_untouched=True));print('PREPARED',len(cases),sum(len(q['FIT'])for q in selection.values()),'FIT')

if __name__=='__main__':main()
