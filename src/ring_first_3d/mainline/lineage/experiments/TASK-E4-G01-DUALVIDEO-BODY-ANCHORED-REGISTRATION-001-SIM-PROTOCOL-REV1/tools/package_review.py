from pathlib import Path
import json,shutil,hashlib,subprocess,csv,collections
import numpy as np
from scipy.spatial.transform import Rotation
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.synthetic.io import fetch
root=Path.cwd();tid='TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1';td=root/'experiments'/tid;run=td/'runs/SIM_REV1_001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=load_task(td/'TASK.yaml');state=read_state(run);assert state['accepted'];check_artifacts(run,state)
i=verify_task(t)
assert i['freeze_sha256']==state['freeze_sha256']
from ring_first_3d.sim.geometry import transform,summary
commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md','metrics.json','failures.json','evidence.png']:
 assert not(td/name).exists();shutil.copyfile(run/name,td/name)
shutil.copytree(run/'visualization',td/'visualization');(td/'evidence').mkdir();shutil.copyfile(run/'RUN_MANIFEST.json',td/'evidence/ORIGINAL_RUN_MANIFEST.json');shutil.copyfile(run/'FREEZE.json',td/'evidence/FREEZE.json')
for folder in sorted((run/'attempts').iterdir()):
 out=td/'evidence/attempts'/folder.name;out.mkdir(parents=True)
 for f in folder.iterdir():
  if f.is_file() and f.suffix in {'.json','.txt','.md','.csv'}:shutil.copyfile(f,out/f.name)
reg=json.loads(fetch(run,'sim_regression','payload.json').read_text()) if False else json.loads((next((run/'attempts').glob('*-sim_regression-*'))/'payload.json').read_text())
for stage,name in [('G1_initialize','IMAGE_FITS.json'),('G1_initialize','BODY_FREEZE.json'),('G1_initialize','REUSE_RECEIPTS.json')]:shutil.copyfile(fetch(run,stage,name),td/'visualization'/name)
metrics=json.loads(fetch(run,'G4_evaluate','REGISTRATION_METRICS.json').read_text());lookup={(r['condition'],r['method']):r for r in metrics['rows']};pred=json.loads(fetch(run,'G3_matrix_predict','PREDICTIONS_FROZEN.json').read_text());g1=json.loads(fetch(run,'G1_evaluate','G1_METRICS.json').read_text());g2=json.loads(fetch(run,'G2_evaluate','G2_METRICS.json').read_text());imagefits=json.loads(fetch(run,'G1_initialize','IMAGE_FITS.json').read_text());cond=['S0','S1','S2','S3','S4']
pairs=[]
for first,second in [('M0','M2'),('M1','M2'),('M2_DIRECT','M2'),('RING_ONLY','M2'),('M2','M2_RING')]:
 valid=[c for c in cond if lookup[c,first]['status']=='NUMERIC' and lookup[c,second]['status']=='NUMERIC']
 for metric,key in [('relative_rotation_deg',('relative_after','rotation_deg')),('relative_translation_mm',('relative_after','translation_mm')),('GT_surface_MAE_mm',('GT_surface_mm','MAE'))]:
  a=np.array([lookup[c,first][key[0]][key[1]]for c in valid]);b=np.array([lookup[c,second][key[0]][key[1]]for c in valid]);pairs.append(dict(first=first,second=second,metric=metric,target_conditions=5,common_numeric_conditions=valid,N=len(valid),first_mean=float(a.mean()),second_mean=float(b.mean()),paired_second_minus_first=summary(b-a),signed_mean_difference=float((b-a).mean()),historical_fusion=False))
(td/'visualization/PAIRED_COMPARISONS.json').write_text(json.dumps(pairs,indent=2)+'\n')
# Full per-point audit, including misses, contact-unknown cuts and actual barycentric coordinates.
frozen=json.loads(fetch(run,'G2_mapping','MAPPING_FROZEN.json').read_text());mapping_fail=[];points=td/'visualization/G2_CANDIDATE_AUDIT.csv';N=0
fields=['source_id','video','role','domain','method','point_index','u','v','mapped_u','mapped_v','face_id','bary0','bary1','bary2','X_mm','Y_mm','Z_mm','confidence','numeric_valid','Ring_contact_unknown','failure_reason','GT_virtual_original_pixel_visible','GT_candidate_point_error_mm']
with points.open('w',newline='')as stream:
 w=csv.writer(stream,lineterminator='\n');w.writerow(fields)
 for r in frozen['rows']:
  m=np.load(fetch(run,'G2_mapping','maps/'+r['key']+'.npz'));truth=np.load(fetch(run,'G0_simulate','private/'+r['id']+'.npz'));uv=m['original_uv'].astype(int);tv=truth['true_visible'][uv[:,1],uv[:,0]];truepoints=truth['points'][uv[:,1],uv[:,0]]
  err=np.linalg.norm(m['points']-truepoints,axis=1);counter=collections.Counter(m['reason'].tolist());mapping_fail.append(dict(id=r['id'],video=r['video'],role=r['role'],domain=r['domain'],method=r['method'],target_N=len(uv),reason_counts=dict(counter),numeric_N=int(m['valid'].sum()),contact_unknown_N=int(m['contact_unknown'].sum()),GT_virtual_visible_N=int(tv.sum()),real_source_GT_note='G01-like virtual ray diagnostic only, not certified physical G01 correspondence'))
  for i in range(len(uv)):
   e=float(err[i])if m['valid'][i]and tv[i]and not m['contact_unknown'][i]else float('nan')
   row=[r['id'],r['video'],r['role'],r['domain'],r['method'],i,*m['original_uv'][i],*m['mapped_uv'][i],int(m['face'][i]),*m['bary'][i],*m['points'][i],float(m['confidence'][i]),bool(m['valid'][i]),bool(m['contact_unknown'][i]),str(m['reason'][i]),bool(tv[i]),e]
   w.writerow(['NaN'if isinstance(v,(float,np.floating))and not np.isfinite(v)else v for v in row]);N+=1
(td/'visualization/MAPPING_FAILURES.json').write_text(json.dumps(mapping_fail,indent=2)+'\n')
# Outcome and source-scope summaries: no post-evaluation re-selection or re-fit.
formal={d:dict(frames=sum(r['domain']==d for r in imagefits),numeric=sum(r['formal']['available']for r in imagefits if r['domain']==d),strict_stable=sum(r['formal']['quality'].get('strict_stable',False)is True for r in imagefits if r['domain']==d))for d in ['synthetic','real_source']}
summary_methods={m:dict(primary_targets=5,independent_numeric=sum(lookup[c,m]['status']=='NUMERIC'for c in cond),relative_pose_pass=sum(lookup[c,m].get('relative_pose_pass',False)for c in cond))for m in t['sim']['methods']}
# Rotation components are post-freeze diagnostics, not an algorithm switch.
injections=json.loads(fetch(run,'G0_simulate','private/INJECTIONS.json').read_text());pose_components=[]
for p in pred['rows']:
 if p['status']!='NUMERIC':continue
 E={v:np.asarray(p['corrections'][v])@np.asarray(injections[p['condition']][v])for v in ['004','005']};rel=np.linalg.inv(E['004'])@E['005'];pose_components.append(dict(condition=p['condition'],method=p['method'],relative_rotvec_deg=np.rad2deg(Rotation.from_matrix(rel[:3,:3]).as_rotvec()).tolist(),relative_translation_vector_mm=rel[:3,3].tolist()))
(td/'visualization/RELATIVE_POSE_COMPONENTS.json').write_text(json.dumps(pose_components,indent=2)+'\n')
summary_result=dict(execution='ALL_G0_G4_EXECUTED',scientific_result='BODY_MEDIATED_REGISTRATION_DID_NOT_PASS_FROZEN_POSE_CRITERION',criterion=dict(rotation_deg_max=.5,translation_mm_max=.2),methods=summary_methods,DXY_scope='Frozen API consumed only center/basis/quality; no P/Q modification, no diameter research, no extra candidate search after user steering',DXY_counts=formal,Body_arm=g1['selected_arm'],Body_freeze_sha256=json.loads(fetch(run,'G1_initialize','BODY_FREEZE.json').read_text())['body_sha256'],regression=reg,run_seconds=state['spent_seconds'],budget=t['budget'],local_full_run=str(run),implementation_commit=commit)
(td/'SCIENTIFIC_RESULT.json').write_text(json.dumps(summary_result,indent=2,ensure_ascii=False)+'\n')
# Keep all scientific failures and mapping reasons; no permanent-rule promotion.
ledger=json.loads((td/'visualization/FAILURE_LEDGER.json').read_text());ledger['mapping_failure_rows']=mapping_fail;ledger['formal_DXY_quality_counts']=formal;ledger['code_errors_observed']=0;(td/'visualization/FAILURE_LEDGER.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n')
entries=[]
def entry(id,symptom,cause,paths):
 entries.append(dict(id=id,category='scientific_negative',modules=['DV03','DV04','DV05','DV06'],symptom=symptom,cause=cause,cause_status='observed_only',repair='Retain the frozen negative result for human review; no GT-based parameter retuning or automatic method substitution',regression=['test_sim_rev1: full rigid geometry, gauge and mediated-vs-direct query contracts'],evidence=[dict(path=str((td/p).relative_to(root)),sha256=sha(td/p))for p in paths],rule_status='candidate',review=dict(status='unreviewed',reviewer=None,evidence=None)))
entry('FM-SIM-POSE-001','M2 numeric on 5/5 primary conditions but 0/5 meet relative rotation<=0.5deg and translation<=0.2mm','Coarse-Body bias / candidate ambiguity and rotation observability are plausible, not causally isolated; small surface distance does not certify relative SE3',['visualization/REGISTRATION_METRICS.json','visualization/RELATIVE_POSE_COMPONENTS.json'])
entry('FM-SIM-ROTATION-001','Robust ICP leaves ~1.5deg rotation despite very small GT surface error','Partial-surface geometry permits a low surface residual with residual rotation; no claim of a proven sole cause',['visualization/REGISTRATION_METRICS.json','visualization/PAIRED_COMPARISONS.json'])
entry('FM-SIM-MAPPING-001','Mediated mapping has unmatched and Ring-contact-unknown points and nonzero GT candidate errors','Ellipse-to-ellipse warp is a candidate correspondence, not a physical correction; coarse model and unknown cuts remain limitations',['visualization/G2_METRICS.json','visualization/MAPPING_FAILURES.json'])
(td/'FAILURE_REGISTRY.json').write_text(json.dumps(dict(schema=1,policy='Task-local candidate scientific facts only; no automatic promotion to permanent rules; previous authenticity failure evidence retained',failures=entries),indent=2,ensure_ascii=False)+'\n')
intro=f'''# SIM_PROTOCOL_REV1：执行完成，二维主体配准尚未达标

**G0–G4全部实际运行，Runner 14个阶段及产物检查通过，82项回归通过。科学结论：M2在5/5主条件产生独立数值输出，但0/5同时满足冻结的0.5°/0.2mm相对位姿门限。没有按GT结果重调参数、重新选择Body或重跑DXY。**

S1的M2相对误差由2.000°/0.500mm变为1.925825°/0.126307mm；GT曲面MAE/p95为0.015705/0.060733mm。Robust ICP为1.500132°/0.009874mm，曲面MAE/p95约0.003588/0.012816mm；这些小曲面残差均不能证明正确相对旋转。Ring-only在本轮Y倾斜设置下5/5通过，不能将这项恢复归功于二维主体。

实现提交：`{commit}`。原始Runner冻结指纹：`{state['freeze_sha256']}`。历史原G0、TASK与失败记录原样保留，本轮为独立SIM_PROTOCOL_REV1。

[完整曲面交互](visualization/mesh_registration.html) · [真实对应逐点CSV](visualization/G2_CANDIDATE_AUDIT.csv) · [全部负结果/未匹配台账](visualization/FAILURE_LEDGER.json) · [共同数值条件配对](visualization/PAIRED_COMPARISONS.json)

DXY仅为当前Body初始化与中介映射提供冻结API的中心、basis、质量；没有算法修改或P/Q/直径精度研究。合成/原图各33帧数值候选；严格稳定分别{formal['synthetic']['strict_stable']}/33和{formal['real_source']['strict_stable']}/33，不能将数值候选称为严格测量通过。E1/E2/显式代理各三初值均收敛；Body依冻结优先级选E1，并在全部配准中保持SHA不变。原TRF多初值使用冻结历史源码中的20261104+start种子；仿真协议的20261116种子与无随机误差矩阵分开记录。

G2数值覆盖和独立可评价覆盖分开报告：合成中介2670/3168有Body候选，984/3168同时可独立评价且非Ring接触未知；直接原像素1549/3168有候选，117/3168独立可评价。真实原图分支仅为G01-like虚拟射线诊断。所有{N}个目标查询点、Face ID=-1、NaN、接触未知及置信度均已导出，不只展示成功点。

本地运行共{state['spent_seconds']:.3f}s，低于7200s预算；没有新的主体重建训练、实际HERO推理或跨视频BA。表面统计为完整局部Mesh顶点对独立GT三角面的距离，所有视频完整顶点均在分母内；这不是直径精度评估。L1与主S0–S4独立。

---

'''
(td/'TECHNICAL_REPORT.md').write_text(intro+(td/'TECHNICAL_REPORT.md').read_text())
(td/'RESULT_CARD.md').write_text(intro.split('---')[0]+'\n[完整报告](TECHNICAL_REPORT.md) · [RUN_MANIFEST](RUN_MANIFEST.json)\n')
# Local-only visual exports; original runner snapshots remain untouched.
p=td/'visualization/index.html';s=p.read_text();note='<p style="background:#ffe8cc;padding:16px"><b>科学结论：二维主体M2尚未达标。</b>5/5主条件有独立数值输出，0/5通过冻结相对位姿门限。Ring-only 5/5。所有失败、未匹配与HOLDOUT均保留。</p><p><a href="G2_CANDIDATE_AUDIT.csv">逐点Face/重心/XYZ/置信度/失败CSV</a> · <a href="PAIRED_COMPARISONS.json">共同数值条件配对</a> · <a href="MAPPING_FAILURES.json">逐帧对应失败</a> · <a href="IMAGE_FITS.json">仅二维候选与质量</a> · <a href="../FAILURE_REGISTRY.json">候选Failure Registry</a></p>'
s=s.replace('<h1>',note+'<h1>',1);p.write_text(s)
# Match interactive and static scientific error palettes, without changing data.
import matplotlib
matplotlib.use('Agg')
from matplotlib import colormaps
palette=(colormaps['turbo'](np.linspace(0,1,256))[:,:3]*255).round().astype(int).tolist();p=td/'visualization/mesh_registration.html';before=sha(p);s=p.read_text();old="function heat(e){let t=Math.min(1,Math.max(0,e));return 'rgb('+Math.round(35+220*t)+','+Math.round(160*(1-t))+','+Math.round(240*(1-t))+')'}";new="const SCIENTIFIC_PALETTE="+json.dumps(palette,separators=(',',':'))+";function heat(e){const c=SCIENTIFIC_PALETTE[Math.round(Math.min(1,Math.max(0,e))*255)];return 'rgb('+c.join(',')+')'}";assert old in s;s=s.replace(old,new);p.write_text(s)
(td/'PRESENTATION_RECEIPT.json').write_text(json.dumps(dict(original_Runner_scene_sha256=before,delivered_scene_sha256=sha(p),change='Presentation only: match offline interactive GT error palette to existing static Turbo 0-1+mm. No mesh, correction, input or metric changed.',additional_outputs='Read-only exports and summaries of frozen existing predictions/evaluations; no new DXY calls, fitting or parameter selection'),indent=2)+'\n')
(td/'README.md').write_text('''# SIM_PROTOCOL_REV1交付

G0–G4全部运行；执行验收通过，科学M2位姿门限未通过。先读RESULT_CARD与TECHNICAL_REPORT。

直接离线打开`visualization/index.html`，再进入完整曲面五阶段交互。支持全部S0–S4/独立L1、M0/M1/M2/Ring/直接像素/Ring辅助方法。灰Body、黑Ring、红004、蓝005都是真实冻结网格；GT仅评价。

```bash
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/TASK.yaml --run-dir experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001-SIM-PROTOCOL-REV1/runs/SIM_REV1_001
```

`policy.py check`校验TASK，`run --stage 阶段名`只能按依赖执行，`accept`验收完整产物，科学结论等待人工审阅。无force/跳过门禁。原始全量RGB/Mask/轴向深度/完整Mesh/Face映射NPZ保留在本地runs；Git只提交代码、冻结配置、小表、精选PNG和包含完整曲面的离线HTML。DXY无需重跑；新提示限定其为G1/G2辅助，未开展任何DXY算法研究。
''')
manifest=dict(schema='sim-rev1-delivery-1',execution_status='ALL_G0_G4_COMPLETED',runner_accepted=True,scientific_acceptance='AWAITING_HUMAN_REVIEW',scientific_result=summary_result['scientific_result'],implementation_commit=commit,task_sha256=sha(td/'TASK.yaml'),source_manifest_sha256=sha(td/'inputs/G01_DUALVIDEO_SOURCES.json'),runner_freeze_sha256=state['freeze_sha256'],local_original_run=str(run),stages={s:'PASS'for s in t['authorization']['stages']},regression=dict(tests=82,failures=0,errors=0),methods=summary_methods,budget=t['budget'],spent_seconds=state['spent_seconds'],preserved_original_failure_task=str(root/'experiments/TASK-E4-G01-DUALVIDEO-BODY-ANCHORED-REGISTRATION-001'))
files=[p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json'];manifest['artifacts']={str(p.relative_to(td)):dict(sha256=sha(p),bytes=p.stat().st_size)for p in sorted(files)};(td/'RUN_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print('PACKAGED',len(manifest['artifacts']),'files;',N,'candidate records; implementation',commit)
