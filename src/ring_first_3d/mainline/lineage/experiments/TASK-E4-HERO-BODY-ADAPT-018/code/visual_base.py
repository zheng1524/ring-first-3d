from common import *
import ast,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py'
for node in ast.parse(SRC.read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['actual_mesh_image','edge']:
  source=ast.get_source_segment(SRC.read_text(),node)
  if node.name=='actual_mesh_image':source=source.replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]','rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]')
  exec(compile(source,str(SRC)+':direct_reuse','exec'),globals())
def finish(fig,name,dpi=135):
 p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def model_panel(ax,name,z,bounds,angle=(25,-65),color='#7b59ac',face_colors=None):
 r=np.load(R/'inputs'/name/'RING.npz');F=z.get('F_solid',z['F']);fc=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))if face_colors is None else face_colors.copy();fc[z.get('inferred_base_faces',np.zeros(len(F),bool))]=[.65,.65,.65];im,sc=actual_mesh_image(z['V'],F,r['V'],r['F'],bounds,*angle,color,fc);ax.imshow(im);ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm at viewer center',fontsize=6);ax.axis('off')
