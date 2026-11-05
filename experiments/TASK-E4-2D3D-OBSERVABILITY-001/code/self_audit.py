from common import *
import subprocess
def main():
    assert load(R/'metrics/ALL_PREDICTIONS_FREEZE.json')['all_predictions_frozen_before_this_first_native_GT_evaluation']
    rows=[]
    for name in ['P0','GT_native','ORIGINAL','SUBPIXEL_TARGET']:
        inp=R/'audit_only'/(name+'_BLENDER_INPUT.npz');out=R/'metrics'/(name+'_SELF_INTERSECTION.json')
        assert inp.exists()
        p=subprocess.run([BLENDER,'--factory-startup','--background','--threads','2','--python-exit-code','2','--python',str(R/'code/blender_self_check.py'),'--',str(inp),str(out)],capture_output=True,text=True,timeout=120)
        (R/'runtime'/(name+'_SELF_CHECK.log')).write_text(p.stdout+p.stderr);assert p.returncode==0;rows.append(dict(state=name,**load(out)))
    save('metrics/SELF_INTERSECTION_AUDIT.json',dict(rows=rows,not_a_full_formal_certificate=True,no_geometry_postprocessing=True));print('SELF_AUDIT_DONE',[(x['state'],x['nonadjacent_intersecting_triangle_pairs_N'])for x in rows],flush=True)
if __name__=='__main__':main()
