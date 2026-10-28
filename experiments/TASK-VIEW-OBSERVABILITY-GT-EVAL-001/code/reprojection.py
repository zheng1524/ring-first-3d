"""Standard A->B: original A triangles and A vertex RGB; B read only after prediction."""
from io_utils import *
from functools import lru_cache
sys.addaudithook(guard_no_gt)
sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor'))
import open3d as o3d
plt=vis.configure()
@lru_cache(None)
def cad_scene(ring_kind):
    c=next(x for x in cases()if x['ring']==ring_kind);m=ring(c);rt=o3d.t.geometry.RaycastingScene(nthreads=2);rt.add_triangles(o3d.core.Tensor(np.asarray(m.vertices,np.float32)),o3d.core.Tensor(np.asarray(m.faces,np.uint32)));return rt
def render(P,F,C,K,pose,H,ring_kind):
    """Prediction API has NO target RGB, Mask, depth or GT inputs."""
    T=np.asarray(P)@H[:3,:3].T+H[:3,3];rt=o3d.t.geometry.RaycastingScene(nthreads=2);rt.add_triangles(o3d.core.Tensor(T.astype(np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)))
    uv=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)];rays=o3d.core.Tensor(vis.camera_rays(uv,K,pose).astype(np.float32));hit=rt.cast_rays(rays);z=hit['t_hit'].numpy();rz=cad_scene(ring_kind).cast_rays(rays)['t_hit'].numpy();fid=hit['primitive_ids'].numpy();bary=hit['primitive_uvs'].numpy();valid=np.isfinite(z)&(z>0)&(z<=rz+.05);rgba=np.zeros((360*640,4),np.uint8);w=bary[valid];weights=np.c_[1-w.sum(1),w];rgba[valid,:3]=np.rint(np.clip((C[F[fid[valid]]]*weights[:,:,None]).sum(1),0,1)*255).astype(np.uint8);rgba[valid,3]=255
    return dict(RGBA=rgba.reshape(360,640,4),z_mm=z.reshape(360,640),face_id=fid.reshape(360,640),source_barycentric=bary.reshape(360,640,2),known_CAD_z_mm=rz.reshape(360,640),valid=valid.reshape(360,640))
def evaluate(pred,B,labels):
    valid=pred['valid'];polyp=labels==1;common=valid&polyp;err=np.abs(pred['RGBA'][:,:,:3].astype(float)-B.astype(float));mae=err.mean(2);v=mae[common]
    return dict(target_Polyp_pixels=int(polyp.sum()),all_image_pixels=int(polyp.size),prediction_valid_pixels=int(valid.sum()),common_pixels=int(common.sum()),uncovered_target_pixels=int((polyp&~valid).sum()),predicted_outside_target_pixels=int((valid&~polyp).sum()),target_coverage=float(common.sum()/polyp.sum())if polyp.any()else None,common_fraction_image=float(common.mean()),outside_target_fraction_prediction=float((valid&~polyp).sum()/valid.sum())if valid.any()else None,RGB_MAE_0_255=float(v.mean())if len(v)else None,RGB_median_0_255=float(np.median(v))if len(v)else None,RGB_p95_0_255=float(np.quantile(v,.95))if len(v)else None,RGB_RMSE_0_255=float(np.sqrt(np.mean(err[common]**2)))if len(v)else None,independent_geometric_distance_mm=None,geometric_distance_status='NOT_EVALUABLE_NO_INDEPENDENT_TARGET_DEPTH',GT_used=False),mae,common
def neutral(rgba):
    out=np.full(rgba.shape[:2]+(3,),.82);a=rgba[:,:,3]>0;out[a]=rgba[a,:3]/255.;return out
def make_figure(row,pred,metrics,mae,common,P,C,p,c,B):
    fig=plt.figure(figsize=(27,8));gs=fig.add_gridspec(2,5,width_ratios=[1,1,1,1,1.55],hspace=.22,wspace=.14);axs=[fig.add_subplot(gs[:,i])for i in range(4)];A=np.asarray(Image.open(c['RGB']).convert('RGB'));t=row['B_target'];pose=np.array(t['c2w']);K=np.array(t['K']);H=np.array(row['H_A_to_B_world']);T=P@H[:3,:3].T+H[:3,3]
    axs[0].imshow(A);axs[0].set_title('1｜A 真实源帧\n'+row['A']+'\n'+c['condition'],fontsize=10);axs[0].axis('off')
    vis.view_camera_rgb(axs[1],P,C,p['K'],p['pose'],(640,360),size=.08);axs[1].set_title('2｜A 相机 / 实际 P0 XYZ + 源 RGB\nN='+str(len(P))+'；未补面/未贴图',fontsize=10);axs[1].set_facecolor('#d1d1d1');axs[1].set_axis_off()
    depth=vis.project_camera(P,p['K'],p['pose'])[1];zmed=float(np.median(depth[depth>0]));length=5*p['K'][0,0]/zmed;axs[1].plot([15,15+length],[340,340],c='black',lw=2);axs[1].text(15,325,'5 mm @ median Z='+f'{zmed:.1f}',fontsize=7)
    axs[2].imshow(B);axs[2].set_title('3｜B 真实目标帧\n'+row['B']+'\n'+row['pose_status'],fontsize=10);axs[2].axis('off')
    axs[3].imshow(neutral(pred['RGBA']));axs[3].set_title('4｜A→B / 仅 A 原三角面 + A RGB\n灰=UNSUPPORTED_BY_A；CAD遮挡已处理',fontsize=10);axs[3].axis('off')
    sub=gs[:,4].subgridspec(2,2,hspace=.42,wspace=.14);aa=[fig.add_subplot(sub[i//2,i%2])for i in range(4)];overlay=B/255.;v=pred['valid'];overlay[v]=.5*overlay[v]+.5*pred['RGBA'][v,:3]/255.;aa[0].imshow(overlay);aa[0].set_title('5a｜B与预测 50%叠加',fontsize=8)
    support=np.full((360,640,3),.85);polyp=cv2.imread(t['Mask'],0)==1;support[polyp&~v]=[1,.75,.05];support[v&~polyp]=[.9,.15,.2];support[common]=[.1,.7,.4];aa[1].imshow(support);aa[1].set_title('5b｜绿=共同，黄=未覆盖\n红=预测外逸；无选择性抹除',fontsize=8)
    diff=np.full((360,640),np.nan);diff[common]=mae[common];im=aa[2].imshow(diff,cmap='magma',vmin=0,vmax=80);aa[2].set_facecolor('#cfcfcf');aa[2].set_title('5c｜共同有效区 RGB MAE\n未覆盖不参与误差',fontsize=8);fig.colorbar(im,ax=aa[2],fraction=.045,pad=.01)
    basis=vis.basis((0,0));rm=ring(c);b=diag.square_bounds([P,rm.vertices],[basis])[0];diag.points(aa[3],P,C,b,'5d｜A实际XYZ侧视 / mm',basis=basis,point_size=.08,alpha=1)
    for ax in aa[:3]:ax.axis('off')
    metrics_text=f"共同支持 {metrics['common_pixels']}/{metrics['target_Polyp_pixels']} target pixels = {metrics['target_coverage']:.1%}; 画幅占比 {metrics['common_fraction_image']:.1%}; 外逸 {metrics['predicted_outside_target_pixels']}/{metrics['prediction_valid_pixels']} prediction pixels\nRGB MAE {metrics['RGB_MAE_0_255']:.2f}/255; p95 {metrics['RGB_p95_0_255']:.2f}; 光轴角 {metrics['conditional_optical_angle_deg']:.2f}°; 基线 {metrics['conditional_baseline_mm']:.2f} mm — {row['pose_status']}"
    fig.suptitle(row['pair_id']+'｜标准五面板：真实跨帧 / 不使用B颜色、B深度或GT；三角面颜色仅原A顶点重心插值',fontsize=14);fig.text(.03,.05,metrics_text+'\n004 raw编号仅历史近似绑定：以关键帧ID+RGB SHA为准。相机/光照/反光/遮挡均可能引起差异；该图不证明自主三维准确性。',fontsize=10)
    fig.subplots_adjust(top=.85,bottom=.20);dest=R/'figures/A_to_B'/(row['pair_id']+'.png');dest.parent.mkdir(parents=True,exist_ok=True);fig.savefig(dest,dpi=130,facecolor='white');plt.close(fig);return str(dest.relative_to(R))
def main():
    verify_predictions();frozen=load(R/'provenance/A_TO_B_PAIRS_BEFORE_RENDER.json');rows=[]
    for row in frozen['pairs']:
        if not row['executable']:continue
        c,P,C,m,p,uv=source(row['A']);t=row['B_target'];H=np.array(row['H_A_to_B_world']);pred=render(P,m.faces,C,np.array(t['K']),np.array(t['c2w']),H,c['ring']);out=R/'local_results/reprojection';out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(row['pair_id']+'.npz'),**pred)
        # The target image is FIRST opened here, after the immutable prediction exists.
        B=np.asarray(Image.open(t['RGB']).convert('RGB'));labels=cv2.imread(t['Mask'],0);stats,mae,common=evaluate(pred,B,labels);Apose=H@p['pose'];Bpose=np.array(t['c2w']);stats.update(pair_id=row['pair_id'],group=row['group'],A=row['A'],B=row['B'],pose_status=row['pose_status'],conditional_optical_angle_deg=angle(Apose[:3,2],Bpose[:3,2]),conditional_baseline_mm=float(np.linalg.norm(Apose[:3,3]-Bpose[:3,3])),reliable_cross_source_baseline_mm=None if'CANDIDATE'in row['pose_status']else float(np.linalg.norm(Apose[:3,3]-Bpose[:3,3])),B_RGB_used_in_prediction=False,B_depth_used_in_prediction=False,B_Mask_used_to_modify_prediction=False,source_RGB_SHA256=sha(c['RGB']),source_geometry_SHA256=sha(c['mesh']),target_RGB_SHA256=sha(t['RGB']),prediction_file=str((out/(row['pair_id']+'.npz')).relative_to(R)),prediction_SHA256=sha(out/(row['pair_id']+'.npz')),visibility='POSITIVE_Z / FRAME / ORIGINAL_SOURCE_TRIANGLE_ZBUFFER / KNOWN_CAD. B tissue occlusion UNKNOWN',original_cleanup_final='Raw; rejected candidates not adopted',status='UNQUALIFIED_CAMERA_STRESS'if c['condition']=='UNQUALIFIED_STRESS'else'CANDIDATE_ONLY'if'CANDIDATE'in row['pose_status']else'FROZEN_CAMERA_CONDITIONAL')
        stats['figure']=make_figure(row,pred,stats,mae,common,P,C,p,c,B);rows.append(stats);both('a_to_b_results',rows);print('A_TO_B',row['pair_id'],'cover',round(stats['target_coverage'],3),'MAE',round(stats['RGB_MAE_0_255'],2),flush=True)
    # Independent frozen-depth *consistency*, not actual depth GT.
    depths=[]
    for a in cases():
        for b in cases():
            if a['id']==b['id']or a['group']!=b['group']or a['video']!=b['video']:continue
            _,P,C,m,p,uv=source(a['id']);_,Q,D,mm,q,quv=source(b['id']);xy,z=vis.project_camera(P,q['K'],q['pose']);valid=np.isfinite(xy).all(1)&(z>0);px=np.zeros_like(xy,int);px[valid]=np.rint(xy[valid]).astype(int);valid&=(px[:,0]>=0)&(px[:,0]<640)&(px[:,1]>=0)&(px[:,1]<360);ids=np.flatnonzero(valid);u,v=px[ids].T;good=(q['labels'][v,u]==1)&np.isfinite(q['depth_mm'][v,u])&(q['depth_mm'][v,u]>0);ids=ids[good];u,v=px[ids].T;dz=z[ids]-q['depth_mm'][v,u];depths.append(dict(group=a['group'],A=a['id'],B=b['id'],source_points=len(P),target_polyp_depth_support=len(dz),median_signed_delta_mm=float(np.median(dz)),median_absolute_delta_mm=float(np.median(abs(dz))),p95_absolute_delta_mm=float(np.quantile(abs(dz),.95)),within_03mm=int((abs(dz)<=.3).sum()),front_conflict_gt03mm=int((dz<-.3).sum()),behind_difference_gt03mm=int((dz>.3).sum()),identity='MODEL_DEPTH_CONSISTENCY; shared HERO/cameras; not GT; B depth evaluation only'))
    both('within_video_depth_conflicts',depths)
if __name__=='__main__':main()
