"""One deterministic bounded discovery pass; flags propose, never delete."""
from common import *

def main():
    p=load(R/'config/A2_PREREGISTERED.json'); assert sha(R/'config/A2_PREREGISTERED.json')==load(R/'config/BEFORE_CANDIDATES.json')['protocol']['sha256']
    assert not (R/'CLEANUP_CANDIDATES.csv').exists(), 'DISCOVERY_ALREADY_DONE'
    ss={cid:baseline(cid) for cid in IDS}; X=np.concatenate([s['X'] for s in ss.values()]); lo,hi=X.min(0),X.max(0)
    old=read_csv(BASE/'PROJECTIVE_CLEANUP_DECISIONS.csv'); previous={int(r['native_pixel_id']):r['review_id'] for r in old if r['derived_action']=='RETAIN_UNRESOLVED'}
    assert len(previous)==9
    allrows=[]; selected=[]; counts=[]
    for cid,s in ss.items():
        uv=s['native_uv']; ids=s['native_id']; u,v=uv.T; Z=s['depth'][v,u]; xyz=s['X']
        dt=cv2.distanceTransform(s['valid'].astype(np.uint8),cv2.DIST_L2,5)[v,u]
        jump=neighbours(s['depth'],s['valid'])[v,u]
        d=np.load(BASE/'local_results'/(cid+'_native_raw_diagnostic.npz')); raw_map=dict(zip(d['native_id'].tolist(),d['distance_to_own_original_raw_faces_mm'].tolist())); raw=np.array([raw_map[int(i)] for i in ids])
        extrema=np.zeros(len(ids),bool); extrema[np.r_[xyz.argmin(0),xyz.argmax(0)]]=True
        boundary=np.minimum(abs(xyz-lo),abs(xyz-hi)).min(1)<=p['candidate_generation']['global_boundary_band_mm']
        discontinuous=jump>=p['candidate_generation']['native_4neighbour_jump_mm']; rawedge=(raw>1)&(dt<=2)
        prev=np.isin(ids,list(previous)) if cid=='G01_004_new_r00' else np.zeros(len(ids),bool)
        flags=prev|extrema|boundary|discontinuous|rawedge
        j=np.flatnonzero(flags); priority=np.select([prev,extrema,boundary,discontinuous,rawedge],[0,1,2,3,4],default=9)
        order=j[np.lexsort((ids[j],priority[j]))]; pick=set(order[:p['candidate_generation']['max_review_pool_per_source']].tolist())
        assert all(k in pick for k in np.flatnonzero(prev|extrema))
        archive=archive_uv(s,uv)
        for k in order:
            reasons=[name for name,mask in [('PREVIOUS_9',prev),('SOURCE_AXIS_EXTREME',extrema),('GLOBAL_BOUNDARY_BAND',boundary),('NATIVE_DEPTH_JUMP',discontinuous),('RAW_EDGE_DIFFERENCE',rawedge)] if mask[k]]
            row=dict(source=cid,native_id=int(ids[k]),native_u=int(u[k]),native_v=int(v[k]),archive_u=float(archive[k,0]),archive_v=float(archive[k,1]),
                axial_depth_mm=float(Z[k]),X_mm=float(xyz[k,0]),Y_mm=float(xyz[k,1]),Z_mm=float(xyz[k,2]),proposal_reasons=reasons,priority=int(priority[k]),
                source_mask_interior_px=float(dt[k]),max_native_neighbour_jump_mm=float(jump[k]),distance_to_own_original_Raw_mm=float(raw[k]),
                previous_review_id=previous.get(int(ids[k]),'') if cid=='G01_004_new_r00' else '',selected_for_projection=k in pick,baseline_valid=True)
            allrows.append(row)
            if k in pick: selected.append(row)
        counts.append(dict(source=cid,original_N=len(native(cid)['native_id']),baseline_N=len(ids),anomaly_discovery_N=len(j),review_pool_N=len(pick),not_reviewed_anomaly_N=len(j)-len(pick),axis_extrema_N=int(extrema.sum()),previous_9_N=int(prev.sum())))
    for k,row in enumerate(selected): row['candidate_id']=f'A2_{k+1:05d}'
    table('CANDIDATE_DISCOVERY_ALL_FLAGS.csv',allrows); table('CLEANUP_CANDIDATES.csv',selected)
    save('CANDIDATE_DISCOVERY_SUMMARY.json',dict(per_source=counts,baseline_N=sum(r['baseline_N'] for r in counts),candidate_N=len(selected),unreviewed_anomaly_N=sum(r['not_reviewed_anomaly_N'] for r in counts),originals_N=106144,all_unreviewed_retained=True,global_baseline_point_bounds_mm=[lo,hi],protocol=asset(R/'config/A2_PREREGISTERED.json')))
    print('A2_CANDIDATES',len(selected),counts,flush=True)

if __name__=='__main__': main()
