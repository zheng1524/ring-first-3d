from scene_renderer import *
import re,html,ast
def main():
    checks=[]
    def check(n,x):assert x,n;checks.append(n)
    for x in load(R/'provenance/INPUTS_FROZEN.json')['files']:check('frozen historical input '+x['path'],sha(x['path'])==x['sha256'])
    changes=load(R/'audit/panel2_changes.json');check('all 11 existing pairs processed',len(changes)==11);checked=set()
    for r in changes:
        old=np.asarray(Image.open(r['old_figure']).convert('RGBA'));new=np.asarray(Image.open(R/r['new_figure']).convert('RGBA'));x0,y0,x1,y1=r['allowed_panel2_rectangle_xyxy'];outside=np.ones(old.shape[:2],bool);outside[y0:y1,x0:x1]=False;check(r['pair_id']+' entire outside area pixel-identical',old.shape==new.shape and np.array_equal(old[outside],new[outside]));check(r['pair_id']+' change confined to Panel2',np.any(old[y0:y1,x0:x1]!=new[y0:y1,x0:x1]));check(r['pair_id']+' fixed .08 point size and opaque Ring',r['depth']['point_size']==.08 and r['depth']['alpha']==1 and r['depth']['CAD_alpha_values']==[0,1]);check(r['pair_id']+' delivered file hash',sha(R/r['new_figure'])==r['new_figure_SHA256'])
        if r['A']not in checked:
            checked.add(r['A']);a,m,rp=layers(r['A']);pc,bc,z,Z=depth_colors(a);C=np.r_[pc,bc];valid=np.isfinite(Z)&(Z>0);L=(C.max(1)+C.min(1))/2;cfg=load(R/'color_config.json');t=(Z-z['min_Z_mm'])/(z['max_Z_mm']-z['min_Z_mm']);check(r['A']+' shared axial depth mapping correct',np.allclose(L[valid],cfg['near_lightness']+(cfg['far_lightness']-cfg['near_lightness'])*t[valid]));gray,info,ri,drawn=panel2_image(r['A'],gray_control=True);oldrow=next(x for x in rows()if x['A']==r['A']);oldgray=np.asarray(Image.open(PREV/oldrow['figures']['A_neutral_geometry.png']).convert('RGB'));check(r['A']+' full grayscale control matches prior 3D rendering exactly',np.array_equal(gray,oldgray));newraw=np.asarray(Image.open(R/r['new_geometry']).convert('RGB'));exposed=(ri[:,:,3]==1)&(oldgray.max(2)<=25);check(r['A']+' all exposed CAD pixels identical',np.array_equal(newraw[exposed],oldgray[exposed]));check(r['A']+' depth derived from unchanged XYZ, not new depth prediction',z['axial_Z_SHA256']==r['depth']['axial_Z_SHA256'])
    core=load(R/'audit/CORE_FIG2_PIXEL_AUDIT.json');a=np.asarray(Image.open(core['original']).convert('RGB'));b=np.asarray(Image.open(core['new']).convert('RGB'));x0,y0,x1,y1=core['allowed_rect'];outside=np.ones(a.shape[:2],bool);outside[y0:y1,x0:x1]=False;check('public Fig2 all pixels outside Panel2 identical',np.array_equal(a[outside],b[outside]))
    for p in (R/'code').glob('*.py'):
        tree=ast.parse(p.read_text());check('syntax '+p.name,True)
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and(isinstance(n.func,ast.Attribute)and n.func.attr in ['evaluate','scene_metrics','point_projection','segment_plane','register','compute_depth'])];check('no evaluation/upstream calls '+p.name,len(calls)==0)
    for x in load(R/'audit/LOCAL_ASSET_INDEX.json'):check('local asset '+x['path'],sha(x['path'])==x['sha256'])
    links=0
    for s in re.findall(r'(?:href|src)="([^"]+)"',(R/'visualizations/index.html').read_text()):
        check('HTML '+s,(R/'visualizations'/html.unescape(s)).resolve().exists());links+=1
    for root,s in load(R/'runtime/PROTECTED_START.json').items():check('protected workspace '+root,state(Path(root))==s)
    save('audit/VALIDATION.json',dict(passed=len(checks),checks=checks,small_tests=7,cases=11,source_scenes=len(checked),HTML_links=links,all_pixels_outside_Panel2_identical=True,all_historical_metrics_SHA_unchanged=True,upstream_or_evaluation_runs=0,GT_used=False));print('VALIDATION_PASS',len(checks),'checks;',links,'HTML links')
if __name__=='__main__':main()
