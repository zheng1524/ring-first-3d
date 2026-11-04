"""Source, fairness, implementation-contract and export checks; not GT validation."""
from fitting import *
def main():
    checks=[]
    def ck(name,passed,**extra):checks.append(dict(name=name,passed=bool(passed),**extra))
    freeze=load(R/'provenance/PREOPTIMIZATION_CORRECTION_v0.2.json')
    for x in freeze['files']:ck('corrected_freeze:'+x['path'],sha(REPO/x['path'])==x['sha256'])
    for x in load(R/'provenance/INPUT_ASSET_SHA.json'):ck('source:'+x['path'],sha(x['path'])==x['sha256'])
    for x in load(R/'provenance/DXY_RUNTIME_SOURCE_INDEX.json'):ck('DXY_source:'+x['path'],sha(x['path'])==x['sha256'])
    records=load(R/'metrics/ALL_FITS.json');primary=load(R/'metrics/PRIMARY_A_ONLY.json');ck('72_fixed_fits',len(records)==72);ck('24_primary_conditions',len(primary)==24);ck('8_synthetic_contracts',load(R/'metrics/SYNTHETIC_TESTS.json')['all_pass'])
    for scene,sc in protocol()['scenes'].items():
        for variant in protocol()['variants']:
            for start in protocol()['optimization']['initializations']:
                a,b=[next(x for x in records if(x['scene'],x['arm'],x['variant'],x['start'])==(scene,arm,variant,start))for arm in ['E1','E2']];ck(scene+variant+str(start)+':same_9p_initial',np.array_equal(a['initial'],b['initial'])and np.array_equal(a['R0'],b['R0'])and a['source_ids']==b['source_ids']and np.array_equal(a['weights'],b['weights']))
        for cid in sc['A']+sc['B']:
            o=obs(cid);s=source(cid);n=cleaned(cid);uv=o['depth_native_uv'];values=n['depth'][uv[:,1],uv[:,0]];ck(cid+':full_original_Mask',np.array_equal(o['full_polyp'],s['labels']==1));ck(cid+':32_shared_native_pixels_16_pairs',len(uv)==32 and len(o['pairs'])==16 and np.array_equal(values,o['depth_mm'])and len(np.unique(o['depth_native_pixel_id']))==32)
            D=o['depth_delta_mm'];pairs=o['pairs'];ck(cid+':relative_axial_depth_identity',np.array_equal(D,values[pairs[:,0]]-values[pairs[:,1]]))
        for m in [m for m in primary if m['scene']==scene]:
            candidates=[x for x in records if(x['scene'],x['arm'],x['variant'])==(scene,m['arm'],m['variant'])];ck(scene+m['arm']+m['variant']+':A_only_selection',m['objective']==min(x['objective']for x in candidates));ck(scene+m['arm']+m['variant']+':B_not_fit',not(set(m['source_ids'])&set(sc['B'])))
            met=m['B'][0];ck(scene+m['arm']+m['variant']+':fixed_B_denominator',met['intersection_N']+met['miss_N']==int(obs(sc['B'][0])['full_polyp'].sum())and met['depth_fixed_N']==32 and met['relative_depth_hit_pair_N']+met['relative_depth_miss_pair_N']==16)
            if m['variant']=='full':
                P,F=mesh(np.array(m['p']),np.array(m['R0']));tm=trimesh.load(R/'local_results'/(scene+'__'+m['arm']+'.ply'),process=False);ck(scene+m['arm']+':true_exported_mesh',np.array_equal(F,tm.faces)and abs(P-tm.vertices).max()<2e-6)
    # Check soft-loss source modules never read morphology/class metadata.
    for filename in ['losses.py','fitting.py']:
        src=(R/'code'/filename).read_text();ck(filename+':no_class_name_dispatch',not any(token in src for token in ["['kind']","['morphology']","'Ip'","'Is'","'IIa'",'head_cue','MORPH_OPEN','fitEllipse']))
    geometry=[];root=[]
    for m in primary:
        if m['variant']!='full':continue
        P,F=mesh(np.array(m['p']),np.array(m['R0']));tm=trimesh.Trimesh(P,F,process=False);c,Q,a=decode(np.array(m['p']),np.array(m['R0']));geometry.append(dict(scene=m['scene'],arm=m['arm'],components=len(tm.split(only_watertight=False)),watertight=bool(tm.is_watertight),degenerate_faces=int((tm.area_faces<1e-12).sum()),axis_ratio=float(a.max()/a.min()),self_intersection='excluded by convex ellipsoid family; not a true shape certificate',backside='PRIOR_INFERRED_NOT_OBSERVED'))
        for cid in protocol()['scenes'][m['scene']]['A']:
            o=obs(cid);s=source(cid);rays=vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']);z=first_depth(np.array(m['p']),np.array(m['R0']),rays);tz=cast(mesh_scene(P,F),o['depth_native_uv'],o['Kn'],s['T'])[0];cad=cast(ringscene(m['scene']),o['depth_native_uv'],o['Kn'],s['T'])[0];common=np.isfinite(z)&np.isfinite(tz);center,M,axes,curve=ellipse_projection(np.array(m['p']),np.array(m['R0']),s['K'],s['T']);outside=(curve[:,0]<0)|(curve[:,0]>639)|(curve[:,1]<0)|(curve[:,1]>359)
            root.append(dict(scene=m['scene'],arm=m['arm'],source=cid,analytic_mesh_hit_disagreement=int((np.isfinite(z)!=np.isfinite(tz)).sum()),analytic_mesh_depth_mm=stats(z[common]-tz[common]),modeled_root_behind_CAD_N=int((np.isfinite(z)&(z>cad+.05)).sum()),predicted_contour_outside_FOV_N=int(outside.sum())))
    save('metrics/GEOMETRY_AUDIT.json',geometry);save('metrics/ROOT_AND_VISIBILITY_AUDIT.json',root)
    traces=''
    for name in ['dxy','prepare','synthetic','pre_ring_pool_fix_fits','fits','analysis','visualize']:
        p=R/'runtime'/(name+'.log')
        if p.exists():traces+='\n### '+name+'\n'+p.read_text()
    (R/'metrics/EXECUTION_TRACE.txt').write_text(traces)
    save('metrics/VALIDATION.json',dict(integrity_and_fairness_all_pass=all(x['passed']for x in checks),checks=checks,scientific_conclusion='MIXED; conditional exploratory, not GT validation',qualification_promoted=False))
    save('provenance/ENVIRONMENT.json',dict(Python=sys.version,numpy=np.__version__,scipy=__import__('scipy').__version__,opencv=cv2.__version__,open3d=o3d.__version__,trimesh=trimesh.__version__,CPU_only=True,DXY_worker_Python='3.10.19',DXY_worker_numpy='1.26.4',DXY_worker_scipy='1.15.3',DXY_worker_cv2='4.10.0',DXY_worker_skimage='0.25.2'))
    print('VALIDATION',len(checks),'checks;',sum(x['passed']for x in checks),'passed',flush=True);assert all(x['passed']for x in checks)
if __name__=='__main__':main()
