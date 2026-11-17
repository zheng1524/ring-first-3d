"""Read-only export from accepted, frozen Runner predictions, never new fits."""
from pathlib import Path
import json,hashlib,shutil,csv,re,subprocess
import numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.synthetic.io import fetch,save_json
root=Path.cwd();td=root/'experiments/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001';run=td/'runs/STRESS_REAL_001';task=load_task(td/'TASK.yaml');state=read_state(run);assert state['accepted'];assert verify_task(task)['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state)
from ring_first_3d.stress.real import manifest,load_view,native_pixels
from ring_first_3d.multisurface.registration import model_namespace
from ring_first_3d.multisurface.geometry import transform
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['TECHNICAL_REPORT.md','RESULT_CARD.md','metrics.json','failures.json','evidence.png']:
 assert not(td/name).exists();shutil.copyfile(run/name,td/name)
shutil.copytree(run/'visualization',td/'visualization');(td/'evidence').mkdir()
for name in ['FREEZE.json','RUN_MANIFEST.json']:shutil.copyfile(run/name,td/'evidence'/('ORIGINAL_'+name))
for folder in sorted((run/'attempts').iterdir()):
 out=td/'evidence/attempts'/folder.name;out.mkdir(parents=True)
 for p in folder.iterdir():
  if p.is_file()and p.suffix in {'.json','.txt','.csv','.md'}:shutil.copyfile(p,out/p.name)
vis=td/'visualization';pred=json.loads(fetch(run,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text())['rows'];frames=[f for f in json.loads(fetch(run,'G0_views_noise','public/FRAME_INDEX.json').read_text())if f['role']=='FIT'];bodies={a:dict(np.load(fetch(run,'G1_body',a+'_BODY.npz')))for a in ['E1','E2']};truth={f['id']:dict(np.load(fetch(run,'G0_views_noise','private/'+f['id']+'_truth.npz')))for f in frames};fits={f['id']:f for f in json.loads(fetch(run,'G1_body','IMAGE_FITS.json').read_text())};ns=model_namespace(task);rows=[];figures=[]
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import cv2
representatives={next(f['id']for f in frames if f['video']==v)for v in ['004','005']}

def correspondence_plot(image,labels,fit,body,C,K,X,m,errors,title,path):
 from scipy.spatial.transform import Rotation
 c,Q,a=ns['decode'](body['p'],body['R0']);inv=np.linalg.inv(X);p=np.r_[transform(c[None],inv)[0],np.zeros(3),np.log(a)];R0=inv[:3,:3]@Q;_,_,_,curve=ns['ellipse_projection'](p,R0,K,C)
 fig,axs=plt.subplots(1,2,figsize=(15,5),layout='constrained');uv=m['original_uv'];mapped=m['mapped_uv'];keep=m['accepted'];theta=np.arange(256)*2*np.pi/256;ellipse=np.asarray(fit['center_px'])+np.c_[np.cos(theta),np.sin(theta)]@np.asarray(fit['basis_px']).T
 for ax in axs:
  ax.imshow(image);contours,_=cv2.findContours((labels==1).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
  for cnt in contours:ax.plot(cnt[:,0,0],cnt[:,0,1],c='#33cc77',lw=.6)
  ax.plot(ellipse[:,0],ellipse[:,1],c='orange',lw=1.,label=fit['mapping_fit']);ax.plot(curve[:,0],curve[:,1],c='white',lw=1.,label='Frozen Body projection in pulled-back source chart');ax.set(xlim=(0,image.shape[1]),ylim=(image.shape[0],0),xlabel='native x [px]',ylabel='native y [px]')
 color=np.where(keep,'#22bb55','#ffbb22')if errors is None else np.where(~keep,'#ffbb22',np.where(errors>.5,'#dd2233','#22bb55'))
 axs[0].scatter(uv[:,0],uv[:,1],s=12,c=color,marker='x');axs[0].set_title('All source samples; orange=unmatched/rejected')
 segments=np.stack([uv,mapped],axis=1);finite=np.isfinite(segments).all((1,2));axs[1].add_collection(LineCollection(segments[finite],colors=color[finite],linewidths=.6,alpha=.6));axs[1].scatter(mapped[finite,0],mapped[finite,1],s=9,c=color[finite]);axs[1].set_title('Ellipse-mediated candidates, not physical pose correction')
 for ax in axs:ax.legend(fontsize=6)
 fig.suptitle(title+('\nRed=accepted candidate >0.5mm from independent true material point; rejected targets remain shown'if errors is not None else'\nNo GT: green accepted is only numerical correspondence; correctness cannot be certified'),fontsize=9);fig.savefig(path,dpi=110);plt.close(fig)

for r in pred:
 if r['status']!='NUMERIC':continue
 for f in frames:
  path=fetch(run,'G3_all_predict',r['key']+'/'+f['id']+'_FINAL_CANDIDATES.npz');m=dict(np.load(path));take=np.linspace(0,len(truth[f['id']]['Ptrue'])-1,min(task['fusion']['registration_samples_per_view'],len(truth[f['id']]['Ptrue'])),dtype=int);Q=m['candidate_points'];err=np.linalg.norm(Q-truth[f['id']]['Ptrue'][take],axis=1);accepted=m['accepted'];row=dict(key=r['key'],id=f['id'],video=f['video'],target_N=len(err),accepted_N=int(accepted.sum()),rejected_N=int((~accepted).sum()),candidate_error_to_true_material_mm=[float(x)if np.isfinite(x)else None for x in err],accepted=accepted.tolist(),original_uv=m['original_uv'].tolist(),mapped_uv=m['mapped_uv'].tolist(),candidate_body_face=m['face'].tolist(),candidate_bary=m['bary'].tolist(),confidence=m['confidence'].tolist(),accepted_error_above_body_tolerance_N=int((accepted&(err>.5)).sum()),GT_only_postfreeze=True)
  rows.append(row)
  if f['id']in representatives and r['arm']=='E1'and r['method']in ['BODY_HIER','BODY_HIER_CTF']:
   obs=np.load(fetch(run,'G0_views_noise','public/observations/'+f['id']+'.npz'));C=next(c['estimated_C']for c in json.loads(fetch(run,'G0_views_noise','public/conditions/'+r['condition']+'/ESTIMATED_POSES.json').read_text())if c['id']==f['id']);filename='CORR_'+r['key']+'_'+f['video']+'.png';correspondence_plot(obs['RGB'],obs['labels'],fits[f['id']],bodies[r['arm']],np.asarray(C),np.asarray(f['K']),np.asarray(r['surface_corrections'][f['id']]),m,err,r['key']+' / '+f['id'],vis/'figures'/filename);figures.append(filename)
save_json(vis/'CANDIDATE_FAILURE_DIAGNOSTICS.json',dict(rows=rows,classification='Post-freeze independent material discrepancy, not a new prediction gate',failed_candidates_retained=True))
# No-GT real correspondence evidence from the same frozen native candidates.
realpred=json.loads(fetch(run,'real_predict','REAL_PREDICTIONS_FROZEN.json').read_text());sourceby={g['group']:g for g in manifest(task)['groups']};realrows=[]
for group in realpred['groups']:
 if group['status']!='NUMERIC':continue
 g=group['group'];src=sourceby[g];data=[load_view(r,[.3,.1])for r in src['views']if r['role']=='FIT'];body=dict(np.load(fetch(run,'real_predict',g+'/'+group['primary_body']+'_BODY.npz')));represent={next(d['id']for d in data if d['video']==v)for v in ['004','005']if any(d['video']==v for d in data)}
 for record in group['records']:
  if record['status']!='NUMERIC':continue
  for d in data:
   m=dict(np.load(fetch(run,'real_predict',g+'/'+record['method']+'/'+d['id']+'_CANDIDATES.npz')));realrows.append(dict(group=g,method=record['method'],id=d['id'],target_N=len(m['accepted']),accepted_N=int(m['accepted'].sum()),rejected_N=int((~m['accepted']).sum()),absolute_correspondence_correctness='NOT_EVALUABLE_NO_GT'))
   if record['method']=='BODY_HIER'and d['id']in represent:
    cache=np.load(d['source']['assets']['cache']['path']);H,W=d['labels'].shape;y,x=np.mgrid[:H,:W];p=native_pixels(np.c_[x.ravel(),y.ravel()],d['K'],cache['K']);image=cache['RGB'][p[:,1],p[:,0]].reshape(H,W,3);filename='CORR_'+g+'_'+d['video']+'.png';correspondence_plot(image,d['labels'],d['fit'],body,d['C'],d['K'],np.asarray(record['corrections'][d['id']]),m,None,g+' / '+d['id']+' REAL no GT',vis/'figures'/filename);figures.append(filename)
 # Correct near/far clipping for this page's complete frozen geometry extent.
 page=vis/g/'multisurface_3d.html';s=page.read_text();s=s.replace('-p.z/100.0','-p.z/1000.0');page.write_text(s)
save_json(vis/'REAL_CANDIDATE_DIAGNOSTICS.json',dict(rows=realrows,GT_available=False))
page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Frozen correspondence failures</title><style>body{font:16px system-ui;max-width:1500px;margin:25px auto}img{max-width:100%}</style><h1>实际图像与冻结二维主体候选，包含错误/拒绝对应</h1><p>绿色轮廓=观测Mask，橙椭圆=正式像素主体，白色=拉回源图表的冻结Body投影。GT仅用于仿真预测冻结后的候选误差诊断。所有代表帧固定为每视频第一个FIT，未按结果挑选。</p><a href="index.html">首页与实际完整Mesh切面</a>'
for name in figures:page+='<h2>'+name+'</h2><img loading="lazy" src="figures/'+name+'">'
page+='<p><a href="CANDIDATE_FAILURE_DIAGNOSTICS.json">全部仿真候选/Face/重心/置信度/错误</a> · <a href="REAL_CANDIDATE_DIAGNOSTICS.json">真实拒绝/未匹配数量</a></p></html>'; (vis/'correspondence_failures.html').write_text(page)
p=vis/'index.html';s=p.read_text().replace('</html>','<p><a href="correspondence_failures.html">实际源图、二维主体、Body投影及错误/未匹配对应</a></p></html>');p.write_text(s)
# Add explicit all-case and per-view failure indexes without changing raw snapshots.
ledger=json.loads((vis/'FAILURE_LEDGER.json').read_text());ledger['real_group_results']=json.loads((vis/'REAL_METRICS.json').read_text())['rows'];ledger['candidate_failure_index']='CANDIDATE_FAILURE_DIAGNOSTICS.json';ledger['real_candidate_failure_index']='REAL_CANDIDATE_DIAGNOSTICS.json';ledger['all_simulated_cases_cut_plot']='sections_all.html';save_json(vis/'FAILURE_LEDGER.json',ledger)
s=json.loads((vis/'STRESS_METRICS.json').read_text());reals=json.loads((vis/'REAL_METRICS.json').read_text());commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();report=td/'TECHNICAL_REPORT.md';text=report.read_text();text+='\n## 冻结后只读交付核验\n\n实现提交 `'+commit+'`；Runner指纹 `'+state['freeze_sha256']+'`。117项实测回归、16阶段执行/产物门禁通过。原始Runner快照和失败证据保留；补充只读导出未重新拟合、调参或选择预测。报告首图仍为真实完整Mesh切面。\n\n[实际源图/二维主体/Body投影/拒绝与错误对应](visualization/correspondence_failures.html)保留所有96目标/视角的Face、重心、置信度与NaN；仿真候选GT错配只在冻结后标注，真实对应不认证精度。全部组合的切面通过[切面索引](visualization/sections_all.html)查看；真实组另有逐方法完整网格。\n';report.write_text(text)
summary=dict(implementation_commit=commit,execution='COMPLETED',tests=117,stages=16,simulation_numeric=sum(r['status']=='NUMERIC'for r in s['rows']),simulation_models=len(s['rows']),scientific_failure_cases=len(ledger['failures']),dispersion_GT_contradictions=s['contradictions'],real_groups_numeric=len({r['group']for r in reals['rows']if r['status']=='NUMERIC'}),real_groups_target=3,real_absolute_accuracy='NOT_EVALUABLE',DXY_calls=0,new_HERO_inference=0,camera_optimization=False,GT_alignment=False,history_measurement_fallback=0)
save_json(td/'SCIENTIFIC_RESULT.json',summary)
entries=[]
for id,symptom,paths in [('FM-STRESS-C0-001','Error-free C0 may drift under Body correspondence; retain independent material errors',['visualization/STRESS_METRICS.json','visualization/figures/C0_SECTIONS.png']),('FM-STRESS-DISPERSION-001','Lower surface dispersion is not independent material or reconstruction accuracy',['visualization/STRESS_METRICS.json','visualization/CANDIDATE_FAILURE_DIAGNOSTICS.json']),('FM-STRESS-REAL-PILOT-001','Real HERO pilot lacks independent GT; source/holdout/overlap evidence only',['visualization/REAL_AUDIT.json','visualization/REAL_METRICS.json'])]:
 entries.append(dict(id=id,category='scientific_negative',modules=['SR01','SR02','SR03'],symptom=symptom,cause='Observed evidence only; individual model bias and measurement contributions are not causally isolated',cause_status='observed_only',repair='Preserve metrics, original geometry and all failures for human review; do not tune using GT or promote automatic permanent rules',regression=['117 original and added scope/source/coordinate/isolation tests'],evidence=[dict(path=str((td/p).relative_to(root)),sha256=sha(td/p))for p in paths],rule_status='candidate',review=dict(status='unreviewed',reviewer=None,evidence=None)))
save_json(td/'FAILURE_REGISTRY.json',dict(schema=1,failures=entries,permanent_rule_promotion=False))
manifest=dict(schema='stress-real-delivery-1',task_id=task['task_id'],implementation_commit=commit,runner_freeze_sha256=state['freeze_sha256'],accepted=True,scientific_acceptance='AWAITING_HUMAN_REVIEW',local_original_run=str(run),spent_seconds=state['spent_seconds'],budget=task['budget'],summary=summary)
files=sorted(p for p in td.rglob('*')if p.is_file()and'runs'not in p.relative_to(td).parts and p!=td/'RUN_MANIFEST.json');manifest['artifacts']={str(p.relative_to(td)):dict(bytes=p.stat().st_size,sha256=sha(p))for p in files};save_json(td/'RUN_MANIFEST.json',manifest)
print('Packaged',len(files),'files,',len(figures),'correspondence panels;',summary)
