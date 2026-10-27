"""Controlled copy of previously tested source-color point projection only."""
from common import *

def raster(P,rgb,kind,ids,K,pose,shape,scene):
    h,w=shape;uv,z=vis.project_camera(P,np.array(K),np.array(pose));finite=np.isfinite(uv).all(1)&(z>0);xy=np.zeros_like(uv,dtype=int);xy[finite]=np.floor(uv[finite]+.5).astype(int);inside=finite&(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h);ii=np.flatnonzero(inside)
    depth=np.full(h*w,np.inf);who=np.full(h*w,-1,int);pix=xy[ii,1]*w+xy[ii,0];order=np.lexsort((ids[ii],z[ii],pix));sp=pix[order];first=np.r_[True,sp[1:]!=sp[:-1]];chosen=ii[order[first]];pixels=sp[first]
    cad=scene.cast(np.c_[np.tile(np.arange(w),h),np.repeat(np.arange(h),w)]);cz=cad['t_hit'].numpy();visible=z[chosen]<=cz[pixels]+load(R/'config.json')['CAD_occlusion_tolerance_mm'];who[pixels[visible]]=chosen[visible];depth[pixels[visible]]=z[chosen[visible]];valid=who>=0
    color=np.zeros((h*w,4),np.uint8);color[valid,:3]=np.rint(np.asarray(rgb)[who[valid]]*255).astype(np.uint8);color[valid,3]=255;labels=np.zeros(h*w,int);labels[valid]=kind[who[valid]];original=np.full(h*w,-1,int);original[valid]=ids[who[valid]]
    return dict(RGBA=color.reshape(h,w,4),kind=labels.reshape(h,w),source_original_id=original.reshape(h,w),z=depth.reshape(h,w),CAD_hit=np.isfinite(cz).reshape(h,w),input_points=len(P),positive_points=int(finite.sum()),in_bounds_points=int(inside.sum()),zbuffer_points=len(chosen),CAD_hidden=int((~visible).sum()),point_only_covered=int(valid.sum()))

def errors(pred,target,mask):return stats(np.abs(pred['RGBA'][:,:,:3].astype(float)-target.astype(float)).mean(2)[mask])

def evaluate(raw,cleaned,target,mask):
    Rpol=raw['kind']==1;Cpol=cleaned['kind']==1;obj=mask==1;common=Rpol&Cpol;ids=common&(raw['source_original_id']==cleaned['source_original_id']);rs=Rpol&obj;cs=Cpol&obj;both=common&obj;N=int(obj.sum());row=dict(target_polyp_denominator=N,raw_polyp_covered=int(rs.sum()),cleaned_polyp_covered=int(cs.sum()),raw_coverage=float(rs.sum()/N),cleaned_coverage=float(cs.sum()/N),coverage_change=float((cs.sum()-rs.sum())/N),raw_outside_polyp=int((Rpol&~obj).sum()),cleaned_outside_polyp=int((Cpol&~obj).sum()),raw_valid=errors(raw,target,rs),cleaned_valid=errors(cleaned,target,cs),common_support_N=int(both.sum()),common_raw=errors(raw,target,both),common_cleaned=errors(cleaned,target,both),same_original_point_N=int((ids&obj).sum()),same_original_raw=errors(raw,target,ids&obj),same_original_cleaned=errors(cleaned,target,ids&obj),lost_polyp_pixels=int((Rpol&~Cpol).sum()),new_polyp_pixels=int((Cpol&~Rpol).sum()),changed_winner_common_pixels=int((common&~ids).sum()),raw_full_prediction_RGB_error=errors(raw,target,Rpol),cleaned_full_prediction_RGB_error=errors(cleaned,target,Cpol),background_raw_error=errors(raw,target,(raw['kind']==2)&(mask==0)),geometry_accuracy=None,metric_identity='RGB_VIEW_CONSISTENCY_NOT_DEPTH_ACCURACY')
    return row
