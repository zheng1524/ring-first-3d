"""Compose video-level transforms and slice shared group tracks without relabeling."""
import numpy as np
def connect(videos,reference,edges):
 out={v:dict(T=None,path=[],status='UNCONNECTED')for v in videos}
 out[reference]=dict(T=np.eye(4),path=[reference],status='REFERENCE')
 changed=True
 while changed:
  changed=False
  for (a,b),t in edges.items():
   if t is None:continue
   for parent,child,rel in [(a,b,np.asarray(t)),(b,a,np.linalg.inv(t))]:
    if out[parent]['T']is not None and out[child]['T']is None:
     out[child]=dict(T=out[parent]['T']@rel,path=[child]+out[parent]['path'],status='CONNECTED');changed=True
 return out
def pair_view(frames,poses,tr,a,b):
 ids=[i for side in [a,b]for i,f in enumerate(frames)if f['case']==side]
 ff=[dict(frames[i],side='A'if frames[i]['case']==a else'B',id=('A'if frames[i]['case']==a else'B')+'__'+frames[i]['id'].split('__',1)[1])for i in ids]
 return ff,poses[ids],dict(tr,xy=tr['xy'][:,ids].copy())
