"""Actual cached RGB and actual frozen meshes, no smoothing or chosen winner."""
from visual_base import *
import matplotlib.colors as mcolors
for node in ast.parse((R/'code/figures_body_alignment.py').read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['camera','render','show']:exec(compile(ast.Module(body=[node],type_ignores=[]),'direct013_body_renderer','exec'),globals())
TAGS=['S0','S8','S16','S32'];ANGLES=[(89.999,0),(-89.999,0),(0,0),(0,90),(0,180),(0,270)]
def z(n,t):return dict(np.load(R/'arms'/t/'local_results'/n/'FINAL.npz'))
def overlay(ax,n,cid,tag=None):
 if cid is None:ax.axis('off');ax.text(.5,.5,'HOLDOUT NOT AVAILABLE',ha='center');return
 a=np.load(R/'inputs'/n/(cid+'.npz'));rg=np.load(R/'inputs'/n/'RING.npz');cad=np.load(R/'runtime/cad_depth'/(cid+'.npz'))['z'];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 if tag:
  m=z(n,tag);d=cast(scene(m['V'],m['F']),a['K'],a['T'],360,640);p=np.isfinite(d)&(d<cad);edge(ax,p,'gold');rgba=np.zeros((360,640,4));rgba[(a['labels']==1)&~p]=[.1,.25,1,.55];rgba[(a['labels']==0)&p]=[1,.1,.04,.55];ax.imshow(rgba);rr=next(v for v in load(R/'metrics/PER_VIEW_METRICS.json')if v['case']==n and v['tag']==tag and v['view']==cid);text=f"{tag} IoU={rr['IoU']:.3f} FN={rr['FN']} FP={rr['FP']}"
 else:text='RGB/observed Mask'
 ax.set_title(n+' '+cid+'\n'+text,fontsize=7);ax.axis('off')
def native():
 cases=load(R/'config/CASE_LOCK.json');reps=load(R/'config/REPRESENTATIVE_VIEWS.json');fig,aa=plt.subplots(11,5,figsize=(21,28))
 for row,c in enumerate(cases):
  n=c['name'];cid=reps[n]['HOLDOUT']or reps[n]['FIT'];overlay(aa[row,0],n,cid)
  for j,t in enumerate(TAGS,1):overlay(aa[row,j],n,cid,t)
  f,ax=plt.subplots(2,5,figsize=(20,9))
  for i,role in enumerate(['FIT','HOLDOUT']):
   cid=reps[n][role];overlay(ax[i,0],n,cid)
   for j,t in enumerate(TAGS,1):overlay(ax[i,j],n,cid,t)
  f.suptitle(n+' fixed original013 FIT / Mesh-update HOLDOUT | common native pixels\nGreen observed Polyp, cyan observed Ring, gold model, blue miss, red known-background extra. No frame selection by output.');finish(f,'details/'+n+'_FIT_HOLDOUT_Contours.png')
 fig.suptitle('Fig1 | Same-video, same HOLDOUT camera: S0 / S8 / S16 / S32 actual reprojections\nFixed original013 representative frames; blue missing Polyp, red extra known background. HOLDOUT is for Mesh updates, not end-to-end camera certification.');finish(fig,'Fig1_All_Groups_Native_Contours.png')
def bodies():
 cases=load(R/'config/CASE_LOCK.json');geo={(v['case'],v['label']):v for v in load(R/'metrics/GEOMETRY_AUDIT.json')};fig,aa=plt.subplots(11,5,figsize=(21,28));ringfig,ra=plt.subplots(11,4,figsize=(18,27))
 for i,c in enumerate(cases):
  n=c['name'];initial=dict(np.load(R/'inputs'/n/'INITIAL.npz'));mm=[initial]+[z(n,t)for t in TAGS];bound=np.concatenate([m['V']for m in mm]+[np.load(R/'inputs'/n/'RING.npz')['V']])
  for j,(t,m)in enumerate(zip(['INITIAL']+TAGS,mm)):model_panel(aa[i,j],n,m,bound);aa[i,j].set_title(n+' '+t,fontsize=8)
  f,ax=plt.subplots(5,6,figsize=(22,17))
  for row,(t,m)in enumerate(zip(['INITIAL']+TAGS,mm)):
   for col,angle in enumerate(ANGLES):model_panel(ax[row,col],n,m,bound,angle);ax[row,col].set_title(n+' '+t+' '+['+Z','-Z','+X','+Y','-X','-Y'][col],fontsize=8)
  f.suptitle(n+' actual world-mm meshes, six fixed directions; black CAD, gray inferred cap\nSame extent and scale for every arm. No smoothing, clipping or synthetic stalk.');finish(f,'details/'+n+'_World_Six_Views.png')
  for j,t in enumerate(TAGS):
   m=z(n,t);sd=np.load(R/'local_results/dense_ring'/(n+'_'+t+'_FACE_SIGNED.npz'))['signed_distance_mm'];colors=np.tile([.55,.36,.7],(len(sd),1));colors[sd<0]=[1,.12,.04];model_panel(ra[i,j],n,m,bound,face_colors=colors);q=geo[n,t];ra[i,j].set_title(n+' '+t+f" dense={q['Ring_dense_penetration_mm']:.6f}mm\nsparse pass={q['old_sparse_nonworsening_vs_initial']}",fontsize=7)
 fig.suptitle('Fig2 | Identical013 INITIAL -> S0 / S8 / S16 / S32, one shared body per condition\nBlack frozen Ring CAD; actual world-mm geometry and flat face shading. Original9 exact011; G10/11 frozen013 recipe-equivalent initialization.');finish(fig,'Fig2_All_Groups_Actual_Meshes.png');ringfig.suptitle('Independent64-sample Ring audit, never an optimization guard\nRed face has at least one negative CAD-material sample; not the whole triangle. Do not equate old sparsePASS with no penetration.');finish(ringfig,'details/Independent_Dense_Ring_Evidence.png')
def curves():
 rows=load(R/'metrics/CASE_ARM_METRICS.json');cases=load(R/'config/CASE_LOCK.json');by={(v['case'],v['arm']):v for v in rows};fig,aa=plt.subplots(6,4,figsize=(21,21),layout='constrained');ymax=max(1.5,max((v['Chamfer_MAE_mm']for v in rows if v['Chamfer_MAE_mm']is not None),default=0)*1.05)
 for i,c in enumerate(cases):
  n=c['name'];a,b=aa[i//2,(i%2)*2:(i%2)*2+2];q=[by[n,t]for t in TAGS];a.plot(range(4),[x['FIT_IoU']for x in q],'o-',label='common FIT');a.plot(range(4),[x['HOLDOUT_IoU']for x in q],'s--',label='HOLDOUT');a.set_ylim(0,1);a.set_ylabel('Native Mask IoU',fontsize=8);a.set_title(n+' N='+','.join(str(x['actual_FIT_N'])for x in q)+' | span='+','.join(f"{x['max_direction_span_deg']:.1f}"for x in q)+' deg',fontsize=7);a.legend(fontsize=6);b.plot(range(4),[x['Chamfer_MAE_mm']for x in q],'x:',c='red');b.set_ylim(0,ymax);b.set_ylabel('Best-rigid Chamfer (mm)',fontsize=8);b.set_title(n+f" 32-S0={q[-1]['Chamfer_MAE_mm']-q[0]['Chamfer_MAE_mm']:+.5f} mm",fontsize=8)
  for p in [a,b]:p.set_xticks(range(4),TAGS);p.grid(alpha=.15)
 for a in aa[-1,2:]:a.axis('off')
 fig.suptitle('Fig3 | Single-video view-count comparison: fixed evaluation pool and actual direction span\nShared absolute3D axis; GT used only after all44 predictions/scale freeze. 013 loss keeps1/Nfit depth normalization.',fontsize=12);finish(fig,'Fig3_View_Count_2D_3D.png')
def aligned():
 rows=load(R/'metrics/BLENDER_METRICS.json');by={(v['case'],v['label']):v for v in rows};fig,aa=plt.subplots(11,5,figsize=(21,29))
 for i,c in enumerate(load(R/'config/CASE_LOCK.json')):
  n=c['name'];g=dict(np.load(R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'));ms=[dict(np.load(R/'local_results/aligned'/n/(t+'.npz')))for t in TAGS];bounds=np.concatenate([g['V']]+[m['V']for m in ms]);show(aa[i,0],g['V'],g['F'],bounds,(20,-65),n+' original Blender body',body_color='#8d9299')
  for j,(t,m)in enumerate(zip(TAGS,ms),1):q=by[n,t];show(aa[i,j],m['V'],m['F'],bounds,(20,-65),n+' '+t+f" CD={q['Chamfer_MAE_mm']:.3f} / DxyAE={q['Dxy_AE_mm']:.3f}mm",g)
 fig.suptitle('Fig4 | After Ring-based Metric Recovery and Best 6-DoF Rigid Alignment\nGT gray, predictions purple; same013/014 evaluator. No scale fitting, mirror, nonrigid registration or mesh postprocessing. Not end-to-end pose accuracy.');finish(fig,'Fig4_Blender_Best_Rigid_Comparison.png')
def main():
 assert(R/'provenance/EVALUATION_COMPLETE.json').exists();print('FIG native',flush=True);native();print('FIG meshes',flush=True);bodies();print('FIG curves',flush=True);curves();print('FIG GT',flush=True);aligned()
if __name__=='__main__':main()
