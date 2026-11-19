"""Observed ellipse coordinates -> frozen Body ellipse -> visible 3D candidates."""
import json
import numpy as np
from ..synthetic.io import fetch,save_json,outputs
from ..contracts.identities import sha256
from ..policy.contracts import require
from .geometry import scene,cast,spd_basis,visible_contour,choose
from .legacy import namespace


def candidates(uv,fit,body,K,C,ns,shrink=.97,mediated=True,body_scene=None):
    center,M,axes,curve=ns['ellipse_projection'](body['p'],body['R0'],K,C)
    vals,U=np.linalg.eigh(M);Bb=U@np.diag(1/np.sqrt(vals))@U.T
    Bo=spd_basis(np.asarray(fit['basis_px']));co=np.asarray(fit['center_px'])
    normalized=(uv-co)@np.linalg.inv(Bo).T
    mapped=center+shrink*normalized@Bb.T if mediated else np.asarray(uv).copy()
    mesh_scene=body_scene if body_scene is not None else scene(body['V'],body['F'])
    z,face,bary=cast(mesh_scene,mapped,K,C);valid=np.isfinite(z)&(z>0)
    Q=np.full((len(uv),3),np.nan);Q[valid]=np.einsum('ni,nij->nj',bary[valid],body['V'][body['F'][face[valid]]])
    fit_error=np.abs(np.linalg.norm(normalized,axis=1)-1)
    confidence=np.exp(-fit_error*2);confidence[~valid]=0
    reasons=np.where(valid,'VISIBLE_CANDIDATE_NOT_PHYSICAL_CORRECTION','NO_VISIBLE_BODY_FACE')
    return dict(original_uv=uv,mapped_uv=mapped,normalized_ellipse_coordinates=normalized,points=Q,face=face,bary=bary,valid=valid,confidence=confidence,reason=reasons,
        observed_center=co,observed_basis=Bo,body_center=center,body_basis=Bb,body_conic=M,body_curve=curve,
        displacement_px=np.linalg.norm(mapped-uv,axis=1))


def run(task,attempt):
    root=attempt.parents[1];ns=namespace(task);body=dict(np.load(fetch(root,'G1_initialize','FROZEN_BODY.npz')));bs=scene(body['V'],body['F'])
    fits=json.loads(fetch(root,'G1_initialize','IMAGE_FITS.json').read_text());frames=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text());by={r['id']:r for r in frames}
    rows=[];(attempt/'maps').mkdir()
    for f in fits:
        cid=f['id'];a=np.load(fetch(root,'G0_simulate','public/initialization/'+cid+'.npz'));labels=a['labels']if f['domain']=='synthetic'else a['real_labels']
        uv,contact=visible_contour(labels);take=np.linspace(0,len(uv)-1,min(len(uv),task['sim']['mapping_samples_per_frame']),dtype=int);uv=uv[take];contact=contact[take]
        for method in ['MEDIATED','DIRECT_PIXEL']:
            m=candidates(uv,f,body,a['K'],a['C'],ns,task['sim']['mapping_radial_shrink'],method=='MEDIATED',bs)
            # Ring contact cuts are observable segmentation edges, not certified
            # physical Polyp boundaries. Retain them with zero confidence.
            m['contact_unknown']=contact;m['confidence'][contact]=0;m['reason'][contact]='RING_CONTACT_UNKNOWN_PHYSICAL_CONTOUR'
            key=f['domain']+'__'+cid+'__'+method;np.savez_compressed(attempt/'maps'/(key+'.npz'),**m)
            valid=m['valid'];require(np.isnan(m['points'][~valid]).all(),'NAN_CONTRACT',key)
            if valid.any():require(np.max(abs(m['bary'][valid].sum(1)-1))<1e-5,'BARYCENTRIC_CONTRACT',key)
            rows.append(dict(id=cid,video=f['video'],role=f['role'],domain=f['domain'],method=method,fit_provenance=f['mapping_fit'],key=key,targets=len(uv),numeric_candidates=int(valid.sum()),contact_unknown=int(contact.sum()),mean_pixel_warp=float(m['displacement_px'].mean()),mapping_is_pose_correction=False))
    save_json(attempt/'MAPPING_FROZEN.json',dict(rows=rows,body_sha256=sha256(fetch(root,'G1_initialize','FROZEN_BODY.npz')),GT_read_by_predictor=False))
    return outputs(attempt,dict(status='PASS',role='predictor',rows=rows,GT_read_by_predictor=False))
