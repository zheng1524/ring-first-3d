"""Scientific figures from actual frozen data, common physical/color scales."""
import os,json,csv,shutil
from pathlib import Path
import numpy as np
from historical_io import W
T=Path(__file__).resolve().parent.parent;B=W/'runs/m2f12_historical004';os.environ['MPLCONFIGDIR']=str(B/'plot_runtime')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=list(csv.DictReader((T/'evidence/COMPARISON_LONG.csv').open()));registry=json.loads((T/'evidence/INPUT_REGISTRY.json').read_text());F=T/'figures';F.mkdir(exist_ok=True)
labels=[r['group'].removeprefix('GP_').split('mm')[0]+'/'+r['video_id']for r in registry]
fig,axes=plt.subplots(3,1,figsize=(14,10),sharex=True);x=np.arange(10)
for ax,key,title in zip(axes,['numeric_cameras','own_qualified_cameras','legal_target_count'],['Numeric cameras','Each route\'s own qualified cameras (different native gates)','Targets with 3 legal supports (V6 target may be unvalidated)']):
 for j,(route,color)in enumerate([('H004_RAW_BASELINE','#1976a3'),('V6','#b57332')]):
  rs=[next(v for v in rows if v['route']==route and v['group']==r['group']and v['video']==r['video_id'])for r in registry];vals=[int(r[key])for r in rs];bars=ax.bar(x+(j-.5)*.36,vals,.34,color=color,label=route)
  ax.bar_label(bars,padding=2,fontsize=8)
 ax.set_title(title);ax.set_ylabel('count');ax.grid(axis='y',alpha=.2);ax.legend(fontsize=9)
axes[-1].set_xticks(x,labels,rotation=30,ha='right');fig.suptitle('Fixed denominator: 5 physical groups / 10 videos; native schedules differ\nCoverage comparison, not a paired causal or absolute-pose accuracy test',fontsize=12);fig.tight_layout();fig.savefig(F/'COMPARISON_OVERVIEW.png',dpi=130);plt.close(fig)
fig=plt.figure(figsize=(19,8))
for j,r in enumerate(registry):
 ax=fig.add_subplot(2,5,j+1,projection='3d');R=B/'H004_RAW_BASELINE'/r['case'];p=R/'landmarks/INDEPENDENT_VIDEO.npz';th=np.linspace(0,2*np.pi,120);rad=r['ring_inner_mm']/2+.6
 ax.plot(rad*np.cos(th),rad*np.sin(th),np.zeros_like(th),color='black',linewidth=1)
 if p.exists():
  X=np.load(p)['X'];a=json.loads((R/'landmarks/BUILD_AUDIT.json').read_text());qc=[x for x in a['tracks']if x['qualified']];colors=['#df8a24'if x['category']=='polyp'else'#7c4da5'if x['category']=='mixed'else'#999999'for x in qc];ax.scatter(*X.T,c=colors,s=2,alpha=.6)
  cs=json.loads((R/'registration/CAMERAS.json').read_text());C=np.array([v['C']for v in cs if v['C']is not None]);ax.plot(*C[:,:3,3].T,color='#1976a3',linewidth=1);ax.scatter(*C[:,:3,3].T,c='#1976a3',s=5)
  shown=((X[:,0]>=-25)&(X[:,0]<=25)&(X[:,1]>=-25)&(X[:,1]<=25)&(X[:,2]>=-10)&(X[:,2]<=60)).sum();title=f"{labels[j]} | shown {shown}/{len(X)} landmarks"
 else:title=labels[j]+' | NO MAP'
 ax.set_title(title,fontsize=8);ax.set(xlim=(-25,25),ylim=(-25,25),zlim=(-10,60),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.tick_params(labelsize=6);ax.view_init(20,-60)
fig.suptitle('H004 actual landmarks and recovered camera centers; fixed viewport clips out-of-range points (counts stated)\nBlack: physical Ring centerline; gray/background, orange/polyp, purple/mixed; arbitrary per-video yaw, no pose GT',fontsize=11);fig.tight_layout();fig.savefig(F/'LANDMARKS_AND_TRAJECTORIES.png',dpi=120);plt.close(fig)
links=[('COMPARISON_OVERVIEW.png','Native coverage, fixed ten-video denominator'),('LANDMARKS_AND_TRAJECTORIES.png','Actual landmarks/cameras, axes in mm')]
for p in sorted((B/'HERO_LIMITED').glob('*/*/HERO_A_TO_B.png')):
 name=p.parent.parent.name+'__'+p.parent.name+'.png';shutil.copyfile(p,F/name);links.append((name,p.parent.name+' / '+p.parent.parent.name))
html='<!doctype html><meta charset="utf-8"><title>M2F12 figures</title><h1>M2F12 evidence</h1><p>Real imagery and computed geometry. Ring dimensions and depth are in millimeters. No independent pose/shape GT. Native schedules differ; A→B B views are HERO supports.</p>'
html+=''.join('<p><a href="'+p+'">'+title+'</a></p><img style="max-width:1100px;width:100%" src="'+p+'">'for p,title in links);(F/'index.html').write_text(html)
(T/'VISUALIZATION_INDEX.md').write_text('# Visualization index\n\nFixed 5 groups / 10 videos. Real images, physical mm units, independent pose/registered-shape GT evaluation NOT_EVALUABLE.\n\n'+''.join('- ['+title+'](figures/'+p+')\n'for p,title in links)+'\n[HTML gallery](figures/index.html)\n')
print('FIGURES',len(links))
