"""Actual completed G01/G03 predictions, read-only and GT-free."""
from visual_base import *

def main():
 fig,axes=plt.subplots(2,4,figsize=(18,10))
 for row,n in enumerate(['G01','G03']):
  init=dict(np.load(R/'inputs'/n/'INITIAL.npz'));final=dict(np.load(R/'arms/FINAL_014/local_results'/n/'FINAL.npz'));rg=np.load(R/'inputs'/n/'RING.npz');b=np.concatenate([init['V'],final['V'],rg['V']])
  c=next(x for x in load(R/'config/CASE_LOCK.json')if x['name']==n);cid=next(x['id']for x in c['views']if x['role']=='FIT');a=np.load(R/'inputs'/n/(cid+'.npz'));cad=cast(scene(rg['V'],rg['F']),a['K'],a['T'],360,640)
  axes[row,0].imshow(a['RGB']);edge(axes[row,0],a['labels']==1,'lime');edge(axes[row,0],a['labels']==2,'cyan')
  for m,col in [(init,'gold'),(final,'magenta')]:
   zz=cast(scene(m['V'],m['F']),a['K'],a['T'],360,640);edge(axes[row,0],np.isfinite(zz)&(zz<cad),col)
  axes[row,0].set_title(n+' '+cid+'; green observed, gold011, magenta014',fontsize=8);axes[row,0].axis('off')
  for ax,m,label,angle in [(axes[row,1],init,'011 initial',(0,-65)),(axes[row,2],final,'014 final',(0,-65)),(axes[row,3],final,'014 final oblique',(25,-65))]:
   model_panel(ax,n,m,b,angle);ax.set_title(n+' '+label,fontsize=10)
 fig.suptitle('Actual completed G01 / G03 predictions | native observation and fixed metric viewer\nNo GT read; no smoothing, post-trimming, fake stalk or scale adjustment. Black CAD. Not a geometry accuracy claim.')
 finish(fig,'details/Intermediate_G01_G03_Final_Predictions.png')
if __name__=='__main__':main()
