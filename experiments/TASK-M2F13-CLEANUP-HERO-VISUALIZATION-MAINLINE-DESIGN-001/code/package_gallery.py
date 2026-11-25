"""Publish all source identities, own-output metrics, fixed denominators and relative gallery links."""
import csv,gzip,html,shutil,collections
from common import *
unique=read(B/'ALL_UNIQUE_SOURCES.json');alias=read(B/'ALL_ALIAS_RESULTS.json');rows=unique+alias;assert len(rows)==204 and len(unique)==174 and len(alias)==30
index=read(T/'evidence/VISUALIZATION_INDEX.json');reg=read(P12/'evidence/INPUT_REGISTRY.json');comp={x['group']+'_'+x['video']:x for x in csv.DictReader(open(P12/'COMPARISON.csv'))}
for r in rows:
 r['camera_input_sha256']=hashlib.sha256(json.dumps([x['C']for x in r['input_identity']],separators=(',',':')).encode()).hexdigest();r['intrinsics_input_sha256']=hashlib.sha256(json.dumps([x['K']for x in r['input_identity']],separators=(',',':')).encode()).hexdigest()
 r['inference_protocol']='official352x640;common-work-K+.5;translation-mm-to-m;refine1;fast_cost_volumeFalse;FP16-autocast'
 if r.get('representation')=='native_M2F12' or r.get('action')=='REUSE':
  prior=Path(r['native_path']).resolve().parent;r['execution_code_commit']='NOT_CAPTURED_FOR_OLD_HERO; original evaluator full SHA below';r['inference_receipt_path']=str(prior/'INFERENCE_STARTED.json');r['inference_receipt_sha256']=sha(prior/'INFERENCE_STARTED.json');r['inference_started_receipt']=read(prior/'INFERENCE_STARTED.json');r['execution_evaluator_sha256']=r['inference_started_receipt']['code_sha256']
 r['model_sha256']=MODEL_SHA;r['membership_meaning']='original H004 conditional gate, not independent quality PASS'if r['route']=='H004_RAW_BASELINE'else'original V6 supported-package membership; target own qualification separate'
 if r['route']=='H004_RAW_BASELINE':r['execution_code_commit']=read(B/'HERO_RUN_RECEIPT.json')['execution_git_commit']if r['action']=='NEW'else'NOT_CAPTURED_FOR_OLD_HERO; original evaluator full SHA below'
 r['mesh_definition']='native 352x640 original CORE topology'if r.get('representation','').startswith('native')else'original V6 352-to-360 linear depth resize, Polyp mask, triangle axial-Z range <=0.75 mm'
 r['failure']=r.get('failure','')
cols=['source_id','canonical_source_id','canonical','route','case','target_raw_frame','support_raw_frames','combo_id','formal','target_qualified','support_qualified','action','status','failure','membership_meaning','native_path','native_sha256','mesh_path','mesh_sha256','mesh_definition','model_sha256','camera_input_sha256','intrinsics_input_sha256','inference_protocol','execution_evaluator_sha256','inference_receipt_path','inference_receipt_sha256','cameras_sha256','supports_sha256','execution_code_commit','run_state','run_state_sha256','ring_MAE_mm','ring_P95_mm','ring_max_mm','ring_over_5mm_fraction','camera_conditional_CAD_coverage','numeric_valid_depth_fraction','A_to_B_conditional_coverage','A_to_B_conditional_RGB_MAE_255','vertices','faces','input_identity']
with open(T/'SOURCE_MANIFEST.csv','w')as f:
 w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n");w.writeheader()
 for r in rows:
  row={k:r.get(k,'')for k in cols};row.update(target_raw_frame=r['input_identity'][0]['raw_frame'],support_raw_frames=[x['raw_frame']for x in r['input_identity'][1:]],ring_MAE_mm=r['ring']['MAE_mm'],ring_P95_mm=r['ring']['p95_mm'],ring_max_mm=r['ring']['max_mm'],ring_over_5mm_fraction=r['ring']['over_5mm_fraction'],camera_conditional_CAD_coverage=r['ring']['coverage'],numeric_valid_depth_fraction=r['ring']['native_valid_fraction'],A_to_B_conditional_coverage=r['a_to_b']['target_coverage'],A_to_B_conditional_RGB_MAE_255=r['a_to_b']['RGB_MAE_0_255']);w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':'))if isinstance(v,(dict,list))else v for k,v in row.items()})
with gzip.open(T/'evidence/ALL_SOURCE_RECORDS.json.gz','wt')as f:json.dump(rows,f,ensure_ascii=False)
summary=[]
for rr in reg:
 for route in ['H004_RAW_BASELINE','V6']:
  ss=[r for r in unique if r['case']==rr['case']and r['route']==route];orig=[r for r in rows if r['case']==rr['case']and r['route']==route];c=comp[rr['case']];legal=int(c[route+'_legal_target_count']);summary.append(dict(case=rr['case'],route=route,legal_targets=legal,original_legal_support_tuples=c.get(route+'_legal_support_tuples',''),unique_generated_combinations=len(ss),origin_records=len(orig),existing_or_reused=sum(r['action']!='NEW'for r in ss),new_inference=sum(r['action']=='NEW'for r in ss),new_inference_failed=0,renderable_unique=sum(r['renderable']for r in ss),formal_members=sum(r['formal']for r in ss),target_own_qualified=sum(r['target_qualified']for r in ss),failed_or_empty_status=''if ss else c[route+'_failure']or c[route+'_limited_HERO_status']))
with open(T/'VIDEO_SUMMARY.csv','w')as f:w=csv.DictWriter(f,fieldnames=summary[0],lineterminator="\n");w.writeheader();w.writerows(summary)
fail=read(B/'V6_NOT_GENERATED_AND_BINDING_FAILURES.json');save(T/'evidence/V6_NOT_GENERATED.json',fail)
for name in ['HERO_RUN_RECEIPT.json','MODEL_RECEIPT.json','PLANS_FROZEN.json']:
 if name=='PLANS_FROZEN.json':
  with gzip.open(T/'evidence/PLANS_FROZEN.json.gz','wt')as f:json.dump(read(B/name),f)
 else:shutil.copy2(B/name,T/'evidence'/name)
for name in ['hero_all.log','evaluate_sources.log','evaluate_aliases.log','render_all.log','render_supplements.log']:shutil.copy2(B/name,T/'evidence'/name)
# HTML contains own-output metric for every origin. Color ordering matches rendering, per panel.
esc=lambda x:html.escape(str(x));parts=['''<!doctype html><html lang="zh"><meta charset="utf-8"><title>M2F13 全部 HERO</title><style>body{font:15px system-ui;margin:24px;color:#182028}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #ccd;padding:5px;text-align:left}img{max-width:100%;height:auto}section{border-top:3px solid #678;margin-top:36px;padding-top:12px}.warn{background:#fff2cf;padding:12px}summary{cursor:pointer}code{overflow-wrap:anywhere}nav a{display:inline-block;margin:5px}</style><h1>M2F13：固定5组10视频，两线全部生成面源</h1>''']
parts+=['<p>H004：76个原合法Target，7次严格复用、69次新增、0失败。V6：128条已有来源、98个唯一完整输入组合，其中66个原正式面源（Target自身VALIDATED仅14个、52个未通过；三Support均通过）；30条同输入来源保留原输出和自身指标。合计174个唯一组合，204条输出记录，全部可渲染。无新相机求解、ICP、额外缩放、融合或选择性删面。</p>','<p class="warn">“正式”仅表示各原路线自身准入/打包成员，不是共同独立质量通过。V6中Target自身未通过、仅Support通过的情况单独显示。H004的FEATURE_HELD未从建库排除。Ring CAD误差依赖所给相机；A→B的B参与HERO，属于条件性一致性诊断。绝对位姿GT与共同独立端到端有效覆盖均NOT_EVALUABLE。禁止以不同帧均值宣布路线优劣。</p>','<p>各视频/路线原毫米世界分别展示，yaw未经跨视频认证。全范围图不裁面；近景标出视锥外顶点与含裁切三角形数量。V6多个运行坐标规范未相互认证：总览明确警示，另按原运行分开。黑色为真实R5/R10 CAD；透视比例尺仅在观察中心深度精确。RGB为原Target顶点采样色，保留渲染光照。每源图集避免叠加图遮住内部面。32个旧诊断深度本轮按原V6定义转换Mesh；5个M2F12同输入原生Mesh保留独立别名图。所有色标>5mm均显式统计，不能把白色无共同像素当零误差。</p>','<p><a href="SOURCE_MANIFEST.csv">204条完整逐源清单</a> · <a href="VIDEO_SUMMARY.csv">20条视频汇总</a> · <a href="evidence/ALL_SOURCE_RECORDS.json.gz">完整输入/输出/指标JSON</a> · <a href="evidence/V6_NOT_GENERATED.json">既有未生成与中断尝试</a> · <a href="MAINLINE_DESIGN.md">主线设计</a></p><nav>']
for e in index:parts.append(f'<a href="#{esc(e["route"]+e["case"])}">{esc(e["route"]+" / "+e["case"].replace("GP_", ""))}</a>')
parts.append('</nav>')
for e,s in zip(index,summary):
 ss=sorted([r for r in rows if r['case']==e['case']and r['route']==e['route']],key=lambda r:(r['input_identity'][0]['raw_frame'],not r['canonical'],r['source_id']))
 parts.append(f'<section id="{esc(e["route"]+e["case"])}"><h2>{esc(e["route"]+" / "+e["case"])}</h2><p>{esc(json.dumps(s,ensure_ascii=False))}</p>')
 for name in e['images']:parts.append(f'<details {"open" if "ALL_NUMERIC" in name else ""}><summary>{esc(name)}</summary><a href="figures/{esc(name)}"><img loading="lazy" src="figures/{esc(name)}" alt="{esc(name)}"></a></details>')
 for kind in ['gauge_images','near_images']:
  for item in e.get(kind,[]):parts.append(f'<details><summary>{esc(kind+" / "+item["gauge"])}</summary><img loading="lazy" src="figures/{esc(item["image"])}"><p>颜色顺序（turbo从起点到终点）：{esc(", ".join(item["sources"]))}</p></details>')
 parts.append('<p>ALL与FORMAL配色分别按RAW帧、source_id排序后均匀采样turbo；两个子集不共享色号。下表含全部来源，自身指标不以canonical代填。input/原文件路径及哈希见CSV。</p><table><tr><th>source_id / canonical</th><th>真实Target → 3Support</th><th>原成员 / 自身准入 / 动作</th><th>Ring MAE / P95 / max mm；>5mm%</th><th>CAD共同覆盖 / 数值深度率</th><th>条件A→B覆盖 / RGB MAE</th></tr>')
 for r in ss:parts.append('<tr><td><code>'+esc(r['source_id'])+'</code><br>'+esc('unique'if r['canonical']else'alias of '+r['canonical_source_id'])+'</td><td>'+esc(str(r['input_identity'][0]['raw_frame'])+' → '+str([x['raw_frame']for x in r['input_identity'][1:]]))+'</td><td>'+esc(f"{r['formal']} / T={r['target_qualified']}, S={r['support_qualified']} / {r['action']}")+'</td><td>'+esc(f"{r['ring']['MAE_mm']:.3f} / {r['ring']['p95_mm']:.3f} / {r['ring']['max_mm']:.3f}; {100*r['ring']['over_5mm_fraction']:.2f}%")+'</td><td>'+esc(f"{r['ring']['coverage']:.3f} / {r['ring']['native_valid_fraction']:.3f}")+'</td><td>'+esc(f"{r['a_to_b']['target_coverage']:.3f} / {r['a_to_b']['RGB_MAE_0_255']:.3f}")+'</td></tr>')
 parts.append('</table></section>')
parts.append('</html>');(T/'HERO_ALL_VIDEOS_INDEX.html').write_text('\n'.join(parts))
print('PACKAGED',len(rows),'records',len(summary),'video route rows')
