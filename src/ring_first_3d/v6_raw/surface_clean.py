"""Three preregistered single-source trials. Original vertices and face subsets only."""
from pathlib import Path
import json,types,time
import numpy as np

def native_mapping(uv,native_height,working_height):
 y=(uv[:,1]+.5)*native_height/working_height-.5
 lo=np.clip(np.floor(y).astype(int),0,native_height-1);hi=np.clip(np.floor(y).astype(int)+1,0,native_height-1);w=y-np.floor(y)
 nearest=np.c_[uv[:,0],np.clip(np.floor(y+.5).astype(int),0,native_height-1)]
 return nearest,lo,hi,w

def candidate_faces(f,opposition,support,confirmed):
 stretched=(f['perspective_stretch']>4)|(f['native_depth_jump_mm']>.5)
 return (confirmed | (stretched & (opposition>=2))) & (support<2) & ~f['CAD_occluded']

def components_and_boundary(V,F):
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 if not len(F):return dict(faces=0,components=0,boundary_edges=0,boundary_components=0,area_mm2=0.)
 edge,counts=np.unique(np.sort(F[:,[[0,1],[1,2],[2,0]]].reshape(-1,2),axis=1),axis=0,return_counts=True);be=edge[counts==1]
 def cc(e):
  if not len(e):return 0
  _,ix=np.unique(e,return_inverse=True);ix=ix.reshape(-1,2);a,b=ix.T;n=ix.max()+1
  return int(connected_components(coo_matrix((np.ones(2*len(a)),(np.r_[a,b],np.r_[b,a])),shape=(n,n)),directed=False,return_labels=False))
 tri=V[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 return dict(faces=len(F),components=cc(edge),boundary_edges=len(be),boundary_components=cc(be),area_mm2=float(area.sum()))

def silhouette_evidence(V,F,R,reference,cad):
 import cv2,open3d as o3d
 from scipy.ndimage import distance_transform_edt
 from .route import read,K
 L=read(R/'inputs/ledger005.json');gates=read(R/'metrics/GATES.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];C=np.load(R/f'predictions/local005_camera_{primary}.npz')['c2w'];scene=o3d.t.geometry.RaycastingScene(nthreads=1);scene.add_triangles(o3d.core.Tensor(cad['V'].astype(np.float32)),o3d.core.Tensor(cad['F'].astype(np.uint32)))
 points=np.concatenate([V[F],V[F].mean(1)[:,None]],axis=1);X=points.reshape(-1,3);opposition=np.zeros(len(F),np.uint16);support=np.zeros(len(F),np.uint16);unknown=np.zeros(len(F),np.uint16);records=[];perview=[]
 for i,g in enumerate(gates):
  if i==reference or not g['new_pass']:continue
  T=C[i];cam=(X-T[:3,3])@T[:3,:3];q=cam@K.T;uv=q[:,:2]/q[:,2:];finite=np.isfinite(uv).all(1)&np.isfinite(cam).all(1);inside=finite&(cam[:,2]>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);ids=np.flatnonzero(inside);pix=np.clip(np.floor(uv[ids]+.5).astype(int),[0,0],[639,359]);lab=cv2.imread(L[i]['Mask_path'],0);labels=np.full(len(X),255,np.uint8);dist=np.zeros(len(X));labels[ids]=lab[pix[:,1],pix[:,0]];dm=distance_transform_edt(lab!=1);dist[ids]=dm[pix[:,1],pix[:,0]]
  rays=np.c_[uv[ids],np.ones(len(ids))]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(T[:3,3],rays.shape),rays@T[:3,:3].T];hit=scene.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy();hidden=np.zeros(len(X),bool);hidden[ids]=np.isfinite(hit)&(cam[ids,2]>hit+.05)
  visible=(inside&~hidden).reshape(-1,4).all(1);opp=visible&((labels==0)&(dist>3)).reshape(-1,4).all(1);sup=visible&(labels==1).reshape(-1,4).all(1);unk=~(opp|sup)
  opposition+=opp;support+=sup;unknown+=unk;perview.append(np.c_[opp,sup,unk]);records.append(dict(index=i,raw_frame=L[i]['raw_frame'],opposed_faces=int(opp.sum()),supported_faces=int(sup.sum()),unknown_faces=int(unk.sum()),camera_admission='Q1; conditional, not independent truth',GT_used=False))
 return opposition,support,unknown,records,np.asarray(perview,dtype=np.uint8)

def mapped_input_for_source(c,out=None):
 """Existing V6 archived-Mesh adapter, shared without invoking any clean rule."""
 import cv2,trimesh
 from . import route as r
 from ..mainline.native.geometry import resize_index_intrinsics
 R=Path(c['run']);tag=c['tag'];
 if out is not None:out.mkdir(parents=True,exist_ok=True)
 meshpath=R/'meshes'/(tag+'_Polyp.ply');nativepath=R/'raw'/(tag+'.npz');assert r.sha(meshpath)==c['mesh_sha256'] and r.sha(nativepath)==c['native_sha256']
 a=dict(np.load(nativepath));z=a['depth_mm'].squeeze();assert z.ndim==2;L=r.read(R/'inputs/ledger005.json');i=int(a['reference']);row=L[i];rgb=cv2.cvtColor(cv2.imread(row['RGB_path']),cv2.COLOR_BGR2RGB);labels=cv2.imread(row['Mask_path'],0);assert rgb.shape[:2]==labels.shape
 nh,nw=z.shape;wh,ww=labels.shape;assert nw==ww,'native_mapping supports the actual V6 unchanged-width contract'
 zw=cv2.resize(z.astype(float),(ww,wh),interpolation=cv2.INTER_LINEAR);T=a['c2w'][i];K=a['K_full'];Kn=a['K_index_native'];assert np.allclose(Kn,resize_index_intrinsics(K,labels.shape,z.shape),atol=1e-10),'NATIVE_K_RESIZE_MISMATCH';valid=(labels==1)&np.isfinite(zw)&(zw>0);y,x=np.nonzero(valid);uv=np.c_[x,y]
 m=trimesh.load(meshpath,process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces);old=r.legacy();mods=r.bind(old,R,r.read(R/'inputs/INPUT_IDENTITY.json'));reconstructed=mods['v6'].depth_mesh(zw,valid,T,rgb)
 assert np.array_equal(F,reconstructed.faces),'ORIGINAL_FACE_ORDER_MISMATCH';assert np.array_equal(V.astype(np.float32),np.asarray(reconstructed.vertices).astype(np.float32)),'ORIGINAL_VERTEX_MAPPING_MISMATCH'
 nuv,lo,hi,w=native_mapping(uv,nh,wh);mapped=np.clip(np.floor((np.arange(nh)+.5)*wh/nh).astype(int),0,wh-1);labn=labels[mapped,:];rgbn=rgb[mapped,:]
 raw=dict(V=V,F=F,uv=uv,native_uv=nuv,native_pixel_id=nuv[:,1]*nw+nuv[:,0],original_vertex_id=np.arange(len(V)),original_face_id=np.arange(len(F)),native_y_lower=lo,native_y_upper=hi,native_y_upper_weight=w)
 if out is not None:np.savez_compressed(out/'ORIGINAL_MAPPING.npz',**raw)
 cadpath=r.W/'runs/m2f5_unified/cad'/('R5.npz' if '_R5_' in c['case'] else 'R10.npz');cad=dict(np.load(cadpath))
 payload=dict(raw=raw,native=dict(depth_mm=z,K_index_native=Kn,reference_pose_mm=T),image_native=dict(labels=labn,RGB=rgbn),working=dict(depth_mm=zw,labels=labels,RGB=rgb,K=K),original_mesh_path=str(meshpath))
 return dict(R=R,tag=tag,meshpath=meshpath,nativepath=nativepath,z=z,L=L,i=i,row=row,rgb=rgb,labels=labels,zw=zw,T=T,K=K,Kn=Kn,valid=valid,uv=uv,m=m,V=V,F=F,raw=raw,cadpath=cadpath,cad=cad,payload=payload)

def run_one(c,out,figpath):
 import cv2,trimesh
 from scipy.ndimage import distance_transform_edt
 from scipy.spatial import cKDTree
 from . import route as r
 from ..mainline.native.cleaning import classify_native
 from ..mainline.native import _clean_kernels
 from .visualize import draw,plt
 info=mapped_input_for_source(c,out)
 R,tag,meshpath,nativepath,z,L,i,row,rgb,labels,zw,T,K,Kn,valid,uv,m,V,F,raw,cadpath,cad,payload=(info[k] for k in ['R','tag','meshpath','nativepath','z','L','i','row','rgb','labels','zw','T','K','Kn','valid','uv','m','V','F','raw','cadpath','cad','payload'])
 baseline=classify_native(out,cadpath,mapped_input=payload);f=dict(np.load(out/'FACE_EVIDENCE.npz'));op,su,unknown,views,perview=silhouette_evidence(V,F,R,i,cad);gap=(f['reason_bits']&(1<<13))!=0;deleted=candidate_faces(f,op,su,gap);hist=f['state']==2
 reason=np.zeros(len(F),np.uint16);reason[(f['perspective_stretch']>4)|(f['native_depth_jump_mm']>.5)]|=1;reason[op>=2]|=2;reason[gap]|=4;reason[su>=2]|=8;reason[f['CAD_occluded']]|=16;reason[deleted]|=32
 # All original vertices, including unreferenced ones, remain exactly recoverable.
 np.savez_compressed(out/'CANDIDATE_ORIGINAL_FACE_SUBSET.npz',V=V,F=F[~deleted],original_vertex_id=np.arange(len(V)),original_face_id=np.flatnonzero(~deleted),deleted_original_face_id=np.flatnonzero(deleted),reason_bits=reason,opposing_views=op,supporting_views=su,unknown_views=unknown,observer_evidence=perview,native_pixel_id=raw['native_pixel_id'],working_uv=uv)
 trimesh.Trimesh(V,F[~deleted],vertex_colors=np.asarray(m.visual.vertex_colors),process=False).export(out/'C1_original_faces_only.ply')
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 ns=dict(np=np,coo_matrix=coo_matrix,connected_components=connected_components);comp=types.FunctionType(_clean_kernels.face_components.__code__,ns,'face_components',_clean_kernels.face_components.__defaults__)(F[deleted]) if deleted.any() else np.array([],int)
 np.savez_compressed(out/'DELETED_REGIONS.npz',original_face_id=np.flatnonzero(deleted),region_id=comp)
 # Diagnostic continuous raw density is never an error label or a deletion input.
 tree=cKDTree(V);rho=(tree.query_ball_point(V,.4,return_length=True,workers=1)-1)/(np.pi*.4**2);low=rho<=np.quantile(rho,.2);grid=np.zeros((360,640),np.uint8);grid[uv[low,1],uv[low,0]]=1;nc,cc,st,_=cv2.connectedComponentsWithStats(grid);lowfrac=float(st[1:,4].max()/max(low.sum(),1)) if nc>1 else 0.
 tri=V[F];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 def counts(remove):
  before=np.unique(F);after=np.unique(F[~remove]);return dict(deleted_faces=int(remove.sum()),deleted_face_area_mm2=float(areas[remove].sum()),vertices_losing_all_incident_faces=int(len(np.setdiff1d(before,after))),vertices_touching_deleted_faces=int(len(np.unique(F[remove]))),coordinates_deleted=0,topology=components_and_boundary(V,F[~remove]))
 rec=dict(**{k:v for k,v in c.items() if k!='clean_not_run_yet'},clean_not_run_yet=False,historical=counts(hist),candidate=counts(deleted),raw=components_and_boundary(V,F),density_diagnostic=dict(q80_over_q10=float(np.quantile(rho,.8)/max(np.quantile(rho,.1),1e-9)),low_q20_vertices=int(low.sum()),largest_source_contiguous_low_fraction=lowfrac,not_error_truth=True),hist_state_counts=baseline['counts'],native_confirmed_gap_faces=int(gap.sum()),candidate_regions=int(comp.max()+1) if len(comp) else 0,qualified_observers=views,reason_bits={'1':'perspective stretch>4 or native local jump>.5 mm','2':'at least2 outside original silhouettes, margin>3px, all4 samples','4':'two-sided native grid gap','8':'2 mask supports: retained conflict','16':'CAD occluded: retained unknown','32':'derived face deleted'},original_face_subset=True,original_vertex_coordinates_bitwise=True,depth_MAE_used=False,working_shape=[360,640],native_shape=list(z.shape),mapping='OpenCV linear resize: native y=(working y+.5)*352/360-.5; original row-major valid vertices + original .75mm face test reproduced exactly; jump/gap uses nearest native pixel; bilinear lower/upper/weights saved',raw_recovery='original PLY+native referenced by SHA; ORIGINAL_MAPPING contains full original V/F, ids and pixel mapping',source_artifacts=dict(mesh=str(meshpath),mesh_sha256=r.sha(meshpath),depth=str(nativepath),depth_sha256=r.sha(nativepath),camera_sha256=r.sha(R/f"predictions/local005_camera_{r.read(R/'predictions/local005_primary.json')['primary_version']}.npz")),candidate_status='DIAGNOSTIC_NOT_ADOPTED',potential_structure_damage='cannot certify anatomy or other-object occlusion; any removed area may include real thin structure; inspect single-source figure')
 r.save(out/'RESULT.json',rec)
 bounds=np.r_[V,cad['V']];colors=np.asarray(m.visual.vertex_colors)[:,:3]/255.;facecolors=colors[F].mean(1);marked=facecolors*.25+.65;marked[deleted]=[.95,.05,.08]
 fig,axs=plt.subplots(2,3,figsize=(13,8))
 for rowaxes,(e,az) in zip(axs,[(20,60),(0,90)]):
  for ax,ff,col,title in zip(rowaxes,[F,F,F[~deleted]],[facecolors,marked,facecolors[~deleted]],['Raw 原始单源','删除位置：红色；灰色仍保留','Cleaned 原顶点 / 原面子集']):
   draw(ax,V,ff,col,cad,bounds,e,az);ax.set_title(title)
 fig.suptitle(c['case'].replace('GP_','')+f"\nTarget RAW {c['raw_target']} / Support {c['raw_support']}；单来源、同Raw完整毫米范围、同视角\n"+f"C1删除 {deleted.sum()}/{len(F)} 面，{areas[deleted].sum():.3f} mm²；原顶点坐标全保留。黑色Ring CAD；红色仅表示候选删除，不是真值",fontsize=10)
 note='依据：两侧原生网格断裂，或拉伸面被至少两合格视图轮廓反证；遮挡/双视图支持冲突保留。\n'+c['reason']+'。真实细柄、主体、遮挡仍须人工核查；未自动采用。'
 fig.text(.5,.025,note,ha='center',fontsize=9);fig.tight_layout(rect=(0,.07,1,.88));fig.savefig(figpath,dpi=120);plt.close(fig)
 assert r.sha(meshpath)==c['mesh_sha256'] and r.sha(nativepath)==c['native_sha256']
 return rec

def main():
 from . import route as r
 r.environment();T=r.WT/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001';B=r.W/'runs/v6_full_run_001/clean';B.mkdir(parents=True,exist_ok=True);(T/'figures').mkdir(exist_ok=True)
 cases=r.read(T/'config/CLEAN_CASES_FROZEN.json')['cases'];rules=r.read(T/'config/CLEAN_RULE_FROZEN.json');assert len(cases)==3 and rules['parameter_search_runs']==0
 assert rules['thresholds']==dict(perspective_stretch=4,native_depth_jump_mm=.5,silhouette_margin_work_px=3,opposing_views=2,support_veto_views=2),'FROZEN_CLEAN_RULE_DRIFT'
 assert rules['depth_MAE_used'] is False and rules['automatic_mainline_adoption'] is False
 rows=[]
 for j,c in enumerate(cases,1):
  fig=T/'figures'/f'clean_{j}.png';rows.append(run_one(c,B/f'case{j}',fig));rows[-1]['rule_sha256']=r.sha(T/'config/CLEAN_RULE_FROZEN.json');rows[-1]['execution_source_sha256']=r.sha(__file__);r.save(B/f'case{j}'/'RESULT.json',rows[-1]);print('CLEAN_DONE',j,rows[-1]['historical']['deleted_faces'],rows[-1]['candidate']['deleted_faces'],flush=True)
 r.save(T/'evidence/CLEAN_RESULTS.json',rows)
 r.save(B/'RESULTS.json',rows)
 html=['<meta charset="utf-8"><h1>三源 clean 小试（未自动采用）</h1><p>每图一个来源，Raw / 删除标记 / Cleaned，同范围同视角；候选仅改变原面集合。</p>']
 for j,c in enumerate(cases,1):
  p=B/f'clean_{j}.png'
  if not p.exists():p.symlink_to(T/'figures'/p.name)
  html.append(f'<h2>{c["case"]} / RAW {c["raw_target"]}</h2><img style="max-width:100%" src="clean_{j}.png">')
 (B/'index.html').write_text(''.join(html))
if __name__=='__main__':main()
