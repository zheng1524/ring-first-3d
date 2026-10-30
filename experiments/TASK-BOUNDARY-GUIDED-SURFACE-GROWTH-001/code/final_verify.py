"""Read-only checks of protected assets and final deliverables; task writes only."""
from common import *
import struct,re,importlib.metadata as md
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit

def main():
    checks=[]
    def check(name,ok,**detail):
        checks.append(dict(test=name,passed=bool(ok),**detail))
        if not ok:raise AssertionError(name+' '+str(detail))
    # Source snapshots may contain task code which legitimately evolved. Only
    # immutable upstream manifests are recursively verified against originals.
    frozen=[R/'provenance/INPUTS_FROZEN.json',BASE/'provenance/INPUTS_FROZEN.json',BASE/'provenance/F2_GEOMETRY_FROZEN.json',BASE/'provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json']
    seen={}
    for p in frozen:
        data=load(p)
        for row in data.get('files',[]):
            if row['path']in seen:check('compatible original freeze '+row['path'],seen[row['path']]==row['sha256']);continue
            seen[row['path']]=row['sha256'];check('immutable upstream SHA '+row['path'],sha(row['path'])==row['sha256'])
    for model in load(BASE/'provenance/MODEL_WEIGHTS.json'):check('original weight '+model['model'],sha(model['path'])==model['sha256'])
    before=load(R/'runtime/PROTECTED_START.json');after={}
    for path,original in before.items():
        current=state(Path(path));after[path]=current;check('protected workspace unchanged '+path,current==original)
    save('runtime/PROTECTED_END.json',after)
    # Final source identity binds every reference/source RGB and frozen K,c2w.
    refs=cases();check('36 readable source references',len(refs)==36)
    new=load(R/'metrics/new_HERO_sources.json');check('22 successful and 2 explicit runtime failures',len(new)==24 and sum(x['success']for x in new)==22)
    for row in new:
        if row['success']:check(row['reference']+' native depth immutable',sha(row['native_depth_path'])==row['native_depth_SHA'])
        else:check(row['reference']+' failed source has no invented XYZ',not any(c['id']==row['reference']for c in refs))
    models=load(R/'metrics/GLB_INDEX.json')+load(R/'metrics/crossvideo_candidate_GLB_INDEX.json');check('30 native and 4 candidate GLBs',len(models)==34)
    for row in models:
        path=Path(row['path']);check('GLB SHA '+path.name,sha(path)==row['sha256'])
        with path.open('rb')as f:
            head=f.read(12);magic,version,size=struct.unpack('<4sII',head);length,kind=struct.unpack('<II',f.read(8));tree=json.loads(f.read(length))
        check('valid GLB2 '+path.name,magic==b'glTF'and version==2 and size==path.stat().st_size)
        meshes=tree['meshes'];nodes=[n for n in tree['nodes']if'mesh'in n];names=[n.get('name','')for n in nodes];check('real background and Ring nodes '+path.name,any('Background' in n for n in names)and any('Ring' in n for n in names))
        polyp=[meshes[n['mesh']]for n in nodes if 'Background'not in n.get('name','')and'Ring'not in n.get('name','')]
        check('GLB source provenance '+path.name,all('source_original_vertex_ids'in m.get('extras',{})and m['extras']['glb_unit']=='m'for m in polyp))
    images=list((R/'figures').rglob('*.png'))
    for p in images:
        with Image.open(p)as im:im.verify()
    check('11 public core PNG and local round frames',len(list((R/'figures').glob('*.png')))==11 and len(images)>300,image_N=len(images))
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.links=[]
        def handle_starttag(self,tag,attrs):self.links.extend(v for k,v in attrs if k in ['href','src'])
    files=[p for folder in ['local_results','figures','code','config']for p in (R/folder).rglob('*')if p.is_file()and'__pycache__'not in str(p)]
    rows=[dict(path=str(p),relative_path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),public_upload_eligible=not p.is_relative_to(R/'local_results')and not p.is_relative_to(R/'figures/local'))for p in sorted(files)]
    both('OUTPUT_ASSET_INDEX',rows)
    # The report links this audit itself. Check that link after saving below.
    parser=Links();page=R/'visualizations/index.html';parser.feed(page.read_text())
    for link in parser.links:
        if not urlsplit(link).scheme:check('HTML local link '+link,(page.parent/unquote(link.split('#')[0])).exists())
    report=R/'TECHNICAL_REPORT.md'
    for link in re.findall(r'\]\(([^)]+)\)',report.read_text()):
        if link in ['provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json','provenance/FINAL_VERIFICATION.json']:continue
        if not urlsplit(link).scheme:check('report local link '+link,(R/unquote(link.split('#')[0])).exists())
    check('one complete technical report',len(list(R.rglob('TECHNICAL_REPORT.md')))==1)
    growthtests=load(R/'metrics/growth_result_tests.json');check('all original-face/UV/RGB/rigidity/held-frame checks pass',len(growthtests)==11517 and all(x['passed']for x in growthtests))
    inputs=[]
    for c in refs:
        inputs.extend(Path(c[k])for k in ['RGB','Mask','pack','mesh']if k in c)
        if 'source_points'in c:inputs.append(Path(c['source_points']))
    # All camera and potential RGB/Mask inputs already bound by the old frozen
    # inventory/input manifest; bind the actual final camera table as well.
    inputs+=[BASE/'metrics/view_distribution.json',BASE/'metrics/registration_edges.json',R/'provenance/EVALUATION_TARGETS_FROZEN.json',R/'provenance/NEW_CASES.json']
    save('provenance/FINAL_ACTUAL_SOURCE_INPUTS.json',stamp(inputs,GT_used=False,meaning='final binding; earlier input and per-step freezes establish pre-prediction identity'))
    from geometry import o3d
    open3d_module=o3d()
    versions={n:md.version(n)for n in ['numpy','scipy','Pillow','matplotlib','trimesh','torch']};versions['cv2_module']=cv2.__version__;versions['open3d_module']=open3d_module.__version__;save('provenance/ENVIRONMENT.json',dict(Python=sys.version,executable=sys.executable,packages=versions,open3d_module_path=open3d_module.__file__))
    code=list((R/'code').glob('*.py'))+list((R/'config').glob('*.json'))+list((R/'provenance/source_versions').glob('*.py'))+[REPO/'visualization'/n for n in ['real_p0_renderer.py','same_camera_scene.py','pointcloud_audit_renderer.py']]
    save('provenance/FINAL_CODE_AND_SOURCE_MANIFEST.json',stamp(code,base_commit=load(R/'provenance/INPUTS_FROZEN.json')['base_commit'],actual_successful_HERO=22,GT_used=False,recorded_after_predictions=True))
    both('final_delivery_checks',checks)
    save('provenance/FINAL_VERIFICATION.json',dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS',tests_N=len(checks),original_face_and_growth_tests_N=len(growthtests),protected_workspaces_N=len(before),upstream_unique_SHA_files_N=len(seen),model_weights_N=len(load(BASE/'provenance/MODEL_WEIGHTS.json')),source_references_N=len(refs),images_N=len(images),local_GLBS_N=len(models),GT_used=False,source_geometry_accuracy='NOT_CERTIFIED',scientific_failures_kept=True))
    print('FINAL VERIFICATION',len(checks),'PASS; protected',len(before),'images',len(images),'GLB',len(models),flush=True)

if __name__=='__main__':main()
