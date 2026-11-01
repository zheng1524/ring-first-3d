"""Actual original HERO faces and actual source-ray evidence, CPU only."""
from depth_windows import *
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch,Polygon
plt=vis.configure()
COLORS={'MULTI_SUPPORTED':'#2b9b70','SINGLE_SUPPORTED_UNVERIFIED':'#efb54a','FREE_SPACE_CONFLICT':'#dc473b','CAD_OCCLUDED':'#26384f','CORRESPONDENCE_UNRESOLVED':'#9b59b6','UNKNOWN':'#bdbdbd'}
FIGS={}
def geometry(ax,ids,face_colors=None,bounds=((-13,13),(-13,13)),inset=False):
    e,right,up=vis.basis((-65,22));tri=[];color=[]
    for cid in ids:
        s=source(cid);tri.append(s['P'][s['F']]);rgb=s['RGB'][s['uv'][:,1],s['uv'][:,0]]/255
        col=face_colors.get(cid)if face_colors is not None else None;color.append(rgb[s['F']].mean(1)if col is None else col)
    cad=ring(source(ids[0])['c']['ring']);tri.append(np.asarray(cad.vertices)[cad.faces]);color.append(np.tile([.012,.012,.012],(len(cad.faces),1)));T=np.concatenate(tri);C=np.concatenate(color);order=np.argsort(T.mean(1)@e);xy=np.stack([T@right,T@up],axis=2)
    ax.add_collection(PolyCollection(xy[order],facecolors=C[order],edgecolors='none',rasterized=True));ax.set(xlim=bounds[0],ylim=bounds[1]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([]);scale=5 if bounds[0][1]-bounds[0][0]>=13 else 1;x,y=bounds[0][0]+.5,bounds[1][0]+.5;ax.plot([x,x+scale],[y,y],'k-',lw=1.5);ax.text(x,y+.3,f'{scale} mm',fontsize=6)
    if inset:
        points=np.concatenate([source(cid)['P']for cid in ids]+[np.asarray(cad.vertices)]);P=np.c_[points@right,points@up];mid=(P.min(0)+P.max(0))/2;span=max(np.ptp(P,axis=0))+2;b=[(v-span/2,v+span/2)for v in mid];a=ax.inset_axes([.70,.70,.29,.29]);geometry(a,ids,face_colors,b,False);a.text(.02,.85,'全范围',transform=a.transAxes,fontsize=5)
def consensus_colors(cid):
    c=candidates(cid);r=reduced(cid);col=np.tile([.83,.83,.83],(len(source(cid)['F']),1))
    from matplotlib.colors import to_rgb
    for label,color in COLORS.items():col[c['face_id'][r['label']==label]]=to_rgb(color)
    return col
def finish(fig,name,description,cids):
    fig.savefig(R/'figures'/name,dpi=140,facecolor='white');plt.close(fig);FIGS[name]=dict(description=description,source_ids=cids,geometry='unchanged original HERO triangles + fixed opaque black CAD; no fusion output or inferred surface',camera_pose_modified=False);print('FIGURE',name,flush=True)
def figure1():
    fig,axs=plt.subplots(4,5,figsize=(23,17));ids=[s for sid in scene_ids()for s in ordered_sources(sid)]
    for ax,cid in zip(axs.ravel(),ids):
        c=candidates(cid);r=reduced(cid);geometry(ax,[cid],{cid:consensus_colors(cid)},inset=True);ax.set_title(cid+' | '+ROLES[cid]+f'\n{len(c["face_id"])}候选；支持{(r["label"]=="MULTI_SUPPORTED").sum()} / 冲突代理{(r["label"]=="FREE_SPACE_CONFLICT").sum()}',fontsize=8)
    for a in axs.ravel()[17:]:a.axis('off')
    axs.ravel()[17].legend(handles=[Patch(color=v,label=k)for k,v in COLORS.items()],loc='center',fontsize=8)
    axs.ravel()[18].text(0,.9,'灰色底面：未采样，未判断\n颜色仅是原面重心的证据代理\n全部461,023原面保留\n共享上游图像不等于独立票\n相机资格仍是条件性\nG01两视频不统一坐标',va='top',fontsize=10)
    fig.suptitle('E3-C | 全17来源的 V3 证据分布：支持、冲突、遮挡与未决\n同一±13mm主窗；小窗全范围；颜色不认证整张面或物理准确性',fontsize=15);fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig1_multisource_consensus.png','All17 original raw meshes; centroid-evidence labels only, unsampled faces unassessed',ids)
def figure2():
    specs=load(R/'provenance/RAY_SELECTION_FROZEN.json');mode_rows=rows(R/'MULTIMODAL_DEPTH_CANDIDATES.csv');fig,axs=plt.subplots(4,3,figsize=(21,17));selected=[]
    for k,sid in enumerate(scene_ids()):
        spec=next(r for r in specs if r['scene']==sid and r['selection']=='PREREGISTERED_05_TO_1MM');selected.append(spec);a,b=spec['origin'],spec['observer'];z=np.load(R/'local_results/rays'/(spec['ray_id']+'.npz'));src=list(z['source_ids']);j=src.index(b);t=z['t'];X=z['origin_X'];modes=[r for r in mode_rows if r['ray_id']==spec['ray_id']]
        geometry(axs[k,0],[a,b],inset=True);_,right,up=vis.basis((-65,22));line=z['points'];axs[k,0].plot(line@right,line@up,color='#2574b7',lw=1,ls='--');axs[k,0].scatter([X@right],[X@up],s=30,c='orange',edgecolors='black');axs[k,0].set_title(sid+' | 原Raw面与真实观察源射线\n'+a.replace(sid+'_','')+' → '+b.replace(sid+'_','')+' | face '+str(spec['face_id']),fontsize=9)
        ax=axs[k,1];ax.plot(t,z['S'][j],label='Support（数值响应）',c='#2467b0');ax.plot(t,z['O'][j],label='Occlusion（数值响应）',c='#df9c34');ax.plot(t,z['F'][j],label='Free 原始响应（非合格票）',c='gray',ls=':');ax.plot(t,z['F_V2'][j],label='Free 最低资格门控',c='#ce3934');ax.plot(t,z['F_V3'][j],label='Free V3 合格代理',c='black',ls='--');ax.axvline(next(float(r['axial_depth_in_observer_mm'])for r in modes if r['mode_kind']=='ORIGIN_ORIGINAL_FACE'),c='orange',lw=1);ax.axvline(next(float(r['axial_depth_in_observer_mm'])for r in modes if r['mode_kind']=='OBSERVER_NATIVE_PIXEL'),c='blue',lw=1,ls='--');ax.set(xlabel='观察源相机轴向 Z (mm)',ylabel='未校准响应',ylim=(-.03,1.05));ax.set_title('实际 B0 几何三通道；CAD后方不作负票',fontsize=10);ax.legend(fontsize=6,loc='best')
        ax=axs[k,2]
        for u,sourceid in enumerate(src):ax.plot(t,z['S'][u],lw=1,ls='--'if sourceid==a else'-',label=sourceid.replace(sid+'_','')+('（自身不投外票）'if sourceid==a else''))
        for mi,r in enumerate(modes):
            center=float(r['axial_depth_in_observer_mm']);y=-.05-.035*mi;ax.scatter([center],[y],s=12,c='black')
            if r['lower_mm']and r['upper_mm']:ax.plot([float(r['lower_mm']),float(r['upper_mm'])],[y,y],lw=2,alpha=.7)
        ax.set(xlabel='同一冻结观察源射线的轴向 Z (mm)',ylabel='逐来源Support与独立深度区间',ylim=(-.05-.035*len(modes),1.05));ax.set_title(f'{len(modes)}个来源标记候选；不平均、不选层\n原面/原生深度分离 {abs(spec["delta_native_mm"]):.3f} mm',fontsize=10);ax.legend(fontsize=6,loc='upper right')
    fig.suptitle('E3-C | 真实源相机射线上的 Support / Occlusion / Free-space 与多峰区间\n虚线射线与区间是查询/假设，不是新几何；局部误差窗未校准，重叠区间仍保留来源身份',fontsize=14);fig.tight_layout(rect=[0,0,1,.95]);save('provenance/FIG2_RAY_CASES.json',selected);finish(fig,'Fig2_visibility_channels_and_modes.png','Same-ray real source channel curves, retained original/native modes and actual raw meshes',IDS)
def figure_cases():
    out=[]
    for sid in ['G01_004','G01_005']:
        stretch=[];unique=[]
        for cid in sorted(scene_sources(sid)):
            c=candidates(cid);r=reduced(cid);s=source(cid);edge=np.linalg.norm(s['P'][s['F'][c['face_id']]][:,[1,2,0]]-s['P'][s['F'][c['face_id']]],axis=2).max(1)
            for j,fid in enumerate(c['face_id']):
                if c['tags'][j]&16:stretch.append((float(edge[j]),cid,int(fid),j))
                if c['tags'][j]&8 and c['own_visible'][j]and not(c['tags'][j]&16)and not(c['tags'][j]&32)and r['free'][j]==0:unique.append((cid,int(fid),j))
        if stretch:
            e,cid,fid,j=sorted(stretch,key=lambda x:(-x[0],x[1],x[2]))[0];out.append(dict(scene=sid,source_id=cid,face_id=fid,index=j,kind='STRETCH_PROXY',selection='maximum original edge length within frozen stretch candidates; no consensus-score selection',manual_error_truth='NOT_PROVIDED'))
        if unique:
            cid,fid,j=sorted(unique)[0];out.append(dict(scene=sid,source_id=cid,face_id=fid,index=j,kind='SOURCE_UNIQUE_NO_ADMISSIBLE_OPPOSITION',selection='first lexicographic unique, own-visible, non-stretch/non-minor candidate with no V3 opposition; illustrative case only, not population filtering',manual_anatomy_truth='NOT_PROVIDED'))
    save('provenance/FIG3_CASE_SELECTION.json',out);return out
def figure3():
    specs=figure_cases();fig,axs=plt.subplots(len(specs),4,figsize=(22,4.5*len(specs)))
    for k,spec in enumerate(specs):
        cid=spec['source_id'];j=spec['index'];c=candidates(cid);s=source(cid);fid=spec['face_id'];X=c['XYZ'][j];uv,_=vis.project_camera(X[None],s['K'],s['T']);a=axs[k,0];a.imshow(s['RGB']);a.scatter(uv[0,0],uv[0,1],s=45,c='yellow',edgecolors='red');a.axis('off');a.set_title(cid+f' | 原face {fid}\n'+spec['kind'],fontsize=9);zz=a.inset_axes([.02,.02,.45,.45]);zz.imshow(s['RGB']);x,y=uv[0];zz.set(xlim=(max(0,x-40),min(639,x+40)),ylim=(min(359,y+40),max(0,y-40)));zz.set_xticks([]);zz.set_yticks([])
        colors=np.tile([.83,.72,.72],(len(s['F']),1));colors[fid]=[1,0,0];geometry(axs[k,1],[cid],{cid:colors},inset=True);_,right,up=vis.basis((-65,22));axs[k,1].scatter([X@right],[X@up],s=35,c='yellow',edgecolors='red');axs[k,1].set_title('原始三角面位置及完整原Mesh\n不以证据标签删面',fontsize=9)
        refs=[b for b in scene_sources(spec['scene'])if b!=cid];a=axs[k,2];a.axis('off');text=[];dN=[];dM=[];tau=[]
        for b in refs:
            q=np.load(observer_file(cid,b));text.append(b.replace(spec['scene']+'_','')+f'  S={q["S"][j]:.2f} / F2={int(q["native_free"][j])} / F3={int(q["free3"][j])}\n   O={int(q["behind"][j])} CAD={int(q["cad"][j])}  原生-Raw一致={int(q["align"][j])}')
            dN.append(q['delta'][j]);dM.append(q['raw_delta'][j]);tau.append(q['tau'][j])
        a.text(0,.98,'\n'.join(text),va='top',fontsize=8);a.set_title('逐来源证据（均非错误真值）',fontsize=9)
        a=axs[k,3];yy=np.arange(len(refs));a.hlines(yy,-np.array(tau),tau,color='#b7c8dd',lw=6);a.scatter(dN,yy,c='#356cb0',label='原生轴向差');a.scatter(dM,yy,c='#e18a2d',marker='x',label='Raw首交轴向差');a.axvline(0,c='black',lw=.7);a.set_yticks(yy);a.set_yticklabels([x.replace(spec['scene']+'_','')for x in refs],fontsize=7);a.set_xlabel('各观察源自己的轴向深度差 (mm)',fontsize=8);a.set_title('分开比较，不跨轴平均\n阴影=冻结候选/观察误差区间',fontsize=9);a.legend(fontsize=7)
    fig.suptitle('E3-C | 原生异常延伸代理 vs 单来源独有且无合格反对的候选\n案例按固定几何/字典序规则选择；没有真实错误或真实侧面标签，所有原面均保留',fontsize=14);fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig3_extension_and_unique_surfaces.png','Actual RGB/original face IDs; contrasting evidence without physical-error certification',[s['source_id']for s in specs])
def stacked(ax,entries,labels):
    bottom=np.zeros(len(entries));x=np.arange(len(entries))
    for name,color in COLORS.items():
        y=np.array([e['class_counts'].get(name,0)/e['candidate_N']for e in entries]);ax.bar(x,y,bottom=bottom,color=color,width=.65);bottom+=y
    ax.set_xticks(x);ax.set_xticklabels(labels,fontsize=8);ax.set_ylim(0,1);ax.set_ylabel('固定候选的证据标签比例',fontsize=8)
def figure4():
    ab=load(R/'V0_V3_ABLATION.json');strata=rows(R/'metrics/ALL_OBSERVERS_STRATUM_RESULTS.csv');fig,axs=plt.subplots(4,5,figsize=(25,16))
    for k,sid in enumerate(scene_ids()):
        cid=ordered_sources(sid)[0];geometry(axs[k,0],[cid],{cid:consensus_colors(cid)},inset=False);axs[k,0].set_title(sid+f' | {len(scene_sources(sid))} HERO\n'+('同一物理组 G01'if sid.startswith('G01')else sid.split('_')[0])+'；条件相机',fontsize=9)
        control=ab.get('MATCHED_C0_CHANNEL_ADDITION_AUDIT',{}).get('results',{}).get('ALL_OBSERVERS',{}).get(sid,ab['ALL_OBSERVERS'][sid]);entries=[control['V'+str(v)]for v in range(4)];stacked(axs[k,1],entries,['V0','V1','V2','V3']);axs[k,1].set_title('固定C0通道的补充消融控制\n原预注册版本另保留于JSON',fontsize=10)
        stacked(axs[k,2],[ab[stage][sid]['V3']for stage in ['REP_OBSERVERS','ALL_OBSERVERS']],['代表观察源','全部观察源']);axs[k,2].set_title('V3加入RESERVED\n候选与源自身锚点不变',fontsize=10)
        a=axs[k,3];a.bar([0,1],[entries[3]['raw_channel_mean']['S'],entries[3]['correlation_normalized_channel_mean']['S']],color=['#5189b5','#487252']);a.set_xticks([0,1]);a.set_xticklabels(['原始总响应','相关性归一'],fontsize=8);a.set_ylabel('每固定候选的支持票质量',fontsize=8);a.set_title('质量代理，非正确概率',fontsize=10)
        a=axs[k,4];names=['CO_VISIBLE_SMOOTH_PROXY','STRETCH_PROXY','SOURCE_UNIQUE_PROXY'];rates=[];ns=[]
        for name in names:
            rr=[r for r in strata if r['scene']==sid and r['variant']=='V3'and r['stratum']==name];den=sum(int(r['candidate_N'])for r in rr);num=sum(int(r['any_free_proxy_N'])for r in rr);rates.append(num/den if den else 0);ns.append(den)
        a.bar(range(3),rates,color=['#5189b5','#dc473b','#efb54a'])
        for ii,den in enumerate(ns):
            if den==0:a.text(ii,.03,'N/A',ha='center',fontsize=8)
        a.set_xticks(range(3));a.set_xticklabels(['共视光滑代理','长边代理','独有格代理'],rotation=25,fontsize=7);a.set_ylim(0,1);a.set_ylabel('存在V3自由空间冲突的候选比例',fontsize=8);a.set_title('分层诊断，不是真实错误率\nN='+str(ns),fontsize=9)
    fig.legend(handles=[Patch(color=v,label=k)for k,v in COLORS.items()],loc='lower center',ncol=3,fontsize=8);fig.suptitle('E3-C | 全4视频 / 3物理组的消融、RESERVED增量与相关性差异\nG01两视频不当作独立病例；无GT，无面片删除；少冲突或高支持不证明物理准确',fontsize=15);fig.tight_layout(rect=[0,.07,1,.95]);finish(fig,'Fig4_multiview_multigroup_ablation.png','All4 videos, V0-V3, constant cohort stage changes, normalized response and unverified strata',IDS)
def main():
    allow_manifest();freeze('BEFORE_CORE_FIGURES.json');figure1();figure2();figure3();figure4();save('provenance/FIGURE_PROVENANCE.json',FIGS)
if __name__=='__main__':main()
