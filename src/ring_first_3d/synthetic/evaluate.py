"""Independent evaluator role: only reads predictions after their SHA freeze."""
import json
import numpy as np
from scipy.spatial.transform import Rotation
from .io import fetch,save_json,outputs,stage_record
from .raster import independent_rays
from ..policy.contracts import require
from ..contracts.coordinates import project


def stats(error,denominator,valid,z):
    values=np.asarray(error)[valid]
    return dict(target_N=int(denominator),independent_numeric_N=int(valid.sum()),failed_N=int(denominator-valid.sum()),
        independent_coverage=float(valid.mean()),MAE_mm=float(values.mean())if len(values)else None,
        median_mm=float(np.median(values))if len(values)else None,p95_mm=float(np.quantile(values,.95))if len(values)else None,max_mm=float(values.max())if len(values)else None,
        median_absolute_relative_error_to_axial_depth=float(np.median(values/z[valid]))if len(values)else None,
        within_0p1mm_N=int((values<=.1).sum()),measurement_correctness="Correspondence error against synthetic latent true surface point, not polyp diameter")


def evaluate(task,attempt,condition,smoke=False):
    root=attempt.parents[1];prefix="C0_smoke"if smoke else condition
    stage=prefix+"_predict"
    folder,payload=stage_record(root,stage)
    freeze=json.loads(fetch(root,stage,"PREDICTIONS_FROZEN.json").read_text())
    require(freeze["Body_updated"]is False and freeze["GT_read_by_predictor"]is False,"GT_LEAK","Predictor contract")
    body=np.load(fetch(root,"G0_prepare","public/initial_body.npz"));V,F=body["V"],body["F"]
    rows=[];pairs=[]
    cameras=json.loads(fetch(root,"G0_prepare","private/cameras.json").read_text())
    if smoke:cameras=cameras[:1]
    for camera in cameras:
        cid=camera["id"];ob=np.load(fetch(root,"G0_prepare","public/"+condition+"/"+cid+".npz"));truth=np.load(fetch(root,"G0_prepare","private/"+cid+".npz"))
        actual=np.load(fetch(root,stage,"predictions/"+cid+".npz"));Ptrue=truth["P_true"];Pobs=actual["P_obs"]
        T,K=np.array(camera["T"]),ob["K"];cfg=task["science"]["conditions"][condition]
        # Independent construction with scipy Rotation, not inject() result reuse.
        cam_true=(Ptrue-T[:3,3])@T[:3,:3]
        Ry=Rotation.from_rotvec(np.array([0,np.radians(cfg["rotation_y_deg"]),0])).as_matrix()
        biased=cam_true*(1+cfg["depth_bias_mm"]/cam_true[:,2])[:,None]
        expected=(biased@Ry.T+np.array([cfg["translation_x_mm"],0,0]))@T[:3,:3].T+T[:3,3]
        injection_error=float(np.linalg.norm(Pobs-expected,axis=1).max())
        require(injection_error<.001,"INJECTION_PROTOCOL","Independent perturbation verification: "+cid)
        local_shift=(Pobs-Ptrue)@T[:3,:3]
        if condition=="C1":
            expected_ray=np.c_[ob["uv"],np.ones(len(Pobs))]@np.linalg.inv(K).T
            require(np.max(abs(local_shift-expected_ray))<.001,"INJECTION_PROTOCOL","Actual axial Z +1 mm along each native pixel ray")
        z_oracle=independent_rays(V,F,ob["uv"],K,T)
        oracle_z_error=float(abs(z_oracle-truth["z_true"]).max())
        require(np.isfinite(z_oracle).all() and oracle_z_error<.001,"ORACLE_CONTRACT","Independent true camera raycast")
        # Oracle is evaluation-only, with latent GT face+barycentric material ID.
        oracle=np.einsum("ni,nij->nj",truth["bary"],V[F[truth["face"]]])
        errors={};valids={};evaluated=dict(P_true=Ptrue,uv=ob["uv"],injection_vector_mm=Pobs-Ptrue,
            oracle_points=oracle,true_face=truth["face"],true_bary=truth["bary"],role=ob["role"])
        for method in ["nearest_surface","pixel_face","pixel_face_ring","oracle_true_camera"]:
            if method=="oracle_true_camera":Q=oracle;valid=np.ones(len(Q),bool);face=truth["face"];bary=truth["bary"]
            else:Q=actual[method+"_points"];valid=actual[method+"_valid"];face=actual[method+"_face"];bary=actual[method+"_bary"]
            require(np.isfinite(Q[valid]).all() and np.isnan(Q[~valid]).all(),"NAN_CONTRACT",method)
            err=np.linalg.norm(Q-Ptrue,axis=1);errors[method]=err;valids[method]=valid
            r=dict(condition=condition,view_id=cid,role=camera["role"],method=method,**stats(err,len(Q),valid,truth["z_true"]),
                exact_face_fraction=float((face[valid]==truth["face"][valid]).mean())if valid.any()else None,
                independent_injection_max_mm=injection_error,actual_world_displacement_mean_mm=float(np.linalg.norm(Pobs-Ptrue,axis=1).mean()),
                actual_camera_axial_shift_min_mm=float(local_shift[:,2].min()),actual_camera_axial_shift_max_mm=float(local_shift[:,2].max()),
                independent_Oracle_ray_depth_max_mm=oracle_z_error,oracle=method=="oracle_true_camera")
            if valid.any():
                reconstructed=np.einsum("ni,nij->nj",bary[valid],V[F[face[valid]]])
                require(np.max(np.linalg.norm(reconstructed-Q[valid],axis=1))<1e-8 and np.max(abs(bary[valid].sum(1)-1))<1e-5,"BARYCENTRIC_CONTRACT",method)
            if condition=="C0":require(r["independent_numeric_N"]>=100 and r["max_mm"]<.001,"C0_GATE","Unperturbed numeric matches must be accurate; unmatched targets remain explicit failures")
            rows.append(r);evaluated[method+"_error_mm"]=err;evaluated[method+"_valid"]=valid
        for first,second in [("nearest_surface","pixel_face"),("pixel_face","pixel_face_ring")]:
            common=valids[first]&valids[second]
            pairs.append(dict(condition=condition,view_id=cid,first=first,second=second,common_success_N=int(common.sum()),target_N=len(Ptrue),
                first_MAE_mm=float(errors[first][common].mean())if common.any()else None,second_MAE_mm=float(errors[second][common].mean())if common.any()else None,
                paired_delta_second_minus_first_mm=float((errors[second][common]-errors[first][common]).mean())if common.any()else None))
        (attempt/"evaluation").mkdir(exist_ok=True)
        np.savez_compressed(attempt/"evaluation"/(cid+".npz"),**evaluated)
    save_json(attempt/"metrics.json",dict(rows=rows,paired=pairs,conditions=task["science"]["conditions"][condition],prediction_freeze=freeze,
        GT_used_for_algorithm_selection=False,Body_updated=False,oracle_excluded_from_predictions=True))
    return outputs(attempt,dict(status="PASS",role="evaluator",rows=rows,paired=pairs,GT_read_by_evaluator=True,body_update_N=0))
