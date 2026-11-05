from common import *
def main():
    public=Path('/home/liu/new-polyp-dxy/docs/theory');cfg=load(OLD/'PROTOCOL_FREEZE.json');jobs=load(OLD/'scene_manifest.json');rows=[]
    for key,s in cfg['source_models'].items():
        assert sha(s['path'])==s['sha256'];sources=[j for j in jobs if j['model']==key];R10=[s for s in sources if s['inner_diameter_mm']==10];poses={tuple(s['ring_center_mm'])for s in R10}
        rows.append(dict(model=key,role='FIRST_CASE'if key=='IIa6.5'else'HUMAN_HOLD_AFTER_FIRST_CASE',source=asset(s['path']),object_name='球体',native_to_mm=1000,body_static_by_manifest=True,all_R10_scene_static=False if len(poses)>1 else True,Ring_poses_mm=sorted(poses),views=[dict(id=s['source_id'],Ring_center=s['ring_center_mm'],scene=asset(OLD/'scenes'/s['source_id']/'scene.json'),oracle=asset(OLD/'scenes'/s['source_id']/'oracle_mask.png'))for s in R10]))
    seed=next(s for s in jobs if s['source_id']=='IIa6.5_R10_obs01');selected=[next(s for s in jobs if s['source_id']==f'IIa6.5_R10_obs{i:02d}')for i in [0,1,3,4,5]]
    assert all(s['asset_sha256']==seed['asset_sha256']for s in selected);assert all(s['ring_center_mm']==seed['ring_center_mm']for s in selected)
    save('config/SCENE_INPUTS.json',dict(source=seed['asset_path'],source_sha256=seed['asset_sha256'],Ring_scene='/home/liu/polyp_research/ring_anchor_3d/assets/scene.blend',Ring_scene_sha256=sha('/home/liu/polyp_research/ring_anchor_3d/assets/scene.blend'),seed=seed,views=selected,static_scene='body + Ring pose fixed to obs01; existing obs02 cannot be mixed because Ring differs by 0.118444459mm',first_case_only=True))
    save('assets_index/SOURCE_AUDIT.json',dict(models=rows,source_generator=asset(OLD/'scripts/render_scenes.py'),source_poses=asset(OLD/'scripts/physical_poses.py'),DXY_theory_manifest=asset(public/'SOURCE_MANIFEST.json'),DXY_scene_table=asset(public/'data/scenes.csv'),DXY_is_read_only=True,GT_allowed='synthetic controlled target generation and separate 3D audit only',original_prediction_tables_not_used=True))
    print('ASSET_IDENTITY_AUDIT',[(x['model'],x['all_R10_scene_static'])for x in rows],flush=True)
if __name__=='__main__':main()
