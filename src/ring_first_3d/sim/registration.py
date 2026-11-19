"""Actual complete-mesh rigid registration, one SE(3) per video, fixed Body."""
import json,time
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from ..synthetic.io import fetch,save_json,outputs
from ..contracts.coordinates import unproject,validate_c2w
from ..contracts.identities import sha256
from ..policy.contracts import require,PolicyError
from .geometry import transform,se3,parameters,scene,closest,choose,contour
from .mapping import candidates
from .legacy import namespace


def ring_pose(V):
    center=V.mean(0);_,_,U=np.linalg.svd(V-center,full_matrices=False);normal=U[-1]
    if normal[2]<0:normal=-normal
    return center,normal


def ring_only(V):
    c,n=ring_pose(V);z=np.array([0.,0.,1.]);axis=np.cross(n,z);mag=np.linalg.norm(axis)
    R=np.eye(3)if mag<1e-12 else Rotation.from_rotvec(axis/mag*np.arctan2(mag,n@z)).as_matrix()
    T=np.eye(4);T[:3,:3]=R;T[:3,3]=-R@c;return T


def robust_icp(source,target,threshold=1.5,iterations=60):
    import open3d as o3d
    def cloud(mesh):
        V,F=mesh;tri=o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(V),o3d.utility.Vector3iVector(F));tri.compute_vertex_normals()
        p=o3d.geometry.PointCloud();p.points=tri.vertices;p.normals=tri.vertex_normals;return p
    s,t=cloud(source),cloud(target)
    est=o3d.pipelines.registration.TransformationEstimationPointToPlane(o3d.pipelines.registration.TukeyLoss(k=.5))
    fit=o3d.pipelines.registration.registration_icp(s,t,threshold,np.eye(4),est,o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iterations))
    return np.asarray(fit.transformation),dict(fitness=float(fit.fitness),inlier_RMSE_mm=float(fit.inlier_rmse),correspondences=len(fit.correspondence_set),loss='Open3D Tukey point-to-plane, k=0.5mm')


def optimize(task,meshes,rings,cameras,observations,fits,body,ns,mediated=True,use_ring=False):
    sc=task['sim'];fit_ids={c['id']for c in cameras if c['role']=='FIT'};body_scene=scene(body['V'],body['F'])
    # Equal temporal coverage independent of GT and condition names.
    selected=[]
    for v in ['004','005']:
        opts=sorted(c['id']for c in cameras if c['video']==v and c['role']=='FIT')
        selected.extend(opts[i]for i in np.linspace(0,len(opts)-1,sc['initialization_views_per_video'],dtype=int))
    anchors=[];views=[]
    for c in cameras:
        if c['id']not in selected:continue
        cid=c['id'];a=observations[cid];K=np.asarray(c['K']);C=np.asarray(c['T_estimated']);f=fits[cid]
        y,x=np.where((a['labels']==1)&np.isfinite(a['depth_axial_mm']))
        ix=np.linspace(0,len(x)-1,min(len(x),sc['mapping_samples_per_frame']),dtype=int);uv=np.c_[x[ix],y[ix]]
        P=unproject(uv,a['depth_axial_mm'][y[ix],x[ix]],K,C)
        m=candidates(uv,f,body,K,C,ns,sc['mapping_radial_shrink'],mediated,body_scene)
        valid=m['valid'];anchors.append(dict(video=c['video'],P=P[valid],Q=m['points'][valid],weights=m['confidence'][valid],id=cid,total=len(uv),valid=int(valid.sum())))
        boundary=choose(contour(a['labels']==1),64)
        views.append(dict(video=c['video'],K=K,C=C,boundary=boundary))
    V4,F4=meshes['004'];V5,F5=meshes['005'];s4=scene(V4,F4)
    sample5=choose(V5[F5].mean(1),sc['registration_surface_samples'])
    counts={v:sum(a['valid']for a in anchors if a['video']==v)for v in ['004','005']}
    # Keep the same observation origin for all methods; no known inverse error
    # transform or clean camera is available to this predictor.
    p=np.zeros(12);rot=np.deg2rad(sc['registration_bounds_rotation_deg']);tr=sc['registration_bounds_translation_mm']
    bound=np.tile(np.r_[np.full(3,rot),np.full(3,tr)],2);trace=[];w=sc['weights'];ring_poses={v:ring_pose(rings[v])for v in rings}
    for outer in range(sc['registration_outer_iterations']):
        X4,X5=se3(p[:6]),se3(p[6:]);in4=transform(transform(sample5,X5),np.linalg.inv(X4))
        near,normals,_=closest(s4,in4);keep=np.linalg.norm(near-in4,axis=1)<2.
        src=sample5[keep];dst=near[keep];normals=normals[keep]
        def residual(q):
            X={'004':se3(q[:6]),'005':se3(q[6:])};parts=[]
            for a in anchors:
                if len(a['P']):parts.append(((transform(a['P'],X[a['video']])-a['Q'])*np.sqrt(a['weights'][:,None]*w['mediated_anchors']/max(1,len(a['P'])))).ravel())
            delta=transform(src,X['005'])-transform(dst,X['004']);norm=normals@X['004'][:3,:3].T
            parts.append(np.einsum('ni,ni->n',delta,norm)*np.sqrt(w['geometry']/max(1,len(src))))
            for view in views:
                C=X[view['video']]@view['C']
                try:
                    center,M,axes,_=ns['ellipse_projection'](body['p'],body['R0'],view['K'],C)
                    distance=ns['signed_distance'](view['boundary'],center,M,axes)/10
                except(ValueError,np.linalg.LinAlgError):distance=np.full(len(view['boundary']),100.)
                parts.append(distance*np.sqrt(w['contour']/max(1,len(distance))))
            if use_ring:
                for v in ['004','005']:
                    c,n=ring_poses[v];T=X[v];parts.append(np.r_[T[:3,:3]@c+T[:3,3],np.cross(T[:3,:3]@n,[0,0,1])*5]*np.sqrt(w['ring']))
            return np.concatenate(parts)
        initial=residual(p);t=time.monotonic()
        result=least_squares(residual,p,bounds=(-bound,bound),method='trf',loss='soft_l1',f_scale=.25,max_nfev=sc['registration_max_nfev'],ftol=1e-6,xtol=1e-6,gtol=1e-6,x_scale=np.tile([.05,.05,.05,.5,.5,.5],2))
        p=result.x;trace.append(dict(outer=outer,initial_objective=float(initial@initial/2),final_objective=float(result.fun@result.fun/2),optimizer_success=bool(result.success),nfev=result.nfev,seconds=time.monotonic()-t,correspondences=int(keep.sum()),parameters=p.tolist(),termination=result.message))
    return {'004':se3(p[:6]),'005':se3(p[6:])},dict(anchors=counts,trace=trace,optimizer_success=all(r['optimizer_success']for r in trace),method='2D ellipse-mediated + contour + robust full-surface geometry',mediated=mediated,Ring_used=use_ring,GT_read=False,
        anchor_preview=[dict(id=a['id'],video=a['video'],P=a['P'][:24].tolist(),Q=a['Q'][:24].tolist(),confidence=a['weights'][:24].tolist())for a in anchors])


def run(task,attempt,smoke=False):
    root=attempt.parents[1];ns=namespace(task);bodyfile=fetch(root,'G1_initialize','FROZEN_BODY.npz');body_sha=sha256(bodyfile);body=dict(np.load(bodyfile))
    allfits=json.loads(fetch(root,'G1_initialize','IMAGE_FITS.json').read_text());fits={r['id']:r for r in allfits if r['domain']=='synthetic'}
    index=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text())
    observations={r['id']:dict(np.load(fetch(root,'G0_simulate','public/observations/'+r['id']+'.npz')))for r in index}
    conditions=['S0','S1']if smoke else task['sim']['condition_order'];rows=[];failures=[]
    for condition in conditions:
        cameras=json.loads(fetch(root,'G0_simulate','public/conditions/'+condition+'/cameras.json').read_text());meshes={};rings={}
        for v in ['004','005']:
            a=np.load(fetch(root,'G0_simulate','public/conditions/'+condition+'/'+v+'_mesh.npz'));meshes[v]=(a['V'],a['F'])
            rings[v]=np.load(fetch(root,'G0_simulate','public/conditions/'+condition+'/'+v+'_ring.npz'))['V']
        for method in task['sim']['methods']:
            started=time.monotonic();out=attempt/condition/method;out.mkdir(parents=True)
            try:
                if method=='M0':X={v:np.eye(4)for v in meshes};details=dict(method='No correction',optimizer_success=True)
                elif method=='M1':
                    T,details=robust_icp(meshes['005'],meshes['004'],task['sim']['ICP_threshold_mm'],task['sim']['ICP_iterations']);X={'004':np.eye(4),'005':T}
                elif method=='RING_ONLY':
                    X={v:ring_only(rings[v])for v in meshes};details=dict(method='Unlabelled 3D CAD center and plane normal; minimum twist gauge',optimizer_success=True,yaw_about_Ring_normal_observable=False)
                else:X,details=optimize(task,meshes,rings,cameras,observations,fits,body,ns,method!='M2_DIRECT',method=='M2_RING')
                changes={}
                for v,(V,F)in meshes.items():
                    validate_c2w(X[v]);new=transform(V,X[v]);np.savez_compressed(out/(v+'_registered.npz'),V=new,F=F)
                    edge0=V[F[:,1]]-V[F[:,0]];edge1=new[F[:,1]]-new[F[:,0]]
                    require(np.max(abs(np.linalg.norm(edge0,axis=1)-np.linalg.norm(edge1,axis=1)))<1e-9,'MESH_RIGIDITY','Full mesh topology and shape unchanged')
                    changes[v]=float(np.linalg.norm(new-V,axis=1).max())
                record=dict(condition=condition,family=task['sim']['family_by_condition'][condition],method=method,status='NUMERIC',corrections={v:T.tolist()for v,T in X.items()},
                    details=details,full_mesh_max_displacement_mm=changes,shared_SE3_parameter_count_per_video=6,Body_frozen=True,point_to_Body_replacement=False,seconds=time.monotonic()-started)
            except PolicyError:raise
            except(ValueError,RuntimeError,np.linalg.LinAlgError)as e:
                # A method failure is retained; never select another method's
                # answer as a fallback or abort the other legal comparisons.
                record=dict(condition=condition,family=task['sim']['family_by_condition'][condition],method=method,status='FAILED_NAN',corrections=None,reason=str(e),seconds=time.monotonic()-started)
                failures.append(record)
            save_json(out/'PREDICTION.json',record);rows.append(record)
            print('REGISTER',condition,method,record['status'],record['seconds'],flush=True)
    require(sha256(bodyfile)==body_sha,'BODY_IMMUTABLE','Frozen coarse Body changed')
    save_json(attempt/'PREDICTIONS_FROZEN.json',dict(rows=rows,Body_sha256=body_sha,GT_read_by_predictor=False,history_prediction_fallback=0,failures=failures,smoke=smoke))
    return outputs(attempt,dict(status='PASS',role='predictor',rows=rows,scientific_failures=failures,Body_frozen=True,GT_read_by_predictor=False))
