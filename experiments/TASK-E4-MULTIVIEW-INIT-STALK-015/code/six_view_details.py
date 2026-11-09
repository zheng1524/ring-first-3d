"""Unmodified actual meshes, frozen per-case framing, six explicit viewer angles."""
from visual_base import *
from final_figures import models

def main():
 assert(R/'provenance/PHASE_B_PREDICTIONS_FROZEN.json').exists()
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];mm=models(n);labels=[t+' '+s for s in ['INITIAL','FINAL']for t in ['Init-A','Init-B','Init-C']];rr=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[*[m['V']for m in mm],rr['V']];angles=[(25,-65),(0,0),(0,90),(0,180),(75,-65),(-60,-65)];fig,ax=plt.subplots(6,6,figsize=(20,20))
  for i,ang in enumerate(angles):
   for j,m in enumerate(mm):model_panel(ax[i,j],n,m,bounds,angle=ang);ax[i,j].set_title(labels[j]+' / '+str(ang),fontsize=7)
  fig.suptitle(n+' | Six fixed views of all3 initializers and their final meshes\nSame native mm and common bounds; black CAD; gray inferred cap. No smoothing or trimming.');fig.subplots_adjust(top=.95,hspace=.1,wspace=.02);finish(fig,'details/'+n+'_All_Initializers_Six_Views.png',100)
  tags=['Stalk-A','Stalk-B','Stalk-C'];paths=[R/'arms'/t/'local_results'/n/'FINAL.npz'for t in tags]
  if not all(p.exists()for p in paths):continue
  mm=[dict(np.load(p))for p in paths];bounds=np.r_[bounds,*[m['V']for m in mm]];fig,ax=plt.subplots(6,3,figsize=(12,21))
  for i,ang in enumerate(angles):
   for j,m in enumerate(mm):model_panel(ax[i,j],n,m,bounds,angle=ang);ax[i,j].set_title(tags[j]+' / '+str(ang),fontsize=8)
  fig.suptitle(n+' | All3 stalk updates, six native-mm views\nBlack fixed CAD; no GT selection.');fig.subplots_adjust(top=.96);finish(fig,'details/'+n+'_Stalk_Six_Views.png',105)
 print('ALL_SIX_VIEW_DETAILS_COMPLETE',flush=True)
if __name__=='__main__':main()
