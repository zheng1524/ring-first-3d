from hero_objective018 import *
import open3d as o3d
def configure(c):
 c.renderer.rasterizer.raster_settings.bin_size=0;c.hard.raster_settings.bin_size=0
 with torch.no_grad():
  for d in c.views.values():
   z=c.hard(c.ring,cameras=d['cam']).zbuf[0,...,0];valid=z>0;d.update(cad_z=torch.where(valid,z,torch.full_like(z,float('inf'))),cad_finite=valid)
def main():
 rows=[]
 for group in ['G06','G05','G01','G03']:
  c=Case(group);configure(c);ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),dtype=torch.float64,device=device,requires_grad=True);hero=HeroDepth018(c,ch,'TRUSTED');m=ch.mesh(q);s=scene(c.V,c.F)
  for cid,a in hero.obs.items():
   loss,info,data=hero.term(m,cid,True);g=torch.autograd.grad(loss,q,retain_graph=True)[0];ray=np.c_[a['uv'],np.ones(len(a['uv']))]@np.linalg.inv(a['K']).T;T=a['T'];rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);oz=s.cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();take=data['active']&np.isfinite(oz);err=abs(data['z'][take]-oz[take]);repeat=hero.term(ch.mesh(q),cid,True)[2];valid=(data['face_id']==repeat['face_id']);same=float(abs(data['z']-repeat['z']).max());row=dict(group=group,view=cid,active=int(take.sum()),O3D_P3D_depth=stats(err),repeat_depth_max_mm=same,repeat_face_ids_same=bool(valid.all()),full_parameter_gradient_finite=bool(torch.isfinite(g).all()),full_parameter_gradient_norm=float(g.norm()),native_samples=len(a['uv']),passed=bool(len(err)>0 and np.quantile(err,.95)<.003 and torch.isfinite(g).all()and same<1e-7));rows.append(row);assert row['passed'],row
  del c,ch,hero,m,q;torch.cuda.empty_cache()
 # Uncapped robust derivative and bounded missing-cost mathematical controls.
 x=torch.tensor([.2,2.,20.,200.],dtype=torch.float64,device=device,requires_grad=True);v=huber018(x);g=torch.autograd.grad(v.sum(),x)[0];assert (g>0).all()and torch.isfinite(g).all()
 save('metrics/P3D_HERO_PROJECTION_GRADIENT_GATE.json',dict(rows=rows,all29_passed=all(x['passed']for x in rows),uncapped_Huber_test=dict(residual=x.detach().cpu().numpy(),gradient=g.detach().cpu().numpy()),bin_size=0,world_interpolation=True,no_zbuf_as_mm=True,no_GT=True));print('ALL29_NATIVE_P3D_PROJECTION_GRADIENT_GATE_PASS',flush=True)
if __name__=='__main__':main()
