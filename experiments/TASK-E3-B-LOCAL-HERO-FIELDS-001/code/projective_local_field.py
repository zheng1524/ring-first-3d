"""B0: native axial-depth evidence only, never an Euclidean/object SDF."""
from hero_native_adapter import *
DOMAINS=['Surface','Free-space','CAD-occluded','Unknown','Ambiguous']
REASONS={1:'OUTSIDE_ROI_OR_CAMERA',2:'NON_POLYP_MASK',4:'INVALID_NATIVE_DEPTH',8:'CAD_OCCLUDED',16:'NATIVE_DEPTH_BEHIND_CAD',32:'BEHIND_NARROWBAND_UNKNOWN',64:'NO_ORIGINAL_FACE_AT_RAY',128:'UNKNOWN_SIGN',256:'BOUNDARY_SIGN_UNQUALIFIED',512:'NORMAL_OR_GRAZING_UNQUALIFIED',1024:'NEAREST_FACE_COMPETITION',2048:'SELF_OCCLUDED_ORIGINAL_SURFACE'}
class ProjectiveLocalField:
    def __init__(self,source_id):self.source_id=source_id;self.s=source(source_id);self.p=cfg()
    def query(self,X_mm):
        X=np.asarray(X_mm,float).reshape(-1,3);s=self.s;n=len(X);finite=np.isfinite(X).all(1);safe=X.copy();safe[~finite]=s['T'][:3,3]+s['T'][:3,2]
        uv,z=vis.project_camera(safe,s['K'],s['T']);un,zn=vis.project_camera(safe,s['Kn'],s['T']);uv=np.nan_to_num(uv,nan=-1e9,posinf=-1e9,neginf=-1e9);un=np.nan_to_num(un,nan=-1e9,posinf=-1e9,neginf=-1e9)
        pixel=np.floor(uv+.5).astype(np.int64);pn=np.floor(un+.5).astype(np.int64);h,w=s['depth'].shape
        inside=finite&in_roi(self.source_id,safe)&(z>0)&(pixel[:,0]>=0)&(pixel[:,0]<640)&(pixel[:,1]>=0)&(pixel[:,1]<360)&(pn[:,0]>=0)&(pn[:,0]<w)&(pn[:,1]>=0)&(pn[:,1]<h)
        ids=np.flatnonzero(inside);D=np.full(n,np.nan);mask=np.zeros(n,bool);cad=np.full(n,np.inf);face=np.full(n,-1,np.int64);meshZ=np.full(n,np.inf)
        if len(ids):
            u,v=pixel[ids].T;mask[ids]=s['labels'][v,u]==1;D[ids]=s['depth'][pn[ids,1],pn[ids,0]];cad[ids]=camera(self.source_id).cast(uv[ids])['t_hit'].numpy();meshZ[ids],face[ids]=cast(self.source_id,uv[ids]);face[~np.isfinite(meshZ)]=-1
        numeric=np.isfinite(D)&(D>0);delta=D-z;eps=self.p['ordering_epsilon_mm'];occ=inside&np.isfinite(cad)&(z>cad+eps);contradict=inside&mask&numeric&np.isfinite(cad)&(D>cad+eps)
        legal=inside&mask&numeric&~occ&~contradict;raw_band=inside&mask&numeric&(abs(delta)<=self.p['band_mm']);surface=legal&raw_band;free=legal&(delta>self.p['band_mm'])
        ambiguous=contradict&~occ;domain=np.full(n,3,np.uint8);domain[free]=1;domain[surface]=0;domain[ambiguous]=4;domain[occ]=2
        value=np.full(n,np.nan);value[surface|free]=delta[surface|free];reason=np.zeros(n,np.uint32);reason[~inside]|=1;reason[inside&~mask]|=2;reason[inside&~numeric]|=4;reason[occ]|=8;reason[contradict]|=16;reason[legal&(delta< -self.p['band_mm'])]|=32;reason[inside&(face<0)]|=64
        sign=np.full(n,'UNKNOWN_SIGN',dtype='<U40');sign[surface]='LOCAL_PROJECTIVE_NOT_OBJECT_INTERIOR';sign[free]='CONDITIONAL_FRONT_FREE'
        return dict(value=value,field_kind=np.full(n,'PROJECTIVE_AXIAL',dtype='<U32'),valid_surface=surface,valid_free=free,cad_occluded=occ,unknown=~(surface|free|occ),ambiguous=ambiguous,
            sign_status=sign,source_id=self.source_id,source_family=s['row']['source_family'],original_face_id=face,native_pixel=pn,source_pixel=pixel,raw_projective_delta_mm=delta,raw_surface_band=raw_band,
            domain=domain,reason_codes=reason,reliability_factors=dict(camera='REFERENCE_SCREENED_CONDITIONAL',parent_camera_candidate_N=s['row']['parent_camera_candidate_N'],Mask_Polyp=mask,native_numeric_depth=numeric,
            inside_frozen_ROI_and_camera=inside,CAD_depth_contradiction=contradict,source_family=s['row']['source_family'],probability_calibrated=False),
            CAD_Z_mm=cad,original_mesh_Z_mm=meshZ,native_Z_mm=D,source_Z_mm=z)
