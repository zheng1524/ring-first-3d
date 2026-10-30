"""Additional original-triangle support; old point-center metrics unchanged."""
from evaluate import *
def historical_f2_blocks(sid):
    out=[]
    for c in historical_cases():
        if sceneid(c)!=sid:continue
        s=source(c['id']);ids=np.flatnonzero(old_F2(c['id'])['accepted'][s['F']].all(1))
        if len(ids):out.append(dict(id=c['id'],reference=c['id'],face_ids=ids,H=np.eye(4),face_generations=np.zeros(len(ids),int),role='HISTORICAL_F2_COMPLETE_FACES_ONLY',original_component=-1))
    return out
def main(selected=None):
    import common as shared
    frozen_cases=shared.cases();shared.cases=lambda:frozen_cases;globals()['cases']=lambda:frozen_cases
    surface=[];common=[];sampling=[];novelty=[]
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        if selected and sid not in selected:continue
        if not(R/f'local_results/scenes/{sid}_Final.json').exists():continue
        start=load_scene(sid,0);final=load_scene(sid);methods={'Selected_Main':[b for b in start if b['role'].startswith('PRIMARY')],'Initial_S0':start,'Historical_Cleaned_F1':f1_blocks(sid,False),'Historical_F2':historical_f2_blocks(sid),'AllAvailable_Cleaned_F1':f1_blocks(sid,True),'F3_PreJoint_SameFaces':no_joint(final),'F3_Joint':final}
        for t in target_rows(sid):
            target=cv2.imread(t['Mask'],0)==1;den=int(target.sum());rays={}
            for method,blocks in methods.items():
                a=mesh_arrays(blocks);rays[method]=raymesh(a['P'],a['F'],t)['valid']
            initial=rays['Initial_S0']&target
            for method,hit in rays.items():
                valid=hit&target;union=hit|target;surface.append(dict(scene=sid,target=t['id'],role=t['role'],method=method,target_Polyp_N=den,original_triangle_supported_N=int(valid.sum()),coverage=float(valid.sum()/den),Mask_IoU=float(valid.sum()/max(1,union.sum())),outside_target_N=int((hit&~target).sum()),new_vs_S0_N=int((valid&~initial).sum()),lost_vs_S0_N=int((initial&~hit).sum()),renderer='ray hits of only actual original accepted triangles; no new faces/smoothing/point interpolation',separate_from_historical_pointcenter_protocol=True))
            folder=R/'local_results/evaluation'/sid/t['id'];pred={k:np.load(folder/(k+'.npz'))for k in ['Initial_S0','F3_PreJoint_SameFaces','F3_Joint']};mask=target.copy()
            for p in pred.values():mask&=p['layer']==1
            B=np.asarray(Image.open(t['RGB']).convert('RGB'));errs={k:stats(abs(p['RGBA'][:,:,:3].astype(float)-B).mean(2)[mask])for k,p in pred.items()};common.append(dict(scene=sid,target=t['id'],same_support_N=int(mask.sum()),target_Polyp_N=den,support_fraction=float(mask.sum()/den),errors=errs,role='exact shared support of S0 / PreJoint / Joint; independent target RGB only'))
            p0=pred['Initial_S0'];pj=pred['F3_Joint'];sampling.append(dict(scene=sid,target=t['id'],target_Polyp_N=den,point_center_old_support_lost_N=int(((p0['layer']==1)&target&(pj['layer']!=1)).sum()),triangle_old_support_lost_N=int((initial&~rays['F3_Joint']).sum()),point_center_old_support_lost_fraction=float(((p0['layer']==1)&target&(pj['layer']!=1)).sum()/den),triangle_old_support_lost_fraction=float((initial&~rays['F3_Joint']).sum()/den),interpretation='support changes include resampling under rigid point displacement; triangle test is an additional actual-face diagnostic, never replacement of point metrics'))
        steps=load(R/f'metrics/growth_steps_{sid}.json')
        for row in steps:
            k=row['round'];before=load_scene(sid,k-1);after=load_scene(sid,k);cid=row['reference'];s=source(cid);newfaces=np.concatenate([np.array(b['face_ids'])[np.array(b['face_generations'])==k]for b in after if b['reference']==cid]);component=int(face_components(s['F'])[newfaces[0]]);H=group_H(before,cid,component);a=mesh_arrays(before);st,dz,_=classify(a['P'],a['F'],s,target_source(cid),H);prior_novel=(st[s['F'][newfaces]]==NOVEL).any(1);prior_explained=(st[s['F'][newfaces]]==EXPLAINED).all(1);novelty.append(dict(scene=sid,step=k,reference=cid,accepted_new_complete_faces=len(newfaces),already_explained_before_joint_face_N=int(prior_explained.sum()),already_explained_before_joint_area_mm2=float(s['areas'][newfaces[prior_explained]].sum()),no_projected_novel_vertex_before_joint_face_N=int((~prior_novel).sum()),no_projected_novel_vertex_before_joint_area_mm2=float(s['areas'][newfaces[~prior_novel]].sum()),accepted_joint=bool(row['joint_alignment'].get('accepted',False)),GT_used=False,note='post-output diagnostic, never used to retune or select prediction'))
        print('SURFACE SUPPORT AUDIT',sid,flush=True)
    both('actual_triangle_crossframe_support',surface);both('identical_common_support_RGB',common);both('sampling_vs_surface_change',sampling);both('joint_created_novelty_audit',novelty)
if __name__=='__main__':main(sys.argv[1:]or None)
