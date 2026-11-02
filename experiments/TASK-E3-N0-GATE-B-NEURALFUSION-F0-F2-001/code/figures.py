"""True original/output meshes, fixed cameras and metric scale. CPU rendering."""
from common import *
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb
from scipy.ndimage import map_coordinates
plt=vis.configure();plt.rcParams.update({'font.size':10,'axes.titlesize':11})
dom=cfg()['domain'];lo=np.array(dom['world_cube_min_mm']);hi=np.array(dom['world_cube_max_mm'])
def axes3(ax):
    ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm');ax.set_box_aspect(hi-lo);ax.view_init(20,-65)
def mesh3(ax,m,color='#c3b4aa',facecolors=None):
    triangles=np.asarray(m.vertices)[np.asarray(m.faces)]
    if facecolors is None:
        normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-10)
        light=np.array([.3,-.5,1]);light/=np.linalg.norm(light);shade=.4+.6*np.abs(normal@light)
        facecolors=np.clip(np.asarray(to_rgb(color))[None,:]*shade[:,None],0,1)
    ax.add_collection3d(Poly3DCollection(triangles,facecolors=facecolors,edgecolors='none'))
    cad=ringmesh();ax.add_collection3d(Poly3DCollection(np.asarray(cad.vertices)[np.asarray(cad.faces)],facecolors='black',edgecolors='none'));axes3(ax)
def rawmesh():
    s=original(CORE[0]);return trimesh.Trimesh(s['P'],s['F'],process=False)
def render(m,K,T,shape=(640,352)):
    W,H=shape;u,v=np.meshgrid(np.arange(W),np.arange(H));uv=np.c_[u.ravel(),v.ravel()]
    rays=vis.camera_rays(uv,K,T).astype(np.float32);sc=mesh_scene(m.vertices,m.faces);hit=sc.cast_rays(o3d.core.Tensor(rays))
    depth=hit['t_hit'].numpy();norm=hit['primitive_normals'].numpy();ok=np.isfinite(depth)
    light=-rays[:,3:];light/=np.linalg.norm(light,axis=1,keepdims=True)
    shade=.3+.65*np.abs(np.sum(norm*light,axis=1))
    img=np.ones((W*H,3));img[ok]=shade[ok,None]*np.array([.96,.91,.86])
    cad=ringscene().cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();cb=np.isfinite(cad)&((~ok)|(cad<=depth+.002));img[cb]=.025
    return img.reshape(H,W,3)
def window(cid):
    s=native(cid,'V2');u,v=s['uv'].T;return u.min()-12,u.max()+12,v.min()-12,v.max()+12
def view_image(ax,img,cid,title):
    a,b,c,d=window(cid);ax.imshow(img);ax.set(xlim=(a,b),ylim=(d,c),title=title);ax.axis('off')
def finish(fig,name):
    fig.text(.5,.008,'G01_004真实数据；黑色Ring为冻结CAD，单位mm；F0仅ref08。Mesh未删面/平滑/补洞；GT未用；F1/F2因F0失败未运行。',ha='center',fontsize=9)
    if name!='Fig2_Real_Projection_First_Depth.png':fig.tight_layout(rect=(0,.03,1,.96))
    fig.savefig(R/'figures'/name,dpi=155,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)
def main():
    n=native(CORE[0],'V2');K,T=n['K'],n['T']
    ms=[rawmesh(),output_mesh('O3D','V6','F0'),output_mesh('NN','V6','F0')]
    titles=['原始HERO ref08 / 历史Raw原三角面','Matched Open3D / V6 F0','官方预训练NeuralFusion / V6 F0 / FAIL']
    fig=plt.figure(figsize=(19,12));fig.suptitle('图1 | 同观察相机、同毫米坐标：原始HERO / 同条件Open3D / NeuralFusion',fontsize=15)
    for k,(m,title)in enumerate(zip(ms,titles)):
        ax=fig.add_subplot(2,3,k+1);view_image(ax,render(m,K,T),CORE[0],title+'\n统一灰色材质，非真实RGB贴图')
        ax=fig.add_subplot(2,3,k+4,projection='3d');mesh3(ax,m);ax.set_title(title+f'\n{len(m.faces):,}个原输出面全部保留')
    finish(fig,'Fig1_Real_Mesh_Comparison_F0.png')
    fig=plt.figure(figsize=(18,13));fig.suptitle('图2 | 首层可见深度：真实RGB、Open3D与NeuralFusion；ref13/ref03只作留出检查',fontsize=15)
    for i,cid in enumerate(CORE):
        raw=original(cid);ax=fig.add_subplot(3,3,i*3+1);rgb=cv2.resize(raw['RGB'],(640,352),interpolation=cv2.INTER_AREA);view_image(ax,rgb,cid,cid.replace('G01_004_','')+(' / 输入'if i==0 else' / 留出，共享上游RGB'))
        for j,method in enumerate(['O3D','NN']):
            ev=np.load(R/'local_results'/f'{method}_V6_F0_evaluation.npz');ids=ev[cid+'_native_id'];cat=ev[cid+'_category'];err=ev[cid+'_hit_mm']-ev[cid+'_depth_mm']
            array=np.full((352,640),np.nan);array.flat[ids]=np.where(np.isfinite(err),err,np.nan)
            bg=np.ones((352,640,3));bg.reshape(-1,3)[ids[cat=='MISS']]=.65;bg.reshape(-1,3)[ids[cat=='CAD_OCCLUDED']]=.02
            ax=fig.add_subplot(3,3,i*3+j+2);ax.imshow(bg);array.flat[ids[cat=='CAD_OCCLUDED']]=np.nan
            im=ax.imshow(np.ma.masked_invalid(array),cmap='coolwarm',vmin=-2,vmax=2,interpolation='nearest')
            a,b,c,d=window(cid);ax.set(xlim=(a,b),ylim=(d,c),title=f'{method} V6：预测首层 − HERO / mm\n灰=MISS；黑=CAD遮挡；固定V2原生分母');ax.axis('off')
    cax=fig.add_axes([.93,.25,.014,.5]);fig.colorbar(im,cax=cax,label='轴向深度偏差 / mm（HERO不是GT）')
    # Reserve a separate legend strip, outside all real-image panels.
    fig.subplots_adjust(left=.02,right=.90,top=.89,bottom=.045,wspace=.12,hspace=.25)
    finish(fig,'Fig2_Real_Projection_First_Depth.png')
    fig=plt.figure(figsize=(19,12));fig.suptitle('图3 | F0失败证据：Unknown边界闭合面与真实相机射线的多层交点',fontsize=15)
    m=ms[2];flags=np.array([a['unknown_boundary_proxy']=='True'for a in csv.DictReader((R/'NN_V6_F0_FACE_VALIDITY.csv').open())]);col=np.tile(to_rgb('#41a591'),(len(flags),1));col[flags]=to_rgb('#df7967')
    ax=fig.add_subplot(2,2,1,projection='3d');mesh3(ax,m,facecolors=col);ax.set_title(f'完整NN Mesh：红=邻接Unknown单元，绿=8角均已观测\n{flags.sum():,}/{len(flags):,}面邻接Unknown，未删除')
    ax=fig.add_subplot(2,2,2)
    for v,color in [('V2','#9862b3'),('V6','#218c8d')]:
        ev=np.load(R/'local_results'/f'NN_{v}_F0_evaluation.npz');cat=ev[CORE[0]+'_category'];e=ev[CORE[0]+'_hit_mm']-ev[CORE[0]+'_depth_mm'];ok=(cat!='CAD_OCCLUDED')&np.isfinite(e)
        ax.hist(e[ok],bins=np.linspace(-2,2,81),histtype='step',lw=1.8,label=f'{v}：固定分母MISS={np.sum(cat=="MISS")}',color=color)
    ax.axvline(-.25,color='grey',ls='--');ax.axvline(.25,color='grey',ls='--');ax.set(xlabel='首层 − HERO / mm；超±2mm尾部另见CSV',ylabel='射线数',title='同一V2固定原生分母：高命中不等于正确首层');ax.legend()
    worst=load(R/'F0_WORST_REAL_RAYS.json');case=worst[0];cid=case['source'];nn=native(cid,'V2');u,v=case['native_u'],case['native_v'];ray=vis.camera_rays(np.array([[u,v]]),nn['K'],nn['T'])[0]
    a=min(case['source_HERO_depth_mm'],case['output_first_hit_mm'])-1;b=max(case['source_HERO_depth_mm'],case['output_first_hit_mm'])+1
    depth=np.linspace(a,b,800);X=ray[:3]+depth[:,None]*ray[3:];G=(X-np.asarray(dom['O_mm']))/dom['L_mm']*128
    field=np.load(R/'local_results/NN_V6_F0_field.npz');known=map_coordinates(field['known'].astype(float),G.T,order=1,mode='constant',cval=0)>=.9999
    value=map_coordinates(field['sdf_raw'],G.T,order=1,mode='constant',cval=np.nan)*dom['L_mm'];value[~known]=np.nan
    ax=fig.add_subplot(2,2,3);ax.plot(depth,value,color='#218c8d',label='已观测单元内SDF插值（非新推理）');ax.axhline(0,color='grey');ax.axvline(case['source_HERO_depth_mm'],color='black',ls='--',label='原HERO轴向深度')
    for k,z in enumerate(case['intersection_depths_mm']):ax.axvline(z,color='#dd7654',alpha=.7,label='真实Mesh交点'if k==0 else None)
    ax.set(xlabel='真实ref08射线轴向Z / mm',ylabel='Neural SDF / mm',title=f'最差当前有效射线：原生ID {case["native_id"]}\n首层误差{case["error_mm"]:.3f}mm；未知区不画为0');ax.legend(fontsize=8)
    ax=fig.add_subplot(2,2,4);raw=original(cid);rgb=cv2.resize(raw['RGB'],(640,352),interpolation=cv2.INTER_AREA);ax.imshow(rgb);ax.plot(u,v,'r+',ms=14,mew=2);ax.set(xlim=(u-28,u+28),ylim=(v+28,v-28),title='同一原生Pixel ID的真实RGB\n不调整相机、不按该失败像素优化输入',xlabel='native u',ylabel='native v')
    finish(fig,'Fig3_Unknown_Closure_And_Real_Ray.png')
    fig=plt.figure(figsize=(19,12));fig.suptitle('图4 | 清理候选V6与保守V2：只融合ref08，模型域/体素/权重/相机完全相同',fontsize=15)
    for i,v in enumerate(['V2','V6']):
        nn=native(CORE[0],v);raw=original(CORE[0]);rgb=cv2.resize(raw['RGB'],(640,352),interpolation=cv2.INTER_AREA);colors=rgb[nn['uv'][:,1],nn['uv'][:,0]]/255
        ax=fig.add_subplot(2,3,i*3+1,projection='3d');ax.scatter(*nn['X'].T,s=.35,c=colors,depthshade=False);cad=ringmesh();ax.add_collection3d(Poly3DCollection(np.asarray(cad.vertices)[np.asarray(cad.faces)],facecolors='black',edgecolors='none'));axes3(ax);ax.set_title(f'{v}原生ref08输入 / {len(nn["ids"]):,}点')
        mesh=output_mesh('NN',v,'F0');ax=fig.add_subplot(2,3,i*3+2);view_image(ax,render(mesh,K,T),CORE[0],f'{v} NN F0 / 相同ref08观察相机')
        ax=fig.add_subplot(2,3,i*3+3,projection='3d');mesh3(ax,mesh);run=load(R/f'NN_{v}_F0_METRICS.json');ax.set_title(f'{v} NN F0 / 原输出Mesh\n当前输入首层p95={run["ref08_current_input_values"]["native_depth_error_p95_including_misses_mm"]:.3f}mm，FAIL')
    finish(fig,'Fig4_V2_V6_Same_Scale_Control.png')
if __name__=='__main__':main()
