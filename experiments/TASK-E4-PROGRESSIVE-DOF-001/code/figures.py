"""Four review figures from actual frozen SDF meshes; no geometry postprocessing."""
from model import *
from continuous import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt.rcParams.update({'font.size':8,'axes.titlesize':9})
def arr(p):return dict(np.load(p))
def meshplot(ax,V,F,cad,title,color='#519ac2',values=None):
    m=trimesh.Trimesh(V,F,process=False);shade=.65+.35*np.maximum(0,m.face_normals@np.array([.3,-.5,.8]));col=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))
    if values is not None:col=plt.get_cmap('coolwarm')((np.clip(np.asarray(values)[F].mean(1),-1,1)+1)/2)[:,:3]
    ax.add_collection3d(Poly3DCollection(V[F],facecolors=col*shade[:,None],edgecolors='none',rasterized=True));ax.add_collection3d(Poly3DCollection(cad['V'][cad['F']],facecolors=(.025,.025,.025),edgecolors='none',rasterized=True));ax.set(xlim=(-6.6,6.6),ylim=(-6.6,6.6),zlim=(-1,2.3),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=title);ax.set_box_aspect([13.2,13.2,3.3]);ax.view_init(27,-70);ax.grid(False);ax.tick_params(labelsize=6,pad=0)
def edge(ax,mask,color):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    for c in cs:ax.plot(c[:,0,0],c[:,0,1],color=color,lw=.9)
def savefig(fig,name):fig.savefig(R/'figures'/name,dpi=165,bbox_inches='tight',facecolor='white');plt.close(fig)
def main():
    post=load(R/'metrics/POSTERIOR.json');assert post['all_predictions_frozen_before_GT'];stages=post['stages'];renderer=Renderer();cad=arr(R/'inputs/RING_CAD.npz');gt=arr(post['GT_source']['path']);P0=arr(R/'local_results/P0/MODEL.npz');models=[('P0',P0)]+[(s,arr(R/'local_results'/s/'FINAL/MODEL.npz'))for s in stages];ends={x['name']:x for x in post['endpoints']};colors=['#8c969e','#428cbe','#db933d','#9767ba']
    fig,axs=plt.subplots(2,len(models)+1,figsize=(4*(len(models)+1),8),subplot_kw={'projection':'3d'})
    for j,(name,a)in enumerate([('Native CAD GT',gt)]+models):
        vol=trimesh.Trimesh(a['V'],a['F'],process=False).volume;label=name+f'\nraw Mesh volume {vol:.3f} mm3';color='#c98493'if j==0 else colors[j-1]
        for i in range(2):
            meshplot(axs[i,j],a['V'],a['F'],cad,label,color)
            if i==1:axs[i,j].view_init(15,-90);axs[i,j].set(xlim=(-3.9,3.9),ylim=(-3.9,3.9));axs[i,j].set_box_aspect([7.8,7.8,3.3])
    fig.suptitle('One progressive run | SAME native CAD, P0, mm coordinates and black Ring\nTop: common oblique camera; bottom: common 15-degree side close-up (Ring continues outside display crop); raw zero-set meshes, no smoothing',fontsize=11);fig.subplots_adjust(top=.84,wspace=.03,hspace=.24);savefig(fig,'Fig1_Actual_Progressive_Meshes.png')
    fig,axs=plt.subplots(5,len(models),figsize=(4*len(models),15));selection=load(R/'metrics/KERNEL_SELECTION.json')
    for i,c in enumerate(renderer.views):
        d=renderer.data[c['id']];rgb=d['target_rgb'];target=d['target'];ys,xs=np.nonzero(target);bg=np.full_like(rgb,235);bg[target]=[222,169,179];bg[rgb[:,:,1]>128]=[10,10,10]
        for j,(name,a)in enumerate(models):
            ax=axs[i,j];ax.imshow(bg);edge(ax,target,'#24be30');pred=renderer.project(scene(a['V'],a['F']),c['id'])[0];edge(ax,pred,colors[j]);met=subpixel_metrics(renderer,a['V'],a['F'],c['id']);ax.set(xlim=(xs.min()-20,xs.max()+20),ylim=(ys.max()+20,ys.min()-20),title=f'{c["id"].split("_")[-1]} {c["role"]} | {name}\nIoU {met["full_IoU"]:.4f}, p95 {met["subpixel_contour_px"]["p95"]:.2f}px');ax.set_aspect('equal');ax.tick_params(labelsize=6)
            if name=='S1'and selection['eligible']:
                for k,item in enumerate(selection['selected']):
                    if item['medoid']['view']!=c['id']:continue
                    p=np.array(item['medoid']['predicted_uv']);ax.plot(p[0],p[1],'x',c=['#007cc3','#d93131'][k],ms=7,mew=2);ax.text(p[0]+2,p[1],['E','S'][k],color=['#007cc3','#d93131'][k],fontsize=9)
    fig.suptitle('Fixed native Blender target labels (pink), GT contour green, frozen-stage prediction contours\nSame five cameras/native pixel coordinates; E/S crosses are predicted S1 residual medoids, NOT GT correspondences',fontsize=11);fig.tight_layout(rect=[0,0,1,.94]);savefig(fig,'Fig2_Five_View_Contours.png')
    rows=post['all_checkpoints'];fig,axs=plt.subplots(2,3,figsize=(15,8));xx=np.arange(len(rows));labels=[x['name']for x in rows]
    losses=[objective(Body(),renderer,np.array(x['q']),False)[0]for x in rows]
    axs[0,0].semilogy(xx,losses,'-o',ms=3,label='actual original Powell scalar');axs[0,0].set(title='Unchanged training objective',ylabel='loss')
    axs[0,1].plot(xx,[x['fit_IoU']for x in rows],'-o',ms=3,label='FIT');axs[0,1].plot(xx,[x['holdout_IoU']for x in rows],'--o',ms=3,label='HOLDOUT');axs[0,1].set(title='Fixed full Mask IoU',ylabel='IoU')
    axs[0,2].plot(xx,[x['Chamfer_mm']['MAE']for x in rows],'-o',ms=3,label='MAE');axs[0,2].plot(xx,[x['Chamfer_mm']['p95']for x in rows],'--o',ms=3,label='p95');axs[0,2].set(title='Post-freeze native GT geometry',ylabel='mm')
    axs[1,0].plot(xx,[x['volume']['symmetric_difference_mm3']for x in rows],'-o',ms=3,label='same fixed 2^19 Sobol queries');axs[1,0].set(title='3D symmetric-difference volume proxy',ylabel='mm3')
    axs[1,1].plot(xx,[x['volume']['GT_added_recovery']for x in rows],'-o',ms=3,label='added GT volume recovery');axs[1,1].plot(xx,[x['volume']['GT_removed_recovery']for x in rows],'--o',ms=3,label='removed GT volume recovery');axs[1,1].set(title='Both signs reported separately',ylabel='fraction')
    axs[1,2].plot(xx,[x['physical']['quality']['normal_angle_deg']['p95']for x in rows],'-o',ms=3,label='adjacent normal p95');axs[1,2].set(title='Raw Mesh roughness',ylabel='degrees')
    for ax in axs.ravel():
        for i,x in enumerate(rows):
            if x['name'].endswith('/START'):ax.axvline(i,c='k',ls=':',alpha=.3)
        ax.set_xticks(xx,labels,rotation=65,ha='right',fontsize=5);ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle('Saved last iterates only; no best-checkpoint selection | all GT metrics AFTER prediction freeze\nStage transitions repeat the previous final mesh; diagnostics never replace optimizer outputs',fontsize=11);fig.tight_layout(rect=[0,0,1,.92]);savefig(fig,'Fig3_Training_And_Independent_3D.png')
    body=Body();pairs=[('S1 global update',P0,models[1][1])]
    for stage in stages[1:]:pairs.append((stage+' local update at its fixed final global parameters',arr(R/'audit_only'/('COMPONENT_'+stage+'_GLOBAL_ONLY.npz')),arr(R/'local_results'/stage/'FINAL/MODEL.npz')))
    fig,axs=plt.subplots(len(pairs),3,figsize=(14,4*len(pairs)),subplot_kw={'projection':'3d'},squeeze=False);rtGT=scene(gt['V'],gt['F'])
    for i,(name,reference,changed)in enumerate(pairs):
        V,F=reference['V'],reference['F'];rt=scene(V,F);z=signed(rt,V);wanted=-signed(rtGT,V)+z;actual=-signed(scene(changed['V'],changed['F']),V)+z
        for j,(lab,value)in enumerate([('GT required change on reference',wanted),('Actual learned change on same reference',actual),('Remaining discrepancy (actual minus GT)',actual-wanted)]):
            meshplot(axs[i,j],V,F,cad,name+'\n'+lab,values=value)
            if i>0:
                cc=body.kernel_centers(np.asarray(changed['q']));axs[i,j].scatter(cc[:,0],cc[:,1],cc[:,2],c=['#147ac0','#c9252e'],s=25,depthshade=False)
    fig.suptitle('Eulerian distance-change diagnostics on the SAME reference surfaces; not material vertex motion\nRow 1 reference=P0; later reference=frozen stage global-only zero set. Actual output Meshes are in Fig1. Kernel centers blue E / red S',fontsize=11);fig.subplots_adjust(top=.82,bottom=.12,wspace=.04,hspace=.3);cb=fig.add_axes([.35,.035,.30,.018]);fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-1,1),cmap='coolwarm'),cax=cb,orientation='horizontal',label='mm: blue inward / red outward; displayed range +/-1mm');savefig(fig,'Fig4_Global_Local_Contributions.png');print('FOUR_PROGRESSIVE_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
