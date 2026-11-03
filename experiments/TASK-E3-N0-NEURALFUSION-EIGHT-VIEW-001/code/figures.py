"""Four evidence composites from real meshes/images. Rendering changes no geometry."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import textwrap
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt.rcParams.update({'font.size':9,'axes.titlesize':10,'figure.facecolor':'white'})
COLORS=np.array([[.25,.68,.42],[.95,.58,.16],[.62,.43,.78]])
@lru_cache(None)
def output(tag):return trimesh.load(R/'meshes'/f'{tag}_raw_mm.ply',process=False)
@lru_cache(None)
def raw_combined(scene):
    # Original surfaces, unchanged topology; concatenation is display-only, no fusion.
    pp=[];ff=[];offset=0
    for cid in protocol()['orders'][scene]:
        a=original(cid);pp.append(a['P']);ff.append(a['F']+offset);offset+=len(a['P'])
    return trimesh.Trimesh(np.concatenate(pp),np.concatenate(ff),process=False)
def look_frame(vector):
    z=-np.asarray(vector,float);z/=np.linalg.norm(z);x=np.cross(z,[0.,0.,1.]);x/=np.linalg.norm(x);y=np.cross(z,x);return np.stack([x,y,z],1)
def ortho_rays(scene,side=False,size=360,zoom=1.,offset=None):
    dom=protocol()['domains'][scene];lo=np.array(dom['source_extent_min_mm']);hi=np.array(dom['source_extent_max_mm']);center=(lo+hi)/2 if offset is None else np.asarray(offset);W=dom['L_mm']/zoom
    B=look_frame([1.,.15,.15]if side else[.5,-1.,.85]);v,u=np.mgrid[:size,:size];xy=np.c_[((u.ravel()+.5)/size-.5)*W,((v.ravel()+.5)/size-.5)*W];origin=center+xy@B[:,:2].T-B[:,2]*100
    rays=np.c_[origin,np.broadcast_to(B[:,2],origin.shape)].astype(np.float32);return rays,[-W/2,W/2,W/2,-W/2],B,center
def shade(P,F,result,direction,smooth=False):
    hit=result['t_hit'].numpy();valid=np.isfinite(hit);ids=result['primitive_ids'].numpy().astype(np.int64);normals=result['primitive_normals'].numpy().astype(float)
    if smooth and valid.any():
        m=trimesh.Trimesh(P,F,process=False);vn=np.asarray(m.vertex_normals);b=result['primitive_uvs'].numpy()[valid];w=np.c_[1-b.sum(1),b];normals[valid]=(vn[F[ids[valid]]]*w[:,:,None]).sum(1);normals[valid]/=np.maximum(1e-20,np.linalg.norm(normals[valid],axis=1))[:,None]
    light=-np.asarray(direction);strength=.35+.65*np.abs(normals@light);color=np.array([.69,.75,.82]);img=np.ones((len(hit),3));img[valid]=color*strength[valid,None];return img,hit,ids
def render(scene,mesh,side=False,smooth=False,categories=None,size=360,zoom=1.,offset=None):
    rays,extent,B,center=ortho_rays(scene,side,size,zoom,offset);ds=mesh_scene(mesh.vertices,mesh.faces);result=ds.cast_rays(o3d.core.Tensor(rays));img,hit,ids=shade(np.asarray(mesh.vertices),np.asarray(mesh.faces),result,B[:,2],smooth)
    if categories is not None:
        ok=np.isfinite(hit);cat=categories[ids[ok]];col=np.array([COLORS[0]if c=='OBSERVED_NEAR_PROXY'else(COLORS[1]if c=='INFERRED_UNSUPPORTED_PROXY'else COLORS[2])for c in cat]);img[ok]=col
    cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();black=np.isfinite(cad)&(cad<=hit+.002);img[black]=.015
    return img.reshape(size,size,3),extent
def panel(ax,scene,mesh,title,**kw):
    img,extent=render(scene,mesh,**kw);ax.imshow(img,extent=extent);ax.set_title('\n'.join(textwrap.wrap(title,38)));ax.set_xlabel('display plane x (mm)');ax.set_ylabel('display plane y (mm)');ax.tick_params(labelsize=7)
def finish(fig,name,title):
    fig.suptitle(title,fontsize=15);fig.subplots_adjust(top=.92,bottom=.055,hspace=.44,wspace=.34);fig.savefig(R/'figures'/name,dpi=160);plt.close(fig);print('FIGURE',name,flush=True)
def figure1():
    p=protocol();fig,axes=plt.subplots(4,8,figsize=(24,12));gate={r['source']:r for r in load(R/'config/CAMERA_GATE_RESULTS.json')['sources']}
    for pair,(scene,ii)in enumerate(p['orders'].items()):
        positive=np.concatenate([cleaned(c)['depth'][cleaned(c)['valid']]for c in ii]);norm=Normalize(positive.min(),positive.max())
        for j,cid in enumerate(ii):
            s=native(cid);c=crop(cid);ax=axes[2*pair,j];rgb=s['RGB'].copy();mask=s['labels']==1;contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(rgb,contours,-1,(0,255,80),1)
            rc=np.load(R/f'runtime/ring/{cid}_ORIGINAL.npz')['CAD_mask'];curves,_=cv2.findContours(rc.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(rgb,curves,-1,(0,0,0),2)
            ax.imshow(rgb);ax.axis('off');ax.set_title(f"{scene} F{j} {cid.split('_004_')[-1]}\n{block(cid).split('_')[-1]} / {gate[cid]['qualification'].replace('INSUFFICIENT_EVIDENCE','INSUFF.').replace('CONDITIONAL_USABLE','COND.')}\nRGB / Mask / CAD")
            ax=axes[2*pair+1,j];a=np.ma.masked_where(~c['valid'],c['depth_mm']);im=ax.imshow(a,cmap='viridis',norm=norm);vv,uu=np.mgrid[:240,:320];cad,_=cast(ringscene(scene),np.c_[uu.ravel(),vv.ravel()],c['K_crop'],s['T']);black=np.isfinite(cad).reshape(240,320)&(c['labels']==2);overlay=np.ones((240,320,4));overlay[:,:,:3]=0;overlay[:,:,3]=black;ax.imshow(overlay);ax.axis('off');ax.set_title(f"320x240; scale={float(c['scale']):.3f}\nvalid={int(c['valid'].sum())}; Z (mm)")
        if len(ii)<8:
            for j in range(len(ii),8):
                axes[2*pair,j].axis('off');axes[2*pair+1,j].axis('off')
            axes[2*pair,len(ii)].text(.02,.9,'G06: FIVE existing HERO\nNo fabricated eight-view data\nSame current Gate / cleanup\nIndependent metric domain',va='top',transform=axes[2*pair,len(ii)].transAxes)
            # A real camera/CAD geometry inset, world coordinates in mm.
            for scene2,position in [('G01_004',(2,6)),('G06_004',(3,6))]:
                ax0=axes[position];spec=ax0.get_subplotspec();ax0.remove();ax=fig.add_subplot(spec,projection='3d');m=ringmesh(scene2);ax.add_collection3d(Poly3DCollection(m.triangles,facecolor='black',linewidth=0,alpha=1))
                for k,cid in enumerate(p['orders'][scene2]):
                    T=source(cid)['T'];C=T[:3,3];ax.scatter(*C,s=15);ax.text(*C,str(k),fontsize=7);ax.quiver(*C,*(T[:3,2]*4),color='grey')
                centers=np.array([source(cid)['T'][:3,3]for cid in p['orders'][scene2]]);Q=np.r_[centers,m.vertices];mid=(Q.min(0)+Q.max(0))/2;rad=np.ptp(Q,axis=0).max()/2+2;ax.set(xlim=(mid[0]-rad,mid[0]+rad),ylim=(mid[1]-rad,mid[1]+rad),zlim=(mid[2]-rad,mid[2]+rad),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=scene2+' frozen cameras');ax.set_box_aspect([1,1,1]);ax.tick_params(labelsize=6)
        fig.colorbar(im,ax=list(axes[2*pair+1,:len(ii)]),fraction=.01,pad=.01,label=scene+' axial mm')
    finish(fig,'Fig1_Inputs_Crops_Cameras.png','Real inputs / latest Gate / exact crops / frozen cameras — Mask green, CAD black; no GT')
def historical_o3d():
    path=REPO/'experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/previews/G1_mm.glb';ALLOWED.add(str(path.resolve()));m=trimesh.load(path,force='mesh',process=False);save('provenance/HISTORICAL_OPEN3D_COMPARISON.json',dict(asset=asset(path),source='E3-D0 G1 original six-source native Open3D, .1mm voxels, uncleaned; GLB numeric units mm by historical export',input_to_NeuralFusion=False,matched_to_new_eight=False));return m
def figure2():
    fig,axes=plt.subplots(4,6,figsize=(23,17));p=protocol();summary=load(R/'metrics/PREFIX_SUMMARY.json');old=historical_o3d()
    for k,(scene,ii)in enumerate(p['orders'].items()):
        cells=axes[k*2:(k+1)*2].ravel();panel(cells[0],scene,raw_combined(scene),'Original HERO surfaces (display concatenation)')
        if k==0:panel(cells[1],scene,old,'Historical Open3D G1 — different 6 inputs / 0.1mm')
        else:cells[1].axis('off');cells[1].text(.1,.5,'Historical G06 Open3D\nNOT_AVAILABLE\nNo new TSDF invented',transform=cells[1].transAxes)
        for j in range(len(ii)):
            tag=f'{scene}_forward_F{j}';panel(cells[2+j],scene,output(tag),f'{scene} F{j} ({j+1} views)')
        slot=2+len(ii);panel(cells[slot],scene,output(f'{scene}_reverse_F{len(ii)-1}'),scene+' strict reverse final')
        for a in cells[slot+1:]:a.axis('off')
        ax=cells[-1];ax.axis('on')
        for order,style in [('forward','-o'),('reverse','--s')]:
            rr=[r for r in summary if r['scene']==scene and r['order']==order];ax.plot([r['view_N']for r in rr],[r['agree_fraction']for r in rr],style,label=order)
        ax.set(title='Fixed all-source first-hit agreement <=0.25mm',xlabel='views',ylabel='fraction',ylim=(0,1));ax.legend(fontsize=8);ax.grid(alpha=.25)
    finish(fig,'Fig2_Raw_Open3D_All_Prefixes.png','All original outputs at fixed per-group millimetre display cameras; black = unchanged CAD')
def figure3():
    fig,axes=plt.subplots(5,4,figsize=(18,21));p=protocol();scene='G01_004'
    for j,stage in enumerate([0,2,4,7]):
        center=np.median(np.concatenate([cleaned(c)['X']for c in p['orders'][scene]]),axis=0)
        tag=f'{scene}_forward_F{stage}';m=output(tag);panel(axes[0,j],scene,m,f'F{stage}: body detail / flat normals',zoom=1.8,offset=center);panel(axes[1,j],scene,m,f'F{stage}: side detail / unchanged geometry',side=True,zoom=1.8,offset=center)
        panel(axes[2,j],scene,m,f'F{stage}: same body detail / smooth normals',smooth=True,zoom=1.8,offset=center)
    scene='G06_004'
    for j,stage in enumerate([0,1,3,4]):panel(axes[3,j],scene,output(f'{scene}_forward_F{stage}'),f'G06 F{stage} side view / flat',side=True)
    # Actual final Translator SDF slab and interpolated zero-contours; no fabricated reconstruction.
    for j,scene in enumerate(p['orders']):
        n=len(p['orders'][scene])-1;tag=f'{scene}_forward_F{n}';f=np.load(R/'local_results'/f'{tag}_field.npz');known=f['known'];slab=int(np.argmax(known.sum((0,2))));a=f['sdf_raw'][:,slab,:].T*p['domains'][scene]['L_mm'];valid=known[:,slab,:].T;ax=axes[4,2*j];im=ax.imshow(np.ma.masked_where(~valid,a),origin='lower',cmap='coolwarm',vmin=-.5,vmax=.5);ax.contour(f['sdf_MC_unknown_positive_sentinel'][:,slab,:].T,levels=[0],colors='black',linewidths=.4);ax.set(title=f'{scene} actual Translator SDF (mm)\ny-index={slab}; black=MC iso0; white=unqueried',xlabel='x voxel',ylabel='z voxel');fig.colorbar(im,ax=ax,fraction=.045)
        ax=axes[4,2*j+1];verts=np.load(R/'local_results'/f'{tag}_MC_identity.npz')['vertices_index_float'];fractions=np.mod(verts,1);fractional=fractions[(fractions>1e-5)&(fractions<1-1e-5)];ax.hist(fractional,bins=30,color='steelblue');ax.set(title=f'{scene}: floating MC coordinates\nNo rounding / no cube-face export',xlabel='fractional coordinate within voxel',ylabel='coordinate count')
    finish(fig,'Fig3_TSDF_Mesh_Shading_Details.png','Actual TSDF → floating Marching Cubes; flat vs smooth-normal display changes no geometry')
def real_render(cid,tag):
    s=native(cid);h,w=s['depth'].shape;vv,uu=np.mgrid[:h,:w];uv=np.c_[uu.ravel(),vv.ravel()];m=output(tag);ds=mesh_scene(m.vertices,m.faces);result=ds.cast_rays(o3d.core.Tensor(vis.camera_rays(uv,s['Kn'],s['T']).astype(np.float32)));hit=result['t_hit'].numpy().astype(float);fid=result['primitive_ids'].numpy().astype(np.int64);cad,_=cast(ringscene(s['c']['scene_id']),uv,s['Kn'],s['T']);evaluation=np.load(R/'local_results'/f'{tag}_evaluation.npz');categories=evaluation['mesh_face_category'];img=np.ones((h*w,3));ok=np.isfinite(hit);cat=categories[fid[ok]];img[ok]=np.array([COLORS[0]if c=='OBSERVED_NEAR_PROXY'else(COLORS[1]if c=='INFERRED_UNSUPPORTED_PROXY'else COLORS[2])for c in cat]);black=np.isfinite(cad)&(cad<=hit+.002);img[black]=0
    return img.reshape(h,w,3),hit.reshape(h,w),cad.reshape(h,w)
def figure4():
    fig,axes=plt.subplots(4,4,figsize=(21,15));examples=['G01_004_ref08','G01_004_ref13','G06_004_ref04','G06_004_new_r00']
    for i,cid in enumerate(examples):
        s=native(cid);scene=s['c']['scene_id'];last=len(protocol()['orders'][scene])-1;tag=f'{scene}_forward_F{last}';rgb=s['native_RGB'].copy();curves,_=cv2.findContours((s['native_labels']==1).astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(rgb,curves,-1,(0,255,0),1);axes[i,0].imshow(rgb);axes[i,0].set_title(cid+' actual RGB + original Mask');axes[i,0].axis('off')
        img,hit,cad=real_render(cid,tag);axes[i,1].imshow(img);axes[i,1].set_title('Final first visible Mesh / black CAD\ngreen near input; orange inferred; purple unknown');axes[i,1].axis('off')
        visible=s['valid']&~(np.isfinite(cad)&(s['depth']>cad+.002));err=hit-s['depth'];a=np.ma.masked_where(~visible|~np.isfinite(hit),err);cmap=plt.get_cmap('coolwarm').copy();cmap.set_bad('white');im=axes[i,2].imshow(a,cmap=cmap,vmin=-1,vmax=1);yy,xx=np.nonzero(visible&~np.isfinite(hit));axes[i,2].scatter(xx,yy,s=.15,c='magenta');axes[i,2].set_title('Actual first hit minus original HERO (mm)\nwhite=no eligible observation; magenta=MISS');axes[i,2].axis('off');fig.colorbar(im,ax=axes[i,2],fraction=.025)
        # Fixed input-only profile: row containing the largest original Polyp span.
        row=int(np.argmax((s['native_labels']==1).sum(1)));_,first,_=real_render(cid,f'{scene}_forward_F0');u=np.arange(s['depth'].shape[1]);mask=s['valid'][row];depth=np.where(mask,s['depth'][row],np.nan);axes[i,3].plot(u,depth,'k.',ms=1.5,label='original HERO');axes[i,3].plot(u,np.where(mask,first[row],np.nan),color='grey',lw=.8,label='F0 first');axes[i,3].plot(u,np.where(mask,hit[row],np.nan),color='tab:blue',lw=.8,label='final first');axes[i,3].set(title=f'Actual camera ray row={row} (input-chosen)',xlabel='native u pixel',ylabel='axial Z mm');axes[i,3].legend(fontsize=7);axes[i,3].grid(alpha=.2)
    finish(fig,'Fig4_RealRGB_FirstHits_Caps.png','Real-camera first intersections and approximate surface evidence — not physical ground truth')
def main():
    figure1();figure2();figure3();figure4();save('provenance/FIGURE_INPUTS.json',dict(code=asset(Path(__file__)),real_geometry_only=True,geometry_smoothing=False,GT=False))
if __name__=='__main__':main()
