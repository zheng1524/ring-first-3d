"""Shared metric, first-visible-surface evidence; no registration, fusion or repair."""
from common import *
from evaluate020 import visibility_query,contour_stats
import open3d as o3d
import collections,types,importlib,ast
P18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018';P20=REPO/'experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020'
GROUPS=['G01','G03','G05','G06']
VIS_NAMES=['SUPPORTED_PROXY','FRONT_DISAGREEMENT_PROXY','DEEPER_SELF_OCCLUSION_POSSIBLE','CAD_OCCLUDED','UNKNOWN','MIXED_SUPPORT_FRONT']
VIS_COLORS=np.array([[.15,.72,.35],[.90,.16,.15],[.23,.48,.88],[.53,.32,.7],[.65,.65,.65],[1.,.66,.10]])

def wait_freeze():
 while not(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json').exists():time.sleep(5)
 for a in load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')['files']:assert sha(a['path'])==a['sha256']

def group_data(group,transform=None):
 conf=next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group);H=np.eye(4)if transform is None else np.asarray(transform);out=[];vv={v['id']:v for v in load(R/'config/VIEWS.json')}
 for s in conf['sources']:
  assert sha(s['mesh']['path'])==s['mesh']['sha256']and sha(s['observation']['path'])==s['observation']['sha256'];a=dict(np.load(s['observation']['path']));m=dict(np.load(s['mesh']['path']));G=H if s['video']=='005'else np.eye(4);grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z'];meta=s.get('meta',vv.get(s['id'],{}));cache=s.get('cache',meta.get('cache'));X=a['X']@G[:3,:3].T+G[:3,3];V=m['V']@G[:3,:3].T+G[:3,3];out.append(dict(id=s['id'],source=s,obs=a,mesh=m,X=X,V=V,F=m['F'],C=G@a['T'],G=G,grid=grid,video=s['video'],role=s['role'],meta=meta,cache=cache))
 return conf,out

def rays(uv,K,C):
 d=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;return o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],d.shape),d@C[:3,:3].T].astype(np.float32))

def mapped_labels(labels,K,Kn,shape):
 y,x=np.mgrid[:shape[0],:shape[1]];uv=np.c_[x.ravel(),y.ravel()];q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(Kn).T@K.T;q=q[:,:2]/q[:,2:];px=np.floor(q+.5).astype(int);inside=(px[:,0]>=0)&(px[:,0]<labels.shape[1])&(px[:,1]>=0)&(px[:,1]<labels.shape[0]);lab=np.full(len(uv),255,np.uint8);lab[inside]=labels[px[inside,1],px[inside,0]];return lab.reshape(shape)

def cpu_curve_distance(obs,V,edges,C,K):
 if not len(obs)or not len(edges):return np.full(len(obs),np.nan)
 p=(V[edges]-C[:3,3])@C[:3,:3];q=p@K.T;q=q[...,:2]/q[...,2:];a,b=q[:,0],q[:,1];v=b-a;out=[]
 for i in range(0,len(obs),256):
  D=obs[i:i+256,None]-a[None];t=np.sum(D*v[None],axis=-1)/np.maximum(np.sum(v*v,axis=-1),1e-12);out.extend(np.sqrt(np.min(np.sum((D-np.clip(t,0,1)[...,None]*v[None])**2,axis=-1),axis=-1)))
 return np.array(out)

def actual_ring_points(v,diameter):
 path=R/'group_ring_evidence'/(v['view_id']+'.npz');path.parent.mkdir(exist_ok=True)
 if path.exists():return dict(np.load(path))
 cache=np.load(v['cache']);mod=types.ModuleType('dxy_mid');mod.__path__=['/home/liu/new-polyp-dxy/src/dxy_mid'];sys.modules.setdefault('dxy_mid',mod);recover=importlib.import_module('dxy_mid._engine.ring_component').recover;cv2.setRNGSeed(20261111);np.random.seed(20261111);report,payload=recover(cache['labels'],cache['RGB'][:,:,::-1],diameter);raw=contour(cache['labels']==2);tree=cKDTree(raw);e={}
 for name in ['inner','outer']:
  p=np.asarray(payload.get(name+'_points',np.empty((0,2))));dist,idx=tree.query(p);e[name]=np.unique(raw[idx[dist<=2.5]],axis=0);e[name+'_unsupported']=p[dist>2.5]
 np.savez_compressed(path,**e);save('group_ring_evidence/'+v['view_id']+'.json',dict(original_DXY=report,diameter_mm=diameter,no_2D_DXY_measurement_used=True,Mask_boundary_snap_limit_px=2.5,source=asset(Path('/home/liu/new-polyp-dxy/src/dxy_mid/_engine/ring_component.py'))));return e

def body_quality(V,F,solid,V0,ringV,ringF):
 # Same mature 018 adaptive CAD sample audit, with 11 parity rays (020 fix).
 path=P18/'code/safe_geometry.py';tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='dense_face_distance');src=ast.get_source_segment(path.read_text(),node).replace('nsamples=3','nsamples=11');space=dict(np=np,o3d=o3d);exec(compile(src,str(path)+':reused_dense_face_distance','exec'),space);sd=space['dense_face_distance'](scene(ringV,ringF),V,solid,ringV,64,ringF)
 mm=trimesh.Trimesh(V,solid,process=False);o=o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V),o3d.utility.Vector3iVector(solid));si=np.asarray(o.get_self_intersecting_triangles()).reshape(-1,2);tri=V[solid];t0=V0[solid];area=trimesh.triangles.area(tri);a0=trimesh.triangles.area(t0);edge=np.linalg.norm(tri[:,[1,2,0]]-tri,axis=2);e0=np.linalg.norm(t0[:,[1,2,0]]-t0,axis=2);qual=4*np.sqrt(3)*area/np.maximum((edge*edge).sum(1),1e-20);_,counts=np.unique(np.sort(np.r_[solid[:,[0,1]],solid[:,[1,2]],solid[:,[2,0]]],axis=1),axis=0,return_counts=True);visible_set=set(map(tuple,F.tolist()));cap=np.array([tuple(f)not in visible_set for f in solid])
 try:
  cm=trimesh.collision.CollisionManager();cm.add_object('CAD',trimesh.Trimesh(ringV,ringF,process=False));collision=bool(cm.in_collision_single(mm));cstatus='COMPUTED_FCL'
 except Exception as e:collision=None;cstatus='MISSING_FCL:'+str(e)
 out=dict(visible_faces_N=len(F),solid_faces_N=len(solid),vertices_N=len(V),inferred_cap_faces_N=int(cap.sum()),area_visible_mm2=float(trimesh.triangles.area(V[F]).sum()),watertight=bool(mm.is_watertight),winding_consistent=bool(mm.is_winding_consistent),components_N=len(mm.split(only_watertight=False)),nonmanifold_edges_N=int((counts>2).sum()),boundary_edges_N=int((counts==1).sum()),self_intersection_pairs_N=len(si),Ring_FCL_surface_collision=collision,Ring_collision_engine=cstatus,Ring_dense_min_mm=float(sd.min()),Ring_dense_inside_faces_N=int((sd<-.001).sum()),Ring_diagnostic_tolerance_mm=.001,max_vertex_displacement_mm=float(np.linalg.norm(V-V0,axis=1).max()),mean_vertex_displacement_mm=float(np.linalg.norm(V-V0,axis=1).mean()),max_edge_stretch=float((edge/np.maximum(e0,1e-12)).max()),min_area_ratio=float((area/np.maximum(a0,1e-12)).min()),triangle_quality=stats(qual),geometry_accuracy='NOT_EVALUABLE_NO_GT')
 return out,dict(Ring_face_min_mm=sd,quality=qual,area_ratio=area/np.maximum(a0,1e-12),edge_stretch=(edge/np.maximum(e0,1e-12)).max(1),self_intersection_pairs=si,displacement_mm=np.linalg.norm(V-V0,axis=1))
