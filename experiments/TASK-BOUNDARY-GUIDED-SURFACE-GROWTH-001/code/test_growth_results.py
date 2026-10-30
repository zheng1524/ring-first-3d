"""Meaningful provenance, monotonic face, joint-transform and held-frame checks."""
from evaluate import *
def main(selected=None):
    import common as shared
    frozen=shared.cases();shared.cases=lambda:frozen;globals()['cases']=lambda:frozen;checks=[]
    def check(n,ok):assert bool(ok),n;checks.append(dict(test=n,passed=True))
    verify();check('Original input/config SHA unchanged',True)
    for c in frozen:
        s=source(c['id']);uv,z=vis.project_camera(s['P'],s['p']['K'],s['p']['pose']);check(c['id']+' exact source UV/depth',np.max(abs(uv-s['uv']))<1e-6 and np.max(abs(z-s['p']['depth_mm'][s['uv'][:,1],s['uv'][:,0]]))<1e-6);check(c['id']+' original source RGB',np.array_equal(np.rint(s['C']*255).astype(np.uint8),s['frame'][s['uv'][:,1],s['uv'][:,0]]))
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        if selected and sid not in selected:continue
        path=R/f'local_results/scenes/{sid}_Final.json'
        if not path.exists():continue
        final=load(path);previous=set();initial=set();total_area=0.
        for k in range(final['accepted_steps']+1):
            blocks=load_scene(sid,k);now=set()
            for b in blocks:
                s=source(b['reference']);fids=np.array(b['face_ids']);check(sid+f'S{k} '+b['id']+' original complete faces only',np.all(fids>=0)and np.all(fids<len(s['F']))and not cleaned(b['reference'])['clean_removed'][s['F'][fids]].any());H=np.array(b['H']);check(sid+f'S{k} '+b['id']+' is bounded rigid derived transform',np.allclose(H[:3,:3].T@H[:3,:3],np.eye(3),atol=1e-6)and abs(np.linalg.det(H[:3,:3])-1)<1e-6 and motion_ok(H,b['role']));now|={(b['reference'],int(f))for f in fids}
            check(sid+f'S{k} no old accepted face removal',previous<=now)
            if k:
                added=now-previous;check(sid+f'S{k} adds a complete connected original patch',len(added)>=cfg()['growth_min_complete_patch_faces']and len({x[0]for x in added})==1);cid=next(iter(added))[0];fids=np.array([f for r,f in added]);check(sid+f'S{k} new triangles share real original edges',len(np.unique(face_components(source(cid)['F'][fids])))==1);total_area+=source(cid)['areas'][fids].sum()
            else:initial=now.copy()
            previous=now
        check(sid+' keeps all initial engineering complete faces',initial<=previous);a=unique_points(final['blocks']);check(sid+' no duplicate source IDs in point output',len(set(zip(a['references'],a['original_ids'])))==len(a['P']));sumsteps=sum(x['delta_area_mm2']for x in load(R/f'metrics/growth_steps_{sid}.json'));check(sid+' area ledger exact sum of original new faces',abs(total_area-sumsteps)<1e-6);check(sid+' finite explicit stop reason',bool(final['stop_reason']))
    held=set(load(R/'provenance/EVALUATION_TARGETS_FROZEN.json')['target_ids']);records=load(R/'metrics/new_HERO_sources.json')
    for r in records:
        check(r['reference']+' evaluation images excluded from new HERO',r['reference_view']not in held and not(set(r['source_views'])&held))
        if r['success']:check(r['reference']+' native new depth SHA retained',sha(r['native_depth_path'])==r['native_depth_SHA'])
    s=source('G01_004_ref08');t=target_source('G01_004_ref08');t.update(RGB='/nonexistent_B_RGB',Mask='/nonexistent_B_Mask');p=projection(s['P'][:50],s['C'][:50],t);check('Prediction rendering does not read B RGB/Mask',p['RGBA'].shape==(360,640,4))
    both('growth_result_tests',checks);print('GROWTH RESULT TESTS',len(checks),'PASS',flush=True)
if __name__=='__main__':main(sys.argv[1:]or None)
