"""Mask-only initializer copied verbatim from the previous frozen fit.py."""
from model import *
def seed(body,renderer):
    q=np.r_[body.a['V'].mean(0),0.];V,F=body.mesh(q);points=[];weights=[];arrows=[];m=trimesh.Trimesh(V,F,process=False)
    for cid in protocol()['fit_views']:
        r=renderer.silhouette(V,F,cid);d=renderer.data[cid];dist,ind=d['tree'].query(r['uv']);target=d['contour'][ind];w=np.maximum(dist-.75,0)**2
        for j in range(len(dist)):
            arrows.append(dict(view=cid,P=r['P'][j],uv=r['uv'][j],target_uv=target[j],face_id=int(r['faces'][j]),normal=r['normal'][j],distance_px=float(dist[j]),seed_weight=float(w[j])))
        points.extend(r['P']);weights.extend(w)
    weights=np.array(weights);assert weights.sum()>0,'INSUFFICIENT_VISIBLE_MASK_SIGNAL';center=np.average(points,axis=0,weights=weights);growth=sum(int(renderer.data[c]['target'].sum())-int(renderer.project(scene(V,F),c)[0].sum())for c in protocol()['fit_views']);q=np.r_[center,-.05 if growth>0 else .05];save('metrics/MASK_ONLY_INITIALIZATION.json',dict(q=q,rule=protocol()['seed_rule'],positive_target_minus_base_pixels=growth,GT_read=False));table('metrics/INITIAL_CORRESPONDENCES.csv',arrows);return q
