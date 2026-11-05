"""Actual native CAD, actual frozen predictions and read-only audit data."""
from continuous import *
from model import Body
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import LineCollection
plt.rcParams.update({'font.size':8,'axes.titlesize':9})
def arr(p):return dict(np.load(p))
def draw(ax,V,F,cad,title,color='#519ac2',values=None):
    m=trimesh.Trimesh(V,F,process=False);shade=.65+.35*np.maximum(0,m.face_normals@np.array([.3,-.5,.8]));col=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))
    if values is not None:col=plt.get_cmap('coolwarm')((np.clip(np.asarray(values)[F].mean(1),-.5,.5)+.5))[:,:3]
    ax.add_collection3d(Poly3DCollection(V[F],facecolors=col*shade[:,None],edgecolors='none',rasterized=True));ax.add_collection3d(Poly3DCollection(cad['V'][cad['F']],facecolors=(.025,.025,.025),edgecolors='none',rasterized=True));ax.set(xlim=(-6.6,6.6),ylim=(-6.6,6.6),zlim=(-.5,2.3),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=title);ax.set_box_aspect([13.2,13.2,2.8]);ax.view_init(27,-70);ax.grid(False);ax.tick_params(labelsize=6,pad=0)
def edges(ax,mask,color):
    co,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    for c in co:ax.plot(c[:,0,0],c[:,0,1],c=color,lw=.8)
def savefig(fig,name):fig.savefig(R/'figures'/name,dpi=165,bbox_inches='tight',facecolor='white');plt.close(fig)
def main():
    assert load(R/'metrics/NATIVE_POSTERIOR.json')['all_predictions_frozen']
    body=Body();renderer=Renderer();cad=arr(R/'inputs/RING_CAD.npz');base=arr(R/'inputs/BASE_SOURCE_MESH.npz');gt=arr(R/'audit_only/NATIVE_CAD_GT.npz');arms=['ORIGINAL','SUBPIXEL_TARGET'];final={a:arr(R/'local_results'/a/'FINAL/MODEL.npz')for a in arms};metrics=load(R/'metrics/NATIVE_POSTERIOR.json')
    fig,axs=plt.subplots(5,4,figsize=(14,14))
    for i,c in enumerate(renderer.views):
        d=renderer.data[c['id']];rgb=d['target_rgb'];target=d['target'];ys,xs=np.nonzero(target)
        for j,(name,data)in enumerate([('Native Blender label target',None),('Independent P0',base),('Original objective FINAL',final[arms[0]]),('Subpixel target FINAL',final[arms[1]])]):
            ax=axs[i,j];bg=np.full_like(rgb,235);bg[target]=[220,165,175];bg[rgb[:,:,1]>128]=[15,15,15];ax.imshow(bg);edges(ax,target,'#25bd31')
            if data is not None:
                pred=renderer.project(scene(data['V'],data['F']),c['id'])[0];edges(ax,pred,'#166ad1');m=subpixel_metrics(renderer,data['V'],data['F'],c['id']);name+=f'\nIoU {m["full_IoU"]:.4f}, p95 {m["subpixel_contour_px"]["p95"]:.2f}px'
            ax.set(xlim=(xs.min()-20,xs.max()+20),ylim=(ys.max()+20,ys.min()-20),title=f'{c["id"].split("_")[-1]} {c["role"]}\n{name}');ax.set_aspect('equal');ax.tick_params(labelsize=5)
    fig.suptitle('Native CAD N0 ONLY | green target / blue prediction | fixed cameras and native pixel coordinates\nActual Blender labels, not clinical photographs; identical display crop; no geometric postprocessing',fontsize=11);fig.tight_layout(rect=[0,0,1,.95]);savefig(fig,'Fig1_Native_Five_View_Results.png')
    ob=load(R/'metrics/OBSERVABILITY.json');loc=ob['locations'][1];fig=plt.figure(figsize=(15,8));ax=fig.add_subplot(231)
    aa=arr(R/'audit_only/MASK_seed_JACOBIAN.npz')
    for key,lab in [('J_epsilon','eps .02'),('J_half','eps .01')]:ax.semilogy(np.arange(1,5),np.linalg.svd(aa[key]*aa['D'],compute_uv=False),'-o',label=lab)
    ax.set(title=f'Physical-column whitened SVD\nrelative J difference {loc["epsilon_relative_J_difference"]:.3f}: NOT STABLE',xlabel='singular index',ylabel='px/noise per mm physical mode');ax.legend();ax.grid(alpha=.2)
    ax=fig.add_subplot(232);modes=ob['perturbations'];xx=np.arange(4);ax.bar(xx,[x['achieved_displacement_mm']['maximum']for x in modes]);ax.axhline(.3,c='r',ls='--');ax.set_xticks(xx,[x['mode']for x in modes],rotation=25,ha='right');ax.set(title='Actual controlled mode amplitudes\nBound-limited responses retained',ylabel='mm max on fixed P0 reference')
    ax=fig.add_subplot(233)
    for x in modes:
        ax.plot(np.arange(5),[p['Mask_mutual_IoU']for p in x['per_view']],'-o',label=x['mode'],ms=3)
    ax.set_xticks(np.arange(5),['00 H','01 F','03 F','04 H','05 F']);ax.set(title='Seed vs mode: mutual Mask IoU',ylabel='IoU');ax.legend(fontsize=6);ax.grid(alpha=.2)
    seedq=np.array(load(R/'metrics/MASK_ONLY_INITIALIZATION.json')['q']);V,F=body.mesh(seedq)
    seed_scene=scene(V,F)
    for j,(name,data)in enumerate([('MASK-only seed',dict(V=V,F=F)),('Weak negative',arr(R/'local_results/A2_weak_minus/MODEL.npz')),('Weak positive',arr(R/'local_results/A2_weak_plus/MODEL.npz'))]):
        ax=fig.add_subplot(2,3,j+4,projection='3d');draw(ax,data['V'],data['F'],cad,name+' | body close-up',values=signed(seed_scene,data['V'])if j else None);ax.set(xlim=(-3.4,3.4),ylim=(-3.4,3.4),zlim=(-.1,2.3));ax.set_box_aspect([6.8,6.8,2.4])
        ax.text2D(.02,.02,'Color: current surface distance to seed\nred outward / blue inward; Ring extends beyond crop',transform=ax.transAxes,fontsize=7)
    fig.suptitle('Fixed-index residual observability | P0 amplitude zero has three exact center-null parameters\nLocal SVD and weak-mode responses do not prove global ambiguity; some requested 0.2--0.5mm modes unavailable at sampled endpoints',fontsize=11);fig.tight_layout(rect=[0,0,1,.92]);savefig(fig,'Fig2_Observability_And_Actual_Modes.png')
    fig,axs=plt.subplots(2,4,figsize=(16,8),subplot_kw={'projection':'3d'})
    names=[('Independent P0',base),('Unmodified native CAD GT',gt),('Original FINAL',final[arms[0]]),('Subpixel target FINAL',final[arms[1]])]
    for j,(name,a)in enumerate(names):
        dm=trimesh.Trimesh(a['V'],a['F'],process=False).volume;draw(axs[0,j],a['V'],a['F'],cad,name+f'\nvolume {dm:.3f} mm3',color='#c88596'if j==1 else'#519ac2')
    rtGT=scene(gt['V'],gt['F']);rt0=scene(base['V'],base['F']);ref=signed(rt0,base['V']);dGT=-signed(rtGT,base['V'])+ref
    draw(axs[1,0],base['V'],base['F'],cad,'Native GT required change on fixed P0',values=dGT)
    draw(axs[1,1],gt['V'],gt['F'],cad,'Native GT: exact source triangles retained',color='#c88596')
    for j,arm in enumerate(arms):
        a=arr(R/'audit_only'/f'{arm}_FINAL_ERRORS.npz');draw(axs[1,j+2],a['V0'],a['F0'],cad,arm+' actual Eulerian change',values=a['pred_Eulerian'])
    fig.suptitle('Actual meshes in identical mm coordinates / black Ring CAD\nLower-row scalar maps use the SAME initial surface and SAME signed-distance-change operator (+outward / -inward, fixed +/-0.5mm color range)',fontsize=11);fig.subplots_adjust(top=.85,bottom=.12,wspace=.06,hspace=.25)
    cb=fig.add_axes([.36,.04,.28,.015]);fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-.5,.5),cmap='coolwarm'),cax=cb,orientation='horizontal',label='Eulerian surface-distance change mm: blue inward / red outward');savefig(fig,'Fig3_Native_3D_And_Region_Motion.png')
    fig,axs=plt.subplots(2,3,figsize=(15,8))
    for k,arm in enumerate(arms):
        rows=[x for x in metrics['stages']if x['arm']==arm];xx=np.arange(len(rows));col=['#246dbc','#d07a28'][k]
        axs[0,0].plot(xx,[x['fit_IoU']for x in rows],'-o',c=col,label=arm+' FIT',ms=3);axs[0,0].plot(xx,[x['holdout_IoU']for x in rows],'--',c=col,label=arm+' HOLDOUT')
        axs[0,1].plot(xx,[x['visible_region_Chamfer_mm']['MAE']for x in rows],'-o',c=col,label=arm+' visible',ms=3);axs[0,1].plot(xx,[x['unknown_region_Chamfer_mm']['MAE']for x in rows],'--',c=col,label=arm+' unknown')
        axs[0,2].plot(xx,[x['volume']['symmetric_difference_mm3']for x in rows],'-o',c=col,label=arm,ms=3)
        axs[1,0].plot(xx,[x['volume']['added_recovery_ratio']for x in rows],'-o',c=col,label=arm+' add',ms=3);axs[1,0].plot(xx,[x['volume']['removed_recovery_ratio']for x in rows],'--',c=col,label=arm+' remove')
        axs[1,1].plot(xx,[x['physical']['quality']['normal_angle_deg']['p95']for x in rows],'-o',c=col,label=arm,ms=3)
        axs[1,2].plot(xx,[x['center_error_mm']for x in rows],'-o',c=col,label=arm,ms=3)
    titles=[('Training and untouched holdout','Mask IoU'),('Visible / unknown geometric error','mean symmetric distance mm'),('Native GT symmetric-difference volume','mm3 fixed-grid proxy'),('Independent added / removed recovery','fraction, full GT denominator'),('Mesh roughness','adjacent-normal p95 degrees'),('Body center-of-mass error','mm; NOT a kernel q_GT')]
    for ax,(title,ylabel)in zip(axs.ravel(),titles):ax.set(title=title,ylabel=ylabel,xlabel='P0 / START / saved rounds / FINAL');ax.grid(alpha=.2);ax.legend(fontsize=6)
    fig.suptitle('Post-freeze native CAD audit: same data, same seed, same Powell budget, one target-boundary change\nTrajectory volume uses coarse fixed-node proxy; independent Sobol endpoint validation in report; lower loss or better Mask is not 3D correctness',fontsize=10);fig.tight_layout(rect=[0,0,1,.93]);savefig(fig,'Fig4_Trajectories_And_3D_Failures.png');print('FOUR_GATE_A_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
