"""Accepted real-P0 point/CAD renderer; original-face edges are diagnostics."""
from render import *
from frontier import *
from matplotlib.collections import LineCollection
PINK=np.array([.94,.29,.55]);BLUE=np.array([.15,.65,.93]);COLORS=np.array([PINK,BLUE,[.95,.66,.18],[.31,.74,.39],[.73,.38,.86],[.95,.42,.19]])
def data_blocks(blocks,by_generation=False):
    a=display_arrays(blocks);cid=blocks[0]['reference'];s=source(cid);b=background(cid);col=COLORS[a['generation']%len(COLORS)]if by_generation else a['C'];return dict(P=a['P'],C=col,B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=cid)
def blank(cid,P,C):
    s=source(cid);return dict(P=P,C=C,B=np.empty((0,3)),BC=np.empty((0,3)),p=s['p'],ring=s['ring'],primary=cid)
def lines(ax,XYZ,color,angle_=(-65,22),lw=.8,zorder=4):
    eye,right,up=vis.basis(angle_);xy=np.stack([XYZ@right,XYZ@up],-1);ax.add_collection(LineCollection(xy,colors=color,linewidths=lw,zorder=zorder))
def p0():
    ids=load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections'];fig,axes=plt.subplots(3,4,figsize=(21,15));parameters=[]
    for i,g in enumerate(['G06','G07','G08']):
        sid=g+('_005'if g=='G08'else'_004');main=source(ids[sid]);new=next(c for c in cases()if c['group']==g and c.get('new_reference'));s=source(new['id']);z=old_F2(new['id']);raw=point_data(new['id']);mainids=np.unique(main['F'][clean_faces(ids[sid])]);fids=np.flatnonzero(z['accepted'][s['F']].all(1));newids=np.unique(s['F'][fids]);bounds=diag.square_bounds([main['P'],raw['P'],main['ring'].vertices],[vis.basis((-65,22))])[0];empty=lambda c,n:np.tile(c,(n,1))
        d=blank(ids[sid],main['P'][mainids],empty(PINK,len(mainids)));side(axes[i,0],d,g+' 主参考Cleaned / 粉\n'+('UNQUALIFIED_CAMERA_STRESS'if g=='G07'else main['c']['condition']),(-65,22),bounds)
        n=~cleaned(new['id'])['clean_removed'];d=blank(ids[sid],s['P'][n],empty(BLUE,n.sum()));side(axes[i,1],d,'Cleaned F1蓝色完整来源（非整片获认可）\nF2实际接纳点 '+str(z['accepted'].sum())+'/'+str(n.sum()),(-65,22),bounds)
        d=blank(ids[sid],np.r_[main['P'][mainids],s['P'][newids]],np.r_[empty(PINK,len(mainids)),empty(BLUE,len(newids))]);side(axes[i,2],d,'实际F2完整原面：'+str(len(fids))+'面\n'+f'{s["areas"][fids].sum():.3f} mm²（工程认可，非GT）',(-65,22),bounds)
        edges,_=edge_counts(s['F'][fids]);lines(axes[i,2],s['P'][edges],BLUE,lw=.3,zorder=1)
        b=load_scene(sid,0);front=frontier(b);side(axes[i,3],d,'真实开放边界；非自动可生长\n绿外观测终止 / 橙选面切口 / 红Ring遮挡',(-65,22),bounds);colors=np.array([{'OBSERVATION_TERMINATION':'#159c40','GROWTH_SELECTION_FRONTIER':'#dd891e','RING_OCCLUSION':'#bc3333'}.get(x,'#777')for x in front['categories']]);lines(axes[i,3],front['XYZ_edges'],colors,lw=.7);parameters.append(dict(scene=sid,source=new['id'],bounds_mm=bounds,angle=[-65,22],original_faces_used=fids,old_F2_points=int(z['accepted'].sum()),camera_condition=new['condition']))
    fig.suptitle('P0｜人工认可区域的来源核对：完整F1来源 ≠ F2接纳点 ≠ 完整原始三角面\n主体/新增均实际XYZ，黑色实体CAD。旧几何保存独立版本；用户最新授权允许派生的局部联合调整。',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);fig.subplots_adjust(hspace=.26);put(fig,'Fig1_engineering_seed_recovery.png');save('provenance/Fig1_PARAMETERS.json',parameters)
    fig,axes=plt.subplots(2,3,figsize=(19,11))
    for i,sid in enumerate(['G01_004','G01_005']):
        d=data_blocks(load_scene(sid,0));fr=frontier(load_scene(sid,0));bounds=diag.square_bounds([d['P'],d['B'],d['ring'].vertices],[vis.basis((-65,22)),vis.basis((0,0))])
        for j,a in enumerate([(-65,22),(0,0)]):side(axes[i,j],d,sid+' 初始主参考 / 实际RGB / mm',a,bounds[j]);lines(axes[i,j],fr['XYZ_edges'][fr['eligible']],'#d0472d',a,lw=.8)
        axes[i,2].axis('off');text=sid+' 生长边界分类\n'
        for kind in sorted(set(fr['categories'])):text+=kind+f'：{fr["lengths"][fr["categories"]==kind].sum():.2f} mm\n'
        axes[i,2].text(.02,.95,text+'\n清理内孔/深度断裂/未知不自动当外边界。\nRing边界须新源真实可见才可尝试外延。\n旧F2仅对照，不再用其点级接纳作唯一算法。',va='top',fontsize=10)
    fig.suptitle('P1｜G01实际原面边界：斜视 / 侧视 / 分类，黑色实体CAD；背景仅DISPLAY_ONLY',fontsize=13);fig.tight_layout(rect=[0,.01,1,.94]);put(fig,'Fig2_G01_initial_frontiers.png')
    fig,axes=plt.subplots(5,3,figsize=(18,23))
    for i,sid in enumerate(ids):
        cc=[c for c in cases()if sceneid(c)==sid];Ps=[];Cs=[];Fp=[];Fc=[]
        for j,c in enumerate(cc):
            s=source(c['id']);k=~cleaned(c['id'])['clean_removed'];Ps.append(s['P'][k]);Cs.append(np.tile(COLORS[j%6],(k.sum(),1)));k=old_F2(c['id'])['accepted'];Fp.append(s['P'][k]);Fc.append(np.tile(COLORS[j%6],(k.sum(),1)))
        main=source(ids[sid]);bounds=diag.square_bounds(Ps+[main['ring'].vertices],[vis.basis((-65,22))])[0]
        for j,(P,C,title)in enumerate([(np.concatenate(Ps),np.concatenate(Cs),'历史Cleaned F1全来源'),(np.concatenate(Fp),np.concatenate(Fc),'历史F2点级选择（只读对照）')]):side(axes[i,j],blank(ids[sid],P,C),sid+' / '+title,(-65,22),bounds)
        d=data_blocks(load_scene(sid,0),True);d['B']=np.empty((0,3));d['BC']=d['B'];side(axes[i,2],d,'按质量/连续支持面积选定S0\n'+('UNQUALIFIED_CAMERA_STRESS'if sid.startswith('G07')else main['c']['condition']),(-65,22),bounds)
    fig.suptitle('P0基线｜Cleaned F1 / 历史F2 / 本轮初始主体与工程种子\n每行固定同视角、毫米范围与点大小；所有完整原面/源点均保留，最终几何是否改善尚待实验',fontsize=13);fig.tight_layout(rect=[0,.01,1,.96]);fig.subplots_adjust(hspace=.30);put(fig,'Fig3_F1_F2_selected_initial.png')
if __name__=='__main__':p0()
