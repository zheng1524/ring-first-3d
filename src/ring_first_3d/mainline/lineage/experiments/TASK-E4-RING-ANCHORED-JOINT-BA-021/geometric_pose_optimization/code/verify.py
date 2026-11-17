"""Integrity verification of a paused experiment, separate from scientific validity."""
from gcommon import *
import ast,csv,collections

def main():
 checks=[]
 def ck(name,ok,detail=None):checks.append(dict(name=name,pass_integrity=bool(ok),detail=detail))
 def hcheck(name,arr):
  bad=[a['path']for a in arr if not Path(a['path']).is_file()or sha(a['path'])!=a['sha256']];ck(name,not bad,bad)
 hcheck('original021 cameras/code/quick manifest unchanged',load(M/'provenance/UPSTREAM_FROZEN.json')['files'])
 old=load(P/'quick_solver_review/provenance/DELIVERY_MANIFEST.json')
 for key in ['code','reports','solver_poses','photo_poses']:hcheck('quick frozen '+key,old[key])
 for g in load(P/'config/FOUR_GROUP_INPUTS.json'):
  hcheck(g['group']+' original Ring/bodies unchanged',[g['ring']]+list(g['bodies'].values()));hcheck(g['group']+' all native HERO mesh/observations unchanged',[s[k]for s in g['sources']for k in ['mesh','observation']])
 inp=load(M/'provenance/INPUTS_FROZEN.json');hcheck('new input/protocol frozen receipt unchanged',[inp['views'],inp['protocol']]+inp['sources'])
 vv=load(M/'config/VIEWS.json');ck('98 unique canonical views and81FIT17HOLDOUT',len(vv)==len({v['id']for v in vv})==98 and collections.Counter(v['group']for v in vv)==dict(G01=68,G03=9,G05=11,G06=10)and sum(v['role']=='FIT'for v in vv)==81 and sum(v['role']=='HOLDOUT'for v in vv)==17)
 H=np.array(load(P/'results/B3.json')['T']);bad=[]
 for v in vv:
  d=np.load(v['cache']);expected=H@d['T']if v['group']=='G01'and v['video']=='005'else d['T']
  if not(np.allclose(v['K'],d['K'],atol=1e-12)and np.allclose(v['T'],expected,atol=1e-12)and sha(v['RGB_source'])==v['RGB_SHA256']and v['capture_type']=='VIDEO_FRAME'):bad.append(v['id'])
 ck('all original RGB identity K and explicit world transforms consistent',not bad,bad)
 J=load(M/'metrics/JACOBIAN_VALIDATION.json');ck('120 registered blocks720 per-axis comparisons',len(J)==120 and all(len(r['columns'])==6 for r in J)and set(r['group']for r in J)==set(GROUPS))
 ck('h1e-5 local convergence retained without overwriting failed multistep gate',all(r['pass_all6']for r in J if r['h']==.00001)and not load(M/'config/JACOBIAN_GATE.json')['pass_required_geometric_J']and any(not r['pass_all6']for r in J if r['h']==.0001))
 ck('144 real objective branch probes preserved',len(load(M/'metrics/FAILURE_BRANCH_ISOLATION.json'))==144)
 edges=load(M/'metrics/CAD_VISIBILITY_SWITCH_CAUSES.json');ck('all4 groups realCAD switching edge traces',len(edges)==4 and sum(len(r['changed_edges'])for r in edges)==13)
 g05=next(r for r in edges if r['group']=='G05');badedge=next(e for e in g05['changed_edges']if e['CAD_vertex_ids']==[9065,9129]);ck('G05 real miss treated visible then finite hit culled',badedge['states']['base']['ray_hit_finite']==False and badedge['states']['base']['visible']and badedge['states']['plus']['ray_hit_finite']and not badedge['states']['plus']['visible'])
 dd=next(r for r in load(M/'metrics/FAILURE_BRANCH_ISOLATION.json')if r['group']=='G05'and r['point']=='zero'and r['h']==.0001 and r['axis']==0);ck('actual objective sign reversal preserved',dd['AD_objective']<0 and dd['objective_FD']['all']['full_visible_edges_recomputed_FD']>0 and abs(dd['objective_FD']['all']['nearest_reassociate_same_visible_edges_FD']-dd['AD_objective'])<1e-6)
 st=load(M/'STAGE_GATE_DECISION.json');ck('paused status and no invented solver/pose/photo results',st['status']=='PAUSED_FOR_HUMAN_DIAGNOSIS'and not st['stage_A_completed']and st['stage_A_formal_solver_runs']==st['stage_A_derived_camera_outputs_N']==st['stage_B_photo_runs']==0 and st['stage_B']=='NOT_RUN_STAGE_A_GATE'and not list((M/'results').rglob('FINAL.json'))and not list((M/'optimization').rglob('TRACE.json')))
 rows=load(M/'metrics/ALL_VIDEO_P0_METRICS.json');ck('all98 P0 metrics preserved P1 missing',len(rows)==98 and all(r['P1_translation_mm']is None and r['P1_Ring_IoU']is None and r['P1_status']=='NOT_RUN_JACOBIAN_GATE'for r in rows))
 hero=load(M/'metrics/P0_NATIVE_HERO_PROXIES.json');ck('all51 source HERO baselines with category conservation',sum(r['sources_N']for r in hero)==51 and all(r['known_N']==r['visibility_categories']['supported']+r['visibility_categories']['front']+r['visibility_categories']['behind']and r['fixed_source_target_N']==r['known_N']+r['visibility_categories']['cad_occluded']+r['visibility_categories']['unknown']for r in hero))
 scores=list(csv.DictReader((M/'FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.csv').open()));ck('all4 P1 numeric gaps exported as NaN notzero',len(scores)==4 and all(r['P1_translation_mm']=='NaN'and r['P1_HERO_improvement_mm']=='NaN'for r in scores))
 photos=list(csv.DictReader((M/'metrics/TWELVE_PHOTO_NOT_RUN.csv').open()));ck('12 correct same-capture photo identities explicitly not run',len(photos)==12 and all(r['status']=='NOT_RUN_STAGE_A_GATE'for r in photos))
 for p in(M/'code').glob('*.py'):ast.parse(p.read_text())
 ck('all current code parses',True)
 reports=['TECHNICAL_REPORT_SUMMARY.md','TECHNICAL_REPORT.md','CLASSICAL_GEOMETRIC_OPTIMIZATION_AUDIT.md','RING_JACOBIAN_VALIDATION.md','FOUR_GROUP_POSE_OPTIMIZATION_DECISION.md','FAILURE_LEDGER.md']+[g+'_POSE_REPORT.md'for g in GROUPS]
 ck('all required reports include fixed research audit table',all((M/p).is_file()and '| 历史测量值回退 | 0' in(M/p).read_text()for p in reports))
 ck('six actual figures, nofake stageB figures',len(list((M/'figures').glob('*.png')))==6 and not list((M/'figures').glob('Figure7*'))and not list((M/'figures').glob('Figure8*')))
 manifest=load(M/'provenance/REPORT_DELIVERY_MANIFEST.json')
 for k in ['code','reports','figures']:hcheck('delivery manifest '+k,manifest[k])
 hcheck('gate unchanged',[manifest['stage']]);save('metrics/DELIVERY_INTEGRITY.json',dict(pass_integrity=all(c['pass_integrity']for c in checks),checks=checks,scientific_geometric_gate_pass=False,formal_pose_optimizer_runs=0,stage='PAUSED_FOR_HUMAN_DIAGNOSIS',history_measurement_fallback=0))
 print(json.dumps(dict(pass_integrity=all(c['pass_integrity']for c in checks),checks=len(checks),failed=[c for c in checks if not c['pass_integrity']],scientific_geometric_gate_pass=False),ensure_ascii=False))
 if not all(c['pass_integrity']for c in checks):raise SystemExit(1)
if __name__=='__main__':main()
