"""Restore the historical 018 TRUSTED-only export on frozen NEW V6 surfaces.

Classification and gap rules are reused intact. No C1 or OBS_TRUSTED filtering.
"""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,subprocess,time,types
import numpy as np
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[3]
TASK='TASK-V6-RESTORE-TRUSTED-ONLY-CLEAN-001';T=WT/'experiments'/TASK
B=W/'runs/v6_full_run_001';O=W/'runs/v6_trusted_clean_restore_001'
LABELS=['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN']
COLORS=np.array([[.12,.75,.23],[1.,.79,.03],[.94,.08,.10],[.60,.60,.60]])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def save(p,x):
 from .route import clean
 from .full_run import atomic_json
 atomic_json(p,clean(x))
def table(p,rows):
 from .full_run import table as write
 write(p,rows)

def trusted_subset(V,F,state):
 state=np.asarray(state)
 if len(state)!=len(F) or not np.isin(state,[0,1,2,3]).all():raise ValueError('FACE_STATE_CONTRACT')
 ids=np.flatnonzero(state==0)
 return dict(V=V,F=F[ids],original_vertex_id=np.arange(len(V)),original_face_id=ids,excluded_original_face_id=np.flatnonzero(state!=0))

def progress_snapshot(label):
 manifest=read(read(B/'SNAPSHOT.json')['config']);m=read(manifest['manifest']);rows=[];failures=[]
 for entry in m['videos']:
  p=B/'states'/(entry['case']+'.json');r=read(p) if p.exists() else dict(case=entry['case'],group=entry['group'],status='PENDING',origin='',renderable=0,native_success=0)
  rows.append(r)
  if 'FAILED' in r['status']:
   R=Path(r['run_path']);path=R/'metrics/local005_solver.json';log=B/'logs'/(r['case']+'__'+r['current_stage']+'.log')
   failures.append(dict(case=r['case'],stage=r['current_stage'],reason=r.get('reason'),solver=read(path) if path.exists() else None,log=str(log),log_tail=log.read_text().splitlines()[-12:] if log.exists() else []))
 completed=[r for r in rows if r['status']=='DONE'];outputs=[r for r in rows if r.get('renderable',0)>0];running=[r for r in rows if r['status'].endswith('RUNNING') or r['status']=='RENDERING'];pending=[r for r in rows if r['status']=='PENDING'];groups={r['group'] for r in outputs}
 launch=read(B/'LAUNCH.json');pid=launch['pid'];alive=Path(f'/proc/{pid}').exists();logs=list((B/'logs').glob('*.log'));latest_log=max(logs,key=lambda p:p.stat().st_mtime);artifacts=list((B/'HIST').glob('*/raw/*.npz'))+list((B/'HIST').glob('*/RUN_STATE.json'))+list((B/'prepared').glob('*/PREPARED.json'));latest_art=max(artifacts,key=lambda p:p.stat().st_mtime)
 at=lambda p:datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat()
 x=dict(checked_beijing=now(),phase_value=True,queue_status=read(B/'PROGRESS.json')['status'],groups_total=len(m['groups']),videos_total=len(rows),normal_completed_with_output=sum(r.get('renderable',0)>0 for r in completed),normal_completed_without_output=sum(not r.get('renderable',0)>0 for r in completed),failed=len(failures),running=len(running),pending=len(pending),other=len(rows)-len(completed)-len(failures)-len(running)-len(pending),videos_with_nonempty_hero=len(outputs),groups_with_nonempty_hero=len(groups),single_source_surfaces=sum(r.get('renderable',0) for r in rows),native_success=sum(r.get('native_success',0) for r in rows),phase_video_output_coverage=len(outputs)/len(rows),phase_group_output_coverage=len(groups)/len(m['groups']),active=running,latest_log=dict(path=str(latest_log),modified_beijing=at(latest_log),tail=latest_log.read_text().splitlines()[-5:]),latest_artifact=dict(path=str(latest_art),modified_beijing=at(latest_art)),runner_pid=pid,runner_alive=alive,execution_snapshot=read(B/'SNAPSHOT.json'),failures=failures,manifest_path=manifest['manifest'],manifest_sha256=sha(manifest['manifest']),counting='output coverage, not correctness; completion includes legal zero; no unreferenced vertices counted as surfaces')
 x['phase_value']=x['queue_status'] not in ['COMPLETE','COMPLETE_WITH_FAILURES'];save(T/'evidence'/('PROGRESS_'+label+'.json'),x);table(T/'evidence'/('VIDEOS_'+label+'.csv'),rows);return x

def freeze():
 # Selected from existing raw nearviews + raw-only topology; never from class labels.
 choices=[('GP_Ip_12.0mm_closed_R5_single_refY_004',301,'异常延伸','Raw近景可见下方长延伸、离散小片；此Target完整范围21.5×16.9×15.4mm，原拓扑多分量'),('GP_Ip_10.3mm_closed_R5_single_refY_005',579,'孤立小片','Raw近景可见主体下方独立片和边缘细条；选择首个冻结Target观察这些原生分量'),('GP_IIa_22.0mm_closed_R10_single_refY_005',640,'边界敏感','宽浅曲面围绕Ring展开，外缘薄且有分隔；观察可信筛选对宽主面与正常边缘的影响'),('GP_Ip_4.0mm_closed_R10_single_refY_004',68,'较正常对照','Raw中体积紧凑、原面单连通；作为较正常对照，不按预计清理效果选取')]
 records=[];journal=[json.loads(x) for x in (B/'INFERENCE_STARTS.jsonl').read_text().splitlines()]
 for case,target,role,reason in choices:
  state=read(B/'states'/(case+'.json'));assert state['status']=='DONE' and state['origin']=='NEW'
  R=Path(state['run_path']);assert R==B/'HIST'/case;complete=read(R/'HERO_COMPLETE.json');plan=read(R/'PLAN_FROZEN.json');c=next(c for c in plan['legal'] if c['raw_target']==target);tag=c['tag'];rr=next(x for x in read(R/'metrics/MVS005_supported_runs.json') if x['tag']==tag);assert rr['success'];start=next(x for x in journal if x['case']==case and x['tag']==tag);assert start['input_sha256']==c['input_sha256']
  mesh=R/'meshes'/(tag+'_Polyp.ply');depth=R/'raw'/(tag+'.npz');assert sha(mesh)==complete['outputs'][str(mesh)] and sha(depth)==rr['raw_SHA256'];L=read(R/'inputs/ledger005.json');primary=read(R/'predictions/local005_primary.json')['primary_version'];camera=R/f'predictions/local005_camera_{primary}.npz';meta=read(R/'inputs/INPUT_IDENTITY.json');cad=W/'runs/m2f5_unified/cad'/('R5.npz' if meta['ring_inner_mm']==5 else 'R10.npz');frames=[]
  for i in [c['reference']]+c['sources']:
   f=L[i];assert sha(f['RGB_path'])==f['RGB_SHA256'] and sha(f['Mask_path'])==f['Mask_SHA256'];frames.append(f)
  paths=[mesh,depth,camera,cad,R/'config.json',R/'PLAN_FROZEN.json',R/'HERO_COMPLETE.json',R/'CAMERA_COMPLETE.json',R/'inputs/INPUT_IDENTITY.json',R/'inputs/ledger005.json',R/'inputs'/('TUPLE_'+tag+'.json')]+[Path(f[k]) for f in frames for k in ['RGB_path','Mask_path']]
  records.append(dict(case=case,group=state['group'],video=case.rsplit('_',1)[1],raw_target=target,raw_support=c['raw_support'],tag=tag,role=role,selection_reason=reason,run=str(R),mesh_sha256=sha(mesh),native_sha256=sha(depth),camera_path=str(camera),cad_path=str(cad),input_sha256=c['input_sha256'],model_sha256=plan['model_sha256'],raw_path=meta['raw_path'],raw_video_sha256=meta['raw_sha256'],frames=frames,new_inference_start=start,hero_execution_commit=complete['execution_commit'],camera_execution_commit=read(R/'CAMERA_COMPLETE.json')['execution_commit'],artifacts={str(p):sha(p) for p in paths},selection_images=dict(path=state['figure'],sha256=sha(B/state['figure'])),old_labels_used=False))
 path=T/'config/SOURCES_FROZEN.json';assert not path.exists(),'SAMPLES_ALREADY_FROZEN';save(path,dict(frozen_beijing=now(),before_classification=True,cases=records,classifier=str(WT/'src/ring_first_3d/mainline/native/cleaning.py'),classifier_sha256=sha(WT/'src/ring_first_3d/mainline/native/cleaning.py'),kernel_sha256=sha(WT/'src/ring_first_3d/mainline/native/_clean_kernels.py'),protocol_sha256=sha(WT/'src/ring_first_3d/mainline/native/cleaning_protocol.json'),export_rule='state==0',C1_used=False,OBS_TRUSTED_used=False));return records

def component_ids(F):
 from ..mainline.native import _clean_kernels
 from scipy.sparse import coo_matrix
 from scipy.sparse.csgraph import connected_components
 f=_clean_kernels.face_components
 return types.FunctionType(f.__code__,dict(np=np,coo_matrix=coo_matrix,connected_components=connected_components),f.__name__,f.__defaults__)(F)

def stats(V,F,areas=None):
 from .surface_clean import components_and_boundary
 x=components_and_boundary(V,F);ids=component_ids(F)
 if areas is None:areas=np.linalg.norm(np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]),axis=1)/2
 ca=np.bincount(ids,weights=areas) if len(ids) else np.array([]);x.update(face_edge_components=len(ca),largest_component_areas_mm2=sorted(ca.tolist(),reverse=True)[:5],referenced_vertices=len(np.unique(F)),unreferenced_vertices=len(V)-len(np.unique(F)));return x

def project_view(X,bounds,cad,elev,azim):
 allv=np.r_[bounds,cad['V']];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();e,a=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)]);forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);pc=(X-pos)@np.array([right,down,forward]).T;return pc[:2]/pc[2]*490+199.5

def render(c,info,state,result,path):
 from .visualize import plt,draw
 from matplotlib.patches import Patch
 V,F,cad=info['V'],info['F'],info['cad'];bounds=np.r_[V,cad['V']];color=np.asarray(info['m'].visual.vertex_colors)[:,:3]/255.;rgb=color[F].mean(1);trust=state==0
 fig,axs=plt.subplots(2,3,figsize=(14,9))
 for row,(e,a) in zip(axs,[(20,60),(0,90)]):
  for ax,ff,cols,title in zip(row,[F,F,F[trust]],[rgb,COLORS[state],rgb[trust]],['原始 Raw（原RGB）','原面四态标注','历史 TRUSTED-only 实际子集']):
   if len(ff):draw(ax,V,ff,cols,cad,bounds,e,a)
   else:
    # CAD-only scene: never show excluded Raw geometry as an empty subset.
    draw(ax,cad['V'],cad['F'],np.full((len(cad['F']),3),.035),cad,bounds,e,a);ax.text(.5,.5,'可信子集为空',transform=ax.transAxes,ha='center')
   ax.set_title(title)
  focus=result['focus'];q=project_view(np.array(focus['xyz_mm']),bounds,cad,e,a)
  for ax in row[:2]:ax.annotate(focus['label'],xy=q,xytext=(10,26),fontsize=8,color='#205070',bbox=dict(facecolor='white',alpha=.9),arrowprops=dict(arrowstyle='->',color='#205070'))
 legend=[Patch(facecolor=COLORS[i],label=label) for i,label in [(0,'可信 TRUSTED'),(1,'待定 UNCERTAIN'),(3,'未知 UNKNOWN'),(2,'拒绝 REJECTED')]]
 fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.5,.065),ncol=4,fontsize=10)
 fig.suptitle(c['case']+f"\nTarget RAW {c['raw_target']} / Support {c['raw_support']} · {c['role']}\n仅保留 TRUSTED；UNKNOWN 与 UNCERTAIN 同时排除（REJECTED亦排除）\n同源、同视角、同Raw完整毫米范围；黑色Ring CAD；没有修改坐标、重网格或补洞",fontsize=11)
 q=result['states'];text='；'.join(f"{LABELS[i]} {q[i]['faces']}面 / {q[i]['area_mm2']:.3f}mm²" for i in [0,1,3,2]);fig.text(.5,.045,text,ha='center',fontsize=9);fig.text(.5,.018,'排除未知/待定表示本轮不使用这些面，不等于证明错误。正常边界、薄结构可能同步减少，需人工判断。',ha='center',fontsize=9)
 fig.tight_layout(rect=(0,.11,1,.87));fig.savefig(path,dpi=130);plt.close(fig)


def run():
 from . import route as r
 from .surface_clean import mapped_input_for_source
 from ..mainline.native.cleaning import classify_native
 import trimesh
 r.B=O;r.environment();O.mkdir(exist_ok=True);sources=read(T/'config/SOURCES_FROZEN.json');assert sources['protocol_sha256']==sha(WT/'src/ring_first_3d/mainline/native/cleaning_protocol.json');assert sources['classifier_sha256']==sha(WT/'src/ring_first_3d/mainline/native/cleaning.py');assert sources['kernel_sha256']==sha(WT/'src/ring_first_3d/mainline/native/_clean_kernels.py');rows=[]
 for k,c in enumerate(sources['cases'],1):
  dest=O/f'source{k}';assert not(dest/'COMPLETE.json').exists(),'NO_SILENT_RERUN'
  for p,h in c['artifacts'].items():assert sha(p)==h,'FROZEN_INPUT_DRIFT '+p
  info=mapped_input_for_source(c,dest);V,F=info['V'],info['F'];record=classify_native(dest,c['cad_path'],mapped_input=info['payload']);e=dict(np.load(dest/'FACE_EVIDENCE.npz'));state=e['state'];assert np.array_equal(e['original_face_id'],np.arange(len(F))) and np.array_equal(e['F'],F)
  subset=trusted_subset(V,F,state);np.savez_compressed(dest/'TRUSTED_ONLY.npz',**subset,working_uv=info['uv'],native_pixel_id=info['raw']['native_pixel_id']);np.savez_compressed(dest/'EXCLUDED_FACES.npz',V=V,F=F[state!=0],original_vertex_id=np.arange(len(V)),original_face_id=np.flatnonzero(state!=0),state=state[state!=0],reason_bits=e['reason_bits'][state!=0]);trimesh.Trimesh(V,subset['F'],vertex_colors=np.asarray(info['m'].visual.vertex_colors),process=False).export(dest/'TRUSTED_ONLY.ply')
  area=e['area_mm2'];states=[dict(code=i,label=LABELS[i],faces=int((state==i).sum()),area_mm2=float(area[state==i].sum())) for i in range(4)];cid=component_ids(F);components=[]
  for i in range(int(cid.max())+1 if len(cid) else 0):
   use=cid==i;components.append(dict(component_id=i,faces=int(use.sum()),area_mm2=float(area[use].sum()),centroid_mm=np.average(V[F[use]].mean(1),axis=0,weights=area[use]),states=[dict(code=j,faces=int((use&(state==j)).sum()),area_mm2=float(area[use&(state==j)].sum())) for j in range(4)]))
  components.sort(key=lambda x:x['area_mm2'],reverse=True);boundary=e['boundary_face'];lower=info['uv'][F].mean(1)[:,1]>=np.quantile(info['uv'][F].mean(1)[:,1],.8)
  zones=[]
  for name,sel in [('原面边界邻接面',boundary),('源图像下方20%面中心（位置代理非解剖标签）',lower)]:zones.append(dict(name=name,faces=int(sel.sum()),area_mm2=float(area[sel].sum()),states=[dict(code=j,faces=int((sel&(state==j)).sum()),area_mm2=float(area[sel&(state==j)].sum())) for j in range(4)]))
  if c['role']=='孤立小片':focus=dict(label='原始独立片（非错误真值）',xyz_mm=components[1]['centroid_mm'])
  elif c['role']=='异常延伸':
   centers=V[F].mean(1);distance=np.linalg.norm(centers-np.median(centers,axis=0),axis=1);idx=np.flatnonzero(lower);j=idx[np.argmax(distance[idx])];focus=dict(label='下方延伸/细条关注区',xyz_mm=centers[j])
  else:
   centers=V[F].mean(1);idx=np.flatnonzero(boundary);j=idx[np.argmax(centers[idx,0])];focus=dict(label='原始边缘（可能是真实结构）',xyz_mm=centers[j])
  result=dict(case=c['case'],target=c['raw_target'],supports=c['raw_support'],role=c['role'],input_sha256=c['input_sha256'],raw=stats(V,F,area),states=states,trusted=stats(V,F[state==0],area[state==0]),trusted_plus_uncertain_diagnostic=dict(faces=int(np.isin(state,[0,1]).sum()),area_mm2=float(area[np.isin(state,[0,1])].sum()),not_018_rule=True),excluded_area_mm2=float(area[state!=0].sum()),components=components,zones=zones,focus=focus,native_shape=list(info['z'].shape),working_shape=list(info['labels'].shape),gap=record,filter='state==0',C1_used=False,OBS_TRUSTED_used=False,execution_commit=r.head(),finished_beijing=now(),source_code_sha256=sha(__file__),input_adapter_sha256=sha(WT/'src/ring_first_3d/v6_raw/surface_clean.py'))
  save(dest/'RESULT.json',result);render(c,info,state,result,T/'figures'/f'source{k}.png')
  for p,h in c['artifacts'].items():assert sha(p)==h
  save(dest/'COMPLETE.json',dict(result_sha256=sha(dest/'RESULT.json'),outputs={str(p):sha(p) for p in dest.glob('*') if p.is_file()},original_inputs_unchanged=True));rows.append(result);print('TRUSTED_COMPLETE',k,c['case'],states,flush=True)
 save(T/'evidence/RESULTS.json',rows);table(T/'SURFACE_COUNTS.csv',[dict(case=r['case'],target=r['target'],**s) for r in rows for s in r['states']]);return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['progress','freeze','run']);ap.add_argument('--label',default='INITIAL');a=ap.parse_args()
 if a.action=='progress':print(json.dumps(progress_snapshot(a.label),ensure_ascii=False,default=str))
 elif a.action=='freeze':print(len(freeze()))
 else:run()
if __name__=='__main__':main()
