"""Pilot-only evidence composition. Reuses unchanged native cleaning and renderer."""
from pathlib import Path
import argparse,os,json,shutil,time
import numpy as np
from ring_first_3d.v6_raw.full_run import read,atomic_json,table,hash_file
W=Path('/home/liu/ring_first_3d_workspace');WT=Path(__file__).resolve().parents[1];TASK='TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001';T=WT/'experiments'/TASK;O=W/'runs/v6_frontend_photo_pilot_001';B=W/'runs/v6_full_run_001'
def clean(variant):
 from ring_first_3d.v6_raw import route as r
 from ring_first_3d.v6_raw.surface_clean import mapped_input_for_source
 from ring_first_3d.v6_raw.trusted_restore import trusted_subset
 from ring_first_3d.mainline.native.cleaning import classify_native
 r.B=O/'postprocess';r.environment();rows=[]
 assert hash_file(WT/'src/ring_first_3d/mainline/native/cleaning_protocol.json')=='99c00fe52effa2589c21ad93c2f06a3b1c4d9c86c4c0c37b9bf5a2db33495b56'
 for v in read(T/'evidence/PILOT_MANIFEST.json')['videos']:
  case=v['case'];sp=O/variant/'states'/(case+'.json')
  if not sp.exists():continue
  s=read(sp);R=Path(s['run_path']);result=O/variant/'display'/case/'RESULTS.json'
  if s['status']!='DONE' or not result.exists():continue
  for source in read(result):
   if source['status']!='RENDERABLE':continue
   from ring_first_3d.v6_raw.clean_stage import clean_source
   rows.append(clean_source(source,case,R,O/variant/'clean'/case/source['tag'],variant))
 atomic_json(O/variant/'CLEAN_RESULTS.json',rows);table(T/('CLEAN_'+variant+'.csv'),[{k:x[k] for k in ['case','tag','target','target_media_type','target_view_id','raw_faces','trusted_faces','raw_area_mm2']} for x in rows]);return rows

def graphs():
 from ring_first_3d.v6_raw.visualize import plt
 m=read(T/'evidence/PILOT_MANIFEST.json');chosen=['GP_IIa_4.5mm_closed_R10_single_refY_005','GP_Is_7.0mm_closed_R5_single_refY_005']
 for case in chosen:
  fig,axs=plt.subplots(2,1,figsize=(15,7))
  for ax,var in zip(axs,['R1','R2']):
   R=O/var/'HIST'/case;p=R/'COMPONENT.json'
   if not p.exists():ax.text(.1,.5,var+' 尚未获得分量');continue
   c=read(p);pool=read(R/'ORIGINAL_VIEW_POOL.json');xy=np.array([[i if a['media_type']=='video' else i-22,0 if a['media_type']=='video' else 1] for i,a in enumerate(pool)],float)
   for edge in c['graph_edges']:
    i,j=edge['i'],edge['j'];q=xy[[i,j]];ax.plot(q[:,0],q[:,1],color='steelblue' if pool[i]['media_type']==pool[j]['media_type']=='video' else '#bd68ae',alpha=.35,lw=.7)
   for i,a in enumerate(pool):
    ax.scatter(*xy[i],c='green' if i in c['retained_indices'] else 'red',marker='s' if a['media_type']=='photo' else 'o');ax.text(xy[i,0],xy[i,1]+.08,str(a['raw_frame']) if a['media_type']=='video' else '照片'+a['photo_id'],rotation=70,fontsize=7)
   ref=c['original_reference'];ax.set_title(var+f"：原锚 {ref['reference_raw']}；诊断B {ref['diagnostic_raw']}（可用={c['diagnostic_available']}）；保留{len(c['retained_indices'])}/{len(pool)}。红=排除，绿=原锚分量")
   ax.set_ylim(-.4,1.7);ax.set_yticks([0,1],['视频（真实帧号）','照片（无时间边）']);ax.set_xlabel('仅身份布局，线为满足原RANSAC标准的训练匹配边；不是相机位置')
  fig.tight_layout();fig.savefig(T/'figures'/('GRAPH_'+case+'.png'),dpi=110);plt.close(fig)

def single_figures():
 from ring_first_3d.v6_raw import route as r
 from ring_first_3d.v6_raw.surface_clean import mapped_input_for_source
 from ring_first_3d.v6_raw.trusted_restore import render
 r.B=O/'postprocess';r.environment();allrows=[]
 for var in ['R1','R2']:
  if (O/var/'CLEAN_RESULTS.json').exists():allrows+=read(O/var/'CLEAN_RESULTS.json')
 baseline={x['case']:x['state'].get('renderable',0) for x in read(T/'evidence/R0_IDENTITIES.json')['videos']};choices=[]
 for label,predicate in [('恢复视频',lambda x:baseline[x['case']]==0 and x['target_media_type']=='video'),('R10成功对照',lambda x:'Ip_20.0' in x['case'] and x['target_media_type']=='video'),('R5成功对照',lambda x:'Ip_8.8' in x['case'] and x['target_media_type']=='video'),('照片Target',lambda x:x['target_media_type']=='photo')]:
  candidates=[x for x in allrows if predicate(x)]
  if candidates:choices.append((label,candidates[len(candidates)//2]))
 for j,(label,x) in enumerate(choices,1):
  R=O/x['variant']/'HIST'/x['case'];c=next(a for a in read(R/'PLAN_FROZEN.json')['legal'] if a['tag']==x['tag']);c.update(case=x['case'],run=str(R),mesh_sha256=x['raw_mesh_sha256'],native_sha256=x['native_sha256'],role=label)
  info=mapped_input_for_source(c);state=np.load(O/x['variant']/'clean'/x['case']/x['tag']/'FACE_EVIDENCE.npz')['state'];res=dict(states=x['states'],focus=dict(label=label,xyz_mm=np.median(info['V'],axis=0).tolist()))
  display=dict(c)
  if c.get('target_media_type')=='photo':display['raw_target']='照片 '+c['target_view_id'].rsplit(':',1)[-1]+'（无视频帧号）'
  display['raw_support']=[('照片 '+v.rsplit(':',1)[-1]) if ':photo:' in v else v.rsplit(':',1)[-1] for v in c.get('support_view_ids',[])] or c['raw_support']
  render(display,info,state,res,T/'figures'/f'SINGLE_{j}.png');x['figure']='figures/SINGLE_'+str(j)+'.png';x['role']=label
 atomic_json(T/'evidence/SINGLE_SOURCE_FIGURES.json',[x for _,x in choices])

def summarize():
 import html,trimesh
 cohort=read(T/'evidence/PILOT_MANIFEST.json');r0={x['case']:x for x in read(T/'evidence/R0_IDENTITIES.json')['videos']};videos=[];sources=[];photoids=set();common=[];units={}
 for v in cohort['videos']:
  case=v['case']
  for variant in ['R0','R1','R2']:
   sp=O/variant/'states'/(case+'.json')
   state=r0[case]['state'] if variant=='R0' else read(sp) if sp.exists() else {'status':'PENDING'}
   R=Path(state.get('run_path',str(O/variant/'HIST'/case)));p=R/'PLAN_FROZEN.json';plan=read(p) if p.exists() else {};rows=read(state['source_results']) if state.get('source_results') and Path(state['source_results']).exists() else []
   component=read(R/'COMPONENT.json') if (R/'COMPONENT.json').exists() else {};selection=read(R/'INITIALIZATION_SELECTION.json') if (R/'INITIALIZATION_SELECTION.json').exists() else {};cleanrows=read(O/variant/'CLEAN_RESULTS.json') if (O/variant/'CLEAN_RESULTS.json').exists() else [];cc={x['tag']:x for x in cleanrows if x['case']==case}
   units[(case,variant)]=(R,plan,rows);ledger=read(R/'inputs/ledger005.json') if (R/'inputs/ledger005.json').exists() else []
   out=[x for x in rows if x['status']=='RENDERABLE'];vp=[x for x in out if x.get('target_media_type','video')=='video'];pp=[x for x in out if x.get('target_media_type')=='photo']
   for x in pp:photoids.add(x['target_view_id'])
   rec=dict(case=case,group=v['group'],variant=variant,status=state['status'],original_video_targets=r0[case]['original_target_count'],original_video_views=r0[case]['original_target_count']+1,photo_input_views=sum(Path(p['path']).stem.rsplit('_',1)[0]==v['group'] for p in cohort['static_photos']) if variant=='R2' else 0,retained_component_views=len(component.get('retained_indices',[])) if component else None,numeric_cameras=plan.get('numeric_cameras'),q0=plan.get('old_cameras'),q1=plan.get('new_cameras'),selected_initialization=plan.get('selected_version'),legal_video_tuples=sum(x.get('target_media_type','video')=='video' for x in plan.get('legal',[])),legal_photo_tuples=sum(x.get('target_media_type')=='photo' for x in plan.get('legal',[])),actual_native_success=state.get('native_success',0),video_raw=len(vp),photo_raw=len(pp),video_trusted=sum(x.get('target_media_type','video')=='video' and cc.get(x['tag'],{}).get('trusted_faces',0)>0 for x in out) if variant!='R0' and len(cc)==len(out) else None,photo_trusted=sum(x.get('target_media_type')=='photo' and cc.get(x['tag'],{}).get('trusted_faces',0)>0 for x in out) if variant!='R0' and len(cc)==len(out) else None,clean_processed=len(cc),diagnostic_available=component.get('diagnostic_available'),initialization_plans=selection.get('plans'),reason=state.get('reason',''),run_path=str(R))
   videos.append(rec)
   for x in rows:
    c=next(a for a in plan['legal'] if a['tag']==x['tag']);sources.append(dict(case=case,variant=variant,tag=x['tag'],raw_target=c['raw_target'],raw_support=c['raw_support'],target_media_type=c.get('target_media_type','video'),target_view_id=c.get('target_view_id'),target_physical_view_id=ledger[c['reference']].get('physical_view_id',ledger[c['reference']]['RGB_SHA256']),target_RGB_SHA256=ledger[c['reference']]['RGB_SHA256'],target_Mask_SHA256=ledger[c['reference']]['Mask_SHA256'],support_RGB_SHA256=[ledger[i]['RGB_SHA256'] for i in c['sources']],support_Mask_SHA256=[ledger[i]['Mask_SHA256'] for i in c['sources']],model_sha256=plan['model_sha256'],camera_sha256=plan['cameras_sha256'],support_view_ids=c.get('support_view_ids'),support_photos=sum(y is None for y in c['raw_support']),status=x['status'],reason=x.get('reason',''),rule=c['rule_version'],input_sha256=c['input_sha256'],mesh_path=x['mesh_path'],mesh_sha256=x.get('mesh_sha256'),native_path=str(R/'raw'/(x['tag']+'.npz')),native_sha256=hash_file(R/'raw'/(x['tag']+'.npz')) if (R/'raw'/(x['tag']+'.npz')).exists() else None,trusted_faces=cc.get(x['tag'],{}).get('trusted_faces'),raw_area_mm2=cc.get(x['tag'],{}).get('raw_area_mm2')))
  baseR,baseplan,baserows=units[(case,'R0')];baseout={x['raw_target']:x for x in baserows if x['status']=='RENDERABLE'}
  for target,b in baseout.items():
   bp=next(x for x in baseplan['legal'] if x['raw_target']==target);bm=trimesh.load(b['mesh_path'],process=False)
   for variant in ['R1','R2']:
    R,plan,rows=units[(case,variant)];pipeline_status=next(q['status'] for q in videos if q['case']==case and q['variant']==variant);x=next((x for x in rows if x['raw_target']==target),None);cp=next((x for x in plan.get('all_targets',[]) if x['raw_target']==target),None)
    rec=dict(case=case,target=target,variant=variant,R0_tag=b['tag'],R0_support=bp['raw_support'],new_support=cp['raw_support'] if cp else None,new_status=x['status'] if x else 'NO_OUTPUT_FINAL' if pipeline_status=='DONE' or pipeline_status.endswith('_FAILED') else 'PENDING',pipeline_status=pipeline_status,missing_reason=(cp.get('failure_reason',cp.get('reason','')) if cp else 'NO_PLAN_OR_OUTSIDE_COMPONENT') if not x else '',support_changed=cp['raw_support']!=bp['raw_support'] if cp else None,R0_area_mm2=float(bm.area),new_area_mm2=None,area_ratio=None,relative_footprint_change_warning=None,not_accuracy=True)
    if x and x['status']=='RENDERABLE':
     mm=trimesh.load(x['mesh_path'],process=False);ratio=float(mm.area/bm.area);rec.update(new_area_mm2=float(mm.area),area_ratio=ratio,relative_footprint_change_warning=ratio<.5 or ratio>2,R0_z_range_mm=np.quantile(bm.vertices[:,2],[.05,.5,.95]).tolist(),new_z_range_mm=np.quantile(mm.vertices[:,2],[.05,.5,.95]).tolist())
    common.append(rec)
 table(T/'VIDEO_COMPARISON.csv',videos);table(T/'SOURCE_MANIFEST.csv',sources);table(T/'COMMON_105_TARGETS.csv',common);atomic_json(T/'evidence/VIDEO_COMPARISON.json',videos)
 summary={}
 for var in ['R0','R1','R2']:
  vv=[r for r in videos if r['variant']==var];ss=[r for r in sources if r['variant']==var];summary[var]=dict(videos=12,groups=6,completed=sum(r['status']=='DONE' or r['status'].endswith('_FAILED') for r in vv),videos_with_video_raw=sum(r['video_raw']>0 for r in vv),groups_with_video_raw=len({r['group'] for r in vv if r['video_raw']>0}),video_raw=sum(r['video_raw'] for r in vv),photo_registration_raw=sum(r['photo_raw'] for r in vv),physical_photo_targets=len({r['target_physical_view_id'] for r in ss if r['target_media_type']=='photo' and r['status']=='RENDERABLE'}),video_trusted=sum(r['video_trusted'] or 0 for r in vv) if var!='R0' else None,photo_trusted=sum(r['photo_trusted'] or 0 for r in vv) if var!='R0' else None,original_video_target_denominator=sum(r['original_video_targets'] for r in vv),clean_processed=sum(r['clean_processed'] for r in vv))
  done_clean=var!='R0' and all((r['status']=='DONE' or r['status'].endswith('_FAILED')) and r['clean_processed']==r['video_raw']+r['photo_raw'] for r in vv)
  summary[var].update(clean_complete=done_clean,clean_unprocessed_raw=sum(r['video_raw']+r['photo_raw']-r['clean_processed'] for r in vv),video_trusted_evaluated_nonempty=sum(r['target_media_type']=='video' and r.get('trusted_faces') is not None and r['trusted_faces']>0 for r in ss),photo_registration_trusted_evaluated_nonempty=sum(r['target_media_type']=='photo' and r.get('trusted_faces') is not None and r['trusted_faces']>0 for r in ss))
  physical_clean={r['target_physical_view_id'] for r in ss if r['target_media_type']=='photo' and r.get('trusted_faces') is not None and r['trusted_faces']>0}
  summary[var]['physical_photo_trusted_targets_evaluated']=len(physical_clean) if var!='R0' else None
  summary[var]['physical_photo_trusted_targets']=len(physical_clean) if done_clean else None
  summary[var]['photo_registration_trusted']=summary[var].pop('photo_trusted') if done_clean else None
  summary[var].pop('photo_trusted',None)
  if not done_clean:summary[var]['video_trusted']=None
 atomic_json(T/'evidence/SUMMARY.json',summary)
 parts=['<meta charset="utf-8"><style>body{font-family:system-ui;margin:25px;max-width:1900px}td,th{border:1px solid #bbb;padding:6px}img{max-width:100%}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}</style><h1>V6 前端恢复与照片混合小试</h1><p>固定6组12视频18照片；R0 原基线，R1 统一前端修复，R2 同补丁接入照片。非空Raw为输出覆盖，不代表正确率。照片Target另列，不抵消原视频退化。不同视频坐标独立，没有融合、ICP、缩放或形变。</p><p><a href="TECHNICAL_REPORT.md">技术报告</a> · <a href="VIDEO_COMPARISON.csv">逐视频链条</a> · <a href="SOURCE_MANIFEST.csv">全部源身份</a> · <a href="COMMON_105_TARGETS.csv">原105个Target回归</a></p><pre>'+html.escape(json.dumps(summary,ensure_ascii=False,indent=2))+'</pre>']
 # Chinese headline table; machine-readable complete counts remain downloadable.
 parts[0]=parts[0][:parts[0].index('<pre>')]
 parts.append('<p><a href="evidence/SUMMARY.json">完整计数JSON</a> · <a href="VIEW_MANIFEST.csv">逐视图相机与准入</a> · <a href="PHOTO_MATCH_DIAGNOSTICS.csv">照片匹配原因</a> · <a href="INITIALIZATION_COMPARISON.csv">初始化比较</a></p><table><tr><th>路线</th><th>完成视频</th><th>视频有Raw</th><th>视频Target Raw / 252</th><th>照片Raw注册 / 独立照片</th><th>视频Trusted</th><th>照片Trusted注册 / 独立照片</th></tr>')
 display=lambda x:'未评估完成' if x is None else str(x)
 for var,q in summary.items():parts.append(f'<tr><td>{var}</td><td>{q["completed"]}/12</td><td>{q["videos_with_video_raw"]}/12</td><td>{q["video_raw"]}/252</td><td>{q["photo_registration_raw"]} / {q["physical_photo_targets"]}张（18张照片分母）</td><td>{display(q["video_trusted"])}</td><td>{display(q["photo_registration_trusted"])} / {display(q["physical_photo_trusted_targets"])}</td></tr>')
 parts.append('</table><p>Trusted尚未处理完时显示未评估，不计作0；照片注册次数和独立物理照片数分开。R0 Trusted未在本轮全量重评。</p>')
 regressions=[x for x in common if x['variant']=='R2' and x['new_status']=='NO_OUTPUT_FINAL']
 if regressions:parts.append('<p style="color:#a00;font-weight:bold">回归警示：R2已丢失原成功对照中的'+str(len(regressions))+'个Target；不能用新增照片抵消。当前R2不满足全量推广条件。原因见技术报告及固定相机只读诊断。</p>')
 parts.append('<p>共同原Target已出面：'+ '；'.join(v+' '+str(sum(x['variant']==v and x['new_status']=='RENDERABLE' for x in common))+'/105' for v in ['R1','R2'])+'。不同视频/路线坐标未经跨视频认证，不叠加比较；每栏全部面源保留，近景出画数量已标注。</p>')
 for v in cohort['videos']:
  case=v['case'];parts.append('<h2>'+case+'</h2><div class="grid">')
  for var in ['R0','R1','R2']:
   row=next(x for x in videos if x['case']==case and x['variant']==var);parts.append('<section><h3>'+var+'</h3><p>'+html.escape(str({k:row[k] for k in ['status','video_raw','photo_raw','video_trusted','photo_trusted','selected_initialization']}))+'</p>')
   root=B if var=='R0' else O/var;p=root/'figures'/('HIST__'+case+'__近景逐源.png');dest=T/'figures'/(var+'_'+case+'.png')
   if p.exists() and row['status']=='DONE':
    if not dest.exists() or hash_file(dest)!=hash_file(p):shutil.copyfile(p,dest)
    parts.append('<img loading="lazy" src="figures/'+dest.name+'">')
   else:parts.append('<p>无可展示面源／运行未完成。原因与完整分母保留在表中。</p>')
   parts.append('</section>')
  parts.append('</div>')
 for p in sorted((T/'figures').glob('RING*.png'))+sorted((T/'figures').glob('PHOTO*.png'))+sorted((T/'figures').glob('GRAPH*.png'))+sorted((T/'figures').glob('SINGLE*.png')):parts.append('<h2>'+p.stem+'</h2><img loading="lazy" src="figures/'+p.name+'">')
 (T/'index.html').write_text(''.join(parts));(O/'index.html').write_text('<meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report/index.html"><a href="report/index.html">小试报告</a>')
 print(summary,flush=True)

def metrics(variant):
 import tempfile,cv2,trimesh
 from ring_first_3d.v6_raw import route as r
 from ring_first_3d.v6_raw.evaluate import scorer,depth_diagnostic
 r.B=O/'postprocess';r.environment();old,ring_only=scorer();allrows=[];allpairs=[]
 for v in read(T/'evidence/PILOT_MANIFEST.json')['videos']:
  case=v['case'];root=B if variant=='R0' else O/variant;sp=root/'states'/(case+'.json')
  if not sp.exists():continue
  st=read(sp)
  if st['status']!='DONE' or not st.get('renderable'):
   original=read(B/'states'/(case+'.json'));br=Path(original['run_path']);bp=read(br/'PLAN_FROZEN.json') if (br/'PLAN_FROZEN.json').exists() else {};bt=sorted(c['raw_target'] for c in bp.get('legal',[]))
   for a,b in zip(bt,bt[1:]+bt[:1]):
    if a!=b:allpairs.append(dict(case=case,variant=variant,A_raw=a,B_raw=b,A_identity=a,B_identity=b,pair_identity='R0_FIXED_TARGET_PAIR',independent_test=False,status='NOT_EVALUABLE_MISSING_OUTPUT',pipeline_status=st['status'],MAE_mm=None,P95_absolute_mm=None))
   continue
  R=Path(st['run_path']);dest=O/'metrics'/variant/case;dest.mkdir(parents=True,exist_ok=True)
  if (dest/'COMPLETE.json').exists() and read(dest/'COMPLETE.json').get('postprocess_sha256')==hash_file(__file__):allrows+=read(dest/'SOURCES.json');allpairs+=read(dest/'PAIRS.json');continue
  plan=read(R/'PLAN_FROZEN.json');rows=[];loaded={};ns=None
  with tempfile.TemporaryDirectory(dir=dest) as temp:
   for c in plan['legal']:
    mesh=R/'meshes'/(c['tag']+'_Polyp.ply');native=R/'raw'/(c['tag']+'.npz')
    if not mesh.exists():continue
    row=dict(case=case,route='V6',plan=c,v6_root=str(R),ring_inner_mm=5 if '_R5_' in case else 10);fs=old.frames(row);z=np.load(native);C=fs[0]['c2w_mm'];np.savez_compressed(Path(temp)/'HERO_native.npz',depth_mm=z['depth_mm'],K_index_native=z['K_index_native'],reference_pose_mm=C)
    rm,d,heat,ns=ring_only(row,fs,Path(temp));rm.update(max_mm=float(d.max()) if len(d) else None,over5_count=int((d>5).sum()),over5_fraction=float((d>5).mean()) if len(d) else None)
    m=trimesh.load(mesh,process=False);rows.append(dict(case=case,variant=variant,tag=c['tag'],target=c['raw_target'],target_view_id=c.get('target_view_id'),target_media_type=c.get('target_media_type','video'),mesh_sha256=hash_file(mesh),area_mm2=float(m.area),**rm))
    loaded[c['tag']]=dict(V=np.asarray(m.vertices),F=np.asarray(m.faces),color=np.asarray(m.visual.vertex_colors)[:,:3]/255,depth=cv2.resize(z['depth_mm'].astype(float),(640,360),interpolation=cv2.INTER_LINEAR),labels=fs[0]['labels'],K=fs[0]['K'],C=C,plan=c)
  # Fixed directed neighbouring Target identities, not nearest by result quality.
  # For original success videos all variants use the exact R0 pair list.
  baseline=read(B/'states'/(case+'.json'));BR=Path(baseline['run_path']);bp=read(BR/'PLAN_FROZEN.json') if (BR/'PLAN_FROZEN.json').exists() else {};base_targets=sorted(c['raw_target'] for c in bp.get('legal',[]))
  targets=base_targets if base_targets else sorted(c['raw_target'] for c in plan['legal'] if c['raw_target'] is not None)
  by={d['plan']['raw_target']:d for d in loaded.values() if d['plan']['raw_target'] is not None};pairs=[]
  comparisons=list(zip(targets,targets[1:]+targets[:1]));anchor=min(by) if by else None
  if (R/'inputs/REFERENCE_RECEIPT.json').exists():
   ref=read(R/'inputs/REFERENCE_RECEIPT.json')['reference_index'];anchor_raw=read(R/'inputs/ledger005.json')[ref]['raw_frame'];anchor=anchor_raw if anchor_raw in by else anchor
  for tag,d in loaded.items():
   if d['plan'].get('target_media_type')=='photo':
    by[tag]=d
    if anchor is not None:comparisons.extend([(tag,anchor),(anchor,tag)])
  for a,b in comparisons:
   if a==b:continue
   rec=dict(case=case,variant=variant,A_raw=a if isinstance(a,int) else None,B_raw=b if isinstance(b,int) else None,A_identity=a,B_identity=b,pair_identity='PHOTO_TO_ANCHOR_CONDITIONAL' if isinstance(a,str) or isinstance(b,str) else 'R0_FIXED_TARGET_PAIR' if base_targets else 'NEW_VIDEO_TARGET_IDENTITY_ORDER',independent_test=False)
   if a not in by or b not in by:rec.update(status='NOT_EVALUABLE_MISSING_OUTPUT',MAE_mm=None,P95_absolute_mm=None);pairs.append(rec);continue
   A,D=by[a],by[b];pred=ns['render'](A['V'],A['F'],A['color'],D['K'],D['C'],np.eye(4),'R5' if '_R5_' in case else 'R10');rec.update(depth_diagnostic(pred['z_mm'],D['depth'],pred['valid']&(D['labels']==1)),B_is_HERO_support=D['plan']['reference'] in A['plan']['sources'],conditional_diagnostic=True);pairs.append(rec)
  atomic_json(dest/'SOURCES.json',rows);atomic_json(dest/'PAIRS.json',pairs);atomic_json(dest/'COMPLETE.json',dict(plan_sha256=hash_file(R/'PLAN_FROZEN.json'),postprocess_sha256=hash_file(__file__),original_scorer_sha256=hash_file(Path(old.__file__)),evaluation_adapter_sha256=hash_file(WT/'src/ring_first_3d/v6_raw/evaluate.py'),pair_rule='fixed R0 raw target cyclic adjacent list; new-only videos identity order; no quality selection',post_output_only=True));allrows+=rows;allpairs+=pairs;print('METRICS',variant,case,len(rows),flush=True)
 table(T/('METRICS_'+variant+'.csv'),allrows);table(T/('PAIRS_'+variant+'.csv'),allpairs)

def views():
 rows=[]
 for v in read(T/'evidence/PILOT_MANIFEST.json')['videos']:
  case=v['case']
  for variant in ['R0','R1','R2']:
   root=B if variant=='R0' else O/variant;sp=root/'states'/(case+'.json')
   if not sp.exists():continue
   state=read(sp);R=Path(state['run_path']);meta=R/'inputs/INPUT_IDENTITY.json'
   if not meta.exists():continue
   full=read(R/'ORIGINAL_VIEW_POOL.json') if (R/'ORIGINAL_VIEW_POOL.json').exists() else read(meta)['frames'];local=read(meta)['frames'];index={a['id']:i for i,a in enumerate(local)};gates=read(R/'metrics/GATES.json') if (R/'metrics/GATES.json').exists() else [];plan=read(R/'PLAN_FROZEN.json') if (R/'PLAN_FROZEN.json').exists() else {};selection=read(R/'predictions/local005_primary.json') if (R/'predictions/local005_primary.json').exists() else {};primary=selection.get('primary_version');camera=R/f'predictions/local005_camera_{primary}.npz';C=np.load(camera)['c2w'] if camera.exists() else None;component=read(R/'COMPONENT.json') if (R/'COMPONENT.json').exists() else {};retained=set(component.get('retained_indices',range(len(full))))
   for oi,a in enumerate(full):
    i=index.get(a['id']) if oi in retained else None;g=gates[i] if i is not None and i<len(gates) else {};media=a.get('media_type','video');identity=a.get('view_id',case+':raw:'+str(a['raw_frame']));isB=component.get('original_reference',{}).get('diagnostic_view_id')==identity
    rows.append(dict(case=case,variant=variant,original_pool_index=oi,view_id=identity,physical_view_id=a.get('physical_view_id',a['RGB_SHA256']),media_type=media,raw_frame=a['raw_frame'],photo_id=a.get('photo_id'),source_path=a.get('source_path',read(meta)['raw_path']),source_sha256=a.get('source_sha256',read(meta)['raw_sha256']),RGB_SHA256=a['RGB_SHA256'],Mask_SHA256=a['Mask_SHA256'],K=a['K'],original_to_work=a.get('original_to_work'),coordinate_system=case,original_diagnostic=isB,retained_component=oi in retained,local_camera_index=i,numeric_camera=bool(C is not None and i is not None and np.isfinite(C[i]).all()),camera_c2w_mm=C[i].tolist() if C is not None and i is not None else None,camera_sha256=hash_file(camera) if camera.exists() else None,initialization=primary,q0=g.get('old_pass'),q1=g.get('new_pass'),held_observations=g.get('metrics',{}).get('held_observations'),held_RGB_MAE_px=g.get('metrics',{}).get('held_reprojection',{}).get('MAE'),held_RGB_P95_px=g.get('metrics',{}).get('held_reprojection',{}).get('p95'),held_positive_fraction=g.get('metrics',{}).get('held_positive_fraction'),Ring_MAE_px=g.get('metrics',{}).get('ring_held_self_contour_px',{}).get('MAE'),Ring_P95_px=g.get('metrics',{}).get('ring_held_self_contour_px',{}).get('p95'),gate_reasons=g.get('reasons'),support_use=sum(i in c['sources'] for c in plan.get('legal',[])) if i is not None else 0,legal_target=any(i==c['reference'] for c in plan.get('legal',[])) if i is not None else False,excluded_reason='NOT_IN_ORIGINAL_ANCHOR_COMPONENT' if oi not in retained else 'ORIGINAL_DIAGNOSTIC_B' if isB else '',intrinsics_basis=a.get('intrinsics_basis','FIXED_VIDEO_K'),independent_calibration=a.get('independent_calibration_available',False)))
 table(T/'VIEW_MANIFEST.csv',rows);atomic_json(T/'evidence/VIEW_MANIFEST.json',rows)

def photo_diagnostics():
 from ring_first_3d.v6_raw.visualize import plt
 import cv2
 rows=[]
 for R in sorted((O/'R2/HIST').glob('*')):
  if not (R/'ORIGINAL_VIEW_POOL.json').exists():continue
  pool=read(R/'ORIGINAL_VIEW_POOL.json');comp=read(R/'COMPONENT.json');trpath=R/'observations/FULL_tracks005.npz';ppath=R/'observations/FULL_pairs005.npz'
  if not trpath.exists():continue
  tr=np.load(trpath);pairs=np.load(ppath);accepted={tuple(sorted((e['i'],e['j']))) for e in comp['graph_edges']};metric=read(R/'metrics/track005.json');per=metric['per_frame']
  for i,a in enumerate(pool):
   if a['media_type']!='photo':continue
   candidate_counts=[]
   for k,(u,v) in enumerate(pairs['ij']):
    if i not in [u,v]:continue
    row=pairs['pair'+str(k)];n=int((~tr['held'][row[:,0].astype(int)]).sum()) if len(row) else 0;candidate_counts.append(dict(other=int(v if u==i else u),training_correspondences=n,accepted_edge=tuple(sorted((int(u),int(v)))) in accepted))
   rows.append(dict(case=R.name,photo_id=a['photo_id'],view_id=a['view_id'],features=per[i]['features'],mixed_union_observations=per[i]['track_observations'],identity_preserved_observations=int(np.isfinite(tr['xy'][:,i,0]).sum()),retained_component=i in comp['retained_indices'],max_training_pair=max([x['training_correspondences'] for x in candidate_counts],default=0),accepted_graph_edges=sum(x['accepted_edge'] for x in candidate_counts),pairs=candidate_counts,reason='IN_ANCHOR_COMPONENT' if i in comp['retained_indices'] else 'NO_TRAINING_PAIR_REACHES_12' if max([x['training_correspondences'] for x in candidate_counts],default=0)<12 else 'NO_ACCEPTED_GEOMETRIC_PATH_TO_ORIGINAL_ANCHOR'))
 table(T/'PHOTO_MATCH_DIAGNOSTICS.csv',rows)
 group='GP_IIa_9.5mm_closed_R10_single_refY';fig,axs=plt.subplots(2,3,figsize=(14,6))
 for col,p in enumerate(sorted((O/'photo_prepared').glob(group+'_*'))):
  if col>=3:break
  a=read(p/'PREPARED.json');axs[0,col].imshow(cv2.cvtColor(cv2.imread(a['RGB_path']),cv2.COLOR_BGR2RGB));axs[1,col].imshow(cv2.imread(a['Mask_path'],0),vmin=0,vmax=2,cmap='viridis');d=next(x for x in rows if x['case']==group+'_004' and x['photo_id']==a['photo_id']);axs[0,col].set_title('照片'+a['photo_id']+'，真实RGB');axs[1,col].set_title(f"独立INIT Mask；SIFT特征{d['features']}\n最大训练配对{d['max_training_pair']}；通过几何边{d['accepted_graph_edges']}")
 for ax in axs.flat:ax.axis('off')
 fig.suptitle('IIa9.5/R10 静态照片独立输入：原1920×1080→工作640×360；共同K依据采集设置确认，非独立标定\n照片无视频时间戳；图中的003未进入原锚分量。没有借用视频姿态。',fontsize=10);fig.tight_layout(rect=(0,0,1,.89));fig.savefig(T/'figures/PHOTO_INPUTS.png',dpi=110);plt.close(fig)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['clean','graphs','single','summary','metrics','views','photos']);ap.add_argument('--variant',choices=['R0','R1','R2']);a=ap.parse_args()
 if a.stage=='clean':clean(a.variant)
 elif a.stage=='graphs':graphs()
 elif a.stage=='single':single_figures()
 elif a.stage=='metrics':metrics(a.variant)
 elif a.stage=='views':views()
 elif a.stage=='photos':photo_diagnostics()
 else:summarize()
if __name__=='__main__':main()
