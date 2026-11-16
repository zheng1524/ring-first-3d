"""Small strict TASK.yaml contract; no commands, eval, YAML tags or silent defaults."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import yaml
from . import VERSION
from .._legacy import LOCK, ROOT, source
from ..adapters.dxy import verify_dxy
from ..contracts.identities import sha256, verify_assets

STAGES = ("preflight", "contracts", "smoke", "artifacts")
PROTECTED = (Path("/home/liu/polyp_research"), Path("/home/liu/new-polyp-dxy"))
MODULES = {
    "T01": dict(sources=[], requires=[], units="native_image_px"),
    "T03": dict(sources=["T03"], requires=["T01"], units="native_image_px"),
    "T04": dict(sources=["T04"], requires=["T03"], units="native_image_px"),
    "T10": dict(sources=["T10"], requires=[], units="native_image_px"),
    "T11": dict(sources=["T11"], requires=["T10"], units="mm"),
    "T12": dict(sources=["T12"], requires=[], units="mm"),
    "T13": dict(sources=["T13", "rgb"], requires=["T12"], units="native_image_px"),
    "T24": dict(sources=["T24", "common"], requires=[], units="mm"),
    "T31": dict(sources=["T31", "common"], requires=["T24"], units="mm"),
    "T34": dict(sources=["T34", "common"], requires=["T24"], units="mm"),
}


class PolicyError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise PolicyError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class StrictLoader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(isinstance(key, str) and key not in result, "YAML_KEYS", "Keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def fields(value, names, context):
    require(type(value) is dict and set(value) == set(names.split()), "SCHEMA", context + " requires exactly: " + names)


def text(value):
    return type(value) is str and bool(value.strip())


def write_allowed(path):
    p = Path(path).absolute()
    require(p == p.resolve(), "OUTPUT_SYMLINK", "Output root must not traverse symbolic links")
    require(not any(p == r or r in p.parents for r in PROTECTED), "PROTECTED_OUTPUT", str(p))
    return p


def load_task(path):
    path = Path(path).resolve()
    require(path.stat().st_size <= 65536, "SCHEMA", "TASK.yaml exceeds 64 KiB")
    try:
        require(not any(isinstance(token, yaml.tokens.AliasToken) for token in yaml.scan(path.read_text())), "YAML", "Aliases are not accepted in task contracts")
        task = yaml.load(path.read_text(), Loader=StrictLoader)
    except (yaml.YAMLError, RecursionError) as e:
        raise PolicyError("YAML", str(e)) from e
    fields(task, "schema task_id goal modules variables inputs split authorization acceptance budget stop output_root", "TASK")
    require(task["schema"] == 1 and type(task["schema"]) is int, "SCHEMA", "Only schema 1 supported")
    require(text(task["task_id"]) and re.fullmatch(r"TASK-[A-Z0-9][A-Z0-9-]{2,100}", task["task_id"]), "SCHEMA", "Invalid task_id")
    require(text(task["goal"]), "SCHEMA", "Goal required")
    ids = task["modules"]
    require(type(ids) is list and ids and all(type(x) is str for x in ids) and len(set(ids)) == len(ids) and set(ids) <= MODULES.keys(), "MODULE", "Unknown/duplicate/empty module IDs")
    for mid in ids:
        require(set(MODULES[mid]["requires"]) <= set(ids), "MODULE_DEPENDENCY", mid)
    fields(task["variables"], "geometry_unit pixel_coordinates camera_transform depth_convention parameters", "variables")
    expected = dict(geometry_unit="mm", pixel_coordinates="native_image_px", camera_transform="opencv_c2w", depth_convention="axial_z")
    for k, v in expected.items():
        require(task["variables"][k] == v, "COORDINATES", k + " must be " + v)
    require(type(task["variables"]["parameters"]) is dict, "SCHEMA", "Frozen parameters must be a mapping")
    inp = task["inputs"]
    fields(inp, "fixture support reference source_lock dxy_root evidence", "inputs")
    for key in ("fixture", "support", "reference", "source_lock", "evidence"):
        fields(inp[key], "path sha256", "inputs." + key)
        require(text(inp[key]["path"]) and type(inp[key]["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", inp[key]["sha256"]), "SCHEMA", key + " path/hash")
        p = Path(inp[key]["path"])
        inp[key]["path"] = str((path.parent / p).resolve() if not p.is_absolute() else p.resolve())
    require(text(inp["dxy_root"]), "SCHEMA", "dxy_root required")
    inp["dxy_root"] = str((path.parent / inp["dxy_root"]).resolve())
    split = task["split"]
    fields(split, "manifest FIT HOLDOUT GT access", "split")
    fields(split["manifest"], "path sha256", "split.manifest")
    require(text(split["manifest"]["path"]) and type(split["manifest"]["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", split["manifest"]["sha256"]), "SCHEMA", "Camera role manifest path/hash")
    split["manifest"]["path"] = str((path.parent / split["manifest"]["path"]).resolve())
    for key in ["FIT", "HOLDOUT", "GT"]:
        require(type(split[key]) is list and all(text(x) for x in split[key]) and len(set(split[key])) == len(split[key]), "DATA_ISOLATION", key)
    require(split["FIT"] == ["FIT"] and split["HOLDOUT"] and not set(split["FIT"]) & set(split["HOLDOUT"]), "DATA_ISOLATION", "Use explicit, disjoint frozen camera roles")
    require(not split["GT"] and split["access"] == "verification_only_no_GT", "GT_LEAK", "This runner never accepts GT or scientific evaluation handlers")
    auth = task["authorization"]
    fields(auth, "approved_by reference stages", "authorization")
    require(auth["approved_by"] == "user" and text(auth["reference"]), "AUTHORIZATION", "Explicit user task reference required")
    require(type(auth["stages"]) is list and auth["stages"] and auth["stages"] == list(STAGES[:len(auth["stages"])]), "AUTHORIZATION", "Authorized stages must be an ordered prefix")
    # Existing 0.1 Preflight/Smoke are audited, indivisible integration bundles.
    # A TASK may request subset source checking, but must declare their full
    # module scope before executing the bundled APIs. No hidden extra modules.
    fields(task["acceptance"], "required_stages min_contract_tests require_visualization require_failure_log", "acceptance")
    ac = task["acceptance"]
    require(ac["required_stages"] == list(STAGES) and type(ac["min_contract_tests"]) is int and ac["min_contract_tests"] >= 11 and ac["require_visualization"] is True and ac["require_failure_log"] is True, "ACCEPTANCE", "Cannot weaken required gates or artifacts")
    fields(task["budget"], "max_seconds stage_timeout_seconds max_attempts_per_stage max_output_bytes", "budget")
    for key, value in task["budget"].items():
        require(type(value) in (int, float) and math.isfinite(value) and value > 0, "BUDGET", key)
    for key in ["max_attempts_per_stage", "max_output_bytes"]:
        require(type(task["budget"][key]) is int, "BUDGET", key + " must be integer")
    require(task["budget"]["stage_timeout_seconds"] <= task["budget"]["max_seconds"], "BUDGET", "Stage timeout exceeds total budget")
    require(task["stop"] == ["gate_failure", "input_drift", "budget_exceeded"], "STOP_POLICY", "All mandatory stops required")
    require(text(task["output_root"]), "SCHEMA", "output_root required")
    out = write_allowed(path.parent / task["output_root"])
    require(out.parts[-3:] == ("experiments", task["task_id"], "runs"), "OUTPUT_SCOPE", "Use isolated experiments/TASK-ID/runs")
    task["output_root"] = str(out)
    try:
        canonical(task)
    except (ValueError, TypeError, RecursionError) as e:
        raise PolicyError("SCHEMA", "Task must be finite JSON-compatible data") from e
    return task


def verify_task(task):
    inp = task["inputs"]
    for key in ("fixture", "support", "reference", "source_lock", "evidence"):
        rec = inp[key]
        require(Path(rec["path"]).is_file() and sha256(rec["path"]) == rec["sha256"], "SOURCE_SHA", key)
    require(Path(inp["source_lock"]["path"]).resolve() == (ROOT / "src/ring_first_3d/source_lock.json").resolve(), "SOURCE_LOCK", "Must use the executing harness source lock")
    f = json.loads(Path(inp["fixture"]["path"]).read_text())
    support = json.loads(Path(inp["support"]["path"]).read_text())
    ref = json.loads(Path(inp["reference"]["path"]).read_text())
    require(Path(inp["support"]["path"]) == Path(inp["fixture"]["path"]).with_name("support_fixture.json") and Path(inp["reference"]["path"]) == Path(inp["fixture"]["path"]).with_name("frozen_reference.json"), "INPUT_BINDING", "Existing API uses named sibling fixtures")
    require(ref["fixture_SHA256"] == inp["fixture"]["sha256"] and ref["source_lock_SHA256"] == inp["source_lock"]["sha256"], "INPUT_BINDING", "Frozen reference bindings differ")
    require(f.get("GT_read") is False and f.get("history_prediction_fallback") == 0, "GT_LEAK", "Fixture GT/fallback flags")
    verify_assets(f["assets"])
    verify_assets(support["assets"])
    meta_path = Path(f["real_case_root"]) / "inputs" / f["case"] / "CASE.json"
    split_source = task["split"]["manifest"]
    require(Path(split_source["path"]) == meta_path and sha256(meta_path) == split_source["sha256"], "DATA_ISOLATION", "Camera split manifest must be the actual frozen pack")
    meta = json.loads(meta_path.read_text())
    fit = [v["id"] for v in meta["views"] if v["role"] == "FIT"]
    held = [v["id"] for v in meta["views"] if v["role"] != "FIT"]
    require(set(task["split"]["HOLDOUT"]) == {v["role"] for v in meta["views"] if v["role"] != "FIT"} and len(set(fit+held)) == len(fit)+len(held), "DATA_ISOLATION", "TASK roles/identities must equal actual frozen cameras")
    require(meta["unit"] == task["variables"]["geometry_unit"], "COORDINATES", "Actual pack units")
    ids = task["modules"]
    relevant = sorted({key for mid in ids for key in MODULES[mid]["sources"]})
    for key in relevant:
        source(key)  # Existing hash-locked historical loader.
    if "T01" in ids:
        verify_dxy(inp["dxy_root"])
    files = {str(p.relative_to(ROOT)): sha256(p) for base in ["src/ring_first_3d", "tools/research", "tests"]
             for p in sorted((ROOT / base).rglob("*.py"))}
    files["tools/research/run.sh"] = sha256(ROOT / "tools/research/run.sh")
    files["docs/registry/FAILURE_REGISTRY.json"] = sha256(ROOT / "docs/registry/FAILURE_REGISTRY.json")
    import importlib.metadata
    import importlib.util
    import os
    versions = {}
    for name in ["numpy", "scipy", "opencv-python", "torch", "PyYAML", "scikit-image", "trimesh", "open3d", "python-fcl"]:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "UNAVAILABLE"
    spec=importlib.util.find_spec("pytorch3d")
    binary_identity={}
    if spec and spec.submodule_search_locations:
        for p in Path(next(iter(spec.submodule_search_locations))).glob("_C*.so"):
            binary_identity[str(p)]=sha256(p)
    environment={k:os.environ.get(k) for k in ["PATH","PYTHONPATH","CUDA_VISIBLE_DEVICES","RING_FIRST_SOURCE_ROOT","OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","LD_LIBRARY_PATH"]}
    fingerprint = dict(task=task, policy_version=VERSION, python=sys.version, executable=sys.executable,
                       versions=versions, implementation_sha256=files,
                       compiled_renderer_sha256=binary_identity,environment=environment,
                       source_root=str(Path(os.environ.get("RING_FIRST_SOURCE_ROOT", ROOT)).resolve()))
    return dict(status="PASS", freeze_sha256=digest(fingerprint), fingerprint=fingerprint,
                module_contracts={mid: MODULES[mid] for mid in ids}, verified_assets=len(f["assets"])+len(support["assets"]))
