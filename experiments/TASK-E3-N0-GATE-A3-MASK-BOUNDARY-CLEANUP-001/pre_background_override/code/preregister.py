from common import *

def main():
    assert not (R/'config/A3_PREREGISTERED.json').exists()
    assert git(REPO,'rev-parse','HEAD')=='75ba88303f5ca2e3eee362451d7a717d92506e10'
    assert git(A2.parents[1],'status','--porcelain=v1','--untracked-files=all')==''
    checks=[]
    for root in [BASE,A2]:
        for a in load(root/'DELIVERY_INDEX.json')['files']:
            assert sha(a['path'])==a['sha256'];checks.append(a)
        checks.append(asset(root/'DELIVERY_INDEX.json'))
    for row in MANIFEST['sources']:
        for a in row['assets'].values():
            assert sha(a['path'])==a['sha256'];checks.append(a)
    checks.append(asset(CAD))
    for a in load(A2/'LOCAL_RESULTS_INDEX.json')['files']:
        assert sha(a['path'])==a['sha256'];checks.append(a)
    old=read_csv(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv');orange=[r for r in old if r['category']=='B_DEPTH_LAYER_RETAIN'];assert len(orange)==1929
    save('config/A3_PREREGISTERED.json',dict(task=R.name,parent_commit=git(REPO,'rev-parse','HEAD'),source_order=IDS,versions=VERSIONS,orange_input=asset(A2/'PROJECTIVE_CLEANUP_DECISIONS.csv'),expected_B=1929,V1_N=105875,
        primary_rule='B only; inside original Polyp Mask, exact native identity and certain mapping; distance<=2 native pixels -> V2 suppress; >2 retain',boundary_native_px=2.,search_rounds=1,
        mask_coordinate_definition=dict(input='unchanged original archived640x360 Polyp labels',native_WH=[640,352],archive_WH=[640,360],native_to_archive='exact inherited K_archive @ inv(K_native), with half-pixel pixel centers',
            distance='Euclidean distance from continuous mapped candidate center to nearest NON-Polyp original MASK PIXEL CENTER; not to cell edge; no extra0.5 subtraction',
            metric_native_units='original y coordinates times352/360; original x times640/640',implementation='original-mask exact scipy EDT for integer centers; equivalent KDTree for continuous mapped query',image_exterior='one virtual non-Polyp pixel border',
            membership='floor(archive_uv+0.5); native legacy label must agree; mismatch is exception, retained',crop_grid='never measure boundary in320x240'),
        V1='A2 exact baseline copies, including historical46 and A2red223',V2='mask only qualified orange<=2px',V3='mask all identity/membership/mapping-qualified orange; exceptions protected under explicit no-auto-delete rule; if any, report V3_ALL_B_INCOMPLETE, never silently drop them',
        safety='all non-B, redA prior exclusions, purpleC, greenD unchanged; outside/identity/mapping failures retained in V2/V3 and listed',reversible=True,
        common_model_domain=load(A2/'MODEL_DOMAIN_COMPARISON.json')['current_candidate'],crop='exact inherited make_crop with originalMask; A/K/c2w all unchanged, same nearest IDs',
        diagnostics=dict(raw_distance_proxy_mm=1.,jump_mm=1.,area_proxy='Z^2/(fx*fy), not actual surface area',
            component='8-connectivity for native/crop valid masks; holes=fill_holes(valid)-valid; no repair',
            body='distance>2 native px under primary ORIGINAL-mask metric; V1-fixed denominator',
            head='original nativePolyp connected component with maximum overlap of camera rays through inner Ring at RingZ=0',
            side='other original Polyp components; anatomical proxy, not certified tissue label',
            possible_thin='existing native medial-ridge width<=6 proxy diagnostic only; if none NOT_EVALUABLE, no new hard gate',
            fixed_cases='reuse A2 ref03/r04/r00 fixed original/selectedIDs; distinguish suppressed observation from corrected error',
            fixed_jump_denominator='V1 legal4-neighbour pairs; unavailable pairs reported separately',historical_3px_gate='REVOKED_BY_USER_FOR_A3_ONLY; historical GateA/A2 FAIL kept unchanged'),
        acceptance='engineering integrity PASS required; scientific improvement assessed separately; no3px blocker; no GT certification of real surface loss; recommend at most controlled V1/V2 future ablation, not automatic GateB',
        prohibited=['GPU','NNforward','training','newHERO','newTSDF','camera optimization','GT/Oracle','original mutations']))
    save('config/PROTECTED_START.json',dict(worktrees=protected_state(),assets=checks,A2_head=git(A2.parents[1],'rev-parse','HEAD')))
    save('config/BEFORE_RESULTS.json',dict(protocol=asset(R/'config/A3_PREREGISTERED.json'),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('A3_FROZEN',sha(R/'config/A3_PREREGISTERED.json'),flush=True)

if __name__=='__main__':main()
