from common017 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors
from scipy.ndimage import distance_transform_edt
SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py'
node=next(n for n in ast.parse(SRC.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='actual_mesh_image')
source=ast.get_source_segment(SRC.read_text(),node).replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]','rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]')
exec(compile(source,str(SRC)+':face_color_only_adapter','exec'),globals())
plt.rcParams.update({'font.size':8,'axes.titlesize':9})
COLORS=np.array([[.12,.72,.23],[.95,.75,.12],[.86,.1,.13],[.55,.55,.55]])
def evidence(r,rep='ARCHIVE_RAW'):return dict(np.load(R/'final_results'/r['source_id']/rep/'FACE_EVIDENCE.npz'))
def render(ax,a,r,bounds=None,angle=(22,-65),color='#809fb3',sel=None,fc=None,title=''):
    V,F=a['V'],a['F'];sel=np.ones(len(F),bool)if sel is None else sel;m=trimesh.load(r['ring'],process=False)
    if not sel.any():
        ax.text(.5,.5,'No faces selected\n(no fabricated result)',ha='center',va='center',transform=ax.transAxes);ax.axis('off');ax.set_title(title);return
    im,scale=actual_mesh_image(V,F[sel],m.vertices,m.faces,V[np.unique(F)] if bounds is None else bounds,*angle,color,None if fc is None else fc[sel]);ax.imshow(im);ax.plot([18,18+2*scale],[376,376],c='black',lw=2);ax.text(18,365,'2 mm at view centre',fontsize=6,color='black');ax.axis('off');ax.set_title(title)
def out(fig,name):
    p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=145,bbox_inches='tight');plt.close(fig)
def frame(ax,r,a=None):
    im=np.asarray(Image.open(r['RGB']));lab=np.asarray(Image.open(r['Mask']));ax.imshow(im)
    for mask,col in [(lab==1,'lime'),(lab==2,'cyan')]:
        cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
        for c in cs:ax.plot(c[:,0,0],c[:,0,1],c=col,lw=.7)
    if a is not None:
        cent=a['native_uv'][a['F']].mean(1);q=np.c_[cent,np.ones(len(cent))]@np.linalg.inv(np.array(r['Kn'])).T@np.array(r['K']).T;uv=q[:,:2]/q[:,2:]
        for state in [1,3,2]:
            idx=np.flatnonzero(a['state']==state);idx=idx[::max(1,len(idx)//1500)];ax.scatter(*uv[idx].T,s=1.5,c=[COLORS[state]],alpha=.7)
    ax.axis('off');ax.set_title(r['source_id']+'\nRGB + original Polyp/Ring Mask')
def heat(a,key,vmin,vmax,log=False,cmap='magma'):
    x=a[key];norm=colors.LogNorm(vmin,vmax)if log else colors.Normalize(vmin,vmax);rgb=plt.get_cmap(cmap)(norm(np.clip(x,vmin,vmax)))[:,:3];rgb[~np.isfinite(x)]=[.55,.55,.55];return rgb,plt.cm.ScalarMappable(norm=norm,cmap=cmap)
def main():
    rows=load(R/'config/SOURCE_LOCK.json');repids=['G01_004_new_r00','G03_key04_raw00554','G05_key04_raw00542','G06_004_ref04'];reps=[next(r for r in rows if r['source_id']==cid)for cid in repids]
    fig,axs=plt.subplots(4,4,figsize=(16,14))
    for i,r in enumerate(reps):
        a=evidence(r);frame(axs[i,0],r);render(axs[i,1],a,r,title='Original archived Raw | oblique');render(axs[i,2],a,r,angle=(5,0),title='Original archived Raw | world side');render(axs[i,3],a,r,fc=COLORS[a['state']],title='Internal reliability (not truth)')
    fig.suptitle('017 | Four physical groups, original HERO Raw Mesh surfaces | black fixed Ring CAD, millimetres\nGreen TRUSTED / yellow UNCERTAIN / red REJECTED / gray UNKNOWN; no coordinate change, fusion or smoothing',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);out(fig,'Fig1_Four_Group_Original_Geometry.png')
    keys=[('perspective_stretch',1,20,True),('tangent_stretch',1,10,True),('density_normalized',0,1.5,False),('normal_angle_deg',0,90,False),('CAD_min_signed_mm',-.1,.5,False)]
    fig,axs=plt.subplots(4,5,figsize=(19,14))
    for i,r in enumerate(reps):
        a=evidence(r)
        for j,(key,lo,hi,log)in enumerate(keys):
            fc,sm=heat(a,key,lo,hi,log,'coolwarm'if key.startswith('CAD')else'magma');render(axs[i,j],a,r,fc=fc,title=r['group']+' | '+key);fig.colorbar(sm,ax=axs[i,j],fraction=.025,pad=.01)
    fig.suptitle('Actual per-original-face evidence | gray = unavailable; indicators are correlated, not independent votes\nPerspective stretch alone confounds steep views; tangent correction is conditional. CAD proximity alone NEVER deletes.',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);out(fig,'Fig2_Internal_Geometric_Evidence.png')
    fig,axs=plt.subplots(4,3,figsize=(14,14))
    for i,r in enumerate(reps):
        a=evidence(r);frame(axs[i,0],r,a);render(axs[i,1],a,r,fc=COLORS[a['state']],title=r['source_id']+' | actual original archived faces');render(axs[i,2],a,r,angle=(5,0),fc=COLORS[a['state']],title='Side view | same face states')
    fig.suptitle('Reliability locations in RGB and true 3D | green trusted / yellow uncertain / red rejected / gray unknown\nTRUSTED = observation-supported internally ordinary, NOT certified physical surface. Unknown and uncertain are retained.',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);out(fig,'Fig3_Confidence_And_Source_Pixels.png')
    fig,axs=plt.subplots(4,4,figsize=(16,14))
    for i,r in enumerate(reps):
        a=evidence(r);keep=a['state']!=2;render(axs[i,0],a,r,title=r['source_id']+' | RAW');render(axs[i,1],a,r,sel=~keep,color='#df2020',title='Actually rejected original faces');render(axs[i,2],a,r,sel=keep,title='CLEANED | identical camera/bounds');render(axs[i,3],a,r,sel=keep,angle=(5,0),title='CLEANED | side view')
    fig.suptitle('Conservative cleaning | identical Raw-defined camera, physical scale and Ring CAD\nNo synthetic replacement for empty deletion. Retained XYZ and connectivity are original subsets; no filling or mesh smoothing.',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);out(fig,'Fig4_Before_Removed_After.png')
    # Every source gets all four requested figure classes, not just chosen previews.
    for r in rows:
        a=evidence(r);old=evidence(r,'ARCHIVE_RAW');keep=a['state']!=2
        fig,axs=plt.subplots(2,4,figsize=(16,8));frame(axs[0,0],r,a);render(axs[0,1],old,r,title='Archived original Raw (historical resize)');render(axs[0,2],a,r,title='Original Raw with frozen face IDs');render(axs[0,3],a,r,angle=(5,0),title='Original Raw side')
        render(axs[1,0],a,r,fc=COLORS[a['state']],title='Face-level confidence');render(axs[1,1],a,r,sel=~keep,color='red',title='Actually removed');render(axs[1,2],a,r,sel=keep,title='Retained original subset');render(axs[1,3],a,r,sel=keep,angle=(5,0),title='Retained side | same bounds')
        fig.suptitle(r['source_id']+' | original face and pixel IDs in FACE_EVIDENCE.npz / FACE_DECISIONS.csv.gz\nAll four requested views; black CAD, mm; archive and native are distinct topologies.');fig.tight_layout(rect=[0,0,1,.92]);out(fig,'full/'+r['source_id']+'_Geometry_Confidence_Cleanup.png')
        fig,axs=plt.subplots(2,3,figsize=(13,8))
        for ax,(key,lo,hi,log)in zip(axs.ravel(),keys+[('boundary_distance_native_px',0,10,False)]):
            fc,sm=heat(a,key,lo,hi,log);render(ax,a,r,fc=fc,title=key);fig.colorbar(sm,ax=ax,fraction=.025)
        fig.suptitle(r['source_id']+' | per-face internal evidence | gray unknown | mm / source-native pixels');fig.tight_layout(rect=[0,0,1,.94]);out(fig,'full/'+r['source_id']+'_Evidence.png')
    print('FOUR_CORE_AND_36_SOURCE_FIGURES',flush=True)
if __name__=='__main__':main()
