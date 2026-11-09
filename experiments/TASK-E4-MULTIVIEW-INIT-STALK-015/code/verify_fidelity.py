"""Algorithm/source/identity tests; project GT never read."""
from common import *
import ast

def functions(p):return {q.name:ast.dump(q,include_attributes=False)for q in ast.parse(p.read_text()).body if isinstance(q,ast.FunctionDef)}
def main():
 old=REPO/'experiments/TASK-E4-PYTORCH3D-014/code';pairs=[]
 for f in ['safe_geometry.py','multiview.py','contour_objective.py']:
  pairs.append(dict(file=f,exact_upstream_bytes=sha(R/'code'/f)==sha(old/f),source=asset(old/f)))
 a=functions(old/'best_rigid014.py');b=functions(R/'code/best_rigid015.py');rigid_checks={k:a[k]==b[k]for k in ['frames','pca','apply','rigid','interpolate','align','feret']};freeze=load(R/'provenance/PHASE_A_CODE_AND_PROTOCOL_FROZEN.json');print('FREEZE_KEYS',list(freeze),flush=True);selection=load(R/'config/VIEW_SELECTION.json');views=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];s=selection[n];meta=load(R/'inputs'/n/'CASE.json');vv={v['id']:v for v in meta['views']};fit=s['FIT'];held=s['HOLDOUT'];views.append(dict(case=n,Nfit=len(fit),Nheld=len(held),no_overlap=not bool(set(fit)&set(held)),same_video=len({vv[x]['video']for x in fit+held})==1,selected_original_FIT_present=set(s['original013FIT']).issubset(fit)))
 ok=all(p['exact_upstream_bytes']for p in pairs)and all(rigid_checks.values())and all(v['no_overlap']and v['same_video']and v['selected_original_FIT_present']for v in views);save('metrics/ALGORITHM_FIDELITY_TESTS.json',dict(upstream=pairs,rigid_function_AST_identical=rigid_checks,views=views,all_checks_pass=ok,GT_read=False));assert ok;print('FIDELITY_PASS',flush=True)
if __name__=='__main__':main()
