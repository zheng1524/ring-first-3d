"""Four review figures using real frozen XYZ/CAD and existing CPU renderers."""
from common import *
from matplotlib.patches import Circle
from matplotlib.collections import PolyCollection

STAMP='CPU CONTRACT TEST / NOT NEW MODEL OUTPUT'
plt=vis.configure()

def solid_view(ax,P,color,rm,bounds,**kw):
    # Layout-only opaque rendering of the existing CAD triangles. The original
    # point renderer is unchanged. This overview is not a source-view z-buffer.
    _,right,up=vis.basis()
    q=np.c_[rm.vertices@right,rm.vertices@up]
    ax.add_collection(PolyCollection(q[rm.faces],facecolor='black',edgecolor='none',zorder=.8))
    return vis.view(ax,P,color,rm,bounds,**kw)

def finish(fig,name):
    fig.text(.5,.006,STAMP+' | fixed Ring-First cameras | GT DENY',ha='center',fontsize=11,color='firebrick')
    fig.savefig(R/'figures'/name,dpi=135,facecolor='white');plt.close(fig)

def image(ax,z,title,cmap='viridis',vmin=None,vmax=None):
    ax.imshow(np.full(np.asarray(z).shape+(3,),.77))
    a=np.ma.masked_invalid(z);im=ax.imshow(a,cmap=cmap,vmin=vmin,vmax=vmax);ax.set_title(title,fontsize=8);ax.axis('off');return im

def main():
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');C={c['id']:c for c in D['references']};gn=legacy_geometry_namespace(D)
    prop=load(R/'provenance/G01_PROPOSED_INPUTS.json')['proposals'];pairs=list(csv.DictReader((R/'metrics/REFERENCE_COVISIBILITY.csv').open()))
    # Figure 1: actual local scene and an explicit parent DAG for every source.
    fig=plt.figure(figsize=(21,24));gs=fig.add_gridspec(6,3,height_ratios=[1,1,1,1,1,.75],hspace=.47,wspace=.25)
    for row,sid in enumerate(['G01_004','G01_005','G06_004','G08_005','G07_004']):
        refs=[c for c in D['references']if c['scene_id']==sid];c=refs[0];P,colors,_,_=gn['points'](c['id']);rm=ring(c['ring'])
        ax=fig.add_subplot(gs[row,0]);solid_view(ax,P,colors,rm,vis.limits([P],rm),title=sid+' | actual Raw XYZ / mm\n'+c['condition'],size=.5);ax.tick_params(labelsize=7)
        ax=fig.add_subplot(gs[row,1],projection='3d');T=np.array([x['c2w_mm']for x in refs]);centers=T[:,:3,3]
        ax.plot_trisurf(*np.asarray(rm.vertices).T,triangles=rm.faces,color='black',linewidth=0,shade=False,alpha=1)
        ax.scatter(*centers.T,c='royalblue',s=15);ax.quiver(*centers.T,*T[:,:3,2].T,length=5,color='royalblue',linewidth=.6)
        ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=f'{len(refs)} real reference cameras\nseparate local Ring frame');ax.tick_params(labelsize=6);ax.title.set_fontsize(9)
        ax=fig.add_subplot(gs[row,2]);ax.axis('off');rgb=sorted({h for x in refs for h in x['source_alias_hashes']});rgbpos={h:y for h,y in zip(rgb,np.linspace(.92,.06,len(rgb)))}
        cy=np.linspace(.92,.06,len(refs))
        for h,y in rgbpos.items():ax.text(.01,y,h[:7],fontsize=6,color='#555555',va='center')
        for x,y in zip(refs,cy):
            ax.text(.30,y,x['id'].replace(sid+'_',''),fontsize=6,va='center',bbox=dict(fc='#dceaff',ec='none',pad=1))
            for h in x['source_alias_hashes']:ax.plot([.15,.29],[rgbpos[h],y],c='#9db4c9',alpha=.5,lw=.4)
            ax.plot([.58,.68],[y,y],c='black',lw=.5);ax.text(.69,y,'Raw → Cleaned',fontsize=6,va='center')
            ax.plot([.88,.97],[y,.48],c='#dd9851',lw=.45)
        ax.text(.97,.5,'F1\nF2\nF3',fontsize=8,color='#994700',va='center')
        ax.set(xlim=(0,1.09),ylim=(0,1),title=f'{len(rgb)} parent RGB hashes → {len(refs)} HERO refs\nshared parents: correlated priors, no new cases');ax.title.set_fontsize(9)
    for j,x in enumerate(load(R/'provenance/PHOTO_QUALIFICATION.json')):
        ax=fig.add_subplot(gs[5,j]);ax.imshow(np.asarray(Image.open(x['RGB']['path'])));ax.axis('off');ax.set_title(x['id']+' | real image; pose UNKNOWN\nMASt3R cached comparisons='+str(len(x['matching_evidence']))+'; NOT metric input',fontsize=10)
    fig.suptitle('Scene & Source DAG | 4 physical groups / 5 video framesystems\n36 refs / 47 HERO RGB identities / 154 HERO input edges; strict holdout = 0',fontsize=15,y=.995)
    finish(fig,'Fig1_scene_source_DAG.png')

    # Figure 2: same physical mm coordinates across old and two fixed proposals.
    qs=load(R/'config/SDF_DOMAIN_CANDIDATES.json')['candidates'];ss=load(R/'metrics/SDF_GATE_STATUS.json')
    rows=list(csv.DictReader((R/'metrics/SDF_RAY_DOMAIN_TESTS.csv').open()))
    fig,axs=plt.subplots(2,3,figsize=(21,13))
    for j,sid in enumerate(['G01_004','G01_005']):
        cid=prop[sid][0];c=C[cid];P,col,_,_=gn['points'](cid);T=np.array(c['c2w_mm']);K=np.array(c['K_raw']);rm=ring(c['ring'])
        old=dict(id='E0_OLD',center_mm=[0,0,0],physical_radius_mm=25.,ROI_center_mm=qs[sid][0]['ROI_center_mm'],ROI_radius_mm=qs[sid][0]['ROI_radius_mm'])
        for k,q in enumerate([old]+qs[sid]):
            ax=axs[j,k];origin=np.array(q['center_mm']);roi=np.array(q['ROI_center_mm'])
            ax.add_patch(Circle((origin[0],origin[2]),q['physical_radius_mm'],fill=False,color='#b9533c',lw=1.5))
            ax.add_patch(Circle((roi[0],roi[2]),q['ROI_radius_mm'],fill=False,color='green',ls='--',lw=1))
            ax.add_collection(PolyCollection(np.asarray(rm.vertices)[:,[0,2]][rm.faces],facecolor='black',edgecolor='none',zorder=.8))
            ax.scatter(P[:,0],P[:,2],c=col,s=.08);ax.scatter(rm.vertices[:,0],rm.vertices[:,2],c='black',s=.3)
            colors={'FOREGROUND':'green','NEAR_BACKGROUND':'royalblue','RING_MASK':'black','IMAGE_CORNERS':'#d89a31'}
            data=[r for r in rows if r['source']==cid and r['domain']==q['id']]
            for kind,color in colors.items():
                rr=[r for r in data if r['ray_class']==kind]
                for r in rr[::max(1,len(rr)//3)][:3]:
                    ray=vis.camera_rays(np.array([[int(r['u']),int(r['v'])]]),K,T)[0];d=ray[3:]/np.linalg.norm(ray[3:]);end=ray[:3]+d*65
                    ax.plot([ray[0],end[0]],[ray[2],end[2]],c=color,lw=.5,alpha=.75)
            ax.scatter(T[0,3],T[2,3],c='blue',marker='^',s=40)
            ax.text(.02,.98,f'XYZ camera radius={np.linalg.norm(T[:3,3]-origin):.2f} mm\nSphere radius={q["physical_radius_mm"]:.2f} mm\nX/Z projection; all 3 axes used in tests',transform=ax.transAxes,va='top',fontsize=7)
            ax.set(xlim=(-90,90),ylim=(-70,110),aspect='equal',xlabel='X mm',ylabel='Z mm',title=sid+' / '+q['id']+'\n'+('EXPECTED_FAIL_E0' if k==0 else 'geometry proposal; full-ray mask STILL INVALID'))
            ax.tick_params(labelsize=7);ax.title.set_fontsize(9)
    fig.suptitle('MonoSDF domain gate | real source rays / physical mm\nred=absorbing sphere; dashed green=visible source ROI; green=FG blue=BG black=Ring gold=corners',fontsize=14)
    fig.text(.5,.055,f"No network execution. Official sampler: BLOCKED_STATIC_ANALYSIS_ONLY. Ray/Z max error {ss['ray_Z_max_error_mm']:.2g} mm.\nFull-ray opacity is forced to 1; predicted saturated BCE {ss['saturated_mask_BCE_expected']:.7f}, E0 recorded {ss['E0_recorded_silhouette_min']:.7f}. STOP_SDF_BRANCH.",ha='center',fontsize=11)
    fig.subplots_adjust(top=.88,bottom=.14,hspace=.32,wspace=.22)
    finish(fig,'Fig2_SDF_domain_gate.png')

    # Figure 3: exactly three real source estimates per video in one frozen view.
    pns=dict(globals(),camera=lambda t:SameCameraScene(ring('R10'),np.array(t['K']),np.array(t['c2w']),(640,360),str(VENDOR)),cfg=lambda:dict(CAD_tolerance_mm=.05))
    projection=extract(GROW/'code/geometry.py',['projection'],pns)['projection']
    fig,axs=plt.subplots(2,6,figsize=(25,9));hero_stats=[]
    for j,sid in enumerate(['G01_004','G01_005']):
        ids=prop[sid];c=C[ids[0]];target=dict(K=c['K_raw'],c2w=c['c2w_mm']);native=np.load(c['pack'])['depth_mm'];label=np.load(c['pack'])['labels'];layers=[]
        for k,cid in enumerate(ids):
            P,col,F,uv=gn['points'](cid);out=projection(P,col,target);layers.append(out)
            im=image(axs[j,k],np.where(out['source_id']>=0,out['z'],np.nan),sid+' '+cid.replace(sid+'_','')+' → '+ids[0].replace(sid+'_','')+'\nRaw axial Z / mm',vmin=15,vmax=55)
            fig.colorbar(im,ax=axs[j,k],shrink=.5,fraction=.035,pad=.01)
        a,b=layers[0],layers[1];v=(a['source_id']>=0)&(b['source_id']>=0);dz=np.full((360,640),np.nan);dz[v]=abs(a['z'][v]-b['z'][v]);tau=np.maximum(.5,3*a['z']/min(target['K'][0][0],target['K'][1][1]));conflict=v&(dz>tau)
        display=np.full((360,640,3),.77);display[v]=[.15,.7,.3];display[conflict]=[1,.1,.15];display[np.isfinite(a['CAD_z'])&~v]=[0,0,0]
        axs[j,3].imshow(display);axs[j,3].axis('off');axs[j,3].set_title(f'red=conflict {int(conflict.sum())}/{int(v.sum())}\ngreen=depth agreement; grey=UNKNOWN',fontsize=8)
        raw=np.load(R/f'local_results/depth_conditions/{sid}_Raw_points.npz');cl=np.load(R/f'local_results/depth_conditions/{sid}_Cleaned_points.npz')
        removed=raw['validity']&~cl['validity'];view=np.full((360,640,3),.77);view[cl['validity']]=[.1,.7,.3];view[removed]=[1,.2,.1]
        axs[j,4].imshow(view);axs[j,4].axis('off');axs[j,4].set_title('Raw → Cleaned source pixels\nred=removed; no hole filling',fontsize=8)
        P,col,_,_=gn['points'](ids[0]);rm=ring('R10');solid_view(axs[j,5],P,col,rm,vis.limits([P],rm),title=sid+' actual XYZ + black CAD / mm',size=.3);axs[j,5].title.set_fontsize(8);axs[j,5].tick_params(labelsize=6)
        folder=R/'local_results/hero_conflicts';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(sid+'.npz'),depth_layers=np.stack([x['z']for x in layers]),source_index_layers=np.stack([x['source_id']for x in layers]),conflict=conflict,common=v,raw_cleaned_removed=removed)
        hero_stats.append(dict(scene=sid,reference_ids=ids,common_unique_pixel_N=int(v.sum()),conflict_N=int(conflict.sum()),threshold='max(0.5mm,3 pixel footprints)',not_GT=True))
    table('metrics/HERO_FIGURE_CONFLICT_COUNTS.csv',hero_stats)
    fig.suptitle('HERO geometry & conflicts | 3 real references per video; all source layers retained\nHERO is estimated depth. Agreement is conditional support, not true surface certification. Ring-occluded/unknown remain distinct.',fontsize=14)
    fig.subplots_adjust(top=.82,bottom=.10,hspace=.35,wspace=.20);finish(fig,'Fig3_HERO_geometry_conflicts.png')

    # Figure 4: each family has axial depth and original source-index panels.
    fig=plt.figure(figsize=(23,23));gs=fig.add_gridspec(5,5,height_ratios=[1,1,1,1,1.1],hspace=.36,wspace=.13)
    for j,sid in enumerate(['G01_004','G01_005']):
        for k,kind in enumerate(['Raw','Cleaned','F1','F2','F3']):
            z=np.load(R/f'local_results/depth_conditions/{sid}_{kind}_triangles.npz');valid=z['validity'];ax=fig.add_subplot(gs[j*2,k]);im=image(ax,z['axial_Z_mm'],sid+' '+kind+' / axial Z mm\n'+str(int(valid.sum()))+'/230400 valid',vmin=15,vmax=55)
            c=C[prop[sid][0]];sc=SameCameraScene(ring('R10'),np.array(c['K_raw']),np.array(c['c2w_mm']),(640,360),str(VENDOR));opaque=sc.ring_image();opaque[valid,3]=0;ax.imshow(opaque)
            fig.colorbar(im,ax=ax,shrink=.45,fraction=.04,pad=.01)
            ax=fig.add_subplot(gs[j*2+1,k]);ids=z['source_original_point_or_triangle_id'].astype(float);ids[~valid]=np.nan
            image(ax,ids,kind+' original triangle IDs + parent refs\ngrey=UNKNOWN; no inferred fill',cmap='turbo')
            ax.contour(z['ring_occluded'],levels=[.5],colors=['black'],linewidths=.4)
    old=list(csv.DictReader((R/'metrics/E0_M3_FAILURE_RECHECK.csv').open()))
    for j,row in enumerate(old):
        src=load(E0/'config/map_minimal.json')['input_ids'][j];data=np.load(E0/f'local_results/map/M3/view{j}_official_outputs.npz');gauge=np.load(E0/'local_results/map/M3/surface.npz')['evaluation_gauge_to_frozen_first_camera'];P=data['pts3d'][0].reshape(-1,3);P=(P@gauge[:3,:3].T+gauge[:3,3])*1000
        v=np.isfinite(P).all(1)&(data['mask'][0,...,0].reshape(-1)>.5)&np.isin(data['source_Mask'].reshape(-1),[1,2]);rm=ring('R10');ax=fig.add_subplot(gs[4,j*2:j*2+2]);colors=data['img_no_norm'][0].reshape(-1,3)[v]
        solid_view(ax,P[v],colors,rm,vis.limits([P[v]],rm),title='E0 M3 OLD FAILURE / NOT NEW RUN\n'+src+'; XYZ and fixed black CAD / mm',size=.3);ax.title.set_fontsize(9);ax.tick_params(labelsize=6)
    ax=fig.add_subplot(gs[4,4]);ax.axis('off');text='Official depth utility: zero = missing\nNaN rejected; extra valid key rejected\nSource K/c2w unchanged\nOne prior per real RGB view\nF1/F2/F3 share source ancestors\n\nE0 M3 frozen cache:'
    for row in old:
        st=json.loads(row['CAD_distance_mm']);text+=f"\nN={row['Ring_output_valid_N']}/{row['Ring_input_pixel_N']} Ring pixels\nCAD median={st['median']:.2f} mm\np95={st['p95']:.2f} mm\npose Δt={float(row['pose_translation_residual_mm']):.3g} mm"
    ax.text(0,.98,text,va='top',fontsize=9)
    fig.suptitle('Map legal geometry adapter | existing XYZ / open triangles → frozen source-view depth_z\nTop 4 rows are CPU conversions. Bottom row is OLD E0 M3 failure cache. No new model output.',fontsize=15,y=.99)
    finish(fig,'Fig4_Map_legal_geometry_adapter.png')
    save('provenance/FIGURE_SOURCES.json',dict(stamp=STAMP,renderer=asset(REPO/'visualization/real_p0_renderer.py'),
        SameCameraScene=asset(REPO/'visualization/same_camera_scene.py'),
        figures=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],
        scientific_success='NOT_EVALUATED',no_GT=True,real_source_geometry=True))
    html='''<!doctype html><meta charset="utf-8"><title>E1 C0+C1 CPU audit</title><style>body{max-width:1450px;margin:auto;padding:24px;font:17px sans-serif;background:#f3f5f7;color:#17232d}img{width:100%;background:white}article{margin:32px 0;padding:20px;background:white}a{color:#1261a0}.tag{color:#ad2c23;font-weight:bold}</style><h1>E1 来源恢复与 CPU 合同测试</h1><p class="tag">CPU CONTRACT TEST / NOT NEW MODEL OUTPUT · MODEL_RUN_N=0</p><p>C0_LIMITED · OpenCV/CAD CPU gate · SDF ADAPTER_INVALID / STOP_SDF_BRANCH · Map derived-depth contract gate</p><p><a href="../TECHNICAL_REPORT.md">完整技术报告</a> · <a href="../RESULT_INDEX.md">结果索引</a> · <a href="../FAILURE_LEDGER.md">失败台账</a> · <a href="../REPRODUCE.md">CPU 复现</a></p>'''
    for title,p in zip(['来源、局部坐标与父系 DAG','SDF 域、射线及旧失败拦截','多参考 HERO 深度冲突','Map 合法几何适配与旧 M3 故障'],sorted((R/'figures').glob('Fig*.png'))):
        html+=f'<article><h2>{title}</h2><a href="../figures/{p.name}"><img src="../figures/{p.name}"></a></article>'
    (R/'visualizations/index.html').write_text(html)
    print('FOUR_FIGURES_COMPLETE',flush=True)

if __name__=='__main__':main()
