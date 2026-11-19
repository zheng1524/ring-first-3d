import json
from pathlib import Path
import numpy as np
from .._legacy import definitions, main_loop_block, line_statements
from ..contracts.identities import validate_split


def _unit(x):
    x = np.asarray(x, float)
    if np.linalg.norm(x) == 0:
        raise ValueError("Zero camera direction")
    return x / np.linalg.norm(x)


def _angle(a, b):
    return float(np.degrees(np.arccos(np.clip(_unit(a) @ _unit(b), -1, 1))))


def quality_features(arrays, center_mm):
    """T10 pixel-derived quality, original AST; caller supplies audited RGB/labels/T."""
    import cv2
    from scipy.ndimage import distance_transform_edt
    ns = dict(np=np, cv2=cv2, distance_transform_edt=distance_transform_edt,
              a=arrays, center=np.asarray(center_mm), v={}, qualities=[])
    definitions("T10", ["skeleton_proxy"], ns)
    # Skip only the historical np.load; use caller-provided arrays, no path writes.
    line_statements("T10", 28, ns, skip=1)
    return dict(sharpness=ns["sharp"], mask_complete_proxy=1-ns["border"],
                thin_structure_visibility_proxy=ns["thin"], Ring_free_fraction=ns["ringfree"],
                direction=ns["D"].tolist())


def collapse_exact_duplicates(views, visibility):
    """Explicit legacy-pool migration: identical metadata AND visibility only.

    Selection itself still rejects duplicate IDs. Caller must record this audit.
    Conflicting observations with the same ID are never silently resolved.
    """
    keep, seen, audit = [], {}, []
    visibility = np.asarray(visibility)
    if len(visibility) != len(views):
        raise ValueError("Visibility/pool length mismatch")
    for i, v in enumerate(views):
        if v["id"] not in seen:
            seen[v["id"]] = i;keep.append(i)
            continue
        j = seen[v["id"]]
        if v != views[j] or not np.array_equal(visibility[i], visibility[j]):
            raise ValueError("Conflicting duplicate identity: " + v["id"])
        audit.append(dict(id=v["id"], retained_index=j, redundant_index=i,
                          criterion="all metadata equal and visibility array exactly equal"))
    return [views[i] for i in keep], visibility[keep], audit


def select_views(views, strategy="quality_diversity", max_views=8, *, baseline_ids=(),
                 mandatory_ids=(), holdout_ids=(), visibility=None, weights=None,
                 source_filter=None, target=None, features=None, K=None, cache_root=None):
    views = [dict(v, id=v.get("id", v.get("view"))) for v in views]
    ids = validate_split(views, holdout_ids)
    if not views or not isinstance(max_views, int) or max_views < 1:
        raise ValueError("Nonempty FIT pool and positive integer max_views required")
    by = {v["id"]: v for v in views}
    if not set(baseline_ids) <= set(ids) or not set(mandatory_ids) <= set(ids):
        raise ValueError("Anchors/baseline must belong to FIT pool")
    if len(set(baseline_ids)) != len(baseline_ids) or len(set(mandatory_ids)) != len(mandatory_ids):
        raise ValueError("Duplicate anchors")
    ns = dict(np=np, fit=views, unit=_unit, angle=_angle)
    if strategy in ("quality_diversity", "direction_quota"):
        if max_views > 8:
            raise ValueError("T10/T11 historical cap is 8")
        for v in views:
            if not np.isclose(np.linalg.norm(v["direction"]), 1.):
                raise ValueError("Unit directions required")
        if len({v["video"] for v in views}) != 1:
            raise ValueError("T10/T11 require a single-video pool")
        quality = {v["id"]: v for v in views}
        if strategy == "quality_diversity":
            if not baseline_ids or len(baseline_ids) > max_views:
                raise ValueError("T10 requires a nonempty baseline within requested limit")
            ns.update(baseline=list(baseline_ids), qualities=[[
                np.log1p(v["sharpness"]), v["mask_complete_proxy"],
                v["thin_structure_visibility_proxy"], v["Ring_free_fraction"]] for v in views])
            main_loop_block("T10", 30, 32, ns)
        else:
            if len(mandatory_ids) > max_views or any("direction_block" not in v for v in views):
                raise ValueError("T11 requires explicit partitions and fitting anchors")
            ns.update(mandatory=list(mandatory_ids), quality=quality)
            main_loop_block("T11", 47, 59, ns)
        chosen = ns["chosen"][:max_views]
        out = dict(strategy=strategy, ids=chosen, historical_cap=8, truncation="prefix only")
        if strategy == "direction_quota":
            fn = definitions("T11", ["weights"], dict(np=np))["weights"]
            out["weights"] = fn(views, chosen)
        return out
    if strategy == "max_coverage":
        vis, weight = np.asarray(visibility), np.asarray(weights)
        if vis.dtype != bool or vis.shape != (len(views), len(weight)) or not np.isfinite(weight).all() or (weight < 0).any():
            raise ValueError("Aligned boolean visibility and nonnegative finite source-tagged weights required")
        ns = definitions("T12", ["greedy"], ns)
        rank, rows = ns["greedy"](views, vis, weight, source_filter)
        return dict(strategy=strategy, ids=[ids[i] for i in rank[:max_views]],
                    ranked=rows[:max_views], historical_cap=36,
                    area_identity="source-tagged proxy, not true anatomical surface area")
    if strategy == "hero_support":
        if target is None or target["id"] not in ids or features is None or K is None or cache_root is None or max_views > 3:
            raise ValueError("T13 requires FIT target, feature provider, native K, writable task cache; cap 3")
        root = Path(cache_root).resolve()
        def save(name, obj):
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(obj, indent=2) + "\n")
        def stats(x):
            x = np.abs(np.asarray(x)); x = x[np.isfinite(x)]
            return dict(N=len(x), MAE=float(x.mean()), median=float(np.median(x)), p95=float(np.quantile(x, .95)), maximum=float(x.max()))
        import cv2
        ns.update(N=root, K0=np.asarray(K), features=features, BF=cv2.BFMatcher(cv2.NORM_L2),
                  load=lambda p: json.loads(Path(p).read_text()), save=save, stats=stats)
        definitions("rgb", ["mutual"], ns)
        definitions("T13", ["support_pairs"], ns)
        cand = ns["support_pairs"](views, by[target["id"]])
        # The literal three-support diversification block is executed from T13.main.
        ns.update(vs=views, cand=cand, chosen=[])
        main_loop_block("T13", 91, 96, ns)
        return dict(strategy=strategy, ids=[s["id"] for s in ns["chosen"][:max_views]], candidates=cand)
    raise ValueError("Unknown historical strategy: " + strategy)
