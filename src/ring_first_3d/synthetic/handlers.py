"""Allowlisted G0–G1 handlers, prediction and evaluation run in separate workers."""
import io
import json
from pathlib import Path
import unittest
import numpy as np
from .io import fetch,save_json,outputs
from .correspondence import correspond,METHODS
from ..contracts.coordinates import unproject
from ..contracts.identities import sha256
from ..policy.contracts import ROOT,require


def regression(attempt):
    loader=unittest.defaultTestLoader
    baseline=unittest.TestSuite([loader.discover(str(ROOT/"tests"),pattern="test_harness_contracts.py"),loader.discover(str(ROOT/"tests"),pattern="test_policy_bootstrap.py")])
    baseline_count=baseline.countTestCases()
    suite=unittest.TestSuite([baseline,loader.discover(str(ROOT/"tests"),pattern="test_synthetic_correspondence.py")])
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (attempt/"regression_log.txt").write_text(stream.getvalue())
    return dict(status="PASS"if result.wasSuccessful()and baseline_count==35 else"FAIL",baseline_tests=baseline_count,tests=result.testsRun,failures=len(result.failures),errors=len(result.errors))


def predict(task,attempt,condition,smoke=False):
    root=attempt.parents[1];body_path=fetch(root,"G0_prepare","public/initial_body.npz")
    body_sha=sha256(body_path);body=np.load(body_path);ring=np.load(fetch(root,"G0_prepare","public/ring.npz"))
    V,F=body["V"],body["F"];cameras=json.loads(fetch(root,"G0_prepare","public/cameras.json").read_text())
    if smoke:cameras=cameras[:1]
    rows=[];(attempt/"predictions").mkdir()
    for camera in cameras:
        cid=camera["id"];obs=np.load(fetch(root,"G0_prepare","public/"+condition+"/"+cid+".npz"))
        uv,z,K,estimated=obs["uv"],obs["z_observed"],obs["K"],obs["T_estimated"]
        P=unproject(uv,z,K,estimated);checks=json.loads(str(obs["injection_metadata"]))
        require(np.allclose(P,obs["P_observed"],atol=1e-10),"OBSERVATION_CONTRACT","Reconstruction from corrupted observation only")
        matches,maps=correspond(V,F,ring["V"],ring["F"],uv,P,K,estimated,(180,320))
        result=dict(P_obs=P,T_estimated=estimated,uv=uv,role=obs["role"],body_depth_map=maps["body"]["z"],ring_depth_map=maps["ring"]["z"])
        for method,record in matches.items():
            for key,value in record.items():result[method+"_"+key]=value
        p=attempt/"predictions"/(cid+".npz");np.savez_compressed(p,**result)
        rows.append(dict(view_id=cid,role=camera["role"],N=len(P),injection=checks,sha256=sha256(p),
            numeric={m:int(matches[m]["valid"].sum())for m in METHODS}))
    require(sha256(body_path)==body_sha,"BODY_IMMUTABLE","Body changed")
    save_json(attempt/"PREDICTIONS_FROZEN.json",dict(condition=condition,method_ids=list(METHODS),rows=rows,Body_sha256=body_sha,
        Body_updated=False,GT_read_by_predictor=False,history_prediction_fallback=0,parameters=task["science"]["conditions"][condition]))
    return outputs(attempt,dict(status="PASS",role="predictor",condition=condition,rows=rows,Body_updated=False,GT_read_by_predictor=False))


def dispatch(stage,task,attempt):
    if stage=="research_regression":return regression(attempt)
    if stage=="G0_prepare":
        from .scene import prepare
        return prepare(task,attempt)
    if stage=="G1_visualize":
        from .visualize import render
        return render(task,attempt)
    smoke=stage.startswith("C0_smoke")
    condition=stage.split("_")[0]
    require(condition in task["science"]["condition_order"],"UNAUTHORIZED_STAGE",stage)
    if stage.endswith("_predict"):return predict(task,attempt,condition,smoke)
    if stage.endswith("_evaluate"):
        from .evaluate import evaluate
        return evaluate(task,attempt,condition,smoke)
    raise ValueError("Unregistered scientific stage")
