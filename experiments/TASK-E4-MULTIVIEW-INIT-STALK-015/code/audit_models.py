"""Independent geometry, stability and input-evidence metrics. No GT access."""
from common import *
from safe_geometry import dense_face_distance,self_intersections
from evaluate import area_samples,distance
import open3d as o3d
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist

def audit(n,path,baseline=None):
    a=np.load(path);V,F,Fs=a['V'],a['F'],a['F_solid'];r=np.load(R/'inputs'/n/'RING.npz');rs=scene(r['V'],r['F']);sd=dense_face_distance(rs,V,Fs,r['V'],64,r['F']);pen=max(0.,-float(sd.min()));tm=trimesh.Trimesh(V,Fs,process=False);cm=trimesh.collision.CollisionManager();cm.add_object('CAD',trimesh.Trimesh(r['V'],r['F'],process=False));si=self_intersections(V,Fs);pl=np.array(load(R/'inputs'/n/'BASE_SELECTION.json')['selected_plane']);h=V@pl[:3]+pl[3];flag=a['inferred_base_faces'];xy=V[:,:2];hull=ConvexHull(xy);dxy=float(pdist(xy[hull.vertices]).max());base=0.
    if baseline is not None:base=baseline['dense_Ring_penetration_mm']
    rec=dict(case=n,path=str(path),vertices=len(V),observed_eligible_faces=len(F),solid_faces=len(Fs),inferred_cap_faces=int(flag.sum()),dense_Ring_penetration_mm=pen,added_Ring_penetration_vs_common013_mm=max(0.,pen-base),dense_nonworsening_vs_common013=pen<=base+1e-5,Ring_FCL=bool(cm.in_collision_single(tm)),self_intersections_N=si['intersections'],self_pairs=si['pairs'],components=len(tm.split(only_watertight=False)),watertight=bool(tm.is_watertight),winding_consistent=bool(tm.is_winding_consistent),degenerate_faces_N=int((tm.area_faces<1e-12).sum()),base_below_vertices_N=int((h<-1e-7).sum())if flag.any()else None,model_height_above_estimated_base_mm=float(h.max())if flag.any()else None,model_RingXY_Feret_mm=dxy,roughness_dihedral_deg=stats(np.degrees(tm.face_adjacency_angles)),no_GT=True,comparison_baseline_path=baseline.get('path')if baseline is not None else None,comparison_baseline_penetration_mm=base,baseline_flag_name_note='dense_nonworsening_vs_common013 uses supplied baseline; Phase A: original013 INITIAL; Phase B: common Phase A FINAL')
    return rec

def compare_surfaces(a,b):
    p=np.load(a);q=np.load(b);P=area_samples(p['V'],p['F'],4096);Q=area_samples(q['V'],q['F'],4096);d=np.r_[distance(scene(q['V'],q['F']),P),distance(scene(p['V'],p['F']),Q)];return dict(surface_distance_mm=stats(d),center_shift_mm=float(np.linalg.norm(p['V'].mean(0)-q['V'].mean(0))),world_extents_change_mm=np.ptp(q['V'],axis=0)-np.ptp(p['V'],axis=0),definition='4096 deterministic area samples per direction; no alignment, no GT')

def fixed_depth(score,role='FIT'):
    a=[q for q in score['per_view']if q['role']==role and q.get('fixed_depth_N',0)>0];N=sum(q['fixed_depth_N']for q in a);H=sum(q['depth_hit_N']for q in a);cost=sum(q['fixed_depth_cost']*q['fixed_depth_N']for q in a);E=sum(q['depth_MAE_mm']*q['depth_hit_N']for q in a if q['depth_MAE_mm']is not None)
    return dict(fixed_N=N,hit_N=H,miss_N=N-H,hit_rate=H/N if N else None,fixed_cost=cost/N if N else None,active_MAE_mm=E/H if H else None)
