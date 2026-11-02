"""Post-hoc descriptive strata, not a new reconstruction or new success gate."""
from evaluate import topology
from hero_tsdf_adapter import *
def main():
    rawrows=[]
    for cid in G1:
        s=source(cid);m=trimesh.Trimesh(vertices=s['P'],faces=s['F'],process=False);t,_=topology(m);rawrows.append(dict(source=cid,**t))
    table('ORIGINAL_MESH_TOPOLOGY.csv',rawrows)
    windows=load(R/'config/FIG3_WINDOWS.json');out=[]
    for cid in G1:
        s=source(cid);X=s['P'][s['F']].mean(1);ar=s['area']
        for k,(center,label)in enumerate(zip(windows['centers_mm'],windows['labels'])):
            angle=(0,0)if k==1 else(-65,22);_,right,up=vis.basis(angle);delta=X-np.asarray(center);keep=(abs(delta@right)<=2.5)&(abs(delta@up)<=2.5)
            for name in ['G0','G1']:
                d=np.load(R/'local_results/EVALUATION'/(name+'_'+cid+'_original_faces.npz'))['distance_mm'];r=dict(mesh=name,source=cid,region=label,posthoc=True,original_face_N=int(keep.sum()),original_area_mm2=float(ar[keep].sum()),retained_area_fraction=float(ar[keep&(d<=.25)].sum()/ar[keep].sum())if keep.any()else np.nan,anatomical_region_certified=False)
                out.append(r)
    table('DETAIL_REGION_METRICS.csv',out)
    print('SUPPLEMENTAL_DESCRIPTIVE_METRICS',len(out),flush=True)
if __name__=='__main__':main()
