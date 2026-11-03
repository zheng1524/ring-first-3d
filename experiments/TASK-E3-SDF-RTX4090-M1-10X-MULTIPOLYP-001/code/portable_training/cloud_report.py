"""Independent CPU visualization of official raw outputs; never edits predicted Mesh."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
extract(HISTORY_N0/'code/figures.py',['look_frame','shade'],globals())
extract(TASK/'code/predecessor_deliver.py',['output','metric','raw_hero'],globals())
DOMAINS=load(TASK/'config/EXPERIMENT_FROZEN.json')['domains']
STEPS=[2000,4000,10000,20000]
VIEWS=[[.5,-1.,.85],[1.,.15,.15],[-1.,.15,.15],[.15,1.,.15],[.15,-1.,.15],[.001,-.001,1.]]


def write(name,value):
    p=TASK/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(value),ensure_ascii=False,indent=2)+'\n')
def all_metrics(scene):return [load(p)for p in sorted((TASK/'groups'/scene/'metrics').glob('single_M1_step*_GEOMETRY.json'))]
def render(scene,mesh,view=0,categories=None,size=300):
    d=DOMAINS[scene];C=np.array(d['O_mm'])+d['L_mm']/2;W=d['L_mm'];B=look_frame(VIEWS[view])
    yy,xx=np.mgrid[:size,:size];xy=np.c_[((xx.ravel()+.5)/size-.5)*W,((yy.ravel()+.5)/size-.5)*W]
    origin=C+xy@B[:,:2].T-B[:,2]*100;rays=np.c_[origin,np.broadcast_to(B[:,2],origin.shape)].astype(np.float32)
    if mesh is not None and len(mesh.faces):
        ds=mesh_scene(mesh.vertices,mesh.faces);result=ds.cast_rays(o3d.core.Tensor(rays))
        img,hit,ids=shade(np.asarray(mesh.vertices),np.asarray(mesh.faces),result,B[:,2],smooth=False)
        if categories is not None:
            ok=np.isfinite(hit);cat=categories[ids[ok]]
            img[ok]=np.array([[.2,.7,.4]if c=='OBSERVED_NEAR_PROXY'else([.95,.6,.2]if c=='INFERRED_UNSUPPORTED_PROXY'else[.6,.4,.8])for c in cat])
    else:img=np.ones((len(rays),3));hit=np.full(len(rays),np.inf)
    cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();img[np.isfinite(cad)&(cad<=hit+.002)]=.015
    return img.reshape(size,size,3),[-W/2,W/2,W/2,-W/2]
def panel(ax,scene,mesh,title,view=0,categories=None):
    image,extent=render(scene,mesh,view,categories);ax.imshow(image,extent=extent);ax.set_title(title,fontsize=8)
    ax.set_xlabel('plane x mm',fontsize=7);ax.set_ylabel('plane y mm',fontsize=7);ax.tick_params(labelsize=6)
def finish(fig,name,title):
    fig.suptitle(title,fontsize=12);fig.tight_layout(rect=[0,0,1,.965]);fig.savefig(TASK/'figures'/name,dpi=140);plt.close(fig)


def main():
    (TASK/'figures').mkdir(exist_ok=True);latest={}
    for scene in ORDERS:
        m=all_metrics(scene)
        if m:latest[scene]=m[-1]
    fig,axs=plt.subplots(3,5,figsize=(17,10))
    gate={r['source']:r for r in load(TASK/'config/CAMERA_GATE_RESULTS.json')['sources']}
    for row,(scene,ids)in enumerate(ORDERS.items()):
        for col,cid in enumerate(ids):
            cp=np.load(TASK/'frozen_inputs/crops'/(cid+'.npz'));axs[row,col].imshow(cp['RGB'])
            axs[row,col].contour(cp['labels']==1,levels=[.5],colors='lime',linewidths=.5)
            axs[row,col].set_title(cid+'\n'+gate[cid]['qualification'],fontsize=7);axs[row,col].axis('off')
        panel(axs[row,3],scene,raw_hero(scene),scene+' Raw original HERO')
        panel(axs[row,4],scene,raw_hero(scene,True),'Cleaned original-face display')
    finish(fig,'Fig1_HERO_Inputs.png','Actual RGB/Mask/current Gate; Raw and cleaned original faces; black actual CAD')

    for view,name in [(0,'Fig2_M1_1x_2x_5x_10x.png'),(1,'Extra_Stages_Side.png')]:
        fig,axs=plt.subplots(3,4,figsize=(14,10))
        for row,scene in enumerate(ORDERS):
            for col,step in enumerate(STEPS):
                m=metric(scene,step);panel(axs[row,col],scene,output(scene,step),f'{scene} {step} ({step//2000}x)'+(' NOT_RUN'if m is None else''),view)
        finish(fig,name,'True neural iso-zero Mesh; same own metric window/view,256^3; no geometry smoothing/deletion')

    fig,axs=plt.subplots(3,6,figsize=(18,9))
    for row,scene in enumerate(ORDERS):
        info=latest.get(scene);step=info['step']if info else None;mesh=output(scene,step)if step is not None else None
        for col in range(6):panel(axs[row,col],scene,mesh,f'{scene} step{step} view{col+1}'if info else scene+' NOT_RUN',col)
    finish(fig,'Fig3_Latest_Six_Views.png','All raw predicted faces; six fixed Ring-world views; black actual CAD; not physical truth certification')

    fig,axs=plt.subplots(3,4,figsize=(14,10))
    for row,(scene,ids)in enumerate(ORDERS.items()):
        cid=ids[0];cp=np.load(TASK/'frozen_inputs/crops'/(cid+'.npz'));axs[row,0].imshow(cp['RGB'])
        axs[row,0].contour(cp['labels']==1,levels=[.5],colors='lime',linewidths=.5);axs[row,0].set_title(cid+' real RGB/Mask');axs[row,0].axis('off')
        info=latest.get(scene)
        if info:
            step=info['step'];folder=TASK/'groups'/scene/'local_results'/info['tag'];data=np.load(folder/'evaluation.npz')
            n=native(cid);depth=np.full(n['depth'].size,np.nan);hit=data[cid+'_hit_mm'];depth[data[cid+'_native_id']]=np.where(np.isfinite(hit),hit,np.nan)
            pixel=cp['source_ids'];inside=pixel>=0;image=np.full(pixel.shape,np.nan);image[inside]=depth[pixel[inside]]
            valid_depth=n['depth'][n['valid']];axs[row,1].imshow(image,cmap='viridis',vmin=float(valid_depth.min()),vmax=float(valid_depth.max()))
            axs[row,1].set_title(f'First axial depth mm, step{step}');axs[row,1].axis('off')
            mask=data[cid+'_full_image_visible_hit'].ravel();projected=np.zeros(pixel.shape,bool);projected[inside]=mask[pixel[inside]]
            axs[row,2].imshow(cp['RGB']);rgba=np.zeros((*pixel.shape,4));rgba[projected&(cp['labels']==0)]=[1,0,0,.8];axs[row,2].imshow(rgba);axs[row,2].set_title('Red=outside real Polyp; Ring excluded');axs[row,2].axis('off')
            mesh=output(scene,step);cat=data['mesh_face_category']if'mesh_face_category'in data else None
            panel(axs[row,3],scene,mesh,'Green=HERO-near; orange=inferred; purple=unknown',categories=cat)
        else:
            for ax in axs[row,1:]:ax.text(.2,.5,'NOT_RUN',transform=ax.transAxes);ax.axis('off')
    finish(fig,'Fig4_Observed_Inferred_Projection.png','Evidence from true cameras/Mask/HERO/CAD; proxy labels, not ground truth; all Mesh faces preserved')

    fig,axs=plt.subplots(1,3,figsize=(14,4))
    for ax,scene in zip(axs,ORDERS):
        files=sorted((TASK/'groups'/scene/'metrics').glob('single_M1_TRAINING.csv'));rr=[]
        legacy=TASK/'lineage/G01_local_training.csv'
        if scene=='G01_004'and legacy.exists():rr=[r for r in rows(legacy)if int(r['step'])<=4000]
        for file in files:rr+=rows(file)
        for key in ['loss','surface','first_depth','rgb']:
            use=[r for r in rr if r.get(key)not in [None,'']]
            if use:ax.plot([int(r['step'])for r in use],[float(r[key])for r in use],label=key)
        ax.set_title(scene);ax.set_xscale('symlog',linthresh=100);ax.set_xlabel('actual cumulative optimizer updates');ax.legend(fontsize=7);ax.grid(alpha=.2)
    finish(fig,'Extra_Training_Losses.png','Recorded actual optimization; lower loss alone is not geometric improvement')

    summaries=[];per_reference=[]
    for scene in ORDERS:
        for m in all_metrics(scene):
            rr=m['rays'];den=sum(r['fixed_visible_N']for r in rr)
            summaries.append(dict(scene=scene,step=m['step'],fixed_visible_N=den,
                hit_fraction=sum(r['hit_N']for r in rr)/den,agreement_fraction=sum(r['agreement_N']for r in rr)/den,
                cleaned_retention=sum(r['cleaned_HERO_retained_0p25_N']for r in rr)/max(1,sum(r['cleaned_visible_N']for r in rr)),
                fourplus_fraction=sum(r['multi_4plus_N']for r in rr)/den,
                negative_volume_mm3=m['negative_grid_volume_mm3'],components=m.get('components_N'),
                surface_categories=m.get('surface_categories',{})))
            per_reference+=rr
    write('metrics/STAGE_SUMMARY.json',summaries);write('metrics/PER_REFERENCE_RESULTS.json',per_reference)
    lines=['# RTX4090 MonoSDF M1 多息肉训练结果','',
        '固定M1比较基准N=2000；每组最低目标20000。G01从完整4000状态接续，G06/G08各自独立新模型；没有将三组步数相加或借用另一息肉的场。', '',
        '环境：RTX4090 24564MiB，driver560.35.03，Python3.12，PyTorch2.7.1+cu126；本地原cu128环境差异已记录，源数据/网络/损失/200k尺度调度不变。', '',
        '|组/阶段|实际步数|固定可见原生分母|首次命中|首层≤.25mm|清理主面点保留|≥4层交点|','|---|---:|---:|---:|---:|---:|---:|']
    for r in summaries:
        if r['step']in STEPS or r['step']==latest[r['scene']]['step']:
            lines.append(f'|{r["scene"]}|{r["step"]}|{r["fixed_visible_N"]}|{r["hit_fraction"]:.2%}|{r["agreement_fraction"]:.2%}|{r["cleaned_retention"]:.2%}|{r["fourplus_fraction"]:.2%}|')
    completed=[s for s in ORDERS if latest.get(s,{}).get('step',0)>=20000]
    lines+=['',f'最低10倍训练完成：{len(completed)}/3。当前未完成阶段保留NOT_RUN，不能提前作科学成败判定。','',
        '## 核心问题','',
        '1. **表面是否改善？** 必须同时比较固定分母首层一致和可信主面保留；逐参考详表也公开，不能用总Loss下降代替。',
        '2. **连续性与细节？** 原始组件、面积、法向角、256³零面及六视角全部保留；网格连续/平滑不等于物理准确。',
        '3. **错误封闭？** 未见/遮挡面单列未知，Mesh全部保留，不能把推断封闭直接认证为真实组织。',
        '4. **HERO是否被改变？** 首层深度/未命中/原面和点保留按原始观测统计，清理屏蔽仍在分母。任一来源下降均为风险，不靠删点或换源掩盖。',
        '5. **新侧面是否合理？** 绿色仅为真实相机/HERO附近代理；橙色/紫色为推断或不足，面积增加不是新解剖证据。',
        '6. **是否值得继续？** 最终仍需研究者/PM读图和逐参考表；只有观测几何解释与保留共同改善才支持继续投入。未达论文完整预算或未收敛不得否定整条路线。', '',
        '模型和优化器完全恢复，不重置loss step/调度器；pilot100次更新计入累计步数。具体耗时和4090速度见metrics/RTX4090_PERFORMANCE.json与RUN_HISTORY.json。', '',
        '## 图与结果','',
        '![输入及HERO](figures/Fig1_HERO_Inputs.png)','![1x2x5x10x](figures/Fig2_M1_1x_2x_5x_10x.png)',
        '![最新六视角](figures/Fig3_Latest_Six_Views.png)','![支持推断与投影](figures/Fig4_Observed_Inferred_Projection.png)', '',
        'checkpoint：groups/场景/checkpoints/single_M1/；原始场/Mesh：groups/场景/local_results/single_M1_stepXXXXXX/。PLY毫米，原始SDF乘本组s转毫米。', '',
        '|审计项目|必须汇报|','|---|---|','|目标组数|3独立物理息肉G01/G06/G08|',f'|本算法独立成功|最低训练工程完成{len(completed)}/3，物理正确性NOT_EVALUABLE|','|本算法失败|未完成阶段NOT_RUN；物理误差NaN，不混作成功|','|历史测量值回退|0|','|失败组及具体原因|控制器/各组INTERRUPTION单列；不改标准制造PASS|','|最终统计样本|三组固定原生分母；无获授权物理GT样本|','|是否用GT选算法|否，GT/Oracle不读；输入/科学配置/源码哈希先冻结|', '',
        '物理MedARE/MAE/p95/max与共同成功组物理配对全部NOT_EVALUABLE。训练视角和HERO相关来源不是独立GT。当前6份INSUFFICIENT_EVIDENCE、3份CONDITIONAL_USABLE，均按既有条件研究入组，不认证绝对位姿。']
    (TASK/'TECHNICAL_REPORT.md').write_text('\n'.join(lines)+'\n')
    write('provenance/REPORT_STATE.json',dict(latest_mesh_steps={s:m['step']for s,m in latest.items()},minimum20k_completed=completed,
        evaluation_GT=False,geometry_deleted=False,human_acceptance='PENDING'))
    print('REPORT_REFRESHED', {s:m['step']for s,m in latest.items()},flush=True)


if __name__=='__main__':main()
