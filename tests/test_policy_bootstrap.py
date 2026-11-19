"""Policy/control-flow tests use test doubles only at the expensive handler boundary.

Real integration is separately executed through the public CLI and recorded.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml
from ring_first_3d.policy.contracts import ROOT, PolicyError, load_task, verify_task, digest, MODULES
from ring_first_3d.policy.runner import run_stage, accept, writer
from ring_first_3d.policy.artifacts import read_state, write_json
from ring_first_3d.policy.memory import registry

sys.path.insert(0,str(ROOT/"tools/research"))
from policy import make_task


class PolicyCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"TASK.yaml"
        make_task("TASK-POLICY-REGRESSION-001",self.path)
        self.raw=yaml.safe_load(self.path.read_text())
        self.raw["output_root"]=str(Path(self.tmp.name)/"experiments/TASK-POLICY-REGRESSION-001/runs")
        self.save()

    def save(self):
        self.path.write_text(yaml.safe_dump(self.raw))
        return load_task(self.path)

    def reject(self,code,operation):
        with self.assertRaises(PolicyError)as cm:operation()
        self.assertEqual(cm.exception.code,code)


class ContractTests(PolicyCase):

    def test_valid_existing_fixture_contract(self):
        info=verify_task(self.save());self.assertEqual(info["verified_assets"],233)
        self.assertEqual(set(info["module_contracts"]),set(MODULES))

    def test_wrong_units(self):
        self.raw["variables"]["geometry_unit"]="m"
        self.reject("COORDINATES",self.save)

    def test_wrong_camera_and_depth(self):
        for key,value in [("camera_transform","opencv_w2c"),("depth_convention","ray_range"),("pixel_coordinates","resized_px")]:
            previous=self.raw["variables"][key];self.raw["variables"][key]=value
            self.reject("COORDINATES",self.save);self.raw["variables"][key]=previous

    def test_SHA_mismatch(self):
        self.raw["inputs"]["fixture"]["sha256"]="0"*64
        self.reject("SOURCE_SHA",lambda:verify_task(self.save()))

    def test_fit_holdout_overlap(self):
        self.raw["split"]["HOLDOUT"]=["FIT"]
        self.reject("DATA_ISOLATION",self.save)

    def test_actual_role_mismatch(self):
        self.raw["split"]["HOLDOUT"]=["INVENTED_ROLE"]
        self.reject("DATA_ISOLATION",lambda:verify_task(self.save()))

    def test_GT_leak(self):
        self.raw["split"]["GT"]=["/tmp/ground_truth.blend"]
        self.reject("GT_LEAK",self.save)

    def test_duplicate_YAML_and_unknown_command(self):
        self.path.write_text(self.path.read_text()+"schema: 1\n")
        self.reject("YAML_KEYS",lambda:load_task(self.path))
        self.raw["command"]="python arbitrary_algorithm.py"
        self.reject("SCHEMA",self.save)

    def test_unsafe_YAML_tag(self):
        self.path.write_text('!!python/object/apply:os.system ["touch /tmp/policy-must-not-execute"]')
        self.reject("YAML",lambda:load_task(self.path))

    def test_unapproved_stage_and_weakened_acceptance(self):
        self.raw["authorization"]["stages"]=["smoke"]
        self.reject("AUTHORIZATION",self.save)
        self.raw["authorization"]["stages"]=["preflight"]
        self.raw["acceptance"]["require_visualization"]=False
        self.reject("ACCEPTANCE",self.save)

    def test_protected_output(self):
        self.raw["output_root"]="/home/liu/polyp_research/experiments/TASK-POLICY-REGRESSION-001/runs"
        self.reject("PROTECTED_OUTPUT",self.save)

    def test_module_dependency_and_unknown_module(self):
        self.raw["modules"]=["T31"]
        self.reject("MODULE_DEPENDENCY",self.save)
        self.raw["modules"]=["UNREGISTERED"]
        self.reject("MODULE",self.save)

    def test_source_contract_scope(self):
        self.raw["modules"]=["T24"]
        info=verify_task(self.save());self.assertEqual(list(info["module_contracts"]),["T24"])

    def test_unreviewed_rule_promotion(self):
        data=copy.deepcopy(registry());data["failures"][0]["rule_status"]="reviewed_permanent"
        p=Path(self.tmp.name)/"memory.json";p.write_text(json.dumps(data))
        self.reject("UNREVIEWED_RULE",lambda:registry(p))

    def test_worker_IO_guard_and_dirfd_cleanup(self):
        import subprocess
        attempt=Path(self.tmp.name)/"worker";attempt.mkdir()
        script='''import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from _policy_worker import install_io_guard
from ring_first_3d.policy.contracts import PolicyError
attempt=Path(sys.argv[2]);install_io_guard(attempt)
with tempfile.TemporaryDirectory(dir=attempt) as d:Path(d,"asset").write_text("temporary")
codes=[]
for target,mode in [(attempt/"hidden.blend","r"),(attempt.parent/"outside.txt","w")]:
 try:target.open(mode)
 except PolicyError as e:codes.append(e.code)
print(json.dumps(codes))
'''
        p=subprocess.run([sys.executable,"-c",script,str(ROOT/"tools/research"),str(attempt)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),["GT_LEAK","WRITE_ISOLATION"])


class RunnerTests(PolicyCase):
    def identity(self,task):
        fingerprint={"task":task,"test_double":"state machine only, not real API evidence"}
        return dict(status="PASS",fingerprint=fingerprint,freeze_sha256=digest(fingerprint))

    def invoke(self,task,root,stage,handler=None):
        def success(stage,task,pending,timeout,freeze):
            result=dict(status="PASS",test_double=True)
            write_json(pending/"payload.json",result)
            return result
        with patch("ring_first_3d.policy.runner.verify_task",side_effect=self.identity),patch("ring_first_3d.policy.runner.execute",side_effect=handler or success):
            return run_stage(task,root,stage)

    def accepted(self,task,root):
        with patch("ring_first_3d.policy.runner.verify_task",side_effect=self.identity):return accept(task,root)

    def test_unauthorized_next_stage(self):
        self.raw["authorization"]["stages"]=["preflight"];task=self.save();root=Path(task["output_root"])/"test"
        self.invoke(task,root,"preflight")
        self.reject("UNAUTHORIZED_STAGE",lambda:self.invoke(task,root,"contracts"))
        self.assertTrue((root/"visualization/index.html").is_file())
        self.assertEqual(len(json.loads((root/"failures.json").read_text())["failures"]),1)

    def test_failed_gate_not_bypassed_and_resume(self):
        task=self.save();root=Path(task["output_root"])/"test"
        self.invoke(task,root,"preflight")
        first=read_state(root)["attempts"][0];old_hash=first["sha256"]
        def fail(*args):raise PolicyError("GATE_FAILED","Intentional unit fault at existing handler boundary")
        self.reject("GATE_FAILED",lambda:self.invoke(task,root,"contracts",fail))
        self.reject("PREDECESSOR_FAILED",lambda:self.invoke(task,root,"smoke"))
        self.invoke(task,root,"contracts");self.invoke(task,root,"smoke");self.invoke(task,root,"artifacts")
        self.assertTrue(self.accepted(task,root)["accepted"])
        self.assertEqual(read_state(root)["attempts"][0]["sha256"],old_hash)
        self.assertTrue(self.invoke(task,root,"preflight")["resumed"])
        self.assertEqual(len(read_state(root)["attempts"]),6)

    def test_missing_visualization_and_artifact_tamper(self):
        task=self.save();root=Path(task["output_root"])/"test"
        for stage in ["preflight","contracts","smoke","artifacts"]:self.invoke(task,root,stage)
        (root/"visualization").unlink()
        self.reject("ARTIFACT_MISSING",lambda:self.accepted(task,root))
        (root/"visualization").symlink_to("current/visualization")
        (root/"metrics.json").write_text("{}")
        self.reject("ARTIFACT_SHA",lambda:self.accepted(task,root))

    def test_frozen_parameters_must_not_change_on_resume(self):
        task=self.save();root=Path(task["output_root"])/"test";self.invoke(task,root,"preflight")
        task["variables"]["parameters"]["changed"]=1
        self.reject("FREEZE_DRIFT",lambda:self.invoke(task,root,"contracts"))

    def test_budget_exhaustion_stops_handler(self):
        self.raw["budget"]["max_output_bytes"]=10;task=self.save();root=Path(task["output_root"])/"test"
        self.reject("BUDGET_OUTPUT",lambda:self.invoke(task,root,"preflight"))
        self.assertEqual(read_state(root)["status"],"INCOMPLETE_OR_FAILED")

    def test_run_lock_rejects_concurrent_writer(self):
        task=self.save();root=Path(task["output_root"])/"test";root.mkdir(parents=True)
        with writer(root):
            self.reject("RUN_BUSY",lambda:self.invoke(task,root,"preflight"))

    def test_recover_interrupted_attempt_without_partial_PASS(self):
        task=self.save();root=Path(task["output_root"])/"test";self.invoke(task,root,"preflight")
        state=read_state(root);pending=root/"attempts/.pending-interrupted";pending.mkdir()
        request=dict(attempt_id="0002-contracts-interrupted",stage="contracts",freeze_sha256=state["freeze_sha256"],timeout_seconds=1.,started_UTC=0)
        write_json(pending/"request.json",request);write_json(pending/"payload.json",dict(status="PASS"))
        self.invoke(task,root,"contracts")
        failures=json.loads((root/"failures.json").read_text())["failures"]
        self.assertEqual(failures[0]["status"],"INTERRUPTED")
        self.assertEqual(len(read_state(root)["attempts"]),3)

    def test_partial_result_and_atomic_no_overwrite(self):
        task=self.save();root=Path(task["output_root"])/"test";self.invoke(task,root,"preflight")
        state=read_state(root);pending=root/"attempts/.pending-partial";pending.mkdir()
        req=dict(attempt_id="0002-contracts-partial",stage="contracts",freeze_sha256=state["freeze_sha256"],timeout_seconds=1.,started_UTC=0)
        write_json(pending/"request.json",req);(pending/"result.json").write_text('{"status":"PASS"')
        self.invoke(task,root,"contracts")
        self.assertTrue((root/"attempts/0002-contracts-partial/partial_result.json").is_file())
        with self.assertRaises(FileExistsError):write_json(root/"FREEZE.json",dict(overwrite=True))

    def test_timeout_kills_real_worker_process(self):
        import subprocess
        from ring_first_3d.policy.runner import execute
        task=self.save();root=Path(task["output_root"])/"test";self.invoke(task,root,"preflight")
        pending=root/"attempts/.timeout-test";pending.mkdir();children=[]
        real_popen=subprocess.Popen
        def record(*a,**kw):
            p=real_popen(*a,**kw);children.append(p);return p
        with patch("ring_first_3d.policy.runner.subprocess.Popen",side_effect=record):
            self.reject("BUDGET_TIMEOUT",lambda:execute("preflight",task,pending,.001,root/"FREEZE.json"))
        self.assertEqual(len(children),1)
        self.assertIsNotNone(children[0].poll())


if __name__=="__main__":unittest.main()
