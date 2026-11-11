"""Six real-data failure figures. No simulated optimized camera or convergence plot."""
from geometric import *
from visual_base import plt,edge
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def finish(fig,n):
 fig.savefig(M/'figures'/n,dpi=135,bbox_inches='tight');plt.close(fig)
def main():
 vv=load(M/'config/VIEWS.json');jac=load(M/'metrics/JACOBIAN_VALIDATION.json');diag=load(M/'metrics/FAILURE_BRANCH_ISOLATION.json');switch=load(M/'metrics/CAD_VISIBILITY_SWITCH_CAUSES.json');score=load(M/'metrics/FOUR_GROUP_POSE_OPTIMIZATION_SCORECARD.json');base=load(M/'metrics/ALL_VIDEO_P0_METRICS.json');groups=load(P/'config/FOUR_GROUP_INPUTS.json')
 fig,axs=plt.subplots(2,3,figsize=(17,9))
 for i,g in enumerate(GROUPS):
  xs=[.001,.0001,.00001];ys=[max(r['relative_Frobenius']for r in jac if r['group']==g and r['part']=='outer'and r['h']==h)for h in xs];axs[0,0].loglog(xs,ys,'o-',label=g)
 axs[0,0].axhline(.001,c='red',ls='--',label='frozen local-J tolerance');axs[0,0].invert_xaxis();axs[0,0].set(xlabel='normalized finite-difference step',ylabel='Outer J relative Frobenius error',title='Outer residual: branch switches at finite steps');axs[0,0].legend(fontsize=7)
 for part in ['inner','outer','SIFT','prior','all']:
  ys=[max(r['relative_Frobenius']for r in jac if r['part']==part and r['h']==h)for h in [.001,.0001,.00001]];axs[0,1].loglog([.001,.0001,.00001],ys,'o-',label=part)
 axs[0,1].invert_xaxis();axs[0,1].legend(fontsize=7);axs[0,1].set(xlabel='normalized step',ylabel='max relative error over4groups/2states',title='At1e-5 local AD and FD converge')
 rr=[r for r in diag if r['group']=='G05'and r['point']=='zero'and r['h']==.0001];x=np.arange(6)
 for off,kk,label in [(-.25,'AD_objective','local AD'),(0,'local_fixed_edge_FD','FD fixed correspondence'),(.25,'full_visible_edges_recomputed_FD','FD recomputed visible edges')]:
  y=[r[kk]if kk=='AD_objective'else r['objective_FD']['all'][kk]for r in rr];axs[0,2].bar(x+off,y,.25,label=label)
 axs[0,2].set(xticks=x,xticklabels=['tx','ty','tz','rx','ry','rz'],title='G05 actual objective: tx derivative changes sign',ylabel='dL/d normalized camera coordinate');axs[0,2].legend(fontsize=6)
 pts=load(M/'metrics/CLAMP_TRANSITION_NATIVE_OBSERVATIONS.json');counts=[sum(r['group']==g for r in pts)for g in GROUPS];axs[1,0].bar(GROUPS,counts);axs[1,0].set(title='Observed points crossing segment-foot clamp',ylabel='registered1e-4 diagnostic rows (not unique anatomy)')
 axs[1,1].axis('off');axs[1,1].text(.02,.95,'Implemented: real CAD edge residual + RGB SIFT\nfloat64 SE(3) and exact forward-mode AD\nSciPy bounded TRF wrapper available\n\nFormal optimizer calls: 0\nDerived final camera poses: 0\nStage B photo optimization: NOT RUN\n\nNo LM convergence curve is shown,\nbecause preflight failed before formal solving.',va='top',fontsize=11)
 axs[1,2].axis('off');axs[1,2].text(.02,.95,'PAUSED_FOR_HUMAN_DIAGNOSIS\n\nLocal-J numerical gate failed at1e-4.\nAt1e-5 all local tests pass,\nbut actual CAD visibility/type switching\ncan change the objective direction.\n\nData-only rank6 in4 representative views\nis not evidence of stable global refinement.\nNo old result is relabeled as P1.',va='top',fontsize=11)
 fig.suptitle('Figure1 | Actual geometric Jacobian and objective diagnosis — cameras remain frozen\nOnly original Ring CAD, real masks and real SIFT. No HERO/body/GT enters the residual.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Figure1_Geometric_Jacobian_and_Stop.png')
 for k,g in enumerate(GROUPS):
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');a=np.load(v['cache']);C=np.array(v['T']);K=np.array(v['K']);gr=next(r for r in groups if r['group']==g);cad=CADCurves(gr['ring']['path']);ec=np.load(M/'evaluation'/(v['id']+'.npz'));row=next(r for r in base if r['id']==v['id']);cs=next(r for r in score if r['group']==g);fig,axs=plt.subplots(2,3,figsize=(18,9));ax=axs[0,0];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');edge(ax,ec['ring_pred'],'black');ax.axis('off');ax.set_title(g+' '+v['id']+' | unchanged P0\nrealPolyp green / Ring cyan / actualCAD black')
  ax=axs[0,1];ax.imshow(a['RGB']);r=load(M/'inputs'/v['id']/'RGB_GEOMETRY.json');ms=[z for z in r['matches']if z['role']=='FEATURE_HELD'];ms=ms[np.linspace(0,len(ms)-1,min(40,len(ms)),dtype=int)].tolist()if isinstance(ms,np.ndarray)else[ms[i]for i in np.linspace(0,len(ms)-1,min(40,len(ms)),dtype=int)]if ms else[]
  for m in ms:
   u=projection(np.array(m['X'])[None],C,K)[0][0];o=np.array(m['uv']);ax.scatter(*o,c='lime',s=7);ax.scatter(*u,c='red',marker='x',s=10);ax.annotate('',xy=u,xytext=o,arrowprops=dict(arrowstyle='->',lw=.6,color='yellow'))
  ax.axis('off');ax.set_title('Real unused-for-pose SIFT track observations\nobserved green / fixed-map projection red / residual yellow')
  axs[0,2].remove();ax=fig.add_subplot(2,3,3,projection='3d');b=np.load(gr['bodies']['B2']['path']);ax.add_collection3d(Poly3DCollection(cad.V[cad.F],facecolors='black',edgecolors='none'));ax.add_collection3d(Poly3DCollection(b['V'][b['F']],facecolors='#7464b0',alpha=.35,edgecolors='none'));cams=np.array([r['T']for r in vv if r['group']==g]);points=np.r_[cad.V,b['V'],cams[:,:3,3]]
  for vid,col in [('004','tab:blue'),('005','tab:orange')]:
   cv=[r for r in vv if r['group']==g and r['video']==vid];ps=np.array([r['T']for r in cv]);
   if len(ps):ax.plot(*ps[:,:3,3].T,'.-',ms=3,c=col,label=vid+' P0');ax.quiver(*ps[0,:3,3],*(ps[0,:3,2]*3),color=col)
  lo,hi=points.min(0),points.max(0);ax.set(xlim=(lo[0]-1,hi[0]+1),ylim=(lo[1]-1,hi[1]+1),zlim=(lo[2]-1,hi[2]+1),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title='Frozen metric scene; 018body context only\nNo derived optimized camera exists');ax.set_box_aspect(hi-lo+2);ax.view_init(20,-65);ax.legend(fontsize=6)
  ax=axs[1,0];ax.imshow(a['RGB']);p=Problem([v]);ev=p.rings[0]
  for key,col in [('inner','cyan'),('outer','orange')]:ax.scatter(ev[key][:,0],ev[key][:,1],c=col,s=4)
  for r in pts:
   if r['group']==g:ax.scatter(*r['uv'],edgecolors='red',s=65,facecolors='none')
  ed=next(r for r in switch if r['group']==g)
  for e in ed['changed_edges']:
   uv=projection(np.array(e['XYZ_mm']),canon_np(C),K)[0];ax.plot(*uv.T,c='red',lw=1.5)
  ax.axis('off');ax.set_title('Actual supported I/O samples; red: switching CAD edges\nred circles: observed segment-clamp transitions')
  ax=axs[1,1];rr=[r for r in diag if r['group']==g and r['point']=='zero'and r['h']==.0001];x=np.arange(6)
  for off,key,label in [(-.25,'AD_objective','AD local'),(0,'nearest_reassociate_same_visible_edges_FD','FD fixed visible set'),(.25,'full_visible_edges_recomputed_FD','FD full visibility')]:ax.bar(x+off,[r[key]if key=='AD_objective'else r['objective_FD']['all'][key]for r in rr],.25,label=label)
  ax.set(xticks=x,xticklabels=['tx','ty','tz','rx','ry','rz'],ylabel='dL/d normalized coordinate',title='Same original data, h=1e-4; no pose accepted');ax.legend(fontsize=6)
  ax=axs[1,2];ax.axis('off');ax.text(.01,.98,f"Canonical video views: {cs['target_video_views_N']}\nFIT / protected HOLDOUT: {cs['FIT_N']} / {cs['HOLDOUT_N']}\nRepresentative originalRing IoU: {row['P0_Ring_known_Mask_IoU']:.4f}\nInner MAE / P95: {row['P0_inner_px']['MAE']:.3f} / {row['P0_inner_px']['p95']:.3f} px\nOuter MAE / P95: {row['P0_outer_px']['MAE']:.3f} / {row['P0_outer_px']['p95']:.3f} px\n\nP1: NOT_RUN_JACOBIAN_GATE\nOptimized pose correction: NaN\nFull-group refinement success: NOT TESTED\n\nFigures show existing geometry and actual\nfinite-difference probes only.\nHERO / body never used in camera fitting.",va='top',fontsize=10)
  fig.suptitle(f'Figure{k+2} | {g} real projection and geometric preflight evidence — formal refinement stopped\nP0 is original frozen camera; no fabricated before/after result.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,f'Figure{k+2}_{g}_Real_Geometric_Failure_Evidence.png')
 fig,axs=plt.subplots(2,3,figsize=(16,8));x=np.arange(4)
 for off,role,col in [(-.2,'FIT','tab:blue'),(.2,'HOLDOUT','tab:orange')]:axs[0,0].bar(x+off,[r[role+'_P0_Ring_IoU']for r in score],.4,label=role,color=col)
 axs[0,0].set(xticks=x,xticklabels=GROUPS,title='P0 Ring IoU; no optimizedP1 columns',ylabel='knownMask IoU');axs[0,0].legend()
 for off,key in [(-.2,'Inner'),(.2,'Outer')]:axs[0,1].bar(x+off,[r['FIT_P0_'+key+'_MAE_px']for r in score],.4,label=key)
 axs[0,1].set(xticks=x,xticklabels=GROUPS,title='P0 FIT observed Ring boundary error',ylabel='640x360 pixel MAE');axs[0,1].legend()
 axs[0,2].bar(GROUPS,[r['P0_HERO_MAE_mm']for r in score]);axs[0,2].set(title='P0 frozen native HERO known-set depth proxy',ylabel='mm; no camera/body/GT update')
 for i,g in enumerate(GROUPS):
  rr=[r for r in jac if r['group']==g and r['h']==.0001];axs[1,0].bar(i,sum(not r['pass_all6']for r in rr))
 axs[1,0].set(xticks=x,xticklabels=GROUPS,title='Failed1e-4 Jacobian block tests',ylabel='over2states x5components')
 axs[1,1].bar(GROUPS,[r['target_video_views_N']for r in score]);axs[1,1].set(title='All98 canonical input views audited',ylabel='video views; aliases not duplicated')
 axs[1,2].axis('off');axs[1,2].text(.02,.95,'Four-group formal refinements: 0/4\nP1 derived camera outputs: 0/98\nHistorical measurement fallback: 0\nPhoto-stage runs: 0/12\n\nP1 accuracy and gains remain NaN.\nNo selected successful group is substituted.\n\nPAUSED_FOR_HUMAN_DIAGNOSIS',va='top',fontsize=12)
 fig.suptitle('Figure6 | Complete four-group P0 inventory and explicit missing P1 outcomes\nNo GT, no photo extension, no silent replacement with historical improved poses.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Figure6_Four_Group_Scorecard_and_Not_Run.png');save('runtime/FIGURES_COMPLETE.json',dict(epoch=time.time(),core_figures=6,stage_B_figures='NOT_RUN_STAGE_A_GATE'));print('SIX_REAL_DIAGNOSTIC_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
