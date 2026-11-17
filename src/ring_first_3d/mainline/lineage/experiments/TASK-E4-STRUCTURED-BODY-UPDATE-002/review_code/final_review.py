"""Read-only scientific verification and hardlink curation, after Runner acceptance."""
from pathlib import Path
from html.parser import HTMLParser
import csv, hashlib, json, os, shutil
import numpy as np

TD = Path(__file__).resolve().parents[1]
RUN = TD / 'runs/PILOT_002'

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, value): p.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
def link(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        assert sha(src) == sha(dst), str(dst)
    else:
        os.link(src, dst)

def main():
    state = read(RUN/'RUN_MANIFEST.json')
    assert state['accepted'] and state['status'] == 'ACCEPTED_ENGINEERING'
    assert state['spent_seconds'] <= 14400
    logical = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    assert logical <= 450000000, logical
    for rec in state['attempts']:
        assert sha(RUN/rec['path']) == rec['sha256']
    latest = {}
    for rec in state['attempts']:
        r = read(RUN/rec['path'])
        latest[r['stage']] = RUN/'attempts'/r['attempt_id']
    for rec in read(TD/'inputs/INPUT_MANIFEST.json')['files']:
        assert sha(Path(rec['path'])) == rec['sha256'], rec['path']
    verified_predictions = {}
    ring_checks = []
    rows = list(csv.DictReader((TD/'metrics/RING_COLLISION_METRICS.csv').open()))
    for case in ['G01', 'G03', 'G05']:
        stage = latest['G1_'+case]
        for rec in read(stage/'BODY_PREDICTIONS_FROZEN.json')['records']:
            assert rec['status'] == 'NUMERIC'
            mesh = stage/rec['mesh_relative']
            assert sha(mesh) == rec['mesh_sha256']
            verified_predictions[case+'/'+rec['arm']] = rec['mesh_sha256']
        for arm in ['DEFORM_ONLY', 'DEFORM_SWEEP']:
            src = TD/'runs'/case/arm
            dst = TD/'review_assets'/case/arm
            for n in ['INITIAL.npz', 'RING_INITIAL.npz', 'RING_FINAL.npz']:
                link(src/n, dst/n)
            for p in src.glob('STEP_*/BODY.npz'):
                link(p, dst/p.relative_to(src))
            link(src/'STEP_035/GRAPH.npz', dst/'STEP_035/GRAPH.npz')
            for p in src.glob('FINAL_PAIRS/*.npz'):
                link(p, dst/p.relative_to(src))
            for p in src.glob('GROWTH_PROPOSAL_*/*.npz'):
                link(p, dst/p.relative_to(src))
            initial, final = np.load(src/'RING_INITIAL.npz'), np.load(src/'RING_FINAL.npz')
            eps = float(next(r for r in rows if r['case']==case and r['arm']==arm)['epsilon_mm'])
            vals = {k: float((final[k]-initial[k]).max()) for k in ['body_penetration', 'ring_penetration']}
            assert all(v <= eps for v in vals.values()), (case, arm, vals, eps)
            ring_checks.append(dict(case=case, arm=arm, epsilon_mm=eps, max_probe_penetration_delta_mm=vals))
    views = read(TD/'visualization/SUMMARY.json')['per_view_changes']
    protected = [v for v in views if v['protected']]
    bad = [v for v in protected if v['IoU_delta'] < -.01000001 or v['Boundary_delta_px'] > 1.00000001]
    assert not bad, bad
    geometry = list(csv.DictReader((TD/'metrics/GEOMETRY_METRICS.csv').open()))
    finals = [r for r in geometry if r['arm'] in ['DEFORM_ONLY', 'DEFORM_SWEEP']]
    assert len(finals)==6
    for r in finals:
        assert r['self_intersections']=='0' and r['watertight']=='True' and r['winding']=='True' and not r['violations'], r
    figures = list((TD/'visualization/figures').glob('*.png'))
    for p in figures:
        assert p.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n', str(p)
    refs = []
    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for k, v in attrs:
                if k in ['src','href'] and not v.startswith(('#','http','data:')):
                    target = (TD/'visualization'/v).resolve()
                    assert target.exists(), str(target)
                    refs.append(str(target))
    Links().feed((TD/'visualization/index.html').read_text())
    accepted = Path('/tmp/structured002-accept.json')
    assert read(accepted)['accepted']
    shutil.copyfile(accepted, TD/'evidence/CLI_ACCEPT.json')
    verification = read(TD/'evidence/FINAL_PATH_VERIFICATION.json')
    verification.update(figures=len(figures), verified_html_references=len(refs),
        protected_case_arm_views=len(protected), protected_violations=0,
        canonical_logical_bytes=logical, canonical_spent_seconds=state['spent_seconds'],
        final_prediction_sha256=verified_predictions, final_ring_fixed_probe_checks=ring_checks,
        final_geometry=dict(predictions=6, self_intersections=0, all_watertight=True, all_winding_consistent=True),
        review_is_post_acceptance=True, no_HERO_executed=True)
    dump(TD/'evidence/FINAL_PATH_VERIFICATION.json', verification)
    print(json.dumps(dict(figures=len(figures), protected_views=len(protected), protected_violations=0,
        prediction_hashes_verified=len(verified_predictions), logical_bytes=logical, seconds=state['spent_seconds']), indent=2))

if __name__ == '__main__': main()
