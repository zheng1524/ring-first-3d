"""User-authorized wide-angle supplement; same Panel2/full-scene implementation.

Freeze pairs by camera angle BEFORE SIFT or new projection metrics. No original
experiment overwritten, no cross-video pairing, pose changes or learned depth.
"""
from common import *
import reuse_panel2_sift as panel
from experiment_a import infer,render,metrics
from PIL import ImageDraw,ImageFont
import html
W=R/'visualization_large_angle';W.mkdir(exist_ok=True)
GROW=Path('/home/liu/ring_first_3d_boundary_growth/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001')
INC=Path('/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001')
old_layers=panel.layers
def angle(a,b):return float(np.degrees(np.arccos(np.clip(a@b/(np.linalg.norm(a)*np.linalg.norm(b)),-1,1))))
def background(cid):
    for parent in [INC,GROW,PART]:
        p=parent/'local_results/background'/(cid+'.npz')
        if p.exists():return p
    raise FileNotFoundError('No original frozen background '+cid)
@lru_cache(None)
def layers(cid):
    if any(x['A']==cid for x in panel.BASE_ROWS):return old_layers(cid)
    s=source(cid);o=original(cid);p=background(cid);z=np.load(p);ids=np.flatnonzero(z['display']);bu=z['source_uv'][ids];uv=o['uv'];P=o['P']
    a=dict(Polyp_XYZ_mm=P,Polyp_source_uv=uv,Polyp_RGB=s['RGB'][uv[:,1],uv[:,0]]/255.,Polyp_original_ids=np.arange(len(P)),Background_XYZ_mm=z['XYZ_mm'][ids],Background_RGB=z['RGB'][ids],Background_source_uv=bu,Background_original_cache_ids=ids,K=s['K'],c2w=s['T'])
    panel.check(cid+': original background display mask reused',np.array_equal(a['Background_RGB'],s['RGB'][bu[:,1],bu[:,0]]/255.)and np.all(s['labels'][bu[:,1],bu[:,0]]==0))
    return a,ringmesh(CC[cid]['scene_id']),Path(CC[cid]['Ring_CAD']['path'])
def data(cid):
    a,ring,rp=layers(cid)
    return dict(c=CC[cid],P=a['Polyp_XYZ_mm'],C=a['Polyp_RGB'],B=a['Background_XYZ_mm'],BC=a['Background_RGB'],uv=a['Polyp_source_uv'],BU=a['Background_source_uv'],B_ids=a['Background_original_cache_ids'],p=dict(K=a['K'],pose=a['c2w']),ring=ring)
def freeze():
    target=R/'config/LARGE_ANGLE_PAIRS_FROZEN.json'
    if target.exists():return load(target)
    candidates=[]
    for scene in ['G01_004','G06_004','G08_005']:
        ids=sorted([cid for cid,c in CC.items()if c['scene_id']==scene and GATE[cid]['admission']=='CONDITIONAL_RESEARCH_INPUT'])
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                A,B=source(a)['T'],source(b)['T'];candidates.append(dict(scene=scene,A=a,B=b,optical_axis_deg=angle(A[:3,2],B[:3,2]),Ring_center_bearing_deg=angle(A[:3,3],B[:3,3]),baseline_mm=float(np.linalg.norm(A[:3,3]-B[:3,3]))))
    selected=[]
    for scene in ['G01_004','G06_004','G08_005']:
        ranked=sorted([c for c in candidates if c['scene']==scene],key=lambda x:(-x['optical_axis_deg'],x['A'],x['B']))
        for x in ranked[:2 if scene=='G01_004'else 1]:
            x=dict(x)
            # Direction chosen deterministically: larger frozen reference index is A.
            if CC[x['A']]['reference_index']<CC[x['B']]['reference_index']:x['A'],x['B']=x['B'],x['A']
            selected.append(x)
    files=[]
    for x in selected:
        for cid in [x['A'],x['B']]:
            for k in ['RGB','Mask','pack','source_points','mesh','camera_file']:files.append(Path(CC[cid][k]))
        files +=[background(x['A']),Path(CC[x['A']]['Ring_CAD']['path'])]
    obj=dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='USER_REQUEST_WIDE_ANGLE_SUPPLEMENT; old frozen A/B results retained',selection='Maximum optical-axis angle among current conditionally admitted same-video HERO cameras; G01 top2, G06/G08 top1; no matching/coverage/RGB selection. A is larger reference index.',candidates=candidates,pairs=selected,inputs=[asset(p)for p in sorted(set(files))],code=asset(Path(__file__)),SIFT_rules='unchanged experiment_a.infer; no threshold search; failed estimates retained; no RF pose fallback',view_angle_definitions='optical angle=acos(RA[:,2] dot RB[:,2]); Ring bearing angle=acos(CA dot CB/(norm(CA)norm(CB))), Ring center fixed at world origin')
    save('config/LARGE_ANGLE_PAIRS_FROZEN.json',obj);return obj
def failure_image(size,status):
    im=Image.new('RGB',size,'#eeeeee');d=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',28)
    d.multiline_text((30,50),'SIFT未能恢复足够支持的位姿\n'+status+'\n保留失败；不以Ring-First填充',font=font,fill='black',spacing=12);return np.asarray(im)
def main():
    pr=freeze();panel.V=W;panel.layers=layers;ns=panel.namespace();panel.NS=ns
    frozen=[R/'metrics/A_POSES.json',R/'metrics/A_REPROJECTION.json',R/'metrics/B_SVD_RESULTS.json',R/'config/PROTOCOL.json']
    before={str(p):sha(p)for p in frozen};rows=[];poses=[];display=[];public=R/'figures/large_angle';public.mkdir(exist_ok=True)
    for spec in pr['pairs']:
        a,b=spec['A'],spec['B'];sa,sb=source(a),source(b);d=data(a);pose,Tb=infer(a,b);poses.append(pose);pose_for_plot=dict(pose)
        pose_for_plot.setdefault('rotation_difference_deg',float('nan'));pose_for_plot.setdefault('translation_direction_difference_deg',float('nan'))
        out=R/'local_results/large_angle'/(a+'__'+b);out.mkdir(parents=True,exist_ok=True)
        geometry,dep,cad,drawn=ns['panel2_image'](a);gray,_=ns['scene_image'](d,sa['K'],sa['T'],neutral=True)
        full_rf,rfinfo=ns['scene_image'](d,sb['K'],sb['T']);rf=ns['point_projection'](d,sb['K'],sb['T'])
        if Tb is not None:
            full_sf,sfinfo=ns['scene_image'](d,sb['K'],Tb);sf=ns['point_projection'](d,sb['K'],Tb)
            panel.check(a+': same all points and display sizes in both arms',rfinfo['Polyp_points']==sfinfo['Polyp_points']and rfinfo['Background_points']==sfinfo['Background_points']and rfinfo['shared_point_size']==sfinfo['shared_point_size']==.8)
        else:
            full_sf=failure_image((1280,720),pose['SIFT_S0_status']);sf={k:v.copy()for k,v in rf.items()};sf['layer'][:]=-1;sf['RGBA'][:]=0
        # Original scientific triangle metric definition reused on these NEW pairs.
        P,F,C,keep=archived_mesh(a,'Raw');trf=render(P,F,C,sb['K'],sb['T'],np.eye(4),CC[a]['scene_id']);tsf=render(P,F,C,sb['K'],Tb,np.eye(4),CC[a]['scene_id'])if Tb is not None else None
        common=trf['valid']&(sb['labels']==1)&(tsf['valid']if tsf is not None else False)
        trio=[]
        for name,pred in [('Ring-First',trf),('SIFT + RF-scale',tsf)]:
            m=dict(**spec,method=name,geometry='Raw original HERO triangles',SIFT_status=pose['SIFT_S0_status'],status='RETURNED'if pred is not None else'NOT_EVALUABLE_SIFT_FAILED')
            if pred is not None:m.update(metrics(pred,sb['RGB'],sb['labels'],common));np.savez_compressed(out/('triangle_'+('RF'if name=='Ring-First'else'SIFT')+'.npz'),**pred)
            rows.append(m);trio.append(m)
        m=trio[0];old=dict(common_pixels=int((trf['valid']&(sb['labels']==1)).sum()),target_Polyp_pixels=m['target_polyp_N'],target_coverage=m['coverage'],RGB_MAE_0_255=m['own_valid_RGB']['MAE'])
        new,diff,roi=ns['scene_metrics'](rf,sb['RGB'],sb['labels'])
        row=dict(A=a,B=CC[b]['reference'],group=CC[a]['group'],B_target=dict(Mask=CC[b]['Mask']),pose_status=GATE[a]['qualification'],optical_axis_angle_deg=spec['optical_axis_deg'],baseline_mm=spec['baseline_mm'],pair_id=a+'__'+b,B_camera_in_A=sb['T'])
        ns['figure_pair'](row,d,sa['RGB'],sb['RGB'],gray,full_rf,new,old,rf,diff,roi,out)
        base=np.asarray(Image.open(out/'Five_Panels.png').convert('RGBA'));base,rect=panel.patch_panel2(ns,base,geometry,dep)
        Image.fromarray(base).save(out/'Five_Panels_depth_color.png')
        im,dm=panel.append_comparison(Image.fromarray(base),full_rf,full_sf,rf,sf,sb['RGB'],sb['labels'],pose_for_plot,dep,a,b)
        # A separate header distinguishes optical orientation from camera orbit; no number relabeling.
        header=Image.new('RGBA',(im.width,85),'white');dr=ImageDraw.Draw(header);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',25)
        dr.text((25,5),f"大视角补充｜光轴夹角 {spec['optical_axis_deg']:.2f}°；绕Ring中心观察方向差 {spec['Ring_center_bearing_deg']:.2f}°；基线 {spec['baseline_mm']:.2f}mm",font=font,fill='black')
        dr.text((25,42),'按冻结相机角度选取，非按重建效果筛选；同视频、无跨视频配准；'+pose['SIFT_S0_status'],font=font,fill='black')
        result=Image.new('RGBA',(im.width,im.height+85),'white');result.paste(header,(0,0));result.paste(im,(0,85));dest=public/(a+'__'+CC[b]['reference']+'_Wide_Panel2_SIFT.png');result.save(dest)
        display.append(dict(**spec,figure=str(dest.relative_to(R)),SIFT_status=pose['SIFT_S0_status'],source_points=len(d['P']),background_points=len(d['B']),display_only_metrics=dm))
        print('WIDE',a,'->',b,'optical',round(spec['optical_axis_deg'],2),'orbit',round(spec['Ring_center_bearing_deg'],2),pose['SIFT_S0_status'],flush=True)
    for path,digest in before.items():panel.check('old scientific output unchanged '+path,sha(path)==digest)
    for obj in pr['inputs']:panel.check('original wide-angle input unchanged '+obj['path'],sha(obj['path'])==obj['sha256'])
    save('metrics/LARGE_ANGLE_POSES.json',poses);save('metrics/LARGE_ANGLE_RESULTS.json',rows);save('metrics/LARGE_ANGLE_DISPLAY.json',dict(figures=display,checks=panel.checks,passed=all(x['passed']for x in panel.checks),original_metrics_before=before,old_images_retained=True))
    keys=list(dict.fromkeys(k for x in rows for k in x));table('metrics/LARGE_ANGLE_RESULTS.csv',[{k:x.get(k)for k in keys}for x in rows])
    parts=['<!doctype html><meta charset="utf-8"><title>大视角 Panel2 + SIFT</title><style>body{font:16px sans-serif;max-width:1400px;margin:auto}img{width:100%}</style><h1>大视角 A→B，原Panel2方法 + SIFT</h1><p>选择只依据冻结同视频相机的光轴夹角；另列绕Ring中心的观察方向差。G08最大可用光轴差15.1°，不冒称达到30°。旧帧对和指标保留。</p><p><a href="../METRICS_EXPLAINED.md">覆盖率与轮廓误差说明</a></p>']
    for x in display:
        href='../'+x['figure'];parts.append(f'<h2>{html.escape(x["A"]+" → "+CC[x["B"]]["reference"])}；光轴{x["optical_axis_deg"]:.2f}° / 观察方向{x["Ring_center_bearing_deg"]:.2f}°</h2><a href="{href}"><img src="{href}"></a>')
    (W/'index.html').write_text('\n'.join(parts));print('WIDE_COMPLETE',len(display),'checks',len(panel.checks),flush=True)
if __name__=='__main__':main()
