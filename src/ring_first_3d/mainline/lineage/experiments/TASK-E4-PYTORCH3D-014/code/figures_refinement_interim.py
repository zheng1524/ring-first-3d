"""Read-only actual E controls; no GT, no method selection, no mesh edits."""
from visual_base import *

def main():
 n='G03';tags=['D_D2_bidir','E0_none','E1_global','E2_adaptive'];models=[dict(np.load(R/'arms'/t/'local_results'/n/'FINAL.npz'))for t in tags]
 common=np.concatenate([m['V']for m in models]+[np.load(R/'inputs'/n/'RING.npz')['V']]);fig,axes=plt.subplots(2,4,figsize=(19,10))
 for row,angle in enumerate([(0,-65),(25,-65)]):
  for j,(tag,m)in enumerate(zip(tags,models)):
   model_panel(axes[row,j],n,m,common,angle)
   run=load(R/'arms'/tag/'metrics'/(n+'_RUN.json'))
   axes[row,j].set_title(f"{tag}\nV={len(m['V'])}; accepted={run['accepted']}; displacement={run['maximum_displacement_mm']:.6f} mm",fontsize=9)
 fig.suptitle('G03 | Actual coarse / no subdivision / global / adaptive continuation\nSame world bounds, black metric CAD, real meshes. Vertex density or displacement alone is not stalk recovery.')
 finish(fig,'details/Intermediate_G03_E_Actual_Controls.png')
if __name__=='__main__':main()
