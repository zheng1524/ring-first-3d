"""Read-only source, projection-color, CAD and delivery checks."""
from common import *
import ast,re,html
def main():
    verify();checks=[]
    def check(n,x):
        if not x:raise AssertionError(n)
        checks.append(n)
    rows=load(R/'metrics/results.json');plan=load(R/'provenance/PAIRS_FROZEN.json')['pairs'];check('11 pairs, four independent physical groups',len(rows)==len(plan)==11 and len({r['group']for r in rows})==4)
    for n in ['real_p0_renderer.py','same_camera_scene.py','pointcloud_audit_renderer.py']:
        original=next(x for x in load(R/'provenance/INPUTS_FROZEN.json')['files']if x['path']==str(REPO/'visualization'/n));check('official renderer unchanged '+n,sha(original['path'])==original['sha256'])
    # Only display adapter changed after initial sample: scientific projection/evaluation functions exact.
    p='experiments/TASK-AB-FULL-SCENE-VIS-002/code/scene_renderer.py';initial=subprocess.check_output(['git','show','0d4285c:'+p],cwd=REPO).decode();now=(REPO/p).read_text();functions=lambda s:{x.name:ast.dump(x,include_attributes=False)for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)};f,g=functions(initial),functions(now)
    for name in f:
        if name!='scene_image':check('initial frozen scientific function unchanged '+name,f[name]==g[name])
    old=load(AUDIT/'metrics/a_to_b_results.json');reused=0
    for r in rows:
        p=next(x for x in plan if x['pair_id']==r['pair_id']);c,P,C,m,pack,uv=source(r['A']);data=np.load(r['source_geometry_path']);bg=np.load(p['background_cache']);bid=data['Background_original_cache_ids'];check(r['pair_id']+' all original P0 XYZ unchanged',np.array_equal(data['Polyp_XYZ_mm'],P));check(r['pair_id']+' original background XYZ exact IDs',np.array_equal(data['Background_XYZ_mm'],bg['XYZ_mm'][bid])and np.array_equal(bid,np.flatnonzero(bg['display'])));check(r['pair_id']+' A background RGB/source UV identities',np.array_equal(data['Background_RGB'],bg['RGB'][bid])and np.array_equal(data['Background_source_uv'],bg['source_uv'][bid]));check(r['pair_id']+' all background label0',np.all(pack['labels'][data['Background_source_uv'][:,1],data['Background_source_uv'][:,0]]==0))
        pred=np.load(r['prediction_path']);layer=pred['layer'];ids=pred['source_original_id'];colors=pred['RGBA'][:,:,:3];a=layer==1;b=layer==0;check(r['pair_id']+' point RGB exactly from A Polyp',np.array_equal(colors[a],np.rint(C[ids[a]]*255).astype(np.uint8)));check(r['pair_id']+' point RGB exactly from A background',np.array_equal(colors[b],np.rint(bg['RGB'][ids[b]]*255).astype(np.uint8)));check(r['pair_id']+' actual CAD opaque, black, positive depth',np.all(pred['RGBA'][layer==2,3]==255)and np.max(colors[layer==2])<=25 and np.all(pred['axial_depth_mm'][layer>=0]>0))
        # Independent target comparison; source rendering is already frozen on disk.
        B=np.asarray(Image.open(p['B_target']['RGB']).convert('RGB'));mask=cv2.imread(p['B_target']['Mask'],0);v,u=np.nonzero(mask==1);base=v>=np.quantile(v,.8);center=np.median(np.c_[u[base],v[base]],0);rv,ru=np.nonzero(mask==2);radius=2*max(np.ptp(u)/2,np.ptp(ru)/2);yy,xx=np.indices(mask.shape);roi=(mask==0)&(((xx-center[0])/radius)**2+((yy-center[1])/(.75*radius))**2<=1);cp=a&(mask==1);cb=b&roi;diff=np.abs(colors.astype(float)-B.astype(float)).mean(2);n=r['new_point_scene'];check(r['pair_id']+' P/BG independent complete denominators',n['Polyp_target_N']==int((mask==1).sum())and n['Background_target_ROI_N']==int(roi.sum())and n['Polyp_common_N']==int(cp.sum())and n['Background_common_N']==int(cb.sum()));check(r['pair_id']+' new independent P/BG errors',abs(n['Polyp_RGB_MAE']-diff[cp].mean())<1e-10 and abs(n['Background_RGB_MAE']-diff[cb].mean())<1e-10);check(r['pair_id']+' no B inputs to prediction',not n['B_RGB_used_for_prediction']and not n['B_Mask_used_for_prediction'])
        check(r['pair_id']+' unchanged native original source camera',np.array_equal(np.array(r['geometry_render']['c2w_display']),pack['pose']));check(r['pair_id']+' B camera source-A conversion exact',np.allclose(r['full_scene_render']['c2w_display'],p['B_camera_in_A'],atol=1e-12,rtol=0));check(r['pair_id']+' one shared source RGB point artist',r['full_scene_render']['shared_point_artist']and r['full_scene_render']['shared_point_size']==.8);check(r['pair_id']+' neutral geometry no source colors',not r['geometry_render']['source_RGB_used_for_point_colors']and r['geometry_render']['neutral']and r['geometry_render']['shared_point_size']==.08)
        gray=np.asarray(Image.open(R/r['figures']['A_neutral_geometry.png']));check(r['pair_id']+' actual Panel2 image strictly grayscale',np.array_equal(gray[:,:,0],gray[:,:,1])and np.array_equal(gray[:,:,1],gray[:,:,2]))
        for name,fp in r['figures'].items():
            im=Image.open(R/fp);im.load();check(r['pair_id']+' true PNG '+name,im.width>1000 and im.height>600)
        if p['old_pair_id']:
            original=next(x for x in old if x['pair_id']==p['old_pair_id']);check(r['pair_id']+' full legacy numeric record unchanged',all(original[k]==v for k,v in r['legacy_Polyp_only'].items()));reused+=1
        if c['group']=='G07':check(r['pair_id']+' stress identity preserved',r['pose_status']=='UNQUALIFIED_CAMERA_STRESS')
    check('four inherited pairs compare exactly',reused==4)
    for p in (R/'code').glob('*.py'):ast.parse(p.read_text());check('Python3.12 source '+p.name,True)
    for x in load(R/'metrics/LOCAL_ASSET_INDEX.json'):check('local asset SHA '+x['relative_path'],sha(x['path'])==x['sha256'])
    text=(R/'visualizations/index.html').read_text();links=re.findall(r'(?:href|src)="([^"]+)"',text);nlink=0
    for link in links:
        if link.startswith('#'):continue
        check('HTML link '+link,(R/'visualizations'/html.unescape(link)).resolve().exists());nlink+=1
    check('one full technical report',len(list(R.rglob('TECHNICAL_REPORT.md')))==1);check('four public PNG only',len(list((R/'figures').glob('*.png')))==4)
    protected=[]
    for path,oldstate in load(R/'runtime/PROTECTED_START.json').items():
        ok=state(Path(path))==oldstate;check('protected workspace '+path,ok);protected.append(dict(path=path,unchanged=ok,HEAD=oldstate['HEAD']))
    both('PROTECTED_WORKSPACES',protected);save('metrics/VALIDATION.json',dict(passed=len(checks),checks=checks,small_tests=load(R/'metrics/small_tests.json'),HTML_links=nlink,full_cases=11,independent_groups=4,reused_legacy_identical=4,GT_used=False,upstream_runs=0,scientific_claim='VISUALIZATION_RESTORED; NO_ACCURACY_IMPROVEMENT_OR_REGISTRATION_CERTIFICATION'));print('VALIDATION_PASS',len(checks),'HTML',nlink)
if __name__=='__main__':main()
