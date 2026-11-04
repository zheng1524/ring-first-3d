"""Reuse PANEL2-003 scripts and original full-scene layers, append SIFT panels.

Original scientific predictions/metrics and historical PNGs remain untouched.
Only disposable task-local images/projection caches are generated.
"""
from common import *
import colorsys,html,shutil
from PIL import ImageDraw,ImageFont
import matplotlib.transforms as transforms
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene

PANEL=Path('/home/liu/ring_first_3d_panel2_depth/experiments/TASK-AB-SCENE-PANEL2-DEPTH-COLOR-003')
BASE=Path('/home/liu/ring_first_3d_ab_scene/experiments/TASK-AB-FULL-SCENE-VIS-002')
V=R/'visualization_panel2_sift';V.mkdir(exist_ok=True)
plt=vis.configure()
BASE_ROWS=load(BASE/'metrics/results.json')
checks=[]

def check(name,passed,**extra):
    checks.append(dict(name=name,passed=bool(passed),**extra));assert passed,name

@lru_cache(None)
def layers(cid):
    rec=next(x for x in BASE_ROWS if x['A']==cid);a=dict(np.load(rec['source_geometry_path']));cad=ringmesh(CC[cid]['scene_id']);rp=Path(CC[cid]['Ring_CAD']['path'])
    check(cid+': same original Raw Polyp XYZ',np.array_equal(a['Polyp_XYZ_mm'],original(cid)['P']))
    check(cid+': same source K/c2w',np.array_equal(a['K'],source(cid)['K'])and np.array_equal(a['c2w'],source(cid)['T']))
    rgb=source(cid)['RGB'];pu=a['Polyp_source_uv'];bu=a['Background_source_uv']
    check(cid+': both layers colored only by A',np.array_equal(a['Polyp_RGB'],rgb[pu[:,1],pu[:,0]]/255.)and np.array_equal(a['Background_RGB'],rgb[bu[:,1],bu[:,0]]/255.))
    return a,cad,rp

def data(cid):
    a,cad,rp=layers(cid);p=dict(K=a['K'],pose=a['c2w']);rec=next(x for x in BASE_ROWS if x['A']==cid)
    return dict(c=CC[cid],P=a['Polyp_XYZ_mm'],C=a['Polyp_RGB'],B=a['Background_XYZ_mm'],BC=a['Background_RGB'],uv=a['Polyp_source_uv'],BU=a['Background_source_uv'],B_ids=a['Background_original_cache_ids'],p=p,ring=cad),rec

def namespace():
    for name,parent in [('config.json',BASE),('display_config.json',BASE),('color_config.json',PANEL)]:
        dest=V/name
        if not dest.exists():shutil.copy2(parent/name,dest)
        check('exact historical display config '+name,sha(dest)==sha(parent/name))
    ns=dict(globals(),R=V,PREV=BASE,layers=layers)
    extract(BASE/'code/scene_renderer.py',['camera_scene','scene_image','point_projection','background_eval_roi','scene_metrics','side_plot'],ns)
    extract(BASE/'code/render_cases.py',['fmt','figure_pair'],ns)
    extract(PANEL/'code/scene_renderer.py',['depth_colors','panel2_image'],ns)
    extract(PANEL/'code/render_cases.py',['panel_canvas'],ns)
    return ns

def patch_panel2(ns,base_image,depth_image,depth):
    # Exact original PANEL2-003 canvas/rectangle routine; all other pixels copied.
    canvas,rect,_=ns['panel_canvas'](depth_image,depth);new=base_image.copy();x0,y0,x1,y1=rect
    check('legacy five-panel canvas shape unchanged',new.shape==canvas.shape)
    new[y0:y1,x0:x1]=canvas[y0:y1,x0:x1];outside=np.ones(new.shape[:2],bool);outside[y0:y1,x0:x1]=False
    check('five-panel pixels outside Panel2 copied exactly',np.array_equal(new[outside],base_image[outside]))
    return new,rect

def rgb_error(pred,B):return abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2)

def append_comparison(base,full_rf,full_sift,rf,sf,B,mask,pose,depth,cid,bid):
    """The old full five-panel PNG is copied byte-for-byte above the new strip."""
    width,height=base.size;dpi=180
    fig=plt.figure(figsize=(16,8.2),dpi=dpi)
    gs=fig.add_gridspec(2,4,height_ratios=[1,.8],wspace=.12,hspace=.25)
    # Same physical pixel size/aspect and point renderer for both pose views.
    for j,(im,name)in enumerate([(full_rf,'6a｜Ring-First A→B 完整点云场景'),(full_sift,'6b｜SIFT + RF-scale A→B 完整点云场景')]):
        ax=fig.add_subplot(gs[0,2*j:2*j+2]);ax.imshow(im,interpolation='nearest');ax.set_title(name,fontsize=11);ax.axis('off')
    # Common source layer class and same target region; both actual point-center supports.
    roi,_=NS['background_eval_roi'](mask)
    cp=(rf['layer']==1)&(sf['layer']==1)&(mask==1);cb=(rf['layer']==0)&(sf['layer']==0)&roi;common=cp|cb
    ax=fig.add_subplot(gs[1,0]);small=cv2.resize(full_sift,(640,360),interpolation=cv2.INTER_AREA);valid=sf['layer']>=0;overlay=B/255.;overlay[valid]=.5*overlay[valid]+.5*small[valid]/255.;ax.imshow(overlay);ax.set_title('7a｜SIFT 与真实B 50%叠加',fontsize=9);ax.axis('off')
    for j,(p,label)in enumerate([(rf,'Ring-First'),(sf,'SIFT + RF-scale')]):
        ax=fig.add_subplot(gs[1,j+1]);err=np.where(common,rgb_error(p,B),np.nan);ax.imshow(err,cmap='magma',vmin=0,vmax=80);ax.set_facecolor('#ccc');ax.axis('off');ax.set_title('7'+('b'if j==0 else'c')+'｜'+label+' RGB差异\n相同P/BG共同区；0–80/255',fontsize=9)
    ax=fig.add_subplot(gs[1,3]);panel=np.full((360,640,3),.82);rv=(rf['layer']==1)|(rf['layer']==0);sv=(sf['layer']==1)|(sf['layer']==0)
    panel[rv&sv]=[.15,.7,.35];panel[rv&~sv]=[.9,.2,.2];panel[sv&~rv]=[.2,.45,.95];panel[(rf['layer']==2)|(sf['layer']==2)]=0;ax.imshow(panel);ax.set_title('7d｜共同支持绿，RF独有红\nSIFT独有蓝；非物理正确性标签',fontsize=9);ax.axis('off')
    fig.suptitle('追加SIFT对比｜上方五面板：原PANEL2-003风格；下方两种位姿共用同一Raw HERO、背景XYZ、CAD和点大小',fontsize=11,y=.995)
    note=f"A={cid} → B={CC[bid]['reference']}｜R差异 {pose['rotation_difference_deg']:.3f}° / t方向差异 {pose['translation_direction_difference_deg']:.3f}°（相对RF，非GT）\n当前相机资格 A={GATE[cid]['qualification']}；B={GATE[bid]['qualification']}。SIFT仅借RF平移长度；背景仅DISPLAY_ONLY。\n旧Raw场景显示 / P={depth['Polyp_N']:,}, BG={depth['Background_N']:,}；与Cleaned三角面正式评价分开。所有点、原生ID、相机与已保存指标不变。"
    fig.text(.025,.015,note,fontsize=8);fig.subplots_adjust(left=.025,right=.99,top=.93,bottom=.12);fig.canvas.draw();strip=Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy());plt.close(fig)
    check('new SIFT strip same canvas width',strip.width==width)
    out=Image.new('RGBA',(width,height+strip.height),'white');out.paste(base,(0,0));out.paste(strip,(0,height))
    check('entire old five-panel base preserved in appended image',np.array_equal(np.asarray(out)[:height],np.asarray(base)))
    return out,dict(common_Polyp_pixels=int(cp.sum()),common_BG_pixels=int(cb.sum()),RF_common_RGB_MAE=float(rgb_error(rf,B)[common].mean())if common.any()else None,SIFT_common_RGB_MAE=float(rgb_error(sf,B)[common].mean())if common.any()else None,identity='SUPPLEMENTARY_POINT_SCENE_DISPLAY_PROXY; not original triangle evaluation')

def main():
    global NS
    NS=namespace();codepaths=[PANEL/'code/scene_renderer.py',PANEL/'code/render_cases.py',BASE/'code/scene_renderer.py',BASE/'code/render_cases.py',PANEL/'color_config.json',BASE/'config.json',BASE/'display_config.json']
    codepaths +=[Path('/home/liu/ring_first_3d_panel2_depth/visualization')/name for name in ['real_p0_renderer.py','same_camera_scene.py','pointcloud_audit_renderer.py']]
    existing=load(R/'metrics/A_REPROJECTION.json');poses=load(R/'metrics/A_POSES.json')
    protected=[R/'metrics/A_POSES.json',R/'metrics/A_REPROJECTION.json',R/'metrics/B_SVD_RESULTS.json',R/'config/PROTOCOL.json']
    protected +=[Path(x['path'])for x in load(PANEL/'provenance/INPUTS_FROZEN.json')['files']]
    before={str(p):sha(p)for p in protected}
    sourcefiles=[Path(next(x for x in BASE_ROWS if x['A']==spec['A'])['source_geometry_path'])for spec in protocol()['pairs']]
    save('provenance/PANEL2_SIFT_BEFORE.json',dict(reused_scripts=[asset(p)for p in codepaths],source_layers=[asset(p)for p in sourcefiles],display_only=True,scientific_metrics_before={str(p):before[str(p)]for p in protected[:4]},newcode=asset(Path(__file__))))
    records=[];public=R/'figures/panel2_sift';public.mkdir(exist_ok=True)
    for spec in protocol()['pairs']:
        a,b=spec['A'],spec['B'];sa,sb=source(a),source(b);d,oldrec=data(a);pose=next(x for x in poses if x['A']==a);siftT=np.array(pose['SIFT_B_c2w']);out=R/'local_results/panel2_sift'/(a+'__'+b);out.mkdir(parents=True,exist_ok=True)
        # Reuse PANEL2-003 depth color renderer directly; includes all legacy P+BG min/max.
        geometry,depth,cad,drawn=NS['panel2_image'](a)
        oldcolor=next(x for x in load(PANEL/'audit/panel2_changes.json')if x['A']==a)
        cached=np.asarray(Image.open(PANEL/oldcolor['new_geometry']).convert('RGB'))
        check(a+': old Panel2 image bitwise replay',np.array_equal(geometry,cached))
        gray,ginfo=NS['scene_image'](d,sa['K'],sa['T'],neutral=True)
        full_rf,rfinfo=NS['scene_image'](d,sb['K'],sb['T']);full_sf,sfinfo=NS['scene_image'](d,sb['K'],siftT)
        rf=NS['point_projection'](d,sb['K'],sb['T']);sf=NS['point_projection'](d,sb['K'],siftT)
        check(a+': equal display point counts and sizes',rfinfo['Polyp_points']==sfinfo['Polyp_points']and rfinfo['Background_points']==sfinfo['Background_points']and rfinfo['shared_point_size']==sfinfo['shared_point_size']==.8)
        new,diff,roi=NS['scene_metrics'](rf,sb['RGB'],sb['labels'])
        raw=next(x for x in existing if x['A']==a and x['kind']=='Raw'and x['method']=='Ring-First');cachedtri=np.load(R/'local_results/A'/(a+'__'+b+'_Raw_RF.npz'))
        old=dict(common_pixels=int((cachedtri['valid']&(sb['labels']==1)).sum()),target_Polyp_pixels=raw['target_polyp_N'],target_coverage=raw['coverage'],RGB_MAE_0_255=raw['own_valid_RGB']['MAE'])
        rel=sa['T'][:3,2]@sb['T'][:3,2];angle=float(np.degrees(np.arccos(np.clip(rel,-1,1))))
        row=dict(A=a,B=CC[b]['reference'],group=CC[a]['group'],B_target=dict(Mask=CC[b]['Mask']),pose_status=GATE[a]['qualification'],optical_axis_angle_deg=angle,baseline_mm=float(np.linalg.norm(sa['T'][:3,3]-sb['T'][:3,3])),pair_id=a+'__'+b,B_camera_in_A=sb['T'])
        # Unmodified original five-panel figure function, then its original Panel2 replacement.
        NS['figure_pair'](row,d,sa['RGB'],sb['RGB'],gray,full_rf,new,old,rf,diff,roi,out)
        base=np.asarray(Image.open(out/'Five_Panels.png').convert('RGBA'));base,rect=patch_panel2(NS,base,geometry,depth)
        if a=='G06_004_ref04':
            original=PANEL/'figures/cases/G06_004_ref04__to__key01_raw00229/Five_Panels_depth_color.png'
            # Exact same old A/B pair: reuse the entire historical PNG; append current qualification note.
            base=np.asarray(Image.open(original).convert('RGBA'))
            oldpred=np.load(oldrec['prediction_path'])
            check('G06 old point projection exactly replayed',all(np.array_equal(rf[k],oldpred[k])for k in rf))
            check('G06 old full A->B scene exactly replayed',np.array_equal(full_rf,np.asarray(Image.open(BASE/oldrec['figures']['Full_AtoB_Scene.png']).convert('RGB'))))
        Image.fromarray(base).save(out/'Five_Panels_depth_color.png');Image.fromarray(geometry).save(out/'A_geometry_depth_color.png')
        Image.fromarray(full_sf).save(out/'SIFT_Full_AtoB_Scene.png');np.savez_compressed(out/'RF_point_projection.npz',**rf);np.savez_compressed(out/'SIFT_point_projection.npz',**sf)
        newimage,display_metrics=append_comparison(Image.fromarray(base),full_rf,full_sf,rf,sf,sb['RGB'],sb['labels'],pose,depth,a,b)
        name=a+'__'+CC[b]['reference']+'_Panel2_plus_SIFT.png';dest=public/name;newimage.save(dest)
        records.append(dict(A=a,B=b,new_figure=str(dest.relative_to(R)),base_five_panel=str((out/'Five_Panels_depth_color.png').relative_to(R)),preserved_base_height=base.shape[0],base_depth_range_mm=[depth['min_Z_mm'],depth['max_Z_mm']],Polyp_N=depth['Polyp_N'],Background_N=depth['Background_N'],base_five_panel_pixels_changed=0,source_layers=asset(oldrec['source_geometry_path']),depth=depth,RF=rfinfo,SIFT=sfinfo,display_comparison=display_metrics))
        print('PANEL2_PLUS_SIFT',a,CC[b]['reference'],'P/BG',depth['Polyp_N'],depth['Background_N'],flush=True)
    for p,value in before.items():check('preserved input/output '+p,sha(p)==value)
    save('metrics/PANEL2_SIFT_VISUALIZATION.json',dict(reused_implementation='AST original PANEL2-003 depth_colors/panel2_image/panel_canvas plus AB-FULL-SCENE-002 scene_image/point_projection/figure_pair/side_plot',figures=records,checks=checks,all_checks_passed=all(c['passed']for c in checks),new_scientific_optimization=0,metric_definition_changed=False,old_figures_retained=True))
    index=['<!doctype html><meta charset="utf-8"><title>Panel2 + SIFT</title><style>body{font:16px sans-serif;max-width:1400px;margin:auto}img{width:100%}article{margin:30px 0}</style><h1>复用原Panel2五面板，追加SIFT</h1><p>原Raw HERO+背景场景；相同XYZ/颜色/点大小/CAD。SIFT+RF-scale，GT不可评价。原Cleaned科学指标保持不变。</p>']
    for rec in records:
        href='../'+rec['new_figure'];index.append(f'<article><h2>{html.escape(rec["A"]+" → "+CC[rec["B"]]["reference"])}</h2><a href="{href}"><img src="{href}"></a></article>')
    (V/'index.html').write_text('\n'.join(index))
    print('DONE',len(records),'figures; checks',len(checks),flush=True)

if __name__=='__main__':main()
