# 017 frozen protocol

18 native HERO sources in four physical groups; G01 11, G03 1, G05 1, G06 5. Video004 only. No old Gate exclusion, no new HERO.

{
  "seed": 20261110,
  "groups": [
    "G01",
    "G03",
    "G05",
    "G06"
  ],
  "source_counts": {
    "G01": 11,
    "G03": 1,
    "G05": 1,
    "G06": 5
  },
  "representations": [
    "ARCHIVE_RAW",
    "NATIVE_GRID"
  ],
  "inherited_density": {
    "task": "TASK-PHASEC-DENSITY-MULTIGROUP-001",
    "status": "APPROVED_EXPERIMENTAL_DIAGNOSTIC_ONLY",
    "radius_mm": 0.4,
    "knn_k": 12,
    "normal_k": 16,
    "minimum_cos_incidence": 0.15,
    "maximum_nonplanarity": 0.1,
    "score_threshold": 0.5,
    "D0": "clip(min(rho_radius/rho_expected,rho_knn/rho_expected),0,1)",
    "continuity_score": "1/(1+max(0,max_neighbor_tangent_normalized_stretch-1)+max_neighbor_abs_delta_log_density/log(2))",
    "D1": "max(D0,continuity_score), conservative conjunction, never deletes points",
    "density_gradient": "source 8-neighbor maximum abs delta log normalized density per source-pixel distance; physical gradient also retained",
    "candidate_rule": "score < 0.5 and normalization reliable; unknown remains NaN",
    "minimum_regular_screened_frames": 3,
    "normalization": "rho_expected=fx*fy*abs(dot(n_cam,K^-1 pixel))/Z^2; axial Z in mm; n from local P0 PCA",
    "mask_boundary_px": 3,
    "Ring_neighbor_px": 3,
    "cross_reference_conflict_mm": 0.3,
    "source_neighbors": [
      [
        1,
        0
      ],
      [
        0,
        1
      ],
      [
        1,
        1
      ],
      [
        -1,
        1
      ]
    ],
    "parameter_search_runs": 0,
    "point_deletions": 0,
    "GT_used": false,
    "view_angle_deg": [
      0,
      0
    ],
    "physical_scale": "mm",
    "G01_bin_width_mm": 1.0,
    "minimum_tangent_eigen_ratio": 0.02
  },
  "thresholds": {
    "stretch_perspective": 8.0,
    "stretch_tangent": 4.0,
    "native_depth_jump_mm": 0.5,
    "normal_coherence": 0.7,
    "neighbor_angle_deg": 65.0,
    "needle_quality": 0.15,
    "edge_native_px": 2.0,
    "incidence_min": 0.2,
    "ring_near_mm": 0.3,
    "ring_inside_mm": 0.02,
    "ring_inside_samples_min": 2,
    "competition_mm": 0.02,
    "competition_k": 32,
    "density_warning": 0.25,
    "small_component_area_fraction": 0.001
  },
  "rule": "REJECT only (severe perspective AND reliable tangent stretch AND native depth jump AND needle/normal kink AND near original Mask edge AND non-grazing) OR (sampled CAD material penetration AND native depth jump AND needle/normal kink AND non-grazing); invalid/native-unbound/occluded/grazing is UNKNOWN and retained. All other anomalies UNCERTAIN retained.",
  "independence": "stretch/needle/area/density and depth jump/normal are correlated consequences of the same depth surface; not independent votes. Source-edge context and CAD are separate support; labels are uncalibrated artifact evidence, not truth.",
  "all_groups_same_rule": true,
  "threshold_search": 0,
  "GT": false,
  "multiview_loss": false,
  "multiview_deletion": false,
  "vertex_update": false,
  "interpolation": false,
  "hole_filling": false,
  "native_grid_definition": "unfiltered two-triangle pixel lattice [a,b,c],[b,d,c], only all vertices finite positive native depth and nearest original Mask Polyp. No max-depth-jump prefilter. Stable lattice ID=2*(v*(W-1)+u)+side; created index topology, not original archive face identity.",
  "archive_definition": "exact existing single-reference vertex/face arrays, original face IDs unchanged; archive often historical bilinear depth 352->360. Output subsets preserve all input vertex values.",
  "boundary_definition": "EDT distance between foreground sample centre and closest background sample centre, padded background at image border; no half-pixel subtraction; mask mapped to native with frozen K, nearest pixel centre floor(u+.5).",
  "nearest_competition": "32 face-centroid candidates, exact point-to-triangle distance, exclude all vertex-sharing faces. Incomplete screen; UNCERTAIN only.",
  "CAD_sampling": "vertices, 3 edge midpoints, centroid, signed distance nsamples=3; watertight winding-consistent CAD required. Finite samples do not certify absence of intersection.",
  "safeguards": "No automatic threshold relaxation or additional deletion round. Any continuity/coverage loss is reported, not hidden. All retained vertices unchanged, only face subset. No anatomy labels/true-error GT."
}
