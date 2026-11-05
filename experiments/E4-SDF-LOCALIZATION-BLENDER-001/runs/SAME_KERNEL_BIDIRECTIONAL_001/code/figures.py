"""Paired evidence from actual DMTet meshes and frozen Blender masks."""
from pathlib import Path
import os,sys,json
PAIR=Path(__file__).resolve().parents[1];(PAIR/'runtime/mpl').mkdir(parents=True,exist_ok=True);(PAIR/'figures/full').mkdir(parents=True,exist_ok=True);os.environ['MPLCONFIGDIR']=str(PAIR/'runtime/mpl');sys.dont_write_bytecode=True
import numpy as np,cv2,trimesh,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import LineCollection
from PIL import Image
plt.rcParams.update({'font.size':8,'axes.titlesize':10})
CASES=['A_expansion','B_contraction']
def load(p):return json.loads(Path(p).read_text())
def arrays(p):return dict(np.load(p))
def meshplot(ax,V,F,cad,title,color='#5796bd',values=None,facecolors=None):
    m=trimesh.Trimesh(V,F,process=False);shade=.65+.35*np.maximum(0,m.face_normals@np.array([.3,-.5,.8]));col=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))
    if values is not None:col=plt.get_cmap('coolwarm')(np.clip((np.asarray(values)[F].mean(1)+.6)/1.2,0,1))[:,:3]
    if facecolors is not None:col=facecolors
    ax.add_collection3d(Poly3DCollection(V[F],facecolors=col*shade[:,None],edgecolors='none',linewidth=0,rasterized=True));ax.add_collection3d(Poly3DCollection(cad['V'][cad['F']],facecolors=(.03,.03,.03),edgecolors='none',linewidth=0,rasterized=True));ax.set(xlim=(-6.6,6.6),ylim=(-6.6,6.6),zlim=(-.5,2.2),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=title);ax.set_box_aspect([13.2,13.2,2.7]);ax.view_init(27,-70);ax.grid(False);ax.tick_params(labelsize=6,pad=0)
def lines(ax,mask,col,known):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);seg=[]
    for c in cs:
        co=c[:,0]
        for a,b in zip(co,np.roll(co,-1,axis=0)):
            if known[a[1],a[0]]and known[b[1],b[0]]:seg.append([a,b])
    ax.add_collection(LineCollection(seg,colors=col,linewidths=1.1))
def save(fig,name):fig.savefig(PAIR/'figures'/name,dpi=165,bbox_inches='tight',facecolor='white');plt.close(fig)
def main():
    info={}
    for name in CASES:
        r=PAIR/'cases'/name;assert (r/'metrics/PREDICTION_FREEZE.json').exists();info[name]=dict(r=r,e=load(r/'metrics/GEOMETRY_EVALUATION.json'),diag=load(r/'metrics/GT_OBJECTIVE_DIAGNOSTIC.json'),vol=load(r/'metrics/VOLUME_VALIDATION.json'),gt=arrays(r/'audit_only/TARGET_GT.npz'),init=arrays(r/'local_results/INITIAL/MODEL.npz'),final=arrays(r/'local_results/FINAL/MODEL.npz'),cad=arrays(r/'inputs/RING_CAD.npz'))
    fig,axs=plt.subplots(2,3,figsize=(14,8),subplot_kw={'projection':'3d'})
    for i,name in enumerate(CASES):
        d=info[name];label='A: expansion'if i==0 else'B: contraction'
        for j,(key,title)in enumerate([('init','INITIAL'),('gt','GT, same kernel/grid/DMTet'),('final','FINAL recovery')]):
            m=d[key];v=trimesh.Trimesh(m['V'],m['F'],process=False).volume;meshplot(axs[i,j],m['V'],m['F'],d['cad'],f'{label} | {title}\nActual volume {v:.4f} mm3',color=['#9da6ad','#d68c99','#549dc7'][j])
    fig.suptitle('Same-kernel symmetric controls | Actual initial / GT / recovered DMTet meshes\nBlack = identical Ring CAD; same metric camera/scale; no smoothing or geometry cleanup',fontsize=12);fig.subplots_adjust(top=.86,hspace=.35,wspace=.08);save(fig,'Fig1_Paired_Actual_Meshes.png')
    cams=load(info[CASES[0]]['r']/'inputs/CAMERAS.json');fig,axs=plt.subplots(5,4,figsize=(15,15))
    for i,c in enumerate(cams):
        for k,name in enumerate(CASES):
            r=info[name]['r'];rgb=np.asarray(Image.open(r/'inputs'/('TARGET__'+c['id']+'.png')).convert('RGB'));target=(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1]);ring=rgb[:,:,1]>128;bg=np.full_like(rgb,235);bg[target]=[226,169,178];bg[ring]=[15,15,15];ys,xs=np.nonzero(target)
            for j,st in enumerate(['INITIAL','FINAL']):
                a=arrays(r/'audit_only'/(st+'__'+c['id']+'_PROJECTION.npz'));ax=axs[i,2*k+j];ax.imshow(bg);lines(ax,target,'#23c744',a['known']);lines(ax,a['pred'],'#166fdf'if st=='FINAL'else'#c033b5',a['known']);ax.set(xlim=(xs.min()-15,xs.max()+15),ylim=(ys.max()+15,ys.min()-15),title=f'{name} | {st}\n{c["id"].split("_")[-1]} | {c["role"]}');ax.set_aspect('equal');ax.tick_params(labelsize=6)
    fig.suptitle('Native Blender target masks, identical cameras | green target / magenta initial / blue final\nDisplay crop only; no K/c2w/crop-map changes; CAD/Ring UNKNOWN omitted symmetrically from contour loss',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);save(fig,'Fig2_Paired_Five_View_Contours.png')
    fig,axs=plt.subplots(2,3,figsize=(15,8),subplot_kw={'projection':'3d'})
    for i,name in enumerate(CASES):
        d=info[name];a=arrays(d['r']/'audit_only/FINAL_SURFACE.npz');V=a['V'];F=a['F'];label='A expansion'if i==0 else'B contraction'
        meshplot(axs[i,0],V,F,d['cad'],label+' | GT geometric displacement',values=a['GT']);meshplot(axs[i,1],V,F,d['cad'],label+' | actual predicted displacement',values=a['pred'])
        colors=np.tile([.76,.76,.76],(len(F),1));g=a['GT_changed'][F].sum(1)>=2;p=a['pred_changed'][F].sum(1)>=2;colors[g]=[.9,.22,.25];colors[p]=[.2,.4,.9];colors[g&p]=[.65,.2,.75];meshplot(axs[i,2],V,F,d['cad'],label+' | actual changed-region overlap\nred GT / blue prediction / purple common',facecolors=colors)
    for ax in axs[:,:2].ravel():fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-.6,.6),cmap='coolwarm'),ax=ax,shrink=.42,pad=.12,label='mm: +outward / -inward')
    fig.suptitle('Same geometric operator on the common INITIAL DMTet surface\nMaps are correspondence references, not replacement meshes; actual surfaces are in Fig1',fontsize=12);fig.subplots_adjust(top=.86,hspace=.35,wspace=.12);save(fig,'Fig3_Paired_GT_vs_Predicted_Regions.png')
    fig,axs=plt.subplots(2,5,figsize=(21,8))
    for i,name in enumerate(CASES):
        d=info[name];rows=d['e']['stages'];xx=np.arange(len(rows));labels=[x['stage']for x in rows];ax=axs[i]
        ax[0].plot(xx,[x['parameter_center_error_mm']for x in rows],'-o',ms=3,label='center 3D error');ax[0].plot(xx,[abs(x['center_Z_error_mm'])if x['center_Z_error_mm']is not None else None for x in rows],'-o',ms=3,label='|Z error|');ax[0].axhline(.5,c='r',ls='--',label='0.5 mm gate');ax[0].set(ylabel='mm',title=name+' | center error')
        ax[1].plot(xx,[x['fit_IoU']for x in rows],'-o',ms=3,label='FIT');ax[1].plot(xx,[x['holdout_IoU']for x in rows],'-o',ms=3,label='HOLDOUT');ax[1].set(title='Full visible Mask IoU')
        ax[2].plot(xx,[x['GT_region_error_mm']['MAE']for x in rows],'-o',ms=3,label='GT-region MAE');ax[2].plot(xx,[x['non_target_motion_mm']['maximum']for x in rows],'-o',ms=3,label='non-target max');ax[2].plot(xx,[x['non_target_motion_mm']['p95']for x in rows],'-o',ms=3,label='non-target p95');ax[2].set(title='Physical geometric errors',ylabel='mm')
        ax[3].plot(xx,[x['quality']['normal_angle_deg']['p95']for x in rows],'-o',ms=3,label='adjacent-normal p95');ax[3].set(title='Actual Mesh roughness',ylabel='degrees')
        ax[4].plot(xx,[x['objective']for x in rows],'-o',ms=3,label='actual objective');ax[4].axhline(d['diag']['GT_loss'],c='black',ls='--',label='GT parameters, post-freeze');ax[4].set(title='Unchanged loss and GT diagnostic')
        for a in ax:
            a.grid(alpha=.2);a.set_xticks(xx,labels,rotation=45,ha='right',fontsize=6);a.legend(fontsize=6)
    fig.suptitle('Fixed two-run comparison | GT measurements and GT loss evaluated only after prediction freeze\nNo GT restart, radius search, optimizer change, best-checkpoint selection or added cases',fontsize=12);fig.tight_layout(rect=[0,0,1,.93]);save(fig,'Fig4_Paired_Roundwise_Diagnostics.png');print('PAIRED_FOUR_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
