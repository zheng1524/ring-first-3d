"""Four real point figures, exclusively using the recovered C0 renderer."""
import sys
import run as r
sys.path.insert(0,str(r.REPO))
from visualization import real_p0_renderer as vis
np=r.np;R=r.R;plt=vis.configure();cache={};ringcache={};metadata=[]
from matplotlib.patches import Patch

def data(c):
    if c['id']not in cache:
        a=dict(np.load(R/f'local_results/{c["id"]}/Raw_Marked_Cleaned_identities.npz'));rgb=vis.source_colors(c['RGB'],a['source_u'],a['source_v']);cache[c['id']]=(a,rgb)
    return cache[c['id']]
def ring(c):
    if c['ring']not in ringcache:
        p='/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj'if c['ring']=='R10'else'/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj';ringcache[c['ring']]=r.trimesh.load(p,process=False)
    return ringcache[c['ring']]
def bounds(cc,angle):
    # Original limits(): all Raw points and CAD Ring, never re-fit Cleaned bounds.
    return vis.limits([data(c)[0]['XYZ_mm']for c in cc],ring(cc[0]),angle=angle)
def row(c,tier):return next(x for x in RESULTS if x['id']==c['id']and x['tier']==tier)
def panel(ax,c,mode,tier,lim,angle,title=None):
    a,rgb=data(c);P=a['XYZ_mm'];d=a['candidate_'+tier];colors=rgb.copy();keep=np.ones(len(P),bool)
    if mode=='marked':colors[d]=[.86,.10,.10]
    if mode=='cleaned':keep=~d
    st=row(c,tier)
    text=title or {'raw':'Raw 全部原点','marked':'候选标记：红色，非错误GT','cleaned':'Cleaned 派生试验，非正式预测'}[mode]
    detail=f'{int(d.sum())}/{len(P)} 标删；主分量保留 {100*st["raw_main_area_retained_fraction"]:.2f}%'if mode!='raw'else f'N={len(P)}；{c["morphology"]}/{c["ring"]}'
    vis.view(ax,P[keep],colors[keep],ring(c),lim,angle=angle,title=c['id']+' '+text+'\n'+detail,size=.8)
    metadata.append(dict(id=c['id'],mode=mode,tier=tier,bounds_mm=lim,angle_degrees=angle,point_size=.8,source_RGB=True,raw_points=len(P),plotted_points=int(keep.sum()),CAD_ring=c['ring']))
def done(fig,name,title):
    fig.suptitle(title,fontsize=14);fig.tight_layout(rect=[0,.045,1,.93]);fig.subplots_adjust(hspace=.30)
    fig.legend(handles=[Patch(color=[.85,.65,.68],label='原源RGB点颜色，未平滑'),Patch(color=[.86,.10,.10],label='候选删除标记，不是GT'),Patch(color='#26343d',label='原CAD Ring线点')],loc='lower center',ncol=3,fontsize=10)
    fig.savefig(R/f'figures/{name}.png',dpi=160,facecolor='white');plt.close(fig);print('PNG',name,flush=True)
def main():
    global RESULTS
    r.verify();frozen=r.load(R/'provenance/OUTPUTS_FROZEN.json');assert all(r.sha(R/x['path'])==x['sha256']for x in frozen['files'])
    RESULTS=r.load(R/'metrics/reference_results.json');cc=r.cases();tier=r.load(R/'metrics/recommendation.json')['recommended_preview_tier'];angle=(-65,22)
    q=[c for c in cc if c['group']=='G01'and c['video']=='004'];lim=bounds(q,angle);fig,ax=plt.subplots(3,3,figsize=(18,15))
    for i,c in enumerate(q):
        for j,mode in enumerate(['raw','marked','cleaned']):panel(ax[i,j],c,mode,tier,lim,angle)
    done(fig,'Fig1_004_Raw_Marked_Cleaned','Fig1｜004三原参考：Raw / C档候选标记 / C档派生Cleaned\n恢复原C0真实三维绘图，全部对照同相机/尺度；原P0始终保留；无GT')
    q=[c for c in cc if c['group']=='G01'and c['video']=='005'];angle=(0,0);lim=bounds(q,angle);fig,ax=plt.subplots(3,3,figsize=(18,15))
    for i,c in enumerate(q):
        for j,mode in enumerate(['raw','marked','cleaned']):panel(ax[i,j],c,mode,tier,lim,angle)
    done(fig,'Fig2_005_Raw_Marked_Cleaned','Fig2｜005三原参考：复用认可Fig3的原侧视与CAD Ring线点\nC档只试验稀疏拉伸候选；密集曲面真伪未研究，紧密采样对照均保留')
    ids=['G02_004_ref04','G04_004_ref04','G06_004_ref04','G07_004_ref04'];q=[next(c for c in cc if c['id']==id)for id in ids];angle=(-65,22);lim=bounds(q,angle);fig,ax=plt.subplots(4,3,figsize=(18,19))
    for i,c in enumerate(q):
        for j,mode in enumerate(['raw','marked','cleaned']):panel(ax[i,j],c,mode,tier,lim,angle,title=c['condition']+' / '+{'raw':'Raw','marked':'候选C','cleaned':'Cleaned C'}[mode])
    done(fig,'Fig3_multigroup_C_cleanup','Fig3｜Ip / Is / IIa及R5：相同原渲染配置、同毫米视域\nC档存在少删/无动作/边界受损，压力组不记作可靠性成功')
    ids=['G01_004_ref13','G01_005_raw00057','G03_004_ref04'];q=[next(c for c in cc if c['id']==id)for id in ids];fig,ax=plt.subplots(3,4,figsize=(22,16));angle=(0,0)
    for i,c in enumerate(q):
        lim=bounds([c],angle)
        if i<2:
            a,_=data(c);pack=dict(np.load(c['pack']));uv=np.c_[a['source_u'],a['source_v']];_lab,comp,head=r.source_components(pack,uv);minor=comp!=head;cut=np.quantile(uv[minor,1],.8);proxy=minor&(uv[:,1]>=cut);_eye,right,up=vis.basis(angle);center=np.median(a['XYZ_mm'][proxy],axis=0);q2=np.array([center@right,center@up]);lim=[(float(v-5),float(v+5))for v in q2]
        panel(ax[i,0],c,'raw','C',lim,angle,title='Raw，源小分量10mm放大窗'if i<2 else'Raw，相机不合格压力全景')
        for j,t in enumerate(['C','M','A'],1):panel(ax[i,j],c,'cleaned',t,lim,angle,title=t+'档：残留/潜在误删检查')
    done(fig,'Fig4_threshold_failures_and_stalk_risk','Fig4｜同一窗口的三档取舍：潜在细柄受损、拉伸残留及主片断裂压力反例\n前两行是源小分量代理放大，非解剖GT；C/M/A全景指标分母不因窗口裁切改变')
    r.save('provenance/FIGURE_CONFIG.json',dict(renderer='visualization/real_p0_renderer.py',renderer_sha256=r.sha(r.REPO/'visualization/real_p0_renderer.py'),draw_functions_unchanged=True,point_interpolation=False,surface_reconstruction=False,DPI=160,panels=metadata))
    assert all(r.sha(R/x['path'])==x['sha256']for x in frozen['files']);r.verify()
if __name__=='__main__':main()
