from free_model import *

def main():
 guard_optimizer();rows=[]
 for meta in load(R/'config/CASE_LOCK.json'):
  c=Case(meta['name']);ch=FreeVertices(c);obj=Objective(c,ch);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);t=time.time();L,p=obj(q);L.backward();g=q.grad.detach();V=ch.vertices(q).detach().cpu().numpy();same=np.max(abs(V-c.V));good=bool(torch.isfinite(L)and torch.isfinite(g).all()and g.norm()>0);old=R.parent/'CAP_REPAIR_STABLE_011';src=np.load(old/'local_results'/c.name/'FINAL.npz');exact=np.array_equal(c.V,src['V'])and np.array_equal(c.F,src['F']);tests=dict(initial_is_exact_011FINAL=exact,initial_chart_error_mm=float(same),finite_nonzero_full_vertex_gradient=good,gradient_nonzero_vertex_N=int((g.norm(dim=1)>0).sum()),visible_vertex_N=len(ch.used),allocated_parameter_N=3*ch.N,independent_parameter_N=3*len(ch.used)-int(c.boundary.sum())if ch.cap else 3*ch.N,forward_backward_seconds=time.time()-t)
  # A controlled arithmetic probe only: no optimizer updates or parameter mutation.
  probe=torch.linspace(-.001,.001,3*ch.N,device=device,dtype=torch.float64).reshape(ch.N,3);pv=ch.vertices(probe).detach().cpu().numpy()
  if ch.cap:tests['rim_plane_error_mm']=float(abs(pv[c.boundary]@ch.plane[:3]+ch.plane[3]).max());assert tests['rim_plane_error_mm']<1e-7
  assert exact and same<1e-10 and good
  rows.append(dict(case=c.name,**tests));print(c.name,tests,flush=True)
 save('metrics/PREFLIGHT.json',dict(passed=True,optimizer_updates=0,cases=rows));table('metrics/PREFLIGHT.csv',rows)

if __name__=='__main__':main()
