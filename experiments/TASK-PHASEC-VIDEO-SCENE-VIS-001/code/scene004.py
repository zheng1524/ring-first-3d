"""Only G01 video004: fixed camera, shared RGB point rendering, four samples."""
import os,sys,json,hashlib,argparse,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/matplotlib'))
sys.path.insert(0,str(REPO))
import numpy as np,cv2,trimesh
from PIL import Image,ImageDraw,ImageFont
from visualization import real_p0_renderer as base
from visualization.same_camera_scene import SameCameraScene

def firewall():
    def guard(event,args):
        if event!='open'or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve();s=str(p);name=p.name.lower()
        if name.endswith('.blend')or name.startswith('gt_')or 'oracle'in name or '/gt_mapping/'in s or '/private_gt/'in s or '/evaluation_exports/'in s:raise PermissionError('GT not used '+s)
        flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
        if s.startswith(('/home/liu/polyp_research/','/home/liu/new-polyp-dxy/','/home/liu/ring_first_3d/'))and(any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):raise PermissionError('Protected assets '+s)
    sys.addaudithook(guard)
firewall()
def load(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.integer,np.bool_)):return x.item()
    if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
    return x
def save(p,x):Path(p).write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def unproject(uv,z,K,pose):return (np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T*z[:,None])@pose[:3,:3].T+pose[:3,3]
def diagnose_previous():
    previous=R/'local_scenes/G01_004/Background_from_frozen_depth_FULL.npz'
    if not previous.exists():return
    a=np.load(previous);P=a['XYZ_mm'];near=a['distance_to_Polyp_pixels']<=45;radial=np.linalg.norm(P[:,:2],axis=1)<=9.2;z=(P[:,2]>=-6)&(P[:,2]<=2)
    save(R/'metrics/BACKGROUND_DIAGNOSIS.json',dict(previous_reference='004_ref08/raw676',available_background_points=len(P),source_neighborhood_points=int(near.sum()),after_previous_world_z_radial_crop=int((near&radial&z).sum()),source_neighborhood_world_Z_percentiles_mm=np.percentile(P[near,2],[1,25,50,75,99]),cause='background existed; inappropriate Ring-world Z/radial display crop removed it; old point size/alpha differed',new_rule='same frame label=0 and source Polyp distance<=45px; no world clipping; shared point interface'))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path);parser.add_argument('--no-publish',action='store_true');args=parser.parse_args()
    cfg=load(R/'config.json');assert cfg['scope']=='G01_VIDEO004_ONLY_WAIT_FOR_HUMAN_REVIEW'
    c=load(R/'provenance/SELECTED004.json');assert c['id']==cfg['selected_reference']and c['group']=='G01'and c['video']=='004'
    out=args.output_root or R/'local_scenes/G01_004_same_camera_ref03';out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise FileExistsError('Use a new output directory; preserve earlier assets: '+str(out))
    ledger_path=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/independent_confidence_fusion_v1/inputs/datasets.json');item=next(x for x in load(ledger_path)['004']['ledger']if x['raw_frame']==c['raw_frame']);video=Path(item['source_video']);ring_path=Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj')
    files=[Path(c[k])for k in ['source_points','pack','mesh','RGB','Mask','camera_file']]+[video,ring_path,ledger_path];records=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)for p in files]
    original_hash={x['path']:x['sha256']for x in load(R/'provenance/INPUT004.json')['files']}
    assert all(original_hash[str(p)]==sha(p)for p in files)
    pack=dict(np.load(c['pack']));a=np.load(c['source_points']);P=a['points_mm'];uv=a['uv'].astype(int);assert len(P)==c['points'];assert np.array_equal(pack['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']])
    assert np.array_equal(pack['labels'],cv2.imread(c['Mask'],0));assert np.allclose(P,unproject(uv,pack['depth_mm'][uv[:,1],uv[:,0]],pack['K'],pack['pose']),atol=1e-8,rtol=0)
    cap=cv2.VideoCapture(str(video));cap.set(cv2.CAP_PROP_POS_FRAMES,c['raw_frame']);ok,native=cap.read();cap.release();assert ok
    frame=cv2.cvtColor(native,cv2.COLOR_BGR2RGB);h,w=frame.shape[:2];small=np.asarray(Image.open(c['RGB']).convert('RGB'));sh,sw=small.shape[:2];difference=np.abs(cv2.resize(frame,(sw,sh),interpolation=cv2.INTER_AREA).astype(float)-small).mean();assert difference<1.,('source frame mismatch',difference)
    Image.fromarray(frame).save(out/'Selected_Real_Frame.png')
    nativeK=base.scaled_intrinsics(pack['K'],(sw,sh),(w,h));rgb=small[uv[:,1],uv[:,0]]/255.
    v,u=np.nonzero((pack['labels']==0)&np.isfinite(pack['depth_mm'])&(pack['depth_mm']>0));buv=np.c_[u,v]
    prior_cache=R/'local_scenes/G01_004_same_camera_ref03/Background_FULL_DISPLAY_ONLY.npz'
    if prior_cache.exists():
        cached=dict(np.load(prior_cache));assert np.array_equal(cached['source_u'],u)and np.array_equal(cached['source_v'],v);B=cached['XYZ_mm'];brgb=cached['rgb'];assert np.array_equal(brgb,small[v,u]/255.)
    else:B=unproject(buv,pack['depth_mm'][v,u],pack['K'],pack['pose']);brgb=small[v,u]/255.
    distance=cv2.distanceTransform((pack['labels']!=1).astype(np.uint8),cv2.DIST_L2,5)[v,u];bg=distance<=cfg['background_distance_to_Polyp_pixels']
    np.savez_compressed(out/'Background_FULL_DISPLAY_ONLY.npz',XYZ_mm=B,rgb=brgb,source_u=u,source_v=v,display_mask=bg,depth_source='frozen HERO unvalidated background, DISPLAY_ONLY',backprojection_count=1)
    mesh=trimesh.load(ring_path,process=False);scene=SameCameraScene(mesh,nativeK,pack['pose'],(w,h),cfg['open3d_vendor']);plt=base.configure();dpi=cfg['DPI'];fig=plt.figure(figsize=(w/dpi,h/dpi),dpi=dpi);ax=fig.add_axes([0,0,1,1]);ring_image,drawn,render_info=scene.draw(ax,P,rgb,B[bg],brgb[bg],point_size=cfg['point_size']);scale=scene.scale_bar(ax);fig.canvas.draw();canvas=np.asarray(fig.canvas.buffer_rgba()).copy();plt.close(fig);Image.fromarray(canvas[:,:,:3]).save(out/'Local_3D_Scene.png')
    # Silhouettes are projection support and CAD first-hit contours only.
    projected,sourceZ=base.project_camera(P,pack['K'],pack['pose']);support=np.zeros((sh,sw),np.uint8);ij=np.rint(projected).astype(int);support[ij[:,1],ij[:,0]]=1;support_native=cv2.resize(support,(w,h),interpolation=cv2.INTER_NEAREST)
    overlay=frame.copy();ring_mask=(ring_image[:,:,3]==1).astype(np.uint8);rc,_=cv2.findContours(ring_mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE);pc,_=cv2.findContours(support_native,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(overlay,rc,-1,(0,220,255),2);cv2.drawContours(overlay,pc,-1,(255,210,0),2)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',18);overlay_image=Image.fromarray(overlay);od=ImageDraw.Draw(overlay_image);od.rectangle((8,8,1020,65),fill='white');od.text((16,10),'青：冻结CAD Ring投影  黄：原P0源像素支持边界',font=font,fill='black');od.text((16,36),'仅作相机/展示对应检查；不是三维精度证明',font=font,fill='black');overlay_image.save(out/'Projection_Overlay.png')
    gap=16;header=78;comparison=Image.new('RGB',(2*w+gap,h+header),'white');comparison.paste(Image.fromarray(frame),(0,header));comparison.paste(Image.fromarray(canvas[:,:,:3]),(w+gap,header));d=ImageDraw.Draw(comparison);font2=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',24);d.text((18,8),'原始真实帧｜G01 video004 / raw303（0-based）',font=font2,fill='black');d.text((w+gap+18,8),'同一冻结K/c2w｜RGB点云 + 黑色实体CAD Ring',font=font2,fill='black');d.text((18,43),'背景为同帧RGB三维点云 DISPLAY_ONLY；无独立旋转、无相机优化、无精度结论。',font=font,fill='black');comparison.save(out/'Real_vs_3D.png')
    native_projected,_=base.project_camera(P,nativeK,pack['pose']);expected=(uv+.5)*np.array([w/sw,h/sh])-.5
    metadata=dict(scope='G01_VIDEO004_ONLY_WAIT_FOR_HUMAN_REVIEW',group='G01',actual_video='004',raw_frame=c['raw_frame'],frame_index_base=0,selected_reference=c['id'],reference_frame=c['reference'],selection='existing more oblique ref03; visual display only, no GT',other_available_references=['004_ref08/raw676','004_ref13/raw1043'],source_video=str(video),source_P0=c['source_points'],source_mesh=c['mesh'],native_image_size=[w,h],source_image_size=[sw,sh],source_K=pack['K'],native_K=nativeK,c2w=pack['pose'],native_K_rule='pixel-center preserving resize only',independent_camera_rotation=False,camera_pose_updated=False,full_P0_points=len(P),P0_points_cropped=0,background_available_points=len(B),background_selected_points=int(bg.sum()),background_mask_label=0,background_polyp_pixel_overlap=int((pack['labels'][v[bg],u[bg]]==1).sum()),background_depth_status='UNVALIDATED_FROZEN_HERO_DISPLAY_ONLY',background_world_clipping=None,background_approximation_used=False,background_backprojection_count=1,point_style=dict(size=.8,alpha=1,linewidths=0,rasterized=True,shared_one_artist=True),render=render_info,Ring_transform_modified=False,scale_bar=scale,source_RGB_frame_storage_difference=float(difference),source_pixel_projection_roundtrip_max_px=float(np.max(np.abs(projected-uv))),native_pixel_center_projection_check_max_px=float(np.max(np.abs(native_projected-expected))),projection_overlay_is_accuracy_evidence=False,GT_used=False,upstream_model_runs=0,original_assets_modified=False,output_files=[x.name for x in sorted(out.glob('*.png'))])
    save(out/'SCENE_METADATA.json',metadata);save(out/'INPUT004.json',dict(files=records,GT_used=False));np.savez_compressed(out/'Point_layers_and_source_ids.npz',P0_XYZ_mm=P,P0_source_u=uv[:,0],P0_source_v=uv[:,1],background_display_XYZ_mm=B[bg],background_source_u=u[bg],background_source_v=v[bg],drawn_mask=drawn,world_unit='mm',c2w=pack['pose'],K_native=nativeK)
    assert all(sha(x['path'])==x['sha256']for x in records)
    if not args.no_publish:
        dest=R/'figures/G01_004_same_camera';dest.mkdir(exist_ok=True)
        for name in metadata['output_files']:shutil.copy2(out/name,dest/name)
        save(R/'metrics/SCENE004.json',metadata);save(R/'provenance/INPUT004.json',dict(files=records,GT_used=False));diagnose_previous()
    print('004_SAMPLE_COMPLETE',len(P),'P0;',int(bg.sum()),'background;',render_info['Background_drawn'],'BG drawn;',len(metadata['output_files']),'PNG; source-camera projection only',flush=True)
if __name__=='__main__':main()
