from common import *
def main():
    assert not(R/'provenance/INPUTS_FROZEN.json').exists()
    roots=[Path('/home/liu/polyp_research'),Path('/home/liu/new-polyp-dxy')]+[Path('/home/liu')/n for n in ['ring_first_3d','ring_first_3d_scene_vis','ring_first_3d_abs_density','ring_first_3d_phase_d','ring_first_3d_incremental','ring_first_3d_view_eval','ring_first_3d_ab_scene','ring_first_3d_panel2_depth']]
    save('runtime/PROTECTED_START.json',{str(p):state(p)for p in roots})
    files=[INC/'provenance/CASES.json',INC/'provenance/TARGETS_FROZEN.json',INC/'provenance/REVIEW_TARGETS_FROZEN.json',PHASE/'metrics/D1_decision.json',PHASE/'metrics/D1_backup_PnP.json',OLD/'independent_confidence_fusion_v1/inputs/H_frozen.json',INC/'metrics/B_scenes.json',INC/'metrics/B_source_ledger.json',INC/'metrics/E_visible_coverage.json',INC/'metrics/E_common_support.json',SPARSE/'code/run.py',DENS/'provenance/INPUT_FREEZE.json',DENS/'provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json']
    for c in cases():
        cid=c['id'];source(cid)
        files +=[Path(c[k])for k in ['pack','mesh','source_points','RGB','Mask','camera_file']]+[DENS/f'local_fields/{cid}_fields.npz',INC/f'local_results/background/{cid}.npz',ABS/f'local_results/{cid}/spatial_regions.npz',ring_path(c)]
        if c['group']=='G01':files.append(ABS/f'local_results/{cid}/T2_exact.npz')
    for sid in [s['id']for s in scenes()]:
        for t in targets(sid):files.extend([Path(t['RGB']),Path(t['Mask'])])
    files+=list((REPO/'visualization').glob('*.py'))+list((REPO/'visualization').glob('*.json'))+[DEPTH/'code/scene_renderer.py',DEPTH/'color_config.json']+list((AB/'code').glob('*.py'))
    for root in [DENS,SPARSE,ABS,INC,Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001')]:files.append(root/'TECHNICAL_REPORT.md')
    old=load(DENS/'provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json')['fields']
    for c in cases():p=DENS/f'local_fields/{c["id"]}_fields.npz';assert sha(p)==old[str(p)]
    save('provenance/INPUTS_FROZEN.json',stamp(files,base_commit='a46754dc7b301e58cc46e05493b915948dd45537',GT_used=False,source_cameras_unchanged=True))
    save('provenance/RULES_FROZEN.json',stamp([R/'config/rules.json',R/'TASK.md']+list((R/'code').glob('*.py')),before_any_cleaning_or_registration=True))
    save('provenance/CASES.json',cases());save('provenance/TARGETS_FROZEN.json',{s['id']:targets(s['id'])for s in scenes()})
    print('FROZEN',len(set(files)),'inputs,',len(cases()),'references',flush=True)
if __name__=='__main__':main()
