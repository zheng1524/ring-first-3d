"""CPU-only real-Mesh figures and conditional evidence report; no best-step selection."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
extract(HISTORY_N0/'code/figures.py',['look_frame','shade'],globals())
STEPS=[1000,2000,5000,10000]
DOMAINS=load(TASK/'config/EXPERIMENT_FROZEN.json')['domains']


def output(scene,step):
    folder=TASK/'groups'/scene/'local_results'/f'single_M1_step{step:06d}'
    path=folder/'raw_mm.ply'
    return trimesh.load(path,process=False)if path.exists()else None


def metric(scene,step):
    path=TASK/'groups'/scene/'metrics'/f'single_M1_step{step:06d}_GEOMETRY.json'
    return load(path)if path.exists()else None


def raw_hero(scene,clean=False):
    points=[];faces=[];offset=0
    for cid in ORDERS[scene]:
        a=original(cid);P=a['P'];F=a['F']
        if clean:
            n=native(cid);uv=affine_uv(a['uv'],n['Kn']@np.linalg.inv(n['K']));ij=np.floor(uv+.5).astype(int);h,w=n['depth'].shape
            inside=(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h);keep=np.zeros(len(ij),bool)
            v=np.load(TASK/'frozen_inputs/native'/(cid+'.npz'))['valid'];keep[inside]=v[ij[inside,1],ij[inside,0]]
            F=F[keep[F].all(1)]
        points.append(P);faces.append(F+offset);offset+=len(P)
    return trimesh.Trimesh(np.concatenate(points),np.concatenate(faces),process=False)


def render(scene,mesh,view=0,size=300):
    dom=DOMAINS[scene];center=np.array(dom['O_mm'])+dom['L_mm']/2;W=dom['L_mm']
    B=look_frame([[.5,-1.,.85],[1.,.15,.15],[.001,-.001,1.]][view])
    v,u=np.mgrid[:size,:size];xy=np.c_[((u.ravel()+.5)/size-.5)*W,((v.ravel()+.5)/size-.5)*W]
    origins=center+xy@B[:,:2].T-B[:,2]*100;rays=np.c_[origins,np.broadcast_to(B[:,2],origins.shape)].astype(np.float32)
    if mesh is not None and len(mesh.faces):
        ds=mesh_scene(mesh.vertices,mesh.faces);result=ds.cast_rays(o3d.core.Tensor(rays))
        img,hit,_=shade(np.asarray(mesh.vertices),np.asarray(mesh.faces),result,B[:,2],smooth=False)
    else:img=np.ones((size*size,3));hit=np.full(size*size,np.inf)
    cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy()
    img[np.isfinite(cad)&(cad<=hit+.002)]=.015
    return img.reshape(size,size,3),[-W/2,W/2,W/2,-W/2]


def panel(ax,scene,mesh,title,view=0):
    if mesh is None:title+=' / NO ZERO-SURFACE MESH'
    img,extent=render(scene,mesh,view)
    ax.imshow(img,extent=extent);ax.set_title(title,fontsize=9);ax.set_xlabel('plane x mm',fontsize=8);ax.set_ylabel('plane y mm',fontsize=8);ax.tick_params(labelsize=7)


def finish(fig,name,title):
    fig.suptitle(title,fontsize=12);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(TASK/'figures'/name,dpi=140);plt.close(fig)


def main():
    plt.rcParams.update({'font.size':8})
    fig,axs=plt.subplots(3,4,figsize=(14,10))
    gate={r['source']:r for r in load(TASK/'config/CAMERA_GATE_RESULTS.json')['sources']}
    for row,(scene,ids)in enumerate(ORDERS.items()):
        for col,cid in enumerate(ids):
            cp=np.load(TASK/'frozen_inputs/crops'/(cid+'.npz'));axs[row,col].imshow(cp['RGB'])
            axs[row,col].contour(cp['labels']==1,levels=[.5],colors='lime',linewidths=.5)
            axs[row,col].set_title(cid+'\n'+gate[cid]['block'].split('_')[-1]+' / '+gate[cid]['qualification'],fontsize=8);axs[row,col].axis('off')
        panel(axs[row,3],scene,raw_hero(scene,True),scene+' cleaned original-face display')
    finish(fig,'Fig1_Inputs.png','Actual RGB / original Mask / frozen partition; black actual Ring CAD; no GT')

    for view,name in [(0,'Fig2_Raw_Clean_Initial_Final.png'),(1,'Fig2b_Side_Comparison.png')]:
        fig,axs=plt.subplots(3,4,figsize=(14,10))
        for row,scene in enumerate(ORDERS):
            values=[(raw_hero(scene),'Raw HERO original faces'),(raw_hero(scene,True),'Cleaned original-face display'),(output(scene,0),'M1 initialization'),(output(scene,10000),'M1 10000'if metric(scene,10000)else'M1 10000 NOT_RUN')]
            for col,(m,title)in enumerate(values):panel(axs[row,col],scene,m,scene+' / '+title,view)
        finish(fig,name,'All original geometry retained; same own metric window per polyp; no normal smoothing')

    for view,name in [(0,'Fig3_M1_1x_2x_5x_10x.png'),(1,'Fig3b_M1_Side_Stages.png')]:
        fig,axs=plt.subplots(3,4,figsize=(14,10))
        for row,scene in enumerate(ORDERS):
            for col,step in enumerate(STEPS):panel(axs[row,col],scene,output(scene,step),f'{scene} M1 {step} ({step//1000}x)'+(' NOT_RUN'if not metric(scene,step)else''),view)
        finish(fig,name,'Actual learned SDF iso-zero Mesh at fixed 256^3; same camera/mm per row; black actual CAD')

    fig,axs=plt.subplots(9,4,figsize=(13,23))
    for row,cid in enumerate(ALL_IDS):
        scene=CC[cid]['scene_id'];cp=np.load(TASK/'frozen_inputs/crops'/(cid+'.npz'));n=native(cid)
        axs[row,0].imshow(cp['RGB']);axs[row,0].contour(cp['labels']==1,levels=[.5],colors='lime',linewidths=.5);axs[row,0].set_title(cid+' RGB / original Mask')
        ids=cp['source_ids'];inside=ids>=0;W=n['depth'].shape[1]
        zmin=float(n['depth'][n['valid']].min());zmax=float(n['depth'][n['valid']].max())
        for col,step in [(1,1000),(2,10000)]:
            file=TASK/'groups'/scene/'local_results'/f'single_M1_step{step:06d}'/'evaluation.npz'
            if file.exists():
                data=np.load(file);hit=data[cid+'_hit_mm'];uv_id=data[cid+'_native_id'];depth=np.full(n['depth'].size,np.nan);depth[uv_id]=np.where(np.isfinite(hit),hit,np.nan)
                image=np.full(ids.shape,np.nan);image[inside]=depth[ids[inside]]
                axs[row,col].imshow(image,vmin=zmin,vmax=zmax,cmap='viridis')
                pred=data[cid+'_full_image_visible_hit'].ravel();scope=np.zeros(ids.shape,bool);scope[inside]=pred[ids[inside]]
                axs[row,col].contour(scope,levels=[.5],colors='red',linewidths=.5)
                axs[row,col].set_title(f'M1 {step} first axial mm [{zmin:.1f},{zmax:.1f}]')
                if step==10000:
                    violation=scope&(cp['labels']==0);axs[row,3].imshow(cp['RGB']);overlay=np.zeros((*ids.shape,4));overlay[violation]=[1,0,0,.8];axs[row,3].imshow(overlay);axs[row,3].set_title('Red: predicted visible outside Polyp; Ring excluded')
            else:axs[row,col].text(.1,.5,f'{step} NOT_RUN',transform=axs[row,col].transAxes)
        for ax in axs[row]:ax.axis('off')
    finish(fig,'Fig4_Real_RGB_First_Depth_Overflow.png','All nine real source cameras; MISS left empty; raw Mesh not clipped by Mask; no GT')

    comparisons=[];reference=[];checkpoints=[]
    for scene in ORDERS:
        root=TASK/'groups'/scene
        for step in [0,200,500]+STEPS:
            m=metric(scene,step)
            if not m:continue
            rr=m['rays'];den=sum(r['fixed_visible_N']for r in rr)
            comparisons.append(dict(scene=scene,step=step,fixed_visible_N=den,hit_fraction=sum(r['hit_N']for r in rr)/den,
                agreement_fraction=sum(r['agreement_N']for r in rr)/den,
                cleaned_retention_fraction=sum(r['cleaned_HERO_retained_0p25_N']for r in rr)/max(1,sum(r['cleaned_visible_N']for r in rr)),
                fourplus_fraction=sum(r['multi_4plus_N']for r in rr)/den,
                negative_volume_mm3=m['negative_grid_volume_mm3'],components_N=m.get('components_N'),
                mesh_area_mm2=m.get('area_mm2'),surface_categories=m.get('surface_categories',{})))
            reference.extend(rr)
        index=root/'metrics/single_M1_CHECKPOINT_INDEX.json'
        if index.exists():checkpoints.append(dict(scene=scene,**load(index)))
    # Root writers, not the per-scene training output writer.
    def write_json(name,value):(TASK/name).write_text(json.dumps(clean(value),ensure_ascii=False,indent=2)+'\n')
    write_json('metrics/STAGE_COMPARISON.json',comparisons);write_json('metrics/PER_REFERENCE_RESULTS.json',reference)
    write_json('LOCAL_CHECKPOINT_INDEX.json',checkpoints)
    with (TASK/'metrics/STAGE_COMPARISON.csv').open('w',newline='')as f:
        if comparisons:
            writer=csv.DictWriter(f,fieldnames=list(comparisons[0]));writer.writeheader();writer.writerows({k:json.dumps(v)if isinstance(v,dict)else v for k,v in r.items()}for r in comparisons)
    complete=[scene for scene in ORDERS if metric(scene,10000)]
    report=['# MonoSDF 多物理息肉 M1 延长训练报告','',f'实际完成10,000步并导出最终Mesh：{len(complete)}/3。尚缺结果不记为成功。','',
        '本轮为探索，不是充分收敛或物理精度验收。历史正式M1=0；研究者明确批准新M1基线1000，累计到10000。各阶段同一模型、Adam、调度器连续延伸，不在1000步重置。', '',
        '|物理息肉|步数|1k→10k首次深度一致率≤.25mm|1k→10k清理主面点保留|1k→10k四层以上交点|',
        '|---|---:|---|---|---|']
    answers=[]
    for scene in ORDERS:
        a=next((r for r in comparisons if r['scene']==scene and r['step']==1000),None);b=next((r for r in comparisons if r['scene']==scene and r['step']==10000),None)
        if a and b:
            pct=lambda x:f'{100*x:.2f}%'
            report.append(f'|{scene}|10000|{pct(a["agreement_fraction"])}→{pct(b["agreement_fraction"])}|{pct(a["cleaned_retention_fraction"])}→{pct(b["cleaned_retention_fraction"])}|{pct(a["fourplus_fraction"])}→{pct(b["fourplus_fraction"])}|')
            improved=b['agreement_fraction']>=a['agreement_fraction']and b['cleaned_retention_fraction']>=a['cleaned_retention_fraction']
            answers.append(dict(scene=scene,fixed_geometry_metrics_improve_without_retention_drop=improved,
                negative_volume_ratio=b['negative_volume_mm3']/max(1e-12,a['negative_volume_mm3']),
                note='aggregate proxy only; every reference and visibility failure must also be reviewed'))
        else:report.append(f'|{scene}|NOT_COMPLETED|NOT_EVALUABLE|NOT_EVALUABLE|NOT_EVALUABLE|')
    report+=['','## 判断边界与后续审阅','',
        '跨源HERO与相机均非GT；所有相机资格、固定原生分母、MISS和逐参考结果均保留，不能仅凭汇总或低Loss宣布成功。光滑性/连通与未知闭合独立报告；未知面未被删除或冒充解剖真值。', '',
        'Raw/Cleaned图使用原始归档面，Cleaned仅按当前原生有效性映射筛选原面用于对照，未移动顶点；训练仍用原生HERO。该显示存在已知离散化差异。所有SDF Mesh都由真实网络场经官方提取得到。','',
        '当前候选排序仅根据固定观测代理供下一轮投入选择；需人工检查图3/3b的主体、细柄、侧面与错误封闭，才能作最终几何解释。没有自动放大预算、换源、改Loss或引入GT。', '',
        '完整配置/源资格见config和groups/*/config；逐组原场、Mesh和evaluation.npz在groups/*/local_results，参数及Adam等完整状态索引见LOCAL_CHECKPOINT_INDEX.json。', '',
        '|审计项目|必须汇报|','|---|---|','|目标组数|3，G01/G06/G08独立物理息肉|',f'|本算法独立成功|工程完成{len(complete)}/3；科学正确性NOT_EVALUABLE|',f'|本算法失败|未完成{3-len(complete)}/3，指标保留NaN/NOT_EVALUABLE；科学未知不冒称失败|','|历史测量值回退|0；M0仅历史对照，不转作M1基线|','|失败组及具体原因|见FAILURE_LEDGER及各组INTERRUPTION.json|','|最终统计样本|三组固定原生观测；没有物理准确率样本|','|是否使用GT选择算法|否；视角、配置和源码先冻结，GT/Oracle不读|', '',
        '物理MedARE/MAE/p95/max及共同成功组物理配对全部NOT_EVALUABLE。HERO误差是有条件一致性代理。', '',
        '最终核心问题：若一致率和主面保留同时提高，支持“已有观测几何解释改善”的候选；任一参考覆盖下降必须保留失败风险。不能把新面积/闭合或RGB变好直接写成真实新侧面。']
    (TASK/'TECHNICAL_REPORT.md').write_text('\n'.join(report)+'\n')
    write_json('metrics/EXPLORATORY_CONCLUSION.json',dict(completed_groups=complete,checks=answers,physical_accuracy='NOT_EVALUABLE',human_visual_review='PENDING',automatic_next_training=False))
    print('DELIVERED',len(complete),'/3 completed; no extra optimizer updates',flush=True)


if __name__=='__main__':main()
