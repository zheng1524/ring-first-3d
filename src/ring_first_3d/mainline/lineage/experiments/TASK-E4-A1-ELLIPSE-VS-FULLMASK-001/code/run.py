"""Frozen budget; independent identical starts; B never chooses the output."""
from fitting import *
def main():
    assert(R/'provenance/PREOPTIMIZATION_FREEZE.json').exists()
    assert load(R/'metrics/SYNTHETIC_TESTS.json')['all_pass']
    path=R/'metrics/ALL_FITS.json';records=load(path)if path.exists()else[]
    for scene,sc in protocol()['scenes'].items():
        for arm in protocol()['arms']:
            if arm=='E1'and not sc['E1_available']:continue
            for variant in protocol()['variants']:
                for start in protocol()['optimization']['initializations']:
                    if any((x['scene'],x['arm'],x['variant'],x['start'])==(scene,arm,variant,start)for x in records):continue
                    print('FIT',scene,arm,variant,start,flush=True);problem=Problem(scene,arm,variant);out=problem.solve(start);out['B']=[evaluate(out,c)for c in sc['B']];records.append(clean(out));save('metrics/ALL_FITS.json',records)
                    print('DONE',scene,arm,variant,start,'A-cost',round(out['objective'],4),'B-IoU',round(out['B'][0]['full_mask_IoU'],3),'seconds',round(out['seconds'],2),flush=True)
    chosen=[]
    for scene,sc in protocol()['scenes'].items():
        for arm in protocol()['arms']:
            if arm=='E1'and not sc['E1_available']:continue
            for variant in protocol()['variants']:
                candidates=[x for x in records if(x['scene'],x['arm'],x['variant'])==(scene,arm,variant)];best=min(candidates,key=lambda x:x['objective']);best['A']=[evaluate(best,c)for c in sc['A']];chosen.append(best)
                if variant=='full':
                    P,F=mesh(np.array(best['p']),np.array(best['R0']));trimesh.Trimesh(P,F,process=False).export(R/'local_results'/(scene+'__'+arm+'.ply'))
                for c in sc['B']:evaluate(best,c,save_arrays=True)
    save('metrics/PRIMARY_A_ONLY.json',chosen);print('ALL_FITS_COMPLETE',len(records),flush=True)
if __name__=='__main__':main()
