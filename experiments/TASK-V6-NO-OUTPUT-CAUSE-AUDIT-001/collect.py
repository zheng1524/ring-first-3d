"""Read-only audit of frozen V6 results; no camera/BA/HERO rerun or gate change.

The sole recomputation is original pair_data on cached matches to inspect graph
connectivity. It is diagnostic, not an additional scientific reconstruction.
"""
from pathlib import Path
import ast, collections, csv, datetime, hashlib, json, statistics
import cv2
import numpy as np

T = Path(__file__).resolve().parent
B = Path('/home/liu/ring_first_3d_workspace/runs/v6_full_run_001')
S = B/'snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a'
V6 = Path('/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v6_local_reconstruction/scripts')
cv2.setNumThreads(1)
identities = {}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(p):
    p = Path(p); identities[str(p)] = dict(bytes=p.stat().st_size, sha256=sha(p))
def read(p):
    record(p); return json.loads(Path(p).read_text())
def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False))
def table(p, rows):
    with p.open('w', newline='') as f:
        w=csv.DictWriter(f, list(dict.fromkeys(k for r in rows for k in r)), lineterminator='\n')
        w.writeheader();w.writerows(rows)
def original_function(p, name, namespace):
    record(p); tree=ast.parse(p.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),namespace)
    return namespace[name]
admit=original_function(S/'src/ring_first_3d/v6_raw/policy.py','admit_camera',{'np':np})
pair_data=original_function(V6/'local_ring_sfm.py','pair_data',{'np':np,'cv2':cv2})
def components(n, edges):
    neighbours=[set() for _ in range(n)]
    for i,j in edges: neighbours[i].add(j);neighbours[j].add(i)
    unseen=set(range(n));out=[]
    while unseen:
        todo=[min(unseen)];found=set()
        while todo:
            i=todo.pop()
            if i in found:continue
            found.add(i);todo.extend(neighbours[i]-found)
        unseen-=found;out.append(sorted(found))
    return sorted(out,key=lambda c:(-len(c),c))
def inspect_graph(p):
    frozen=read(p/'metrics/freeze_local_solver_protocol.json')
    assert frozen['files'][str(V6/'local_ring_sfm.py')]==sha(V6/'local_ring_sfm.py')
    cfg=read(p/'config.json');pair_data.__globals__['cfg']=lambda:cfg
    assert frozen['files'][str(p/'config.json')]==sha(p/'config.json')
    frozen_tracks=read(p/'metrics/freeze_tracks.json')
    paths=[p/'observations/tracks005.npz',p/'observations/pairs005.npz']
    for q in paths:
        record(q);assert frozen_tracks['files'][str(q)]==sha(q)
    with np.load(paths[0]) as tr, np.load(paths[1]) as pack:
        edges=pair_data(tr,pack);n=len(tr['ids']);pre=[];counts=[]
        for k,(i,j) in enumerate(pack['ij']):
            rows=pack[f'pair{k}'];training=rows[~tr['held'][rows[:,0].astype(int)]]
            if len(training)>=12:pre.append((int(i),int(j)))
            counts.append(dict(i=int(i),j=int(j),raw_i=int(tr['frame_raw'][i]),raw_j=int(tr['frame_raw'][j]),cached_matches=len(rows),nonheld_matches=len(training)))
        post=components(n,[(e['i'],e['j']) for e in edges]);prec=components(n,pre)
        ref=read(p/'inputs/REFERENCE_RECEIPT.json')['reference_index']
        refc=next(c for c in post if ref in c)
        return dict(frames=n,tracks=len(tr['held']),held_tracks=int(tr['held'].sum()),cached_pairs=len(pack['ij']),pre_ransac_edges=len(pre),accepted_edges=len(edges),pre_component_sizes=list(map(len,prec)),component_sizes=list(map(len,post)),components_raw=[[int(tr['frame_raw'][i]) for i in c] for c in post],reference_raw=int(tr['frame_raw'][ref]),reference_component_size=len(refc),unreachable_raw=[int(tr['frame_raw'][i]) for i in range(n) if i not in refc],pair_counts=counts,accepted=[dict(i=e['i'],j=e['j'],inliers=len(e['rows'])) for e in edges],cv2_version=cv2.__version__,diagnostic_only=True)

record(B/'VIDEO_RESULTS.csv');record(B/'GROUP_RESULTS.csv')
videos=list(csv.DictReader((B/'VIDEO_RESULTS.csv').open()));groups=list(csv.DictReader((B/'GROUP_RESULTS.csv').open()))
assert len(videos)==79 and len(groups)==39
rows=[];frame_rows=[];details={};graphs={};nulls={};total_plan=0;total_completed=0
for v in videos:
    p=Path(v['run_path']);state=read(B/'states'/(v['case']+'.json'));assert state['status']==v['status']
    r=dict(case=v['case'],group=v['group'],status=v['status'],origin=v['origin'],source_execution_commit=v['source_execution_commit'] or 'da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a',run_path=str(p),renderable=int(v['renderable']),selected_targets=int(v['selected_targets']),cause='',q1_cameras=None,frames=None)
    solvers=read(p/'metrics/local005_solver.json')
    r['solver_completed']=sum(bool(x['success']) for x in solvers)
    r['BA_converged']=sum(bool(x.get('BA',{}).get('success')) for x in solvers)
    if v['status']=='CAMERA_FAILED':
        failure=read(p/'CAMERA_FAILURE.json');record(B/'logs'/(v['case']+'__camera.log'))
        if all('Ring pose graph disconnected' in x.get('failure','') for x in solvers):
            r['cause']='GRAPH_DISCONNECTED';g=inspect_graph(p);assert len(g['component_sizes'])>1;graphs[v['case']]=g
            r.update(frames=g['frames'],graph_components='+'.join(map(str,g['component_sizes'])),reference_component=g['reference_component_size'],unreachable_raw=json.dumps(g['unreachable_raw']))
        else:
            assert 'NoneType' in failure['error'] and r['solver_completed']==2
            r['cause']='EMPTY_RING_VALIDATION_TYPEERROR';ledger=read(p/'inputs/ledger005.json');rr=[]
            for i,f in enumerate(ledger):
                q=p/'observations'/(f['id']+'_ring.npz');record(q)
                with np.load(q) as z:rr.append(dict(index=i,raw=f['raw_frame'],q_train=len(z['q_train']),q_held=len(z['q_held']),p_train=len(z['p_train']),p_held=len(z['p_held']),b_train=len(z['b_train']),b_held=len(z['b_held']),raw_boundary=len(z['raw_boundary']),ambiguous_boundary=len(z['ambiguous_boundary']),new_supported_DXY_edges=len(z['new_supported_DXY_edges'])))
            nulls[v['case']]=rr;r['empty_ring_held_frames']=sum(z['q_held']==0 for z in rr);r['frames']=len(rr)
            read(p/'v5raw/metrics/ring_observations.json')
            for frozen_path in ['metrics/freeze_validation_protocol.json','v5raw/metrics/freeze_observations_protocol.json']:
                frozen=read(p/frozen_path)
                for path,digest in frozen['files'].items():
                    if Path(path).suffix=='.py':record(path);assert sha(path)==digest
        details[v['case']]=dict(failure=failure,solvers=solvers)
    else:
        plan=read(p/'PLAN_FROZEN.json');gates=read(p/'metrics/GATES.json');hero=read(p/'HERO_COMPLETE.json');reference=read(p/'inputs/REFERENCE_RECEIPT.json')
        assert hero['budget']==plan['budget'] and not hero['failed']
        assert hero['completed']==r['renderable'];total_plan+=plan['budget'];total_completed+=hero['completed']
        passed=[];cause_counts=collections.Counter();metrics=[]
        labels=['留出观测数','RGB MAE px','RGB P95 px','正深度比例','Ring边界 MAE px','Ring边界 P95 px']
        for i,g in enumerate(gates):
            a,b,reasons=admit(g['metrics']);assert (a,b)==(g['old_pass'],g['new_pass'])
            if b:passed.append(i)
            hard=[label for label in labels if any(s.startswith(label+' ') for s in reasons)]
            cause_counts.update(hard);m=g['metrics'];metrics.append(m)
            frame_rows.append(dict(case=v['case'],raw_frame=g['raw_frame'],q0_pass=a,q1_pass=b,hard_reasons=';'.join(hard),held_n=m['held_observations'],rgb_mae=m['held_reprojection']['MAE'],rgb_p95=m['held_reprojection']['p95'],positive=m['held_positive_fraction'],ring_mae=m['ring_held_self_contour_px']['MAE'],ring_p95=m['ring_held_self_contour_px']['p95'],center_spread_warning=m['initialization_center_spread_mm']))
        assert len(passed)==plan['new_cameras']
        validation=read(p/'metrics/local_validation.json')
        alternative={str(z['version']):sum(admit(f)[1] for f in z['per_frame']) for z in validation['versions']}
        r.update(primary_version=validation['primary'],admitted_per_version=json.dumps(alternative),alternative_max_admitted=max((n for v,n in alternative.items() if v!=str(validation['primary'])),default=0))
        r.update(q1_cameras=len(passed),frames=len(gates),legal_targets=plan['budget'],hero_attempts=hero['completed']+len(hero['failed']),max_supports=max((len(c['sources']) for c in plan['all_targets']),default=0),gate_counts=json.dumps(cause_counts,ensure_ascii=False),q1_raw=json.dumps([gates[i]['raw_frame'] for i in passed]))
        for label,key in [('rgb_mae','MAE'),('rgb_p95','p95')]:
            nums=[m['held_reprojection'][key] for m in metrics if m['held_reprojection'][key] is not None]
            r[label+'_median_across_frames']=statistics.median(nums) if nums else None
        if r['renderable']:r['cause']='OUTPUT'
        elif not passed:r['cause']='NO_ADMITTED_CAMERAS'
        elif len(passed)<3:r['cause']='FEWER_THAN_THREE_ADMITTED_CAMERAS'
        else:r['cause']='INSUFFICIENT_SHARED_TRACK_SUPPORT'
        if not r['renderable']:
            assert hero['budget']==0 and hero['completed']==0
            details[v['case']]=dict(plan=plan,solvers=solvers,reference=reference,gate_counts=dict(cause_counts))
    rows.append(r)
assert total_plan==total_completed==795
counts=collections.Counter(r['cause'] for r in rows)
assert counts==dict(OUTPUT=42,NO_ADMITTED_CAMERAS=21,FEWER_THAN_THREE_ADMITTED_CAMERAS=6,INSUFFICIENT_SHARED_TRACK_SUPPORT=1,GRAPH_DISCONNECTED=8,EMPTY_RING_VALIDATION_TYPEERROR=1)
group_rows=[]
for g in groups:
    rr=[r for r in rows if r['group']==g['group']]
    group_rows.append(dict(group=g['group'],videos=len(rr),with_output=sum(r['renderable']>0 for r in rr),failed=sum(r['status']=='CAMERA_FAILED' for r in rr),video_causes=json.dumps({r['case'].rsplit('_',1)[1]:r['cause'] for r in rr},ensure_ascii=False)))
E=T/'evidence';E.mkdir(exist_ok=True)
table(T/'VIDEO_CAUSES.csv',rows);table(T/'GROUP_CAUSES.csv',group_rows);table(T/'FRAME_GATES.csv',frame_rows)
save(E/'DETAILS.json',details);save(E/'GRAPH_DIAGNOSTICS.json',graphs);save(E/'EMPTY_RING_OBSERVATIONS.json',nulls)
save(E/'SUMMARY.json',dict(checked_beijing=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),science_execution='da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a',counts=dict(counts),groups=39,videos=79,no_output_groups=sum(g['with_output']==0 for g in group_rows),groups_with_camera_failure=sum(g['failed']>0 for g in group_rows),zero_groups_with_camera_failure=sum(g['failed']>0 and g['with_output']==0 for g in group_rows),hero_legal=total_plan,hero_completed=total_completed,hero_failed=0,source_file_count=len(identities),graph_recomputation='original frozen pair_data only, cached tracks/pairs, original RNG seed, no pose/BA/HERO/selection changes'))
assert all(sha(p)==v['sha256'] for p,v in identities.items())
save(E/'SOURCE_IDENTITIES.json',identities)
print('AUDIT_PASS',dict(counts),'sources',len(identities))
for name,g in graphs.items():print(name,g['pre_component_sizes'],'->',g['component_sizes'],'reference',g['reference_component_size'],'unreachable_raw',g['unreachable_raw'])
print('EMPTY_RING_COUNTS', {name:sum(r['q_held']==0 for r in rows) for name,rows in nulls.items()})
