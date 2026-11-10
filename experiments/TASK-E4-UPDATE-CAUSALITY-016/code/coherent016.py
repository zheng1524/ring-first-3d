"""Contact-face-fixed Sobolev proposals; unchanged objective and final GeometryGuard."""
from free_model import *
from scipy import sparse
from scipy.sparse.linalg import splu

def coherent_directions(ch,before,directions,guard):
 F=ch.c.F_solid;contact=guard.lastsd<.02;pin=np.zeros(ch.N,bool)
 if contact.any():pin[np.unique(F[contact])]=True
 edges=guard.edges;adj=sparse.coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(ch.N,ch.N)).tocsr();degree=np.asarray(adj.sum(1)).ravel();L=(sparse.diags(degree)-adj)/max(1.,float(np.median(degree[degree>0])));K=sparse.eye(ch.N,format='csr')+L;free=np.flatnonzero(~pin);out=[];records=[]
 if not len(free):return[],dict(pinned_vertex_N=int(pin.sum()),free_N=0)
 solve=splu(K[free][:,free].tocsc());v0=ch.vertices(before).detach()
 for key,d in directions:
  a=d.detach().cpu().numpy();b=np.zeros_like(a);b[free]=solve.solve(a[free]);td=tensor(b,torch.float64);oldmove=float((ch.vertices(before+d).detach()-v0).norm(dim=1).max());newmove=float((ch.vertices(before+td).detach()-v0).norm(dim=1).max())
  if newmove<1e-15:continue
  td*=min(oldmove,ch.tau)/newmove
  out.append(('PCOH_'+key,td));mm=td.cpu().numpy();records.append(dict(raw_method=key,raw_max_mm=oldmove,new_max_mm=min(oldmove,ch.tau),raw_edge_jump_norm=float(np.linalg.norm(a[edges[:,0]]-a[edges[:,1]])),new_edge_jump_norm=float(np.linalg.norm(mm[edges[:,0]]-mm[edges[:,1]])),pinned_delta_max_mm=float(np.linalg.norm(mm[pin],axis=1).max())if pin.any()else 0.))
 return out,dict(pinned_vertex_N=int(pin.sum()),free_N=len(free),contact_face_N=int(contact.sum()),lambda_sobolev=1.,contact_margin_mm=.02,projection='Dirichlet coordinate subspace; not exact projection onto the full nonlinear feasible set',proposals=records)
