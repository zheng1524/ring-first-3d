"""Source/derivation/denominator integrity checks, not scientific accuracy tests."""
from evaluate import *
import struct
def main():
    checks=[]
    def check(name,ok):
        assert bool(ok),name;checks.append(dict(check=name,passed=True))
    verify();check('frozen 136 selected historical inputs unchanged',True)
    for f in load(R/'provenance/CACHED_ANCHOR_DIAGNOSTIC_INPUTS.json')['files']:check('supplemental input '+f['path'],sha(f['path'])==f['sha256'])
    rows=load(R/'metrics/cleaning_comparison.json');check('all 9 references x5 versions retained',len(rows)==45)
    check('angle selection Raw with B-E continuation',load(R/'metrics/cleaning_decision.json')['selected']=='Raw'and load(R/'metrics/cleaning_decision.json')['continue_B_to_E'])
    for c in cases():
        cid=c['id'];s=source(cid);original=np.load(c['source_points']);rawP=original['XYZ_mm']if'XYZ_mm'in original.files else original['points_mm'];check(cid+' exact original P0 identity',np.array_equal(s['P'],rawP));n=normals(cid);cam=s['p']['pose'][:3,3];v=(s['P']-cam);v/=np.linalg.norm(v,axis=1)[:,None];b=np.degrees(np.arcsin(np.clip(abs((n['normal']*v).sum(1)),0,1)));check(cid+' beta from original source camera',np.allclose(n['beta_deg'],b));check(cid+' source RGB identity',np.array_equal(s['C'],s['frame'][s['uv'][:,1],s['uv'][:,0]]/255.));previous=np.zeros(len(s['P']),bool)
        for deg in [10,15,20]:
            z=np.load(R/f'local_results/cleaning/{cid}/Angle-{deg}.npz');expected=n['angle_deletion_eligible']&(b<deg);check(cid+f' Angle{deg} exact predicate',np.array_equal(z['deleted'],expected));check(cid+f' Angle{deg} reliability retained',not np.any(z['deleted']&~n['angle_deletion_eligible']));check(cid+f' Angle{deg} nested',np.all(~previous|z['deleted']));previous=z['deleted'];fkeep=~z['deleted'][s['F']].any(1);check(cid+f' Angle{deg} original faces only',np.array_equal(z['kept_original_face_ids'],np.flatnonzero(fkeep)))
        check(cid+' original world source projected pixel identity',np.max(abs(vis.project_camera(s['P'],s['p']['K'],s['p']['pose'])[0]-s['uv']))<1e-7)
    check('zero-retention truthiness repair no actual-output effect',all(r['sparse_stretched_proxy_retention']is None or r['sparse_stretched_proxy_retention']>0 for r in rows if r['version'].startswith('Angle')))
    ss=load(R/'metrics/aggregation_summary.json');check('five scenes plus two ambiguity diagnostics',len(ss)==7)
    nadded=0
    for sc in ss:
        for rank,cid in enumerate(sc['references']):
            s=source(cid);z=np.load(R/f'local_results/scenes/{sc["scene"]}/{cid}.npz');check(sc['scene']+cid+' all XYZ immutable',np.array_equal(z['XYZ_mm'],s['P']));check(sc['scene']+cid+' all RGB immutable',np.array_equal(z['RGB'],s['C']));check(sc['scene']+cid+' all UV identity',np.array_equal(z['source_uv'],s['uv']));check(sc['scene']+cid+' class total denominator',sum((z['class_id']==k).sum()for k in range(5))==len(s['P']))
            if rank:
                check(sc['scene']+cid+' additions only from novel candidates',np.all(~z['accepted']|(z['class_id']==NOVEL)));check(sc['scene']+cid+' independent selection Mask support retained',np.all(~z['accepted']|z['selection_mask_support']));nadded+=int(z['accepted'].sum())
            else:check(sc['scene']+cid+' complete primary unchanged',z['accepted'].all()and np.array_equal(z['XYZ_mm'][z['accepted']],s['P']))
    check('public accepted-source index exact denominator',len(load(R/'metrics/accepted_source_index.json'))==nadded==3659)
    for sc in ss:
        for mode in ['primary','core','evidence']:
            path=R/f'local_results/scene_exports/{sc["scene"]}_{mode}.npz';a=np.load(path);names=list(a['reference_names']);ref=a['source_reference_index'];ids=a['source_original_point_id']
            for j,cid in enumerate(names):check(sc['scene']+mode+cid+' scene points exact source IDs',np.array_equal(a['XYZ_mm'][ref==j],source(cid)['P'][ids[ref==j]]))
    for g in load(R/'metrics/GLB_INDEX.json'):
        p=Path(g['path']);check(p.name+' SHA',sha(p)==g['sha256']);buf=p.read_bytes();check(p.name+' GLB binary header',buf[:4]==b'glTF');length,typ=struct.unpack('<II',buf[12:20]);tree=json.loads(buf[20:20+length]);points=sum(tree['accessors'][pr['attributes']['POSITION']]['count']for m in tree['meshes']for pr in m['primitives']if pr.get('mode',4)==0)
        if 'points'in g:
            sc=next(x for x in ss if x['scene']==g['scene']);check(p.name+' actual point primitive denominator',points==g['points']+len(background(sc['primary'])['P']));check(p.name+' source IDs attached',all('original_ids'in m.get('extras',{})or'original_cache_ids'in m.get('extras',{})for m in tree['meshes']if any(pr.get('mode',4)==0 for pr in m['primitives'])))
    for row in load(R/'metrics/cross_view_validation.json'):
        p=R/f'local_results/validation/{row["scene"]}/{row["target"]}/{row["method"]}.npz';a=np.load(p);sid=row['scene'].replace('_alternate','');t=next(x for x in targets(sid)if x['id']==row['target']);mask=cv2.imread(t['Mask'],0)==1;check(row['scene']+row['method']+row['target']+' independent support denominator',row['target_Polyp_N']==int(mask.sum())and row['covered_N']==int(((a['layer']==1)&mask).sum()))
    s=source('G01_004_ref08');t=dict(selection('G01_004'),RGB='/tmp/NO_TARGET_RGB_ALLOWED.png',Mask='/tmp/NO_TARGET_MASK_ALLOWED.png');pred=projection(s['P'],s['C'],t);old=np.load(R/'local_results/validation/G01_004/004_10/primary.npz');check('B image/Mask inaccessible still produces exact prediction',np.array_equal(pred['RGBA'],old['RGBA']))
    h=load(R/'metrics/crossvideo_decision.json');check('crossvideo not fused explicitly',h['status']=='CROSS-VIDEO REGISTRATION CANDIDATE — NOT FUSED'and not h['D2_executed']);check('new crossvideo SIFT no correspondences not misreported improvement',h['training_N']==0 and h['heldout_N']==0 and 'NO_USABLE_NEW_SIFT'in h['selection'])
    for name in ['Fig1_cleaning_comparison.png','Fig2_single_video_aggregation.png','Fig3_crossvideo_comparison.png','Fig4_real_reprojection.png']:
        im=Image.open(R/'figures'/name);check(name+' true PNG present',im.format=='PNG'and im.width>=1800 and im.height>=1000)
    for sc in ss:
        for name in ['Layers_L1-L5.png','Camera_3Views.png','XYZ_3Views.png','Real_vs_3D.png']:check(sc['scene']+name+' present',(R/'figures/cases'/sc['scene']/name).is_file())
    for root,before in load(R/'runtime/PROTECTED_START.json').items():check(root+' protected git/index/status/dirty-content unchanged',state(Path(root))==before)
    for p in [Path('/tmp/gt_forbidden.blend'),Path('/home/liu/polyp_research/DO_NOT_CREATE_grazing_test')]:
        try:
            with p.open('wb')as f:f.write(b'NEVER')
        except PermissionError:check(str(p)+' firewall enforced',True)
        else:raise AssertionError('IO guard not enforced')
    save('provenance/FINAL_SOURCE_MANIFEST.json',stamp(list((R/'code').glob('*.py'))+[R/'config/rules.json'],algorithm_commit='d717a46',GT_mode='NONE',frozen_inputs=136,source_pixels_original=True))
    save('metrics/VALIDATION.json',dict(passed=True,count=len(checks),checks=checks,not_accuracy_certification=True));print('VALIDATED',len(checks),'checks; 10 protected workspaces unchanged',flush=True)
if __name__=='__main__':main()
