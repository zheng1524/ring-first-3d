"""Existing FIT input completion only; reuse the identical native builder."""
from pathlib import Path
from types import SimpleNamespace
import sys,difflib,numpy as np
from PIL import Image
import pipeline as p
import bootstrap_references as old
from ring_first_3d.mainline.native.io import save_json,sha256
CAT=Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-PYTORCH3D-014/config/ALL_VIEWS.json')

def prepare(g,vi):
    fit=[v for v in p.instance_views(g,vi) if v['meta']['role']=='FIT'];pool=list(fit);seen={v['meta']['RGB_content_sha'] for v in pool};held={v['meta']['RGB_content_sha'] for v in p.views() if v['meta']['role']!='FIT'};rejections=[]
    for m in p.read(CAT):
        if m.get('case')!=g or m.get('video')!=vi or m.get('role')!='FIT':continue
        rgbp=p.resolve_asset(m['RGB_source']);labp=p.resolve_asset(m['Mask_source'])
        if not rgbp.is_file() or not labp.is_file():rejections.append(dict(id=m['id'],reason='MISSING_SOURCE_FILE'));continue
        rgb=np.array(Image.open(rgbp).convert('RGB'));lab=np.array(Image.open(labp));h=p.arraysha(rgb)
        if h in held:rejections.append(dict(id=m['id'],reason='CURRENT_HOLDOUT_PIXEL_IDENTITY'));continue
        if h in seen:continue
        assert rgb.shape==(360,640,3) and lab.shape==(360,640) and np.isin(lab,[0,1,2]).all()
        for k,fn in [('RGB_sha',rgbp),('Mask_sha',labp)]:
            if m.get(k):assert sha256(fn)==m[k],str(fn)
        cp=p.TASK/'audit/REFERENCE_DENSITY_REV2'/g/vi/'inputs'/(m['id']+'.npz');cp.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(cp,RGB=rgb,labels=lab,K=m['K'])
        meta={k:v for k,v in m.items() if k not in ['T','T_original','Delta_T','HERO_sources']};meta.update(case=g,video=vi,role='FIT',RGB_source=str(rgbp),Mask_source=str(labp),RGB_content_sha=h,Mask_content_sha=p.arraysha(lab))
        pool.append(dict(meta=meta,cache=p.asset(cp)));seen.add(h)
    assert len(pool)>=8 and pool[4]['meta']['id']==fit[4]['meta']['id']
    lock=p.TASK/'audit/REFERENCE_DENSITY_REV2'/g/vi/'INPUT_FREEZE.json';save_json(lock,dict(catalog=p.asset(CAT),protocol=p.asset(p.TASK/'PROTOCOL_REF_DENSITY_REV2.yaml'),Body_views_unchanged=[v['meta']['id'] for v in fit],calibration_views=pool,rejections=rejections,old_camera_HERO_GT_used=False,source=p.asset(Path(__file__)),native_builder=p.asset(Path(old.__file__))))
    return pool

def main(group=None,video=None):
    p.verify();affected=[]
    for g in p.GROUPS:
        for vi in ['004','005']:
            if group and group!=g or video and video!=vi:continue
            if p.inherited(g,vi):continue
            base=p.OUT/g/vi
            if not (base/'bank/ADMISSION.json').exists() or p.read(base/'bank/ADMISSION.json')['status']!='PASS':continue
            fit=[v for v in p.instance_views(g,vi) if v['meta']['role']=='FIT'];cams=[base/'camera'/v['meta']['id']/'ADMISSION.json' for v in fit]
            if not all(f.exists() for f in cams) or all(p.read(f)['status']=='PASS' for f in cams):continue
            if (p.TASK/'audit/REFERENCE_DENSITY_REV2'/g/vi/'INPUT_FREEZE.json').exists():continue
            affected.append((g,vi,prepare(g,vi)))
    for g,vi,pool in affected:
        base=p.OUT/g/vi;history=p.TASK/'runs/REF_BUILD_REV1_RESULTS'/g/vi;assert not history.exists();history.parent.mkdir(parents=True,exist_ok=True);base.rename(history)
        source=Path(old.__file__).read_text();adapter=source.replace("assert len(fit)==8","assert len(fit)>=8").replace("roles=['FIT']*8","roles=['FIT']*len(fit)").replace('reference_build/REV1','reference_build/REV2').replace('PROTOCOL_REF_BUILD_REV1.yaml','PROTOCOL_REF_DENSITY_REV2.yaml')
        scope=p.TASK/'audit/REFERENCE_DENSITY_REV2'/g/vi
        (scope/'DATA_ADAPTER.py').write_text(adapter);(scope/'DATA_ADAPTER.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),adapter.splitlines(True),fromfile='native_reference_REV1',tofile='same_builder_expanded_inputs_REV2')))
        # All source functions and numerical parameters are inherited exactly;
        # only input count/provenance and output version differ.
        ns=dict(__name__='reference_input_completion',__file__=str(Path(old.__file__)));exec(compile(adapter,str(Path(old.__file__)),'exec'),ns)
        proxy=SimpleNamespace(**{k:getattr(p,k) for k in dir(p) if not k.startswith('_')});proxy.instance_views=lambda gg,vv,pool=pool,g=g,vi=vi:pool if (gg,vv)==(g,vi) else p.instance_views(gg,vv)
        ns['p']=proxy;ns['build_one'](g,vi)
        ad=base/'bank/ADMISSION.json'
        if ad.exists():r=p.read(ad);r['input_completion_revision']='REF_DENSITY_REV2';r['calibration_FIT_count']=len(pool);save_json(ad,r)

if __name__=='__main__':main()
