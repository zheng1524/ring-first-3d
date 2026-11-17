"""Read-only delivery checks. Recompute diagnostics from delivered predictions, not models."""
from io_utils import *
from freeze import state
import re,html,ast,subprocess
def main():
    checks=[]
    def check(name,test):
        if not test:raise AssertionError(name)
        checks.append(name)
    verify_predictions();check('298 frozen prior files unchanged',len(load(R/'provenance/PREDICTIONS_FROZEN.json')['files'])==298)
    oldinputs=load(PREV/'provenance/INPUTS.json')['files']
    for x in oldinputs:check('frozen upstream SHA '+x['path'],sha(x['path'])==x['sha256'])
    for p in (R/'code').glob('*.py'):ast.parse(p.read_text());check('Python3.12 syntax '+p.name,True)
    for c in cases():
        check(c['id']+' P0 pose equals actual trajectory reference',np.array_equal(np.load(c['pack'])['pose'],np.load(c['camera_file'])['c2w'][c['reference_index']]))
        cc,P,C,m,p,uv=source(c['id']);xy,z=vis.project_camera(P,p['K'],p['pose']);check(c['id']+' all original XYZ/source pixels consistent',np.max(abs(xy-uv))<1e-4)
    for path in ['OBSERVABILITY_INPUTS.json','A_TO_B_PAIRS_BEFORE_RENDER.json','PHOTO_PAIRS_BEFORE_RENDER.json','EVALUATION_ONLY_RECEIPT.json','GT_PAIRING_EVIDENCE.json']:
        for x in load(R/'provenance'/path)['files']:check(path+' SHA '+x['path'],sha(x['path'])==x['sha256'])
    before=load(R/'provenance/GT_PROTOCOL_BEFORE_ERRORS.json');original=next(x['sha256']for x in before['files']if x['path'].endswith('gt_evaluate.py'));now=(R/'code/gt_evaluate.py').read_text();old=now.replace('json.dumps(clean(gt))','json.dumps(gt)');check('GT numerical code identical to pre-error freeze; sole stdout fix',hashlib.sha256(old.encode()).hexdigest()==original)
    plan=load(R/'provenance/A_TO_B_PAIRS_BEFORE_RENDER.json')['pairs']+load(R/'provenance/PHOTO_PAIRS_BEFORE_RENDER.json')['pairs'];executed=[x for x in plan if x['executable']];rows=load(R/'metrics/a_to_b_results.json');check('22 executable / 88 explicitly unexecuted / 110 inventory',len(executed)==22 and sum(not x['executable']for x in plan)==88 and len(plan)==110);check('22 actual result rows',len(rows)==22)
    for r in rows:
        row=next(x for x in executed if x['pair_id']==r['pair_id']);c,P,C,m,p,uv=source(row['A']);a=np.load(R/r['prediction_file']);valid=a['valid'];face=a['face_id'][valid];w=a['source_barycentric'][valid];weights=np.c_[1-w.sum(1),w];expected=np.rint(np.clip((C[m.faces[face]]*weights[:,:,None]).sum(1),0,1)*255).astype(np.uint8)
        check(r['pair_id']+' A source RGB exact barycentric identity',np.array_equal(expected,a['RGBA'][valid,:3]));check(r['pair_id']+' no B color/depth/Mask prediction inputs',not r['B_RGB_used_in_prediction']and not r['B_depth_used_in_prediction']and not r['B_Mask_used_to_modify_prediction']);check(r['pair_id']+' valid original face references',np.all(face<len(m.faces))and np.all(weights>=-1e-5));check(r['pair_id']+' positive depth/CAD occlusion',np.all((a['z_mm'][valid]>0)&(a['z_mm'][valid]<=a['known_CAD_z_mm'][valid]+.050001)))
        B=np.asarray(Image.open(row['B_target']['RGB']).convert('RGB'));lab=cv2.imread(row['B_target']['Mask'],0);mask=lab==1;common=valid&mask;err=abs(a['RGBA'][:,:,:3].astype(float)-B.astype(float)).mean(2);check(r['pair_id']+' independent target/support denominator',r['common_pixels']==int(common.sum())and r['target_Polyp_pixels']==int(mask.sum())and r['prediction_valid_pixels']==int(valid.sum())and r['predicted_outside_target_pixels']==int((valid&~mask).sum()));check(r['pair_id']+' RGB error independently recomputed',abs(r['RGB_MAE_0_255']-err[common].mean())<1e-10);check(r['pair_id']+' full prediction retained SHA',sha(R/r['prediction_file'])==r['prediction_SHA256']);check(r['pair_id']+' actual complete PNG',Image.open(R/r['figure']).size==(3510,1040))
        if'CANDIDATE'in r['pose_status']:check(r['pair_id']+' candidate has NO reliable cross-source baseline',r['reliable_cross_source_baseline_mm']is None)
    h=load(R/'metrics/gt_height_evaluation.json');oh=load(R/'prediction_snapshot/C_height_geometry.json');d=load(R/'metrics/gt_dxy_evaluation.json');od=load(R/'prediction_snapshot/D_observed_surface_definition_audit.json');check('all 27 height rows,10 finite,17 NE',len(h)==27 and sum(x['H_pred_mm']is not None for x in h)==10);check('all 81 diameter formal failures retained',len(d)==81 and all(x['formal_Dxy_mm']is None and x['original_formal_measurement_status']=='NOT_EVALUABLE'for x in d));check('72 diagnostic candidates retained',sum(x['Dxy_candidate_mm']is not None for x in d)==72)
    for a,b in zip(h,oh):check('height unchanged '+a['source_id']+a['roi_id'],a['H_pred_mm']==b['H95_mm']and a['diagnostic_H_candidate_mm']==b['diagnostic_H95_candidate_mm'])
    for a,b in zip(d,od):check('Dxy unchanged '+a['source_id']+a['roi_id']+a['model'],a['Dxy_candidate_mm']==b['diagnostic_candidate_Dproj_mm']and a['endpoint_observation_support']==b['endpoint_observation_support'])
    for x in load(R/'evaluation_only/BLENDER_VERIFICATION.json'):check(x['group']+' original blend SHA / cached export exact',sha(x['source'])==x['sha256']and x['cached_export_exact'])
    for x in load(R/'metrics/gt_asset_manifest.json'):check('surface evaluation NE '+x['prediction_scene'],x['surface_evaluable']=='NOT_EVALUABLE'and not x['Ring_GT_geometry'])
    for r in h:
        if r['H_pred_mm']is not None:check('height error arithmetic '+r['source_id']+r['roi_id'],abs(r['error_mm']-(r['H_pred_mm']-r['H_gt_mm']))<1e-12)
    for r in d:
        if r['Dxy_candidate_mm']is not None:check('Dxy error arithmetic '+r['source_id']+r['roi_id']+r['model'],abs(r['error_mm']-(r['Dxy_candidate_mm']-r['Dxy_gt_mm']))<1e-12)
    frames=load(R/'metrics/camera_frame_inventory.json');inv=load(R/'metrics/source_view_inventory.json');check('four groups,21 raw sources,62 camera candidates',len(inv)==21 and len(frames)==62 and len({x['group_id']for x in inv})==4);check('no fabricated photo pose in formal inventory',all(not x['camera_pose_exists']and x['coordinate_frame']=='UNREGISTERED'for x in inv if x['source_type']=='photo'));check('all six photo poses remain unaccepted',len(load(R/'metrics/photo_pose_candidates.json'))==6 and all(not x['accepted']for x in load(R/'metrics/photo_pose_candidates.json')));check('cross-source reliable baseline/angle absent',all(x['baseline_mm']is None and x['optical_axis_angle_deg']is None for x in load(R/'metrics/source_graph_edges.json')))
    for x in load(R/'metrics/local_asset_index.json'):check('local indexed asset '+x['relative_path'],Path(x['path']).exists()and sha(x['path'])==x['sha256'])
    text=(R/'visualizations/index.html').read_text();links=re.findall(r'(?:href|src)="([^"]+)"',text)
    for s in links:
        path=(R/'visualizations'/html.unescape(s)).resolve();check('HTML local link '+s,path.exists())
    check('one full technical report',len(list(R.rglob('TECHNICAL_REPORT.md')))==1)
    tech=(R/'TECHNICAL_REPORT.md').read_text();check('four true public core embeds',len(re.findall(r'!\[.*?\]\(',tech))==4)
    before=load(R/'provenance/PROTECTED_START.json');protected=[]
    for p,old in before.items():
        same=state(Path(p))==old;check('protected workspace unchanged '+p,same);protected.append(dict(path=p,unchanged=same,HEAD=old['HEAD'],tracked_modifications_sha256_unchanged=True))
    both('protected_workspaces',protected)
    save('metrics/VALIDATION.json',dict(passed=len(checks),checks=checks,small_tests=load(R/'metrics/small_tests.json'),HTML_links=len(links),scientific_status='DIAGNOSTIC_ONLY; no baseline acceptance',new_prediction_generation=False));print('VALIDATION_PASS',len(checks),'HTML',len(links))
if __name__=='__main__':main()
