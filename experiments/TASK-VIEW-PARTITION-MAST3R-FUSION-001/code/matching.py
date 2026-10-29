"""Official MASt3R full/ROI calls and an actual SIFT baseline, no point-map use."""
from geometry import *
import time,traceback,gc
def views():return{v['id']:v for v in load(R/'metrics/view_distribution.json')}
def source_view(cid):
    c=case(cid);return next(v for v in views().values()if v['source_id']==c['group']+'_video'+c['video']and v.get('index')==c['reference_index'])
def plan():
    rows=[];vv=views()
    for q in load(R/'metrics/new_reference_plan.json'):
        b=vv[q['reference_view']];old=[c for c in cases()if c['group']==q['group']and c['video']==q['video']];a=min(old,key=lambda c:angle(np.array(source_view(c['id'])['view_direction']),np.array(b['view_direction'])));rows.append(dict(id=q['group']+'_'+q['video']+'_adjacent_new',group=q['group'],A=source_view(a['id'])['id'],B=b['id'],source_case=a['id'],kind='SAME_VIDEO_ADJACENT',block_A=source_view(a['id'])['block'],block_B=b['block'],target_new_HERO_reference=q['reference_view']))
    for name,cid,bid,kind in [('G01_crossvideo','G01_004_ref08','G01_video005_v005_00459','CROSS_VIDEO'),('G01_photo001','G01_004_ref08','G01_photo_001','PHOTO'),('G01_photo002','G01_005_raw00459','G01_photo_002','PHOTO'),('G01_photo003','G01_005_raw00459','G01_photo_003','PHOTO')]:rows.append(dict(id=name,group='G01',A=source_view(cid)['id'],B=bid,source_case=cid,kind=kind,block_A=source_view(cid)['block'],block_B=vv[bid].get('block','PHOTO_POSE_UNKNOWN')))
    save('provenance/MATCHING_PAIRS_FROZEN.json',dict(pairs=rows,source='Batch A directions/quality/roles and pre-existing physical source links; no RGB error used',config=cfg(),frozen_before_matching=True));return rows
def image(v):return np.asarray(Image.open(v['RGB']).convert('RGB'))
def label(v):return cv2.imread(v['Mask'],0)
def annotate(p,q,confidence,a,b,method):
    N=len(p);pa=np.clip(np.floor(p+.5).astype(int),[0,0],[639,359]);pb=np.clip(np.floor(q+.5).astype(int),[0,0],[639,359]);la,lb=label(a),label(b);ca=la[pa[:,1],pa[:,0]];cb=lb[pb[:,1],pb[:,0]];near=cv2.distanceTransform((la!=1).astype(np.uint8),cv2.DIST_L2,5)[pa[:,1],pa[:,0]]<=cfg()['near_background_pixels'];reg=np.where(ca==1,'Polyp',np.where(ca==2,'Ring',np.where(near,'NearBackground','FarBackground')));inside=(p[:,0]>=0)&(p[:,0]<640)&(p[:,1]>=0)&(p[:,1]<360)&(q[:,0]>=0)&(q[:,0]<640)&(q[:,1]>=0)&(q[:,1]<360);A=image(a);B=image(b);spec=(A[pa[:,1],pa[:,0]].min(1)>=245)|(B[pb[:,1],pb[:,0]].min(1)>=245);usable=inside&(ca==cb)&(ca!=2)&~spec
    if method=='MASt3R_ROI':usable&=reg!='FarBackground'
    held=(np.floor(p[:,0]/16).astype(int)+3*np.floor(q[:,1]/16).astype(int))%5==0;train=usable&~held;F=np.full((3,3),np.nan);inlier=np.zeros(N,bool)
    if train.sum()>=12:
        cv2.setRNGSeed(0);ff,ii=cv2.findFundamentalMat(p[train],q[train],cv2.FM_RANSAC,cfg()['fundamental_RANSAC_px'],.999)
        if ff is not None and ff.shape==(3,3):F=ff;inlier[np.flatnonzero(train)]=ii.ravel()>0
    error=np.full(N,np.nan)
    if np.isfinite(F).all():
        x=np.c_[p,np.ones(N)];y=np.c_[q,np.ones(N)];Fx=x@F.T;Fy=y@F;error=abs((y*Fx).sum(1))/np.sqrt(np.maximum(1e-12,(Fx[:,:2]**2).sum(1)+(Fy[:,:2]**2).sum(1)))
    return dict(p=p,q=q,confidence=confidence,region=reg,category_A=ca,category_B=cb,usable=usable,specular=spec,held=held,train_F_inlier=inlier,F=F,F_error_px=error,geometric_candidate=usable&np.isfinite(error)&(error<=cfg()['fundamental_RANSAC_px']),confidence_is_probability=False)
def sift(a,b):
    sf=cv2.SIFT_create(nfeatures=cfg()['SIFT_features'],contrastThreshold=.01);kp1,d1=sf.detectAndCompute(cv2.cvtColor(image(a),cv2.COLOR_RGB2GRAY),None);kp2,d2=sf.detectAndCompute(cv2.cvtColor(image(b),cv2.COLOR_RGB2GRAY),None)
    if d1 is None or d2 is None or min(len(d1),len(d2))<2:return np.empty((0,2)),np.empty((0,2)),np.empty(0)
    fw=cv2.BFMatcher().knnMatch(d1,d2,k=2);rv=cv2.BFMatcher().knnMatch(d2,d1,k=2);r=cfg()['SIFT_ratio'];back={m.queryIdx:m.trainIdx for m,n in rv if m.distance<r*n.distance};ms=[m for m,n in fw if m.distance<r*n.distance and back.get(m.trainIdx)==m.queryIdx];return np.array([kp1[m.queryIdx].pt for m in ms]).reshape(-1,2),np.array([kp2[m.trainIdx].pt for m in ms]).reshape(-1,2),np.array([1/(1+m.distance)for m in ms])
def inputs(v,roi):
    """Reuse official image loader, record its exact crop affine back to640x360."""
    from dust3r.utils.image import load_images,_resize_pil_image
    im=Image.open(v['RGB']).convert('RGB');x0=y0=0
    if roi:
        y,x=np.nonzero(label(v)==1);pad=cfg()['ROI_padding_pixels'];x0=max(0,int(x.min())-pad);y0=max(0,int(y.min())-pad);x1=min(640,int(x.max())+pad+1);y1=min(360,int(y.max())+pad+1);im=im.crop((x0,y0,x1,y1))
    folder=R/'local_results/matching_inputs';folder.mkdir(parents=True,exist_ok=True);path=folder/(v['id']+('_ROI'if roi else'_FULL')+'.png');im.save(path);w0,h0=im.size;wr,hr=_resize_pil_image(im,cfg()['matching_size']).size;data=load_images([str(path)],size=cfg()['matching_size'],verbose=False)[0];hh,ww=data['true_shape'][0];crop=np.array([wr//2-ww/2,hr//2-hh/2]);scale=np.array([w0/wr,h0/hr]);offset=np.array([x0,y0]);return data,dict(scale=scale,crop_offset_resized=crop,source_crop_offset=offset,source_crop_size=[w0,h0],resized_size=[wr,hr],network_size=[int(ww),int(hh)])
def backmap(p,meta):return(p+meta['crop_offset_resized']+.5)*meta['scale']-.5+meta['source_crop_offset']
def main():
    verify();pairs=plan();vv=views();records=[];folder=R/'local_results/matches';folder.mkdir(parents=True,exist_ok=True)
    # A new SIFT baseline is run on every actual selected pair, not old results.
    for pair in pairs:
        a,b=vv[pair['A']],vv[pair['B']];p,q,c=sift(a,b);d=annotate(p,q,c,a,b,'SIFT');np.savez_compressed(folder/(pair['id']+'_SIFT.npz'),**d);records.append(record(pair,'SIFT',d,'NEW_BASELINE_FORWARD',0));print('SIFT',pair['id'],len(p),flush=True)
    sys.path[:0]=[str(V8/'vendor/dependencies'),str(V8/'vendor/mast3r')];import torch
    from mast3r.model import AsymmetricMASt3R
    from mast3r.fast_nn import fast_reciprocal_NNs
    from dust3r.inference import loss_of_one_batch
    from dust3r.utils.device import collate_with_cat
    torch.set_num_threads(3);torch.manual_seed(0);start=time.monotonic();model=AsymmetricMASt3R.from_pretrained(str(V9/'weights/MASt3R_official.pth')).to('cuda').eval();save('provenance/MASt3R_ENVIRONMENT.json',dict(official_commit='f5209afc300cec36239a7ac992263f36847bbba0',torch=torch.__version__,GPU=torch.cuda.get_device_name(),load_seconds=time.monotonic()-start,official_license='CC BY-NC-SA 4.0; checkpoints notice applies',point_maps_used_in_pose_or_fusion=False))
    for pair in pairs:
        for method,roi in [('MASt3R_FULL',False),('MASt3R_ROI',True)]:
            start=time.monotonic();tag=pair['id']+'_'+method
            try:
                ia,ma=inputs(vv[pair['A']],roi);ib,mb=inputs(vv[pair['B']],roi);ia['idx']=0;ib['idx']=1;torch.cuda.reset_peak_memory_stats()
                with torch.inference_mode():
                    out=loss_of_one_batch(collate_with_cat([(ia,ib)]),model,None,'cuda',use_amp=True);d1=out['pred1']['desc'][0].float();d2=out['pred2']['desc'][0].float();p,q=fast_reciprocal_NNs(d1,d2,subsample_or_initxy1=cfg()['matching_stride'],device='cuda',dist='dot',block_size=cfg()['matching_block_size']);dot=(d1[p[:,1],p[:,0]]*d2[q[:,1],q[:,0]]).sum(-1).cpu().numpy();conf={}
                    for key in ['conf','desc_conf']:
                        if key in out['pred1']:conf[key+'_A']=out['pred1'][key][0,p[:,1],p[:,0]].float().cpu().numpy();conf[key+'_B']=out['pred2'][key][0,q[:,1],q[:,0]].float().cpu().numpy()
                pp=backmap(p,ma);qq=backmap(q,mb);d=annotate(pp,qq,dot,vv[pair['A']],vv[pair['B']],method);np.savez_compressed(folder/(tag+'.npz'),**d,native_p=p,native_q=q,**conf);rec=record(pair,method,d,'NEW_OFFICIAL_FORWARD',time.monotonic()-start);rec['peak_GPU_GB']=torch.cuda.max_memory_allocated()/1e9;rec['input_affine_A']=ma;rec['input_affine_B']=mb;records.append(rec);del out,d1,d2,ia,ib;gc.collect();torch.cuda.empty_cache();print('MAST',tag,len(pp),'PolypCandidates',rec['regions']['Polyp']['geometric_candidate_N'],flush=True)
            except Exception:
                records.append(dict(pair=pair['id'],group=pair['group'],method=method,status='FAILED',failure=traceback.format_exc(),seconds=time.monotonic()-start));print(records[-1]['failure'],flush=True);gc.collect();torch.cuda.empty_cache()
            both('matching_comparison',records)
    save('provenance/MATCHING_OUTPUT_FROZEN.json',stamp(list(folder.glob('*.npz'))+[Path(__file__),R/'metrics/matching_comparison.json'],GT_used=False,neural_point_maps_saved=False));print('MATCHING COMPLETE',len(records),'arms',flush=True)
def record(pair,method,d,origin,seconds):
    regions={}
    for name in ['Polyp','NearBackground','FarBackground','Ring']:
        sel=d['region']==name;good=sel&d['geometric_candidate'];cells=np.unique((d['p'][good]//32).astype(int),axis=0);regions[name]=dict(raw_N=int(sel.sum()),usable_N=int((sel&d['usable']).sum()),geometric_candidate_N=int(good.sum()),train_inlier_N=int((sel&d['train_F_inlier']).sum()),held_geometric_N=int((good&d['held']).sum()),spatial_32px_cells=len(cells),held_epipolar_px=stats(d['F_error_px'][sel&d['held']&d['usable']]))
    return dict(pair=pair['id'],group=pair['group'],A=pair['A'],B=pair['B'],method=method,status='MATCHES_RETURNED_NOT_TRUE_CORRESPONDENCE_LABELS',origin=origin,raw_N=len(d['p']),usable_N=int(d['usable'].sum()),regions=regions,seconds=seconds,physical_accuracy='NOT_EVALUABLE_NO_GT',no_neural_pointmap_geometry=True)
if __name__=='__main__':main()
