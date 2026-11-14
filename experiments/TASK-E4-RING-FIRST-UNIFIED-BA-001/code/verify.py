"""Meaningful delivery/scientific contract checks, preserving failed research gate."""
from hero_evaluate import *
import subprocess

def main():
 checks=[]
 def check(name,value,detail=None):checks.append(dict(name=name,PASS=bool(value),detail=detail))
 for rel in ['provenance/INPUTS_FROZEN.json','provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json','provenance/VISIBLE_ARCS_FROZEN_BEFORE_BA.json']:
  bad=[a['path']for a in load(N/rel)['files']if not Path(a['path']).exists()or sha(a['path'])!=a['sha256']];check(rel+'sha',not bad,bad)
 for a in load(N/'provenance/ORIGINAL_SOURCE_READ_RECEIPT.json'):check('originalRFandhistoricalsourceunchanged '+a['path'],sha(a['path'])==a['sha256'])
 views=load(N/'config/VIEWS.json');check('98canonical81FIT17HOLDOUT',len(views)==98 and sum(v['role']=='FIT'for v in views)==81 and sum(v['role']=='HOLDOUT'for v in views)==17);check('noillegalcrossvideogroups',all(v['video']=='004'or v['group']=='G01'for v in views));tracks=load(N/'config/TRACKS.json');check('1728actualRGBtracks18shared',len(tracks)==1728 and sum(t['cross_video']for t in tracks)==18);check('everyRGBtrackpixelidentityverified',load(N/'metrics/ALL_NATIVE_RGB_IDENTITIES_VERIFIED.json')['exact_feature_pixel_observations']==11315)
 stage=load(N/'STAGE_A_GATE.json');check('correctnessStageApassed',stage['PASS']);js=load(N/'metrics/JACOBIAN_BLOCK_TESTS.json');check('72componentJacobianchecks',len(js)==72 and all(j['PASS']for j in js))
 res=getresults();fitvars=0
 for g in GROUPS:
  checkfreeze('provenance/'+g+'_MAIN_POSES_FROZEN.json');r=res[g,'B3'];fitvars+=load(N/'metrics'/(g+'_JOINT_INFORMATION.json'))['actual_variable_camera_N'];check(g+'realjointXYZnotfixed',len(r['X'])>20 and np.linalg.norm(np.array(list(r['X'].values()))-np.array(list(Joint(g,'B3').X0.values())))>1e-8)
  q=load(N/'metrics'/(g+'_JOINT_INFORMATION.json'));check(g+'completejointFD',all(x['PASS']for x in q['complete_joint_FD']));check(g+'reporteddataonlymarginalinformation',q['priors_excluded']and q['landmarks_eliminated']and q['marginal_camera_information_rank']<=q['marginal_camera_information_dimension']);check(g+'oneconnectedSIFTgraph',len(q['graph_components'])==1)
  tr=load(N/'optimization'/g/'B3/TRACE.json');check(g+'allrealCeresLM_Schur',all('DENSE_SCHUR'in x['Ceres']['linear_solver_type_used']and'LEVENBERG_MARQUARDT'in x['Ceres']['trust_region_strategy_type']and x['Ceres']['num_effective_parameters_reduced']>6 and x['Ceres']['usable']for x in tr));check(g+'reassociatedfullobjective下降',r['loss']<=r['initial_loss']+1e-10 and all(x['after']<=x['before']+1e-10 for x in tr));check(g+'physicaldomainaccepted',r['physical'][0])
  # Metadata from the exact formal run records source SHA at optimization time.
  check(g+'actualfitimplementationunchanged',sha(r['source']['path'])==r['source']['sha256'])
  for v in [v for v in views if v['group']==g]:
   C=np.array(r['poses'][v['id']]);check(g+v['id']+'SO3metric',np.max(abs(C[:3,:3].T@C[:3,:3]-np.eye(3)))<1e-10 and abs(np.linalg.det(C[:3,:3])-1)<1e-10);B=np.array(v['T']);check(g+v['id']+'physicalbound',np.linalg.norm(C[:3,3]-B[:3,3])<=1.2+1e-9)
   if v['role']=='HOLDOUT':check(g+v['id']+'protectedHOLDOUT',np.max(abs(C-np.array(r['H_absolute'][v['video']])@np.array(v['RF_native'])))<1e-10 and np.max(abs(np.asarray(r['local'][v['id']])))==0)
  check(g+'B4explicitNOT_RUN_noP0fallback',res[g,'B4']['poses']is None and res[g,'B4']['status'].startswith('NOT_RUN'))
  if g!='G01':check(g+'B2NAP_noinventedcrossvideo',res[g,'B2']['poses']is None)
 check('76active5DcameraBlocks',fitvars==76);ms=load(N/'metrics/PREREGISTERED_MULTISTART_COMPARISON.json');check('sensitivitynotreplaceprimary',ms['primary_unchanged']and ms['not_selected_by_HOLDOUT_HERO'])
 per=load(N/'metrics/PER_VIEW_CAMERA_GEOMETRY.json');check('all490outcomesinclNAandNOTRUN',len(per)==490);check('362numericmetricrows_not362newsolves',sum(r.get('Ring_IoU')is not None for r in per)==362)
 sc=load(N/'metrics/FOUR_GROUP_POSE_SCORECARD.json');b0=next(r for r in sc if r['group']=='G01'and r['method']=='B0'and r['role']=='FIT');b2=next(r for r in sc if r['group']=='G01'and r['method']=='B2'and r['role']=='FIT');check('sharedRigid005nativeMapRGBreprojectioninvariant',abs(b0['descriptor_HELD_reprojection_px_MAE_macro']-b2['descriptor_HELD_reprojection_px_MAE_macro'])<1e-10)
 for r in per:
  if r.get('Ring_IoU')is not None:check(r['id']+r['method']+'exactIoUdenominator',abs(r['Ring_IoU']-r['Ring_intersection_N']/max(1,r['Ring_union_N']))<1e-14)
 hs=load(N/'metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json');base={(r['group'],r['scope']):r for r in hs if r['method']=='B0'and r.get('scope')}
 for r in hs:
  if not r.get('scope'):continue
  check(r['group']+r['method']+r['scope']+'fixedHEROdenominator',r['fixed_N']==base[r['group'],r['scope']]['fixed_N']);sens=r['support_sensitivity_fixed'];check(r['group']+r['method']+r['scope']+'thresholdmonotonic',sens['0.2']<=sens['0.5']<=sens['1.0']);check(r['group']+r['method']+r['scope']+'visibilityconservation',abs(r['support_fraction_fixed']+r['front_fraction_fixed']+r['behind_possible_occlusion_fraction_fixed']+r['CAD_occluded_fraction_fixed']+r['unknown_fraction_fixed']-1)<1e-10)
 originals=load(N/'config/FOUR_GROUP_INPUTS.json');check('51TRUSTEDnativeHEROsourcefilesunchanged',all(sha(s[key]['path'])==s[key]['sha256']for c in originals for s in c['sources']for key in ['mesh','observation']));check('CADand018bodyunchanged',all(sha(c['ring']['path'])==c['ring']['sha256']and all(sha(b['path'])==b['sha256']for b in c['bodies'].values())for c in originals))
 cov=load(N/'metrics/PER_NATIVE_SOURCE_UNIQUE_COVERAGE.json');check('174sourcewiseuniquecoveragerecords',len(cov)==174);check('allnativeFaceIDbindings100percent',all(c['sampled_native_face_binding_N']==c['fixed_unique_native_pixel_N']for c in cov));check('coverageORnotdoublecounting',all(c['unique_known_N']<=c['fixed_unique_native_pixel_N']and c['unique_supported_N']<=c['unique_known_N']for c in cov));check('B2internalrigiditycertified',load(N/'metrics/B2_INTERNAL_RIGID_INVARIANCE.json')['PASS'])
 glbs=load(N/'assets_index/INTERACTIVE_GLBS.json');check('fouractualGLB',len(glbs)==4 and all(Path(x['GLB']['path']).exists()and sha(x['GLB']['path'])==x['GLB']['sha256']for x in glbs));check('GLBroundtripmetric',all(x['roundtrip_bounds_error_m']<1e-6 for x in glbs))
 for x in glbs:
  lay=load(x['layer_manifest']);check(x['group']+'sourcecameraindependentlayers',all(k in {s['kind']for s in lay['nodes']}for k in ['Ring','HERO','CAMERA','BODY']));check(x['group']+'viewerexists',(N/'local_results/interactive'/(x['group']+'_VIEWER.html')).exists())
 stage=load(N/'STAGE_DECISION.json');photos=list(csv.DictReader((N/'metrics/TWELVE_PHOTO_NOT_RUN.csv').open()));check('12photosnotrun',len(photos)==12 and all(p['status']=='NOT_RUN_VIDEO_GATE'for p in photos));check('independentRGBgatepreserved_noHEROselection',stage['hard_fail_reasons']==[] and stage['preregistered_severe_RGB_gate_PASS'] and not stage['scientific_trust_established'] and not stage['independent_HERO_used_for_this_gate']and not stage['B4_run']and stage['photos_run']==0)
 fig=list((N/'figures').glob('Figure*.png'));check('8core4sixviewfigures',len(fig)==8 and len(list((N/'figures').glob('*_SIX_VIEW_ATLAS.png')))==4);reports=list(N.glob('*.md'));check('allreportsrequiredfixedaudit',len(reports)>=12 and all('历史测量值回退'in p.read_text()for p in reports));check('allPython312sourceparse',all(ast.parse(p.read_text())is not None for p in(N/'code').glob('*.py')))
 manifest=load(N/'provenance/DELIVERY_MANIFEST.json')
 for k in ['code','reports','figures']:
  bad=[a['path']for a in manifest[k]if sha(a['path'])!=a['sha256']];check('deliverymanifest'+k,not bad,bad)
 # Existing tracked files outside this new task remain untouched.
 touched=subprocess.check_output(['git','diff','--name-only'],cwd=REPO,text=True).splitlines();check('nohistoricaltrackedmodifications',all(p.startswith(str(N.relative_to(REPO))+'/')for p in touched),touched)
 out=dict(pass_delivery_integrity=all(c['PASS']for c in checks),checks=checks,checks_N=len(checks),failures=[c for c in checks if not c['PASS']],scientific_four_group_geometry_gate_PASS=False,current_status=stage['status'],historical_prediction_fallback=0,new_photos=0,new_HERO_inference=0,body_updates=0)
 save('metrics/DELIVERY_CHECKS.json',out);print(json.dumps({k:v for k,v in out.items()if k not in ['checks']},ensure_ascii=False),flush=True)
 if not out['pass_delivery_integrity']:raise SystemExit(1)
if __name__=='__main__':main()
