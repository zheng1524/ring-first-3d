"""G02 fixed-graph linearity, repeated backward and precision isolation."""
from tape import *
import inspect

def rel(a,b):return float((a-b).norm()/b.norm().clamp_min(1e-20))

def main():
 guard_optimizer();c=Case('G02');ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;obj.depth.begin(ch.mesh(q));rows=[];records=[]
 for cid in c.fit:
  tt,m=view_terms(c,ch,obj,q,cid);joint=sum(tt.values());repeated=[gradient(joint,q)for _ in range(5)];gg={k:gradient(v,q)for k,v in tt.items()};rows.append(dict(view=cid,sum_vs_joint=rel(sum(gg.values()),repeated[0]),repeat_max=max(rel(x,repeated[0])for x in repeated),norm=float(repeated[0].norm()),component_norms={k:float(g.norm())for k,g in gg.items()}))
  for k,v in tt.items():
   rep=[gradient(v,q)for _ in range(3)];records.append(dict(view=cid,component=k,repeat_relative=max(rel(x,rep[0])for x in rep),norm=float(rep[0].norm())))
 prior=obj.prior(ch.mesh(q));terms={k:(.01 if k in ['normal','unsupported']else 1.)*v for k,v in prior.items()};repeated=[gradient(sum(terms.values()),q)for _ in range(5)];separate={k:gradient(t,q)for k,t in terms.items()};prior_summary=dict(sum_vs_joint=rel(sum(separate.values()),repeated[0]),repeat_max=max(rel(g,repeated[0])for g in repeated),part_norms={k:float(g.norm())for k,g in separate.items()})
 for k,t in terms.items():
  rep=[gradient(t,q)for _ in range(5)];records.append(dict(view='PRIOR',component=k,repeat_relative=max(rel(x,rep[0])for x in rep),norm=float(rep[0].norm())))
 # Same rounded geometry, same objective, precision is the sole control.
 normals=[];reference=None;vrounded=c.base.verts_packed().detach()
 for dtype in [torch.float32,torch.float64]:
  v=vrounded.to(dtype).detach().clone().requires_grad_(True);m=Meshes(verts=[v],faces=[tensor(c.F,torch.int64)]);t=mesh_normal_consistency(m);gg=[gradient(t,v)for _ in range(6)]
  if dtype==torch.float64:reference=gg[0]
  normals.append(dict(dtype=str(dtype),value=float(t.detach()),repeat_relative=max(rel(g,gg[0])for g in gg),norm=float(gg[0].norm()),gradient=gg[0].double().cpu().numpy()))
 for a in normals:a['relative_error_to_FP64_same_geometry']=float(np.linalg.norm(a['gradient']-normals[-1]['gradient'])/max(1e-30,np.linalg.norm(normals[-1]['gradient'])))
 # Backend declaration is a further diagnostic, never a new training setting.
 declaration=[]
 torch.use_deterministic_algorithms(True)
 try:
  for cid in c.fit[:1]:
   try:
    ts,_=view_terms(c,ch,obj,q,cid);gradient(sum(ts.values()),q);declaration.append(dict(operation='rendered_view_joint',result='NO_BACKEND_ERROR_NOT_PROOF_OF_DETERMINISM'))
   except RuntimeError as e:declaration.append(dict(operation='rendered_view_joint',result='BACKEND_REJECTED',message=str(e)))
  try:gradient(relative_total(obj.prior(ch.mesh(q))),q);declaration.append(dict(operation='shape_prior',result='NO_BACKEND_ERROR_NOT_PROOF_OF_DETERMINISM'))
  except RuntimeError as e:declaration.append(dict(operation='shape_prior',result='BACKEND_REJECTED',message=str(e)))
 finally:torch.use_deterministic_algorithms(False)
 minimum=trimesh.Trimesh(c.V,c.F,process=False).area_faces.min();out=dict(case='G02',views=rows,component_repeats=records,prior=prior_summary,normal_same_geometry_precision=[{k:v for k,v in a.items()if k!='gradient'}for a in normals],deterministic_backend_declaration=declaration,min_face_area_mm2=float(minimum),optimizer_steps=0,GT_read=False,normal_implementation_file=inspect.getsourcefile(mesh_normal_consistency),interpretation_pending_measurements=True)
 save('metrics/G02_NUMERICAL_ISOLATION.json',out);np.savez_compressed(R/'metrics/G02_NORMAL_PRECISION_GRADIENTS.npz',V=c.V,F=c.F,FP32=normals[0]['gradient'],FP64_same_rounded_geometry=normals[1]['gradient']);print('NUMERIC_DIAG_DONE',prior_summary,normals[0]['repeat_relative'],flush=True)
if __name__=='__main__':main()
