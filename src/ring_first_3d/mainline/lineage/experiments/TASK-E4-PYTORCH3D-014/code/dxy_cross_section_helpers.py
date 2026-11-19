# Read-only AST extraction; provenance in DXY_READONLY_REFERENCE.json
import numpy as np
RULE83={"normal_offsets":[3,5,9],"normal_cos_min":.8}

def smooth_normal(contour,i):
    normals=[]
    for k in RULE83['normal_offsets']:
        v=contour[(i+k)%len(contour)]-contour[(i-k)%len(contour)]
        if np.linalg.norm(v)<1:return None
        normals.append(np.array([-v[1],v[0]])/np.linalg.norm(v))
    n=normals[1]
    return n if min(abs(n@x) for x in normals)>=RULE83['normal_cos_min'] else None

def beyond(ring,p,v,maxd):
 h,w=ring.shape;seen=False
 for d in range(maxd+1):
  x,y=np.rint(p+v*d).astype(int)
  if x<0 or x>=w or y<0 or y>=h:return None
  if ring[y,x]:seen=True;continue
  if seen:return np.array([float(x),float(y)])
 return None
