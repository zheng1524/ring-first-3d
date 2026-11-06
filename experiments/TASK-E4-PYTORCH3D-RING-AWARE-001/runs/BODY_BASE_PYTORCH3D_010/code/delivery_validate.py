"""Artifact/contract validation, separate from failed scientific geometry conditions."""
from common import *
import ast,re,platform,importlib.metadata,subprocess
from planes import normalize

def main():
 checks=[]
 def check(test,ok,**extra):checks.append(dict(test=test,passed=bool(ok),**extra))
 for fn in['PREOPT_FREEZE.json','PREDICTIONS_FROZEN.json','HISTORY_PROTECTION.json']:
  x=load(R/'assets_index'/fn);x=x['files']if isinstance(x,dict)else x;bad=[a['path']for a in x if not Path(a['path']).is_file()or sha(a['path'])!=a['sha256']];check(fn,not bad,N=len(x),mismatches=bad)
 cfg=load(R/'config/PROTOCOL.json');cases=load(R/'config/CASE_LOCK.json');check('locked_distinct_nine',len(cases)==9 and len({c['physical_specimen']for c in cases})==9);check('three_each_type',all(sum(c['morphology']==t for c in cases)==3 for t in['Ip','Is','IIa']))
 serial=load(R/'runtime/SERIAL_STATUS.json');check('all_18_conditions_attempted',len(serial)==18 and len({(x['case'],x['route'])for x in serial})==18 and all(x['returncode']==0 for x in serial));check('eight_300_and_ten_explicit_failures',sum(x['run']['status']=='COMPLETED'for x in serial)==8 and len(load(R/'metrics/FAILURE_DIAGNOSIS.json'))==10);check('no_preflight_optimizer_steps',load(R/'metrics/PREFLIGHT.json')['optimizer_steps']==0);check('unit_and_gradient_preflight',load(R/'metrics/PREFLIGHT.json')['passed']);projection=load(R/'metrics/PROJECTION_GATE.json');check('70_projection_rows_both_routes',projection['passed']and len(projection['rows'])==70)
 old=R.parent/'BODY_BASE_INIT_009';reg=load(R/'metrics/BASE_SIGN_REGRESSION.json');check('seven_BROAD_clips',sum(x['clipped']for x in reg)==7 and all(x['clipped']for x in reg if x['contact']=='BROAD'));check('G05_G09_mandatory_candidates',all(next(x for x in reg if x['case']==n)['clipped']for n in['G05','G09']))
 for c in cases:
  n=c['name'];b=np.load(old/'local_results'/n/'B_SELECTED.npz');P=np.load(R/'inputs'/n/'P_INITIAL.npz');S=np.load(R/'inputs'/n/'S_INITIAL.npz');bs=load(R/'inputs'/n/'BASE_SELECTION.json');idx=P['original_vertex_ID'];check(n+'_preserved_original_B_vertices',np.array_equal(P['V'][idx>=0],b['V'][idx[idx>=0]]))
  check(n+'_P_closed_manifold_initial',trimesh.Trimesh(P['V'],P['F_solid'],process=False).is_watertight);check(n+'_cap_excluded_from_render',len(P['F'])+int(P['inferred_base_faces'].sum())==len(P['F_solid']))
  if bs['truncate_allowed']:
   plane=normalize(bs['selected_plane']);h=b['V']@plane[:3]+plane[3];above=(h[b['F']]>=-1e-10).all(1);sourcefaces=P['original_face_ID'][:len(P['F'])];unchanged=True
   for fid in np.flatnonzero(above):
    candidates=np.flatnonzero(sourcefaces==fid);unchanged&=len(candidates)==1 and np.array_equal(idx[P['F'][candidates[0]]],b['F'][fid])
   check(n+'_all_above_triangles_bitwise_preserved',unchanged,N=int(above.sum()));height=P['V']@plane[:3]+plane[3];check(n+'_retained_halfspace_initial',height.min()>=-1e-8 and abs(height[P['boundary_vertex']]).max()<1e-8)
  else:check(n+'_small_contact_B_unchanged',np.array_equal(P['V'],b['V'])and np.array_equal(P['F'],b['F']))
  s=load(R/'inputs'/n/'SPHERE_INITIALIZATION.json');norm=load(R/'inputs'/n/'NORMALIZATION.json');radius=np.linalg.norm(S['V']-np.array(s['center_mm']),axis=1);check(n+'_official_sphere_uniform_metric_radius',len(S['V'])==642 and len(S['F'])==1280 and abs(radius-s['radius_mm']).max()<1e-5 and norm['scale_mm']==s['radius_mm']and not s['B_parameters_used'])
  for v in c['views']:
   source=old/'inputs'/n/(v['id']+'.npz');copy=R/'inputs'/n/(v['id']+'.npz');check(n+'_'+v['id']+'_RGB_Mask_K_pose_identical009',sha(source)==sha(copy));op=R/'depth_observations'/(v['id']+'.npz')
   if op.exists():
    o=np.load(op);oo=np.load(old/'depth_observations'/(v['id']+'.npz'));check(v['id']+'_native_ID_and_depth_unchanged',np.array_equal(o['pixel_id'],oo['pixel_id'])and np.array_equal(o['z'],oo['z']))
  for a in['P','S']:
   run=load(R/'metrics'/(n+'_'+a+'_RUN.json'));folder=R/'local_results'/n/a;check(n+'_'+a+'_initial_checkpoint', (folder/'STEP_0000.npz').exists())
   if run['status']=='COMPLETED':check(n+'_'+a+'_all_frozen_checkpoints',all((folder/('STEP_%04d.npz'%i)).exists()for i in cfg['checkpoints'])and(folder/'FINAL.npz').exists()and run['optimizer_steps']==300)
   else:check(n+'_'+a+'_no_false_final',not(folder/'FINAL.npz').exists()and(folder/'LAST_SAFE.npz').exists()and(folder/'UNSAFE_CANDIDATE.npz').exists())
  check(n+'_full_detailed_figure_exists',(R/'figures/full'/(n+'_Detailed.png')).exists())
 # Regression for discovered figure dispatch error; verifies actual saved stage resolution.
 from figures import getmodel
 z,_,_=getmodel('G01','P50');check('figure_P50_loads_actual_STEP50',int(z['step'])==50 and np.array_equal(z['V'],np.load(R/'local_results/G01/P/STEP_0050.npz')['V']));z,_,_=getmodel('G06','P50');check('missing_stage_not_substituted',z is None)
 for p in sorted((R/'code').glob('*.py')):ast.parse(p.read_text())
 check('all_source_ast_parse',True,N=len(list((R/'code').glob('*.py'))))
 core=['Fig1_Nine_Case_Overview.png','Fig2_G05_G09_Exact_Clipping.png','Fig3_Representative_Progression.png','Fig4_Observation_Update_Mechanism.png']
 for fn in core:
  with Image.open(R/'figures'/fn)as im:im.verify()
 check('all_core_figures_decode',True)
 missing=[]
 for p in R.glob('*.md'):
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if not target.startswith(('https:','http:','#'))and not(p.parent/target.split('#')[0]).exists():missing.append(str(p)+':'+target)
 check('local_document_links_exist',not missing,missing=missing);check('holdout_not_in_depth_losses',load(R/'metrics/HOLDOUT_LOSS_ISOLATION.json')['all_recorded_depth_loss_sources_are_FIT']);check('all_failed_replays_no_optimizer',all(x['optimizer_steps_in_replay']==0 and x['replay_position_agrees_under_1e_4mm']for x in load(R/'metrics/FAILED_PROPOSAL_GRADIENT_REPLAY.json')))
 qa=load(R/'metrics/BLENDER_GEOMETRY.json');check('independent_all_stage_Blender_evaluation',len(qa)==len(load(R/'metrics/ALL_STAGE_SUMMARY.json')));check('all_initial_meshes_no_detected_nonadjacent_self_intersection',all(x['nonadjacent_self_pair_N']==0 for x in qa if x['label']=='CHECKPOINT'and x['step']==0))
 index=[asset(p)for sub in['inputs','depth_observations','local_results','figures']for p in sorted((R/sub).rglob('*'))if p.is_file()];save('assets_index/LOCAL_RESULTS_INDEX.json',dict(root=str(R),files=index,large_files_local_only=True,failed_FINAL_not_substituted=True))
 packages={}
 for name in['numpy','scipy','torch','pytorch3d','open3d','trimesh','python-fcl','Pillow']:
  try:packages[name]=importlib.metadata.version(name)
  except importlib.metadata.PackageNotFoundError:packages[name]='runtime package metadata not registered'
 out=dict(engineering_delivery_passed=all(x['passed']for x in checks),does_not_mean_18_full_runs_succeeded=True,scientific_budget_18x300_achieved=False,checks=checks,Python=platform.python_version(),packages=packages,real_GT_accuracy='NOT_EVALUABLE',all_predicted_files_unchanged=True,history_unchanged=True);save('assets_index/DELIVERY_VALIDATION.json',out);print(json.dumps(dict(passed=out['engineering_delivery_passed'],N=len(checks),failed=[x for x in checks if not x['passed']]),ensure_ascii=False));assert out['engineering_delivery_passed']
if __name__=='__main__':main()
