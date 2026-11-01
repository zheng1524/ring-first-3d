"""B1: immutable raw-mesh UDF + conservatively conditional local orientation."""
from projective_local_field import *
class MeshLocalField:
    def __init__(self,source_id):
        self.source_id=source_id;self.s=s=source(source_id);self.b0=ProjectiveLocalField(source_id);self.p=cfg();P,F=s['P'],s['F'];tri=P[F];center=tri.mean(1);N=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(N,axis=1);N/=np.maximum(length[:,None],1e-20);N[((s['T'][:3,3]-center)*N).sum(1)<0]*=-1
        edges,count=edge_counts(F);boundary=np.unique(edges[count!=2]);self.boundary_face=np.isin(F,boundary).any(1);self.boundary_edges=edges[count==1]
        accumulated=np.zeros_like(P);weight=np.zeros(len(P))
        for j in range(3):np.add.at(accumulated,F[:,j],N*length[:,None]);np.add.at(weight,F[:,j],length)
        coherence=np.linalg.norm(accumulated,axis=1)/np.maximum(weight,1e-20);self.coherence=coherence[F].min(1);self.N=N;self.center=center;self.tree=cKDTree(center);self.component=face_components(F)
        self.area_by_component=np.bincount(self.component,weights=s['area']);foot=np.mean(((tri-s['T'][:3,3])@s['T'][:3,2]),axis=1)/min(s['K'][0,0],s['K'][1,1]);self.stretch=np.max(np.linalg.norm(tri[:,[1,2,0]]-tri,axis=2),axis=1)/np.maximum(foot,1e-12)>8
    def query(self,X_mm):
        X=np.asarray(X_mm,float).reshape(-1,3);finite=np.isfinite(X).all(1);safe=X.copy();safe[~finite]=0;s=self.s;n=len(X)
        cp,fid,bary=closest(self.source_id,safe);dist=np.linalg.norm(safe-cp,axis=1);b=self.b0.query(safe);inroi=finite&in_roi(self.source_id,safe);raw_band=inroi&(dist<=self.p['band_mm']);normal=self.N[fid]
        # Visibility of nearest actual original point, not of an invented closed surface.
        uv,z=vis.project_camera(cp,s['K'],s['T']);pixel=np.floor(uv+.5).astype(int);inside=(z>0)&(pixel[:,0]>=0)&(pixel[:,0]<640)&(pixel[:,1]>=0)&(pixel[:,1]<360);ids=np.flatnonzero(inside);mask=np.zeros(n,bool);first=np.full(n,np.inf);cad=np.full(n,np.inf)
        if len(ids):
            mask[ids]=s['labels'][pixel[ids,1],pixel[ids,0]]==1;first[ids],_=cast(self.source_id,uv[ids]);cad[ids]=camera(self.source_id).cast(uv[ids])['t_hit'].numpy()
        eps=self.p['ordering_epsilon_mm'];self_occ=np.isfinite(first)&(z>first+eps);surface=raw_band&mask&~b['cad_occluded']&~self_occ&(z<=cad+eps)
        competition=np.zeros(n,bool);local=np.flatnonzero(raw_band)
        for start in range(0,len(local),1024):
            ii=local[start:start+1024];k=min(self.p['competing_centroid_candidates'],len(self.center));_,candidate=self.tree.query(cp[ii],k=k);candidate=np.asarray(candidate).reshape(len(ii),k)
            triangles=s['P'][s['F'][candidate.ravel()]];qq=np.repeat(cp[ii],k,axis=0);near=trimesh.triangles.closest_point(triangles,qq).reshape(len(ii),k,3);dd=np.linalg.norm(near-safe[ii,None,:],axis=2)
            shares=(s['F'][candidate][:,:,:,None]==s['F'][fid[ii]][:,None,None,:]).any((2,3));dd[shares]=np.inf
            competition[ii]=np.min(dd,axis=1)<=dist[ii]+self.p['competition_distance_gap_mm']
        bary3=np.c_[1-bary.sum(1),bary];view=s['T'][:3,3]-cp;view/=np.maximum(np.linalg.norm(view,axis=1,keepdims=True),1e-20);incidence=abs((view*normal).sum(1))
        reliable=(~self.boundary_face[fid])&(self.coherence[fid]>=self.p['normal_coherence_min'])&(incidence>=self.p['incidence_abs_min'])&(bary3.min(1)>self.p['barycentric_interior_min'])&~competition&~self.stretch[fid]
        occ=b['cad_occluded']&finite&inroi;oriented=surface&reliable;value=np.full(n,np.nan);value[surface]=dist[surface];value[oriented]=((safe-cp)*normal).sum(1)[oriented];free=b['valid_free']&~surface&finite&inroi;value[free]=dist[free]
        kind=np.full(n,'UNSIGNED_DISTANCE',dtype='<U32');kind[oriented]='ORIENTED_LOCAL';sign=np.full(n,'UNKNOWN_SIGN',dtype='<U48');sign[oriented]='LOCAL_CAMERA_ORIENTED_CONDITIONAL';sign[free]='UNSIGNED_CONDITIONAL_FREE'
        ambiguous=((surface&competition)|b['ambiguous'])&finite&inroi;domain=np.full(n,3,np.uint8);domain[free]=1;domain[surface]=0;domain[ambiguous]=4;domain[occ]=2
        reason=b['reason_codes'].copy();reason[raw_band&~oriented]|=128;reason[raw_band&self.boundary_face[fid]]|=256;reason[raw_band&~reliable]|=512;reason[competition]|=1024;reason[raw_band&self_occ]|=2048
        out=dict(value=value,field_kind=kind,valid_surface=surface,valid_free=free,cad_occluded=occ,unknown=~(surface|free|occ),ambiguous=ambiguous,sign_status=sign,
            source_id=self.source_id,source_family=s['row']['source_family'],original_face_id=fid,original_vertex_ids=s['F'][fid],original_vertex_pixels=s['uv'][s['F'][fid]],closest_barycentric=bary3,closest_point_mm=cp,raw_udf_mm=dist,raw_surface_band=raw_band,domain=domain,
            reason_codes=reason,reliability_factors=dict(camera='REFERENCE_SCREENED_CONDITIONAL',normal_coherence=self.coherence[fid],incidence_abs=incidence,boundary_face=self.boundary_face[fid],nearest_competition=competition,
            stretch_proxy=self.stretch[fid],minor_component_proxy=self.area_by_component[self.component[fid]]<.01*self.area_by_component.max(),Cleaned_face_kept=(~s['clean']['clean_removed'][s['F'][fid]]).all(1),probability_calibrated=False))
        # Numerical UDF is diagnostic at any finite query; active scalar remains NaN where unknown.
        out['raw_udf_mm'][~finite]=np.nan;return out
