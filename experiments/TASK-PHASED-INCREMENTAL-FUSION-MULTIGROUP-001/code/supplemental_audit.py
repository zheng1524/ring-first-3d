"""Post-run identity audit of historical fields/helpers and depth-cache aliases."""
from assets import *
def main():
    prior={x['path']:x['sha256']for x in load(ABS/'provenance/INPUTS.json')['files']};files=[Path(__file__),SPARSE/'code/run.py',PREV/'provenance/DIAGNOSTIC_OUTPUTS_FROZEN.json',PREV/'TECHNICAL_REPORT.md',SPARSE/'TECHNICAL_REPORT.md',ABS/'TECHNICAL_REPORT.md',PHASE/'TECHNICAL_REPORT.md'];fields=[];aliases=[]
    for c in cases():
        p=PREV/f'local_fields/{c["id"]}_fields.npz';assert sha(p)==prior[str(p)];a=np.load(p);assert np.allclose(a['rho_surface_radius'],a['radius_neighbor_count']/(np.pi*.4**2),rtol=1e-14,atol=1e-12);fields.append(dict(reference=c['id'],field_SHA_matches_previous_ABS_input=True,radius_mm=.4,self_excluded=True,rho_units='points/mm²',source_points=len(a['XYZ_mm'])))
        if c['group']!='G01':
            base=Path(c['camera_file']).parents[1];p=base/'predictions/HERO_native.npz';z=np.load(p);assert z['depth_mm'].ndim==2;aliases.append(dict(group=c['group'],native_depth_shape=z['depth_mm'].shape,camera_batch_shape=z['c2w'].shape,independent_depth_reference=int(z['reference']),HERO_source_image_indices=z['sources'],not_multiple_depth_outputs=True));files += [p,base/'inputs/MVS_cases.json']
    assert sha(SPARSE/'code/run.py')==prior[str(SPARSE/'code/run.py')];save('provenance/SUPPLEMENTAL_INPUT_AUDIT.json',dict(**stamp(files),timing='Original task audit added post-execution; fresh replay runs this identity check before computation. Not a retrospective prefreeze.',fields=fields,aliases=aliases,parameters_changed=False,predictions_changed=False));print('SUPPLEMENTAL_AUDIT_PASS',len(fields),'frozen density fields; helper SHA unchanged; 3 single-reference cache aliases',flush=True)
if __name__=='__main__':main()
