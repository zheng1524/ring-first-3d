from contour_objective import *
from strategy import *
def main():
 guard_optimizer();rows=[]
 for name in ['G03','G01','G02']:
  c=Case(name);ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=Objective(c,ch)
  for cid in c.fit:
   d=c.views[cid];P=(c.V-d['T'][:3,3])@d['T'][:3,:3];u=P@d['Ksmall'].T;u=u[:,:2]/u[:,2:]+.5;screen=d['cam'].transform_points_screen(tensor((c.V-c.center)/c.scale))[0] if False else d['cam'].transform_points_screen(tensor((c.V-c.center)/c.scale))[...,:2];error=np.max(abs(screen.detach().cpu().numpy()-u));assert error<.01,(name,cid,error)
   print('PROJECTION_SCREEN_ERROR_PX',name,cid,error,flush=True)
  for arm in ['A0','A1','A2','A3']:
   obj.arm=arm;obj.contour=ContourDistance(c)if arm in ['A2','A3']else None;L,p=obj(q);g=torch.autograd.grad(L,q)[0];direction=g/g.norm().clamp_min(1e-20);eps=1e-4
   with torch.no_grad():plus=float(obj(q+eps*direction)[0]);minus=float(obj(q-eps*direction)[0])
   ad=float((g*direction).sum());fd=(plus-minus)/(2*eps);row=dict(case=name,loss_arm=arm,loss=float(L),gradient_norm=float(g.norm()),max_vertex_gradient=float(g.norm(dim=1).max()),finite=bool(torch.isfinite(g).all()),autodiff_direction=ad,finite_difference=fd,relative_FD_error=abs(fd-ad)/max(1e-8,abs(ad)),parts=p);rows.append(row)
   np.savez_compressed(R/'local_results'/('GRADIENT_'+name+'_'+arm+'.npz'),V=c.V,F=c.F,gradient=g.cpu().numpy(),q=q.detach().cpu().numpy());print(name,arm,row['gradient_norm'],row['relative_FD_error'],flush=True)
 save('metrics/GRADIENT_PREFLIGHT.json',dict(rows=rows,passed=all(x['finite']and x['gradient_norm']>0 for x in rows),FD_caveat='Full raster and visibility/nearest-edge membership are piecewise; finite differences recorded without hiding switches; no false exact-gradient claim'))
if __name__=='__main__':main()
