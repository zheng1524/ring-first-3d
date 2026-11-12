"""Audit frozen actual results and explicit scientific failure; never refit or repair predictions."""
from gcommon import *
import ast,csv,collections

def main():
 ck=[]
 def check(n,b,d=None):ck.append(dict(check=n,PASS=bool(b),detail=d))
 def hashes(n,arr):
  bad=[a['path']for a in arr if not Path(a['path']).is_file()or sha(a['path'])!=a['sha256']];check(n,not bad,bad)
 hashes('upstream021 source/cameras unchanged',load(M/'provenance/UPSTREAM_FROZEN.json')['files'])
 reuse=load(M/'provenance/REUSE.json');hashes('prior failed experiment/source/photo registry unchanged',[reuse[k]for k in ['previous','gcommon','geometry_inputs','old_counterexamples','photo_manifest']])
 for g in load(P/'config/FOUR_GROUP_INPUTS.json'):
  hashes(g['group']+' originalCAD/body unchanged',[g['ring']]+list(g['bodies'].values()));hashes(g['group']+' all nativeHERO unchanged',[s[k]for s in g['sources']for k in ['mesh','observation']])
 frozen=load(M/'provenance/STAGE2_BEFORE_FORMAL_RUN.json');hashes('formal training protocol and exact loss implementations unchanged',[frozen['protocol']]+frozen['code'])
 vv=load(M/'config/VIEWS.json');check('98 canonicalVIDEO_FRAME81FIT17HOLDOUT',len(vv)==98 and len({v['id']for v in vv})==98 and sum(v['role']=='FIT'for v in vv)==81 and sum(v['role']=='HOLDOUT'for v in vv)==17 and all(v['capture_type']=='VIDEO_FRAME'for v in vv))
 src=load(M/'provenance/MATURE_SOURCE_FETCH.json');check('all7 official source/license files pinned and hashverified',len(src)==7 and all(r.get('pinned_commit_verified_same_bytes')and len(r['commit'])==40 and sha(r['local'])==r['sha256']for r in src))
 j=load(M/'metrics/FIXED_CORRESPONDENCE_JACOBIAN.json');check('60 fixed-correspondence block checks all6DOF3steps pass',len(j)==60 and all(r['pass_local']for r in j));check('Stage1 actual8 solver tests passed',load(M/'STAGE1_GATE.json')['pass_basic_correctness']and load(M/'STAGE1_GATE.json')['actual_TRF_runs']==8)
 syn=load(M/'metrics/CONICS_SYNTHETIC_MID_AUDIT.json');check('8 actual knownCAD-circle inversions',len(syn)==8 and all(r['best_known_circle_center_error_mm']<.01 and r['best_circle_projection_error_px']<.001 for r in syn));mid=load(M/'metrics/CONICS_MID_CONTINUOUS_CURVE_CHECK.json');check('6valid2failedMid selfchecks retained; not swapped forGT',len(mid)==8 and sum(r['Mid_valid']for r in mid)==6 and all(r['true_circle_vs_Mid_continuous_px']is None for r in mid if not r['Mid_valid']))
 reg=load(M/'metrics/OLD_VISIBILITY_REGRESSION.json');check('all4 saved edge counterexample regressions recorded',len(reg)==4 and all(r['no_MISS_automatic_visible']for r in reg));check('all13 old edge states stable under tested perturbations',all(r['repaired_old_edge_states_stable']for r in reg))
 records=[];success=[];failed=[];protected=[]
 for g in GROUPS:
  fr=load(M/'provenance'/(g+'_VIDEO_POSES_FROZEN.json'));hashes(g+' all predictions unchanged since preevaluation freeze',fr['files'])
  for v in[v for v in vv if v['group']==g]:
   for arm in ['P0','S0','A1','A2','A3']:
    r=load(M/'results'/g/arm/v['id']/'FINAL.json');records.append(r)
    if arm=='P0':continue
    if v['role']=='HOLDOUT':protected.append(np.array_equal(r['pose'],v['T'])and r['status']=='PROTECTED_NO_LOCAL_FIT');continue
    if r['status']!='FROZEN_NUMERIC_POSE':failed.append(r);continue
    success.append((g,arm,v,r));C=np.array(r['pose']);C0=np.array(v['T']);physical=np.linalg.norm(C[:3,3]-C0[:3,3])<=1.2+1e-9 and np.degrees(Rotation.from_matrix(C[:3,:3]@C0[:3,:3].T).magnitude())<=10+1e-8
    check(g+arm+v['id']+' SE3 scale/physical/numerical descent',physical and np.isfinite(C).all()and np.allclose(C[:3,:3].T@C[:3,:3],np.eye(3),atol=1e-9)and abs(np.linalg.det(C[:3,:3])-1)<1e-9 and r['final_loss']<=r['initial_loss']+1e-9 and r['physical'][0])
    calls=load(M/'optimization'/g/arm/v['id']/'CALLS.json');tr=load(M/'optimization'/g/arm/v['id']/'TRACE.json');check(g+arm+v['id']+' actualTRF trace and relinearized acceptance',len(calls)==r['nfev']>0 and all(t['after']<=t['before']+1e-9 for t in tr)and not r['HERO_body_GT_in_loss'])
 check('490 outcomes with254 real solves70failedinits68protected98P0',len(records)==490 and len(success)==254 and len(failed)==70 and len(protected)==68 and all(protected))
 check('failedConics no historical prediction fallback',all(r['pose']is None and r['no_prediction_fallback']for r in failed))
 byarm=collections.Counter(a for g,a,v,r in success);check('method target coverage exactly81/46/81/46',byarm==dict(S0=81,A1=46,A2=81,A3=46))
 ev=load(M/'metrics/ALL_VIDEO_METHOD_METRICS.json');check('all490 outcomes evaluated with70explicitmissing',len(ev)==490 and sum(r.get('Ring_IoU')is None for r in ev)==70 and sum(r['new_local_pose']for r in ev)==254)
 den=load(M/'metrics/EXACT_IMAGE_METRIC_DENOMINATORS.json');check('all490 image denominator records, valid unions exact',len(den)==490 and all(r['Ring_union_N']is None or 0<=r['Ring_intersection_N']<=r['Ring_union_N']for r in den))
 hero=load(M/'metrics/FROZEN_DEPTH_COUNTERFACTUAL.json');check('all5methods fourgroups scopes and missingcoverage retained',len(hero)==25 and all(abs(r['support_fraction_fixed']+r['front_fraction_fixed']+r['behind_fraction_fixed']+r['CAD_occluded_fraction_fixed']+r['unknown_fraction_fixed']-1)<1e-10 for r in hero))
 check('rawDepth not reinferred for new pose metrics',all(r['pose_changed_depth_not_reinferred']==(r['method']!='P0')for r in hero))
 cv=load(M/'metrics/RENDER_COVERAGE_CAUSAL_AUDIT.json');check('postrun completeness failure real8curves; no sixth refit',len(cv)==24 and all(r['distance_px']['p95']>4 for r in cv if r['variant']=='ACTUAL_ACCEPTED')and all(r['distance_px']['p95']<.91 for r in cv if r['variant']=='DIAGNOSTIC_RENDER_BAND_WITHOUT_PRIMITIVE_GATE'))
 st=load(M/'STAGE_GATE_DECISION.json');check('current scientific pause overrides preliminary photo allowance',st['status']=='PAUSED_FOR_HUMAN_DIAGNOSIS'and st['stage2_completed']and not st['allow_photo_stage']and load(M/'provenance/PRE_COMPLETENESS_VIDEO_GATE.json')['allow_photo_stage'])
 photos=list(csv.DictReader((M/'metrics/PHOTO_STAGE_NOT_RUN.csv').open()));check('all12photoextensions explicitly notrun',len(photos)==12 and all(r['status']=='NOT_RUN_VIDEO_COMPLETENESS_GATE'for r in photos)and not(M/'results/photos').exists())
 reports=['TECHNICAL_REPORT_SUMMARY.md','TECHNICAL_REPORT.md','MATURE_ALGORITHM_REUSE_AUDIT.md','RING_VISIBILITY_FIX_AND_TEST.md','CONICS_MID_GEOMETRY_AUDIT.md','FOUR_GROUP_RESEARCH_DECISION.md','FAILURE_LEDGER.md'];check('allrequiredreports fixedaudit and no historical fallback',all((M/f).exists()and '| 历史测量值回退 | 0'in(M/f).read_text()for f in reports))
 for f in(M/'code').glob('*.py'):ast.parse(f.read_text())
 check('all source parses',True);check('4core realfigures',len(list((M/'figures').glob('*.png')))==4)
 mani=load(M/'provenance/DELIVERY_MANIFEST.json')
 for k in ['code','reports','figures','predictions']:hashes('delivery manifest '+k,mani[k])
 hashes('stage decision manifest',[mani['stage']]);out=dict(pass_delivery_integrity=all(c['PASS']for c in ck),checks=ck,numeric_camera_outputs=254,target_FIT_routes=324,failed_routes=70,historical_measurement_fallback=0,scientific_full_geometry_gate_pass=False,photo_stage='NOT_RUN_VIDEO_COMPLETENESS_GATE',status='PAUSED_FOR_HUMAN_DIAGNOSIS');save('metrics/DELIVERY_CHECKS.json',out);print(json.dumps(dict(pass_delivery_integrity=out['pass_delivery_integrity'],checks=len(ck),failed=[c for c in ck if not c['PASS']],scientific_full_geometry_gate_pass=False),ensure_ascii=False))
 if not out['pass_delivery_integrity']:raise SystemExit(1)
if __name__=='__main__':main()
