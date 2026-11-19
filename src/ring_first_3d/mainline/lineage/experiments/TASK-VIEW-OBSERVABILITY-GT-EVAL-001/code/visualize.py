"""True cached XYZ, explicit separate gauges, fixed audit charts; no new geometry."""
from io_utils import *
from matplotlib import colors
from visualization.same_camera_scene import SameCameraScene
from functools import lru_cache
plt=vis.configure()
@lru_cache(None)
def scene(cid):
    c=case(cid);p=np.load(c['pack']);return SameCameraScene(ring(c),p['K'],p['pose'],(640,360),str(OLD/'surface_fusion_v3/vendor'))
def output(fig,path):
    p=R/path;p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=140,facecolor='white',bbox_inches='tight');plt.close(fig)
def draw_graph(ax):
    names=['G01_video004','G01_video005','G01_photo001','G01_photo002','G01_photo003'];pos=np.array([[-1,1],[1,1],[-1.5,-.6],[0,-1],[1.5,-.6]]);edges=load(R/'metrics/source_graph_edges.json');indices={x:i for i,x in enumerate(names)}
    for e in edges:
        if e['group']!='G01':continue
        i,j=indices[e['A_source']],indices[e['B_source']];q=pos[[i,j]];cand=e['registration_status']=='CANDIDATE';ax.plot(q[:,0],q[:,1],color='#bc8b22'if cand else'#c4c4c4',ls='--'if cand else':',lw=1.2,zorder=0)
    ax.scatter(*pos.T,s=250,c=['#dc7499','#3280b7','#999999','#999999','#999999']);labels=['video004\nLOCAL Ring 004','video005\nLOCAL Ring 005','photo001\nPOSE_UNKNOWN','photo002\nPOSE_UNKNOWN','photo003\nPOSE_UNKNOWN']
    for p,n in zip(pos,labels):ax.text(*p,n,ha='center',va='bottom',fontsize=9)
    ax.text(0,1.02,'CANDIDATE / NOT FUSED\nRing+背景；跨视角未认证',ha='center',fontsize=8,color='#8f6816');ax.text(0,-1.5,'灰点线：FAILED / UNREGISTERED；已有视觉匹配 ≠ 注册成功\n照片K光学模式未知，历史独立几何验证失败；圆环绕法向旋转不唯一',ha='center',fontsize=8);ax.set(xlim=(-2,2),ylim=(-1.8,1.7),title='五来源连接关系｜没有 REGISTERED 跨来源边');ax.axis('off')
def trajectory_panel(ax,sid,angle_,frames,main):
    c,P,C,m,p,uv=source(main);poses=np.array([r['c2w']for r in frames]);centers=poses[:,:3,3];basis=vis.basis(angle_);rm=ring(c);b=diag.square_bounds([P,rm.vertices,centers],[basis])[0];diag.points(ax,P,C,b,sid+'｜独立本地Ring系 / mm',basis=basis,point_size=.08,alpha=1,ring_scene=scene(main),ring_alpha=.4);proj=lambda q:np.c_[np.asarray(q)@basis[1],np.asarray(q)@basis[2]];q=proj(centers);ax.plot(*q.T,'-o',lw=.7,ms=2,color='#267eae');corners=np.array([[0,0,1],[639,0,1],[639,359,1],[0,359,1]])@np.linalg.inv(p['K']).T
    for i in [0,len(poses)//2,len(poses)-1]:
        pose=poses[i];Q=(corners*5)@pose[:3,:3].T+pose[:3,3];q1=proj(Q);q0=proj([pose[:3,3]])[0];ax.plot(*np.r_[q1,q1[:1]].T,color='#267eae',lw=.5)
        for k in range(4):ax.plot([q0[0],q1[k,0]],[q0[1],q1[k,1]],color='#267eae',lw=.4)
        arrow=proj([pose[:3,3],pose[:3,3]+pose[:3,2]*7]);ax.annotate('',xy=arrow[1],xytext=arrow[0],arrowprops=dict(arrowstyle='->',color='#267eae',lw=.6))
    ax.text(.02,.02,str(len(poses))+'个冻结相机候选；不新增/拟合位姿\n视锥长度5mm仅显示；坐标不可跨视频比较',transform=ax.transAxes,fontsize=7)
def direction_panel(ax,sid,frames):
    poses=np.array([x['c2w']for x in frames]);q=poses[:,:3,3];az=np.degrees(np.arctan2(q[:,1],q[:,0]));el=np.degrees(np.arctan2(q[:,2],np.linalg.norm(q[:,:2],axis=1)));ax.plot(az,el,'o-',ms=3,lw=.8);ax.set(xlabel='本地Ring方位角 / deg',ylabel='Ring→相机仰角 / deg',title=sid+'｜仅本视频局部坐标');ax.grid(alpha=.2)
def camera_figures():
    frames=load(R/'metrics/camera_frame_inventory.json');scenes=load(R/'prediction_snapshot/B_scenes.json');fig,ax=plt.subplots(3,2,figsize=(19,19));a=[x for x in frames if x['source_id']=='G01_video004'];b=[x for x in frames if x['source_id']=='G01_video005'];mains={s['id']:s['main_reference']for s in scenes}
    trajectory_panel(ax[0,0],'video004',(-65,22),a,mains['G01_004']);trajectory_panel(ax[0,1],'video005',(-65,22),b,mains['G01_005']);direction_panel(ax[1,0],'video004',a);direction_panel(ax[1,1],'video005',b);draw_graph(ax[2,0]);ax[2,1].axis('off');ax[2,1].text(0,.96,'可靠共同坐标系：未建立\n\n三张静态照片均真实存在，RGB/Mask可读。\n没有现成、通过验证的相机位姿或深度/P0。\n保留历史候选投影，不伪造三维相机位置。\n\n两视频局部轨迹方向不同，但跨视频精确夹角\n和基线仅能在候选H条件下计算。\nRing法向倾斜可作局部候选比较；\n绕Ring法向旋转仍不可仅靠圆环确定。\n\n粉色点是实际主参考XYZ，黑色为已知CAD；\n点间距、细长异常与孔洞未平滑。\nGT未进入本图。',va='top',fontsize=12);fig.suptitle('G01 五来源可观测性审计｜两条独立局部轨迹，不是共同世界轨迹',fontsize=17);fig.tight_layout(rect=[0,0,1,.97]);output(fig,'figures/G01_camera_view_coverage.png')
    fig,ax=plt.subplots(figsize=(11,8));draw_graph(ax);output(fig,'figures/source_registration_graph.png')
    fig,ax=plt.subplots(1,2,figsize=(15,6));direction_panel(ax[0],'video004',a);direction_panel(ax[1],'video005',b);fig.suptitle('独立局部方位；照片POSE_UNKNOWN，未赋予虚假方向');fig.tight_layout();output(fig,'figures/G01_view_direction_distribution.png')
    rows=[]
    for sid in dict.fromkeys(x['source_id']for x in frames):
        rr=[x for x in frames if x['source_id']==sid];poses=np.array([x['c2w']for x in rr]);tilt=np.degrees(np.arccos(np.clip(-poses[:,2,2],-1,1)));d=np.linalg.norm(poses[:,:3,3],axis=1);pp=[x for x in load(R/'metrics/view_pairwise_metrics.json')if x['A_source']==sid and x['B_source']==sid];rows.append(dict(source=sid,cached_frames=len(rr),qualified_metadata=case(next(s['main_reference']for s in scenes if sid==s['group']+'_video'+s['video']))['qualified_frames'],tilt_to_local_negative_Ring_normal_deg=[float(tilt.min()),float(np.median(tilt)),float(tilt.max())],camera_distance_Ring_mm=[float(d.min()),float(d.max())],within_source_max_optical_angle_deg=max(x['optical_axis_angle_deg']for x in pp),within_source_max_baseline_mm=max(x['baseline_mm']for x in pp),quality=rr[0]['camera_condition']))
    both('view_coverage_summary',rows)
def support_figure():
    scenes=load(R/'prediction_snapshot/B_scenes.json');fig,axes=plt.subplots(6,2,figsize=(19,27),gridspec_kw=dict(height_ratios=[1,1,1,1,1,.5]));palette={0:'#d87099',1:'#aaaaaa',2:'#e43d40',3:'#aaaaaa',4:'#388bd4',5:'#13ad7d'}
    for i,sc in enumerate(scenes):
        allP=[];allC=[]
        for cid in sc['references']:
            c,P,C,m,p,uv=source(cid);z=np.load(PREV/f'local_results/scenes/{sc["id"]}/{cid}_faces_exact.npz');states=np.full(len(P),3,int)
            for k in [3,1,4,0,5,2]:
                ids=np.unique(z['faces'][z['face_status']==k]);ids=ids[ids<len(P)];states[ids]=k
            allP.append(P);allC.append(np.array([colors.to_rgb(palette[int(k)])for k in states]));
        P=np.concatenate(allP);C=np.concatenate(allC);basis=vis.basis((-65,22));bounds=diag.square_bounds([P,ring(c).vertices],[basis])[0];diag.points(axes[i,0],P,C,bounds,sc['id']+'｜'+c['condition']+'\n名义同视频局部系；原点全保留',basis=basis,alpha=1,point_size=.08,ring_scene=scene(sc['main_reference']),ring_alpha=.15)
        cls={k:sum(r['classes'].get(str(k),{}).get('model_area_mm2',0)for r in sc['source_summaries'])for k in range(6)};ys=['主支持(条件)','主未知','冲突','未知','重复观测','新增候选'];values=[cls[k]for k in range(6)];axes[i,1].barh(ys,values,color=[palette[k]for k in range(6)]);axes[i,1].invert_yaxis();axes[i,1].set(xlabel='模型面面积暴露之和 / mm²（非真实解剖面积）',title='新增候选='+f'{sc["new_patch_area_mm2"]:.4f} mm²；独立认证新增=NOT_EVALUABLE');axes[i,1].grid(axis='x',alpha=.15)
    for ax in axes[5]:ax.axis('off')
    axes[5,0].text(0,.9,'照片三来源：UNREGISTERED / NO TRACEABLE P0\n没有共同三维支持图；不把照片匹配数换算为新增面积。\n其他三组仅一份P0：新增0是输入缺失，不是融合成功。',va='top',fontsize=12);axes[5,1].text(0,.9,'颜色来自已冻结面状态关联到原顶点，仅诊断。\n重复面=模型重合证据，不等于独立真实组织认证。\n红=算法冲突；不能单凭它判定哪一份是真。',va='top',fontsize=12);fig.suptitle('四物理组 / 五局部场景｜来源支持与信息缺口；不同视频/物理组没有合并',fontsize=17);fig.tight_layout(rect=[0,0,1,.98]);output(fig,'figures/G01_source_surface_support.png')
def gt_chart():
    s=load(R/'metrics/gt_summary.json');h=load(R/'metrics/gt_height_evaluation.json');d=load(R/'metrics/gt_dxy_evaluation.json');fig,ax=plt.subplots(2,2,figsize=(18,13));groups=['G01','G06','G07','G08'];color=['#a45a83','#28817e','#949494','#be8c29']
    for i,g in enumerate(groups):
        v=[r['H_pred_mm']for r in h if r['group_id']==g and r['H_pred_mm']is not None];gt=s['GT'][g]['H_gt_mm'];ax[0,0].plot([i-.3,i+.3],[gt,gt],color='black',lw=2)
        if v:ax[0,0].scatter(i+np.linspace(-.15,.15,len(v)),v,s=30,color=color[i]);ax[0,0].annotate(f'{len(v)}/{sum(r["group_id"]==g for r in h)}',(i,max(v)+.4),ha='center')
        else:ax[0,0].text(i,.04,'0/3\nNOT EVALUABLE',transform=ax[0,0].get_xaxis_transform(),ha='center',fontsize=9)
        dv=[r['Dxy_candidate_mm']for r in d if r['group_id']==g and r['Dxy_candidate_mm']is not None and r['model']=='core'];dg=s['GT'][g]['Dxy_gt_mm'];ax[0,1].plot([i-.3,i+.3],[dg,dg],color='black',lw=2)
        if dv:ax[0,1].scatter(i+np.linspace(-.15,.15,len(dv)),dv,s=30,color=color[i])
        else:ax[0,1].text(i,.05,'NO CANDIDATE',transform=ax[0,1].get_xaxis_transform(),ha='center',fontsize=9)
    ax[0,0].set(xticks=range(4),xticklabels=groups,ylabel='H95 / mm',title='H95：黑线=完整GT顶点P95；点=有效可见P0条件\n10/27条件；3/4组至少一个有效条件，非独立病例数')
    ax[0,1].set(xticks=range(4),xticklabels=groups,ylabel='Feret / mm',title='3D Dxy数学候选 core / 黑线=完整GT Feret\n正式测量仍81/81失败；候选接近GT不改变状态')
    for a in ax[0]:a.grid(alpha=.2)
    ax[1,0].axis('off');table=[['组','GT H95','有效H范围','GT Dxy','正式Dxy']]
    for r in s['per_group']:
        g=r['group'];hr=r['height_pred_range'];table.append([g,f'{s["GT"][g]["H_gt_mm"]:.4f}','NaN'if hr is None else f'{hr[0]:.4f}–{hr[1]:.4f}',f'{s["GT"][g]["Dxy_gt_mm"]:.4f}',f'0/{r["Dxy_conditions"]}'])
    tt=ax[1,0].table(cellText=table,loc='upper center',cellLoc='center');tt.auto_set_font_size(False);tt.set_fontsize(10);tt.scale(1,2)
    ax[1,0].text(.02,.4,'固定主参考+ROI5–30+core、G01固定004：\nH95有效2/4；MAE='+f'{s["prespecified_group_height"]["MAE_mm"]:.4f}'+' mm\n数学Dxy有效3/4；MAE='+f'{s["prespecified_group_Dxy_math"]["MAE_mm"]:.4f}'+' mm\n正式Dxy 0/4；误差NaN。未挑最佳ROI/视频。',va='top',fontsize=11)
    ax[1,1].axis('off');ax[1,1].text(0,.95,'GT使用模式：SHAPE_SCALAR_CONDITIONAL\n\n4/4原文件SHA/明确组映射与真实底盖已核验。\nGT底盖不是Ring平面，也不来自预测平面。\n全GT与可见预测覆盖、顶点采样不同。\n真实部署组织切面未独立标定；非临床精度。\n\nG01_004基底0/9；G01_005仅4/9有效。\nG07相机不合格，保留压力测试与NaN。\nG06两端点、G08一端点缺独立观测支持。\n\n预测—GT坐标映射未知：表面误差4/4不可评价。\nGT未进入预测/相机/选帧/阈值/融合；没有ICP。',va='top',fontsize=12);fig.suptitle('独立形状GT审计｜真实正负结果与完整分母；不把数学接近变成正式成功',fontsize=17);fig.tight_layout(rect=[0,0,1,.96]);output(fig,'figures/GT_metric_summary.png')
def representative_sheet():
    # Fixed categories from quality/asset condition, not chosen by lowest new RGB error.
    ids=['G06_004_ref04__to__key03_raw00473','G01_004_ref08__to__004_14','G07_004_ref04__to__key06_raw00520'];rows=load(R/'metrics/a_to_b_results.json');ims=[Image.open(R/next(r['figure']for r in rows if r['pair_id']==i)).convert('RGB')for i in ids];width=max(im.width for im in ims);sheet=Image.new('RGB',(width,sum(im.height for im in ims)),'white');y=0
    for im in ims:sheet.paste(im,(0,y));y+=im.height
    sheet.save(R/'figures/A_to_B_core_review.png');save('provenance/CORE_PAIR_SELECTION.json',dict(selected=ids,basis='NORMAL G06 / G01 wide-view P2 pair / UNQUALIFIED G07; all results retained, no numerical success threshold',categories=['comparatively good conditional','limited','stress failure'],not_accuracy_labels=True))
def main():
    verify_predictions();camera_figures();support_figure();gt_chart();representative_sheet();save('provenance/VISUALIZATION_PARAMETERS.json',dict(renderer=str(REPO/'visualization/real_p0_renderer.py'),renderer_SHA256=sha(REPO/'visualization/real_p0_renderer.py'),source_points_subsampled=False,point_size=.08,alpha=1,source_support_colors='diagnostic frozen face status',cameras_estimated_this_task=False,world_trajectories_merged=False));print('CORE_FIGURES_COMPLETE')
if __name__=='__main__':main()
