"""Recompute014G03 contour associations and four local bands, CPU only.
The saved joint gradient is an audited input, not a newly computed gradient.
"""
from common import *
import types
import p3d
p3d.device=p3d.torch.device('cpu')
from contour_objective import ContourDistance,tensor,torch
from strategy import local_directions

def main():
    old=REPO/'experiments/TASK-E4-PYTORCH3D-014/arms/C4_ALL';n='G03';meta=load(old/'inputs'/n/'CASE.json');a=np.load(old/'inputs'/n/'INITIAL.npz');r=np.load(old/'inputs'/n/'RING.npz');g=np.load(old/'metrics/G03_GRADIENT_DIAGNOSTIC.npz');assert np.array_equal(g['V'],a['V'])and np.array_equal(g['F'],a['F']);c=types.SimpleNamespace(F=a['F'],ringV=r['V'],ringF=r['F'],fit=[v['id']for v in meta['views']if v['role']=='FIT'],views={})
    for cid in c.fit:
        z=np.load(old/'inputs'/n/(cid+'.npz'));sid=np.load(old/'inputs'/n/(cid+'_SIDES.npz'));c.views[cid]=dict(K=z['K'],T=z['T'],labels=z['labels'],classes=tensor(cv2.resize(sid['classes'],(320,180),interpolation=cv2.INTER_NEAREST),torch.int64))
    contour_loss=ContourDistance(c);far=np.zeros(len(a['V']),bool);per=[];V=tensor(a['V'],torch.float64)
    for cid in c.fit:
        _,rec=contour_loss(V,cid);last=contour_loss.last.get(cid)
        if last is None:continue
        take=last['reverse_native_px']>=10;nodes=np.unique(last['eid'][last['nn'][take]])if take.any()else np.array([],int);far[nodes]=True;per.append(dict(view=cid,far_target_N=int(take.sum()),associated_vertex_N=len(nodes)))
    grad=tensor(g['full_gradient'],torch.float64);bands=local_directions(types.SimpleNamespace(c=c),torch.zeros_like(grad),grad);covered=np.zeros(len(far),bool)
    for _,d in bands:covered|=d.norm(dim=1).cpu().numpy()>0
    ans=dict(case=n,scope='original014 C4_ALL frozen initial; actual rerun CPU projections/nearest contour and four graph bands',far_associated_vertex_N=int(far.sum()),far_in_four_original_bands_N=int((far&covered).sum()),coverage=float((far&covered).sum()/max(1,far.sum())),historical_claim_far=239,historical_claim_covered=30,claim_reproduced=bool(far.sum()==239 and(far&covered).sum()==30),new_gradient_computed=False,saved_gradient_source=asset(old/'metrics/G03_GRADIENT_DIAGNOSTIC.npz'),source_initial=asset(old/'inputs'/n/'INITIAL.npz'),per_view=per,GT_used=False,prediction_changed=False)
    save('metrics/HISTORICAL_014_G03_RECOUNT.json',ans);np.savez_compressed(R/'metrics/HISTORICAL_014_G03_RECOUNT.npz',V=a['V'],F=a['F'],far=far,old_covered=covered,gradient=g['full_gradient']);print('RECOUNT',ans['far_associated_vertex_N'],ans['far_in_four_original_bands_N'],ans['claim_reproduced'],flush=True)
if __name__=='__main__':main()
