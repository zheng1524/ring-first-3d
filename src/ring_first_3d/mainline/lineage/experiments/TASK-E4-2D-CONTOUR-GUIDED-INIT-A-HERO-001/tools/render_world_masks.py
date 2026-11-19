"""Native real-image projection comparison; no GT-aligned copies or image deformation."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ring_first_3d.multisurface.geometry import scene,cast
TD=Path.cwd()/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';VIS=TD/'visualization';source=json.loads((TD/'inputs/SOURCES.json').read_text());receipts=[]
for row in source['cases']:
 g=row['case'];bodies={}
 for arm in ['A2','A3']:
  p=VIS/'meshes'/(g+'_'+arm+'_WORLD.npz')
  if p.is_file():m=np.load(p);bodies[arm]=scene(m['V'],m['F'])
 selected=[]
 for video in ['004','005']:
  vs=[v for v in row['FIT']if v['meta']['video']==video]
  if vs:selected.append(vs[0])
 if not selected:continue
 ring=np.load(row['static']['RING.npz']['path']);rs=scene(ring['V'],ring['F']);fig,axes=plt.subplots(len(selected),3,figsize=(15,4*len(selected)),squeeze=False,layout='constrained')
 for i,v in enumerate(selected):
  a=np.load(v['cache']['path']);lab=a['labels'];H,W=lab.shape;y,x=np.mgrid[:H,:W];uv=np.c_[x.ravel(),y.ravel()];rz,_,_=cast(rs,uv,a['K'],a['T']);axes[i,0].imshow(a['RGB']);axes[i,0].contour(lab==1,levels=[.5],colors='lime',linewidths=.8);axes[i,0].contour(lab==2,levels=[.5],colors='black',linewidths=.8);axes[i,0].set_title(v['meta']['id']+' / frozen source',fontsize=9)
  for j,arm in enumerate(['A2','A3'],1):
   ax=axes[i,j];ax.imshow(a['RGB'])
   if arm not in bodies:ax.text(.1,.5,arm+' NOT_EVALUABLE',transform=ax.transAxes,color='red');ax.axis('off');continue
   z,_,_=cast(bodies[arm],uv,a['K'],a['T']);pred=(np.isfinite(z)&(z>0)&(z<rz)).reshape(H,W);target=lab==1;known=lab!=2;tp=pred&target;fn=~pred&target;fp=pred&~target&known;overlay=np.zeros((H,W,4));overlay[tp]=[0,.9,0,.3];overlay[fn]=[1,0,1,.6];overlay[fp]=[1,0,0,.6];ax.imshow(overlay);value=int(tp.sum())/max(1,int((tp|fn|fp).sum()));ax.set_title(arm+' WORLD actual triangle projection / IoU %.5f'%value,fontsize=9);receipts.append(dict(case=g,view=v['meta']['id'],video=v['meta']['video'],arm=arm,IoU=value,target_N=int(target.sum()),TP=int(tp.sum()),FN=int(fn.sum()),FP=int(fp.sum()),GT_aligned=False,source_cache_sha256=v['cache']['sha256']))
  for ax in axes[i]:ax.axis('off')
 fig.suptitle(g+' | A2/A3 explain the same frozen004/005 real observations\nGreen overlap / magenta missed / red extra; Ring unknown negatives excluded exactly as evaluator. No camera or image transform.',fontsize=10);fig.savefig(VIS/'figures'/(g+'_A2_A3_WORLD_MASKS.png'),dpi=115);plt.close(fig)
(VIS/'REPRESENTATIVE_WORLD_MASK_PROJECTIONS.json').write_text(json.dumps(receipts,indent=2)+'\n');print('Actual representative world-mask scores',len(receipts))
