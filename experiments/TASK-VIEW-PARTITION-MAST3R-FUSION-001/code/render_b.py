from render import *
from matching import views
def main():
    vv=views();pairs=load(R/'provenance/MATCHING_PAIRS_FROZEN.json')['pairs'];edges={e['id']:e for e in load(R/'metrics/registration_edges.json')};metrics=load(R/'metrics/matching_comparison.json')
    for name,gs in [('G01',['G01']),('G06',['G06']),('G07_G08',['G07','G08'])]:
        pp=[p for p in pairs if p['group']in gs];f,aa=plt.subplots(len(pp),3,figsize=(18,3.5*len(pp)),squeeze=False)
        for i,pair in enumerate(pp):
            a,b=vv[pair['A']],vv[pair['B']];A=np.asarray(Image.open(a['RGB']));B=np.asarray(Image.open(b['RGB']));canvas=np.r_['1',A,B]
            for j,method in enumerate(['SIFT','MASt3R_FULL','MASt3R_ROI']):
                ax=aa[i,j];ax.imshow(canvas);ax.axis('off');path=R/f'local_results/matches/{pair["id"]}_{method}.npz'
                if not path.exists():ax.set_title(pair['id']+' '+method+' FAILED');continue
                z=np.load(path);n=len(z['p']);ids=np.linspace(0,n-1,min(80,n),dtype=int)if n else[]
                colors={'Polyp':'#f23a88','NearBackground':'#22c5b3','FarBackground':'#dfb427','Ring':'black'}
                for k in ids:
                    p,q=z['p'][k],z['q'][k]+[640,0];good=z['geometric_candidate'][k];ax.plot([p[0],q[0]],[p[1],q[1]],color=colors[str(z['region'][k])]if good else'#999',lw=.45,alpha=.85 if good else .25)
                r=next((x for x in metrics if x['pair']==pair['id']and x['method']==method),{});pc=r.get('regions',{}).get('Polyp',{}).get('geometric_candidate_N',0);bc=r.get('regions',{}).get('NearBackground',{}).get('geometric_candidate_N',0);ax.set_title(pair['id']+' / '+method+f'\n原始{n}；F一致候选 Polyp={pc} /近BG={bc}（不是真值）',fontsize=10)
        f.suptitle(name+'｜P4 Matching Comparison｜粉Polyp / 青近BG / 黄远BG / 灰离群\n每面板均匀显示≤80条；完整匹配/置信度/空间格/独立留出指标保存，不以总匹配数当正确率',fontsize=14);f.tight_layout(rect=[0,0,1,.96]);put(f,'P4_mast3r_matching/'+name+'.png')
        f,aa=plt.subplots(len(pp),3,figsize=(16,4*len(pp)),squeeze=False)
        for i,pair in enumerate(pp):
            e=edges[pair['id']];s=source(pair['source_case']);d=point_data(pair['source_case']);b=vv[pair['B']];aa[i,0].imshow(Image.open(b['RGB']));aa[i,0].axis('off');aa[i,0].set_title(pair['id']+' / B真实图',fontsize=10)
            if e.get('selected'):
                im,info=scene_image(d,np.array(b['K']),np.array(e['c2w_target_in_source']));aa[i,1].imshow(im);aa[i,1].axis('off');aa[i,1].set_title(e['selected']+' / A真实XYZ和A RGB\n'+e['status'],fontsize=10);side(aa[i,2],d,'A实际XYZ / mm；原面不变')
                title='Ring中心 '+str(e['Ring'].get('center_mm'))+' mm\nPolyp/BG留出与独立帧单列；不把B重着色'
                aa[i,2].text(.02,.02,title,transform=aa[i,2].transAxes,fontsize=8,bbox=dict(facecolor='white',alpha=.9,edgecolor='none'))
            else:
                for a in aa[i,1:]:a.axis('off');a.text(.1,.5,'PNP FAILED；未伪造配准')
        f.suptitle(name+'｜P5 Ring约束派生刚体候选：真实B / A→B / 实际XYZ\n相机原文件不变；照片K未认证，始终只作候选；G07始终UNQUALIFIED_CAMERA_STRESS',fontsize=13);f.tight_layout(rect=[0,0,1,.96]);put(f,'P5_adjacent_registration/'+name+'.png')
        parts=[p for p in load(R/'metrics/view_partition.json')if p['group']in gs];nodes={x['block']:x for x in load(R/'metrics/pose_graph_nodes.json')};f,aa=plt.subplots(1,2,figsize=(16,8));ax=aa[0];ax.axis('off');positions={p['block']:(i%4*3,-(i//4)*2)for i,p in enumerate(parts)}
        for e in load(R/'metrics/pose_graph_edges.json'):
            if e['a']not in positions or e['b']not in positions:continue
            x,y=positions[e['a']],positions[e['b']];good=e['included_in_optimization'];ax.plot([x[0],y[0]],[x[1],y[1]],'-'if good else'--',color='#178f6a'if good else'#bd8a34');ax.text((x[0]+y[0])/2,(x[1]+y[1])/2,e['edge_status'].replace('VERIFIED_ADJACENT_CONSTRAINT','条件通过'),fontsize=7)
        for p in parts:
            x,y=positions[p['block']];ax.scatter([x],[y],s=80);ax.text(x,y-.15,p['block']+'\n分量'+str(nodes[p['block']]['component']),ha='center',va='top',fontsize=8)
        ax.set_xlim(-2,11);ax.set_ylim(-2*max(1,(len(parts)+3)//4),1);ax.set_title('绿：经检查条件边；虚线：候选；不强接孤立块')
        cid=next(c['id']for c in cases()if c['group']==gs[0]);d=point_data(cid);side(aa[1],d,cid+'｜当前已存在实际XYZ\nP7新参考尚未生成，不伪画新块',(-65,22));f.suptitle(name+'｜P6 多块位姿图与真实XYZ\n局部条件连通分量独立优化；无未经验证边进入求解；无全局融合认证');f.tight_layout(rect=[0,0,1,.93]);put(f,'P6_global_pose/'+name+'.png')
    from deliver import update,index
    r=load(R/'metrics/pose_graph_status.json');body='正式完成9配对×SIFT/MASt3R全图/MASt3R ROI=27臂，其中18次MASt3R新前向，全部返回匹配。官方本地权重与源码只读，未用神经点图生成几何。\n\n|配对|方法|原匹配|Polyp F一致候选|近BG F一致候选|\n|---|---|---|---|---|\n'
    for x in metrics:
        if x.get('regions'):body+='|'+x['pair']+'|'+x['method']+'|'+str(x['raw_N'])+'|'+str(x['regions']['Polyp']['geometric_candidate_N'])+'|'+str(x['regions']['NearBackground']['geometric_candidate_N'])+'|\n'
    body+='\nF一致只是候选，不是正确匹配标签；密集近邻输出存在相关采样。所有原始点对、描述子置信度、Ring/反光、类别、F内/离群和空间格均保存。PnP只用Cleaned实际Polyp XYZ和历史质量背景原点，源像素最近≤2px；不使用MASt3R点图。每区域4×3格均衡，远BG限额，2个固定种子，Ring中心/法向先验与Ring Mask的有限60次局部优化。目标B RGB仅在预测生成后比较。\n\n'
    body+='|配对|选定候选|状态|独立真实帧状态|\n|---|---|---|---|\n'
    for e in edges.values():body+='|'+e['id']+'|'+str(e.get('selected'))+'|'+e['status']+'|'+e.get('independent_frame_status','缺失')+'|\n'
    body+='\n图为21节点、'+str(r['components'])+'个分量、'+str(r['optimized_edges'])+'条条件通过边；初次全图Open3D因不连通拒绝，已保留日志并改为逐真实连通分量优化。没有添加边解决连通性。G01跨视频仅得到一条**条件约束**，尚未通过完整几何/双向融合验收；三照片K仍未认证，不能记为三维新增。G07不入正常成功率。后续将实际运行5份新HERO参考，只有相机条件检查通过者采用派生位姿，其余保留冻结候选并标记诊断身份。\n\n'
    for path in ['P4_mast3r_matching/G01.png','P4_mast3r_matching/G07_G08.png','P5_adjacent_registration/G06.png','P6_global_pose/G01.png']:body+='!['+path+'](figures/'+path+')\n\n'
    update('Batch B — MASt3R与邻接图',body);index();print('BATCH B figures/report complete',flush=True)
if __name__=='__main__':main()
