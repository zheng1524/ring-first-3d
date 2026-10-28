"""Five panels and high-resolution scene pairs; separate old/new metric supports."""
from scene_renderer import *
import legacy_polyp as legacy
def fmt(x):return'NaN'if x is None else f'{x:.2f}'
def figure_pair(row,d,A,B,gray,scene,new,old,pred,diff,roi,out):
    fig=plt.figure(figsize=(16,13.8));gs=fig.add_gridspec(3,2,height_ratios=[1,1,.67],hspace=.18,wspace=.035);axes=[fig.add_subplot(gs[i//2,i%2])for i in range(4)];titles=['1｜A完整真实视场 — '+row['A'],'2｜A同相机几何：统一灰XYZ + 黑色实体CAD','3｜B完整真实视场 — '+row['B'],'4｜A→B：A真实RGB点云 + 背景XYZ + CAD']
    for ax,im,title in zip(axes,[A,gray,B,scene],titles):ax.imshow(im,interpolation='nearest');ax.axis('off');ax.set_title(title,fontsize=11,pad=5)
    sub=gs[2,:].subgridspec(1,4,wspace=.12);aa=[fig.add_subplot(sub[i])for i in range(4)];small=cv2.resize(scene,(640,360),interpolation=cv2.INTER_AREA);valid=pred['layer']>=0;overlay=B.copy().astype(float)/255.;overlay[valid]=.5*overlay[valid]+.5*small[valid]/255.;aa[0].imshow(overlay);aa[0].set_title('5a｜B与完整场景 50%叠加',fontsize=9)
    layer=pred['layer'];targetP=cv2.imread(row['B_target']['Mask'],0)==1;target=targetP|roi;actual=(layer==0)|(layer==1);cp=(layer==1)&targetP;cb=(layer==0)&roi;support=np.full((360,640,3),.82);support[target&~actual]=[1,.76,.1];support[actual&~(cp|cb)]=[.9,.15,.2];support[cp]=[.1,.75,.4];support[cb]=[.15,.55,.95];support[layer==2]=[0,0,0];aa[1].imshow(support);aa[1].set_title('5b｜绿P/蓝BG共同，黄未覆盖\n红ROI外/类别不符，黑CAD（非错误GT）',fontsize=9)
    common=((layer==1)&(cv2.imread(row['B_target']['Mask'],0)==1))|((layer==0)&roi);error=np.where(common,diff,np.nan);aa[2].imshow(error,cmap='magma',vmin=0,vmax=80);aa[2].set_facecolor('#cccccc');aa[2].set_title('5c｜分层有效支持RGB差异\nP/BG指标各自独立分母，色阶0–80',fontsize=9);side_plot(aa[3],d,'5d｜A真实XYZ侧视 / mm');aa[3].tick_params(labelsize=7);aa[3].xaxis.label.set_size(8);aa[3].yaxis.label.set_size(8)
    for ax in aa[:3]:ax.axis('off')
    state='CANDIDATE_ONLY — 未认证注册'if'CANDIDATE'in row['pose_status']else row['pose_status'];fig.suptitle(f"{row['group']}｜{state}｜A/B光轴 {row['optical_axis_angle_deg']:.2f}°；基线 {row['baseline_mm']:.2f} mm（冻结/候选条件）",fontsize=13,y=.996,color='#9c281e'if'CANDIDATE'in state or'STRESS'in state else'black')
    footer=f"旧Polyp-only原三角面：覆盖 {old['common_pixels']}/{old['target_Polyp_pixels']}={old['target_coverage']:.1%}，MAE {old['RGB_MAE_0_255']:.2f}/255（原口径未改）\n新点云场景：P {new['Polyp_common_N']}/{new['Polyp_target_N']}={new['Polyp_target_coverage']:.1%} / MAE {fmt(new['Polyp_RGB_MAE'])}；BG {new['Background_common_N']}/{new['Background_target_ROI_N']}={new['Background_target_coverage']:.1%} / MAE {fmt(new['Background_RGB_MAE'])}\nBACKGROUND_FROM_FROZEN_DEPTH — DISPLAY_ONLY；灰色未知区不补面；无B重着色，无GT；源Ring先验完整随A坐标关系投影。"
    fig.text(.025,.012,footer,fontsize=9);fig.subplots_adjust(left=.025,right=.99,top=.965,bottom=.105);fig.savefig(out/'Five_Panels.png',dpi=180,facecolor='white');plt.close(fig)
    fig,ax=plt.subplots(1,2,figsize=(16,5.35));ax[0].imshow(B,interpolation='nearest');ax[1].imshow(scene,interpolation='nearest')
    for x in ax:x.axis('off')
    ax[0].set_title('B真实完整视场｜'+row['B'],fontsize=11);ax[1].set_title('A→B完整局部点云场景｜源A RGB + 已知CAD',fontsize=11);fig.suptitle(f"{row['pair_id']}｜{state}｜{row['optical_axis_angle_deg']:.2f}° / {row['baseline_mm']:.2f}mm",fontsize=11);fig.text(.02,.02,'背景XYZ仅冻结深度展示；异常间隙/断裂保留；B未用于预测颜色/背景选择。',fontsize=9);fig.subplots_adjust(left=.01,right=.99,top=.86,bottom=.10,wspace=.03);fig.savefig(out/'Real_B_vs_Full_AtoB_Scene.png',dpi=200,facecolor='white');plt.close(fig)
    fig,ax=plt.subplots(1,3,figsize=(18,6));side_plot(ax[0],d,'侧视｜实际P0+背景XYZ+实体CAD / mm');side_plot(ax[1],d,'斜视｜原始空间间隙和异常保留 / mm',(-65,22));basis=vis.basis((-65,22));poses=[d['p']['pose'],np.array(row['B_camera_in_A'])];P=np.r_[d['P'],d['B']];Q=np.array([x[:3,3]for x in poses]);bb=diag.square_bounds([P,Q,d['ring'].vertices],[basis])[0];diag.points(ax[2],P,np.full_like(P,.7),bb,'A/B观察关系（源A坐标）/ mm',basis=basis,point_size=.08,alpha=1)
    for pose,name,col in zip(poses,['A','B(候选)'if'CANDIDATE'in row['pose_status']else'B'],['#1967a6','#bc3d37']):
        xyz=np.array([pose[:3,3],pose[:3,3]+pose[:3,2]*6]);q=np.c_[xyz@basis[1],xyz@basis[2]];ax[2].plot(q[:1,0],q[:1,1],'o',color=col,ms=4);ax[2].annotate(name,xy=q[1],xytext=q[0],arrowprops=dict(arrowstyle='->',color=col),color=col)
    fig.suptitle(row['A']+'｜诊断视角，非真实视频帧；背景DISPLAY_ONLY；相机未优化');fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(out/'Actual_XYZ_side_views.png',dpi=160,facecolor='white');plt.close(fig)
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--pair');args=ap.parse_args();verify();plan=load(R/'provenance/PAIRS_FROZEN.json')['pairs'];rows=load(R/'metrics/results.json')if(R/'metrics/results.json').exists()else[]
    for row in plan:
        if args.pair and args.pair!=row['pair_id']:continue
        if any(x['pair_id']==row['pair_id']for x in rows):continue
        d=scene_data(row['A']);p=d['p'];K=np.array(row['B_target']['K']);pose=np.array(row['B_camera_in_A']);out=R/'figures/cases'/row['pair_id'];out.mkdir(parents=True,exist_ok=True);buf=R/'local_results/projections';buf.mkdir(parents=True,exist_ok=True)
        # All predictions exist before B RGB/Mask are read. Drawing APIs never receive B inputs.
        gray,ginfo=scene_image(d,p['K'],p['pose'],neutral=True);full,finfo=scene_image(d,K,pose);pred=point_projection(d,K,pose);np.savez_compressed(buf/(row['pair_id']+'_scene.npz'),**pred);Image.fromarray(gray).save(out/'A_neutral_geometry.png');Image.fromarray(full).save(out/'Full_AtoB_Scene.png')
        if row['old_pair_id']:
            oldrecord=next(x for x in load(AUDIT/'metrics/a_to_b_results.json')if x['pair_id']==row['old_pair_id']);oldpred=dict(np.load(AUDIT/oldrecord['prediction_file']));mode='REUSED_FROZEN_LEGACY_PREDICTION'
        else:oldpred=legacy.render(d['P'],d['m'].faces,d['C'],K,np.array(row['B_target']['c2w']),np.array(row['H_A_to_B_world']),d['c']['ring']);mode='EXACT_OLD_METRIC_KERNEL_NEW_FROZEN_PAIR'
        np.savez_compressed(buf/(row['pair_id']+'_legacy_polyp.npz'),**oldpred)
        B=np.asarray(Image.open(row['B_target']['RGB']).convert('RGB'));mask=cv2.imread(row['B_target']['Mask'],0);A=np.asarray(Image.open(d['c']['RGB']).convert('RGB'));new,diff,roi=scene_metrics(pred,B,mask);old,_,_=legacy.evaluate(oldpred,B,mask)
        if row['old_pair_id']:
            for k,v in old.items():assert v==oldrecord[k],(row['pair_id'],k,v,oldrecord[k])
        figure_pair(row,d,A,B,gray,full,new,old,pred,diff,roi,out);result=dict(pair_id=row['pair_id'],group=row['group'],A=row['A'],B=row['B'],angle_deg=row['optical_axis_angle_deg'],baseline_mm=row['baseline_mm'],pose_status=row['pose_status'],background_status=row['background_status'],source_P0_N=len(d['P']),source_BG_N=len(d['B']),legacy_metric_identity=mode,legacy_Polyp_only=old,new_point_scene=new,geometry_render=ginfo,full_scene_render=finfo,figures={n:str((out/n).relative_to(R))for n in ['Five_Panels.png','Real_B_vs_Full_AtoB_Scene.png','Actual_XYZ_side_views.png','A_neutral_geometry.png','Full_AtoB_Scene.png']},source_geometry_path=str(R/'local_results/source_layers'/(row['A']+'.npz')),prediction_path=str(buf/(row['pair_id']+'_scene.npz')),legacy_prediction_path=str(buf/(row['pair_id']+'_legacy_polyp.npz')));rows.append(result);both('results',rows);both('legacy_polyp_metrics',[dict(pair_id=r['pair_id'],group=r['group'],angle_deg=r['angle_deg'],status=r['pose_status'],**r['legacy_Polyp_only'])for r in rows]);both('scene_point_metrics',[dict(pair_id=r['pair_id'],group=r['group'],angle_deg=r['angle_deg'],status=r['pose_status'],**r['new_point_scene'])for r in rows]);print('FULL_SCENE',row['pair_id'],'P/bg',len(d['P']),len(d['B']),'new BG cover',round(new['Background_target_coverage'],3),'legacy',old['target_coverage'],flush=True)
if __name__=='__main__':main()
