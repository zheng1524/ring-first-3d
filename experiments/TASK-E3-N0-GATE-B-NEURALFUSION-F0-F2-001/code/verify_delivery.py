"""Read-only replay of identities, arithmetic and geometry serialization checks."""
from common import *
def main():
    validations=load(R/'FINAL_VALIDATION.json')
    assert validations['GPU_pipeline_forward_N']==2 and validations['optimizer_steps']==0
    assert not list(R.glob('*_F1_RUN.json'))and not list(R.glob('*_F2_RUN.json'))
    for row in load(R/'provenance/FROZEN_INPUTS.json')['sources']:
        assert sha(row['original']['path'])==row['original']['sha256']
        assert sha(row['frozen']['path'])==row['original']['sha256']
    for a in load(R/'provenance/ORIGINAL_SHA_START.json')['files']:assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/OFFICIAL_CHECKED_FILES.json')['files']:assert sha(a['path'])==a['sha256']
    for v in ['V6','V2']:
        before=load(R/f'provenance/BEFORE_NN_{v}_F0.json')
        assert sha(before['protocol']['path'])==before['protocol']['sha256']
        assert all(sha(a['path'])==a['sha256']for a in before['code'])
        run=load(R/f'NN_{v}_F0_RUN.json');assert run['learned_parameters_bitwise_unchanged']and run['optimizer_steps']==0
        assert run['official_GPU_unprojection_error_max_mm']<1e-4
        for method in ['NN','O3D']:
            metric=load(R/f'{method}_{v}_F0_METRICS.json');assert not metric['F0_pass']
            p=np.load(R/'local_results'/f'{method}_{v}_F0_evaluation.npz')
            for row in metric['rays']:
                cid=row['source'];ids=p[cid+'_native_id'];cat=p[cid+'_category']
                assert np.array_equal(ids,native(cid,'V2')['ids'])
                assert len(ids)==row['fixed_V2_observation_N']
                assert np.sum(cat=='MISS')==row['miss_N']
                assert np.sum(cat=='AGREE')==row['agree_N']
                assert row['agree_N']+row['near_N']+row['far_N']+row['miss_N']==row['CAD_visible_N']
                assert row['CAD_visible_N']+row['CAD_occluded_N']==len(ids)
            a=output_mesh(method,v,'F0');b=trimesh.load(R/'meshes'/f'{method}_{v}_F0_m.glb',force='mesh',process=False)
            assert np.array_equal(a.faces,b.faces)
            assert np.max(abs(np.asarray(a.vertices)-np.asarray(b.vertices)*1000))<1e-5
    print('READ_ONLY_VERIFICATION_PASS: input identities, original assets, frozen code/thresholds, fixed denominators, four meshes/SI conversion; no inference or training.',flush=True)
if __name__=='__main__':main()
