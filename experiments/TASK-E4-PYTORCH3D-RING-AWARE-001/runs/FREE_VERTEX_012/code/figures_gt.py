from visual_common import *
from evaluate import distance
from matplotlib.colors import Normalize

def aligned_figure():
 cases=load(R/'config/CASE_LOCK.json');sc={x['case']:x for x in load(R/'metrics/RING_SCALE_VALIDATION.json')};fig=plt.figure(figsize=(27,24));gs=fig.add_gridspec(3,3,hspace=.1,wspace=.05);cmap=plt.get_cmap('magma');normalizer=Normalize(0,1)
 for i,c in enumerate(cases):
  n=c['name'];sub=gs[i//3,i%3].subgridspec(2,2,wspace=.03,hspace=.12);axs=[fig.add_subplot(sub[a,b])for a in range(2)for b in range(2)];s=sc[n];axs[0].axis('off');axs[0].text(0,.97,n+' '+c['morphology']+'\n'+c['ring']+' fixed CAD inner D = %.6f mm'%s['CAD_measured_inner_diameter']+'\nTrue D = %.1f mm'%s['true_inner_diameter_mm']+'\nCAD recovery ratio = %.9f'%s['recovery_ratio']+'\nApplied scale = %.9f'%s['applied_scale']+'\nScale locked before GT / ICP\nRigid transform: rotation + translation only\nBlack CAD is carried by the same evaluation transform.',va='top',fontsize=8)
  gt=R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz';ap=R/'local_results/aligned'/n/'FINAL012.npz'
  if not gt.exists()or not ap.exists():
   for ax in axs[1:]:ax.axis('off');ax.text(.5,.5,'NOT_EVALUABLE\nNo verified corresponding GT/alignment',ha='center',transform=ax.transAxes,fontsize=8)
   continue
  g=np.load(gt);a=np.load(ap);raw=np.load(R/'local_results/metric'/n/'FINAL012.npz');rr=np.load(R/'local_results/metric'/n/'RING.npz');T=a['T'];RV=rr['V']@T[:3,:3].T+T[:3,3];bound=np.r_[g['V'],raw['V'],a['V'],RV,rr['V']];F=a['F_solid'];mixedV=np.r_[g['V'],a['V']];mixedF=np.r_[g['F'],F+len(g['V'])];colors=np.r_[np.tile([.67,.7,.72],(len(g['F']),1)),np.tile(matplotlib.colors.to_rgb(COL['FINAL012']),(len(F),1))];colors[len(g['F']):][a['inferred_base_faces']]=[.4,.4,.4]
  rawV=np.r_[g['V'],raw['V']];rawF=np.r_[g['F'],raw['F_solid']+len(g['V'])];im,scl=actual_mesh_image(rawV,rawF,rr['V'],rr['F'],bound,25,-65,COL['FINAL012'],colors);axs[1].imshow(im);axs[1].set_title('Before rigid alignment: GT gray / raw prediction purple',fontsize=7)
  im,scl=actual_mesh_image(mixedV,mixedF,RV,rr['F'],bound,25,-65,COL['FINAL012'],colors);axs[2].imshow(im);axs[2].set_title('After 6-DoF rigid alignment; scale = 1',fontsize=7)
  centers=a['V'][F].mean(1);err=distance(scene(g['V'],g['F']),centers);col=cmap(normalizer(err))[:,:3];col[a['inferred_base_faces']]=[.5,.5,.5];im,scl=actual_mesh_image(a['V'],F,RV,rr['F'],bound,25,-65,COL['FINAL012'],col);axs[3].imshow(im);axs[3].set_title('Closest GT surface error: 0–1+ mm\nGray = inferred closure, not observed tissue',fontsize=7)
  for ax in axs[1:]:ax.plot([20,20+2*scl],[375,375],c='black',lw=1.4);ax.text(20,365,'2 mm',fontsize=5);ax.axis('off')
 fig.suptitle('After Ring-based Metric Recovery and 6-DoF Rigid Alignment\nOriginal model correspondence must be verified; GT never optimized predictions or scale.\nIdentical mm viewer within each case; gray GT, purple prediction, black source CAD. Missing evaluations stay visible.',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig4_Ring_Scale_and_Blender_Alignment.png')

def metrics_figure():
 rows=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json');data={x['case']:x for x in rows if x['label']=='FINAL012'};old={x['case']:x for x in rows if x['label']=='FINAL011'};names=load(R/'config/PROTOCOL.json')['cases'];x=np.arange(9);fig=plt.figure(figsize=(22,17));gs=fig.add_gridspec(3,2,height_ratios=[1,1,1.25],hspace=.4,wspace=.2);axes=[fig.add_subplot(gs[i,j])for i in range(2)for j in range(2)]
 def values(items,key,mul=1):return np.array([np.nan if items[n].get(key)is None else items[n][key]*mul for n in names])
 for ax,key,title,mul in [(axes[0],'Dxy_AE_mm','Dxy absolute error (mm)',1),(axes[1],'Chamfer_MAE_mm','Bidirectional sampled Chamfer MAE (mm)',1)]:
  ax.bar(x-.18,values(old,key,mul),.36,color=COL['FINAL011'],label='011 FINAL');ax.bar(x+.18,values(data,key,mul),.36,color=COL['FINAL012'],label='012 FREE');ax.set_title(title);ax.set_xticks(x,names);ax.legend(fontsize=8)
  for j,n in enumerate(names):
   if data[n].get(key)is None:ax.text(j,.02,'N/E',transform=ax.get_xaxis_transform(),ha='center',fontsize=8)
 axes[2].plot(x,values(old,'HOLDOUT_2D_IoU_original_cameras'),'o-',color=COL['FINAL011'],label='011 holdout');axes[2].plot(x,values(data,'HOLDOUT_2D_IoU_original_cameras'),'o-',color=COL['FINAL012'],label='012 holdout');axes[2].set_xticks(x,names);axes[2].set_ylim(0,1);axes[2].set_title('Original-camera HOLDOUT 2D Mask IoU (unchanged by frame alignment)');axes[2].legend(fontsize=8)
 axes[3].bar(x-.18,values(data,'IoU_3D'),.36,label='valid-solid IoU estimate',color='#388f9c');axes[3].bar(x+.18,values(data,'occupancy_IoU_proxy'),.36,label='occupancy proxy (inferred base)',color='#a4b6bf',hatch='//');axes[3].set_xticks(x,names);axes[3].set_ylim(0,1);axes[3].set_title('3D solid/proxy distinctions; N/E is never filled with zero');axes[3].legend(fontsize=8)
 ax=fig.add_subplot(gs[2,:]);ax.axis('off')
 def fmt(v):return 'N/E'if v is None else'%.3f'%v
 tabledata=[[n,fmt(data[n]['Dxy_GT_mm']),fmt(data[n]['Dxy_pred_mm']),fmt(data[n]['Dxy_relative_error']),fmt(data[n]['height_max_GT_mm']),fmt(data[n]['height_max_pred_mm']),fmt(data[n]['H95_pred_mm']),fmt(data[n]['IoU_3D']),fmt(data[n]['occupancy_IoU_proxy']),fmt(data[n]['Chamfer_MAE_mm'])]for n in names];table=ax.table(cellText=tabledata,colLabels=['Case','GT Dxy mm','Pred Dxy mm','Dxy rel error','GT Hmax mm','Pred Hmax mm','Pred H95 mm','Strict 3D IoU','Occupancy proxy','Chamfer mm'],loc='center',cellLoc='center');table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.7)
 fig.suptitle('Nine targets always retained | After Ring-based Metric Recovery and 6-DoF Rigid Alignment\nN/E means missing/invalid source or metric, never case removal. Height requires an established author base, not the Ring plane.\nConditional pose-free geometric comparisons are not end-to-end camera or clinical measurement accuracy.',fontsize=12);finish(fig,'Fig5_Quantitative_Results.png')

if __name__=='__main__':aligned_figure();metrics_figure();print('GT_FIGURES_COMPLETE')
