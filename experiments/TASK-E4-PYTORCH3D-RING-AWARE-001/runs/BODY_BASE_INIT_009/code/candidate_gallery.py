"""All fixed starts/stages, including failures; display only, never select a model."""
import visualize_body as v
from visualize_body import *
def main():
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];paths=sorted((R/'local_results'/n).glob('*.npz'));tags=['A']+[p.stem for p in paths if p.stem!='A_ELLIPSOID_PARAMETER_ADAPTER'];allV=np.concatenate([model(n,t)['V']for t in tags]);v.common_bounds=lambda name,points=allV:points;v.CACHE.clear();N=len(tags);cols=5;rows=int(np.ceil(N/cols));fig,axs=plt.subplots(rows,cols,figsize=(17,3.5*rows),squeeze=False)
  for ax,tag in zip(axs.ravel(),tags):
   col='A'if tag=='A'else'C'if tag.startswith('C')else'CONTOUR'if'CONTOUR'in tag else'B';meshpanel(ax,n,tag,col,underground=True);title=tag
   p=R/'local_results'/n/(tag+'.json')
   if p.exists():
    meta=load(p);di=meta.get('diagnostics');title+='\n'+('CAD error '+str(di['Ring_collision'])if di else'no independent final CAD label')
   ax.set_title(title,fontsize=8)
  for ax in axs.ravel()[N:]:ax.axis('off')
  fig.suptitle(n+' | every retained fixed initial/stage candidate, including failures\nONE common viewer from all candidate bounds in this gallery, black CAD; gray below estimated base/inferred closure. No geometry edits.',fontsize=11);fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'full/'+n+'_All_Candidates.png',115)
 print('ALL_CANDIDATE_GALLERIES_DONE')
if __name__=='__main__':main()
