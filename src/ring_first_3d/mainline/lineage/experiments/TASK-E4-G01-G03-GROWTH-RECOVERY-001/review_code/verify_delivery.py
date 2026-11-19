"""Verify final published paths, images, immutable predictions and source locks."""
import json,sys,csv,shutil
from pathlib import Path
from html.parser import HTMLParser
from PIL import Image
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from io_utils import read,sha,dump

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ['src','href'])

run=TD/'runs/LOCAL_002';state=read(run/'RUN_MANIFEST.json');assert state['status']=='ACCEPTED_ENGINEERING'
index=TD/'visualization/index.html';parser=Links();parser.feed(index.read_text())
paths=[(index.parent/v).resolve()for v in parser.links if not v.startswith(('http:','https:','#','data:'))]
assert all(p.is_file()for p in paths)
pngs=sorted((TD/'visualization/figures').glob('*.png'));assert len(pngs)==54
for p in pngs:
    with Image.open(p)as im:im.verify()
for c in ['G01','G03']:
    d=TD/'review_assets'/c;r=read(d/'PREDICTIONS_FROZEN.json')['records'][0]
    assert sha(d/('FINAL.npz'if r['status']=='NUMERIC'else'FAILED_ATTEMPT.npz'))==r['mesh_sha256']
    assert (TD/'runs'/c/'DEFORM_SWEEP_RECOVERY').is_dir()
inputs=read(TD/'inputs/INPUT_MANIFEST.json')['files'];assert all(sha(r['path'])==r['sha256']for r in inputs)
lock=read(TD/'protocols/ENGINEERING_REPAIR_001/CODE_LOCK.json')['files'];assert all(sha(r['path'])==r['sha256']for r in lock)
audit=read(TD/'evidence/POST_RUN_GEOMETRY_AUDIT.json')['records']
with(TD/'metrics/ROOT_GEOMETRY_AUDIT.csv').open('w')as f:
    keys=['case','automatic_gate_status','scientific_root_review','target_embedding_depth_mm','actual_C0_SDF_depth_mm','embedded_arc_mm','exposed_arc_mm','formal_stalk_length_mm','root_section_max_SDF_mm']
    w=csv.DictWriter(f,keys,lineterminator="\n");w.writeheader()
    for a in audit:
        config=read(TD/'review_assets'/a['case']/'LOCAL_CONFIGURATION.json')['embedding'];l=a['diagnostic_lengths']
        w.writerow(dict(case=a['case'],automatic_gate_status=a['status'],scientific_root_review=a['root_review_status'],target_embedding_depth_mm=config['embedding_depth_target_mm'],actual_C0_SDF_depth_mm=l['embedding_depth_SDF_mm'],embedded_arc_mm=l['embedded_length_mm'],exposed_arc_mm=l['exposed_stalk_length_mm'],formal_stalk_length_mm=a['reported_stalk_length_mm']if a['reported_stalk_length_mm']is not None else'NaN',root_section_max_SDF_mm=a['proximal_section_SDF_max_mm']))
dump(TD/'evidence/PUBLICATION_VERIFICATION.json',dict(visualization_directory=str(index.parent.resolve()),index=str(index.resolve()),figures=len(pngs),local_links_checked=len(paths),all_local_html_links_exist=True,all_png_files_decoded=True,verified_source_assets=len(inputs),verified_source_files=len(lock),input_hashes_unchanged=True,predictions_unchanged=True,canonical_run=str(run),canonical_freeze=state['freeze_sha256'],target_groups=2,numeric_gate_outputs=1,scientific_acceptance='NOT_CERTIFIED; proximal-section exposure and fixed-GT-frame worsening disclosed'))
shutil.copyfile('/dev/shm/growth-final-accept.json',TD/'evidence/FINAL_POLICY_ACCEPT.json')
shutil.copyfile('/dev/shm/growth-root-crop.txt',TD/'evidence/REVIEW_RENDER_DEPENDENCY_FAILURE.txt')
shutil.copyfile('/dev/shm/growth-root-crop-repaired.txt',TD/'evidence/REVIEW_RENDER_PASS.txt')
dump(TD/'SOURCE_VERSION_TABLE.json',dict(baseline='238c2da1cd842c0eba710a4ec44db5f437bff8e4',G03_optimizer='62c56097916e32da6dde3a3d9018912f76c69378',G01_optimizer='abd4917f2074cb38e22db9b1b5f55b5ff56e6041',canonical_freeze=state['freeze_sha256'],protocol='protocols/ENGINEERING_REPAIR_001/TASK.yaml',protocol_sha256=sha(TD/'protocols/ENGINEERING_REPAIR_001/TASK.yaml'),scientific_parameters_unchanged=True,G03_reoptimized=False))
(TD/'WORK_STATUS.md').write_text('Completed: LOCAL_002 accepted by Research Policy Runner; 247 tests passed. Automatic numeric gate 1/2 (G01), scientific validity remains qualified by partial proximal-section exposure and fixed-frame GT worsening; G03 fails per-view protection and reports NaN. Both frozen runs retained. 54 actual-data figures and full Mesh/evidence published. No further optimization performed. See TECHNICAL_REPORT.md and FAILURE_REGISTRY.json.\n')
print(json.dumps(read(TD/'evidence/PUBLICATION_VERIFICATION.json'),indent=2))
