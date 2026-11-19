"""Actual native data figures, the reused Open3D mesh renderer, and layered GLB."""
from pathlib import Path
import colorsys
import numpy as np
import cv2
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from .camera import torus_contours,observe
from .geometry import project
from .io import save_json,read_json

def ring_metrics(C,K,labels):
    from scipy.spatial import cKDTree
    C=np.asarray(C);a=-np.arctan2(C[1,3],C[0,3]);co,si=np.cos(a),np.sin(a)
    G=np.eye(4);G[:3,:3]=[[co,-si,0],[si,co,0],[0,0,1]]
    uv=torus_contours(G@C,K,256)
    areas=[abs(cv2.contourArea(x.astype(np.float32)))for x in uv];outer=int(np.argmax(areas));inner=1-outer
    pred=np.zeros(labels.shape,np.uint8)
    cv2.fillPoly(pred,[np.rint(uv[outer]).astype(np.int32)],1);cv2.fillPoly(pred,[np.rint(uv[inner]).astype(np.int32)],0)
    known=labels!=1;p=pred.astype(bool)&known;t=labels==2
    q=observe(labels)['q_train'];d=cKDTree(uv.reshape(-1,2)).query(q)[0]
    return dict(Ring_IoU=float((p&t).sum()/max(1,(p|t).sum())),contour_N=len(q),contour_median_px=float(np.median(d)),contour_p95_px=float(np.quantile(d,.95)),evaluation_pixels='640x360 index centres; Polyp-adjacent boundary unknown; no GT'),uv,pred

def contour(ax,mask,color):
    cc,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    for c in cc:ax.plot(c[:,0,0],c[:,0,1],c=color,lw=.6)

def camera_angle(C,bounds):
    mid=(bounds.min(0)+bounds.max(0))/2;v=C[:3,3]-mid
    return float(np.degrees(np.arctan2(v[2],np.linalg.norm(v[:2])))),float(np.degrees(np.arctan2(v[1],v[0])))

def render_panel(ax,V,F,cad,bounds,title,angle,color='#4679b6',face_colors=None):
    from ._mesh_renderer import actual_mesh_image
    im,scale=actual_mesh_image(V,F,cad['V'],cad['F'],bounds,*angle,color,face_colors)
    ax.imshow(im);ax.plot([16,16+2*scale],[378,378],c='black',lw=2)
    ax.text(16,365,'2 mm at centre depth',fontsize=7);ax.axis('off');ax.set_title(title,fontsize=9)
    return im

def finish(fig,p):
    fig.savefig(p,dpi=145,bbox_inches='tight');plt.close(fig)

def scene_export(path,raws,cad,cameras=()):
    """GLB follows glTF metres; authoritative Raw NPZ/PLY remains millimetres."""
    scene=trimesh.Scene()
    ring=trimesh.Trimesh(cad['V']/1000,cad['F'],vertex_colors=np.tile([0,0,0,255],(len(cad['V']),1)),process=False)
    scene.add_geometry(ring,node_name='Ring_R10_CAD',geom_name='Ring_R10_CAD')
    for sid,V,F,color,kind in raws:
        col=np.asarray(color)
        if col.ndim==1:col=np.tile(np.r_[col[:3]*255,255],(len(V),1))
        m=trimesh.Trimesh(V/1000,F,vertex_colors=np.asarray(col,np.uint8),process=False)
        m.metadata.update(source_id=sid,kind=kind,world_unit='m',original_unit='mm',scale_from_mm=.001)
        scene.add_geometry(m,node_name=sid+'__'+kind,geom_name=sid+'__'+kind)
    for frame in cameras:
        C=np.asarray(frame['c2w_mm']);m=trimesh.creation.icosphere(subdivisions=1,radius=.0002)
        m.vertices+=C[:3,3]/1000;m.visual.vertex_colors=[225,110,30,255]
        direction=trimesh.creation.cylinder(radius=.00006,segment=np.array([C[:3,3],C[:3,3]+C[:3,2]*2.])/1000,sections=8)
        m=trimesh.util.concatenate([m,direction]);m.metadata.update(c2w_mm=C.tolist(),source_id=frame['id'])
        scene.add_geometry(m,node_name='CAMERA__'+frame['id'],geom_name='CAMERA__'+frame['id'])
    scene.metadata.update(coordinate_unit='m',original_unit='mm',global_scale=.001,fusion=False,world='fixed Ring-First')
    path.parent.mkdir(parents=True,exist_ok=True);scene.export(path)

def generate(data,output,gallery):
    data=Path(data);output=Path(output);gallery=Path(gallery);assets=gallery/'assets';assets.mkdir(parents=True,exist_ok=True)
    manifest=read_json(data/'DATA_MANIFEST.json');frames=manifest['frames'];target=frames[0]
    rgb=np.asarray(Image.open(data/target['rgb']).convert('RGB'));labels=np.asarray(Image.open(data/target['labels']))
    C=np.asarray(target['c2w_mm']);K=np.asarray(target['K']);cad=dict(np.load(data/'RING_CAD.npz'))
    native=dict(np.load(output/'HERO_native.npz'));raw=dict(np.load(output/'RAW_NATIVE_MESH.npz'));images=dict(np.load(output/'NATIVE_RGB_LABELS.npz'))
    V,F=raw['V'],raw['F'];bounds=np.r_[V[np.unique(F)],cad['V']];angle=camera_angle(C,bounds)
    row,curves,pred=ring_metrics(C,K,labels)
    fig,axs=plt.subplots(2,2,figsize=(12,7))
    axs[0,0].imshow(rgb);axs[0,0].set_title('Real G01 RGB / original work frame')
    axs[0,1].imshow(labels,vmin=0,vmax=2,cmap='viridis');axs[0,1].set_title('Original labels: Background / Polyp / Ring')
    axs[1,0].imshow(rgb);contour(axs[1,0],labels==2,'cyan');contour(axs[1,0],labels==1,'lime')
    for c in curves:axs[1,0].plot(c[:,0],c[:,1],c='orange',lw=1)
    axs[1,0].set_title('Cyan Ring Mask; orange fixed R10 CAD projection')
    axs[1,1].imshow(np.where(labels==1,np.nan,(pred.astype(int)-(labels==2).astype(int))),vmin=-1,vmax=1,cmap='coolwarm')
    axs[1,1].set_title('Known-region Ring disagreement; Polyp overlap unknown')
    for ax in axs.ravel():ax.axis('off')
    fig.suptitle('Real G01 / frozen conditional cameras; camera projection is not absolute pose GT')
    finish(fig,assets/'01_RGB_Mask_CAD_Projection.png')
    fig=plt.figure(figsize=(12,5));ax=fig.add_subplot(121,projection='3d')
    for i,frame in enumerate(frames):
        T=np.asarray(frame['c2w_mm']);pos=T[:3,3];ax.scatter(*pos,label=('target'if i==0 else'support')+' '+frame['id'])
        ax.quiver(*pos,*(T[:3,2]*3),color='tab:orange',arrow_length_ratio=.15)
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    rv=cad['V'];ax.add_collection3d(Poly3DCollection(rv[cad['F']],facecolor=(.035,.035,.035),edgecolor='none'))
    ordered=sorted(frames,key=lambda f:int(f['id'].rsplit('raw',1)[-1]))
    centres=np.array([np.asarray(f['c2w_mm'])[:3,3] for f in ordered])
    ax.plot(centres[:,0],centres[:,1],centres[:,2],c='grey',lw=1,label='selected frame order')
    ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title='Four actual c2w positions + forward directions')
    ax.set_box_aspect((1,1,1));ax.legend(fontsize=5,loc='upper left')
    render_panel(fig.add_subplot(122),V,F,cad,bounds,'Raw target surface in the same fixed Ring world',angle)
    finish(fig,assets/'02_Cameras_And_Ring.png')
    fig,axs=plt.subplots(1,2,figsize=(12,4));z=native['depth_mm']
    im=axs[0].imshow(z,cmap='viridis');fig.colorbar(im,ax=axs[0],label='Native axial Z (mm)')
    im=axs[1].imshow(np.where(images['labels']==1,z,np.nan),cmap='viridis');fig.colorbar(im,ax=axs[1],label='Native axial Z (mm)')
    axs[0].set_title('Actual newly inferred native depth / 352 x 640');axs[1].set_title('Same depth samples inside native Polyp Mask')
    for a in axs:a.axis('off')
    finish(fig,assets/'03_Native_Depth_mm.png')
    # Actual pixel identities link the two images to the saved three-dimensional samples.
    uv=raw['uv'];indices=np.linspace(0,len(uv)-1,5,dtype=int);work=np.c_[uv[indices],np.ones(5)]@np.linalg.inv(native['K_index_native']).T@K.T;work=work[:,:2]/work[:,2:]
    fig,axs=plt.subplots(1,4,figsize=(16,4));axs[0].imshow(rgb);axs[1].imshow(np.where(images['labels']==1,z,np.nan),cmap='viridis')
    for j,k in enumerate(indices):
        color=plt.get_cmap('tab10')(j);axs[0].scatter(*work[j],c=[color],s=20);axs[0].text(*work[j],str(j),color='white')
        axs[1].scatter(*uv[k],c=[color],s=20);axs[1].text(*uv[k],str(j),color='white')
    render_panel(axs[2],V,F,cad,bounds,'Raw native triangles, same pixel identities',angle,face_colors=np.asarray(trimesh.load(output/'Raw_open_mesh.ply',process=False).visual.vertex_colors)[F,:3].mean(1)/255)
    render_panel(axs[3],V,F,cad,bounds,'Raw visible surface / side view', (0,-65))
    axs[0].set_title('Real RGB / five actual source pixels');axs[1].set_title('Native depth / the same five samples')
    for a in axs[:2]:a.axis('off')
    finish(fig,assets/'04_RGB_Depth_Raw_Mesh_Correspondence.png')
    save_json(assets/'PIXEL_XYZ_CORRESPONDENCES.json',[dict(marker=j,native_pixel_id=int(raw['native_pixel_id'][k]),uv_native=uv[k],uv_work=work[j],XYZ_mm=V[k])for j,k in enumerate(indices)])
    angles=[angle,camera_angle(np.asarray(frames[-1]['c2w_mm']),bounds),(80,-65),(0,0),(0,180),(-75,-65)]
    names=['Near target camera','Near complementary support','Top','Side','Reverse side','Underneath']
    fig,axs=plt.subplots(2,3,figsize=(12,8))
    for a,ang,name in zip(axs.ravel(),angles,names):render_panel(a,V,F,cad,bounds,name,ang)
    fig.suptitle('One actual native Raw Mesh, six views / black R10 CAD / fixed millimetre bounds / open surface')
    finish(fig,assets/'05_Raw_Mesh_Six_Views.png')
    cols=np.c_[images['RGB'][uv[:,1],uv[:,0]],np.full(len(uv),255)]
    raws=[(target['id'],V,F,cols,'RAW')]
    if (output/'FACE_EVIDENCE.npz').exists():
        ev=dict(np.load(output/'FACE_EVIDENCE.npz'));raws.append((target['id'],V,F[ev['state']==0],cols,'TRUSTED'))
        fig,axs=plt.subplots(1,3,figsize=(12,4));statecols=np.array([[.2,.75,.3],[.95,.75,.2],[.9,.2,.2],[.55,.55,.55]])
        render_panel(axs[0],V,F,cad,bounds,'Raw: all original native triangles',angle)
        render_panel(axs[1],V,F,cad,bounds,'017: Trusted / Uncertain / Rejected / Unknown',angle,face_colors=statecols[ev['state']])
        render_panel(axs[2],V,F[ev['state']==0],cad,bounds,'Trusted subset; Raw always retained',angle)
        finish(fig,assets/'06_Optional_Cleaning.png')
    scene_export(assets/'scenes/G01_core.glb',raws,cad,frames)
    metrics=[]
    for frame in frames:
        lab=np.asarray(Image.open(data/frame['labels']));r,_,_=ring_metrics(np.asarray(frame['c2w_mm']),np.asarray(frame['K']),lab)
        metrics.append(dict(source_id=frame['id'],qualification=frame['camera_status'],**r))
    save_json(assets/'CAMERA_PROJECTION_METRICS.json',metrics)
    save_json(assets/'DEMO_RESULTS.json',dict(example_id=target['id'],inference=read_json(output/'INFERENCE.json'),comparison=read_json(output/'HISTORICAL_COMPARISON.json')if(output/'HISTORICAL_COMPARISON.json').exists()else None,GLB_unit='m',PLY_and_NPZ_unit='mm',GLB_scale_from_mm=.001))
    return metrics
