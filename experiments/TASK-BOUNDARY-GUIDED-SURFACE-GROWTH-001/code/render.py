"""Exact previously accepted scene drawing functions, rebound to this task."""
from geometry import *
import colorsys
plt=vis.configure()
ns=globals()
tree=ast.parse((GRAZ/'code/scene_renderer.py').read_text())
for node in tree.body:
    if isinstance(node,ast.FunctionDef)and node.name in ['camera_scene','depth_colors','scene_image','side']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(GRAZ/'code/scene_renderer.py'),'exec'),ns)
def point_data(cid,version='Cleaned'):
    s=source(cid);b=background(cid);z=np.load(R/f'local_results/cleaned/{cid}.npz');keep=~z['clean_removed']if version=='Cleaned'else~z['historical_T2_deleted']if version=='T2'else np.ones(len(s['P']),bool)
    return dict(P=s['P'][keep],C=s['C'][keep],B=b['P'],BC=b['C'],p=s['p'],ring=s['ring'],primary=cid)
def put(f,path):
    p=R/'figures'/path;p.parent.mkdir(parents=True,exist_ok=True);f.savefig(p,dpi=150,facecolor='white');plt.close(f)
def batch_a():
    groups=[('G01',['G01']),('G06',['G06']),('G07_G08',['G07','G08'])];views=load(R/'metrics/view_distribution.json');parts=load(R/'metrics/view_partition.json');cleanrows=load(R/'metrics/cleaned_input_audit.json')
    for name,gs in groups:
        cc=[c for c in cases()if c['group']in gs];rep=list({sceneid(c):c['id']for c in cc}.values());f,aa=plt.subplots(len(rep),3,figsize=(16,5*len(rep)),squeeze=False)
        for i,cid in enumerate(rep):
            raw=point_data(cid,'Raw');bounds=diag.square_bounds([raw['P'],raw['B'],raw['ring'].vertices],[vis.basis((-65,22))])[0]
            for j,label in enumerate(['Raw','T2','Cleaned']):d=point_data(cid,label);side(aa[i,j],d,cid+' / '+label+f' N={len(d["P"])}',(-65,22),bounds)
        f.suptitle(name+'｜P1 Raw / Historical-T2 / CLEAN_FOR_FUSION\n真实原XYZ/RGB，黑色CAD；清理为实验性输入，不认证真几何；背景DISPLAY_ONLY',fontsize=13);f.tight_layout(rect=[0,0,1,.93]);put(f,'P1_cleaning/'+name+'.png')
        ss=list(dict.fromkeys(v['source_id']for v in views if v['group']in gs and v.get('pose_known')and'view_direction'in v));f,aa=plt.subplots(len(ss),2,figsize=(14,5*len(ss)),squeeze=False)
        for i,sid in enumerate(ss):
            vv=[v for v in views if v['source_id']==sid and'view_direction'in v];Q=np.array([v['c2w'][:3][0]for v in []])if False else np.array([np.array(v['c2w'])[:3,3]for v in vv]);center=np.array(vv[0]['polyp_center_proxy_mm']);basis=vis.basis((-65,22));q=np.c_[Q@basis[1],Q@basis[2]];cc0=[c for c in cc if c['group']==vv[0]['group']and c['video']==sid[-3:]];d=point_data(cc0[0]['id']);bounds=diag.square_bounds([Q,d['P'],d['ring'].vertices],[basis])[0];side(aa[i,0],d,sid+'｜实际冻结相机候选 / mm',(-65,22),bounds);aa[i,0].plot(q[:,0],q[:,1],'-',c='#bbb',lw=.7)
            for v,xy in zip(vv,q):
                color='#d34b35'if v['camera_candidate_only']else'#217bb2';aa[i,0].plot(*xy,'o',ms=4,color=color);z=np.array([np.array(v['c2w'])[:3,3],center]);xy2=np.c_[z@basis[1],z@basis[2]];aa[i,0].plot(xy2[:,0],xy2[:,1],c=color,lw=.3,alpha=.5)
            thumb=next(x for x in load(R/'metrics/new_reference_plan.json')if x['group']==vv[0]['group']and x['video']==sid[-3:]);v=next(x for x in vv if x['id']==thumb['reference_view']);aa[i,1].imshow(Image.open(v['RGB']));aa[i,1].axis('off');aa[i,1].set_title(v['view_id']+'｜待新推理；距旧参考方向 '+f'{thumb["angular_gap_to_old_deg"]:.2f}°\n'+v['pose_status'],fontsize=10)
        f.suptitle(name+'｜P2 中心到息肉代理的真实视向分析（非只用光轴）\n蓝：既有筛过相机；红：未认证候选；G07始终UNQUALIFIED_CAMERA_STRESS。不同视频独立坐标',fontsize=13);f.tight_layout(rect=[0,0,1,.92]);put(f,'P2_view_distribution/'+name+'.png')
        pp=[p for p in parts if p['group']in gs];f,ax=plt.subplots(figsize=(15,8));ax.axis('off');cols=5;positions={p['block']:(i%cols*3.0,-(i//cols)*2.0)for i,p in enumerate(pp)}
        for e in load(R/'metrics/adjacency_graph.json'):
            if e['a']not in positions or e['b']not in positions or e['status']!='CANDIDATE':continue
            a,b=positions[e['a']],positions[e['b']];ax.plot([a[0],b[0]],[a[1],b[1]],c='#bc8943',ls='--',lw=1,zorder=0)
        from matplotlib.offsetbox import OffsetImage,AnnotationBbox
        for p in pp:
            xy=positions[p['block']];v=next(v for v in views if v['id']==p['representative']);im=np.asarray(Image.open(v['RGB']).resize((144,81)));ax.add_artist(AnnotationBbox(OffsetImage(im,zoom=.7),xy,frameon=True));ax.text(xy[0],xy[1]-.48,p['block']+'\nC:'+str(len(p['Core_Frames']))+' T:'+str(len(p['Transition_Frames']))+' H:'+str(len(p['Holdout_Frames'])),ha='center',va='top',fontsize=8)
        ax.set_xlim(-1.5,13.5);ax.set_ylim(-(max(1,(len(pp)+4)//5))*2,1.0);f.suptitle(name+'｜P3 View-Adjacency Graph\n节点为真实方向块；虚线仅候选邻接；Core/Transition/Holdout匹配前冻结。无跨视频已认证边。');f.tight_layout(rect=[0,0,1,.92]);put(f,'P3_view_partition/'+name+'.png')
        # P0 is a real input identity + module provenance panel, not invented geometry.
        f,aa=plt.subplots(len(rep),2,figsize=(14,4.5*len(rep)),squeeze=False)
        for i,cid in enumerate(rep):
            s=source(cid);aa[i,0].imshow(s['frame']);aa[i,0].axis('off');aa[i,0].set_title(cid+' / 真实冻结输入');rows=[x for x in cleanrows if x['reference']==cid];txt='P0 — RGB/Mask/K/c2w → HERO深度 → 原XYZ\n'+s['c']['condition']+'\n'+f'Raw {len(s["P"])}点 / {len(s["F"])}原面\n'+f'CLEAN_FOR_FUSION {rows[0]["clean_N"]}点\n'+s['c']['pack']+'\n代码：既有load_official / unproject / depth_mesh\nMASt3R：官方本地权重，只做匹配\n本批未新推理；P7将真实运行，绝不重命名旧缓存';aa[i,1].axis('off');aa[i,1].text(.01,.95,txt,va='top',wrap=True,fontsize=10)
        f.suptitle(name+'｜P0 真实资产与复用接口审计；来源/源码SHA见清单');f.tight_layout(rect=[0,0,1,.94]);put(f,'P0_code_reuse/'+name+'.png')
    print('BATCH A figures: 3 composites per P0/P1/P2/P3',flush=True)
if __name__=='__main__':batch_a()
