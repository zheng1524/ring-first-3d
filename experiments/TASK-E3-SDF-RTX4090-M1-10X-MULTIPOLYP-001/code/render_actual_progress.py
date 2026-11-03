"""Only saved optimizer states: G01 M1 0/1000/2000/4000, no new updates."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cloud_report import render,panel,finish,output,raw_hero


def main():
    scene='G01_004';STAGES=[0,1000,2000,4000]
    (TASK/'figures').mkdir(exist_ok=True)
    (TASK/'metrics').mkdir(exist_ok=True)
    fig,axs=plt.subplots(3,6,figsize=(19,10))
    for row,view in enumerate([0,1,5]):
        items=[(raw_hero(scene),'Original HERO'),(raw_hero(scene,True),'Cleaned original-face display')]
        items += [(output(scene,n),'M1 untrained initialization'if n==0 else f'M1 {n} actual updates')for n in STAGES]
        for col,(mesh,title)in enumerate(items):panel(axs[row,col],scene,mesh,title,view)
    finish(fig,'Progress_Fig1_HERO_and_M1_Stages.png',
        'G01_004 real raw Mesh; fixed mm window per row; black actual CAD; no smoothing/deletion; raw files retain full extent')
    mesh=output(scene,4000)
    fig,axs=plt.subplots(2,3,figsize=(12,8))
    for k,ax in enumerate(axs.ravel()):panel(ax,scene,mesh,f'M1 step4000 / actual view{k+1}',k)
    finish(fig,'Progress_Fig2_M1_4000_Six_Views.png','Same learned SDF Mesh in six fixed Ring-world views, millimetres; no new training')

    # Additive display diagnostic: require true first self-visible layer, realMask,
    # source HERO depth and actual CAD order. Never delete a face or alter metrics.
    centers=np.asarray(mesh.vertices)[np.asarray(mesh.faces)].mean(1);own=mesh_scene(mesh.vertices,mesh.faces)
    supported=np.zeros(len(centers),bool);visible_any=supported.copy();BG_conflict=supported.copy()
    for cid in SOURCES:
        n=native(cid);uv,z=vis.project_camera(centers,n['Kn'],n['T']);h,w=n['depth'].shape
        ok=np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5)
        j=np.flatnonzero(ok);ij=np.floor(uv[j]+.5).astype(int)
        cad,_=cast(ringscene(scene),uv[j],n['Kn'],n['T']);first,_=cast(own,uv[j],n['Kn'],n['T'])
        legal=(~np.isfinite(cad)|(z[j]<cad-.002))&np.isfinite(first)&(abs(first-z[j])<=.01)
        j=j[legal];ij=ij[legal];labels=n['native_labels'][ij[:,1],ij[:,0]]
        kept=np.load(TASK/'frozen_inputs/native'/(cid+'.npz'))['valid'][ij[:,1],ij[:,0]]
        depth=n['depth'][ij[:,1],ij[:,0]]
        visible_any[j]|=labels!=2;BG_conflict[j]|=labels==0
        supported[j]|=kept&(labels==1)&(abs(z[j]-depth)<=.25)
    cat=np.where(supported,'OBSERVED_NEAR_PROXY',np.where(visible_any,'INFERRED_UNSUPPORTED_PROXY','UNKNOWN_OCCLUDED_OR_UNSEEN'))
    fig,axs=plt.subplots(2,3,figsize=(12,8))
    for k,ax in enumerate(axs.ravel()):panel(ax,scene,mesh,f'Step4000 evidence / view{k+1}',k,categories=cat)
    finish(fig,'Progress_Fig3_Observed_Inferred.png',
        'Green=first-visible HERO-supported proxy; orange=visible unsupported/conflict; purple=unseen/occluded; black=CAD')
    np.savez_compressed(TASK/'metrics/STEP4000_DISPLAY_EVIDENCE.npz',original_mesh_face_id=np.arange(len(cat)),
        category=cat,visible_BG_Mask_conflict=BG_conflict,all_geometry_unchanged=True)
    (TASK/'metrics/STEP4000_DISPLAY_EVIDENCE.json').write_text(json.dumps(dict(
        scene=scene,step=4000,self_first_visibility_tolerance_mm=.01,HERO_depth_proxy_mm=.25,
        CAD_epsilon_mm=.002,counts={c:int((cat==c).sum())for c in np.unique(cat)},
        visible_BG_mask_conflict_faces=int(BG_conflict.sum()),unverified_labels_not_physical_truth=True,
        geometry_deleted=0,training_updates=0),indent=2)+'\n')

    fig,axs=plt.subplots(3,5,figsize=(17,10))
    latest_data=np.load(TASK/'groups'/scene/'local_results/single_M1_step004000/evaluation.npz')
    for row,cid in enumerate(SOURCES):
        cp=np.load(TASK/'frozen_inputs/crops'/(cid+'.npz'));n=native(cid);pixel=cp['source_ids'];inside=pixel>=0
        axs[row,0].imshow(cp['RGB']);axs[row,0].contour(cp['labels']==1,levels=[.5],colors='lime',linewidths=.5)
        pred=latest_data[cid+'_full_image_visible_hit'].ravel();pm=np.zeros(pixel.shape,bool);pm[inside]=pred[pixel[inside]]
        axs[row,0].contour(pm,levels=[.5],colors='red',linewidths=.5)
        axs[row,0].set_title(cid.removeprefix('G01_004_')+' real RGB / green Mask\nred: M1 4000 projection',fontsize=10)
        zz=n['depth'][n['valid']];vmin,vmax=float(zz.min()),float(zz.max())
        for col,step in [(1,1000),(2,2000),(3,4000)]:
            data=np.load(TASK/'groups'/scene/'local_results'/f'single_M1_step{step:06d}'/'evaluation.npz')
            all_depth=np.full(n['depth'].size,np.nan);d=data[cid+'_hit_mm'];valid=data[cid+'_visible']
            all_depth[data[cid+'_native_id']]=np.where(np.isfinite(d)&valid,d,np.nan)
            image=np.full(pixel.shape,np.nan);image[inside]=all_depth[pixel[inside]]
            im=axs[row,col].imshow(image,cmap='viridis',vmin=vmin,vmax=vmax)
            axs[row,col].set_title(f'{step} first axial depth mm',fontsize=10);fig.colorbar(im,ax=axs[row,col],fraction=.035,pad=.01)
        d=latest_data[cid+'_hit_mm']-latest_data[cid+'_depth_mm'];valid=latest_data[cid+'_visible']&np.isfinite(d)
        all_error=np.full(n['depth'].size,np.nan);all_error[latest_data[cid+'_native_id']]=np.where(valid,d,np.nan)
        image=np.full(pixel.shape,np.nan);image[inside]=all_error[pixel[inside]]
        im=axs[row,4].imshow(image,cmap='coolwarm',vmin=-1,vmax=1);axs[row,4].set_title('4000 first depth\nminus HERO (mm)',fontsize=10)
        fig.colorbar(im,ax=axs[row,4],fraction=.035,pad=.01)
        for ax in axs[row]:ax.axis('off')
    finish(fig,'Progress_Fig4_Real_RGB_First_Depth.png','All three real references; MISS/CAD-hidden left empty; HERO residual is not physical GT error')
    print('FOUR_ACTUAL_PROGRESS_FIGURES_WRITTEN; new optimizer updates0',flush=True)


if __name__=='__main__':main()
