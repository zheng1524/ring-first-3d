from frontier import *
def main():
    rows=[]
    def check(n,ok):assert bool(ok),n;rows.append(dict(test=n,passed=True))
    verify();check('All frozen input SHA unchanged',True)
    for c in historical_cases():
        s=source(c['id']);check(c['id']+' exact copied Cleaned mask',sha(R/f'local_results/cleaned/{c["id"]}.npz')==sha(BASE/f'local_results/cleaned/{c["id"]}.npz'));check(c['id']+' original XYZ retained',np.array_equal(cleaned(c['id'])['XYZ_mm'],s['P']))
    for row in load(R/'metrics/engineering_seeds.json'):
        z=np.load(row['path']);s=source(row['source']);old=old_F2(row['source']);check(row['source']+' exact accepted source points',np.array_equal(z['accepted_original_point_ids'],np.flatnonzero(old['accepted'])));check(row['source']+' exact complete original faces',np.array_equal(z['accepted_original_face_ids'],np.flatnonzero(old['accepted'][s['F']].all(1))));check(row['source']+' exact geometry SHA',np.array_equal(z['XYZ_mm'],s['P']))
    E,st,C,face,_=edge_data(np.array([[0,1,2],[1,3,2]]));check('Two-triangle square has four external edges and one shared edge',sum(C==1)==4 and sum(C==2)==1)
    for sid in load(R/'provenance/MAIN_SURFACES_SELECTED.json')['selections']:
        b=load_scene(sid,0);f=frontier(b);check(sid+' all actual boundary lengths finite',np.isfinite(f['lengths']).all()and(f['lengths']>0).all());check(sid+' cleaning holes not growable',not f['eligible'][f['categories']=='CLEANING_INTERNAL_HOLE'].any())
    check('Four independent physical groups',len({c['group']for c in historical_cases()})==4)
    try:Path('/tmp/oracle_not_opened.blend').read_bytes();raise AssertionError('GT guard absent')
    except PermissionError:check('GT file opens rejected before filesystem read',True)
    for model in load(BASE/'provenance/MODEL_WEIGHTS.json'):check(model['model']+' frozen original weight',sha(model['path'])==model['sha256'])
    both('input_tests',rows);save('provenance/P0_SOURCE_FROZEN.json',stamp([R/'code'/n for n in ['common.py','geometry.py','assets.py','frontier.py','render.py','visualize.py','test_inputs.py']]+[R/'config/growth_rules.json'],GT_used=False));print('INPUT TESTS',len(rows),'PASS',flush=True)
if __name__=='__main__':main()
