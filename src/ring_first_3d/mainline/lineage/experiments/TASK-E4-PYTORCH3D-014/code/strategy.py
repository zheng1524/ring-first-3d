"""Fixed, case-independent optimizer controls; all candidates use unchanged full guard."""
from free_model import *
def project_global(ch,before,d):
 V=ch.vertices(before).detach().cpu().numpy();dv=(ch.vertices(before+d)-ch.vertices(before)).detach().cpu().numpy();C=V.mean(0);B=[]
 for k in range(3):
  e=np.zeros_like(V);e[:,k]=1;B.append(e)
 for k in range(3):
  e=np.zeros_like(V);e[:,k]=V[:,k]-C[k];B.append(e)
 A=np.stack(B,axis=-1).reshape(-1,6);x=np.linalg.lstsq(A,dv.ravel(),rcond=1e-9)[0];out=(A@x).reshape(V.shape)
 # Chart projection retains inherited rim constraints for all models.
 return tensor(out,torch.float64)
def local_directions(ch,before,grad):
 g=grad.detach().cpu().numpy();scores=np.linalg.norm(g,axis=1);F=ch.c.F;edges=np.unique(np.sort(np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]],1),axis=0);adj=[set()for _ in g]
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 selected=set();out=[]
 for ix in np.argsort(-scores):
  if ix in selected:continue
  core={int(ix)};band=set(core)
  for _ in range(2):band|=set(j for i in list(band)for j in adj[i])
  selected|=band;mask=np.zeros(len(g));mask[list(band)]=1;dg=-.02*grad*tensor(mask[:,None],torch.float64);out.append(('LOCAL_'+str(len(out)),dg))
  if len(out)>=4:break
 return out
