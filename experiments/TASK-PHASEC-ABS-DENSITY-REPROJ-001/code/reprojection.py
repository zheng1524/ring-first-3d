"""A RGB/XYZ to B: point z-buffer, immutable CAD visibility, independent B eval."""
from common import *
def prepare():
    cfg=load(R/'config.json');entries=load(OLD/'pointcloud_surface_filter_vnext/inputs/entries.json');ds=load(ICF/'inputs/datasets.json');pairs=[];files=[];audit=[]
    for c in [x for x in cases()if x['group']=='G01'or x['group']=='G06']:
        a,p,rgb,m=data(c);e=next(e for e in entries if e['group']==c['group']and e['actual_video']==c['video']);ledger=ds[c['video']]['ledger']if c['group']=='G01'else e['ledger'];cam=np.load(c['camera_file']);A=p['pose'];sources=list(map(int,p.get('sources',[])));candidates=[]
        for j,fr in enumerate(ledger):
            if j==c['reference_index']or j in sources or not e['camera_qualified'][j]:continue
            B=cam['c2w'][j];angle=np.degrees(np.arccos(np.clip(np.dot(A[:3,3],B[:3,3])/(np.linalg.norm(A[:3,3])*np.linalg.norm(B[:3,3])),-1,1)));baseline=np.linalg.norm(A[:3,3]-B[:3,3]);ok=cfg['target_view_angle_range_degrees'][0]<=angle<=cfg['target_view_angle_range_degrees'][1]and baseline>=cfg['target_baseline_mm_minimum']
            candidates.append(dict(index=j,frame=fr,angle_deg=float(angle),baseline_mm=float(baseline),eligible=bool(ok)))
        audit.append(dict(A=c['id'],candidates=candidates,HERO_sources_excluded=sources))
        valid=[x for x in candidates if x['eligible']]
        if not valid:pairs.append(dict(A=c['id'],status='NOT_EVALUABLE_NO_QUALIFIED_BASELINE',reason='No qualified non-source B in predeclared angle/baseline interval'));continue
        b=min(valid,key=lambda x:(abs(x['angle_deg']-cfg['target_preferred_angle_degrees']),x['index']));fr=b['frame'];j=b['index'];B=cam['c2w'][j];K=cam['K'];bm=cv2.imread(fr['Mask_path'],0);assert bm is not None and(bm==1).any()and(bm==2).any()
        pairs.append(dict(A=c['id'],group=c['group'],video=c['video'],status='FROZEN_BEFORE_RGB_ERROR',B=fr['id'],B_raw_frame=fr['raw_frame'],B_index=j,B_RGB=fr['RGB_path'],B_Mask=fr['Mask_path'],B_K=K,B_c2w=B,view_angle_deg=b['angle_deg'],baseline_mm=b['baseline_mm'],B_not_A_HERO_input=j not in sources,whole_pipeline_holdout=False,qualification='FROZEN_CAMERA_CONDITIONAL',timeline_risk=ds[c['video']]['timeline_risk']if c['group']=='G01'else False,selection='closest to 12deg among qualified 3-25deg and >=0.5mm baseline; no image error'))
        files += [fr['RGB_path'],fr['Mask_path'],c['camera_file']]
    save('provenance/P2_PAIR_SELECTION_AUDIT.json',audit);save('provenance/P2_PAIRS_FROZEN.json',pairs);save('provenance/P2_INPUTS.json',stamp(files));save('provenance/P2_SOURCE_FROZEN.json',stamp([Path(__file__),R/'code/common.py',R/'config.json',R/'provenance/P2_PAIRS_FROZEN.json']));print('P2 PAIRS',[(x['A'],x.get('B'),x.get('view_angle_deg'),x['status'])for x in pairs],flush=True)
    p3=[]
    for A,other in [('G01_004_ref08','G01_005_raw00459'),('G01_005_raw00459','G01_004_ref08')]:
        target=next(x for x in pairs if x['A']==other)
        p3.append(dict(A=A,target_from_P2=other,**{k:v for k,v in target.items()if k!='A'}))
    save('provenance/P3_PAIRS_FROZEN.json',p3)
def background(c):
    a,p,rgb,m=data(c);P=a['XYZ_mm'];uv=np.c_[a['source_u'],a['source_v']];image=np.asarray(Image.open(c['RGB']).convert('RGB'));v,u=np.nonzero((p['labels']==0)&np.isfinite(p['depth_mm'])&(p['depth_mm']>0));B=unproject(np.c_[u,v],p['depth_mm'][v,u],p['K'],p['pose']);base=uv[:,1]>=np.quantile(uv[:,1],.8);cu=np.median(uv[base],0);cp=np.median(P[base],0);pv,pu=np.nonzero(p['labels']==1);rv,ru=np.nonzero(p['labels']==2);rad=2*max(np.ptp(pu)/2,np.ptp(ru)/2);ellipse=((u-cu[0])/rad)**2+((v-cu[1])/(.75*rad))**2<=1;mask=np.zeros(p['labels'].shape,np.uint8);mask[uv[base,1],uv[base,0]]=1;witness=cv2.distanceTransform(1-mask,cv2.DIST_L2,5)[v,u]<=12;sel=(ellipse&(np.linalg.norm(B-cp,axis=1)<=4*(c['R_mm']+.6)))|witness
    return B[sel],image[v[sel],u[sel]]/255.,np.c_[u[sel],v[sel]]
def raster(P,rgb,kind,ids,K,pose,shape,scene):
    h,w=shape;uv,z=vis.project_camera(P,np.array(K),np.array(pose));finite=np.isfinite(uv).all(1)&(z>0);xy=np.zeros_like(uv,dtype=int);xy[finite]=np.floor(uv[finite]+.5).astype(int);inside=finite&(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h);ii=np.flatnonzero(inside)
    depth=np.full(h*w,np.inf);who=np.full(h*w,-1,int);pix=xy[ii,1]*w+xy[ii,0];order=np.lexsort((ids[ii],z[ii],pix));sp=pix[order];first=np.r_[True,sp[1:]!=sp[:-1]];chosen=ii[order[first]];pixels=sp[first]
    cad=scene.cast(np.c_[np.tile(np.arange(w),h),np.repeat(np.arange(h),w)]);cz=cad['t_hit'].numpy();visible=z[chosen]<=cz[pixels]+load(R/'config.json')['CAD_occlusion_tolerance_mm'];who[pixels[visible]]=chosen[visible];depth[pixels[visible]]=z[chosen[visible]];valid=who>=0
    color=np.zeros((h*w,4),np.uint8);color[valid,:3]=np.rint(np.asarray(rgb)[who[valid]]*255).astype(np.uint8);color[valid,3]=255;labels=np.zeros(h*w,int);labels[valid]=kind[who[valid]];original=np.full(h*w,-1,int);original[valid]=ids[who[valid]]
    return dict(RGBA=color.reshape(h,w,4),kind=labels.reshape(h,w),source_original_id=original.reshape(h,w),z=depth.reshape(h,w),CAD_hit=np.isfinite(cz).reshape(h,w),input_points=len(P),positive_points=int(finite.sum()),in_bounds_points=int(inside.sum()),zbuffer_points=len(chosen),CAD_hidden=int((~visible).sum()),point_only_covered=int(valid.sum()))
def predict(c,pair,tier='RAW',H=None):
    a,p,rgb,m=data(c);P=a['XYZ_mm'];B,bRGB,buv=background(c);ids=np.arange(len(P));folder=R/'local_results'/c['id']
    if tier!='RAW':
        z=np.load(folder/(f'{tier}_exact.npz'if tier!='FINAL'else'Final_Cleaned_exact.npz'));ids=z['kept_original_indices']if'kept_original_indices'in z else ids
    points=np.r_[P[ids],B];colors=np.r_[rgb[ids],bRGB];kind=np.r_[np.ones(len(ids),int),np.full(len(B),2)];original=np.r_[ids,len(P)+np.arange(len(B))]
    if H is not None:points=points@H[:3,:3].T+H[:3,3]
    target=np.asarray(Image.open(pair['B_RGB']).convert('RGB'));K=np.array(pair['B_K']);pose=np.array(pair['B_c2w']);scene=SameCameraScene(ring(c),K,pose,(target.shape[1],target.shape[0]),str(OLD/'surface_fusion_v3/vendor'));out=raster(points,colors,kind,original,K,pose,target.shape[:2],scene);out.update(source_RGB_path=c['RGB'],target_RGB_used_for_prediction=False,world_transform=np.eye(4)if H is None else H,source_original_points=len(P),background_points=len(B))
    return out,target
def errors(pred,target,mask):return stats(np.abs(pred['RGBA'][:,:,:3].astype(float)-target.astype(float)).mean(2)[mask])
def evaluate(raw,cleaned,target,mask):
    Rpol=raw['kind']==1;Cpol=cleaned['kind']==1;obj=mask==1;common=Rpol&Cpol;ids=common&(raw['source_original_id']==cleaned['source_original_id']);rs=Rpol&obj;cs=Cpol&obj;both=common&obj;N=int(obj.sum());row=dict(target_polyp_denominator=N,raw_polyp_covered=int(rs.sum()),cleaned_polyp_covered=int(cs.sum()),raw_coverage=float(rs.sum()/N),cleaned_coverage=float(cs.sum()/N),coverage_change=float((cs.sum()-rs.sum())/N),raw_outside_polyp=int((Rpol&~obj).sum()),cleaned_outside_polyp=int((Cpol&~obj).sum()),raw_valid=errors(raw,target,rs),cleaned_valid=errors(cleaned,target,cs),common_support_N=int(both.sum()),common_raw=errors(raw,target,both),common_cleaned=errors(cleaned,target,both),same_original_point_N=int((ids&obj).sum()),same_original_raw=errors(raw,target,ids&obj),same_original_cleaned=errors(cleaned,target,ids&obj),lost_polyp_pixels=int((Rpol&~Cpol).sum()),new_polyp_pixels=int((Cpol&~Rpol).sum()),changed_winner_common_pixels=int((common&~ids).sum()),raw_full_prediction_RGB_error=errors(raw,target,Rpol),cleaned_full_prediction_RGB_error=errors(cleaned,target,Cpol),background_raw_error=errors(raw,target,(raw['kind']==2)&(mask==0)),geometry_accuracy=None,metric_identity='RGB_VIEW_CONSISTENCY_NOT_DEPTH_ACCURACY')
    return row
def store_prediction(dest,out,target):
    dest.mkdir(parents=True,exist_ok=True);Image.fromarray(out['RGBA']).save(dest/'Prediction_A_RGB.png');Image.fromarray(target).save(dest/'B_real_frame.png');alpha=(out['RGBA'][:,:,3]>0)[:,:,None]*.7;overlay=np.rint(target*(1-alpha)+out['RGBA'][:,:,:3]*alpha).astype(np.uint8);Image.fromarray(overlay).save(dest/'Overlay.png');np.savez_compressed(dest/'projection_exact.npz',**out)
def run(cross=False):
    verify()
    for f in ['P2_EXECUTION_FROZEN.json','P2_INPUTS.json']:
        for x in load(R/'provenance'/f)['files']:assert sha(x['path'])==x['sha256'],x['path']
    pairs=load(R/'provenance'/('P3_PAIRS_FROZEN.json'if cross else'P2_PAIRS_FROZEN.json'));rows=[];st='P3'if cross else'P2'
    if cross:assert(R/'metrics/P2_results.json').exists()
    for pair in pairs:
        if pair['status'].startswith('NOT_EVALUABLE'):rows.append(pair);continue
        c=next(c for c in cases()if c['id']==pair['A']);transforms=load(ICF/'inputs/H_frozen.json')if cross else[dict(tag='SAME_VIDEO',H=np.eye(4))]
        for tr in transforms:
            tier='FINAL'if cross or c['group']!='G01'else'T2'
            H=np.array(tr['H']);H=np.linalg.inv(H)if cross and c['video']=='004'else H;raw,target=predict(c,pair,H=H);cleaned,_=predict(c,pair,tier,H);mask=cv2.imread(pair['B_Mask'],0);row=dict(A=c['id'],B=pair['B'],B_raw_frame=pair['B_raw_frame'],candidate=tr['tag'],**evaluate(raw,cleaned,target,mask),cleaned_prediction_identity='REJECTED_T2_DIAGNOSTIC_ONLY'if tier=='T2'else'FINAL_RAW_PRESERVED',final_selected_tier='RAW',target_not_in_A_HERO_inputs=pair.get('B_not_A_HERO_input')if not cross else None,whole_pipeline_independent=False,status='NO_VERIFIED_REGISTRATION'if cross else'POSE_CONDITIONAL_DIAGNOSTIC',source_timeline_risk=c['video']=='004'and c['group']=='G01')
            if cross:
                row.update(Ring_center_offset_mm=np.linalg.norm(H[:3,3]),Ring_normal_angle_degrees=np.degrees(np.arccos(np.clip(H[2,2],-1,1))),H_source_to_target=H,transform_updated=False,background_matches_used_for_new_fit=0,reason='Historical H reused without optimization; Ring yaw symmetry and shared camera/identity errors unresolved; no certified independent background anchors')
            folder=R/'local_results'/st/(c['id']+'__'+tr['tag']);store_prediction(folder/'RAW',raw,target);store_prediction(folder/'CLEANED',cleaned,target);row['local_output']=str(folder);rows.append(row)
            print(st,c['id'],'->',pair['B'],tr['tag'],'cover',round(row['raw_coverage'],3),'RGB MAE',row['raw_valid']['MAE'],flush=True)
    save('metrics/'+st+'_results.json',rows);csvsave('metrics/'+st+'_results.csv',rows)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run','cross']);x=parser.parse_args();prepare()if x.mode=='prepare'else run(x.mode=='cross')
