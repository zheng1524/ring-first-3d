"""Reuse the preceding actual-mesh rendering pipeline; draw recorded failures, never repair geometry."""
from common import *
from evaluate import pointcast
import ast
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
PARENT=R.parents[1];A=Path(load(R/'config/PROTOCOL.json')['A_frozen_root'])
source=PARENT/'code/figures.py';tree=ast.parse(source.read_text())
for fn in tree.body:
    if isinstance(fn,ast.FunctionDef)and fn.name in ['actual_mesh_image','edge']:
        text=ast.get_source_segment(source.read_text(),fn)
        if fn.name=='actual_mesh_image':
            text=text.replace('azim,color):','azim,color,fault_faces=None):')
            text=text.replace('rgb[sel]=np.array(col)*shade[:,None]',"rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and fault_faces is not None:\n            marked=np.isin(fid[sel],np.asarray(fault_faces,dtype=int));indices=np.flatnonzero(sel)[marked];rgb[indices]=np.array([.95,.08,.08])*shade[marked,None]")
        exec(compile(text,str(source)+':display_helpers','exec'),globals())
COL={'P0':'#979fa3','A':'#986bb5','B':'#2c86c4','C':'#24985d','D':'#e3982d'}
def state(name,arm,step=300):
    return R/'inputs'/name/'INITIAL.npz'if arm=='P0'else A/'local_results'/name/'RingAware'/('STEP_%04d.npz'%step)if arm=='A'else R/'local_results'/name/arm/('STEP_%04d.npz'%step)
def finish(fig,name):
    p=R/'figures'/name;p.parent.mkdir(exist_ok=True,parents=True);fig.savefig(p,dpi=155,bbox_inches='tight');plt.close(fig)
def main():
    freeze=load(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_EVALUATION.json')
    for a in freeze['files']:assert sha(a['path'])==a['sha256'],a['path']
    summary=load(R/'metrics/SUMMARY.json');end=load(R/'metrics/ENDPOINTS.json');faults=load(R/'metrics/BLENDER_GEOMETRY_CHECK.json');arms=['P0','A','B','C','D']
    fig,axs=plt.subplots(4,6,figsize=(22,15))
    for i,name in enumerate(['virtual','real']):
        p0=np.load(state(name,'P0'));cad=np.load(R/'inputs'/name/'RING.npz')
        for k,(el,az)in enumerate([(30,-65),(10,-90)]):
            ax=axs[2*i+k,0]
            if name=='virtual':
                gt=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz');im,pxmm=actual_mesh_image(gt['V'],gt['F'],cad['V'],cad['F'],p0['V'],el,az,'#bf858f');ax.imshow(im);ax.plot([20,20+2*pxmm],[375,375],c='black',lw=2);ax.text(20,365,'2 mm at view-center depth',fontsize=7);ax.set_title('Native Blender GT\nindependent posterior reference',fontsize=9)
            else:
                d=np.load(R/'inputs/real/G01_004_ref08.npz');ax.imshow(d['RGB']);ax.set_title('Real RGB ref08\nfull 3D GT: NOT_EVALUABLE',fontsize=9)
            ax.axis('off')
        for j,arm in enumerate(arms,1):
            p=state(name,arm)
            if not p.exists():
                for k in[0,1]:axs[2*i+k,j].text(.1,.5,'STOPPED / NO FINAL');axs[2*i+k,j].axis('off')
                continue
            a=np.load(p);bad=next(f for f in faults if f['case']==name and f['arm']==arm);ids={int(x[0])for x in bad['first_Ring_pairs']}|{int(x)for pair in bad['first_self_pairs']for x in pair}
            for k,(el,az)in enumerate([(30,-65),(10,-90)]):
                image,pxmm=actual_mesh_image(a['V'],a['F'],cad['V'],cad['F'],p0['V'],el,az,COL[arm],list(ids));ax=axs[2*i+k,j];ax.imshow(image);ax.axis('off');ax.plot([20,20+2*pxmm],[375,375],c='black',lw=2);ax.text(20,365,'2 mm at view-center depth',fontsize=7)
                ax.set_title(name+' | '+arm+(' ideal-depth upper bound'if name=='virtual'and arm=='D'else'')+'\nRing pairs %d / self pairs %d'%(bad['Ring_intersecting_triangle_pair_N'],bad['nonadjacent_self_intersection_pair_N']),fontsize=9,color='red'if ids else'black')
    fig.suptitle('P0 / frozen A / B relative shape / C progressive / D depth | actual raw Meshes\nSame metric viewer per case, black CAD; red = recorded collision/self-intersection faces, no geometry repair',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig1_P0_A_B_C_D_Actual_Meshes.png')
    # Same native camera for every prediction, no selected best checkpoint.
    fig,axs=plt.subplots(2,5,figsize=(18,7))
    for i,(name,cid)in enumerate([('virtual','IIa6.5_R10_obs04'),('real','G01_004_growth_r04')]):
        d=np.load(R/'inputs'/name/(cid+'.npz'));cad=np.load(R/'inputs'/name/'RING.npz');cz=cast(scene(cad['V'],cad['F']),d['K'],d['T'],360,640)
        for j,arm in enumerate(arms):
            ax=axs[i,j];ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');edge(ax,d['labels']==2,'cyan');p=state(name,arm)
            if p.exists():
                m=np.load(p);z=cast(scene(m['V'],m['F']),d['K'],d['T'],360,640);pred=np.isfinite(z)&(z<cz);edge(ax,pred,COL[arm]);tt=d['labels']==1;ii=(pred&tt).sum()/max(1,(pred|tt).sum());ax.set_title(cid+' | '+arm+'\nfull Mask IoU %.4f'%ii,fontsize=9)
            ax.axis('off')
    fig.suptitle('Fixed HOLDOUT native RGB/labels, target green / Ring cyan / actual prediction colored\nReal holdout is update-stage only; D virtual uses ideal GT depth, D real uses audited native HERO',fontsize=11);fig.tight_layout(rect=[0,0,1,.9]);finish(fig,'Fig2_Fixed_Holdout_Projection.png')
    fig,axs=plt.subplots(2,3,figsize=(15,8))
    for arm in['A','B','C','D']:
        for ax,name,key in[(axs[0,0],'real','volume_ratio_P0'),(axs[0,1],'real','holdout_IoU'),(axs[0,2],'virtual','Chamfer_MAE_mm'),(axs[1,0],'virtual','symmetric_difference_mm3'),(axs[1,1],'virtual','roughness_p95_deg'),(axs[1,2],'real','holdout_depth_conditional_MAE_mm')]:
            rr=[x for x in summary if x['case']==name and(x['arm']=='P0'or x['arm']==arm)];ax.plot([x['step']for x in rr],[x[key]for x in rr],'-o',c=COL[arm],label=arm,ms=3)
    for ax,title,unit in zip(axs.ravel(),['Real volume / P0','Real full-Mask holdout IoU','Virtual posterior GT Chamfer MAE','Virtual GT difference occupancy proxy*','Virtual adjacent-normal p95','Real HERO holdout conditional MAE*'],['ratio','IoU','mm','mm3','degrees','mm']):
        ax.set(title=title,xlabel='optimizer steps',ylabel=unit);ax.axvline(100,c='gray',ls=':',alpha=.6);ax.grid(alpha=.2);ax.legend(ncol=4,fontsize=7)
    fig.suptitle('All saved checkpoints, fixed final step 300 | C/D release vertices after step 100\n*Self-intersecting meshes have no certified solid volume. Conditional depth MAE must be read with fixed-denominator loss/hits.',fontsize=11);fig.tight_layout(rect=[0,0,1,.90]);finish(fig,'Fig3_Stage_Geometry_And_Depth.png')
    fig,axs=plt.subplots(3,6,figsize=(21,11));last=None
    for i,(name,cid)in enumerate([('virtual','IIa6.5_R10_obs04'),('real','G01_004_ref08'),('real','G01_004_growth_r04')]):
        d=np.load(R/'inputs'/name/(cid+'.npz'));ob=np.load(R/'depth_observations'/(cid+'.npz'));K=ob['K'];T=ob['T'];uv=ob['uv'];q=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T;X=(q*ob['z'][:,None])@T[:3,:3].T+T[:3,3];xy=q@d['K'].T;xy=xy[:,:2]/xy[:,2:]
        cad=np.load(R/'inputs'/name/'RING.npz');_,_,cz=pointcast(scene(cad['V'],cad['F']),X,K,T)
        axs[i,0].imshow(d['RGB']);edge(axs[i,0],d['labels']==1,'lime');edge(axs[i,0],d['labels']==2,'cyan');axs[i,0].set_title(cid+'\n'+('IDEAL GT DEPTH UPPER BOUND'if name=='virtual'else'FROZEN NATIVE HERO'),fontsize=9)
        axs[i,1].imshow(d['RGB']);sc=axs[i,1].scatter(xy[:,0],xy[:,1],c=ob['z'],s=7,cmap='viridis');fig.colorbar(sc,ax=axs[i,1],fraction=.04,label='axial Z mm');axs[i,1].set_title('Fixed native Pixel IDs / depth\nN=%d, no interpolation'%len(uv),fontsize=9)
        for j,arm in enumerate(['A','B','C','D'],2):
            ax=axs[i,j];ax.imshow(d['RGB']);p=state(name,arm)
            if p.exists():
                a=np.load(p);_,_,z=pointcast(scene(a['V'],a['F']),X,K,T);hit=np.isfinite(z)&(z>0)&(z<cz-.05);err=z-ob['z'];last=ax.scatter(xy[hit,0],xy[hit,1],c=err[hit],s=8,cmap='coolwarm',vmin=-2,vmax=2);ax.scatter(xy[~hit,0],xy[~hit,1],marker='x',c='black',s=9);ax.set_title(arm+' | hit %d/%d\nconditional MAE %.3f mm'%(hit.sum(),len(hit),abs(err[hit]).mean()if hit.any()else float('nan')),fontsize=9)
        yy,xx=np.nonzero(d['labels']>0);bounds=(max(0,xx.min()-20),min(640,xx.max()+20),max(0,yy.min()-20),min(360,yy.max()+20))
        for ax in axs[i]:ax.set_xlim(bounds[0],bounds[1]);ax.set_ylim(bounds[3],bounds[2]);ax.axis('off')
    fig.suptitle('Same source rays and actual first-depth residuals, NOT a fabricated dense depth map\nDisplay-only crop from frozen Masks, same native pixel coordinates; K/data unchanged. A/B/C never train on depth.\nD uses FIT views only; black x = missing/occluded, colors clipped to +/-2mm for display.',fontsize=11);fig.tight_layout(rect=[0,.035,1,.91]);cb=fig.add_axes([.38,.015,.25,.012]);fig.colorbar(last,cax=cb,orientation='horizontal',label='Mesh axial Z minus observed Z, mm');finish(fig,'Fig4_Fixed_Ray_Depth_Residuals.png')
    # All original evaluation cameras, same figure layout; retained locally.
    for name in['virtual','real']:
        views=getcase(name)['views'];fig,axs=plt.subplots(len(views),5,figsize=(18,3*len(views)),squeeze=False)
        for i,v in enumerate(views):
            d=np.load(R/'inputs'/name/(v['id']+'.npz'));cad=np.load(R/'inputs'/name/'RING.npz');cz=cast(scene(cad['V'],cad['F']),d['K'],d['T'],360,640)
            for j,arm in enumerate(arms):
                ax=axs[i,j];ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');p=state(name,arm)
                if p.exists():
                    a=np.load(p);z=cast(scene(a['V'],a['F']),d['K'],d['T'],360,640);edge(ax,np.isfinite(z)&(z<cz),COL[arm])
                ax.axis('off');ax.set_title(v['id']+' '+v['role']+' '+arm,fontsize=9)
        fig.tight_layout();finish(fig,'full/'+name+'_ALL_VIEWS.png')
    save('assets_index/VISUALIZATION_SOURCE.json',dict(inherited_helpers=asset(source),functions=['actual_mesh_image','edge'],display_only_change='red face color for original saved collision IDs; no vertex changes',figures=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))]))
    print('Four core figures from actual P0/A/B/C/D Meshes and observed source rays',flush=True)
if __name__=='__main__':main()
