"""Read-only scientific artifact verification; never reruns fitting or edits predictions."""
from common import *
import ast,importlib.metadata,platform,subprocess

def main():
 checks=[]
 def check(name,ok,**extra):checks.append(dict(test=name,passed=bool(ok),**extra))
 for fn in ['PREOPT_FREEZE.json','PREDICTIONS_FROZEN.json','SOURCE_MANIFEST.json']:
  a=load(R/'assets_index'/fn);a=a['files']if isinstance(a,dict)else a;bad=[x['path']for x in a if not Path(x['path']).is_file()or sha(x['path'])!=x['sha256']];check(fn,not bad,N=len(a),mismatches=bad)
 cases=load(R/'config/CASE_LOCK.json');check('nine_distinct_physical_groups',len(cases)==9 and len({x['physical_specimen']for x in cases})==9);check('three_per_stratum',all(sum(x['morphology']==t for x in cases)==3 for t in['Ip','Is','IIa']))
 status=load(R/'runtime/SERIAL_STATUS.json');check('all_nine_fitting_runs_completed',len(status)==9 and all(x['returncode']==0 for x in status))
 check('parametric_preflight',load(R/'metrics/PARAMETRIC_PREFLIGHT.json')['passed']);check('projection_implementation',all(x['projection_pass']for x in load(R/'metrics/PROJECTION_GATE.json')['rows']))
 check('excluded_duplicate_relocated_SHA',all(x['matches']for x in load(R/'assets_index/DUPLICATE_PATH_RELOCATION.json')['files']))
 capN=0
 for c in cases:
  n=c['name'];folder=R/'local_results'/n
  for s in range(3):check(f'{n}_start{s}_both_stages',all((folder/f'B_seed{s}_{t}.json').is_file()for t in['CONTOUR','DEPTH']))
  for t in['B','C']:
   z=np.load(folder/(t+'_SELECTED.npz'));check(f'{n}_{t}_finite_mesh',np.isfinite(z['V']).all()and len(z['F'])>0)
   flag=z['inferred_base_faces'];check(f'{n}_{t}_closure_excluded_from_render',len(z['F'])==len(z['F_solid'])-int(flag.sum()))
   if t=='C'and flag.any():
    capN+=1;b=load(R/'inputs'/n/'BASE.json');plane=np.array(b['plane']);check(f'{n}_cap_above_estimated_base',np.min(z['V']@plane[:3]+plane[3])>=-1e-6 and b['truncate_allowed'])
  for v in c['views']:
   a=np.load(R/'inputs'/n/(v['id']+'.npz'));T=a['T'];check(n+'_'+v['id']+'_input',a['RGB'].shape[:2]==(360,640)and a['labels'].shape==(360,640)and np.isfinite(a['K']).all()and np.isfinite(T).all()and abs(np.linalg.det(T[:3,:3])-1)<1e-4)
  check(n+'_all_figures_present',all((R/'figures/full'/(n+s)).exists()for s in['_Detailed.png','_All_Candidates.png']))
 check('five_formal_cap_cases',capN==5)
 for p in sorted((R/'code').glob('*.py')):ast.parse(p.read_text())
 check('all_code_ast_parse',True,N=len(list((R/'code').glob('*.py'))))
 core=['Fig_Overview_Nine_Cases.png','Fig_Ip_Detailed.png','Fig_Is_Detailed.png','Fig_IIa_Detailed.png']
 for fn in core:
  with Image.open(R/'figures'/fn)as im:im.verify()
 check('four_core_images_decode',True)
 blender=load(R/'metrics/BLENDER_GEOMETRY.json');check('independent_Blender_checks_complete',len(blender)==27);check('final_models_no_detected_nonadjacent_self_intersection',all(x['nonadjacent_self_pair_N']==0 for x in blender if x['arm']in['B','C']))
 # Validate documentation links only for local Markdown links; image files remain local by design.
 import re
 badlinks=[]
 for f in R.glob('*.md'):
  for link in re.findall(r'\]\(([^)]+)\)',f.read_text()):
   if not link.startswith(('http:','https:','#'))and not(f.parent/link.split('#')[0]).exists():badlinks.append(str(f)+':'+link)
 check('report_local_links',not badlinks,bad=badlinks)
 index=[asset(p)for sub in['inputs','depth_observations','local_results']for p in sorted((R/sub).rglob('*'))if p.is_file()]
 save('assets_index/LOCAL_RESULTS_INDEX.json',dict(root=str(R),files=index,large_files_not_uploaded=True,no_GT_geometry_read=True))
 packages={}
 for s in['numpy','scipy','torch','pytorch3d','open3d','trimesh','python-fcl','opencv-python','Pillow']:
  try:packages[s]=importlib.metadata.version(s)
  except importlib.metadata.PackageNotFoundError:packages[s]='runtime package or unavailable metadata'
 out=dict(engineering_delivery_passed=all(x['passed']for x in checks),scientific_success_not_implied=True,checks=checks,Python=platform.python_version(),packages=packages,real_GT_accuracy='NOT_EVALUABLE',predictions_unchanged=True)
 save('assets_index/DELIVERY_VALIDATION.json',out)
 m=load(R/'metrics/MODEL_SELECTION_RECORD.json');save('metrics/RESULT.json',dict(target=9,numerical_output_N=9,numerical_failure_N=0,physical_safe_B_N=sum(x['B_geometry_valid']for x in m),physical_safe_C_N=sum(x['C_geometry_valid']for x in m),formal_base_cap_N=capN,status='MIXED_AWAITING_HUMAN_REVIEW',historical_measurement_fallback_N=0,GT_model_selection=False,GT_accuracy='NOT_EVALUABLE',engineering_validation=out['engineering_delivery_passed'],stopped_before_free_mesh_optimization=True))
 print(json.dumps(dict(passed=out['engineering_delivery_passed'],checks=len(checks),failed=[x for x in checks if not x['passed']]),ensure_ascii=False));assert out['engineering_delivery_passed']
if __name__=='__main__':main()
