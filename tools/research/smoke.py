from _bootstrap import args, emit, ROOT
import hashlib
import json
from pathlib import Path
import tempfile
import numpy as np
from ring_first_3d.contracts.identities import verify_assets, sha256
from ring_first_3d.evaluation.validation import timed_test


def run(fixture, dxy_root):
    f = json.loads(Path(fixture).read_text())
    reference_path = Path(fixture).with_name("frozen_reference.json")
    ref = json.loads(reference_path.read_text())
    if sha256(fixture) != ref["fixture_SHA256"] or sha256(ROOT/"src/ring_first_3d/source_lock.json") != ref["source_lock_SHA256"]:
        raise ValueError("Reference input/source lock changed")
    verify_assets(f["assets"])
    root = Path(f["real_case_root"])/"inputs"/f["case"]
    sample = np.load(root/(f["sample_view"]+".npz"))
    def dxy():
        from ring_first_3d.adapters.dxy import measure_pixels
        from ring_first_3d.contracts.coordinates import ellipse_coordinates
        result = measure_pixels(sample["RGB"], sample["labels"], inner_diameter_mm=f["inner_diameter_mm"],
            source_id=f["dxy_source_id"], dxy_root=dxy_root)
        assert result["available"] == ref["dxy"]["available"]
        assert result["available"], "Real frozen sample produced no geometry; cannot pass numeric reproduction"
        for key in ["center_px", "basis_px"]:
            np.testing.assert_allclose(result[key], ref["dxy"][key], rtol=0, atol=1e-7)
        assert result["quality"]["Geometry"]=="V9.1" and result["quality"]["quality_class"]==ref["dxy"]["quality_class"]
        basis=result["basis_px"];center=result["center_px"]
        np.testing.assert_allclose(ellipse_coordinates(np.asarray(center)+basis[:,0], center, basis), [1,0], atol=1e-10)
        return dict(tolerance_px=1e-7, result=result,
                    semantics="Numeric official candidate, Q conflict recovery; inferred contour is not an observed full outline")
    def selection():
        from ring_first_3d.views.selection import select_views, quality_features, collapse_exact_duplicates
        out={}
        for k,strategy,anchor in [("selection_015","quality_diversity","baseline_ids"),("selection_016","direction_quota","mandatory_ids")]:
            item=f[k]
            result=select_views(item["views"],strategy,holdout_ids=item["holdout_ids"],**{anchor:item[anchor]})
            assert result["ids"]==item["expected"], (k,result["ids"],item["expected"])
            if "weights" in result:
                for view in item["views"]:
                    if view["view"] in result["ids"]:
                        np.testing.assert_allclose(result["weights"][view["view"]],view["weight_balanced"],rtol=0,atol=1e-12)
            out[k]=result
        # Exercise actual T10 pixel quality on the same frozen image, not only saved metadata.
        center=np.load(root/"INITIAL.npz")["V"].mean(0)
        q=quality_features(sample,center)
        old=next(v for v in f["selection_015"]["views"]if v["view"]==f["sample_view"])
        for key in ["sharpness","mask_complete_proxy","thin_structure_visibility_proxy","Ring_free_fraction","direction"]:
            np.testing.assert_allclose(q[key],old[key],atol=1e-10,rtol=0)
        mx=Path(f["max_root"]);j=lambda p:json.loads(p.read_text())
        va=np.load(mx/"selection_verified/G01_VISIBILITY.npz")
        pr=np.load(mx/"selection_verified/G01_PROXY.npz")
        pool=j(mx/"config/G01_FINAL_CAMERA_POOL.json");by={v["id"]:v for v in pool}
        vs=[by[str(i)]for i in va["candidate_ids"]]
        ranked=j(mx/"selection_verified/G01_SELECTION.json")["ranked"]
        vs, visible, duplicate_audit=collapse_exact_duplicates(vs,va["visible"])
        cov=select_views(vs,"max_coverage",max_views=36,visibility=visible,weights=pr["weight_mm2"])
        cov["legacy_duplicate_audit"]=duplicate_audit
        assert cov["ids"]==[r["id"]for r in ranked]
        for actual,expected in zip(cov["ranked"],ranked):
            for key in ["marginal_mm2","cumulative_mm2","proxy_total_mm2","min_direction_to_selected_deg"]:
                np.testing.assert_allclose(actual[key],expected[key],atol=1e-8,rtol=0)
        out["max_coverage"]=cov
        sup=json.loads(Path(fixture).with_name("support_fixture.json").read_text())
        verify_assets(sup["assets"])
        vv=sup["views"];target=vv[0]
        def features(v):
            return dict(np.load(mx/"features"/(v["id"]+".npz")))
        with tempfile.TemporaryDirectory(prefix="harness_support_") as cache:
            support=select_views(vv,"hero_support",max_views=3,target=target,features=features,K=sup["K"],cache_root=cache)
            assert support["ids"]==sup["expected_ids"]
            # Scores are independently recomputed from cached real SIFT descriptors/poses, no pair-cache replay.
            for actual in support["candidates"]:
                expected=next(s for s in sup["expected_pairs"]if s["id"]==actual["id"])
                np.testing.assert_allclose(actual["score"],expected["score"],atol=1e-8,rtol=0)
        out["hero_support_subset"]=support
        return dict(results=out, ids_tolerance="exact", weights_tolerance=1e-12, proxy_area_tolerance_mm2=1e-8,
                    quality_tolerance=1e-10, support_scope="one real target and its three frozen supports; not whole-pool support qualification")
    renderer_holder={}
    def renderer():
        import torch
        from ring_first_3d.rendering.pytorch3d_renderer import MetricRenderer
        from ring_first_3d.contracts.coordinates import project
        if not torch.cuda.is_available():raise FileNotFoundError("No CUDA GPU; renderer NOT_EVALUABLE")
        torch.set_num_threads(2)
        obj=MetricRenderer(f["real_case_root"],f["case"]);c=obj.case;renderer_holder["obj"]=obj
        V=obj.namespace["tensor"](c.V.copy());V.requires_grad_(True)
        out=obj.render(f["sample_view"],V);alpha=out["alpha"];r=ref["renderer"]
        np.testing.assert_allclose(float(out["loss"].detach()),r["loss"],atol=1e-7,rtol=0)
        for value,key in [(float(alpha.sum().detach()),"alpha_sum"),(float((alpha**2).sum().detach()),"alpha_square_sum")]:
            np.testing.assert_allclose(value,r[key],atol=.005,rtol=0)
        assert float(out["weights"].sum())==r["weights_sum"]
        assert float(out["visibility"].sum())==r["visible"]
        assert not out["visibility"].requires_grad, "Detached visibility contract violated"
        out["loss"].backward()
        assert V.grad is not None and torch.isfinite(V.grad).all() and float(V.grad.norm())>0
        d=c.views[f["sample_view"]]
        native,z=project(c.V,d["K"],d["T"])
        screen=d["cam"].transform_points_screen(obj.namespace["tensor"]((c.V-c.center)/c.scale)[None])[0,:,:2].detach().cpu().numpy()
        expected=(native+.5)*.5
        error=float(abs(screen-expected).max());assert error<.001,error
        return dict(device=torch.cuda.get_device_name(), source="fixed metric Body/Ring/c2w/K native pack",input_views=len(c.views),rendered_views=1,
                    loss=float(out["loss"].detach()),alpha_sum=float(alpha.sum().detach()),gradient_norm=float(V.grad.norm()),
                    detached_visibility=True,projection_max_abs_px=error,projection_tolerance_px=.001,
                    loss_tolerance=1e-7,alpha_sum_tolerance=.005,alpha_sha256=hashlib.sha256(alpha.detach().cpu().numpy().tobytes()).hexdigest())
    def compatibility():
        from types import SimpleNamespace
        import torch
        obj=renderer_holder["obj"];c=obj.case
        contour=obj.contour_loss();V=obj.namespace["tensor"](c.V.copy(),torch.float64);V.requires_grad_(True)
        loss,info=contour(V,f["sample_view"])
        assert torch.isfinite(loss) and info["contour_samples"]>0
        loss.backward();assert V.grad is not None and torch.isfinite(V.grad).all()
        chart=SimpleNamespace(plane=np.array([0.,0,1,0]),tau=.01,D=float(np.ptp(c.V,axis=0).max()),cap=False,total_trust_D=.25)
        guard=obj.geometry_guard(chart)
        why,inspection,aux=guard.inspect(c.V,c.V)
        assert np.isfinite(inspection["max_step_mm"])
        moved=c.V.copy();moved[:,0]+=.02
        rejected,_,_=guard.inspect(moved,c.V)
        assert "STEP_TRUST" in rejected
        return dict(contour_loss=float(loss.detach()), contour_info=info, guard_noop_reasons=why,
                    guard_initial_self=guard.initial_self, guard_step_rejected=rejected,
                    scope="Compatibility calls and finite gradients; no optimizer migration or scientific geometry acceptance")
    tests=[timed_test("DXY_real_official",dxy),timed_test("view_selection_frozen",selection),timed_test("renderer_real_metric",renderer)]
    if "obj" in renderer_holder:tests.append(timed_test("contour_guard_compatibility",compatibility))
    return dict(status="PASS" if len(tests)==4 and all(t["status"]=="PASS"for t in tests) else "FAIL_OR_NOT_EVALUABLE",
                fixture_SHA256=sha256(fixture),reference_SHA256=sha256(reference_path),tests=tests,
                GT_read=False,history_prediction_fallback=0)


if __name__ == "__main__":
    a=args("Real DXY/view selection/metric renderer smoke tests")
    result=run(a.fixture,a.dxy_root);emit(result,a.output)
    raise SystemExit(0 if result["status"]=="PASS" else 1)
