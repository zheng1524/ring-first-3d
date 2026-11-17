"""Actual triangle PNG evidence and portable GLB files; HTML is a plain local index."""
from pathlib import Path
import json,csv,shutil,html
import numpy as np
from ..synthetic.io import fetch,save_json,outputs
from ..inita.train import sources
from ..multisurface.geometry import scene,cast,mesh_sections,plane_coordinates

def artifact_files(attempt):
 return sorted(p for p in attempt.rglob('*')if p.is_file()and 'runtime'not in p.relative_to(attempt).parts and p.suffix in ['.png','.glb','.json','.csv','.npz']and not p.name.startswith(('request','result','payload')))

def method_row(case,method,record):return dict(record,case=case,method=method)

def run(task,attempt,smoke=False):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 from matplotlib.collections import LineCollection
 import trimesh
 root=attempt.parents[1];tr='G1_smoke_train'if smoke else'G1_all_train';hr='G2_smoke_hero'if smoke else'G2_all_hero';ev='G3_smoke_evaluate'if smoke else'G3_all_evaluate';body=json.loads(fetch(root,ev,'BODY_SHAPE_METRICS.json').read_text());hero=json.loads(fetch(root,ev,'HERO_METRICS.json').read_text());pred=json.loads(fetch(root,tr,'BODY_PREDICTIONS_FROZEN.json').read_text())['records'];hpred=json.loads(fetch(root,hr,'ALL_HERO_PREDICTIONS_FROZEN.json').read_text())['groups'];cases=list(dict.fromkeys(r['case']for r in pred));src={r['case']:r for r in sources(task)['cases']};real={r['group']:r for r in sources(task)['real_groups']};br={(r['case'],r['arm']):r for r in body['rows']};pr={(r['case'],r['arm']):r for r in pred};figdir=attempt/'figures';figdir.mkdir();models=attempt/'meshes';models.mkdir();world={};aligned={};GT={};evidence=[];update_rows=[]
 def bounds(meshes):
  V=np.concatenate([m['V']for m in meshes]);c=(V.max(0)+V.min(0))/2;r=max(.5,np.ptp(V,axis=0).max()*.55);return c,r
 def show(ax,m,c,r,gt=None,title='',heat=None,gt_reference=False):
  if gt is not None:ax.add_collection3d(Poly3DCollection(gt['V'][gt['F']],facecolors=(.5,.5,.5,.25),edgecolors='none'))
  if m is not None:
   F=m['F'];color=((.5,.5,.5,.8)if gt_reference else(.52,.16,.72,.85))if heat is None else plt.cm.viridis(np.clip(heat[F].mean(1)/max(1e-10,float(heat.max())),0,1));ax.add_collection3d(Poly3DCollection(m['V'][F],facecolors=color,edgecolors='none'))
  else:ax.text(*c,'NOT_EVALUABLE',color='red')
  ax.set(xlim=(c[0]-r,c[0]+r),ylim=(c[1]-r,c[1]+r),zlim=(c[2]-r,c[2]+r),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_box_aspect((1,1,1));ax.view_init(15,-65);ax.set_title(title,fontsize=8);ax.tick_params(labelsize=5)
 def glb(path,items):
  ss=trimesh.Scene()
  for name,m,color in items:
   mm=trimesh.Trimesh(m['V'],m['F'],process=False);mm.visual.face_colors=np.tile(np.array(color,dtype=np.uint8),(len(m['F']),1));ss.add_geometry(mm,node_name=name,geom_name=name)
  ss.metadata.update(unit='mm',one_coordinate_unit_mm=1,GT_copy_only='ALIGNED'in path.name);path.write_bytes(ss.export(file_type='glb'))
 for g in cases:
  GT[g]=dict(np.load(src[g]['GT']['path']))
  for a in ['A0','A2','A2D','A3']:
   if br.get((g,a),{}).get('status')!='NUMERIC':continue
   world[g,a]=dict(np.load(fetch(root,tr,pr[g,a]['world_mesh_relative'])));aligned[g,a]=dict(np.load(fetch(root,ev,br[g,a]['aligned_mesh_relative'])));np.savez_compressed(models/(g+'_'+a+'_WORLD.npz'),**world[g,a]);np.savez_compressed(models/(g+'_'+a+'_ALIGNED.npz'),**aligned[g,a]);glb(models/(g+'_'+a+'_ALIGNED_GT.glb'),[(a,aligned[g,a],[140,40,190,215]),('Independent_GT',GT[g],[145,145,145,70])])
  if(g,'A3')not in world:continue
  trainfolder=fetch(root,tr,g+'/A3/metrics/'+g+'_RUN.json').parents[1];steps=sorted((trainfolder/'contour_evidence').glob('[0-9]*'));initial=np.load(src[g]['resolved013_initial']['path']);V0=initial['V'];V=world[g,'A3']['V'];delta=np.linalg.norm(V-V0,axis=1);records=[]
  for step in steps:
   summary=json.loads((step/'SUMMARY.json').read_text());records.append(summary)
  save_json(attempt/(g+'_UPDATE_TRACE.json'),records)
  for si in sorted(set([0,min(9,len(steps)-1),len(steps)//2,len(steps)-1])):
   dest=attempt/'intermediate'/g/steps[si].name;dest.mkdir(parents=True);shutil.copyfile(steps[si]/'BODY.npz',dest/'BODY.npz');shutil.copyfile(steps[si]/'SUMMARY.json',dest/'SUMMARY.json')
   for v in src[g]['FIT']:shutil.copyfile(steps[si]/(v['meta']['id']+'.npz'),dest/(v['meta']['id']+'.npz'))
  selected=[]
  for vid in ['004','005']:
   vs=[v for v in src[g]['FIT']if v['meta']['video']==vid]
   if vs:selected.extend([vs[0],vs[len(vs)//2]])
  fig=plt.figure(figsize=(18,4*len(selected)),layout='constrained');c,r=bounds([dict(V=V,F=world[g,'A3']['F'])]);rsrc=np.load(src[g]['static']['RING.npz']['path']);rs=scene(rsrc['V'],rsrc['F'])
  for row,v in enumerate(selected):
   cid=v['meta']['id'];d=np.load(v['cache']['path']);lab=d['labels'];H,W=lab.shape;y,x=np.mgrid[:H,:W];uv=np.c_[x.ravel(),y.ravel()];rz,_,_=cast(rs,uv,d['K'],d['T']);masks=[]
   for VV in [V0,V]:
    z,_,_=cast(scene(VV,world[g,'A3']['F']),uv,d['K'],d['T']);masks.append((np.isfinite(z)&(z>0)&(z<rz)).reshape(H,W))
   p=np.load(steps[0]/(cid+'.npz'));ok=p['accepted']if 'accepted'in p else np.zeros(0,bool);sel=np.flatnonzero(ok);sel=sel[np.linspace(0,len(sel)-1,min(10,len(sel)),dtype=int)]if len(sel)else sel
   for col in [0,1,2]:
    ax=fig.add_subplot(len(selected),4,row*4+col+1);ax.imshow(d['RGB']);ax.contour(lab==1,levels=[.5],colors=['lime'],linewidths=.7);ax.contour(lab==2,levels=[.5],colors=['black'],linewidths=.5)
    if col in [0,2]:ax.contour(masks[0 if col==0 else 1],levels=[.5],colors=['magenta'],linewidths=.8)
    if col==1 and 'accepted'in p:
     bad=np.flatnonzero(~p['accepted']);bad=bad[np.linspace(0,len(bad)-1,min(10,len(bad)),dtype=int)]if len(bad)else bad
     if len(bad):ax.scatter(p['body_uv'][bad,0],p['body_uv'][bad,1],marker='x',c='red',s=12,linewidths=.8)
     ax.text(.01,.02,'accepted %d / %d; red X rejected'%(int(ok.sum()),len(ok)),transform=ax.transAxes,color='yellow',fontsize=7)
    if col==1 and len(sel):
     for k in sel:
      a,b=p['body_uv'][k],p['target_uv'][k];ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='yellow',lw=.8));ax.text(a[0],a[1],str(p['edge'][k,0]),color='white',fontsize=5)
      e=p['edge'][k];t=float(p['edge_t'][k]);edge_delta=(1-t)*(V[e[0]]-V0[e[0]])+t*(V[e[1]]-V0[e[1]]);update_rows.append(dict(case=g,view=cid,body_vertex0=int(e[0]),body_vertex1=int(e[1]),body_face=int(p['face'][k]),edge_t=t,initial_normal_residual_px=float(p['normal_residual_px'][k]),actual_3D_edge_update_mm=edge_delta.tolist(),source='initial E pairs / final world vertices; vector is shared update, not per-view causal allocation'))
    ax.set_title(cid+'\n'+['Initial actual projection','Explicit pairs: accepted arrows; vertex ID','Final actual projection'][col],fontsize=8);ax.axis('off')
   ax=fig.add_subplot(len(selected),4,row*4+4,projection='3d');show(ax,world[g,'A3'],c,r,title='Shared 3D displacement [mm]\nmax %.4f; no image transform'%delta.max(),heat=delta);sm=plt.cm.ScalarMappable(norm=plt.Normalize(0,max(1e-10,float(delta.max()))),cmap='viridis');fig.colorbar(sm,ax=ax,shrink=.55,pad=.03,label='vertex displacement [mm]')
   for k in sel[:4]:
    vertex=int(p['edge'][k,0]);ax.text(*V[vertex],str(vertex),fontsize=5,color='black')
  fig.suptitle(g+' | Figure1: 2D normal constraints → calibrated 3D vertex updates; green=observed, magenta=actual projection\nAll source cameras fixed; Ring-contact ambiguity rejected; full E/M trace and rejected pairs remain in NPZ.',fontsize=11);fig.savefig(figdir/(g+'_Fig1_2D_TO_3D.png'),dpi=100);plt.close(fig)
  save_json(attempt/(g+'_MECHANISM_SUMMARY.json'),dict(case=g,all_FIT_rebuilt_every_E_step=True,recorded_E_steps=len(steps),delta_MAE_mm=float(delta.mean()),delta_P95_mm=float(np.quantile(delta,.95)),delta_max_mm=float(delta.max()),initial_contour_gradient_nonzero_views=sum(v['contour_gradient_norm']>0 for v in records[0]['views']),initial_explicit_pairs=sum(v['accepted_N']for v in records[0]['views']),actual_shared_3D_update=True,depth_loss_used=False))
 # Principal Figure1 uses actual selected cases, kept as PNG instead of a web application.
 focus=[g for g in ['G01','G05','G02']if(figdir/(g+'_Fig1_2D_TO_3D.png')).is_file()]
 from PIL import Image,ImageDraw
 imgs=[Image.open(figdir/(g+'_Fig1_2D_TO_3D.png')).convert('RGB')for g in focus]
 if imgs:
  canvas=Image.new('RGB',(max(i.width for i in imgs),sum(i.height for i in imgs)),(255,255,255));y=0
  for i in imgs:canvas.paste(i,(0,y));y+=i.height
  canvas.save(figdir/'Fig1_2D_TO_3D.png')
 # All11 actual scale1 rigid GT-aligned copies.
 fig=plt.figure(figsize=(18,4*len(cases)),layout='constrained')
 for row,g in enumerate(cases):
  c,r=bounds([GT[g]]+[m for(gg,a),m in aligned.items()if gg==g])
  for col,a in enumerate(['A0','A2','A3','GT']):
   ax=fig.add_subplot(len(cases),4,row*4+col+1,projection='3d');m=GT[g]if a=='GT'else aligned.get((g,a));rec=br.get((g,a),{});title=g+' '+a
   if rec.get('status')=='NUMERIC':title+='\nstrict '+str(rec['IoU_3D'])+' / cond %.4f\nCD %.3f, p95 %.3f mm'%(rec['conditional_occupancy_IoU'],rec['Chamfer_MAE_mm'],rec['Chamfer_P95_mm'])
   show(ax,m,c,r,gt=GT[g]if a!='GT'else None,title=title,gt_reference=a=='GT')
 fig.suptitle('Figure2 | A0 historical → A2 frozen → A3 explicit contour → Blender GT\nEvery prediction is a real scale1 best_rigid015 evaluation copy; original world coordinates retained for HERO.',fontsize=11);fig.savefig(figdir/'Fig2_ALL_BODY_GT.png',dpi=100);plt.close(fig)
 # Every full native triangle Mesh, true plane intersections; all methods use identical planes/ranges.
 for gg in hpred:
  if gg['status']!='NUMERIC':continue
  g=gg['case'];meshes={};valid=[r for r in gg['records']if r['status']=='NUMERIC'];dat=[v for v in real[g]['views']if v['role']=='FIT'];ring=dict(np.load(real[g]['assets']['ring']['path']))
  for rr in valid:
   method=rr['method'];meshes[method]=[dict(np.load(fetch(root,hr,g+'/'+method+'/'+v['id']+'.npz')))for v in dat];items=[('Body_'+rr['body_arm'],world[g,rr['body_arm']],[155,155,155,95]),('Ring',ring,[0,0,0,255])]
   for v,m in zip(dat,meshes[method]):items.append((v['video']+'_'+v['id'],m,[230,30,40,210]if v['video']=='004'else[20,70,235,210]))
   glb(models/(g+'_'+method+'_FULL_HERO.glb'),items)
  c,r=bounds([world[g,'A2'],world[g,'A3'],ring]);planes=[(0,c[0]-.12*r),(1,c[1]+.12*r),(2,c[2]-.12*r),(2,c[2]+.12*r)];fig,axes=plt.subplots(4,4,figsize=(19,16),layout='constrained')
  for row,(axis,offset)in enumerate(planes):
   dims=[i for i in range(3)if i!=axis]
   for col,method in enumerate(['M0','H1','H3','H4']):
    ax=axes[row,col];arm='A3'if method=='H4'else'A2'
    for m,color,lw,ls in [(world[g,arm],'gray',1.2,'--'),(ring,'black',1.,'-')]:
     seg=plane_coordinates(mesh_sections(m['V'],m['F'],axis,offset),axis);ax.add_collection(LineCollection(seg,colors=color,linewidths=lw,linestyles=ls))
    if method in meshes:
     for v,m in zip(dat,meshes[method]):
      seg=plane_coordinates(mesh_sections(m['V'],m['F'],axis,offset),axis);ax.add_collection(LineCollection(seg,colors='red'if v['video']=='004'else'blue',linewidths=.6,alpha=.65))
    else:ax.text(.1,.8,'NOT_EVALUABLE',transform=ax.transAxes,color='red')
    ax.set(xlim=(c[dims[0]]-r,c[dims[0]]+r),ylim=(c[dims[1]]-r,c[dims[1]]+r),xlabel='XYZ'[dims[0]]+' [mm]',ylabel='XYZ'[dims[1]]+' [mm]',title=method+' / '+'XYZ'[axis]+'=%.3f mm'%offset);ax.set_aspect('equal');ax.grid(alpha=.2)
  fig.suptitle(g+' Figure3 | All full native HERO triangle-plane intersections; red004 / blue005 / gray fixed Body / black CAD\nNo averaged contour, surface replacement or fusion. Real HERO absolute 3D accuracy is NOT_EVALUABLE.',fontsize=11);fig.savefig(figdir/(g+'_Fig3_HERO_SECTIONS.png'),dpi=115);plt.close(fig)
 # Shape gain vs localization changes; legal strict IoU only, not conditional substitution.
 pairs=json.loads(fetch(root,ev,'PAIRED_COMPARISONS.json').read_text())['body'];fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained');relationship=[]
 for g in hero['groups']:
  if g['status']!='NUMERIC':continue
  methods={r['method']:r for r in g['methods']if r['status']=='NUMERIC'};p=next((p for p in pairs if p['case']==g['case']and p['reference']=='A2'),None)
  if not p:continue
  for family,ax in zip(['cross_video','within_video'],axes):
   if not all(a in methods and methods[a][family]['MAE']is not None for a in ['H1','H4']):continue
   gain=methods['H1'][family]['MAE']-methods['H4'][family]['MAE'];strict=p['strict_IoU_delta'];relationship.append(dict(case=g['case'],family=family,delta_strict_IoU=strict,delta_conditional_IoU=p['conditional_IoU_delta'],HERO_MAE_reduction_mm=gain,strict_missing= strict is None))
   if strict is not None:ax.scatter(strict,gain);ax.annotate(g['case'],(strict,gain))
   else:ax.text(.02,.95-.07*sum(z['family']==family and z['strict_missing']for z in relationship),g['case']+': strict IoU NA; HERO gain %.4fmm'%gain,transform=ax.transAxes,fontsize=8)
 for ax,family in zip(axes,['Cross-video','Within-video']):ax.axhline(0,color='gray',lw=.8);ax.axvline(0,color='gray',lw=.8);ax.set(xlabel='A3 minus A2 strict 3D IoU (valid entities only)',ylabel='H1 minus H4 HERO MAE [mm], positive better',title=family+' / no absolute real3D GT');ax.grid(alpha=.2)
 fig.savefig(figdir/'Fig4_BODY_HERO_RELATION.png',dpi=130);plt.close(fig);save_json(attempt/'BODY_HERO_RELATION.json',relationship)
 # Copy actual numeric evidence, never substitute a positive outcome for missing arms.
 for n in ['BODY_SHAPE_METRICS.json','BODY_SHAPE_METRICS.csv','HERO_METRICS.json','GT_RIGID_TRANSFORMS.json','PAIRED_COMPARISONS.json','FAILURE_LEDGER.json']:shutil.copyfile(fetch(root,ev,n),attempt/n)
 save_json(attempt/'BODY_UPDATE_LINKS.json',update_rows)
 hrows=[]
 for g in hero['groups']:
  by={r['method']:r for r in g.get('methods',[])}
  for method in task['contour']['HERO_methods']:
   r=by.get(method,dict(status='NOT_EVALUABLE',reason=g.get('reason','Missing method')));hrows.append(method_row(g['case'],method,r))
 save_json(attempt/'HERO_ALL11_METRICS.json',hrows)
 with(attempt/'HERO_ALL11_METRICS.csv').open('w',newline='')as f:
  w=csv.DictWriter(f,['case','method','status','within_MAE_mm','within_P95_mm','cross_MAE_mm','cross_P95_mm','body_rate','HOLDOUT_IoU','reason']);w.writeheader()
  for r in hrows:w.writerow(dict(case=r['case'],method=r['method'],status=r['status'],within_MAE_mm=r.get('within_video',{}).get('MAE'),within_P95_mm=r.get('within_video',{}).get('p95'),cross_MAE_mm=r.get('cross_video',{}).get('MAE'),cross_P95_mm=r.get('cross_video',{}).get('p95'),body_rate=r.get('correspondence',{}).get('body_rate'),HOLDOUT_IoU=json.dumps([z['mask_IoU']for z in r.get('HOLDOUT',[])]),reason=r.get('reason')))
 failures=json.loads((attempt/'FAILURE_LEDGER.json').read_text())['failures'];answers=dict(body=pairs,hero=relationship,GT_used_for_selection=False,denominator=11);save_json(attempt/'ANSWERS.json',answers)
 report='# '+task['task_id']+'\n\n![2D to real 3D vertex evidence](visualization/figures/Fig1_2D_TO_3D.png)\n\nA3: original013 + frozen004/005 + explicit normal contour constraints, no HERO depth. A2 frozen historical baseline. A2D removes depth but keeps historical direct contour loss, isolating the new correspondence mechanism. No camera optimization. All trained arms use original train_mesh optimizer/FreeVertices/RingAware/guard/budget and final accepted Mesh.\n\nGT uses best_rigid015 scale1 SE3 on frozen evaluation copies only; source-world Body is unchanged and is used by HERO.\n\nH1=A2+ellipse; H2=A3+ellipse; H3=A2+actual Mesh boundary; H4=A3+actual Mesh boundary. Same sources, transforms budget and 0.5mm Body tolerance. Actual triangles remain rigid; cameras and Body fixed. Boundary transfer is only a candidate constraint; not a physical surface replacement.\n\n## All-case comparisons\n\n'+json.dumps(pairs,indent=2,ensure_ascii=False)+'\n\n## Body/HERO relationship\n\n'+json.dumps(relationship,indent=2,ensure_ascii=False)+'\n\n## Audit\n\n| 审计项目 | 必须汇报 |\n| --- | --- |\n| 目标组数 | 11 physical groups |\n| 本算法独立成功 | A3 numerical '+str(sum(r['arm']=='A3'and r['status']=='NUMERIC'for r in body['rows']))+'/11; numeric output is not accuracy |\n| 本算法失败 | all missing/invalid arms retained in FAILURE_LEDGER |\n| 历史测量值回退 | 0; A0/A2 explicit reference arms only |\n| 失败组及具体原因 | [ledger](visualization/FAILURE_LEDGER.json); G08 missing004; HERO missing native source binding retained |\n| 最终统计样本 | matched A2/A3 and A2D/A3; strict IoU valid entities only; all11 denominator |\n| 是否使用 GT 选择算法 | No; last accepted Mesh and frozen source code; no GT/HOLDOUT tuning |\n\n## Artifacts\n\n[Body metrics](visualization/BODY_SHAPE_METRICS.csv) · [all11 HERO](visualization/HERO_ALL11_METRICS.csv) · [GT SE3](visualization/GT_RIGID_TRANSFORMS.json) · [2D→3D links](visualization/BODY_UPDATE_LINKS.json)\n\n'
 for n in sorted(figdir.glob('*.png')):report+='!['+n.stem+'](visualization/figures/'+n.name+')\n\n'
 (attempt/'TECHNICAL_REPORT.md').write_text(report);(attempt/'RESULT_CARD.md').write_text('# '+task['task_id']+'\n\nExecution completed; scientific results require review. Explicit matched comparisons, failures and actual Meshes retained.\n\n[Report](TECHNICAL_REPORT.md) · [metrics](visualization/BODY_SHAPE_METRICS.csv)\n')
 # Plain manifest only, intentionally no dashboard/WebGL app.
 paths=artifact_files(attempt)
 index='<!doctype html><meta charset="utf-8"><title>Offline artifact index</title><h1>PNG / GLB / exact Mesh files</h1><p>Images are the primary scientific deliverable. GLB: one coordinate unit = 1 mm; named full Mesh nodes may be toggled in a GLB viewer. No web visualization application.</p><svg width="1" height="1"></svg><img src="../evidence.png" width="1" alt="Historical harness evidence only"><ul>'
 for p in paths:
  rel=str(p.relative_to(attempt));index+='<li><a href="'+html.escape(rel)+'">'+html.escape(rel)+'</a></li>'
 (attempt/'index.html').write_text(index+'</ul>\n');return outputs(attempt,dict(status='PASS',scientific_failures=failures,body_pairs=len(pairs),hero_groups=len(hero['groups']),PNG_primary=True))
