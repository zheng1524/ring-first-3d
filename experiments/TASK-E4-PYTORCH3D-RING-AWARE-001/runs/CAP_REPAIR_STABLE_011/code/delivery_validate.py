from common import *
from planes import normalize
import ast,re,platform,importlib.metadata

def main():
 checks=[]
 def check(t,ok,**extra):checks.append(dict(test=t,passed=bool(ok),**extra))
 for fn in['HISTORY_PROTECTION.json','PREOPT_FREEZE.json','PREDICTIONS_FROZEN.json']:
  obj=load(R/'assets_index'/fn);items=obj['files']if isinstance(obj,dict)else obj;bad=[a['path']for a in items if not Path(a['path']).is_file()or sha(a['path'])!=a['sha256']];check(fn,not bad,N=len(items),mismatches=bad)
 check('V1_source_archive_mapping',all(x['matches']and Path(x['retained_path']).is_file()and sha(x['retained_path'])==x['original_sha256']for x in load(R/'assets_index/ENGINEERING_V1_SOURCE_MAPPING.json')))
 cases=load(R/'config/CASE_LOCK.json');check('nine_independent_physical_groups',len(cases)==9 and len({c['physical_specimen']for c in cases})==9);check('three_each_morphology',all(sum(c['morphology']==t for c in cases)==3 for t in['Ip','Is','IIa']));check('preflight_tests',load(R/'metrics/PREFLIGHT.json')['passed']);check('restart_contract',load(R/'metrics/RESTART_CONTRACT.json')['passed']);pg=load(R/'metrics/PROJECTION_GATE.json');check('35_real_projection_rows',pg['passed']and len(pg['rows'])==35)
 inh=load(R/'metrics/C_INHERITANCE.json');check('seven_caps_rule_derived',sum(c['needs_cap']for c in inh)==7);check('seven_exact_frozen_Cs',sum(c['action']=='EXACT_FROZEN_C_REUSED'for c in inh)==7);check('G05_G09_are_parametric_caps',all(next(c for c in inh if c['case']==n)['family']=='cap'for n in['G05','G09']));check('G05_uncertainty_preserved',next(c for c in inh if c['case']=='G05')['base_label']=='UNCERTAIN_BASE')
 runs=load(R/'metrics/NINE_CASE_RESULTS.json');check('nine_routes_full_proposal_budget',len(runs)==9 and all(x['status']=='COMPLETED'and x['outer_iterations']==300 for x in runs));check('accepted_guard_audit',all(x['all_logged_accepted_geometry_pass']and x['all_cap_halfspaces_pass']and x['all_rejections_rollback_exact']for x in runs));check('Adam_clock_replay',all(x['passed']for x in load(R/'metrics/ADAM_CLOCK_REPLAY.json')))
 replay=load(R/'metrics/FULL_OBJECTIVE_COMPONENTS.json');failed_replay=[dict(case=x['case'],difference=x['replay_difference'])for x in replay if x['label']=='FINAL'and not x['replay_within_training_tolerance']];check('strict_full_objective_cross_process_replay_1e_7',len(replay)==18 and not failed_replay,failed=failed_replay,threshold_unchanged=1e-7)
 old=R.parent/'BODY_BASE_INIT_009';p10=R.parent/'BODY_BASE_PYTORCH3D_010';summ=load(R/'metrics/ALL_STAGE_WITH_BLENDER.json')
 for c in cases:
  n=c['name'];root=R/'inputs'/n;init=np.load(root/'INITIAL.npz');end=np.load(R/'local_results'/n/'FINAL.npz');base=load(root/'BASE_SELECTION.json');p=normalize(load(old/'inputs'/n/'BASE.json')['plane']);check(n+'_directed009plane_retained',np.allclose(p,base['selected_plane'],rtol=0,atol=1e-14));check(n+'_topology_and_caps_unchanged',np.array_equal(init['F'],end['F'])and np.array_equal(init['F_solid'],end['F_solid'])and np.array_equal(init['inferred_base_faces'],end['inferred_base_faces'])and len(init['V'])==len(end['V']))
  if base['truncate_allowed']:
   h=end['V']@p[:3]+p[3];capnodes=np.unique(end['F_solid'][end['inferred_base_faces']]);check(n+'_strict_cap_halfspace_boundary',h.min()>-1e-7 and abs(h[capnodes]).max()<1e-7 and init['inferred_base_faces'].sum()==48)
  action=next(x for x in inh if x['case']==n)['action']
  if action=='EXACT_FROZEN_C_REUSED':check(n+'_sourceC_geometry_exact',np.array_equal(init['V'],np.load(old/'local_results'/n/'C_SELECTED.npz')['V']))
  h=load(R/'metrics'/(n+'_TRAINING.json'));run=next(x for x in runs if x['case']==n);check(n+'_update_counts_honest',sum(x['accepted']for x in h)==run['accepted_optimizer_steps']and run['Adam_committed_updates']+run['gradient_restart_updates']==run['accepted_optimizer_steps']);check(n+'_fixed_objective_tolerance',run['loss_nonincrease_with_1e_7_tolerance']);check(n+'_all_checkpoints',all((R/'local_results'/n/('STEP_%04d.npz'%i)).exists()for i in[0,25,50,60,100,150,180,200,250,300]));check(n+'_no_unauthorized_S_or_B_route',not(R/'local_results'/n/'S').exists()and not(R/'local_results'/n/'P').exists())
  for v in c['views']:
   src=old/'inputs'/n/(v['id']+'.npz');dst=root/(v['id']+'.npz');check(v['id']+'_raw_RGB_Mask_camera_exact',sha(src)==sha(dst));obs=R/'depth_observations'/(v['id']+'.npz')
   if obs.exists():check(v['id']+'_fixed_HERO_ID_weight_pair_exact010',sha(obs)==sha(p10/'depth_observations'/obs.name))
  check(n+'_complete_local_visualization',(R/'figures/full'/(n+'_Optimization_Detail.png')).exists())
 # Scientific conditions are reported independently: inherited collisions/stagnation never overwritten as PASS.
 check('independent_geometry_evaluation_complete',len(load(R/'metrics/BLENDER_GEOMETRY.json'))==len(load(R/'metrics/ALL_STAGE_SUMMARY.json')));check('no_real_GT_accuracy_claim',all(x['GT_height_volume_accuracy']=='NOT_EVALUABLE'for x in summ))
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
 check('all_code_ast_parse',True,N=len(list((R/'code').glob('*.py'))))
 core=['Fig1_Nine_B_to_C_Initialization.png','Fig2_G05_G09_Cap_Repair.png','Fig2b_G05_G09_Same_View_Cap_Repair.png','Fig3_Nine_Optimization_Before_After.png','Fig4_Low_to_High_Update_Process.png','Fig5_Geometry_Protection_and_Failures.png']
 for fn in core:
  with Image.open(R/'figures'/fn)as im:im.verify()
 check('five_core_plus_immutable_original_images_decode',True);check('separate_cap_process_figures',all((R/'figures/full'/(n+'_Cap_Repair.png')).exists()for n in['G05','G09']))
 bad=[]
 for p in R.glob('*.md'):
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if not target.startswith(('https:','http:','#'))and not(p.parent/target.split('#')[0]).exists():bad.append(str(p)+':'+target)
 check('all_local_report_links_exist',not bad,bad=bad)
 # Compact public parameter receipt; full candidate vectors remain indexed local artifacts.
 initial_models=[dict(case=c['name'],p=load(R/'inputs'/c['name']/'C_INITIAL_MODEL.json')['p'],meta=load(R/'inputs'/c['name']/'C_INITIAL_MODEL.json')['meta'],input=asset(R/'inputs'/c['name']/'INITIAL.npz'),provenance=load(R/'inputs'/c['name']/'C_INITIAL_MODEL.json')['inheritance'])for c in cases];save('metrics/INITIAL_C_PARAMETERS.json',initial_models)
 for c in cases:
  n=c['name'];alltr=load(R/'metrics'/(n+'_CANDIDATES.json'));accepted=[x for x in alltr if x['accepted']];save('metrics/'+n+'_ACCEPTED_PARAMETERS.json',accepted)
 index=[asset(p)for folder in['inputs','depth_observations','init_results','local_results','figures','metrics','engineering_validation_v1']for p in sorted((R/folder).rglob('*'))if p.is_file()];index.extend(asset(p)for p in sorted((R/'runtime').glob('*.log'))if p.is_file());index.append(asset(R/'runtime/SERIAL_STATUS.json'));save('assets_index/LOCAL_RESULTS_INDEX.json',dict(root=str(R),files=index,large_artifacts_local_only=True,all_failures_preserved=True));packages={}
 for name in['numpy','scipy','torch','pytorch3d','open3d','trimesh','python-fcl','Pillow']:
  try:packages[name]=importlib.metadata.version(name)
  except importlib.metadata.PackageNotFoundError:packages[name]='runtime metadata unregistered'
 result=dict(engineering_delivery_passed=all(x['passed']for x in checks),scientific_improvement_not_implied=True,checks=checks,Python=platform.python_version(),packages=packages,mainline_promoted=False,GT_accuracy='NOT_EVALUABLE');save('assets_index/DELIVERY_VALIDATION.json',result);print(json.dumps(dict(passed=result['engineering_delivery_passed'],tests=len(checks),failed=[x for x in checks if not x['passed']]),ensure_ascii=False));assert result['engineering_delivery_passed']
if __name__=='__main__':main()
