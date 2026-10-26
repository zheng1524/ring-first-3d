"""L1-L5 raw-XYZ audit; no coordinate updates, models, fitting or fusion."""
import os,sys,json,csv,hashlib,argparse,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
PREV=REPO/'experiments/TASK-PHASEC-VIDEO-SCENE-VIS-001'
os.environ.setdefault('MPLCONFIGDIR',str(R/'runtime/matplotlib'))
sys.path.insert(0,str(REPO))
import numpy as np,cv2,trimesh
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial import cKDTree
from visualization import real_p0_renderer as base
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene
O=R
def firewall():
    def guard(event,args):
        if event!='open'or not isinstance(args[0],(str,bytes)):return
        p=Path(os.fsdecode(args[0])).resolve();s=str(p);name=p.name.lower()
        if name.endswith('.blend')or name.startswith('gt_')or 'oracle'in name or '/gt_mapping/'in s or '/private_gt/'in s or '/evaluation_exports/'in s:raise PermissionError('GT excluded '+s)
        flags=args[2]if len(args)>2 and isinstance(args[2],int)else 0;mode=args[1]if len(args)>1 and isinstance(args[1],str)else''
        if (s.startswith(('/home/liu/polyp_research/','/home/liu/new-polyp-dxy/','/home/liu/ring_first_3d/'))or p.is_relative_to(PREV))and(any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):raise PermissionError('Read-only previous asset '+s)
    sys.addaudithook(guard)
firewall()
def clean(x):
    if isinstance(x,dict):return {str(k):clean(v)for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v)for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,(np.integer,np.bool_)):return x.item()
    if isinstance(x,(float,np.floating)):return float(x)if np.isfinite(x)else None
    return x
def load(p):return json.loads(Path(p).read_text())
def save(p,x):
    p=O/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csvsave(p,rows):
    p=O/p;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader()
        for row in rows:w.writerow({k:json.dumps(clean(v),ensure_ascii=False)if isinstance(v,(dict,list,tuple,np.ndarray))else clean(v)for k,v in row.items()})
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def config():return load(R/'config.json')
def scenes():return load(R/'provenance/SCENES.json')
def unproject(uv,z,K,pose):return (np.c_[uv,np.ones(len(uv))]@np.linalg.inv(K).T*z[:,None])@pose[:3,:3].T+pose[:3,3]
def ring_path(c):return Path('/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/inputs/R10_ring.obj')if c['ring']=='R10'else Path('/home/liu/polyp_research/ring_anchor_3d/assets/ring_R5.obj')
def raw(c):
    a=np.load(c['source_points']);P=a['points_mm']if'points_mm'in a else a['XYZ_mm'];uv=a['uv']if'uv'in a else a['pixel_uv'];p=dict(np.load(c['pack']));rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));return P,uv.astype(int),p,rgb
def stats(x):
    x=np.asarray(x,float);return dict(n=len(x),min=float(x.min())if len(x)else None,median=float(np.median(x))if len(x)else None,p95=float(np.percentile(x,95))if len(x)else None,max=float(x.max())if len(x)else None)
def annotate_stages(c,stages,conf):
    for stage in stages:
        final=stage['stage']=='L5';stage.update(coordinate_system='unchanged Ring local XYZ / millimeters / independent per video',source_RGB=c['RGB'],point_renderer='visualization.real_p0_renderer.draw_rgb_points',point_size=conf['L5_point_size']if final else conf['diagnostic_point_size'],point_alpha=1.,projection='frozen source K/c2w perspective'if final else'Ring oblique orthographic '+str(conf['layer_oblique_angle_degrees']))
        stage.setdefault('source_XYZ','exact L1 P0 + L2 background concatenation; local_layers/'+c['scene_id']+'/Layers_L1-L4_XYZ_RGB.npz')
    return stages
def prepare():
    paths=set()
    for c in scenes():
        paths.update(Path(c[k])for k in ['source_points','pack','mesh','RGB','Mask','camera_file','source_video','ledger']);paths.add(ring_path(c));P,uv,p,rgb=raw(c)
        assert len(P)==c['points']and np.allclose(P,unproject(uv,p['depth_mm'][uv[:,1],uv[:,0]],p['K'],p['pose']),atol=1e-8,rtol=0)
        assert np.array_equal(p['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']])and np.array_equal(p['labels'],cv2.imread(c['Mask'],0))
    paths.update((PREV/'figures/G01_004_same_camera').glob('*.png'));paths.update([REPO/'visualization/real_p0_renderer.py',REPO/'visualization/same_camera_scene.py',REPO/'visualization/_phasec_c0_view_frozen.py'])
    save('provenance/INPUT_MANIFEST.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(paths)],old_L5_images_preserved=True,GT_used=False))
    csvsave('metrics/source_identity.csv',scenes());print('PREPARED',len(paths),'input/previous-asset files',flush=True)
def verify():
    for x in load(R/'provenance/INPUT_MANIFEST.json')['files']:assert sha(x['path'])==x['sha256'],x['path']

def dataset(c):
    conf=config();P,uv,p,image=raw(c);rgb=image[uv[:,1],uv[:,0]]/255.;lab=p['labels'];v,u=np.nonzero((lab==0)&np.isfinite(p['depth_mm'])&(p['depth_mm']>0));buv=np.c_[u,v];B=unproject(buv,p['depth_mm'][v,u],p['K'],p['pose']);brgb=image[v,u]/255.
    q=np.quantile(uv[:,1],1-conf['background_base_proxy_lower_source_fraction']);base_ids=np.flatnonzero(uv[:,1]>=q);center_uv=np.median(uv[base_ids],axis=0);center_xyz=np.median(P[base_ids],axis=0)
    base_mask=np.zeros(lab.shape,np.uint8);base_mask[uv[base_ids,1],uv[base_ids,0]]=1;distance=cv2.distanceTransform(1-base_mask,cv2.DIST_L2,5)[v,u];witness=distance<=conf['background_contact_witness_pixels']
    pv,pu=np.nonzero(lab==1);rv,ru=np.nonzero(lab==2);reference_radius=max(np.ptp(pu)/2,np.ptp(ru)/2 if len(ru)else 0,1.)
    outer=c['R_mm']+.6;far_limit=conf['background_far_distance_outer_diameters']*2*outer;distance3=np.linalg.norm(B-center_xyz,axis=1);near3=distance3<=far_limit
    selections={};rows=[]
    for scale in conf['background_ellipse_scales']:
        a=scale*reference_radius;b=conf['background_ellipse_y_over_x']*a;ellipse=((u-center_uv[0])/a)**2+((v-center_uv[1])/b)**2<=1
        # Keep every base-adjacent raw prediction even if it exposes a large gap.
        sel=(ellipse&near3)|witness;selections[str(scale)]=sel
        rows.append(dict(scene_id=c['scene_id'],scale=scale,ellipse_center_uv=center_uv,semi_axes_px=[a,b],base_proxy_center_XYZ_mm=center_xyz,base_proxy_points=len(base_ids),far_limit_mm=far_limit,raw_background=len(B),inside_ellipse=int(ellipse.sum()),ellipse_far_excluded=int((ellipse&~near3&~witness).sum()),contact_witnesses=int(witness.sum()),far_contact_witnesses_retained=int((witness&~near3).sum()),selected_points=int(sel.sum()),selected_world_bounds_mm=np.array([B[sel].min(0),B[sel].max(0)]),selection_is_display_only=True))
    chosen=selections[str(conf['background_selected_scale'])];folder=O/'local_layers'/c['scene_id'];folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(folder/'Raw_Background_FULL.npz',XYZ_mm=B,rgb=brgb,source_u=u,source_v=v,witness=witness,base_proxy_pixel_distance=distance,base_proxy_3D_distance_mm=distance3,**{'selection_'+key:sel for key,sel in selections.items()})
    pose=p['pose'];poses=[]
    for name,offset in [('source_reference',0.),('diagnostic_left',-conf['diagnostic_translation_mm']),('diagnostic_right',conf['diagnostic_translation_mm'])]:
        d=pose.copy();d[:3,3]=pose[:3,3]+offset*pose[:3,0];poses.append(dict(name=name,c2w=d,translation_from_source_mm=offset,role='FROZEN_REAL_REFERENCE_CAMERA'if not offset else'DIAGNOSTIC_ONLY_NOT_VIDEO_FRAME'))
    np.savez_compressed(folder/'Layers_L1-L4_XYZ_RGB.npz',P0_XYZ_mm=P,P0_RGB=rgb,P0_source_u=uv[:,0],P0_source_v=uv[:,1],background_XYZ_mm=B[chosen],background_RGB=brgb[chosen],background_source_u=u[chosen],background_source_v=v[chosen],base_proxy_original_P0_indices=base_ids,contact_witness_background_indices=np.flatnonzero(witness[chosen]),source_K=p['K'],source_c2w=pose,diagnostic_left_c2w=poses[1]['c2w'],diagnostic_right_c2w=poses[2]['c2w'],physical_group=c['group'],actual_video=c['video'],reference_frame=c['reference'],coordinate='unchanged Ring local XYZ millimeters',source_image_size=[p['labels'].shape[1],p['labels'].shape[0]],scene_id=c['scene_id'],condition=c['condition'],morphology=c['morphology'],ring=c['ring'])
    save('metrics/'+c['scene_id']+'_background_ranges.json',rows);csvsave('metrics/'+c['scene_id']+'_background_ranges.csv',rows)
    source=folder/'Selected_Real_Frame.png';cap=cv2.VideoCapture(c['source_video'])
    for index in range(c['raw_frame']+1):ok,frame=cap.read();assert ok
    cap.release();native=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);storage_difference=float(np.abs(cv2.resize(native,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_AREA).astype(float)-image).mean());assert storage_difference<1.;Image.fromarray(native).save(source)
    save('metrics/'+c['scene_id']+'_frame_identity.json',dict(scene_id=c['scene_id'],raw_frame=c['raw_frame'],index_base=0,decoder='SEQUENTIAL_ZERO_BASED_MATCHING_HISTORICAL_PREPARATION',source_RGB_SHA256=sha(c['RGB']),native_frame_SHA256=sha(source),resize_storage_MAD=storage_difference,not_geometry_accuracy=True))
    Bsel=B[chosen];contact=B[witness];metrics=dict(scene_id=c['scene_id'],P0_points=len(P),background_raw_points=len(B),background_selected_points=len(Bsel),selected_ellipse_scale=conf['background_selected_scale'],base_proxy_points=len(base_ids),base_proxy_to_background_nn_mm=stats(cKDTree(Bsel).query(P[base_ids],workers=1)[0]),contact_witness_to_base_proxy_nn_mm=stats(cKDTree(P[base_ids]).query(contact,workers=1)[0]),P0_nearest_neighbor_spacing_mm=stats(cKDTree(P).query(P,k=2,workers=1)[0][:,1]),background_nearest_neighbor_spacing_mm=stats(cKDTree(Bsel).query(Bsel,k=2,workers=1)[0][:,1]),contact_witnesses=len(contact),far_contact_witnesses_retained=rows[0]['far_contact_witnesses_retained'],condition=c['condition'],GT_error=None,metric_identity='PREDICTED_LAYER_GEOMETRY_ONLY_NOT_ACCURACY')
    return P,rgb,Bsel,brgb[chosen],p,native,poses,rows,metrics

def build(c):
    conf=config();P,rgb,B,bRGB,p,frame,poses,ranges,metrics=dataset(c);allP=np.r_[P,B];allRGB=np.r_[rgb,bRGB];mesh=trimesh.load(ring_path(c),process=False);scene=SameCameraScene(mesh,p['K'],p['pose'],(p['labels'].shape[1],p['labels'].shape[0]),conf['open3d_vendor']);plt=base.configure();dest=O/'figures'/c['scene_id'];dest.mkdir(parents=True,exist_ok=True);panels=[];oblique=base.basis(conf['layer_oblique_angle_degrees']);bounds=diag.square_bounds([allP,mesh.vertices],[oblique])[0];dmin,dmax=(allP@oblique[0]).min(),(allP@oblique[0]).max()
    # L5 is the only dense/opaque source-camera rendering.
    H,W=frame.shape[:2];nativeK=base.scaled_intrinsics(p['K'],(p['labels'].shape[1],p['labels'].shape[0]),(W,H));real_scene=SameCameraScene(mesh,nativeK,p['pose'],(W,H),conf['open3d_vendor']);dpi=conf['PNG_DPI'];fig=plt.figure(figsize=(W/dpi,H/dpi),dpi=dpi);ax=fig.add_axes([0,0,1,1]);_img,visible,l5info=real_scene.draw(ax,P,rgb,B,bRGB,point_size=conf['L5_point_size']);real_scene.scale_bar(ax);fig.canvas.draw();l5=np.asarray(fig.canvas.buffer_rgba()).copy()[:,:,:3];plt.close(fig);Image.fromarray(l5).save(O/'local_layers'/c['scene_id']/'L5_Local_3D_Scene.png')
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',22);pair=Image.new('RGB',(2*W+16,H+80),'white');pair.paste(Image.fromarray(frame),(0,80));pair.paste(Image.fromarray(l5),(W+16,80));draw=ImageDraw.Draw(pair);draw.text((16,8),c['scene_id']+' '+c['morphology']+'/'+c['ring']+' / raw'+str(c['raw_frame'])+' / '+c['condition'],font=font,fill='black');draw.text((W+32,8),'L5 同一冻结K/c2w真实感展示',font=font,fill='black');draw.text((16,42),'DISPLAY_ONLY；L5不可作为三维准确性证据；原点/科研相机均未修改。',font=font,fill='black');pair.save(dest/'Real_vs_3D.png')
    diagnostics,geometry=diag.figures(P,rgb,B,bRGB,mesh,scene,p['K'],p['pose'],poses,(p['labels'].shape[1],p['labels'].shape[0]),conf,c['scene_id'],c['morphology'],c['ring'],c['condition'],l5_images=(frame,l5))
    for name,figure in diagnostics.items():figure.savefig(dest/name,dpi=dpi,facecolor='white');plt.close(figure)
    stages_meta=[dict(stage='L1',P0_points=len(P),background_points=0,total_points=len(P),source_XYZ=c['source_points']),dict(stage='L2',P0_points=0,background_points=len(B),total_points=len(B),source_XYZ='local_layers/'+c['scene_id']+'/Raw_Background_FULL.npz and selected source indices'),dict(stage='L3',P0_points=len(P),background_points=len(B),total_points=len(allP),source_XYZ='exact concatenation L1+L2'),dict(stage='L4',P0_points=len(P),background_points=len(B),total_points=len(allP),CAD_source=str(ring_path(c)),CAD_vertices=len(mesh.vertices),CAD_faces=len(mesh.faces),CAD_alpha=conf['diagnostic_CAD_alpha']),dict(stage='L5',P0_points=len(P),background_points=len(B),total_input_points=len(allP),visible_points=int(visible.sum()),CAD_alpha=1.,source_camera_unchanged=True)]
    result=dict(scene_id=c['scene_id'],group=c['group'],actual_video=c['video'],reference=c['reference'],raw_frame=c['raw_frame'],morphology=c['morphology'],ring=c['ring'],condition=c['condition'],stages=annotate_stages(c,stages_meta,conf),metrics=metrics,background_ranges=ranges,diagnostic_cameras=poses,source_K=p['K'],source_c2w=p['pose'],**geometry,L5=l5info,config=conf,accuracy_status='NOT_EVALUABLE',GT_used=False)
    save('metrics/'+c['scene_id']+'_audit.json',result);save('local_layers/'+c['scene_id']+'/SOURCE_AND_PARAMETERS.json',result)
    print('BUILT',c['scene_id'],'L1',len(P),'L2',len(B),'gap proxy median',metrics['base_proxy_to_background_nn_mm']['median'],'; four core PNG',flush=True)
    return result

def main():
    global O
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['prepare','build','summarize']);parser.add_argument('--scene');parser.add_argument('--output-root',type=Path);args=parser.parse_args()
    if args.output_root:
        O=args.output_root.resolve()
        if O.exists()and any(O.iterdir()):raise FileExistsError('Use a new output directory')
        O.mkdir(parents=True,exist_ok=True)
    if args.mode=='prepare':prepare();return
    verify()
    if args.mode=='build':
        for c in scenes():
            if args.scene and c['scene_id']!=args.scene:continue
            build(c)
    else:
        rows=[load(O/f'metrics/{c["scene_id"]}_audit.json')for c in scenes()];save('metrics/scene_index.json',rows);csvsave('metrics/scene_summary.csv',[{**x['metrics'],**{k:x[k]for k in ['group','reference','raw_frame','morphology','ring']},'video':x['actual_video']}for x in rows]);csvsave('metrics/stage_counts.csv',[dict(scene_id=x['scene_id'],**stage)for x in rows for stage in x['stages']]);csvsave('metrics/background_ranges.csv',[a for x in rows for a in x['background_ranges']])
    verify()
if __name__=='__main__':main()
