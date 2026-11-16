"""All-case actual mesh evidence; no prediction is selected by GT."""
from visual_base import *
from evaluate import distance
from matplotlib.colors import Normalize

TAGS=['Init-A','Init-B','Init-C']
def models(n):return [dict(np.load(R/'initializations'/n/(t+'.npz')))for t in TAGS]+[dict(np.load(R/'arms'/t/'local_results'/n/'FINAL.npz'))for t in TAGS]
def rgb_panel(ax,n,cid):
 a=np.load(R/'inputs'/n/(cid+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');ax.axis('off');return a

def main():
 assert(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json').exists();cases=load(R/'config/CASE_LOCK.json');selection=load(R/'config/VIEW_SELECTION.json');choice=load(R/'config/PHASE_A_SELECTED.json')['selected'];ips=load(R/'config/PROTOCOL.json')['phase_B']['cases']
 fig,ax=plt.subplots(len(cases),7,figsize=(22,3*len(cases)))
 for i,c in enumerate(cases):
  n=c['name'];cid=selection[n]['FIT'][0];rgb_panel(ax[i,0],n,cid);ax[i,0].set_title(n+' '+c['morphology']+' real RGB/Mask',fontsize=8);mm=models(n);rr=np.load(R/'inputs'/n/'RING.npz');bounds=np.concatenate([m['V']for m in mm]+[rr['V']])
  for j,m in enumerate(mm):model_panel(ax[i,j+1],n,m,bounds);ax[i,j+1].set_title(TAGS[j%3]+(' INITIAL'if j<3 else' FINAL'),fontsize=8)
 fig.suptitle('All11 independent specimens | A/B/C initializers + identical downstream Mesh optimization\nBlack CAD / gray inferred cap / own frozen mm frame per case. All cases, no favorable-sample selection.',fontsize=13);fig.subplots_adjust(top=.958,hspace=.18,wspace=.02);finish(fig,'Fig1_All11_Initializers_And_Updates.png',105)
 fig,ax=plt.subplots(len(ips),5,figsize=(19,3.6*len(ips)))
 for i,n in enumerate(ips):
  rgb_panel(ax[i,0],n,selection[n]['HOLDOUT'][0]);ax[i,0].set_title(n+' real HOLDOUT',fontsize=8);common=dict(np.load(R/'arms'/choice/'local_results'/n/'FINAL.npz'));mm=[common]
  for t in ['Stalk-A','Stalk-B','Stalk-C']:
   p=R/'arms'/t/'local_results'/n/'FINAL.npz';mm.append(dict(np.load(p))if p.exists()else None)
  rr=np.load(R/'inputs'/n/'RING.npz');bounds=np.concatenate([m['V']for m in mm if m is not None]+[rr['V']])
  for j,m in enumerate(mm):
   if m is None:ax[i,j+1].text(.1,.5,'NO RESIDUAL SIGNAL\nNo optimized prediction');ax[i,j+1].axis('off');continue
   model_panel(ax[i,j+1],n,m,bounds,angle=(12,-65));ax[i,j+1].set_title(['Common Phase A FINAL','Stalk-A','Stalk-B','Stalk-C'][j],fontsize=8)
 fig.suptitle('All5 Ip | common FIT-only selected initialization + three stalk updates\nActual connected meshes, identical camera/scale per specimen. Proxy seed is not anatomical ground truth.');fig.subplots_adjust(top=.93,hspace=.18,wspace=.02);finish(fig,'Fig2_All5_Ip_Stalk_Comparison.png',115)
 # Gradient and actual executed displacement are separate quantities.
 fig,ax=plt.subplots(len(ips),3,figsize=(16,3.5*len(ips)))
 for i,n in enumerate(ips):
  a=np.load(R/'arms/Stalk-A/metrics'/(n+'_STALK_GRADIENTS.npz'));probe=load(R/'arms/Stalk-A/metrics'/(n+'_STALK_PROBE.json'));base=dict(np.load(R/'arms/Stalk-A/inputs'/n/'INITIAL.npz'));rr=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[base['V'],rr['V']];v=a['V'];far=a['far'];old=a['old_candidate'];fc=np.tile([.65,.65,.65],(len(base['F_solid']),1));f=base['F_solid'];fc[far[f].any(1)]=[.9,.25,.2];fc[(far&old)[f].any(1)]=[.95,.7,.1];model_panel(ax[i,0],n,base,bounds,face_colors=fc);ax[i,0].set_title(n+' actual far '+str(probe['far_associated_N'])+'; old-covered '+str(probe['old_local_candidates_cover_far_N']),fontsize=8)
  grad=np.linalg.norm(a['contour'],axis=1);col=plt.get_cmap('viridis')(np.clip(grad[f].mean(1)/max(1e-15,np.quantile(grad,.95)),0,1))[:,:3];model_panel(ax[i,1],n,base,bounds,face_colors=col);ax[i,1].set_title('Actual weighted contour gradient, not displacement',fontsize=8)
  p=R/'arms/Stalk-B/local_results'/n/'FINAL.npz'
  if p.exists():
   z=dict(np.load(p));move=np.linalg.norm(z['V']-v,axis=1);col=plt.get_cmap('magma')(np.clip(move[f].mean(1)/max(1e-15,move.max()),0,1))[:,:3];model_panel(ax[i,2],n,z,bounds,face_colors=col);ax[i,2].set_title('Stalk-B actual total displacement max %.4f mm'%move.max(),fontsize=8)
 fig.suptitle('Current FIT-only mechanism evidence | red far-associated / gold old-band-covered\nNearest image-contour association is a geometric proxy; actual gradient and actual optimizer motion are reported separately.');fig.subplots_adjust(top=.93,hspace=.2);finish(fig,'Fig3_Current_Coverage_Gradient_And_Motion.png',115)
 # Pure-body GT comparisons use exactly the stored rigid transform, no rescaling.
 fig=plt.figure(figsize=(20,3*len(cases)))
 for i,c in enumerate(cases):
  n=c['name'];gp=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz';paths=[R/'local_results/aligned'/n/(t+'_FINAL.npz')for t in TAGS]
  if not gp.exists():continue
  g=np.load(gp);present=[dict(np.load(p))if p.exists()else None for p in paths];bounds=np.r_[g['V'],*[z['V']for z in present if z is not None]];lo=bounds.min(0);hi=bounds.max(0);center=(lo+hi)/2;rad=max(hi-lo)/2
  for j,z in enumerate(present):
   ax=fig.add_subplot(len(cases),3,i*3+j+1,projection='3d');ax.add_collection3d(Poly3DCollection(g['V'][g['F']],facecolors=(.6,.6,.6,.18),edgecolors='none'))
   if z is not None:ax.add_collection3d(Poly3DCollection(z['V'][z['F']],facecolors=(.33,.22,.68,.68),edgecolors='none'))
   ax.set(xlim=(center[0]-rad,center[0]+rad),ylim=(center[1]-rad,center[1]+rad),zlim=(center[2]-rad,center[2]+rad));ax.set_box_aspect((1,1,1));ax.view_init(20,-65);ax.set_title(n+' '+TAGS[j]+' FINAL / mm',fontsize=8);ax.tick_params(labelsize=5)
 fig.suptitle('After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment\nGray Blender / purple prediction; one SE(3) per prediction, fixed scale1. Ring/background excluded from registration.');fig.subplots_adjust(top=.958,hspace=.18);finish(fig,'Fig4_All11_Rigid_Aligned_GT_Comparison.png',110)
 print('FOUR_CORE_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
