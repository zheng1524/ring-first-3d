from context import *
import open3d as o3d,trimesh

def scene(V,F):
 s=o3d.t.geometry.RaycastingScene(nthreads=1);s.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)));return s

def cast_points(s,uv,C,K):
 rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(C[:3,3],rays.shape),rays@C[:3,:3].T];return s.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))

def frozen_sources(g,onlyfit=True):
 conf=next(c for c in load(N/'config/FOUR_GROUP_INPUTS.json')if c['group']==g);out=[];H0=np.array(load(U/'config/H0.json')['G01_005_to004'])
 for s in conf['sources']:
  if onlyfit and (s['role']!='FIT' or s.get('evaluation_only',False)):continue
  assert sha(s['mesh']['path'])==s['mesh']['sha256'];m=dict(np.load(s['mesh']['path']));a=dict(np.load(s['observation']['path']));D=H0 if g=='G01'and s['video']=='005'else np.eye(4);V=m['V']@D[:3,:3].T+D[:3,3];C=D@a['T'];out.append(dict(id=s['id'],video=s['video'],role=s['role'],V=V,F=m['F'],C=C,K=a['K'],mesh=m,obs=a,source=s,normal=a['normal']@D[:3,:3].T,X=a['X']@D[:3,:3].T+D[:3,3],D=D))
 return conf,out

def multivis(a,b,ring):
 # Reuse021 visibility query; depth thresholds inherited0.5mm; reportotherbandsseparately.
 ns=extract(P/'code/evaluate020.py',['visibility_query'],dict(np=np,o3d=o3d));grid=np.full(tuple(b['obs']['native_shape']),np.nan);grid[b['obs']['uv'][:,1],b['obs']['uv'][:,0]]=b['obs']['z'];return ns['visibility_query'](a['X'],b['C'],b['obs']['K'],grid,ring)
