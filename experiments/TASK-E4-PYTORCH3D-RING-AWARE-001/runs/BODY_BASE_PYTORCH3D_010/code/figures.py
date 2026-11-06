"""Project renderer reuse; actual meshes and raw gradients, no geometry beautification."""
from common import *
from evaluate import pointcast
from clip_mesh import clip,basis
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
SRC=R.parents[1]/'code/figures.py'
for node in ast.parse(SRC.read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in['actual_mesh_image','edge']:
  s=ast.get_source_segment(SRC.read_text(),node)
  if node.name=='actual_mesh_image':s=s.replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]',"rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]")
  exec(compile(s,str(SRC)+':reuse','exec'),globals())
COL={'P':'#2787bd','S':'#e59c27','B':'#91979e'};MET=load(R/'metrics/ALL_STAGE_WITH_BLENDER.json');CACHE={};BOUNDS={}
def finish(fig,name,dpi=130):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def getmodel(c,tag):
 route=tag[0]
 if tag=='B':p=R/'inputs'/c/'B_UNCUT.npz';label='Frozen B (static)';key=('B','STATIC_B',0)
 elif tag in['P0','S0']:p=R/'inputs'/c/(route+'_INITIAL.npz');label=route+' initial';key=(route,'CHECKPOINT',0)
 elif tag.endswith('end'):
  run=load(R/'metrics'/(c+'_'+route+'_RUN.json'));folder=R/'local_results'/c/route
  if run['status']=='COMPLETED':p=folder/'FINAL.npz';label=route+' FINAL 300';key=(route,'FINAL',300)
  else:p=folder/'LAST_SAFE.npz';label=route+' STOP@'+str(run['optimizer_steps'])+' / safe@'+str(run['accepted_steps'])+'\nFINAL300 = NaN';key=(route,'LAST_SAFE',run['accepted_steps'])
 elif tag.endswith('unsafe'):
  p=R/'local_results'/c/route/'UNSAFE_CANDIDATE.npz';run=load(R/'metrics'/(c+'_'+route+'_RUN.json'));label=route+' UNSAFE @'+str(run['optimizer_steps']);key=(route,'UNSAFE_CANDIDATE',run['optimizer_steps'])
 else:
  step=int(tag[1:]);p=R/'local_results'/c/route/('STEP_%04d.npz'%step);label=route+' step '+str(step);key=(route,'CHECKPOINT',step)
 if not p.exists():return None,label,key
 return dict(np.load(p)),label,key

def bounds(c):
 if c not in BOUNDS:
  arr=[getmodel(c,t)[0]['V']for t in['B','P0','S0','Pend','Send']]
  for route in['P','S']:
   z,_,_=getmodel(c,route+'unsafe')
   if z is not None:arr.append(z['V'])
  BOUNDS[c]=np.concatenate(arr)
 return BOUNDS[c]
def viewer(V,RV,elev,azim):
 allv=np.r_[V,RV];C=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-C,axis=1).max();el,az=np.radians([elev,azim]);pos=C+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);forward=(C-pos)/np.linalg.norm(C-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos;return np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]),T

def project(P,K,T):
 X=(P-T[:3,3])@T[:3,:3];q=X@K.T;return q[:,:2]/q[:,2:]
def planeplot(ax,c,K,T):
 b=load(R/'inputs'/c/'BASE_SELECTION.json');p=b['selected_plane']
 if p is None:return
 p=np.array(p);norm=load(R/'inputs'/c/'NORMALIZATION.json');C=np.array(norm['center']);A=C-(C@p[:3]+p[3])*p[:3];Q=basis(p[:3]);span=max(3,min(20,np.ptp(bounds(c),axis=0).max()*.6));pts=A+np.array([[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]])*span@Q.T;q=project(pts,K,T);ax.plot(q[:,0],q[:,1],'--',c='#21a7b7',lw=.7)
def angle_near_reference(c):
 case=getcase(c);cid=load(R/'inputs'/c/'BASE_SELECTION.json')['primary'];a=np.load(R/'inputs'/c/(cid+'.npz'));rr=np.load(R/'inputs'/c/'RING.npz');A=np.r_[bounds(c),rr['V']];C=(A.min(0)+A.max(0))/2;d=a['T'][:3,3]-C;return(float(np.degrees(np.arcsin(d[2]/np.linalg.norm(d)))),float(np.degrees(np.arctan2(d[1],d[0]))))
def draw_geometry(ax,c,z,color,angle=(20,-65),face_colors=None):
 rr=np.load(R/'inputs'/c/'RING.npz');F=z['F_solid'];colors=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))if face_colors is None else face_colors.copy();colors[z.get('inferred_base_faces',np.zeros(len(F),bool))]=[.6,.6,.6];im,pxmm=actual_mesh_image(z['V'],F,rr['V'],rr['F'],bounds(c),*angle,color,colors);K,T=viewer(bounds(c),rr['V'],*angle);ax.imshow(im);planeplot(ax,c,K,T);ax.plot([20,20+2*pxmm],[375,375],c='black',lw=1.5);ax.text(20,365,'2 mm (viewer-center)',fontsize=5);ax.set(xlim=(0,400),ylim=(400,0));ax.axis('off');return K,T

def panel(ax,c,tag,angle=(20,-65),title=True):
 z,label,key=getmodel(c,tag)
 if z is None:ax.axis('off');ax.text(.5,.5,label+'\nNOT REACHED / no final substitute',ha='center',va='center',transform=ax.transAxes,fontsize=8,color='red');return
 cache=(c,tag,angle)
 if cache not in CACHE:
  rr=np.load(R/'inputs'/c/'RING.npz');F=z['F_solid'];color=COL['B'if tag=='B'else tag[0]];colors=np.tile(matplotlib.colors.to_rgb(color),(len(F),1));colors[z['inferred_base_faces']]=[.6,.6,.6];im,pxmm=actual_mesh_image(z['V'],F,rr['V'],rr['F'],bounds(c),*angle,color,colors);K,T=viewer(bounds(c),rr['V'],*angle);CACHE[cache]=(im,pxmm,K,T)
 im,pxmm,K,T=CACHE[cache];ax.imshow(im);planeplot(ax,c,K,T);ax.plot([20,20+2*pxmm],[375,375],c='black',lw=1.5);ax.text(20,365,'2 mm (viewer-center)',fontsize=5);ax.set(xlim=(0,400),ylim=(400,0));ax.axis('off');q=next((x for x in MET if(x['case'],x['route'],x['label'],x['step'])==(c,*key)),None)
 if q is not None:ax.text(.01,.99,'CAD '+str(q['Blender_Ring_pair_N'])+' / self '+str(q['Blender_nonadjacent_self_pair_N'])+' / below '+str(q['below_estimated_base_vertex_N']),transform=ax.transAxes,va='top',fontsize=5,color='red'if q['Ring_surface_collision']or(q['Blender_nonadjacent_self_pair_N']or 0)>0 else'dimgray')
 if title:ax.set_title(label,fontsize=8,color='red'if'STOP'in label or'UNSAFE'in label else'black')

def rgb(ax,c,cid,overlays=False):
 a=np.load(R/'inputs'/c/(cid+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 if overlays:
  rr=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640)
  for tag in['Pend','Send']:
   z,_,_=getmodel(c,tag);zz=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(zz)&(zz<cz),COL[tag[0]])
 ax.set(xlim=(0,640),ylim=(360,0));ax.axis('off')
def overview():
 fig=plt.figure(figsize=(29,21));grid=fig.add_gridspec(3,3,hspace=.23,wspace=.08);cases=load(R/'config/CASE_LOCK.json')
 for row,t in enumerate(['Ip','Is','IIa']):
  for col,c in enumerate([x for x in cases if x['morphology']==t]):
   n=c['name'];sub=grid[row,col].subgridspec(2,3,wspace=.03,hspace=.16);axs=[fig.add_subplot(sub[i,j])for i in range(2)for j in range(3)];b=load(R/'inputs'/n/'BASE_SELECTION.json');rgb(axs[0],n,b['primary']);axs[0].set_title(n+' | '+t+' real RGB / original Mask\nbase '+b['base_status']+' / contact '+b['contact_status'],fontsize=8)
   for ax,tag in zip(axs[1:],['B','P0','S0','Pend','Send']):panel(ax,n,tag)
 fig.suptitle('Nine real physical groups | same cameras, Masks, native HERO, Ring-Aware and 100global+200local schedule\nP fitted-body clipping vs S official ico_sphere | blue P / orange S / gray inferred cap, never observed\nSTOP panels show last-safe DIAGNOSTIC only: FINAL300 is NaN. Black solid CAD; one common mm viewer per case, including unsafe candidate bounds.',fontsize=13);finish(fig,'Fig1_Nine_Case_Overview.png')

def detail(c):
 fig,axs=plt.subplots(4,4,figsize=(17,16));angles=[angle_near_reference(c),(0,-65),(28,-65)]
 for i,angle in enumerate(angles):
  for j,tag in enumerate(['P0','S0','Pend','Send']):panel(axs[i,j],c,tag,angle);axs[i,j].set_title(['Near original camera direction','World side','Oblique'][i]+' | '+axs[i,j].get_title(),fontsize=8,color=axs[i,j].title.get_color())
 case=getcase(c);b=load(R/'inputs'/c/'BASE_SELECTION.json');cid=b['primary'];held=next(x['id']for x in case['views']if x['role']!='FIT');rgb(axs[3,0],c,cid,True);axs[3,0].set_title(cid+' FIT | lime target / blue P / orange S',fontsize=8);rgb(axs[3,1],c,held,True);axs[3,1].set_title(held+' UPDATE_HOLDOUT\nstopped = diagnostic only',fontsize=8)
 for j,route in enumerate(['P','S']):
  z,_,_=getmodel(c,route+'unsafe')
  if z is not None:panel(axs[3,j+2],c,route+'unsafe')
  else:
   run=load(R/'metrics'/(c+'_'+route+'_RUN.json'));axs[3,j+2].axis('off');axs[3,j+2].text(0,.9,f"{route}: {run['status']}\noptimizer updates {run['optimizer_steps']}\naccepted {run['accepted_steps']}\nNo unsafe proposal\n\nBase {b['base_status']}\nROI 5-{b['selected_ROI_upper_px']}px\nCAD/self/folds remain explicit\nReal 3D accuracy NOT_EVALUABLE",va='top',fontsize=10)
 fig.suptitle(c+' | '+case['morphology']+' | shared physical bounds across all panels, no post smoothing or surface removal\nGray inferred cap excluded from silhouette/depth losses. Cyan plane is estimated tissue base, not Ring plane.\nNonzero CAD/self counts remain failures; no real GT.',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'full/'+c+'_Detailed.png')

def clip_core():
 fig,axs=plt.subplots(2,4,figsize=(18,9))
 for i,c in enumerate(['G05','G09']):
  bs=load(R/'inputs'/c/'BASE_SELECTION.json');plane=np.array(bs['selected_plane']);B=getmodel(c,'B')[0];P=getmodel(c,'P0')[0];lower=clip(B['V'],B['F'],-plane);V=np.r_[P['V'],lower['V']];F=np.r_[P['F'],lower['F']+len(P['V'])];colors=np.r_[np.tile(matplotlib.colors.to_rgb(COL['P']),(len(P['F']),1)),np.tile([.65,.65,.65],(len(lower['F']),1))];z=dict(V=V,F_solid=F,inferred_base_faces=np.zeros(len(F),bool));draw_geometry(axs[i,0],c,z,COL['P'],(0,-65),colors);axs[i,0].set_title(c+' exact B split: blue retained / gray removed\nNO upper-body refit',fontsize=9);panel(axs[i,1],c,'P0',(0,-65));axs[i,1].set_title('Exact clipped P initial; gray cap inferred\n'+bs['base_status']+' / 5-'+str(bs['selected_ROI_upper_px'])+'px ROI',fontsize=9);panel(axs[i,2],c,'P0',(30,-65));rgb(axs[i,3],c,bs['primary']);e=np.load(R/'inputs'/c/'BASE_EVIDENCE.npz');q=e['background_RGB_uv'];q=q[:,:2]/q[:,2:];axs[i,3].scatter(q[:,0],q[:,1],s=.25,c='#109cb3',alpha=.4);axs[i,3].set_title('Original RGB / Mask / real background samples\nnormal %.3f -> %.3f deg'%(bs['previous_normal_change_deg'],bs['max_normal_change_deg']),fontsize=9)
 fig.suptitle('Geometric clipping audit G05/G09 | preserved original upper vertices are bitwise unchanged\nG05 remains WEAK; G09 sign-equivalence repaired to 3.958 deg. Black CAD, shared mm viewer. No cap is observed tissue.',fontsize=12);fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig2_G05_G09_Exact_Clipping.png')

def progression():
 fig=plt.figure(figsize=(22,16));grid=fig.add_gridspec(3,1,hspace=.2)
 for i,c in enumerate(['G01','G07','G06']):
  sub=grid[i].subgridspec(2,5,hspace=.03,wspace=.03)
  for j,route in enumerate(['P','S']):
   for k,step in enumerate([0,50,100,200,300]):
    ax=fig.add_subplot(sub[j,k]);tag=route+'0'if step==0 else route+'end'if step==300 else route+str(step);panel(ax,c,tag);ax.set_title(c+' '+getcase(c)['morphology']+' | '+ax.get_title(),fontsize=8,color=ax.title.get_color())
 fig.suptitle('Fixed representative cases and planned stages 0 / 50 / 100 / 200 / 300\nNOT REACHED means no output; STOP last-safe is explicitly diagnostic and does not substitute for FINAL300\nSame mm viewer and black CAD within each case. Exact initial caps remain gray and are excluded from all observation losses.',fontsize=12);finish(fig,'Fig3_Representative_Progression.png')

def mechanism():
 fig,axs=plt.subplots(3,4,figsize=(20,13))
 for row,c in enumerate(['G01','G07','G06']):
  case=getcase(c);cid=load(R/'inputs'/c/'BASE_SELECTION.json')['primary'];a=np.load(R/'inputs'/c/(cid+'.npz'));o=np.load(R/'depth_observations'/(cid+'.npz'));folder=R/'local_results'/c/'P';step=50 if(folder/'MECHANISM_0050.npz').exists()else 1;z=np.load(folder/('MECHANISM_%04d.npz'%step));before=z['before_V'];F=z['F'];d=z['actual_displacement_mm'];q=project(before,a['K'],a['T']);after=project(before+d,a['K'],a['T']);rgb(axs[row,0],c,cid);rr=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640);dep=cast(scene(before,F),a['K'],a['T'],360,640);pred=np.isfinite(dep)&(dep<cz);edge(axs[row,0],pred,COL['P']);miss=(a['labels']==1)&~pred;outside=pred&(a['labels']==0);color=np.zeros((360,640,4));color[miss]=[0,.3,1,.4];color[outside]=[1,0,0,.5];axs[row,0].imshow(color);axs[row,0].set_title(c+' P step '+str(step)+' before update\nblue missing / red outside',fontsize=9)
  rgb(axs[row,1],c,cid);X=(np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];uv,_,zh=pointcast(scene(before,F),X,o['K'],o['T']);valid=np.isfinite(zh);sc=axs[row,1].scatter(o['RGB_uv'][valid,0],o['RGB_uv'][valid,1],c=(zh-o['z'])[valid],s=7,cmap='coolwarm',vmin=-2,vmax=2);axs[row,1].scatter(o['RGB_uv'][~valid,0],o['RGB_uv'][~valid,1],s=8,facecolors='none',edgecolors='orange');fig.colorbar(sc,ax=axs[row,1],fraction=.03,label='pred-HERO axial mm');axs[row,1].set_title('Fixed original HERO IDs / first layer residual\norange unhit, not zero-filled',fontsize=9)
  rgb(axs[row,2],c,cid);cam=(before-a['T'][:3,3])@a['T'][:3,:3];_,_,hit=pointcast(scene(before,F),before,a['K'],a['T']);vis=(cam[:,2]>0)&(q[:,0]>=0)&(q[:,0]<640)&(q[:,1]>=0)&(q[:,1]<360)&(abs(cam[:,2]-hit)<.05);ids=np.flatnonzero(vis)[::max(1,int(vis.sum())//80)];axs[row,2].quiver(q[ids,0],q[ids,1],after[ids,0]-q[ids,0],after[ids,1]-q[ids,1],angles='xy',scale_units='xy',scale=1,color='#e34324',width=.003);axs[row,2].set_title('Actual optimizer displacement, true pixel arrows\nmax %.3f mm; momentum + GLOBAL6 Jacobian'%np.linalg.norm(d,axis=1).max(),fontsize=9)
  rows=[x for x in load(R/'metrics/LOSS_GRADIENT_MECHANISM.json')if x['case']==c and x['route']=='P'];axs[row,3].plot([x['step']for x in rows],[x['silhouette_gradient_norm_per_mm']for x in rows],'-o',label='silhouette spatial gradient');axs[row,3].plot([x['step']for x in rows],[x['absolute_gradient_norm_per_mm']+x['relative_gradient_norm_per_mm']for x in rows],'-s',label='abs+relative norms');axs[row,3].set(xlabel='actual saved iteration',ylabel='gradient norm per mm',title='Raw loss gradients are not SGD displacement');axs[row,3].legend(fontsize=7);axs[row,3].tick_params(labelsize=8)
 fig.suptitle('Actual contour/depth evidence and executed geometry updates | fixed representative cases\nLoss gradients are recorded before global/cap parameter Jacobian; displacement includes SGD momentum. No illustrative arrows, no GT.',fontsize=12);fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig4_Observation_Update_Mechanism.png')

def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN.json').exists();overview();clip_core();progression();mechanism()
 for c in load(R/'config/PROTOCOL.json')['cases']:detail(c)
 save('assets_index/VISUALIZATION_SOURCE.json',dict(renderer=asset(SRC),functions=['actual_mesh_image','edge'],changes='face colors and annotations only; true meshes unchanged',common_bounds='union B/P0/S0/final or last-safe and unsafe per case; fixed mm camera for comparison',stopped_panels='diagnostic last-safe, explicit FINAL300 NaN',inferred_cap_color='gray',core_representatives=['G01','G07','G06'],exact_clip_representatives=['G05','G09'],real_GT_read=False));print('FIGURES_DONE')
if __name__=='__main__':main()
