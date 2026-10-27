"""Additional RGB/depth camera-baseline and XYZ views of exact D0 scene points."""
from figures import *
def main():
    index=[]
    for s in scenes():
        cid=load(R/f'metrics/D0_{s["video"]}.json')['main_reference'];src=source(cid);p=src['p'];P,rgb=allpoints(s);poses=[]
        for name,offset in [('reference',0),('left',-1),('right',1)]:
            T=p['pose'].copy();T[:3,3]+=offset*T[:3,0];poses.append(dict(name=name,c2w=T,translation_from_source_mm=offset,role='FROZEN_REFERENCE'if offset==0 else'DIAGNOSTIC_ONLY_NOT_VIDEO_FRAME'))
        q=np.concatenate([vis.project_camera(np.r_[P,ring(cases()[0]).vertices],p['K'],x['c2w'])[0]for x in poses]);lo=np.minimum(q.min(0),[0,0]);hi=np.maximum(q.max(0),[639,359]);pad=(hi-lo)*.025;bounds=[(float(lo[k]-pad[k]),float(hi[k]+pad[k]))for k in range(2)];Z=vis.project_camera(P,p['K'],p['pose'])[1];meta=[];name=s['name'].replace(' ','_').replace('+','plus');dest=R/'local_results/visualizations'/name
        fig,axes=plt.subplots(2,3,figsize=(19,11))
        for j,v in enumerate(poses):
            for i in [0,1]:
                x=diag.points(axes[i,j],P,rgb,bounds,v['name']+' / '+v['role']+'\n'+('RGB'if i==0 else'相机轴向深度'),point_size=.08,alpha=1,K=p['K'],c2w=np.array(v['c2w']),depth_color=bool(i),depth_limits=(float(Z.min()),float(Z.max())),ring_scene=scene_for(target('004','selection')[0]),ring_alpha=.15);meta.append(dict(figure='Camera_3Views',view=v['name'],**x))
        fig.suptitle(s['name']+' '+s['frame']+'\n全部实际L4 XYZ；左/右为±1mm真实平移的平行轴显示副本；科研相机未修改；不冒充视频帧');fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(dest/'Camera_3Views.png',dpi=160);plt.close(fig)
        bases=[x[:3]for x in diag.AXES.values()];limits=diag.square_bounds([P,ring(cases()[0]).vertices],bases);fig,axes=plt.subplots(2,3,figsize=(19,12))
        for j,(axis,data)in enumerate(diag.AXES.items()):
            for i in [0,1]:
                x=diag.points(axes[i,j],P,rgb,limits[j],'World +'+axis+' / '+('RGB'if i==0 else'视向深度'),point_size=.08,alpha=1,basis=data[:3],depth_color=bool(i),ring_scene=scene_for(target('004','selection')[0]),ring_alpha=.15,labels=data[3:]);meta.append(dict(figure='XYZ_3Views',view=axis,**x))
        fig.suptitle(s['name']+' '+s['frame']+'\n实际L4 XYZ；三方向共同毫米尺度；保留孔洞、分层和延伸；CAD透明辅助定位');fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(dest/'XYZ_3Views.png',dpi=160);plt.close(fig)
        np.savez_compressed(dest/'diagnostic_cameras_exact.npz',source_K=p['K'],reference_c2w=poses[0]['c2w'],left_c2w=poses[1]['c2w'],right_c2w=poses[2]['c2w']);index.append(dict(scene=s['name'],frame=s['frame'],poses=poses,camera_pixel_bounds=bounds,XYZ_mm_bounds=limits,panels=meta))
    save('metrics/DIAGNOSTIC_VIEW_INDEX.json',index);print('CAMERA_XYZ_RGB_DEPTH_COMPLETE',flush=True)
if __name__=='__main__':main()
