"""Separate exact observed-surface diameter from full-footprint completeness.

The preregistered 80% convex-hull fill gate is preserved in the original table.
That gate is NOT in the user's Dproj definition: concavity and real holes can
lower hull fill without making the maximum of an observed face union undefined.
No threshold, surface, endpoint, or plane is changed here. This is a disclosed
post-hoc definition audit, never a preregistered or clinical measurement success.
"""
from metric_geometry import *
def main():
    save('provenance/FERET_DEFINITION_AUDIT_FROZEN.json',dict(**stamp([Path(__file__),R/'metrics/D_projected_diameter.json']),post_hoc=True,reason='User defines diameter of effective observed surface projection, not convex/full anatomical footprint. Preserve initial strict results; retain observed-surface numeric values only with usable plane, original camera, sufficient supported model and supported original endpoints.',no_prediction_or_threshold_change=True))
    rows=[]
    for r in load(R/'metrics/D_projected_diameter.json'):
        other=[x for x in r['not_evaluable_reasons']if x!='OPEN_PROJECTION_NOT_SUFFICIENTLY_SUPPORTED'];endcheck=[]
        for ep in r['endpoints']:
            cid=ep['reference'];a=np.load(ep['parent_mesh_file']);photo=a['original_photo_support'];idx=ep['source_vertex_id'];ok=bool(photo[idx])if idx is not None else bool(np.all(photo[np.array(ep['source_edge_original_ids'],int)]));endcheck.append(ok)
        if len(endcheck)!=2 or not all(endcheck):other.append('DIAMETER_ENDPOINT_NOT_OBSERVATION_SUPPORTED')
        value=r['diagnostic_candidate_Dproj_mm']if not other else None;rows.append(dict(**r,strict_initial_status=r['status'],strict_initial_Dproj_mm=r['Dproj_mm'],observed_surface_Dproj_mm=value,observed_surface_status='MODEL_OBSERVED_SURFACE_PROTOTYPE_POSTHOC_AUDIT'if value is not None else'NOT_EVALUABLE',observed_surface_failure_reasons=other,endpoint_observation_support=endcheck,post_hoc_definition_audit=True,clinical_full_Dxy_mm=None,footprint_completeness_certified=False))
    save('metrics/D_observed_surface_definition_audit.json',rows);csvsave('metrics/D_observed_surface_definition_audit.csv',rows);print('FERET_DEFINITION_AUDIT',sum(x['observed_surface_Dproj_mm']is not None for x in rows),'of',len(rows),'conditions; initial strict results unchanged',flush=True)
if __name__=='__main__':main()
