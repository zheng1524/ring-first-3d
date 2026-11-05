from p3d import *
from types import SimpleNamespace

def controls(c):
    """Transparent one-pixel fragment controls through the SAME loss, not a new dataset."""
    d=next(iter(c.views.values()));original={k:d[k]for k in['cad_z','cad_finite','classes','target']};rows=[]
    for label,cls,target,hascad,delta in [('behind_A',1,0,True,.5),('front_A',1,0,True,-.5),('front_B',2,0,True,-.025),('A_noCAD',1,0,False,0),('B_noCAD',2,0,False,0),('C_noCAD',3,0,False,0),('D_noCAD',4,0,False,0),('visible_polyp',2,1,False,0),('CAD_only_C_behind',3,0,True,.5)]:
        # dists inside a soft edge, not a saturated interior; depth in normalized units.
        ds=tensor(np.array([[[-1e-4]]])).requires_grad_();z=tensor(np.array([[[2.+delta/c.scale]]])).requires_grad_()
        fr=SimpleNamespace(pix_to_face=tensor([[[[0]]]],torch.int64),dists=ds[None],zbuf=z[None])
        d.update(cad_z=tensor([[2.]]),cad_finite=tensor([[hascad]],torch.bool),classes=tensor([[cls]],torch.int64),target=tensor([[target]]))
        loss=c.aware(fr,next(iter(c.views)));gg=torch.autograd.grad(loss,[ds,z],allow_unused=True)
        rows.append(dict(control=label,loss=float(loss.detach()),dLoss_dSquaredNDCdist=float(gg[0].item()),dLoss_dZnormalized=float(gg[1].item()) if gg[1] is not None else 0.,finite=all(g is None or torch.isfinite(g).all().item()for g in gg)))
    d.update(original)
    by={r['control']:r for r in rows}
    passed=all(r['finite']for r in rows)and abs(by['behind_A']['dLoss_dSquaredNDCdist'])<1e-5*abs(by['front_A']['dLoss_dSquaredNDCdist'])and by['front_B']['dLoss_dSquaredNDCdist']!=0 and all(abs(by[s]['dLoss_dSquaredNDCdist'])==0 for s in ['A_noCAD','B_noCAD','D_noCAD'])and by['C_noCAD']['dLoss_dSquaredNDCdist']!=0 and by['visible_polyp']['dLoss_dSquaredNDCdist']!=0
    return rows,bool(passed)
def main():
    assert load(R/'metrics/OCCLUSION_AUDIT.json')['optimization_started']==False
    rows=[];control=[];passed=True
    for name in['virtual','real']:
        c=Case(name);rr,ok=controls(c);control.extend([dict(case=name,**r)for r in rr]);passed&=ok
        for cid in c.fit:
            grads={}
            for arm in['Baseline','RingAware']:
                off=torch.zeros_like(c.base.verts_packed(),requires_grad=True);m=c.base.offset_verts(off);l=c.loss(m,cid,arm);g=torch.autograd.grad(l,off,retain_graph=True)[0];grads[arm]=g
                pri=regularizers(m);pl=pri['edge']+.01*pri['normal']+pri['laplacian'];pg=torch.autograd.grad(pl,off,retain_graph=True)[0]
                vertices=m.verts_packed();faces=m.faces_packed();tri=vertices[faces];vol=(tri[:,0]*torch.cross(tri[:,1],tri[:,2],dim=1)).sum()/6*c.scale**3;vg=torch.autograd.grad(vol,off)[0]
                row=dict(case=name,view=cid,arm=arm,loss=float(l.detach()),full_vertex_gradient_norm=float(g.norm()),finite=bool(torch.isfinite(g).all()),nonzero_vertex_N=int((g.norm(dim=1)>0).sum()),official_prior_loss=float(pl.detach()),official_prior_gradient_norm=float(pg.norm()),silhouette_first_order_volume_change_mm3=float(-(vg*g).sum()),prior_first_order_volume_change_mm3=float(-(vg*pg).sum()),first_order_caveat='diagnostic only, lr=1 no momentum at first step; actual nonlinear volume measured independently')
                rows.append(row);passed&=row['finite']and row['full_vertex_gradient_norm']>0
            rows[-1]['gradient_difference_norm']=float((grads['Baseline']-grads['RingAware']).norm())
    # Stability guard is diagnostic, never gradient clipping or loss adjustment.
    for name in ['virtual','real']:
        for cid in [r['view'] for r in rows if r['case']==name and r['arm']=='Baseline']:
            a=next(r for r in rows if r['view']==cid and r['arm']=='Baseline');b=next(r for r in rows if r['view']==cid and r['arm']=='RingAware');passed &= b['full_vertex_gradient_norm'] <= 100*a['full_vertex_gradient_norm']
    table('metrics/FULL_VERTEX_GRADIENTS.csv',rows);table('metrics/OCCLUSION_GRADIENT_CONTROLS.csv',control)
    save('metrics/GRADIENT_GATE.json',dict(passed=bool(passed),rows=rows,controls=control,scope='All actual mesh vertex parameters; one-pixel controls use same fragment loss. No optimizer step.'))
    print('Gradient gate',passed,flush=True)
if __name__=='__main__':main()
