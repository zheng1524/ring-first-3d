"""Recompute A2 only into a NEW task-local runtime directory."""
from pathlib import Path
import argparse,os,hashlib,json

def main():
    root=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();out=Path(args.output).resolve()
    assert out.is_relative_to(root/'runtime') and not out.exists(), 'NEW_TASK_RUNTIME_DIRECTORY_REQUIRED'
    (out/'config').mkdir(parents=True)
    for name in ['A2_PREREGISTERED.json','BEFORE_CANDIDATES.json']:(out/'config'/name).write_bytes((root/'config'/name).read_bytes())
    os.environ['RING_A2_OUTPUT']=str(out)
    from discover import main as discover
    from cleanup import main as cleanup
    from validate_inputs import main as validate
    discover();cleanup();validate()
    from common import save,sha
    names=['CANDIDATE_DISCOVERY_ALL_FLAGS.csv','CLEANUP_CANDIDATES.csv','PROJECTIVE_CLEANUP_EVIDENCE.csv','PROJECTIVE_CLEANUP_DECISIONS.csv','FINAL_BOUNDARY_POINTS.csv','INCREMENTAL_GEOMETRY_VALIDATION.csv','RESAMPLING_FAILURE_DIAGNOSIS.csv']
    rows=[dict(file=n,original_sha256=sha(root/n),replay_sha256=sha(out/n),byte_identical=sha(root/n)==sha(out/n)) for n in names]
    save('REPLAY_VERIFY.json',dict(files=rows,all_identical=all(r['byte_identical'] for r in rows),neural_forward=0,GPU=0,prior_outputs_overwritten=False))
    assert all(r['byte_identical'] for r in rows),rows
    print('A2_REPLAY',len(rows),'CSV byte-identical',flush=True)

if __name__=='__main__':main()
