"""Read-only same-image LightGlue/RoMa controls; never used to fill new output."""
from matching import *
def main():
    vv=views();pairs=load(R/'provenance/MATCHING_PAIRS_FROZEN.json')['pairs'];rows=[];paths=[]
    for pair in pairs:
        a,b=vv[pair['A']],vv[pair['B']]
        for method in ['LightGlue','RoMa']:
            path=OLD/'ring_first_v13_multisource/observations'/(method+'_'+a['view_id']+'__'+b['view_id']+'.npz');reverse=False
            if not path.exists():path=OLD/'ring_first_v13_multisource/observations'/(method+'_'+b['view_id']+'__'+a['view_id']+'.npz');reverse=True
            if not path.exists():rows.append(dict(pair=pair['id'],group=pair['group'],method=method,status='NOT_AVAILABLE_FOR_EXACT_NEW_PAIR',new_forward=False));continue
            paths.append(path);d=np.load(path);p,q=(d['q'],d['p'])if reverse else(d['p'],d['q']);out=annotate(p,q,np.ones(len(p)),a,b,method);row=record(pair,method,out,'HISTORICAL_EXACT_PAIR_REANNOTATED_READ_ONLY',0);row['source_cache']=str(path);row['source_cache_SHA256']=sha(path);row['new_forward']=False;rows.append(row)
    both('historical_matching_baselines',rows);save('provenance/HISTORICAL_MATCH_CACHE_INPUTS.json',stamp(paths,used_for_prediction=False,GT_used=False));print('CACHED BASELINE',sum('raw_N'in r for r in rows),'available /',len(rows),'exact-pair controls')
if __name__=='__main__':main()
