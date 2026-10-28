from common import *
def main():
    assert not(R/'provenance/INPUTS_FROZEN.json').exists()
    roots=[Path('/home/liu/polyp_research'),Path('/home/liu/new-polyp-dxy')]+[Path('/home/liu')/n for n in ['ring_first_3d','ring_first_3d_scene_vis','ring_first_3d_abs_density','ring_first_3d_phase_d','ring_first_3d_incremental','ring_first_3d_view_eval','ring_first_3d_ab_scene']];save('runtime/PROTECTED_START.json',{str(p):state(p)for p in roots})
    files=[p for p in (PREV/'metrics').glob('*')if p.is_file()]+[PREV/'config.json',PREV/'display_config.json',PREV/'provenance/PAIRS_FROZEN.json']+list((PREV/'code').glob('*.py'))
    for r in rows():
        files +=[Path(r['source_geometry_path']),Path(r['prediction_path']),Path(r['legacy_prediction_path'])]+[PREV/p for p in r['figures'].values()];a,m,rp=layers(r['A']);files.append(rp)
    files +=list((PREV/'figures').glob('*.png'))+[REPO/'visualization'/n for n in ['real_p0_renderer.py','same_camera_scene.py','pointcloud_audit_renderer.py']]
    save('color_config.json',dict(depth='A camera axial Z = (XYZ - c2w[:3,3]) @ c2w[:3,:3], component2',range='per original A scene: min/max across BOTH layers, all finite positive Z; no clipping/quantile normalization; same A reused for every B',near_lightness=.82,far_lightness=.27,saturation=.70,Polyp_hue=340/360,Background_hue=170/360,point_size=.08,antialiased=False,Ring='original black opaque CAD unchanged',only_allowed_change='Panel2 point colors, title and depth legend; pixel copy preserves everything else'))
    save('provenance/INPUTS_FROZEN.json',stamp(files,prior_commit='d969bd064e980ab0ca6af3b4d0e6f2e5a1bb1818',evaluation_runs=0,upstream_runs=0,GT_used=False));save('provenance/COLOR_RULE_FROZEN.json',stamp([R/'color_config.json',Path(__file__)]));print('FROZEN',len(set(files)),'inputs;11 pairs')
if __name__=='__main__':main()
