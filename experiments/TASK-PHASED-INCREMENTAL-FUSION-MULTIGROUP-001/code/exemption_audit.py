"""Post-execution geometric witnesses for frozen A exemptions, no selection update."""
from pipeline import *
def main():
    rows=[];o=o3d_module()
    for sc in scenes():
        for cid in sc['references']:
            z=np.load(R/f'local_results/{cid}/Distance_Exempt_Candidate_exact.npz');ids=z['exempt_original_indices'];s=source(cid)
            if not len(ids):continue
            best=np.full(len(ids),np.inf);witness=[None]*len(ids)
            for other in sc['references']:
                if other==cid:continue
                p=source(other);old=np.zeros(len(p['P']),bool);old[np.load(ABS/f'local_results/{other}/T2_exact.npz')['deleted_original_indices']]=True;Fids=np.flatnonzero(~old[p['m'].faces].any(1));rt=o.t.geometry.RaycastingScene(nthreads=2);rt.add_triangles(o.core.Tensor(p['P'].astype(np.float32)),o.core.Tensor(p['m'].faces[Fids].astype(np.uint32)));v=rt.compute_closest_points(o.core.Tensor(s['P'][ids].astype(np.float32)));Q=v['points'].numpy();d=np.linalg.norm(Q-s['P'][ids],axis=1);fid=v['primitive_ids'].numpy()
                for k in np.flatnonzero(d<best):best[k]=d[k];witness[k]=dict(other_reference=other,other_original_face_id=int(Fids[fid[k]]),closest_source_triangle_point_mm=Q[k])
            photo=observation_support(s['P'],s['rgb'],target(sc['id']));front,_=source_conflicts(s['P'],cid,sc['references'])
            for k,idx in enumerate(ids):assert best[k]<=cfg()['distance_exemption_mm']and photo[idx]and not front[idx];rows.append(dict(scene=sc['id'],reference=cid,original_point_id=int(idx),source_u=int(s['a']['source_u'][idx]),source_v=int(s['a']['source_v'][idx]),XYZ_mm=s['P'][idx],distance_mm=best[k],target=target(sc['id'])['id'],target_RGB_Mask_supported=True,no_front_conflict=True,**witness[k],interpretation='PREDICTION_CONSISTENCY_NOT_TRUE_STRUCTURE_LABEL'))
    save('local_results/A_exemption_witnesses_full.json',rows);public=[{k:v for k,v in row.items()if k not in ['XYZ_mm','closest_source_triangle_point_mm']}for row in rows];save('metrics/A_exemption_evidence.json',public);csvsave('metrics/A_exemption_evidence.csv',public);print('EXEMPTION_WITNESSES',len(rows),'verified; full geometry local only; no candidate changed',flush=True)
if __name__=='__main__':main()
