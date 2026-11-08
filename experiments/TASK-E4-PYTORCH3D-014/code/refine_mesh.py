"""One official global subdivision or one BMesh local interpolation from FIT evidence."""
from multiview import *
from scipy.sparse.csgraph import connected_components
from scipy import sparse
import subprocess
MASTER=Path(__file__).resolve().parents[1]
BLENDER='/home/liu/blender/blender-5.0.1-linux-x64/blender'
def restore_bmesh_interpolation(V,F,W,G,parent):
 """Restore exact double-precision edge/face interpolation using BMesh lineage."""
 assert np.linalg.norm(W[:len(V)]-V,axis=1).max()<1e-4;original_float=W.copy();W=W.copy();W[:len(V)]=V;incidence=[set()for _ in W]
 for face,pid in zip(G,parent):
  for index in face:incidence[index].add(int(pid))
 for index in range(len(V),len(W)):
  parents=sorted(incidence[index]);shared=set(F[parents[0]])
  for pid in parents[1:]:shared&=set(F[pid])
  if len(shared)==2:W[index]=V[sorted(shared)].mean(0)
  elif len(shared)==3:
   tri=V[F[parents[0]]];candidates=np.r_[(tri+np.roll(tri,-1,axis=0))*.5,tri.mean(0,keepdims=True)];W[index]=candidates[np.linalg.norm(candidates-original_float[index],axis=1).argmin()]
  else:raise RuntimeError('Unexpected BMesh vertex/parent incidence; do not guess face lineage')
 assert np.linalg.norm(W-original_float,axis=1).max()<1e-4,'BMesh output is not interpolation on its actual parent edge/face'
 return W
def flags(c,ch):
 V=tensor(c.V,torch.float64).requires_grad_(True);cd=ContourDistance(c);signal=np.zeros(len(c.V));count=np.zeros(len(c.V),int);perview=[]
 for cid in c.fit:
  loss,rec=cd(V,cid);g=torch.autograd.grad(loss,V,allow_unused=True)[0];norm=np.linalg.norm(g.detach().cpu().numpy(),axis=1)if g is not None else np.zeros(len(c.V));nz=norm[norm>1e-15];threshold=float(np.quantile(nz,.75))if len(nz)else np.inf;count+=norm>=threshold;signal+=norm/(norm.max()+1e-20);perview.append(dict(view=cid,gradient_nonzero_N=int((norm>1e-15).sum()),threshold=threshold))
 eligible=count>=2;score=signal.copy();top=np.flatnonzero(eligible);top=top[np.argsort(-score[top])[:max(1,int(.2*len(c.V)))]];selected_vertex=np.zeros(len(c.V),bool);selected_vertex[top]=True;selected=selected_vertex[c.F_solid].any(1)
 initial=np.load(MASTER/'inputs'/c.name/'INITIAL.npz');stretch=np.ones(len(c.F_solid))
 if np.array_equal(initial['F_solid'],c.F_solid):
  for i,j in [(0,1),(1,2),(2,0)]:
   e=c.F_solid[:,[i,j]];stretch=np.maximum(stretch,np.linalg.norm(c.V[e[:,0]]-c.V[e[:,1]],axis=1)/np.maximum(np.linalg.norm(initial['V'][e[:,0]]-initial['V'][e[:,1]],axis=1),1e-12))
 selected|=(stretch>1.5)&(count[c.F_solid].max(1)>0);selected[c.inferred]=False
 return selected,dict(signal=signal,view_count=count,edge_stretch=stretch,per_view=perview)

def prepare(name,arm,source,targetroot):
 c=Case(name);a=dict(np.load(source));V,F=a['V'],a['F_solid'];c.V=V;c.F=a['F'];c.F_solid=F;c.inferred=a['inferred_base_faces'];c.boundary=a['boundary_vertex'];c.base=mesh((V-c.center)/c.scale,c.F);ch=FreeVertices(c);mask,diag=flags(c,ch);folder=MASTER/'runtime/refinement'/name;folder.mkdir(parents=True,exist_ok=True);request=folder/'REQUEST.npz';np.savez_compressed(request,V=V,F_solid=F,selected_faces=mask,signal=diag['signal'],view_count=diag['view_count'],edge_stretch=diag['edge_stretch']);out=folder/(arm+'.npz')
 if arm=='E0_none':W,G=V.copy(),F.copy();parent=np.arange(len(F))
 elif arm=='E1_global':
  from pytorch3d.ops import SubdivideMeshes
  # Official operation, no smoothing. Mesh generator only, not a learned model.
  original=Meshes(verts=[tensor(V,torch.float64)],faces=[tensor(F,torch.int64)]);edges=original.edges_packed().detach().cpu().numpy();mm=SubdivideMeshes()(original);W=mm.verts_packed().detach().cpu().numpy().astype(float);G=mm.faces_packed().detach().cpu().numpy();assert np.allclose(W[:len(V)],V,atol=1e-12);assert np.allclose(W[len(V):],V[edges].mean(1),atol=1e-12);mapping={tuple(sorted(f)):i for i,f in enumerate(F)};parent=[]
  for f in G:
   ids=set()
   for k in f:ids.update([int(k)]if k<len(V)else edges[k-len(V)].tolist())
   parent.append(mapping[tuple(sorted(ids))])
  parent=np.asarray(parent,int)
 else:
  subprocess.run([BLENDER,'-b','--factory-startup','-t','2','--python',str(MASTER/'code/bmesh_subdivide.py'),'--',str(request),str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);zz=np.load(out);W,G=zz['V'],zz['F_solid'];parent=zz['parent_coarse_face'];assert(parent>=0).all()and(parent<len(F)).all()
  # BMesh stores float32 coordinates. Re-express its interpolation in the
  # original double-precision triangles; keep old vertices exactly unchanged.
  W=restore_bmesh_interpolation(V,F,W,G,parent)
 oldscene=scene(V,F);inf=c.inferred[parent];body=G[~inf];edges=np.sort(np.r_[body[:,[0,1]],body[:,[1,2]],body[:,[2,0]]],axis=1);ed,nn=np.unique(edges,axis=0,return_counts=True);boundary=np.zeros(len(W),bool)
 if c.inferred.any():boundary[np.unique(ed[nn==1])]=True
 newmesh=trimesh.Trimesh(W,G,process=False);oldmesh=trimesh.Trimesh(V,F,process=False);oldsample=np.r_[V,V[F].mean(1),V[F[:,[0,1]]].mean(1),V[F[:,[1,2]]].mean(1),V[F[:,[2,0]]].mean(1)];newscene=scene(W,G);d1=oldscene.compute_distance(__import__('open3d').core.Tensor(W.astype(np.float32))).numpy();d2=newscene.compute_distance(__import__('open3d').core.Tensor(oldsample.astype(np.float32))).numpy();zero=float(max(d1.max(),d2.max()));assert zero<1e-4,'Subdivision altered shape'
 nearest=cKDTree(W).query(V)[1];assert np.linalg.norm(W[nearest]-V,axis=1).max()<1e-4
 # Interpolate every fine node from the exact shared coarse triangle. This is
 # only a density-invariant prior reference, never a generated prediction.
 cp=scene(V,c.F).compute_closest_points(__import__('open3d').core.Tensor(W.astype(np.float32)));fi=cp['primitive_ids'].numpy().astype(int);uv=cp['primitive_uvs'].numpy();iv=c.F[np.minimum(fi,len(c.F)-1)];bary=np.c_[1-uv.sum(1),uv];tri=W[G];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;aw=np.zeros(len(W));np.add.at(aw,G.ravel(),np.repeat(area/3,3));body_ref=targetroot/'inputs'/name;body_ref.mkdir(exist_ok=True)
 dest=body_ref/'INITIAL.npz'
 if dest.is_symlink():dest.unlink()
 np.savez_compressed(dest,V=W,F=body,F_solid=G,inferred_base_faces=inf,boundary_vertex=boundary,parent_coarse_face=parent)
 # Only body vertices enter regularization; cap-center interpolation is
 # bookkeeping and is excluded from fine residual by zero weight.
 aw[np.setdiff1d(np.arange(len(W)),np.unique(body))]=0
 np.savez_compressed(body_ref/'SHAPE_REFERENCE.npz',coarse_V=V,coarse_faces=c.F,anchors=nearest,interp_vertices=iv,bary=bary,vertex_area_weights=aw)
 rec=dict(case=name,arm=arm,before_vertices=len(V),after_vertices=len(W),before_faces=len(F),after_faces=len(G),selected_faces=int(mask.sum()),max_coarse_edge_stretch=float(diag['edge_stretch'].max()),selected_area_fraction=float(oldmesh.area_faces[mask].sum()/oldmesh.area),subdivision_only_surface_deviation_mm=zero,relative_area_change=float(newmesh.area/oldmesh.area-1),absolute_volume_change_mm3=float(newmesh.volume-oldmesh.volume),watertight=newmesh.is_watertight,winding_consistent=newmesh.is_winding_consistent,GT_used=False,source=str(source),density_prior='common coarse restriction + area-normalized fine residual, optimizer reset',per_view=diag['per_view']);p=MASTER/'metrics/refinement'/ (name+'_'+arm+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(rec),indent=2));np.savez_compressed(folder/(arm+'_SIGNAL.npz'),V=V,F=F,selected=mask,signal=diag['signal'],view_count=diag['view_count'],edge_stretch=diag['edge_stretch']);return rec

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('arm');p.add_argument('source');p.add_argument('targetroot');a=p.parse_args();prepare(a.case,a.arm,Path(a.source),Path(a.targetroot))
