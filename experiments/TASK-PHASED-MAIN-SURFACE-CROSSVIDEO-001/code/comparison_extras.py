"""Post-prediction common-denominator geometry descriptions, never changes predictions."""
from evaluation import *
def main():
    rows=[]
    for video in ['004','005']:
        cc=[c for c in cases()if c['video']==video];P=np.r_[tuple(source(c['id'])['P']for c in cc)]
        for mode in ['SINGLE','B','C','D0_CORE','D0_FULL']:
            m=geometry(video,mode);d,_n=nearest(P,m);Q=m.triangles_center;front=np.zeros(len(Q),bool);seen=np.zeros(len(Q),bool);res=[]
            for c in cc:
                p=source(c['id'])['p'];uv,z=vis.project_camera(Q,p['K'],p['pose']);xy=np.rint(uv).astype(int);inside=(z>0)&(xy[:,0]>=0)&(xy[:,0]<640)&(xy[:,1]>=0)&(xy[:,1]<360);ii=np.flatnonzero(inside);x,y=xy[ii].T;ii=ii[(p['labels'][y,x]==1)&np.isfinite(p['depth_mm'][y,x])];x,y=xy[ii].T;r=z[ii]-p['depth_mm'][y,x];seen[ii]=True;front[ii[r<-cfg()['consistency_mm']]]=True;res.extend(r.tolist())
            rows.append(dict(video=video,method=mode,fixed_original_source_N=len(P),within_025_of_surface_N=int((d<=.25).sum()),fixed_source_retained_surface_fraction=float((d<=.25).mean()),source_to_model_mm=stats(d),method_face_N=len(Q),method_face_exposure_sum_mm2=float(m.area),front_conflict_face_N=int(front.sum()),front_conflict_exposure_area_mm2=float(m.area_faces[front].sum()),front_conflict_exposure_fraction=float(m.area_faces[front].sum()/m.area),any_source_observed_face_N=int(seen.sum()),source_axial_residual_mm=stats(res),is_unique_anatomical_area=False,independent_accuracy=None));print('COMMON_GEOMETRY',video,mode,flush=True)
    save('metrics/D0_common_denominator_geometry.json',rows);csvsave('metrics/D0_common_denominator_geometry.csv',rows)
    old=OLD/'ring_first_v13_multisource/inputs/views.json';views=load(old);photos=[]
    for name in ['photo_001','photo_002','photo_003']:
        v=next(v for v in views if v['id']==name);photos.append(dict(id=name,RGB=v['RGB_path'],RGB_SHA256=sha(v['RGB_path']),pose_status=v['pose_status'],has_confirmed_pose=v['pose']is not None,optical_mode=v.get('optical_mode'),used_in_scene=False,reason='Frozen photo pose absent/UNREGISTERED, optical mode unconfirmed; not forced into fusion'))
    save('metrics/auxiliary_photo_status.json',photos);save('provenance/POST_ANALYSIS_SOURCES.json',stamp([Path(__file__),old]));print('PHOTOS audited, no new pose estimation',flush=True)
if __name__=='__main__':main()
