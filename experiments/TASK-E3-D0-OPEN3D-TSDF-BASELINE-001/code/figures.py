"""Actual triangle ray casting and source XYZ; no texture plane, synthetic mesh or repair."""
from hero_tsdf_adapter import *
from matplotlib.colors import Normalize
plt=vis.configure();plt.rcParams.update({'font.size':9,'axes.titlesize':10})
from visualization.same_camera_scene import SameCameraScene

def raw_mesh(cid):
    s=source(cid);m=trimesh.Trimesh(vertices=s['P'],faces=s['F'],process=False);m.visual.vertex_colors=np.c_[s['RGB'][s['uv'][:,1],s['uv'][:,0]],np.full(len(s['P']),255,np.uint8)];return m

def group_mesh(ids):return trimesh.util.concatenate([raw_mesh(cid)for cid in ids])
class ActualRenderer:
    def __init__(self,m):
        self.m=m;self.scene=o3d.t.geometry.RaycastingScene(nthreads=2)
        for mesh in [m,ringmesh()]:self.scene.add_triangles(o3d.core.Tensor(np.asarray(mesh.vertices,np.float32)),o3d.core.Tensor(np.asarray(mesh.faces,np.uint32)))
    def rays(self,rays,shape):
        rr=self.scene.cast_rays(o3d.core.Tensor(np.asarray(rays,np.float32)));hit=np.isfinite(rr['t_hit'].numpy());g=rr['geometry_ids'].numpy();f=rr['primitive_ids'].numpy();rgb=np.ones((len(rays),4),float);rgb[:,:3]=.975;rgb[:,3]=hit
        ii=np.flatnonzero(hit&(g==0));b=rr['primitive_uvs'].numpy()[ii];bc=np.c_[1-b.sum(1),b];cols=np.asarray(self.m.visual.vertex_colors[:,:3],float)/255.;tri=self.m.faces[f[ii]];col=np.einsum('ij,ijk->ik',bc,cols[tri]);n=rr['primitive_normals'].numpy()[ii];light=-np.asarray(rays)[ii,3:];light/=np.linalg.norm(light,axis=1)[:,None];shade=.55+.45*abs(np.einsum('ij,ij->i',n,light));rgb[ii,:3]=np.clip(col*shade[:,None],0,1);rgb[hit&(g==1),:3]=.025
        return rgb.reshape(*shape,4)
    def camera(self,s):
        v,u=np.mgrid[0:360,0:640];return self.rays(vis.camera_rays(np.c_[u.ravel(),v.ravel()],s['K'],s['T']),(360,640))
    def ortho(self,angle,bounds,N=520):
        eye,right,up=vis.basis(angle);x=np.linspace(*bounds[0],N);y=np.linspace(bounds[1][1],bounds[1][0],N);xx,yy=np.meshgrid(x,y);P=xx.ravel()[:,None]*right+yy.ravel()[:,None]*up+200*eye;dirs=np.broadcast_to(-eye,P.shape);return self.rays(np.c_[P,dirs],(N,N))

def bounds_for(P,angle):
    _,r,u=vis.basis(angle);Q=np.c_[P@r,P@u];lo=Q.min(0);hi=Q.max(0);ctr=(hi+lo)/2;radius=max(hi-lo)*.55;return [[v-radius,v+radius]for v in ctr]
def local_bounds(X,angle,radius=2.5):
    _,r,u=vis.basis(angle);return [[float(X@v-radius),float(X@v+radius)]for v in [r,u]]
def show_ortho(ax,renderer,angle,bounds,title='',axes=True):
    im=renderer.ortho(angle,bounds);ax.imshow(im[:,:,:3],extent=(*bounds[0],*bounds[1]),origin='upper');ax.set_aspect('equal');ax.set_title(title);ax.set_xlabel('视平面横向 / mm');ax.set_ylabel('视平面纵向 / mm');length=5 if np.ptp(bounds[0])>20 else 1;x=bounds[0][0]+.06*np.ptp(bounds[0]);y=bounds[1][0]+.07*np.ptp(bounds[1]);ax.plot([x,x+length],[y,y],c='black',lw=2);ax.text(x,y+.04*np.ptp(bounds[1]),f'{length:g} mm',fontsize=8)
    if not axes:ax.set_xticks([]);ax.set_yticks([])
def rgb_mask(ax,s,title='真实 RGB + 原始 Mask'):
    ax.imshow(s['RGB']);ax.contour(s['labels']==1,levels=[.5],colors=['#41e76c'],linewidths=.65);ax.contour(s['labels']==2,levels=[.5],colors=['#22baff'],linewidths=.65);ax.set_title(title);ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_aspect('equal');ax.axis('off')
def finish(fig,name,text):
    fig.text(.5,.01,text,ha='center',fontsize=9);fig.tight_layout(rect=(0,.035,1,.96));fig.savefig(R/'figures'/name,dpi=170,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)
def fig1():
    s=source('G01_004_ref08');raw=raw_mesh(s['id']);single=output_mesh('SINGLE');control=output_mesh('SINGLE_RESOLUTION_CONTROL');angle=(-65,22);bounds=bounds_for(np.r_[raw.vertices,single.vertices,control.vertices,ringmesh().vertices],angle)
    fig,ax=plt.subplots(2,3,figsize=(15,9));fig.suptitle('Fig 1 | HERO → Open3D TSDF 单来源适配；ref08，真实原始几何与官方融合',fontsize=15)
    for j,(m,title)in enumerate([(raw,'原始 HERO Mesh / 原三角面'),(single,'官方 TSDF / 0.10 mm（主实验）'),(control,'唯一预登记对照 / 0.05 mm')]):show_ortho(ax[0,j],ActualRenderer(m),angle,bounds,title)
    rgb_mask(ax[1,0],s);scene=SameCameraScene(ringmesh(),s['K'],s['T'],(640,360),VENDOR);scene.scale_bar(ax[1,0]);ax[1,1].imshow(s['RGB']);ax[1,1].imshow(ActualRenderer(single).camera(s));ax[1,1].contour(s['labels']==1,[.5],colors=['#41e76c'],linewidths=.65);ax[1,1].set_title('主实验 Mesh + 黑色 CAD / 冻结 ref08 相机');ax[1,1].axis('off');scene.scale_bar(ax[1,1])
    a=HEROToTSDFAdapter.from_source(s,cfg()['depth_trunc_mm']);v,u=np.nonzero(a.valid);uv=np.c_[u,v];z=s['depth'][v,u]
    for name,m,color in [('0.10 mm',single,'#bb3b26'),('0.05 mm',control,'#266eb5')]:
        h,_=cast(mesh_scene(m.vertices,m.faces),uv,s['Kn'],s['T']);err=abs(h-z);xx=np.linspace(0,.25,200);ax[1,2].plot(xx,[(err<=t).mean()for t in xx],label=name,color=color)
    ax[1,2].axhline(.9,c='gray',ls='--');ax[1,2].set(xlabel='轴向绝对误差阈值 / mm',ylabel='全部 13,749 条输入射线比例',ylim=(0,1.02),title='固定分母：未命中仍计入失败');ax[1,2].legend();ax[1,2].grid(alpha=.2)
    finish(fig,'Fig1_adapter_validation.png','全部原面及输出面保留；黑色为冻结 Ring CAD；绿色 Polyp Mask / 蓝色 Ring Mask；工程总门槛 FAIL 保留。')
def fig2():
    raw=group_mesh(CORE);m0=output_mesh('G0');m1=output_mesh('G1');renderers=[ActualRenderer(m)for m in [raw,m0,m1]];s=source('G01_004_ref08');P=np.r_[raw.vertices,m0.vertices,m1.vertices,ringmesh().vertices]
    fig,ax=plt.subplots(3,3,figsize=(15,13));fig.suptitle('Fig 2 | 原始 CORE 对照 → G0 → G1；同一世界坐标，所有碎片与延伸保留',fontsize=15)
    for j,(ren,title)in enumerate(zip(renderers,['三个原始 HERO Mesh 并列（无融合）','G0 / 3 CORE','G1 / 6 来源，5 视角区'])):
        ax[0,j].imshow(ren.camera(s)[:,:,:3]);ax[0,j].set_title(title+'\n冻结 ref08 真实相机');ax[0,j].axis('off');SameCameraScene(ringmesh(),s['K'],s['T'],(640,360),VENDOR).scale_bar(ax[0,j])
    for i,angle,label in [(1,(0,0),'侧向'),(2,(45,35),'世界轴')]:
        bounds=bounds_for(P,angle)
        for j,ren in enumerate(renderers):
            show_ortho(ax[i,j],ren,angle,bounds,label+'；三列同尺度')
            if i==2:
                _,right,up=vis.basis(angle);base=np.array([bounds[0][0]+5,bounds[1][0]+5])
                for xyz,col,lab in zip(np.eye(3)*5,['#ce3d32','#248a3d','#2460cc'],'XYZ'):
                    q=np.array([xyz@right,xyz@up]);ax[i,j].arrow(*base,*q,color=col,width=.08,length_includes_head=True);ax[i,j].text(*(base+q),lab,color=col)
    finish(fig,'Fig2_global_fusion.png','正交两行包含全部 G1 远端碎片；主体细节见 Fig 3。真实相机行受原始视野限制，未移动相机以追踪远端碎片。单位 mm，无 GT。')
def fig3():
    raw=group_mesh(G1);r=[ActualRenderer(m)for m in [raw,output_mesh('G0'),output_mesh('G1')]];s=source('G01_004_ref08');P=s['P'];cases=load(R/'config/FAILURE_CASES.json');faceX=P[s['F']].mean(1);side=faceX[np.argsort(faceX[:,0])[int(.95*len(faceX))]];centers=[P[np.argmax(P[:,2])],side,P[np.argsort(P[:,2])[int(.1*len(P))]],np.array([cases[3][k]for k in ['X_mm','Y_mm','Z_mm']]),np.array([cases[0][k]for k in ['X_mm','Y_mm','Z_mm']])];labels=['上表面 / 头部候选（解剖未认证）','侧面候选；原面 X 的第95百分位','低位细结构 / 可能细柄（未认证）','远端异常；原 Mesh 无对应面','接缝 / 丢失区；F1']
    fig,ax=plt.subplots(5,3,figsize=(13,17));fig.suptitle('Fig 3 | 固定局部窗比较；原始六来源几何始终在左列',fontsize=15)
    for i,(X,label)in enumerate(zip(centers,labels)):
        angle=(-65,22)if i!=1 else (0,0);bounds=local_bounds(X,angle)
        for j,ren in enumerate(r):
            show_ortho(ax[i,j],ren,angle,bounds,['原始 HERO 原三角面','G0','G1'][j]+' | '+label,False)
            _,right,up=vis.basis(angle);ax[i,j].plot(X@right,X@up,'+',color='#2771ba',ms=7)
    save('config/FIG3_WINDOWS.json',dict(centers_mm=centers,labels=labels,halfwidth_mm=2.5,anatomy_certified=False))
    finish(fig,'Fig3_details_and_errors.png','每行共享 5 × 5 mm 窗口；无表面处保持空白。细柄身份及真实背面均未认证，不将 TSDF 孤立面解释为解剖结构。')
def fig4():
    cases=load(R/'config/FAILURE_CASES.json');render=[ActualRenderer(output_mesh(n))for n in ['G0','G1']];scenes=[mesh_scene(output_mesh(n).vertices,output_mesh(n).faces)for n in ['G0','G1']]
    fig,ax=plt.subplots(4,5,figsize=(21,13));fig.suptitle('Fig 4 | 实际位置诊断：OBSERVED 观测；原因 HYPOTHESIS / UNRESOLVED',fontsize=15)
    for i,case in enumerate(cases):
        s=source(case['source_id']);u,v=case['pixel_u'],case['pixel_v'];uv0=np.array([u,v]);lo=np.maximum(uv0-35,[0,0]);hi=np.minimum(uv0+35,[639,359]);rgb_mask(ax[i,0],s,case['case_id']+' / '+s['id']+'\n真实 RGB，蓝十字为待诊断位置');ax[i,0].plot(u,v,'+',c='#22aaff',ms=8);ax[i,0].set_xlim(lo[0],hi[0]);ax[i,0].set_ylim(hi[1],lo[1]);ax[i,0].axis('on');ax[i,0].set_xlabel('原图 u / px')
        pix,z=vis.project_camera(s['P'],s['K'],s['T']);keep=(abs(pix[:,0]-u)<=35)&(abs(pix[:,1]-v)<=35);ax[i,1].imshow(s['RGB']);sc=ax[i,1].scatter(pix[keep,0],pix[keep,1],c=z[keep],cmap='viridis',s=3,linewidths=0);ax[i,1].plot(u,v,'+',c='#22aaff',ms=8);ax[i,1].set(xlim=(lo[0],hi[0]),ylim=(hi[1],lo[1]),title='原始 HERO XYZ / 原身份\nFace '+str(case.get('original_face_id')));ax[i,1].set_aspect('equal');fig.colorbar(sc,ax=ax[i,1],fraction=.045,pad=.02,label='Z / mm')
        for j,ren in enumerate(render):
            ax[i,j+2].imshow(s['RGB']);ax[i,j+2].imshow(ren.camera(s));ax[i,j+2].plot(u,v,'+',c='#22aaff',ms=8);ax[i,j+2].set(xlim=(lo[0],hi[0]),ylim=(hi[1],lo[1]),title=['G0','G1'][j]+' 实际 Mesh + CAD');ax[i,j+2].set_aspect('equal')
        # One actual source-camera horizontal ray fan, all missing predictions stay NaN.
        uu=np.arange(max(0,int(u)-35),min(640,int(u)+36));vv=np.full_like(uu,int(round(v)));uv=np.c_[uu,vv];orig=np.load(s['c']['pack'])['depth_mm'][vv,uu];lab=s['labels'][vv,uu];orig=np.where(lab==1,orig,np.nan)
        ax[i,4].plot(uu,orig,'.-',c='gray',lw=.7,ms=2,label='原始 HERO depth')
        rawhit,_=cast(mesh_scene(s['P'],s['F']),uv,s['K'],s['T']);rawhit[~np.isfinite(rawhit)]=np.nan;ax[i,4].plot(uu,rawhit,':',c='#248a3d',label='原 Mesh first hit')
        for j,(scene,col)in enumerate(zip(scenes,['#cc4935','#276ac0'])):
            h,_=cast(scene,uv,s['K'],s['T']);h[~np.isfinite(h)]=np.nan;ax[i,4].plot(uu,h,color=col,lw=1,label=['G0','G1'][j])
        ringz,_=cast(ringscene(),uv,s['K'],s['T']);ringz[~np.isfinite(ringz)]=np.nan;ax[i,4].plot(uu,ringz,c='black',lw=1,label='CAD first hit');ax[i,4].axvline(u,c='#22aaff',lw=.7);ax[i,4].set(xlabel='真实相机水平射线 u / px',ylabel='轴向深度 / mm',title=case['case_id']+' OBSERVED\n原因仍为 HYPOTHESIS / UNRESOLVED');ax[i,4].legend(fontsize=6,ncol=2);ax[i,4].grid(alpha=.2)
    finish(fig,'Fig4_failure_mechanisms.png','F1 主体丢失；F2 ref08 局部变化（近邻距离仍小）；F3 r04 改善对照；F4 后验远端异常。曲线为合法相机射线；断线表示无命中。')
if __name__=='__main__':
    fig1();fig2();fig3();fig4()
