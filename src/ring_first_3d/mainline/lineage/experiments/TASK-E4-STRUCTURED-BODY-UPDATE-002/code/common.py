"""Read-only adapters to the exact previous initializer and historical geometry."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
from pathlib import Path
import importlib.util,json
import numpy as np
OLD=Path(str(_mainline_path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-MULTIVIEW-STRUCTURAL-UPDATE-001')))
spec=importlib.util.spec_from_file_location('frozen_structural001_body',OLD/'code/body_update.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
INITIALIZE=legacy.initialize
SOURCES=Path(str(_mainline_path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/inputs/SOURCES.json')))
def load_case(case,role=None):
    row=next(r for r in json.loads(SOURCES.read_text())['cases']if r['case']==case);ring=dict(np.load(row['static']['RING.npz']['path']));initial=INITIALIZE(row['resolved013_initial']['path'],ring,ring);views=[]
    for s in ['FIT','HOLDOUT']:
        if role and s!=role:continue
        for v in row[s]:
            a=np.load(v['cache']['path']);m=v['meta'];views.append(dict(id=m['id'],video=m['video'],role=s,direction_block=m.get('direction_block',0),K=a['K'],C=a['T'],labels=a['labels'],RGB=a['RGB']))
    base=json.loads(Path(row['static']['BASE_SELECTION.json']['path']).read_text());chart=json.loads(Path(row['static']['CHART.json']['path']).read_text())
    return initial,views,ring,base,chart,row

def dump(p,x):
    from ring_first_3d.evaluation.validation import clean
    Path(p).write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def geometry(candidate,current,initial,base,chart,ns):
    import trimesh
    V=candidate['V'];F=candidate['F_solid'];tri=V[F];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);a=np.linalg.norm(n,axis=1);m=trimesh.Trimesh(V,F,process=False);why=[]
    if a.min()<1e-8:why.append('DEGENERATE_FACE')
    if not m.is_watertight:why.append('OPEN_MESH')
    if not m.is_winding_consistent:why.append('WINDING')
    if len(m.split(only_watertight=False))!=1:why.append('DISCONNECTED')
    si=ns['self_intersections'](V,F)['intersections']
    if si:why.append('SELF_INTERSECTION')
    lookup={tuple(f):i for i,f in enumerate(initial['F_solid'])};minimum=1.
    for j,f in enumerate(F):
        i=lookup.get(tuple(f))
        if i is None:continue
        q=initial['V'][f];n0=np.cross(q[1]-q[0],q[2]-q[0]);ratio=a[j]/max(1e-20,np.linalg.norm(n0));minimum=min(minimum,ratio)
        if n[j]@n0<=0:why.append('FACE_FLIP');break
        if ratio<.1:why.append('AREA_COLLAPSE');break
    if initial['inferred_base_faces'].any():
        plane=np.asarray(base['selected_plane']);hh=V@plane[:3]+plane[3]
        if hh.min()<-1e-7:why.append('BASE_HALFSPACE')
        rim=initial['boundary_vertex'];p0=initial['V'][rim]@plane[:3]+plane[3]
        if abs(hh[:len(rim)][rim]-p0).max()>1e-7:why.append('BASE_BOUNDARY_MOVED')
    motion=np.linalg.norm(V[:len(initial['V'])]-initial['V'],axis=1)
    if motion.max()>chart['D_mm']:why.append('TOTAL_TRUST')
    return list(set(why)),dict(self_intersections=si,watertight=m.is_watertight,winding=m.is_winding_consistent,min_double_area_mm2=float(a.min()),min_original_area_ratio=minimum,volume_mm3=float(m.volume),referenced_vertices=len(np.unique(F)),all_vertices=len(V),original_displacement_MAE_mm=float(motion.mean()),original_displacement_max_mm=float(motion.max()))
