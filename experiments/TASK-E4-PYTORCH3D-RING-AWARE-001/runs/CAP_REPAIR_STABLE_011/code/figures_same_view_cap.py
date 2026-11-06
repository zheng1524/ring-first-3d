"""Display-only correction: preserve frozen Fig2 and compare all models at identical views."""
from visual import *

def main():
 fig,axs=plt.subplots(4,5,figsize=(23,18))
 for i,c in enumerate(['G05','G09']):
  bs=load(R/'inputs'/c/'BASE_SELECTION.json');bound=bounds(c)
  for k,angle in enumerate([(0,-65),(25,-65)]):
   row=2*i+k;rgb(axs[row,0],c,bs['primary'],['OLD_C','INITIAL']);axs[row,0].set_title(c+' source RGB, not 3D viewer\n'+bs['uncertainty_label'],fontsize=8)
   for j,tag in enumerate(['B','OLD_C','C_START','INITIAL']):
    title={'B':'009 B: retained blue / below-base gray','OLD_C':'009 frozen untruncated C','C_START':'B-blue initialized parametric cap','INITIAL':'011 fitted cap; inferred basal closure gray'}[tag]
    meshpanel(axs[row,j+1],c,tag,angle,title=title+'\nviewer '+str(angle)+' deg; identical mm bounds',bound=bound)
 fig.suptitle('G05 / G09 cap repair: strict same-view comparison\nEvery 3D panel within a row uses the identical camera and millimetre bounds; side and oblique views are separate rows.\nDisplay-only supplement: original pre-optimization Fig2 remains immutable; no model or plane was changed.',fontsize=12)
 fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig2b_G05_G09_Same_View_Cap_Repair.png',145)

if __name__=='__main__':main()
