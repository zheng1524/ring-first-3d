"""Post-freeze strengthening: one closed connected generic two-branch solid, no polyp prior."""
from native_multi import *
from types import SimpleNamespace

def main():
 cells={(x,y,z)for x in range(25)for y in range(10)for z in range(12)if(x<10 or x>=15 and z>=5 or 10<=x<15 and z>=10)};V=[];F=[];index={}
 templates=[((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]),((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)])]
 for c in sorted(cells):
  for direction,quad in templates:
   if tuple(c[j]+direction[j]for j in range(3))in cells:continue
   ids=[]
   for corner in quad:
    p=tuple(c[j]+corner[j]for j in range(3))
    if p not in index:index[p]=len(V);V.append(np.array([-1,-1,4.8])+.2*np.array(p))
    ids.append(index[p])
   F.extend([[ids[0],ids[1],ids[2]],[ids[0],ids[2],ids[3]]])
 V=np.array(V);F=np.array(F);m=trimesh.Trimesh(V,F,process=False);body=scene(V,F);C=np.eye(4);K=np.array([[100.,0,100],[0,100,100],[0,0,1.]]);X=np.array([[0,0,4.8],[3,0,5.8],[0,0,7.2]]);uv,z=project(X,C,K);mask=np.isfinite(cast(body,K,C,201,201))
 def foreground(P):
  p,d=project(P,C,K);p=np.rint(p).astype(int);valid=(p[:,0]>=0)&(p[:,0]<201)&(p[:,1]>=0)&(p[:,1]<201)&(d>0);out=np.zeros(len(P),bool);out[valid]=mask[p[valid,1],p[valid,0]];return out
 s=SimpleNamespace(id='generic_connected_two_branches',C=C,K=K,uv=uv,sub=np.arange(3),z0=z,A=np.c_[np.ones(3),X[:,:2]/z[:,None]],ray=X/z[:,None],o={'X':X},theta=np.zeros(3),peer_conflict=np.zeros(3,bool),points=lambda:X,normals=lambda:np.array([[0,0,-1.],[0,0,-1.],[0,0,1.]]),mask_at=foreground);far=trimesh.creation.box();far.apply_translation([1000]*3);corr=correspond(s,V,F,body,scene(far.vertices,far.faces));theta,info=bias_proposal(s,corr);ok=m.is_watertight and m.is_winding_consistent and len(m.split())==1 and corr['state'].tolist()==[0,0,1] and info['status']=='INSUFFICIENT_CONSTRAINT'and np.array_equal(theta,np.zeros(3));save('metrics/CONNECTED_BRANCH_CONTROL.json',dict(PASS=bool(ok),watertight=m.is_watertight,components=len(m.split()),states=corr['state'],expected='two separate visible branches MATCHED; rear/occluded branch UNEXPLAINED; weak global calibration stays native',bias_status=info['status'],GT_use='synthetic control construction only; after real predictions freeze, no input to real optimization',body_vertices=len(V),body_faces=len(F)));np.savez_compressed(R/'local_results/CONNECTED_BRANCH_CONTROL.npz',V=V,F=F,query_X=X,state=corr['state']);assert ok;print('CONNECTED_BRANCH_CONTROL',ok,flush=True)
if __name__=='__main__':main()
