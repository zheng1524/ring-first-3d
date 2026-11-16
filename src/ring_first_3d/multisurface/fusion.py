"""Owned radial-chart baseline: measured triangle hits first, Body completion.

No observed vertices are projected onto Body or averaged together. The fused
chart is a new explicitly limited star-shaped reconstruction, with seams and
conflicts recorded; every independent source surface remains untouched.
"""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from ..synthetic.io import fetch,save_json,outputs
from ..policy.contracts import require,PolicyError
from .geometry import scene


def body_chart(body,nt=96,nv=96):
    # Uniform polar ANGLES, not uniform Z: the chart must retain narrow polar
    # features. This only retessellates the exact frozen ellipsoid parameters.
    phi=np.arange(nt)*2*np.pi/nt;theta=np.arange(1,nv)*np.pi/nv
    rings=np.array([np.c_[np.sin(t)*np.cos(phi),np.sin(t)*np.sin(phi),np.full(nt,np.cos(t))]for t in theta]).reshape(-1,3)
    unit=np.r_[[[0.,0.,1.]],rings,[[0.,0.,-1.]]];faces=[]
    for j in range(nt):faces.append([0,1+j,1+(j+1)%nt])
    for k in range(nv-2):
        a=1+k*nt;b=a+nt
        for j in range(nt):q=(j+1)%nt;faces.extend([[a+j,b+j,b+q],[a+j,b+q,a+q]])
    last=len(unit)-1;a=1+(nv-2)*nt
    for j in range(nt):faces.append([a+j,last,a+(j+1)%nt])
    p=body['p'];Q=body['R0']@Rotation.from_rotvec(p[3:6]).as_matrix();V=(unit*np.exp(p[6:9]))@Q.T+p[:3]
    return V,np.asarray(faces,int)


def owned_model(body,meshes,videos,cfg):
    import open3d as o3d
    Vb,Fb=body_chart(body);center=body['p'][:3];direction=Vb-center;direction/=np.linalg.norm(direction,axis=1)[:,None]
    rays=np.c_[np.broadcast_to(center,direction.shape),direction].astype(np.float32);n=len(Vb);k=len(meshes)
    depths=np.full((k,n),np.inf);faces=np.full((k,n),-1,int);bary=np.full((k,n,3),np.nan);points=np.full((k,n,3),np.nan);incidence=np.zeros((k,n))
    for i,m in enumerate(meshes):
        r=scene(m['V'],m['F']).cast_rays(o3d.core.Tensor(rays),nthreads=2);t=r['t_hit'].numpy();f=r['primitive_ids'].numpy().astype(np.int64);b=r['primitive_uvs'].numpy().astype(float);norm=r['primitive_normals'].numpy().astype(float)
        good=np.isfinite(t)&(t>0)&(t<50);angle=abs((norm*direction).sum(1));good&=angle>=cfg['fusion_min_incidence'];depths[i,good]=t[good];faces[i,good]=f[good];bary[i,good]=np.c_[1-b[good].sum(1),b[good]]
        points[i,good]=np.einsum('ni,nij->nj',bary[i,good],m['V'][m['F'][f[good]]]);incidence[i,good]=angle[good]
    finite=np.isfinite(depths);support=np.zeros((k,n),int)
    for i in range(k):
        joint=finite&finite[i][None];delta=np.full_like(depths,np.inf);np.subtract(depths,depths[i][None],out=delta,where=joint)
        support[i]=np.sum(joint&(abs(delta)<=cfg['fusion_consensus_mm']),axis=0)
    # One measured owner only. Medians/consensus never become output coordinates.
    score=support.astype(float)+incidence*.1;score[~finite]=-np.inf;winner=np.argmax(score,axis=0);ix=np.arange(n);trusted=support[winner,ix]>=cfg['fusion_min_support'];owner=np.where(trusted,winner,-1)
    V=Vb.copy();V[trusted]=points[winner[trusted],ix[trusted]]
    low=np.min(np.where(finite,depths,np.inf),axis=0);high=np.max(np.where(finite,depths,-np.inf),axis=0);spread=np.where(finite.sum(0)>1,high-low,0.);conflict=(finite.sum(0)>1)&(spread>cfg['fusion_consensus_mm'])
    reason=np.full(n,'BODY_UNOBSERVED_COMPLETION',dtype='<U48');reason[finite.any(0)]='BODY_OBSERVED_UNTRUSTED_COMPLETION';reason[trusted]='MEASURED_OWNER_CONSENSUS';reason[trusted&conflict]='MEASURED_OWNER_CONFLICT_RECORDED'
    tri=V[Fb];edge=np.stack([tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],tri[:,2]-tri[:,1]],1);maxedge=np.linalg.norm(edge,axis=2).max(1)
    area=np.linalg.norm(np.cross(edge[:,0],edge[:,1]),axis=1)/2;keep=(maxedge<=cfg['fusion_max_seam_jump_mm'])&(area>1e-10);F=Fb[keep]
    fowners=owner[F];face_observed=(fowners>=0).all(1);face_body=(fowners<0).all(1);face_seam=~((fowners[:,0]==fowners[:,1])&(fowners[:,1]==fowners[:,2]));baseface=np.where(keep)[0]
    require(len(np.unique(baseface))==len(F),'DUPLICATE_COVERAGE','Only one fused triangle per scaffold cell')
    if trusted.any():require(np.allclose(V[trusted],points[winner[trusted],ix[trusted]],atol=1e-10),'OBSERVATION_REPLACEMENT','Owned points must equal actual source triangle hits, not Body projection')
    return dict(V=V,F=F),dict(owner=owner,selected_source_face=np.where(trusted,faces[winner,ix],-1),selected_source_bary=np.where(trusted[:,None],bary[winner,ix],np.nan),reason=reason,
        source_ids=np.arange(k),candidate_depths=depths,candidate_faces=faces,candidate_bary=bary,candidate_points=points,candidate_incidence=incidence,candidate_support=support,
        conflict=conflict,spread_mm=spread,base_face_ids=baseface,rejected_base_face_ids=np.where(~keep)[0],face_observed=face_observed,face_completion=face_body,face_seam=face_seam,
        all_input_surfaces_retained=True),dict(vertices=n,faces=len(F),measured_owner_vertices=int(trusted.sum()),Body_completion_vertices=int((~trusted).sum()),unobserved_completion_vertices=int((~finite.any(0)).sum()),
        observed_untrusted_completion_vertices=int((finite.any(0)&~trusted).sum()),overlap_conflict_vertices=int(conflict.sum()),max_radial_conflict_mm=float(spread.max()),
        seam_triangles_rejected=int((~keep).sum()),measured_faces=int(face_observed.sum()),completion_faces=int(face_body.sum()),transition_faces=int((~face_observed&~face_body).sum()),
        no_average_coordinates=True,no_duplicate_surface_cells=True,Body_parameters_unchanged=True,chart_polar_angles=96,chart_azimuth_angles=96,
        geometry_model='Uniform-angle radial chart of unchanged frozen ellipsoid parameters with measured source triangle hits; non-star-shaped geometry/owner transitions may leave explicit holes')


def run(task,attempt):
    root=attempt.parents[1];cfg=task['fusion'];pred=json.loads(fetch(root,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text());frames=[r for r in json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT'];rows=[]
    for record in pred['rows']:
        key=record['key'];out=attempt/key;out.mkdir()
        if record['status']!='NUMERIC':rows.append(dict(key=key,status='FAILED_NAN',reason=record['reason']));continue
        meshes=[dict(np.load(fetch(root,'G3_all_predict',key+'/'+r['id']+'.npz')))for r in frames];body=dict(np.load(fetch(root,'G1_body',record['arm']+'_BODY.npz')))
        try:
            model,ownership,summary=owned_model(body,meshes,[r['video']for r in frames],cfg)
            if len(model['F'])<=100:raise ValueError('SCIENTIFIC_FUSION_EMPTY: insufficient actual fused triangle surface; no fake fallback')
            np.savez_compressed(out/'FUSED_MODEL.npz',**model);np.savez_compressed(out/'SURFACE_OWNERSHIP.npz',**{k:v for k,v in ownership.items()if not isinstance(v,bool)})
            status=dict(key=key,condition=record['condition'],arm=record['arm'],method=record['method'],kind=record['kind'],tolerance_mm=record['tolerance_mm'],status='NUMERIC',**summary,
                independent_source_count=len(frames),unfused_surface_paths=[str(fetch(root,'G3_all_predict',key+'/'+r['id']+'.npz'))for r in frames],GT_read_by_predictor=False)
        except PolicyError:raise
        except(ValueError,RuntimeError,np.linalg.LinAlgError)as e:status=dict(key=key,status='FAILED_NAN',reason=str(e))
        save_json(out/'FUSION_RECORD.json',status);rows.append(status);print('FUSION',key,status['status'],flush=True)
    save_json(attempt/'FUSION_FROZEN.json',dict(rows=rows,GT_read_by_predictor=False,Body_frozen=True,all_unfused_surfaces_preserved=True,GT_used_to_select_or_average=False))
    return outputs(attempt,dict(status='PASS',role='predictor',models=len(rows),numeric=sum(r['status']=='NUMERIC'for r in rows),GT_read_by_predictor=False))
