"""Generator role only: genuine G01, explicit canonical pose, no fitted alignment."""
import json
import os
from pathlib import Path
import subprocess
import numpy as np
from .raster import rasterize,independent_rays,ray_map
from .io import save_json,outputs
from ..policy.contracts import ROOT,require
from ..contracts.coordinates import resize_intrinsics,validate_ring
from ..contracts.identities import sha256


def observation(uv,z,K,T,condition,role,observed_mask):
    """Generator-only corruption. No clean camera/depth/latent GT in public output."""
    from .correspondence import inject
    P,estimated,checks=inject(uv,z,K,T,condition)
    return dict(uv=uv,z_observed=z+condition["depth_bias_mm"],K=K,T_estimated=estimated,P_observed=P,
                role=role,observed_mask=observed_mask,injection_metadata=np.array(json.dumps(checks)))


def prepare(task,attempt):
    sc=task["science"];assets=sc["assets"];public=attempt/"public";private=attempt/"private"
    public.mkdir();private.mkdir()
    request=dict(assets=assets,unit_to_mm=sc["unit_to_mm"],body_objects=["球体"],output=str(private))
    save_json(attempt/"export_request.json",request)
    command=[assets["blender_binary"]["path"],"-b","--factory-startup","--disable-autoexec","-t","2","--python",str(ROOT/"tools/research/export_g01_blender.py"),"--",str(attempt/"export_request.json")]
    env=dict(os.environ,XDG_CONFIG_HOME=str(attempt/"runtime/blender_config"))
    with (attempt/"blender_stdout.txt").open("w")as out:
        subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,env=env,check=True,timeout=90)
    exported=np.load(private/"g01_mesh.npz");cached=np.load(assets["gt_cache"]["path"])
    require(np.array_equal(exported["F"],cached["F"]) and np.allclose(exported["V"],cached["V"],atol=1e-10,rtol=0),"GT_EXPORT","Fresh Blender export does not equal registered G01 cache")
    V,F=exported["V"],exported["F"]
    rr=np.load(assets["ring"]["path"]);validate_ring(rr["V"],10.)
    # This exact mesh clone is an explicitly GT-derived synthetic control,
    # never a claimed reconstruction or a GT-free learned initializer.
    np.savez_compressed(public/"initial_body.npz",V=V,F=F)
    np.savez_compressed(public/"ring.npz",V=rr["V"],F=rr["F"])
    fixture=json.loads(Path(task["inputs"]["fixture"]["path"]).read_text());pack=Path(fixture["real_case_root"])/"inputs/G01"
    meta=json.loads((pack/"CASE.json").read_text());by={v["id"]:v for v in meta["views"]}
    cameras=[];validation=[]
    for cid in sc["camera_ids"]:
        a=np.load(pack/(cid+".npz"));K=resize_intrinsics(a["K"],sc["native_resolution"],sc["resolution"]);T=a["T"]
        b=ray_map(V,F,K,T);ring=ray_map(rr["V"],rr["F"],K,T)
        pixel_render=rasterize(V,F,K,T)
        observed=b["valid"] & (b["z"]+1e-4<ring["z"])
        y,x=np.where(observed);uv=np.c_[x,y];P=b["points"][observed]
        require(len(P)>100,"NOT_EVALUABLE","Insufficient genuine G01 visible pixels: "+cid)
        # Independent Open3D engine checks camera/pixel axial depth before any
        # prediction. Failures include all unmatched rays, never mask silently.
        zcheck=independent_rays(V,F,uv,K,T);err=abs(zcheck-b["z"][observed])
        require(np.isfinite(zcheck).all() and float(err.max())<sc["projection_tolerance_mm"],"RASTER_CONTRACT",cid)
        common=observed & pixel_render["valid"]
        raster_error=abs(pixel_render["z"][common]-b["z"][common])
        require(common.any() and float(raster_error.max())<sc["projection_tolerance_mm"],"RASTER_CONTRACT","Independent generator vs T24-adapted raster "+cid)
        for condition in sc["condition_order"]:
            (public/condition).mkdir(exist_ok=True)
            np.savez_compressed(public/condition/(cid+".npz"),**observation(uv,b["z"][observed],K,T,sc["conditions"][condition],by[cid]["role"],observed))
        np.savez_compressed(private/(cid+".npz"),P_true=P,face=b["face"][observed],bary=b["bary"][observed],z_true=b["z"][observed],
            full_body_mask=b["valid"],ring_mask=ring["valid"],ring_hidden=b["valid"]&~observed,body_z=b["z"],ring_z=ring["z"])
        cameras.append(dict(id=cid,role=by[cid]["role"],K=K.tolist(),T=T.tolist(),input_sha256=sha256(pack/(cid+".npz")),observed_N=len(P),image_pixels=320*180))
        validation.append(dict(id=cid,independent_Open3D_z_max_mm=float(err.max()),independent_P3D_common_z_max_mm=float(raster_error.max()),
            raster_unmatched_observed_N=int((observed&~pixel_render["valid"]).sum()),observed_N=len(P),GT_ring_hidden_N=int((b["valid"]&~observed).sum())))
    public_cameras=[{k:v for k,v in camera.items()if k!="T"}for camera in cameras]
    save_json(public/"cameras.json",public_cameras);save_json(private/"cameras.json",cameras)
    save_json(private/"G0_FREEZE.json",dict(source_id="G01:spec_01p-12-:original_blender",assets=assets,cameras=cameras,GT_canonical_transform=sc["canonical_from_blender"],
        placement="Declared synthetic native-author world pose, not real-deployment registration",body_initialization=sc["body_initialization"],body_update_allowed=False,conditions=sc["conditions"],
        independent_render_validation=validation,GT_read_by_generator=True,GT_read_by_predictor_allowed=False))
    return outputs(attempt,dict(status="PASS",role="generator",source_id="G01:spec_01p-12-",body_vertices=len(V),body_faces=len(F),cameras=public_cameras,render_validation=validation))
