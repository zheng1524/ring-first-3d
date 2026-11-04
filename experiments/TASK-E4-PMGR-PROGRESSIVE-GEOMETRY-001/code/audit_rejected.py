"""Retain independently reproducible failure evidence for both rejected rounds."""
from inputs import *
def main():
    rows=[];index=[]
    for dirname in ['REJECTED_PRE_RING_BOUND_CORRECTION','REJECTED_V1P1_MINIMUM_BOUND']:
        root=R/'local_results'/dirname
        if not root.exists():continue
        for file in sorted(root.glob('*.json')):
            if file.name.endswith('__progress.json'):continue
            x=load(file);key=x['key'];folder=root/key
            if not(folder/'P3.npz').exists():continue
            a=np.load(folder/'P0.npz');b=np.load(folder/'P3.npz');F=a['F']
            def distance(V):
                t=V[F];pts=np.vstack([V,t.mean(1),(t[:,0]+t[:,1])/2,(t[:,1]+t[:,2])/2,(t[:,2]+t[:,0])/2]);return ringscene(x['scene']).compute_signed_distance(o3d.core.Tensor(pts.astype(np.float32))).numpy()
            d0=distance(a['V']);d3=distance(b['V']);excess=d3-np.minimum(d0,0);rows.append(dict(round=dirname,case_id=key,rejected_immutable_P0_bound_violations=int((excess<-.010001).sum()),minimum_P0_relative_signed_mm=float(excess.min()),scientific_use='REJECTED_NOT_MIXED_WITH_FORMAL'))
            index.append(asset(file))
    table('metrics/REJECTED_DIAGNOSTICS_AUDIT.csv',rows);save('assets_index/REJECTED_DIAGNOSTICS.json',dict(journals=index,evidence=rows,inputs_original_unchanged=True));print('REJECTED_CASES_REPLAYED',len(rows))
if __name__=='__main__':main()
