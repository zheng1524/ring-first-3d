"""Read-only reuse of existing real Mesh ray renderer. Static figures, no smoothing."""
from geometry_io import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colormaps
from matplotlib.colors import ListedColormap
SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py'
node=next(n for n in ast.parse(SRC.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='actual_mesh_image');source=ast.get_source_segment(SRC.read_text(),node).replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]','rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]');exec(compile(source,str(SRC)+':same019adapter','exec'),globals())
COLS={'004':'#3978b8','005':'#e59c30','PHOTO':'#ab42a2'}
def color(i):return matplotlib.colors.hsv_to_rgb([(i*.6180339887498949)%1,.65,.82])
def finish(fig,name):fig.savefig(N/'figures'/name,dpi=145,bbox_inches='tight');plt.close(fig)
def edges(ax,m,c):
 cs,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
 for cc in cs:ax.plot(cc[:,0,0],cc[:,0,1],c=c,lw=.7)
def bound_parts(ss,ring):return np.r_[ring['V'],*[s['V'][np.unique(s['F'])]for s in ss if len(s['F'])]]
def combine(parts):
 vs=[];fs=[];cs=[];off=0
 for V,F,c in parts:
  vs.append(V);fs.append(F+off);co=np.asarray(c);cs.append(np.tile(co,(len(F),1))if co.ndim==1 else co);off+=len(V)
 return np.concatenate(vs),np.concatenate(fs),np.concatenate(cs)
def panel(ax,parts,ring,bounds,title,angle=(25,-65)):
 if not parts:ax.text(.5,.5,'NOT AVAILABLE',ha='center');ax.axis('off');ax.set_title(title);return
 V,F,c=combine(parts);im,sc=actual_mesh_image(V,F,ring['V'],ring['F'],bounds,*angle,'#6c75be',c);ax.imshow(im);ax.plot([16,16+2*sc],[378,378],c='black',lw=2);ax.text(16,365,'2 mm at center depth',fontsize=6);ax.set_title(title,fontsize=9);ax.axis('off')
def parts(ss):return [(s['V'],s['F'],color(i))for i,s in enumerate(ss)]
