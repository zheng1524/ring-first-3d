"""Scientific figures from actual meshes, fixed source cameras and recorded metrics."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import open3d as o3d
plt.rcParams.update({'font.size':8,'axes.titlesize':9})
COLORS={'P0':'#989da2','Baseline':'#3285bf','RingAware':'#e5a23a'}
def edge(ax,a,color):
    cs,_=cv2.findContours(a.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    for c in cs:ax.plot(c[:,0,0],c[:,0,1],color=color,lw=.9)
def output(fig,name):
    p=R/'figures'/name;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=160,bbox_inches='tight');plt.close(fig)
def actual_mesh_image(V,F,RV,RF,V0,elev,azim,color):
    # Fixed viewer from P0+Ring bounds, NOT optimized or GT geometry.
    allv=np.r_[V0,RV];center=(allv.min(0)+allv.max(0))/2;rad=np.linalg.norm(allv-center,axis=1).max();el,az=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
    forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);T=np.eye(4);T[:3,:3]=np.array([right,down,forward]).T;T[:3,3]=pos
    h=w=400;K=np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]])
    rt=o3d.t.geometry.RaycastingScene(nthreads=2)
    for v,f in[(V,F),(RV,RF)]:rt.add_triangles(o3d.core.Tensor(np.asarray(v,np.float32)),o3d.core.Tensor(np.asarray(f,np.uint32)))
    yy,xx=np.mgrid[:h,:w];d=np.c_[xx.ravel(),yy.ravel(),np.ones(h*w)]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(pos,d.shape),d@T[:3,:3].T].astype(np.float32);hit=rt.cast_rays(o3d.core.Tensor(rays));gid=hit['geometry_ids'].numpy();fid=hit['primitive_ids'].numpy();rgb=np.full((h*w,3),.96)
    for idx,(v,f,col)in enumerate([(V,F,matplotlib.colors.to_rgb(color)),(RV,RF,(.035,.035,.035))]):
        sel=gid==idx;normal=trimesh.Trimesh(v,f,process=False).face_normals;light=(pos-center)/np.linalg.norm(pos-center);shade=.50+.50*np.maximum(0,normal[fid[sel]]@light);rgb[sel]=np.array(col)*shade[:,None]
    # Pixel scale at fixed viewer-center depth, visibly labeled approximate for perspective.
    return np.clip(rgb.reshape(h,w,3),0,1),490./np.linalg.norm(pos-center)
def main():
    frozen=load(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json')
    for a in frozen['files']:assert sha(a['path'])==a['sha256'],a['path']
    official=np.load(R/'local_results/official/RENDER_COMPARISON.npz');repl=load(R/'metrics/OFFICIAL_REPRODUCTION.json')
    fig,axs=plt.subplots(3,4,figsize=(12,8))
    for i,k in enumerate(['target','initial','final']):
        for j in range(4):axs[i,j].imshow(official[k][j],cmap='gray',vmin=0,vmax=1);axs[i,j].axis('off');axs[i,j].set_title(k+' | official view '+str([0,5,10,15][j]))
    fig.suptitle('Official cow multi-view silhouette-only reproduction | 2000 SGD updates\nFull 20-view MSE %.6f -> %.6f; actual exported/reloaded Mesh, no project GT used'%(repl['initial_full_silhouette_L2'],repl['final_full_silhouette_L2']));fig.tight_layout(rect=[0,0,1,.92]);output(fig,'Fig1_Official_Reproduction.png')
    # Three representative views, classification positions and actual foreground order.
    fig,axs=plt.subplots(3,5,figsize=(19,10));audit=load(R/'metrics/OCCLUSION_AUDIT.json')
    for i,(name,cid)in enumerate([('virtual','IIa6.5_R10_obs01'),('real','G01_004_ref08'),('real','G01_004_ref03')]):
        a=np.load(R/'inputs'/name/(cid+'.npz'));s=np.load(R/'inputs'/name/(cid+'_SIDES.npz'));lab=a['labels'];rv=np.load(R/'inputs'/name/'RING.npz');pv=np.load(R/'inputs'/name/'INITIAL.npz');cz=cast(scene(rv['V'],rv['F']),a['K'],a['T'],360,640);pz=cast(scene(pv['V'],pv['F']),a['K'],a['T'],360,640);samples=load(R/'metrics/sides'/(cid+'.json'))
        axs[i,0].imshow(a['RGB']);edge(axs[i,0],lab==1,'lime');edge(axs[i,0],lab==2,'cyan');axs[i,0].set_title(cid+'\n'+('Blender labels; not clinical RGB'if name=='virtual'else'Original real RGB + frozen Masks'))
        axs[i,1].imshow(a['RGB']);axs[i,1].imshow(np.ma.masked_where(s['classes']==0,s['classes']),cmap=ListedColormap(['black','#288be3','#f6a623','#858585','#b7b7b7']),vmin=0,vmax=4,alpha=.75);axs[i,1].set_title('A blue / B orange / C gray / D lightgray')
        axs[i,2].imshow(a['RGB'])
        shown=[r for r in samples if'sites'in r][::max(1,len(samples)//12)]
        for r in shown:
            x=np.array(r['exits']);p=np.array(r['sites']).reshape(-1,2);col=['#288be3','#f6a623','#858585','#b7b7b7']['ABCD'.index(r['class_final'])];axs[i,2].plot(x[:,0],x[:,1],c=col,lw=1);axs[i,2].scatter(p[:,0],p[:,1],c='yellow',s=8)
        axs[i,2].set_title('Actual local sections and sample sites')
        rel=np.zeros(lab.shape);rel[np.isfinite(pz)&np.isfinite(cz)&(pz>cz+.05)]=1;rel[np.isfinite(pz)&np.isfinite(cz)&(pz<cz-.05)]=2
        axs[i,3].imshow(a['RGB']);axs[i,3].imshow(np.ma.masked_where(rel==0,rel),vmin=0,vmax=2,cmap=ListedColormap(['white','#288be3','red']),alpha=.8);edge(axs[i,3],np.isfinite(cz),'black');axs[i,3].set_title('CAD before body blue / front conflict red')
        effective=np.load(R/'local_results/occlusion_audit'/(cid+'.npz'))['effective_RGB'];effective=cv2.resize(effective,(640,360),interpolation=cv2.INTER_NEAREST)
        axs[i,4].imshow(effective);axs[i,4].set_title('Green positive / blue relaxed-negative\nred front conflict / gray background')
        for ax in axs[i]:ax.axis('off')
    fig.suptitle('Ring evidence BEFORE optimization | 2D neighbor and CAD evidence are complementary\nCategories are confidence proxies, not hidden-surface GT. Exact differentiable weights and gradient tests are saved separately.');fig.tight_layout(rect=[0,0,1,.93]);output(fig,'Fig2_Ring_Occlusion_Audit.png')
    gt=np.load(OLD/'audit_only/NATIVE_CAD_GT.npz');fig,axs=plt.subplots(4,4,figsize=(16,15))
    for ci,name in enumerate(['virtual','real']):
        init=np.load(R/'inputs'/name/'INITIAL.npz');rr=np.load(R/'inputs'/name/'RING.npz');modes=[('Native Blender GT',gt,'#bf858d')]if name=='virtual'else[('No real full 3D GT',None,'black')]
        modes += [('P0',init,COLORS['P0'])]+[(arm,np.load(R/'local_results'/name/arm/'FINAL.npz'),COLORS[arm])for arm in['Baseline','RingAware']]
        for ai,(el,az)in enumerate([(30,-65),(10,-90)]):
            for j,(label,m,col)in enumerate(modes):
                ax=axs[ci*2+ai,j]
                if m is None:
                    d=np.load(R/'inputs/real/G01_004_ref08.npz');ax.imshow(d['RGB']);ax.text(.05,.04,'GT accuracy: NOT_EVALUABLE',transform=ax.transAxes,c='yellow')
                else:
                    image,pxmm=actual_mesh_image(m['V'],m['F'],rr['V'],rr['F'],init['V'],el,az,col);ax.imshow(image);ax.plot([20,20+2*pxmm],[375,375],c='black',lw=2);ax.text(20,365,'2 mm at view-center depth',fontsize=7)
                ax.axis('off');ax.set_title(name+' | '+label+'\n'+('common oblique'if ai==0 else'common low side view'))
    fig.suptitle('ACTUAL raw Meshes, black fixed CAD Ring | all project outputs at step 300\nNo smoothing, trimming, filling, GT selection or geometry repair. Each case uses its own unchanged metric frame.');fig.tight_layout(rect=[0,0,1,.95]);output(fig,'Fig3_Actual_Mesh_Comparison.png')
    summary=load(R/'metrics/SUMMARY.json');fig,axs=plt.subplots(2,3,figsize=(15,8))
    for name,ls in[('virtual','-'),('real','--')]:
        for arm in['Baseline','RingAware']:
            rows=list(csv.DictReader((R/'metrics'/(name+'_'+arm+'_TRAINING.csv')).open()));axs[0,0].semilogy([int(r['step'])for r in rows],[float(r['total'])for r in rows],ls,c=COLORS[arm],alpha=.8,label=name+' '+arm)
            sr=[r for r in summary if r['case']==name and r['arm']in['P0',arm]]
            for ax,key in[(axs[0,1],'fit_IoU'),(axs[0,2],'holdout_IoU'),(axs[1,2],'volume_mm3')]:ax.plot([r['step']for r in sr],[r[key]for r in sr],ls+'o',c=COLORS[arm],label=name+' '+arm,ms=4)
            if name=='virtual':
                for ax,key in[(axs[1,0],'Chamfer_MAE_mm'),(axs[1,1],'symmetric_difference_mm3')]:ax.plot([r['step']for r in sr],[r[key]for r in sr],ls+'o',c=COLORS[arm],label=arm,ms=4)
    for ax,title,unit in zip(axs.ravel(),['Actual optimization losses (different ring term)','Full-Mask FIT IoU','Full-Mask HOLDOUT IoU','Independent virtual GT Chamfer MAE','Independent virtual GT difference volume proxy','Raw Mesh net volume'],['loss','IoU','IoU','mm','mm3','mm3']):ax.set(title=title,xlabel='optimizer steps',ylabel=unit);ax.grid(alpha=.2);ax.legend(fontsize=6)
    fig.suptitle('Fixed budget and saved 0/100/200/300 stages; GT read only AFTER prediction freeze\nReal holdout is update-stage only; virtual has no A/B Ring-contact evidence. IoU is not 3D accuracy.');fig.tight_layout(rect=[0,0,1,.92]);output(fig,'Fig4_Training_And_Independent_Evaluation.png')
    for name in['virtual','real']:
        meta=getcase(name);fig,axs=plt.subplots(len(meta['views']),4,figsize=(14,3*len(meta['views'])),squeeze=False)
        for i,v in enumerate(meta['views']):
            cid=v['id'];a=np.load(R/'inputs'/name/(cid+'.npz'));axs[i,0].imshow(a['RGB']);axs[i,0].set_title(cid+' '+v['role'])
            for j,arm in enumerate(['P0','Baseline','RingAware'],1):
                e=np.load(R/'local_results/eval'/(name+'_'+arm+'_'+cid+'.npz'));ax=axs[i,j];ax.imshow(a['RGB']);edge(ax,e['target'],'lime');edge(ax,e['pred'],COLORS[arm]);edge(ax,e['front_conflict'],'red');ax.set_title(arm+' | target green, prediction colored, front conflict red')
            for ax in axs[i]:ax.axis('off')
        fig.tight_layout();output(fig,'full/Projection_'+name+'.png')
    print('Four core figures and full fixed-view projections generated',flush=True)
if __name__=='__main__':main()
