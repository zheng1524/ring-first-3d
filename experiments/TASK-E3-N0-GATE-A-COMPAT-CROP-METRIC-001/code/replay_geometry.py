"""Safe reproduction into a NEW task-local directory; no model forward.
Execute exact existing entrypoints via bound IO, without altering old outputs.
"""
from crop import *
import shutil

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--include-authorized-cleanup',action='store_true');args=parser.parse_args();out=(R/args.output).resolve();assert out.is_relative_to(R/'runtime')and not out.exists(),'use a NEW directory under this task runtime/'
    for d in ['config','code','local_results','figures']:(out/d).mkdir(parents=True,exist_ok=True)
    for name in ['GATE_A_PREREGISTERED.json','BEFORE_FORMAL_CALCULATION.json']:(out/'config'/name).write_bytes((R/'config'/name).read_bytes())
    for p in(R/'code').glob('*.py'):(out/'code'/p.name).write_bytes(p.read_bytes())
    ns=dict(globals(),R=out,ROOT=out,V=out/'derived_projective_v1',save=lambda p,data:save(out/p,data),table=lambda p,rows:table(out/p,rows))
    def run(script,names):
        extract(R/'code'/script,names,ns);ns['main']()
    run('build_crops.py',['main']);run('cross_view.py',['main']);run('metric_domain.py',['make_domain','main'])
    compare=['CROP_GEOMETRY_TESTS.csv','CROSS_VIEW_PROJECTION_VALIDATION.csv','MODEL_DOMAIN_DIAGNOSTICS.csv']
    if args.include_authorized_cleanup:
        (out/'HUMAN_REVIEW_POINTS.csv').write_bytes((R/'HUMAN_REVIEW_POINTS.csv').read_bytes());(out/'INFERENCE_ONLY_SCHEMA.json').write_bytes((R/'config/ORIGINAL_INFERENCE_ONLY_SCHEMA.json').read_bytes())
        run('projective_cleanup.py',['preregister','main']);run('recheck_cleaned_inputs.py',['derived_native','bind_run','main']);run('finish_scope_update.py',['cross_source_with_all_original_identities','prepare_candidate','main']);compare+=['PROJECTIVE_CLEANUP_EVIDENCE.csv','PROJECTIVE_CLEANUP_DECISIONS.csv','PROJECTIVE_CLEANUP_BEFORE_AFTER.csv','POST_REVIEW_INPUT_CONTRACTS.csv','derived_projective_v1/CROP_GEOMETRY_TESTS.csv','derived_projective_v1/CROSS_VIEW_PROJECTION_VALIDATION.csv']
    results=[]
    for name in compare:
        same=(out/name).read_bytes()==(R/name).read_bytes();results.append(dict(file=name,identical_bytes=same));assert same,('REPLAY_DIFFERENCE',name)
    save(out/'REPLAY_VERIFY.json',dict(status='PASS',comparisons=results,original_outputs_unchanged=True,neural_forward=0,GPU=0,cleanup_replay_is_exact_same_rule_not_new_search=args.include_authorized_cleanup))
    print('SAFE_REPLAY_VERIFIED',out,len(compare),'identical CSV files',flush=True)
if __name__=='__main__':main()
