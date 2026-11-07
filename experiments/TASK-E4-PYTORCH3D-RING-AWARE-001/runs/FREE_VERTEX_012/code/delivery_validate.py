from common import *
import ast,re,torch

def main():
 checks=[]
 def check(name,passed,**extra):checks.append(dict(test=name,passed=bool(passed),**extra))
 for fn in ['PREOPT_FREEZE.json','PREDICTIONS_FROZEN_BEFORE_GT.json','SCALE_LOCK_BEFORE_GT.json','EVALUATION_CODE_BEFORE_GT.json','HISTORY_011_PROTECTION.json']:
  a=load(R/'assets_index'/fn);items=a if isinstance(a,list)else a['files'];bad=[x['path']for x in items if not Path(x['path']).exists()or sha(x['path'])!=x['sha256']];check(fn,not bad,N=len(items),mismatches=bad)
 cases=load(R/'config/CASE_LOCK.json');runs=load(R/'metrics/NINE_CASE_RESULTS.json');cfg=load(R/'config/PROTOCOL.json');check('nine_independent_physical_groups',len(cases)==9 and len({c['physical_specimen']for c in cases})==9);check('three_each_type',all(sum(c['morphology']==t for c in cases)==3 for t in ['Ip','Is','IIa']));check('preflight_full_vertex_gradients',load(R/'metrics/PREFLIGHT.json')['passed']);check('nine_formal_outputs',len(runs)==9 and all(x['numerical_output']for x in runs));check('no_new_network_or_spectral_parameterization','Phi'not in(R/'code/free_model.py').read_text()and'FreeVertices'in(R/'code/train.py').read_text())
 old=R.parent/'CAP_REPAIR_STABLE_011';bg=load(R/'metrics/BLENDER_GEOMETRY_CHECKS.json')
 for c in cases:
  n=c['name'];r=next(x for x in runs if x['case']==n);i=np.load(R/'inputs'/n/'INITIAL.npz');f=np.load(R/'local_results'/n/'FINAL.npz');h=load(R/'metrics'/(n+'_TRAINING.json'));check(n+'_exact011FINAL_start',sha(R/'inputs'/n/'INITIAL.npz')==sha(old/'local_results'/n/'FINAL.npz'));check(n+'_no_face_deletion_topology_preserved',np.array_equal(i['F'],f['F'])and np.array_equal(i['F_solid'],f['F_solid'])and np.array_equal(i['inferred_base_faces'],f['inferred_base_faces'])and len(i['V'])==len(f['V']));check(n+'_budget_and_actual_acceptances',r['attempts']<=800 and r['accepted']<=300 and sum(x['accepted']for x in h)==r['accepted']);check(n+'_bounded_actual_steps',max(x['actual_step_mm']for x in h)<=load(R/'inputs'/n/'CHART.json')['tau_mm']+1e-8);check(n+'_finite_geometry_and_gradients',np.isfinite(f['V']).all()and all(np.isfinite(x['gradient_norm'])for x in h));check(n+'_accepted_snapshots_honest',all((R/'local_results'/n/('ACCEPTED_%04d.npz'%k)).exists()for k in cfg['accepted_checkpoints']if k<=r['accepted']));check(n+'_independent_self_check',next(x for x in bg if x['case']==n and x['label']=='FINAL012')['self_intersections_N']==0)
  if i['inferred_base_faces'].any():
   p=np.array(load(R/'inputs'/n/'BASE_SELECTION.json')['selected_plane']);he=f['V']@p[:3]+p[3];check(n+'_cap_halfspace_and_boundary',he.min()>=-1e-7 and abs(he[i['boundary_vertex']]).max()<1e-7)
  state=torch.load(R/'local_results'/n/'FINAL.pt',map_location='cpu',weights_only=False);check(n+'_complete_recovery_state',all(k in state for k in ['optimizer','parameters','torch_state','cuda_state','numpy_state','config','attempt','accepted'])and state['accepted']==r['accepted']and np.array_equal(state['parameters'].numpy(),f['parameters']))
  for v in c['views']:
   check(v['id']+'_frozen_native_image_camera',sha(R/'inputs'/n/(v['id']+'.npz'))==sha(old/'inputs'/n/(v['id']+'.npz')))
   p=R/'depth_observations'/(v['id']+'.npz')
   if p.exists():check(v['id']+'_original_HERO_ID_weights_pairs',sha(p)==sha(old/'depth_observations'/p.name))
 for s in load(R/'metrics/RING_SCALE_VALIDATION.json'):check(s['case']+'_metric_scale_no_GT',s['applied_scale']==1 and abs(s['recovery_ratio']-1)<1e-4 and not s['GT_used'])
 alignment=load(R/'metrics/BLENDER_RIGID_ALIGNMENT.json');check('27_stage_SE3_only_alignments',len(alignment)==27 and all(x['scale']==1 and abs(np.linalg.det(np.array(x['R']))-1)<1e-8 and np.allclose(np.array(x['R']).T@np.array(x['R']),np.eye(3),atol=1e-8)for x in alignment))
 sources=load(R/'evaluation_only/GT_SOURCE_LOCK.json')
 for s in sources:check(s['case']+'_original_GT_source_unchanged',sha(s['path'])==s['sha256']and s['unit_to_mm']==1000.)
 check('GT_access_after_scale_lock',(R/'evaluation_only/GT_SOURCE_INSPECTION.json').stat().st_mtime>(R/'assets_index/SCALE_LOCK_BEFORE_GT.json').stat().st_mtime)
 ms=load(R/'metrics/MEASUREMENT_SUMMARY.json');check('measurement_denominator_and_no_fallback',all(x['target_N']==9 and x['matched_Dxy_evaluation_N']==9 and x['historical_measurement_fallback_N']==0 for x in ms));check('paired_common_nine',load(R/'metrics/PAIRED_011_012.json')['common_N']==9)
 for p in(R/'code').glob('*.py'):ast.parse(p.read_text())
 check('all_code_parses',True);bad=[]
 for p in R.glob('*.md'):
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if not target.startswith(('https:','http:','#'))and not(p.parent/target.split('#')[0]).exists():bad.append(str(p)+':'+target)
 check('local_report_links_exist',not bad,bad=bad)
 figs=['Fig1_Nine_Free_Vertex_Overview.png','Fig2_Three_Ip_Stalk_Review.png','Fig3_Free_Vertex_Update_Process.png','Fig4_Ring_Scale_and_Blender_Alignment.png','Fig5_Quantitative_Results.png']
 for name in figs:
  with Image.open(R/'figures'/name)as im:im.verify()
 check('five_core_figures_decode',True);check('nine_detailed_visualizations',all((R/'figures/full'/(c['name']+'_Three_Stage_Detail.png')).exists()for c in cases));check('historical_reference_only_postfreeze',load(R/'assets_index/HISTORICAL_STATIC_REFERENCE.json')['not_optimization_input'])
 check('nine_downloadable_model_packages',all((R/'review_models'/c['name']/'FINAL012_with_Ring_m.glb').exists()and load(R/'review_models'/c['name']/'MODEL_SEMANTICS.json')['GLB_bounds_verified']for c in cases))
 index=[asset(p)for d in ['inputs','depth_observations','local_results','evaluation_only','figures','metrics','review_models']for p in sorted((R/d).rglob('*'))if p.is_file()]+[asset(p)for p in sorted((R/'runtime').glob('*.log'))]+[asset(R/'runtime/SERIAL_STATUS.json')];save('assets_index/LOCAL_RESULTS_INDEX.json',dict(root=str(R),files=index,checkpoints_local_only=True,raw_models_and_failures_preserved=True))
 result=dict(artifact_integrity_passed=all(x['passed']for x in checks),scientific_success_not_implied=True,checks=checks,all_nine_predictions_available=True,stalk_complete_recovery_demonstrated=False,strict_physical_quality_all_passed=False,limits=['residualCADcontacts','G01sharp_local_dihedral','GT_invalid_solids','inferred_bases','G03_negligible_update','G09_height_and_IoU_limit','inherited011strict_silhouette_replay_gap'],mainline_promoted=False);save('assets_index/DELIVERY_VALIDATION.json',result);print(json.dumps(dict(passed=result['artifact_integrity_passed'],N=len(checks),failed=[x for x in checks if not x['passed']]),ensure_ascii=False));assert result['artifact_integrity_passed']

if __name__=='__main__':main()
