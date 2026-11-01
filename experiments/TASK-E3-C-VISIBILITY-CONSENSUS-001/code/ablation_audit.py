"""Supplementary same-C0 channel-addition control; original protocol is retained."""
from run_consensus import *
def main():
    allow_manifest();freeze('BEFORE_MATCHED_C0_ADDITION_AUDIT.json');out={};checks=[];source_rows=[]
    for stage in ['REP_OBSERVERS','ALL_OBSERVERS']:
        out[stage]={}
        for sid in scene_ids():
            agg={v:Counter()for v in range(4)};n=0;sums={v:dict(S=0.,O=0.,F=0.,corrS=0.,corrO=0.,corrF=0.)for v in range(4)}
            for origin in ordered_sources(sid):
                r=[reduce(origin,stage,v,matched_support=True)for v in range(4)];n+=len(r[0]['label'])
                okay=all(np.array_equal(r[0]['support'],r[v]['support'])and np.array_equal(r[0]['rawS'],r[v]['rawS'])for v in [1,2]);checks.append(dict(stage=stage,source=origin,matched_C0_Support_V0_V1_V2_identical=okay))
                for v in range(4):
                    agg[v].update(r[v]['label'].tolist());sums[v]['S']+=r[v]['rawS'].sum();sums[v]['O']+=r[v]['rawO'].sum();sums[v]['F']+=r[v]['rawF'].sum();sums[v]['corrS']+=r[v]['normS'].sum();sums[v]['corrO']+=r[v]['normO'].sum();sums[v]['corrF']+=r[v]['normF'].sum()
                    source_rows.append(dict(stage=stage,scene=sid,source=origin,variant='V'+str(v),candidate_N=len(r[v]['label']),**dict(Counter(r[v]['label'].tolist())),mean_C0_Support_sum=float(r[v]['rawS'].mean())))
            out[stage][sid]={'V'+str(v):dict(candidate_N=n,class_counts=dict(agg[v]),raw_channel_mean={k:float(sums[v][k]/n)for k in ['S','O','F']},correlation_normalized_channel_mean={k:float(sums[v]['corr'+k]/n)for k in ['S','O','F']},all_candidates_retained_N=n)for v in range(4)}
    save('provenance/MATCHED_C0_ADDITION_AUDIT.json',dict(results=out,checks=checks,status='PASS_C0_CONSTANT'if all(c['matched_C0_Support_V0_V1_V2_identical']for c in checks)else'FAIL',
        disclosure='Post-observation ablation-control audit, no new parameter or field query. Original preregistered response/gating results preserved separately. V0-V2 hold C0 and mandatory legality constant; V1 adds occlusion, V2 adds free; V3 unchanged.',
        no_Ring_off_free_baseline='Minimum CAD/Mask legality never disabled for free; Ring-only causal contribution not isolated by V2-V3'))
    table('metrics/MATCHED_C0_SOURCE_ABLATION.csv',source_rows);ab=load(R/'V0_V3_ABLATION.json');ab['MATCHED_C0_CHANNEL_ADDITION_AUDIT']=dict(results=out,disclosure='supplementary fixed-channel audit; not a newly preregistered scientific hypothesis, no retuning and no replacement of original results');save('V0_V3_ABLATION.json',ab)
    assert all(c['matched_C0_Support_V0_V1_V2_identical']for c in checks);print('MATCHED_C0_ADDITION_AUDIT_COMPLETE',len(checks),flush=True)
if __name__=='__main__':main()
