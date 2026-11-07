from common import *
from evaluate import pointcast
import ast,matplotlib
import open3d as o3d
matplotlib.use('Agg')
import matplotlib.pyplot as plt
SRC=R.parents[1]/'code/figures.py'
for node in ast.parse(SRC.read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['actual_mesh_image','edge']:
  source=ast.get_source_segment(SRC.read_text(),node)
  if node.name=='actual_mesh_image':source=source.replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]',"rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]")
  exec(compile(source,str(SRC)+':reuse','exec'),globals())
COL={'C011':'#2c9bce','FINAL011':'#dea937','FINAL012':'#b35aa5'}
def finish(fig,name,dpi=145):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def model(c,tag):
 p=R/'inputs'/c/('C_011.npz'if tag=='C011'else'INITIAL.npz')if tag in ['C011','FINAL011']else R/'local_results'/c/('FINAL.npz'if tag=='FINAL012'else tag+'.npz')
 return dict(np.load(p))
def bounds(c):
 rr=np.load(R/'inputs'/c/'RING.npz');arrays=[model(c,t)['V']for t in ['C011','FINAL011','FINAL012']];D=load(R/'inputs'/c/'CHART.json')['D_mm'];v=arrays[1];return np.r_[*arrays,rr['V'],[v.min(0)-.25*D,v.max(0)+.25*D]]
def project(P,K,T):
 X=(P-T[:3,3])@T[:3,:3];q=X@K.T;return q[:,:2]/q[:,2:]
def viewer(c,angle,bound=None):
 V=bounds(c)if bound is None else bound;rr=np.load(R/'inputs'/c/'RING.npz');v=np.r_[V,rr['V']];C=(v.min(0)+v.max(0))/2;rad=np.linalg.norm(v-C,axis=1).max();el,az=np.radians(angle);pos=C+3.4*rad*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);forward=(C-pos)/np.linalg.norm(C-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos;return np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]),T
def meshpanel(ax,c,tag,angle=(25,-65),title=None,bound=None):
 z=model(c,tag);rr=np.load(R/'inputs'/c/'RING.npz');F=z['F_solid'];col=COL.get(tag,COL['FINAL012']);colors=np.tile(matplotlib.colors.to_rgb(col),(len(F),1));colors[z['inferred_base_faces']]=[.65,.65,.65];im,scale=actual_mesh_image(z['V'],F,rr['V'],rr['F'],bounds(c)if bound is None else bound,*angle,col,colors);ax.imshow(im);ax.plot([20,20+2*scale],[375,375],c='black',lw=1.4);ax.text(20,365,'2 mm',fontsize=6);ax.set(xlim=(0,400),ylim=(400,0));ax.axis('off');ax.set_title(title or tag,fontsize=8)
def rgb(ax,c,cid,tags=None,crop=None):
 a=np.load(R/'inputs'/c/(cid+'.npz'));ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');rr=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(rr['V'],rr['F']),a['K'],a['T'],360,640)
 for tag in tags or []:
  z=model(c,tag);depth=cast(scene(z['V'],z['F']),a['K'],a['T'],360,640);edge(ax,np.isfinite(depth)&(depth<cz),COL.get(tag,COL['FINAL012']))
 ax.set(xlim=(0,640),ylim=(360,0));ax.axis('off')
 if crop is not None:x0,y0,x1,y1=crop;ax.set(xlim=(x0,x1),ylim=(y1,y0))
