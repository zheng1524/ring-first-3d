"""Replay final user-amended A3 into a fresh task-local directory."""
from pathlib import Path
import argparse,os

def main():
    root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output).resolve()
    assert out.is_relative_to(root/'runtime') and not out.exists(),'FRESH_TASK_RUNTIME_ONLY'
    (out/'config').mkdir(parents=True)
    # The reused V4 analysis binds source lookup to its isolated output root.
    # Copy this exact small audited source; do not copy data or execute a new algorithm.
    (out/'code').mkdir();(out/'code/analyze.py').write_bytes((root/'code/analyze.py').read_bytes())
    for name in ['A3_PREREGISTERED.json','BEFORE_RESULTS.json','USER_BACKGROUND_OVERRIDE.json','AMENDMENT_BEFORE_RESULTS.json']:(out/'config'/name).write_bytes((root/'config'/name).read_bytes())
    os.environ['RING_A3_OUTPUT']=str(out)
    from mask_cleanup import main as cleanup
    from analyze import main as analyze
    cleanup();analyze()
    from v4 import main as final_v4
    final_v4()
    from common import save,sha
    names=['CANDIDATE_DISTANCE_AUDIT.csv','CLEANUP_DECISIONS.csv','SOURCE_VERSION_RETENTION.csv','SOURCE_VERSION_METRICS.csv','GEOMETRY_VALIDATION.csv','REGION_RETENTION.csv','COMPONENT_RETENTION.csv','NEW_GAP_STATISTICS.csv','FIXED_DENOMINATOR_DEPTH_JUMPS.csv','FIXED_DEPTH_CASES.csv']
    names+=['V4_260_CANDIDATES.csv','V4_CLEANUP_DECISIONS.csv','V4_260_MULTIVIEW_EVIDENCE.csv','V4_260_MULTIVIEW_SUMMARY.csv','V4_REMAINING_ANOMALY_PROXIES.csv']
    names+=['FOUR_VERSION_'+n+'.csv'for n in ['SOURCE_VERSION_METRICS','GEOMETRY_VALIDATION','REGION_RETENTION','COMPONENT_RETENTION','NEW_GAP_STATISTICS','FIXED_DENOMINATOR_DEPTH_JUMPS','FIXED_DEPTH_CASES']]
    rows=[dict(file=n,original_sha256=sha(root/n),replay_sha256=sha(out/n),byte_identical=sha(root/n)==sha(out/n))for n in names]
    save('REPLAY_VERIFY.json',dict(files=rows,all_identical=all(r['byte_identical'] for r in rows),NNforward=0,GPU=0,no_historical_or_formal_output_overwritten=True))
    assert all(r['byte_identical'] for r in rows),rows
    print('A3_REPLAY',len(rows),'CSV byte-identical',flush=True)

if __name__=='__main__':main()
