"""Read-only attribution of the R2 Ip8.8/004 regression on frozen cameras.

Replays the original validation kernel with explicit observation masks. Never
optimizes cameras, writes a scientific gate/plan, or invokes HERO.
"""
import ast,hashlib,json
from pathlib import Path
import numpy as np
from ring_first_3d.v6_raw import route as r
from ring_first_3d.v6_raw.frontend_kernels import install
from ring_first_3d.v6_raw.frontend_policy import finite_le,view_tag
from ring_first_3d.v6_raw.policy import admit_camera
W=r.W;O=W/'runs/v6_frontend_photo_pilot_001';T=Path(__file__).resolve().parents[1]/'experiments/TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001';CASE='GP_Ip_8.8mm_closed_R5_single_refY_004'
class Observations(ast.NodeTransformer):
 def visit_Assign(self,node):
  self.generic_visit(node)
  if any(isinstance(t,ast.Name) and t.id=='testids' for t in node.targets):node.value=ast.parse("np.flatnonzero(tr['held'] & (np.arange(len(tr['held'])) < _DIAG_N_TRACKS))",mode='eval').body
  if any(isinstance(t,ast.Name) and t.id=='other' for t in node.targets) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='np.flatnonzero':node.value.args[0]=ast.BinOp(left=node.value.args[0],op=ast.BitAnd(),right=ast.Name(id='_DIAG_VIEW_MASK',ctx=ast.Load()))
  if any(ast.unparse(t)=='(jj, kk)' for t in node.targets):return [node]+ast.parse('_DIAG_PAIRS.append((int(v),int(i),int(t),int(jj),int(kk)))').body
  return node

def replay(var,original_tracks_only,video_views_only):
 R=O/var/'HIST'/CASE;meta=r.read(R/'inputs/INPUT_IDENTITY.json');L=meta['frames'];BR=Path(meta['preprocessing_reuse']['source']).parents[1];orig=np.load(BR/'observations/tracks005.npz');tracks=np.load(R/'observations/tracks005.npz');m=install(r.legacy());mods=r.bind(m,R,meta)
 import validate_select
 validate_select.R=R;validate_select.V5=R/'v5raw';validate_select.contours=mods['v6'].contours
 ref=r.read(R/'inputs/REFERENCE_RECEIPT.json');tree,receipt=m.adapt_reference_lookups(r.V6/'scripts/validate_select.py',ref['reference_index'],ref['heldout_index'],{'reference':1,'heldout':1});tree=Observations().visit(tree);ast.fix_missing_locations(tree);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');captured={};pairs=[]
 ns=dict(validate_select.__dict__);ns.update(save=lambda path,data:captured.update({path:data}),freeze=lambda *args:None,_M2F9_REFERENCE_INDEX=ref['reference_index'],_M2F9_HELDOUT_INDEX=ref['heldout_index'],_FRONTEND_VIEW_TAG=view_tag,_FRONTEND_FINITE_LE=finite_le,_DIAG_N_TRACKS=len(orig['held']) if original_tracks_only else len(tracks['held']),_DIAG_VIEW_MASK=np.asarray([a['media_type']=='video' or not video_views_only for a in L]),_DIAG_PAIRS=pairs)
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(r.V6/'scripts/validate_select.py')+'::readonly_diagnostic','exec'),ns);ns['main']();val=captured['metrics/local_validation.json'];rows=[]
 for v in val['versions']:
  frames=[(i,a) for i,a in enumerate(v['per_frame']) if L[i]['media_type']=='video'];gates=[admit_camera(a) for i,a in frames];chosen=[p for p in pairs if p[0]==v['version'] and L[p[1]]['media_type']=='video'];photo_pairs=sum(L[p[3]]['media_type']=='photo' or L[p[4]]['media_type']=='photo' for p in chosen)
  rows.append(dict(variant=var,original_tracks_only=original_tracks_only,video_views_only=video_views_only,version=v['version'],video_q0=sum(a[0] for a in gates),video_q1=sum(a[1] for a in gates),video_RGB_MAE_median=float(np.median([a['held_reprojection']['MAE'] for i,a in frames if a['held_reprojection']['MAE'] is not None])),held_video_evaluations=len(chosen),triangulations_using_photo=photo_pairs,per_frame=[dict(index=i,raw=L[i]['raw_frame'],q1=gates[k][1],metrics=a) for k,(i,a) in enumerate(frames)]))
 if var=='R1':
  official=r.read(R/'metrics/local_validation.json')
  for v,a in zip(val['versions'],official['versions']):
   for x,y in zip(v['per_frame'],a['per_frame']):assert np.isclose(x['held_reprojection']['MAE'],y['held_reprojection']['MAE'],atol=1e-8)
 return dict(rows=rows,source_sha256=r.sha(r.V6/'scripts/validate_select.py'),adapted_ast_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest(),frozen_camera_hashes={str(p):r.sha(p) for p in R.glob('predictions/local005_camera_*.npz')},official_validation_sha256=r.sha(R/'metrics/local_validation.json'))

def main():
 r.B=O/'postprocess';r.environment();results=[replay('R1',True,True),replay('R2',False,False),replay('R2',True,False),replay('R2',True,True)];out=dict(case=CASE,diagnostic_only=True,frozen_cameras_unchanged=True,new_BA_runs=0,new_HERO_runs=0,official_gates_and_plans_unchanged=True,results=results);r.save(T/'evidence/R2_ZERO_ATTRIBUTION.json',out)
 for q in results:
  for row in q['rows']:print({k:v for k,v in row.items() if k!='per_frame'},flush=True)
if __name__=='__main__':main()
