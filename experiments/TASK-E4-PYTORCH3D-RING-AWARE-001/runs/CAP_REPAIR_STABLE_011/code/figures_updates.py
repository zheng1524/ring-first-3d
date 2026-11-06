from visual import *
from chart import Chart,Case,tensor,torch

def summary(c,label):return next(x for x in load(R/'metrics/ALL_STAGE_WITH_BLENDER.json')if x['case']==c and x['label']==label)
def annotate(ax,c,label):
 x=summary(c,label);ax.text(.01,.98,'CAD '+str(x.get('Blender_Ring_pairs_N'))+' / self '+str(x.get('Blender_self_N'))+' / below '+str(x['below_estimated_base_vertex_N']),transform=ax.transAxes,va='top',fontsize=5,color='red'if(x.get('Blender_self_N')or 0)>0 or x['Ring_surface_collision']else'dimgray')

def final_overview():
 cases=load(R/'config/CASE_LOCK.json');fig=plt.figure(figsize=(30,23));grid=fig.add_gridspec(3,3,hspace=.2,wspace=.05)
 for i,kind in enumerate(['Ip','Is','IIa']):
  for j,c in enumerate([c for c in cases if c['morphology']==kind]):
   n=c['name'];sub=grid[i,j].subgridspec(2,4,wspace=.03,hspace=.15);axs=[fig.add_subplot(sub[r,k])for r in range(2)for k in range(4)];base=load(R/'inputs'/n/'BASE_SELECTION.json');held=next(v['id']for v in c['views']if v['role']!='FIT');run=load(R/'metrics'/(n+'_RUN.json'));rgb(axs[0],n,base['primary']);axs[0].set_title(n+' '+kind+' raw RGB / Mask',fontsize=7);rgb(axs[1],n,base['primary'],['INITIAL']);axs[1].set_title('FIT initial C (blue)',fontsize=7);rgb(axs[2],n,base['primary'],['FINAL']);axs[2].set_title('FIT final (purple)',fontsize=7);rgb(axs[3],n,held,['INITIAL','FINAL']);axs[3].set_title('HOLDOUT initial/final\naccepted '+str(run['accepted_optimizer_steps'])+'/300',fontsize=7)
   for ax,tag,angle in zip(axs[4:],['INITIAL','FINAL','INITIAL','FINAL'],[(0,-65),(0,-65),(30,-65),(30,-65)]):meshpanel(ax,n,tag,angle);annotate(ax,n,tag)
 fig.suptitle('Nine corrected-C routes | initial vs final accepted state after 300 proposal iterations\nBlue initial / purple final; gray inferred closure excluded from observations; black fixed CAD, exact directed009 base\nSame frozen mm viewer within case; accepting few updates or retaining initial collisions is reported, not a scientific PASS.',fontsize=13);finish(fig,'Fig3_Nine_Optimization_Before_After.png')

def stages():
 fig=plt.figure(figsize=(24,15));gs=fig.add_gridspec(3,1,hspace=.2)
 for i,c in enumerate(['G01','G07','G06']):
  sub=gs[i].subgridspec(1,5,wspace=.05)
  for j,step in enumerate([0,60,180,300]):
   ax=fig.add_subplot(sub[0,j]);tag='INITIAL'if step==0 else'STEP_%04d'%step;z=model(c,tag);meshpanel(ax,c,tag);ax.set_title(c+' '+getcase(c)['morphology']+' | '+str(step)+' proposals\n'+('initial'if step==0 else str(z['accepted'])+' accepted / '+str(z['active_modes'])+' local modes'),fontsize=8)
  ax=fig.add_subplot(sub[0,4]);h=load(R/'metrics'/(c+'_TRAINING.json'));ax.plot([x['iteration']for x in h],[x['accepted_loss']for x in h],c='#a4519e',label='accepted full FIT loss');ax.set(xlabel='proposal iteration',ylabel='fixed objective');ax2=ax.twinx();ax2.plot([x['iteration']for x in h],[x['accepted_total']for x in h],c='#318ea4',label='accepted updates');ax2.set_ylabel('accepted count');ax.axvline(60,c='gray',ls=':');ax.axvline(180,c='gray',ls=':');ax.tick_params(labelsize=7);ax2.tick_params(labelsize=7)
 fig.suptitle('Fixed Ip/Is/IIa representatives: initialization -> restricted global -> low-frequency -> detail if eligible\nModes only release after pre-registered accepted-update gates. A flat accepted-count trace is stagnation, not hidden progress.\nActual meshes; no smoothing or viewpoint changes between stages.',fontsize=12);finish(fig,'Fig4_Low_to_High_Update_Process.png')

def draw_candidate(ax,c,V,F,flag,title,bound):
 rr=np.load(R/'inputs'/c/'RING.npz');colors=np.tile(matplotlib.colors.to_rgb(COL['FINAL']),(len(F),1));colors[flag]=[.65,.65,.65];im,s=actual_mesh_image(V,F,rr['V'],rr['F'],bound,20,-65,COL['FINAL'],colors);ax.imshow(im);K,T=viewer(c,(20,-65),bound);planeplot(ax,c,K,T);ax.plot([20,20+2*s],[375,375],c='black',lw=1.5);ax.text(20,365,'2 mm',fontsize=5);ax.axis('off');ax.set_title(title,fontsize=8)

def protection():
 selected=[];categories=[('Ring',lambda x:any('RING'in y or'CAD'in y for y in x['reasons'])),('Shape',lambda x:any(y in['NONADJACENT_SELF_INTERSECTION','FACE_ORIENTATION','AREA_DEGENERACY','BASE_HALFSPACE_OR_BOUNDARY','STEP_TRUST','TOTAL_TRUST']for y in x['reasons'])),('Objective',lambda x:'FULL_FIT_OBJECTIVE'in x['reasons'])]
 alltr=[]
 for c in load(R/'config/PROTOCOL.json')['cases']:
  ts=load(R/'metrics'/(c+'_CANDIDATES.json'));alltr.extend(ts)
 for category,predicate in categories:
  x=next((x for x in alltr if not x['accepted']and predicate(x)),None)
  if x:selected.append((category,x))
 fig,axs=plt.subplots(3,3,figsize=(16,15))
 for i in range(3):
  if i>=len(selected):
   for ax in axs[i]:ax.axis('off')
   axs[i,1].text(.5,.5,'No actual rejected candidate in this category\nPositive cap chart prevents underground structure by construction',ha='center',transform=axs[i,1].transAxes);continue
  category,x=selected[i];c=x['case'];chart=Chart(Case(c));z=model(c,'INITIAL');ts=load(R/'metrics'/(c+'_CANDIDATES.json'));previous=[t for t in ts if t['accepted']and t['iteration']<x['iteration']];qbefore=np.zeros(54)if not previous else np.array(previous[-1]['parameters']);accepted=next((t for t in ts if t['iteration']==x['iteration']and t['accepted']),None);qafter=qbefore if accepted is None else np.array(accepted['parameters']);V0=chart.vertices(tensor(qbefore,torch.float64)).detach().cpu().numpy();Vp=chart.vertices(tensor(np.array(x['parameters']),torch.float64)).detach().cpu().numpy();Va=chart.vertices(tensor(qafter,torch.float64)).detach().cpu().numpy();bb=np.r_[V0,Vp,Va,np.load(R/'inputs'/c/'RING.npz')['V']]
  for ax,V,title in zip(axs[i],[V0,Vp,Va],[c+' before proposal '+str(x['iteration']),category+' rejected: '+','.join(x['reasons'])+'\nalpha '+str(x['alpha'])+' / maxstep %.4fmm'%x['max_step_mm'],'After actual decision\n'+('accepted '+accepted['method']+' alpha '+str(accepted['alpha'])if accepted else'full rejection; parameters and moments restored')]):draw_candidate(ax,c,V,z['F_solid'],z['inferred_base_faces'],title,bb)
 fig.suptitle('Actual proposal/rollback evidence | first recorded Ring, shape and objective rejection categories\nReconstructed from immutable initial C, frozen spectral chart and recorded candidate parameters; no illustrative deformation\nAll three panels in a row share the same mm viewer, black CAD and directed base.',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig5_Geometry_Protection_and_Failures.png')

def details():
 for c in load(R/'config/PROTOCOL.json')['cases']:
  fig,axs=plt.subplots(3,4,figsize=(17,13));base=load(R/'inputs'/c/'BASE_SELECTION.json');held=next(v['id']for v in getcase(c)['views']if v['role']!='FIT');rgb(axs[0,0],c,base['primary'],['INITIAL','FINAL']);axs[0,0].set_title('FIT target lime / initial blue / final purple',fontsize=8);rgb(axs[0,1],c,held,['INITIAL','FINAL']);axs[0,1].set_title('HOLDOUT reprojection',fontsize=8)
  for ax,tag in zip(axs[0,2:],['INITIAL','FINAL']):meshpanel(ax,c,tag,(25,-65));annotate(ax,c,tag)
  for ax,tag in zip(axs[1],['INITIAL','STEP_0060','STEP_0180','FINAL']):meshpanel(ax,c,tag,(0,-65))
  for ax,tag in zip(axs[2,:3],['INITIAL','STEP_0180','FINAL']):meshpanel(ax,c,tag,(35,-65))
  run=load(R/'metrics'/(c+'_RUN.json'));a=summary(c,'INITIAL');b=summary(c,'FINAL');axs[2,3].axis('off');axs[2,3].text(0,.98,f"{c} | {getcase(c)['morphology']}\n{base['uncertainty_label']}\n\nProposals {run['outer_iterations']}\nAccepted {run['accepted_optimizer_steps']}\nAdam {run['Adam_committed_updates']}\nGradient restart {run['gradient_restart_updates']}\nLocal modes {run['final_active_modes']}\n\nFIT IoU {a['FIT_IoU']:.3f} -> {b['FIT_IoU']:.3f}\nHOLDOUT {a['HOLDOUT_IoU']:.3f} -> {b['HOLDOUT_IoU']:.3f}\nDepth fixed cost {a['FIT_raw_fixed_depth_cost']:.3f} -> {b['FIT_raw_fixed_depth_cost']:.3f}\n\nSelf {b.get('Blender_self_N')}\nBelow base {b['below_estimated_base_vertex_N']}\nReal 3D accuracy NOT_EVALUABLE",va='top',fontsize=9)
  fig.suptitle(c+' corrected C -> stable PyTorch3D | same mm frame and frozen viewer\nActual mesh stages; black CAD, gray inferred cap, no postprocess. Collisions and stagnation stay explicit.',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'full/'+c+'_Optimization_Detail.png')

def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN.json').exists();final_overview();stages();protection();details();print('FINAL_FIGURES_DONE')
if __name__=='__main__':main()
