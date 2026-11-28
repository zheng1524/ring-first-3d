"""Compare actual reruns with frozen pre-metadata-repair predictions."""
from common import *

def main():
    before=read(T/'evidence/PRE_SELECTION_ID_REPAIR_PREDICTIONS.json')['results'];rows=[];indices=[]
    for old in before:
        path=T/'runs/results'/old['group']/old['configuration']/'RESULT.json';new=read(path)
        assert new['scientific_key']==revision_key() and new['cache_key']!=old['cache_key']
        a={x['source_id']:x['b_mm'] for x in old['bias']};b={x['source_id']:x['b_mm'] for x in new['bias']};assert a.keys()==b.keys()
        rows.append(dict(group=old['group'],configuration=old['configuration'],parameter_abs_delta=float(np.max(np.abs(np.array(old['p'])-new['p']))),bias_abs_delta_mm=max([abs(a[k]-b[k]) for k in a] or [0]),before_result_sha256=old['result_sha256'],after_result=asset(path)))
        indices.append(dict(group=old['group'],configuration=old['configuration'],coordinate_frame=new['coordinate_frame'],cache_key=new['cache_key']))
    assert len(rows)==93
    save(T/'evidence/SELECTION_ID_REPAIR_FIT_COMPARISON.json',dict(configurations=93,actual_reoptimization=True,scientific_key=revision_key(),max_parameter_abs_delta=max(r['parameter_abs_delta']for r in rows),max_bias_abs_delta_mm=max(r['bias_abs_delta_mm']for r in rows),rows=rows))
    save(T/'evidence/INITIALIZATION_COMPLETE.json',dict(groups=39,single=79,joint=14,configurations=93,scientific_key=revision_key(),remaining='Final verification and packaging tracked separately',results=indices))
    print('REFIT_COMPARED',len(rows),max(r['parameter_abs_delta']for r in rows),max(r['bias_abs_delta_mm']for r in rows))

if __name__=='__main__':main()
