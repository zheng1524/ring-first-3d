"""Only fitted-view contour residuals choose actual surface medoids."""
import os
os.environ['E4_OPTIMIZER_ONLY']='1'
from model import *
from continuous import *
def main():
    assert not(R/'config/KERNEL_CENTERS.json').exists();b=Body();renderer=Renderer();q=np.array(load(R/'metrics/S1_FINISHED.json')['q']);V,F=b.mesh(q);rows=[]
    for cid in protocol()['fit_views']:
        d=renderer.data[cid];r=renderer.silhouette(V,F,cid);dist,idx=d['tree'].query(r['uv']);uv=np.clip(np.rint(r['uv']).astype(int),[0,0],[639,359]);inside=d['target'][uv[:,1],uv[:,0]];weight=np.maximum(dist-.75,0)**2/max(1,len(dist))
        for i in range(len(dist)):
            if weight[i]<=0:continue
            rows.append(dict(view=cid,face_id=int(r['faces'][i]),P=r['P'][i],predicted_uv=r['uv'][i],target_uv=d['contour'][idx[i]],kernel='EXPAND'if inside[i]else'SHRINK',weight=float(weight[i]),distance_px=float(dist[i])))
    selected=[]
    for k in ['EXPAND','SHRINK']:
        group=[x for x in rows if x['kernel']==k]
        if not group:
            save('metrics/KERNEL_SELECTION.json',dict(eligible=False,missing=k,GT_not_read=True));print('KERNEL_SELECTION_NO_SIGNAL',k,flush=True);return
        P=np.array([x['P']for x in group]);w=np.array([x['weight']for x in group]);mean=np.average(P,axis=0,weights=w);j=int(np.argmin(np.sum((P-mean)**2,axis=1)));selected.append(dict(kernel=k,medoid=group[j],candidate_N=len(group),mean_for_medoid_only=mean))
    table('metrics/KERNEL_CANDIDATES.csv',rows);save('metrics/KERNEL_SELECTION.json',dict(eligible=True,selected=selected,GT_not_read=True,only_fit_views=True,rule='residual-weighted mean then nearest actual visible surface point, equal source normalization'))
    save('config/KERNEL_CENTERS.json',dict(centers_mm=[x['medoid']['P']for x in selected],radius_mm=b.radius,source='fit contour residuals after S1 only',GT_not_read=True));print('KERNELS_SELECTED',[(x['kernel'],x['medoid']['P'],x['medoid']['view'])for x in selected],flush=True)
if __name__=='__main__':main()
