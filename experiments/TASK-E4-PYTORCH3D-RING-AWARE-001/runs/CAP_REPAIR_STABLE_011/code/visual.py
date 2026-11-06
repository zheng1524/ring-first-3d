from common import *
from evaluate import pointcast
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
SRC=R.parents[1]/'code/figures.py';OLD=R.parent/'BODY_BASE_INIT_009'
for n in ast.parse(SRC.read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name in['actual_mesh_image','edge']:
  s=ast.get_source_segment(SRC.read_text(),n)
  if n.name=='actual_mesh_image':s=s.replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]',"rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]")
  exec(compile(s,str(SRC)+':reuse','exec'),globals())
COL={'B':'#348cc5','OLD_C':'#e3ad25','INITIAL':'#309aca','FINAL':'#b75bb2'}
def finish(fig,name,dpi=130):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def model(c,tag):
 p=OLD/'local_results'/c/('B_SELECTED.npz'if tag=='B'else'C_SELECTED.npz')if tag in['B','OLD_C']else R/'inputs'/c/'INITIAL.npz'if tag=='INITIAL'else R/'init_results'/c/'C_START.npz'if tag=='C_START'else R/'local_results'/c/(tag+'.npz');z=dict(np.load(p));z.setdefault('F_solid',z['F']);z.setdefault('inferred_base_faces',np.zeros(len(z['F_solid']),bool));return z

def bounds(c):
 arr=np.r_[model(c,'B')['V'],model(c,'OLD_C')['V'],model(c,'INITIAL')['V']];rr=np.load(R/'inputs'/c/'RING.npz');arr=np.r_[arr,rr['V']];lo=arr.min(0);hi=arr.max(0);D=float(np.ptp(model(c,'INITIAL')['V'],axis=0).max());iv=model(c,'INITIAL')['V'];return np.r_[arr,[iv.min(0)-.25*D,iv.max(0)+.25*D]]
def project(P,K,T):
 X=(P-T[:3,3])@T[:3,:3];q=X@K.T;return q[:,:2]/q[:,2:]
def viewer(c,angle,bound=None):
 V=bounds(c)if bound is None else bound;rr=np.load(R/'inputs'/c/'RING.npz');v=np.r_[V,rr['V']];C=(v.min(0)+v.max(0))/2;rad=np.linalg.norm(v-C,axis=1).max();el,az=np.radians(angle);pos=C+3.4*rad*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);forward=(C-pos)/np.linalg.norm(C-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos;return np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]),T

def planeplot(ax,c,K,T):
 p=np.array(load(R/'inputs'/c/'BASE_SELECTION.json')['selected_plane']);Q=np.array(load(OLD/'inputs'/c/'BASE.json')['plane_basis']);A=np.array(load(OLD/'inputs'/c/'BASE.json')['anchor']);span=max(3,min(20,np.ptp(bounds(c),axis=0).max()*.35));q=project(A+np.array([[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]])*span@Q[:,:2].T,K,T);ax.plot(q[:,0],q[:,1],'--',c='#1c9c99',lw=.7);a=project(np.array([A,A+p[:3]*1.]),K,T);ax.annotate('',xy=a[1],xytext=a[0],arrowprops=dict(arrowstyle='->',color='#1c9c99',lw=1));ax.text(a[1,0],a[1,1],'+n (1mm)',fontsize=5,color='#158480')
def meshpanel(ax,c,tag,angle=(20,-65),title=None,bound=None):
 z=model(c,tag);rr=np.load(R/'inputs'/c/'RING.npz');V=z['V'];F=z['F_solid'];col=COL.get(tag,COL['FINAL']);colors=np.tile(matplotlib.colors.to_rgb(col),(len(F),1));colors[z['inferred_base_faces']]=[.65,.65,.65]
 if tag=='B':
  p=np.array(load(OLD/'inputs'/c/'BASE.json')['plane']);colors[V[F].mean(1)@p[:3]+p[3]<0]=[.65,.65,.65]
 bb=bounds(c)if bound is None else bound;image,scale=actual_mesh_image(V,F,rr['V'],rr['F'],bb,*angle,col,colors);ax.imshow(image);K,T=viewer(c,angle,bb);planeplot(ax,c,K,T);ax.plot([20,20+2*scale],[375,375],c='black',lw=1.4);ax.text(20,365,'2 mm at viewer center',fontsize=5);ax.set(xlim=(0,400),ylim=(400,0));ax.axis('off');ax.set_title(title or tag,fontsize=7)

def rgb(ax,c,cid,tags=None):
 a=np.load(R/'inputs'/c/(cid+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 if tags:
  ring=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(ring['V'],ring['F']),a['K'],a['T'],360,640)
  for tag in tags:
   z=model(c,tag);dep=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(dep)&(dep<cz),COL.get(tag,COL['FINAL']))
 ax.set(xlim=(0,640),ylim=(360,0));ax.axis('off')

def initial_figures():
 cases=load(R/'config/CASE_LOCK.json');fig=plt.figure(figsize=(30,23));grid=fig.add_gridspec(3,3,hspace=.22,wspace=.05)
 for i,kind in enumerate(['Ip','Is','IIa']):
  for j,c in enumerate([c for c in cases if c['morphology']==kind]):
   n=c['name'];sub=grid[i,j].subgridspec(2,4,wspace=.02,hspace=.12);axes=[fig.add_subplot(sub[r,k])for r in range(2)for k in range(4)];b=load(R/'inputs'/n/'BASE_SELECTION.json');rgb(axes[0],n,b['primary'],['INITIAL']);axes[0].set_title(n+' '+kind+' RGB / Mask\n'+b['uncertainty_label'],fontsize=7)
   for ax,tag in zip(axes[1:4],['B','OLD_C','INITIAL']):meshpanel(ax,n,tag,title={'B':'009 B blue/gray','OLD_C':'009 frozen C','INITIAL':'011 corrected C'}[tag])
   for ax,tag in zip(axes[4:7],['B','OLD_C','INITIAL']):meshpanel(ax,n,tag,(0,-65),title=tag+' side')
   meshpanel(axes[7],n,'INITIAL',(35,-65),title='011 C oblique + directed base')
 fig.suptitle('Before PyTorch3D: nine-case B to C inheritance | no direct B clipping or sphere training\nB blue/gray uses EXACT 009 directed reference; old C yellow / corrected C blue / inferred closure gray\nExisting seven C meshes reused exactly; only rule-triggered untruncated C refit. Fixed mm bounds within case, black CAD.',fontsize=13);finish(fig,'Fig1_Nine_B_to_C_Initialization.png')
 fig,axs=plt.subplots(2,5,figsize=(22,10))
 for i,n in enumerate(['G05','G09']):
  b=load(R/'inputs'/n/'BASE_SELECTION.json');rgb(axs[i,0],n,b['primary']);e=np.load(R/'inputs'/n/'BASE_EVIDENCE.npz');a=np.load(R/'inputs'/n/(b['primary']+'.npz'));q=project(e['Polyp_internal_XYZ'],a['K'],a['T']);h=e['Polyp_internal_XYZ']@np.array(b['selected_plane'])[:3]+b['selected_plane'][3];sc=axs[i,0].scatter(q[:,0],q[:,1],s=.4,c=h,cmap='coolwarm',vmin=-.5,vmax=.5);fig.colorbar(sc,ax=axs[i,0],fraction=.03,label='HERO h vs009 base mm');axs[i,0].set_title(n+' original Polyp/Background evidence\n'+b['uncertainty_label'],fontsize=8)
  for j,tag in enumerate(['B','OLD_C','C_START','INITIAL']):meshpanel(axs[i,j+1],n,tag,(0,-65)if j<2 else(25,-65),title={'B':'009 directed blue/gray reference','OLD_C':'009 C kept underground ellipsoid','C_START':'B-blue initialized cap (not final clipping)','INITIAL':'011 parametric cap after fit'}[tag])
 fig.suptitle('G05/G09 required cap repair | exact 009 plane normal and offset, +n retained\nG05 stays UNCERTAIN_BASE, no 010 near-ROI plane substitution. G09 side inherited from B-blue, not near-zero HERO median.\nGray basal closure is inferred and excluded from all observations; no real 3D GT.',fontsize=12);fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Fig2_G05_G09_Cap_Repair.png')
 print('INITIAL_FIGURES_DONE')
if __name__=='__main__':initial_figures()
