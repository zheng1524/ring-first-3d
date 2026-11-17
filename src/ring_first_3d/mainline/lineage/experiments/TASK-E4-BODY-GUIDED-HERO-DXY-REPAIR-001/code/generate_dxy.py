"""A1 official API/provenance adapter extended to the 75 current sources."""
from pathlib import Path
import sys,os,json,hashlib,time,ast
R=Path(__file__).resolve().parents[1];DXY=Path('/home/liu/new-polyp-dxy')
sys.dont_write_bytecode=True
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
def load(p):return json.loads(Path(p).read_text())
orig=R.parents[1]/'experiments/TASK-E4-A1-ELLIPSE-VS-FULLMASK-001/code/generate_dxy.py'
tree=ast.parse(orig.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','asset','clean','guard']]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(orig),'exec'))
def save(name,x):
    p=R/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(clean(x),ensure_ascii=False,indent=2)+'\n')
sys.addaudithook(guard)
import numpy as np
sys.path.insert(0,str(DXY/'src'))
from dxy_mid.pipeline import measure_files,measure_frame,VERSION
def one(cid):
    target=R/'provenance/dxy_records'/(cid+'.json')
    if target.exists():return load(target)
    c=next(x for x in load(R/'config/SOURCE_BINDING.json') if x['source_id']==cid)
    rgbsha=c['RGB_source']['sha256'];masksha=c['Mask_source']['sha256'];a=np.load(R/'inputs'/(cid+'.npz'));rgb=a['RGB'];lab=a['labels']
    assert set(np.unique(lab))=={0,1,2} and lab.dtype==np.uint8
    assert hashlib.sha256(rgb.tobytes()).hexdigest()==c['RGB_content_SHA'] and hashlib.sha256(lab.tobytes()).hexdigest()==c['Mask_content_SHA']
    idsha=hashlib.sha256((rgbsha+'|'+masksha).encode()).hexdigest()[:24];t=time.monotonic()
    rec=dict(source=cid,source_RGB=c['RGB_source'],source_Mask=c['Mask_source'],cache=c['cache'],RGB_content_SHA=c['RGB_content_SHA'],Mask_content_SHA=c['Mask_content_SHA'],DXY_commit='75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95',VERSION=VERSION,ring_id=c['ring'],inner_diameter_mm=c['inner_diameter_mm'],entrypoint='dxy_mid.pipeline.'+c['DXY_entrypoint'],image_dimensions=[640,360],input_coordinates='cache-native 640x360; K exact half-pixel transport; no JPEG intermediary',history_prediction_fallback=0,GT_read=False)
    try:
        if c['DXY_entrypoint']=='measure_files':result=measure_files(c['RGB_source']['path'],c['Mask_source']['path'],inner_diameter_mm=c['inner_diameter_mm'],source_id=idsha)
        else:result=measure_frame(np.ascontiguousarray(rgb[:,:,::-1]),lab,inner_diameter_mm=c['inner_diameter_mm'],source_id=idsha,image_sha256=c['RGB_content_SHA'],mask_sha256=c['Mask_content_SHA'])
        keep=['version','Geometry','ring_valid','ring_reason','normal_Gate_pass','Q_conflict_recovery','strict_stable','accepted','candidate_generated','stability_review_pass','geometry_state','quality_class','reason','stability_flags','P_count','Q_count','X_count','body','branch','P_zero_occlusion_inference','coordinate_system','GT_read','history_prediction_fallback','processed_mask_sha256']
        rec['quality']={k:result.audit.get(k) for k in keep};candidate=result.candidate
        if candidate is not None:rec.update(available=True,shape=candidate.shape,center_px=np.asarray(candidate.center_native),basis_px=np.asarray(candidate.basis_native),candidate_provenance=candidate.provenance)
        else:rec.update(available=False,status='NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY')
    except Exception as e:rec.update(available=False,status='DXY_RUNTIME_FAILURE',error=repr(e),quality={})
    rec['seconds']=time.monotonic()-t
    assert sha(c['RGB_source']['path'])==rgbsha and sha(c['Mask_source']['path'])==masksha
    save('provenance/dxy_records/'+cid+'.json',rec)
    print(cid,rec['available'],rec.get('quality',{}).get('quality_class'),round(rec['seconds'],2),flush=True)
    return clean(rec)
if __name__=='__main__':one(sys.argv[1])
