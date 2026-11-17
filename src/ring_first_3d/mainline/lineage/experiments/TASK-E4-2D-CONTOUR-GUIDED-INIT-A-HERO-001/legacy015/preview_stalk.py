"""Paired true meshes in identical native-mm framing, no GT."""
from visual_base import *
import argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');n=ap.parse_args().case;tags=['Stalk-A','Stalk-B','Stalk-C'];chosen=load(R/'config/PHASE_A_SELECTED.json')['selected'];base=dict(np.load(R/'arms'/chosen/'local_results'/n/'FINAL.npz'));models=[]
 for tag in tags:
  p=R/'arms'/tag/'local_results'/n/'FINAL.npz';models.append(dict(np.load(p))if p.exists()else None)
 ring=np.load(R/'inputs'/n/'RING.npz');bounds=np.concatenate([base['V']]+[m['V']for m in models if m is not None]+[ring['V']]);fig,ax=plt.subplots(4,4,figsize=(19,17));shown=[base]+models;labels=['Common Phase A FINAL']+tags;cid=load(R/'config/VIEW_SELECTION.json')[n]['HOLDOUT'][0];a=np.load(R/'inputs'/n/(cid+'.npz'));cad=cast(scene(ring['V'],ring['F']),a['K'],a['T'],*a['labels'].shape)
 for j,(tag,m)in enumerate(zip(labels,shown)):
  if m is None:
   for k in range(4):ax[k,j].text(.1,.5,'NO RESIDUAL SEED\nNo optimized result');ax[k,j].axis('off')
   continue
  for k,angle in enumerate([(20,-65),(0,0),(35,135)]):model_panel(ax[k,j],n,m,bounds,angle=angle);ax[k,j].set_title(tag)
  z=cast(scene(m['V'],m['F']),a['K'],a['T'],*a['labels'].shape);pred=np.isfinite(z)&(z<cad);ax[3,j].imshow(a['RGB']);edge(ax[3,j],a['labels']==1,'lime');edge(ax[3,j],a['labels']==2,'cyan');edge(ax[3,j],pred,'gold');ax[3,j].set_title('Fixed HOLDOUT '+cid,fontsize=8);ax[3,j].axis('off')
 fig.suptitle(n+' | Same world mm / black CAD / gray inferred cap\nFIT-only residual seed. Common objective/guard/budget. No anatomical GT claim.');fig.subplots_adjust(top=.94);finish(fig,'phase_B/'+n+'_Stalk_Comparison.png',120);print('STALK_PREVIEW',n,flush=True)
if __name__=='__main__':main()
