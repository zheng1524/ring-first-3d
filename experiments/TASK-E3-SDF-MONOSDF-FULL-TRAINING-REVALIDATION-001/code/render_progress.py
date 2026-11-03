"""CPU figures from actual saved model geometry; incomplete arms stay labelled."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def draw_mesh(ax, mesh, title, view=(45,-65)):
    g=protocol()['geometry'];C=np.array(g['C_mm']);s=g['mm_per_model_unit']
    if mesh is not None and len(mesh.faces):
        collection=Poly3DCollection(np.asarray(mesh.vertices)[np.asarray(mesh.faces)],
            facecolors='#dcae8d',linewidths=0,rasterized=True)
        ax.add_collection3d(collection)
    cad=ringmesh(SCENE)
    ax.add_collection3d(Poly3DCollection(np.asarray(cad.vertices)[np.asarray(cad.faces)],
        facecolors='black',linewidths=0,rasterized=True))
    ax.set(xlim=(C[0]-s,C[0]+s),ylim=(C[1]-s,C[1]+s),zlim=(C[2]-s,C[2]+s),
        xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=title)
    ax.set_box_aspect((1,1,1));ax.view_init(*view)
    ax.tick_params(labelsize=6)


def main():
    all_geometry=[];latest={}
    for arm in ['M0','M1']:
        entries=[load(p)for p in sorted((R/'metrics').glob(f'single_{arm}_step*_GEOMETRY.json'))]
        all_geometry.extend(entries)
        if entries:latest[arm]=entries[-1]
    # Figure 1: use real formal loss points, not resource-test loss curves.
    fig,axs=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    for arm in ['M0','M1']:
        path=R/f'metrics/single_{arm}_TRAINING.csv'
        if path.exists():
            rr=rows(path);x=np.array([int(r['step'])for r in rr])
            for name in ['loss','rgb','SSI_depth','eikonal']:
                axs[0,0].plot(x,[float(r[name])for r in rr],label=f'{arm} {name}')
        gg=[a for a in all_geometry if a['arm']==arm]
        if gg:
            x=[a['step']for a in gg]
            r08=[a['rays'][0]for a in gg]
            axs[0,1].plot(x,[a['hit_fraction']for a in r08],'-o',label=arm+' ref08 first hit')
            axs[0,1].plot(x,[a['agreement_fraction']for a in r08],'--o',label=arm+' ref08 agree<=.25mm')
            axs[1,0].plot(x,[a['negative_grid_volume_mm3']for a in gg],'-o',label=arm)
            axs[1,1].plot(x,[a['cleaned_HERO_retained_0p25_N']/max(1,a['cleaned_visible_N'])for a in r08],'-o',label=arm)
    titles=['Formal training losses (SSI is not metric accuracy)','Fixed native ref08 denominator',
            'Model negative-grid volume proxy, mm3','Cleaned visible ref08 point retention <=.25mm']
    for ax,title in zip(axs.ravel(),titles):
        ax.set_title(title);ax.set_xscale('symlog',linthresh=10);ax.set_xlabel('actual optimizer updates')
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=7)
        ax.grid(alpha=.2)
    fig.suptitle('Actual saved checkpoints; unfinished arms are NOT_RUN; GT NOT_EVALUABLE')
    fig.savefig(R/'figures/Fig1_Training_Progress.png',dpi=130);plt.close(fig)

    raw=original(SOURCES[0]);n=native(SOURCES[0])
    raw_mesh=trimesh.Trimesh(raw['P'],raw['F'],process=False)
    native_uv=affine_uv(raw['uv'],n['Kn']@np.linalg.inv(n['K']))
    ij=np.floor(native_uv+.5).astype(int);h,w=n['depth'].shape
    valid=(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h)
    retained=np.load(N0/'frozen_inputs/native'/(SOURCES[0]+'.npz'))['valid']
    keep=np.zeros(len(ij),bool);keep[valid]=retained[ij[valid,1],ij[valid,0]]
    # This is only comparison subsetting of unchanged original faces, never prediction input.
    cleaned_mesh=trimesh.Trimesh(raw['P'],raw['F'][keep[raw['F']].all(1)],process=False)
    models=[]
    for arm in ['M0','M1']:
        entry=latest.get(arm)
        path=R/'local_results'/entry['tag']/'raw_mm.ply'if entry else None
        model=trimesh.load(path,process=False)if path and path.exists()else None
        models.append((model,arm+(f" step{entry['step']}"if entry else ' NOT_RUN')))
    fig=plt.figure(figsize=(16,10),constrained_layout=True)
    for row,view in enumerate([(80,-90),(8,0),(35,-60)]):
        for col,(m,title)in enumerate([(raw_mesh,'Original ref08 HERO'),(cleaned_mesh,'Cleaned original-face comparison')]+models):
            draw_mesh(fig.add_subplot(3,4,row*4+col+1,projection='3d'),m,title,view)
    fig.suptitle('Same fixed mm display cube; full raw files preserved; black actual CAD; no geometry smoothing')
    fig.savefig(R/'figures/Fig2_Metric_Geometry_Comparison.png',dpi=115);plt.close(fig)

    fig,axs=plt.subplots(3,5,figsize=(16,9),constrained_layout=True)
    for row,cid in enumerate(SOURCES):
        n=observed_local(cid)
        axs[row,0].imshow(n['native_RGB']);axs[row,0].contour(n['native_labels']==1,levels=[.5],colors='lime',linewidths=.4)
        axs[row,0].set_title(cid+' real RGB/Mask')
        axs[row,1].imshow(np.where(n['native_labels']==1,n['depth'],np.nan),vmin=15,vmax=50,cmap='viridis')
        axs[row,1].set_title('Original axial HERO mm')
        for col,arm in [(2,'M0'),(3,'M1')]:
            entry=latest.get(arm)
            if entry:
                data=np.load(R/'local_results'/entry['tag']/'evaluation.npz')
                hit=data[cid+'_hit_mm'];cid0=data[cid+'_native_id'];image=np.full(n['depth'].shape,np.nan)
                image.ravel()[cid0]=np.where(np.isfinite(hit),hit,np.nan)
                axs[row,col].imshow(image,cmap='viridis',vmin=15,vmax=50)
                mask=data[cid+'_full_image_visible_hit']
                axs[row,col].contour(mask,levels=[.5],colors='red',linewidths=.4)
                axs[row,col].set_title(arm+f" first mesh hit step{entry['step']}; red projection")
            else:axs[row,col].text(.1,.5,arm+' NOT_RUN',transform=axs[row,col].transAxes)
        raw=n['native_uv'];cad,_=cast(ringscene(SCENE),raw,n['Kn'],n['T']);block=np.full(n['depth'].shape,np.nan)
        block.ravel()[n['native_id']]=np.isfinite(cad)&(n['depth'].ravel()[n['native_id']]>cad+.002)
        axs[row,4].imshow(block,vmin=0,vmax=1,cmap='gray_r');axs[row,4].set_title('CAD occlusion on original HERO')
    for ax in axs.ravel():ax.set_axis_off()
    fig.suptitle('Actual cameras; holes/MISS are not filled; nontraining CORE views are diagnostics, not independent GT')
    fig.savefig(R/'figures/Fig3_Real_Image_First_Surface.png',dpi=130);plt.close(fig)

    fig,axs=plt.subplots(2,3,figsize=(13,8),constrained_layout=True)
    g=protocol()['geometry'];C=np.array(g['C_mm']);s=g['mm_per_model_unit']
    for row,arm in enumerate(['M0','M1']):
        entry=latest.get(arm)
        for col,axis in enumerate([0,1,2]):
            ax=axs[row,col]
            if entry:
                folder=R/'local_results'/entry['tag'];field=np.load(folder/f"sdf_{entry['step']}_model.npy",mmap_mode='r')
                k=field.shape[axis]//2;plane=np.take(field,k,axis=axis)*s
                rest=[a for a in range(3)if a!=axis]
                extent=[C[rest[0]]-s,C[rest[0]]+s,C[rest[1]]-s,C[rest[1]]+s]
                ax.imshow(plane.T,origin='lower',extent=extent,cmap='coolwarm',vmin=-2,vmax=2)
                if plane.min()<0<plane.max():ax.contour(plane.T,levels=[0],origin='lower',extent=extent,colors='black',linewidths=.8)
                ax.set_title(f'{arm} step{entry["step"]}, axis{axis} central raw SDF slice')
                ax.set_xlabel('XYZ'[rest[0]]+' mm');ax.set_ylabel('XYZ'[rest[1]]+' mm')
            else:ax.text(.2,.5,arm+' NOT_RUN',transform=ax.transAxes)
    fig.suptitle('Unfiltered raw neural SDF, black iso-zero; central sections do not certify anatomy or hidden closure')
    fig.savefig(R/'figures/Fig4_Raw_SDF_Local_Diagnostics.png',dpi=130);plt.close(fig)
    save('metrics/FIGURE_PROGRESS_INDEX.json',dict(latest=latest,
        scientific_status='IN_PROGRESS_NOT_FINAL_ACCEPTANCE',geometry_edited=False,
        inputs=[asset(p)for p in (R/'metrics').glob('single_M*_step*_GEOMETRY.json')]))
    print('FIGURES_UPDATED',list(latest),flush=True)


def observed_local(cid):return native(cid)


if __name__=='__main__':main()
