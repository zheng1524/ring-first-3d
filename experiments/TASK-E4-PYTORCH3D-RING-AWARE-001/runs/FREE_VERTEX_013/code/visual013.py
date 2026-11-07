from common import *
from evaluate import distance,area_samples
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py'
for node in ast.parse(SRC.read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['actual_mesh_image','edge']:exec(compile(ast.get_source_segment(SRC.read_text(),node),str(SRC)+':reuse','exec'),globals())
COL={'011':'#c39742','012':'#5086bc','013':'#a652af'}
def finish(fig,name,dpi=130):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def zmodel(n,tag):
 if tag=='C':return dict(np.load(R/'inputs'/n/'C_011.npz'))
 if tag=='011':return dict(np.load(R/'inputs'/n/'INITIAL.npz'))
 if tag=='012':return dict(np.load(R.parent/'FREE_VERTEX_012/local_results'/n/'FINAL.npz'if n not in ['G10','G11']else R/'arms/REPLAY_012_FULL/local_results'/n/'FINAL.npz'))
 if tag=='013':return dict(np.load(R/'local_results'/n/'FINAL.npz'))
 return dict(np.load(R/'local_results'/n/(tag+'.npz')))
def bound(n):return np.r_[*[zmodel(n,t)['V']for t in ['011','012','013']],np.load(R/'inputs'/n/'RING.npz')['V']]
def panel(ax,n,tag,angle=(25,-65)):
 z=zmodel(n,tag);r=np.load(R/'inputs'/n/'RING.npz');im,sc=actual_mesh_image(z['V'],z.get('F_solid',z['F']),r['V'],r['F'],bound(n),*angle,COL.get(tag,'#a652af'));ax.imshow(im);ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm at viewer center',fontsize=5);ax.axis('off');ax.set_title(n+' '+tag,fontsize=8)
def rgb(ax,n,cid,tags=['011','012','013']):
 a=np.load(R/'inputs'/n/(cid+'.npz'));r=np.load(R/'inputs'/n/'RING.npz');cad=cast(scene(r['V'],r['F']),a['K'],a['T'],360,640);ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 for tag in tags:
  z=zmodel(n,tag);d=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(d)&(d<cad),COL.get(tag,'purple'))
 ax.axis('off');ax.set_title(cid+' raw Mask green',fontsize=7)
def overview():
 cases=load(R/'config/CASE_LOCK.json');fig,ax=plt.subplots(len(cases),5,figsize=(19,2.5*len(cases)))
 for i,c in enumerate(cases):
  n=c['name'];cid=next(v['id']for v in c['views']if v['role']=='FIT');rgb(ax[i,0],n,cid)
  for j,t in enumerate(['011','012','013'],1):panel(ax[i,j],n,t)
  panel(ax[i,4],n,'013',(0,-65))
 fig.suptitle('Eleven independent real physical groups | frozen 011 / 012 / 013 actual meshes\nSame per-case mm scale and viewer; no smoothing, trimming or inferred intermediate geometry. Black fixed CAD. New G10/G11: recipe-equivalent 011, new012 replication.');finish(fig,'Fig1_Eleven_Actual_Meshes.png')
def ip_review():
 fig,ax=plt.subplots(5,5,figsize=(22,19))
 for i,n in enumerate(['G01','G02','G03','G10','G11']):
  cid=next(v['id']for v in getcase(n)['views']if v['role']=='FIT');rgb(ax[i,0],n,cid)
  for j,t in enumerate(['011','012','013'],1):panel(ax[i,j],n,t,(0,-65))
  panel(ax[i,4],n,'013',(65,-90))
 fig.suptitle('Five Ip stalk review | no hard head/stalk partition in optimization\nGold011 / blue012 / purple013. Actual geometry; 2D contour agreement alone does not establish stalk direction.');finish(fig,'Fig2_Five_Ip_Stalk_Comparison.png')
def loss_and_mechanism():
 fig,axs=plt.subplots(4,4,figsize=(20,18));crops=[]
 for row,n in enumerate(['G03','G01','G02','G10']):
  cid=next(v['id']for v in getcase(n)['views']if v['role']=='FIT');a=np.load(R/'inputs'/n/(cid+'.npz'));rr=np.load(R/'inputs'/n/'RING.npz');cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640);z=zmodel(n,'011');pz=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);miss=(a['labels']==1)&~(np.isfinite(pz)&(pz<cz));axs[row,0].imshow(a['RGB']);axs[row,0].imshow(np.ma.masked_where(~miss,miss),cmap='Reds',alpha=.6);edge(axs[row,0],a['labels']==1,'lime');axs[row,0].set_title(n+' initial actual missed foreground');axs[row,0].axis('off')
  for loss in ['A0','A1','A2','A3']:
   p=R/'arms'/('PILOT_'+loss)/'metrics'/(n+'_TRAINING.json')
   if p.exists():h=load(p);axs[row,1].plot([x['attempt']for x in h],[x['loss']for x in h],label=loss);axs[row,2].plot([x['attempt']for x in h],[x['max_total_displacement_mm']for x in h],label=loss)
  axs[row,1].set_title('Own objective incl different losses');axs[row,2].set_title('Actual max displacement (mm)');axs[row,1].legend();axs[row,2].legend()
  mech=sorted((R/'local_results'/n).glob('MECHANISM_*.npz'))
  if mech:
   d=np.load(mech[0]);V=d['before_V'];P=(V-a['T'][:3,3])@a['T'][:3,:3];p=P@a['K'].T;uv=p[:,:2]/p[:,2:];keep=np.flatnonzero(np.linalg.norm(d['actual_vertex_delta'],axis=1)>0)[::8];W=V+d['actual_vertex_delta'];ww=(W-a['T'][:3,3])@a['T'][:3,:3]@a['K'].T;qw=ww[:,:2]/ww[:,2:];g=V-d['full_loss_gradient']*.02;gg=(g-a['T'][:3,3])@a['T'][:3,:3]@a['K'].T;ug=gg[:,:2]/gg[:,2:];ax=axs[row,3];ax.imshow(a['RGB']);ax.quiver(uv[keep,0],uv[keep,1],(qw-uv)[keep,0],(qw-uv)[keep,1],color='yellow',angles='xy',scale_units='xy',scale=1);ax.quiver(uv[keep,0],uv[keep,1],(ug-uv)[keep,0],(ug-uv)[keep,1],color='cyan',angles='xy',scale_units='xy',scale=1);ax.set_title('Yellow actual step; cyan -0.02 grad projection\nArrows true units, no decorative amplification');ax.axis('off')
 fig.suptitle('Fixed pilots and actual gradient/update mechanism | loss curves have different targets; use common FIT metrics to compare');finish(fig,'Fig3_Loss_Update_Mechanism.png')
def details():
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];fig,axs=plt.subplots(4,3,figsize=(14,16));fit=next(v['id']for v in c['views']if v['role']=='FIT');held=next(v['id']for v in c['views']if v['role']!='FIT')
  for j,t in enumerate(['011','012','013']):rgb(axs[0,j],n,fit,[t]);rgb(axs[1,j],n,held,[t]);panel(axs[2,j],n,t,(0,-65));panel(axs[3,j],n,t,(25,-65))
  fig.suptitle(n+' unchanged source camera reprojection / common-mm actual mesh');finish(fig,'full/'+n+'_Native_Detail.png')
if __name__=='__main__':overview();ip_review();loss_and_mechanism();details()
