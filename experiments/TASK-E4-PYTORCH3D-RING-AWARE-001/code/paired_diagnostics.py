"""Postfreeze paired geometry diagnostics; no optimization or GT access."""
from common import *
from evaluate import pointcast
S=R/'runs/VISIBILITY_ORDER_REPAIR_001'
def main():
    rows=[];pairs=[]
    for name in['virtual','real']:
        meta=getcase(name);a=np.load(R/'inputs'/name/'INITIAL.npz');V,F=a['V'],a['F'];m=trimesh.Trimesh(V,F,process=False);rt=scene(V,F);r=np.load(R/'inputs'/name/'RING.npz');rs=scene(r['V'],r['F']);hidden=np.zeros(len(V),bool)
        for v in meta['views']:
            if v['role']!='FIT':continue
            d=np.load(R/'inputs'/name/(v['id']+'.npz'));uv,z,rz=pointcast(rs,V,d['K'],d['T']);_,_,sz=pointcast(rt,V,d['K'],d['T']);px=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);inside=(z>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360)
            h=inside&(d['labels'][px[:,1],px[:,0]]==2)&(rz<z-.05)&(abs(sz-z)<.05);hidden|=h
        finals=[]
        for arm in['Baseline','RingAware']:
            x=np.load(S/'local_results'/name/arm/'FINAL.npz')['V'];normal_disp=np.einsum('ij,ij->i',x-V,m.vertex_normals)
            rows.append(dict(case=name,arm=arm,P0_material_vertices_total=len(V),P0_front_surface_CAD_occluded_observed_Ring_N=int(hidden.sum()),Ring_hidden_material_outward_signed_mm=stats(normal_disp[hidden])if hidden.any()else'NOT_EVALUABLE_NO_OCCLUDED_P0_VERTICES',Ring_hidden_mean_signed_outward_mm=float(normal_disp[hidden].mean())if hidden.any()else None,Ring_hidden_inward_vertex_N=int((normal_disp[hidden]<0).sum())if hidden.any()else None,all_P0_mean_signed_outward_mm=float(normal_disp.mean()),operator='Fixed P0 vertex IDs and initial area-weighted vertex normals. Material displacement proxy, not nearest-surface distance or true tissue error.',GT='NOT_USED'))
            finals.append(x)
        pairs.append(dict(case=name,actual_same_index_vertex_difference_mm=stats(np.linalg.norm(finals[1]-finals[0],axis=1)),scope='RingAware vs Baseline; same fixed topology and initial vertex IDs'))
    save('metrics/PAIRED_REPAIR_DIAGNOSTICS.json',dict(hidden_proxy=rows,paired_final_mesh_differences=pairs,GT_used=False))
    table('metrics/PAIRED_REPAIR_HIDDEN_PROXY.csv',rows)
    validations=[]
    for name in['virtual','real']:
        logs=[list(csv.DictReader((S/'metrics'/(name+'_'+arm+'_TRAINING.csv')).open()))for arm in['Baseline','RingAware']]
        starts=[np.load(S/'local_results'/name/arm/'STEP_0000.npz')for arm in['Baseline','RingAware']]
        validations.append(dict(case=name,same_initial_V=np.array_equal(starts[0]['V'],starts[1]['V']),same_F=np.array_equal(starts[0]['F'],starts[1]['F']),same_view_order=[r['views']for r in logs[0]]==[r['views']for r in logs[1]],same_steps=len(logs[0])==len(logs[1])==300))
    save('metrics/REPAIRED_PAIRED_FAIRNESS.json',validations)
    print(rows,pairs,flush=True)
if __name__=='__main__':main()
