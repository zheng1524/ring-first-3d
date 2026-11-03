"""Official iso-zero extraction and fixed-original-observation monitoring.

Mesh is never filtered or smoothed. Labels are uncalibrated evidence proxies.
"""
from official_adapter import *
from skimage import measure
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def extraction_functions():
    src = R/'runtime/official_exact/code/utils/plots.py'
    tree = ast.parse(src.read_text())
    functions = {n.name: ast.get_source_segment(src.read_text(), n) for n in tree.body
                 if isinstance(n, ast.FunctionDef)}
    scope = dict(np=np, torch=torch, trimesh=trimesh, measure=measure)
    exec(compile(functions['get_grid_uniform'], str(src), 'exec'), scope)
    original = functions['get_surface_trace']
    ported = original.replace(
        '    z = np.concatenate(z, axis=0)',
        '    z = np.concatenate(z, axis=0)\n'
        '    np.save(str(path)+"/sdf_"+str(epoch)+"_model.npy", '
        'z.reshape(resolution,resolution,resolution).transpose(1,0,2))')
    ported = ported.replace('trimesh.Trimesh(verts, faces, normals)',
                           'trimesh.Trimesh(verts, faces, vertex_normals=normals, process=False)')
    (R/'provenance/OFFICIAL_EXTRACTION_PORT.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), ported.splitlines(True),
        fromfile='official/get_surface_trace', tofile='adapted/get_surface_trace')))
    exec(compile(ported, str(src), 'exec'), scope)
    return scope['get_surface_trace']


@lru_cache(None)
def observed(cid):
    n = native(cid)
    cad, _ = cast(ringscene(SCENE), n['native_uv'], n['Kn'], n['T'])
    z = n['depth'].ravel()[n['native_id']].astype(float)
    visible = ~(np.isfinite(cad) & (z > cad + .002))
    retained = np.load(N0/'frozen_inputs/native'/(cid+'.npz'))['valid']
    return dict(n, z=z, CAD=cad, visible=visible,
                available=retained.ravel()[n['native_id']])


def full_error(error):
    a = np.abs(error)
    if not len(a):
        return dict(value=None, status='NO_OBSERVATIONS')
    with np.errstate(invalid='ignore'):
        q = float(np.quantile(a, .95))
    if not np.isfinite(q):
        return dict(value=None, status='INFINITE_DUE_TO_MISSES')
    return dict(value=q, status='FINITE')


def raw_sdf(model, world):
    g = protocol()['geometry']
    x = (np.asarray(world)-np.array(g['C_mm']))/g['mm_per_model_unit']
    values = []
    with torch.no_grad():
        for chunk in np.array_split(x, max(1, int(np.ceil(len(x)/8192)))):
            t = torch.as_tensor(chunk, dtype=torch.float32, device='cuda')
            values.append(model.implicit_network(t)[:, 0].cpu().numpy()*g['mm_per_model_unit'])
    return np.concatenate(values)


def geometry_checkpoint(model, arm, step, final=False):
    tag = f'single_{arm}_step{step:06d}'
    folder = R/'local_results'/tag
    folder.mkdir(exist_ok=True)
    g = protocol()['geometry']; scale = g['mm_per_model_unit']; center = np.array(g['C_mm'])
    resolution = 512 if final else 128
    was_training = model.training
    model.eval()
    torch.cuda.empty_cache()
    get_surface = extraction_functions()
    with torch.no_grad():
        mesh = get_surface(str(folder), step, lambda x:model.implicit_network(x)[:, 0],
                           resolution=resolution, grid_boundary=[-1., 1.], return_mesh=True, level=0)
    field = np.load(folder/f'sdf_{step}_model.npy', mmap_mode='r')
    negative_volume = float((field < 0).sum()*(2*scale/resolution)**3)
    result = dict(tag=tag, stage='single', arm=arm, step=step, resolution=resolution,
                  extraction='official get_surface_trace; save-field/no-processing IO ports',
                  geometry_modified=False, all_components_preserved=True, GT='NOT_EVALUABLE',
                  negative_grid_volume_mm3=negative_volume,
                  negative_volume_is_model_proxy_not_physical_volume=True)
    arrays = {}
    if mesh is None:
        P = np.empty((0, 3)); F = np.empty((0, 3), int)
    else:
        P = np.asarray(mesh.vertices)*scale+center; F = np.asarray(mesh.faces)
        mesh = trimesh.Trimesh(P, F, process=False)
        mesh.export(folder/'raw_mm.ply')
    scene = mesh_scene(P, F)
    rays = []; raw_faces = []
    for cid in SOURCES:
        n = observed(cid)
        hit, _ = cast(scene, n['native_uv'], n['Kn'], n['T'])
        visible = n['visible']; finite = np.isfinite(hit); den = int(visible.sum())
        error = hit-n['z']; agree = visible & finite & (abs(error) <= .25)
        df = raw_sdf(model, n['X'])
        # Actual source ray intersections; deduplicate shared-edge intersections.
        intersections = scene.list_intersections(o3d.core.Tensor(
            vis.camera_rays(n['native_uv'], n['Kn'], n['T']).astype(np.float32)))
        rid = intersections['ray_ids'].numpy().astype(int)
        tt = intersections['t_hit'].numpy().astype(float)
        ok = (tt > 0) & (tt <= n['CAD'][rid]+.002)
        order = np.lexsort((tt[ok], rid[ok])); r0 = rid[ok][order]; t0 = tt[ok][order]
        unique = np.r_[True, (np.diff(r0) != 0) | (np.abs(np.diff(t0)) > 1e-4)] if len(r0) else np.empty(0, bool)
        counts = np.bincount(r0[unique], minlength=len(hit))
        retained_visible = visible & n['available']
        keep_distance = distance(scene, n['X']) if len(F) else np.full(len(hit), np.inf)
        full95 = full_error(error[visible])
        row = dict(tag=tag, arm=arm, step=step, source=cid, in_training=cid==SOURCES[0],
            fixed_original_N=len(hit), fixed_visible_N=den, CAD_occluded_N=int((~visible).sum()),
            available_input_N=int(n['available'].sum()),
            hit_N=int((visible & finite).sum()), miss_N=int((visible & ~finite).sum()),
            hit_fraction=float((visible & finite).sum()/den), agreement_N=int(agree.sum()),
            agreement_fraction=float(agree.sum()/den), hit_only_error_mm=stats(error[visible & finite]),
            p95_including_misses_mm=full95['value'], p95_including_misses_status=full95['status'],
            cleaned_visible_N=int(retained_visible.sum()),
            cleaned_HERO_retained_0p25_N=int((retained_visible & (keep_distance<=.25)).sum()),
            cleaned_HERO_first_agree_N=int((retained_visible & agree).sum()),
            raw_HERO_SDF_mm=stats(df[visible]),
            absolute_HERO_SDF_mm=stats(abs(df[visible])),
            multi_4plus_N=int((visible & (counts>=4)).sum()),
            multi_4plus_fraction=float((visible & (counts>=4)).sum()/den),
            camera_qualification='INSUFFICIENT_EVIDENCE', physical_GT='NOT_EVALUABLE')
        # Full original Mask, not only successful/HERO pixels, checks leakage.
        yy, xx = np.mgrid[:n['depth'].shape[0], :n['depth'].shape[1]]
        uv = np.c_[xx.ravel(), yy.ravel()]
        all_hit, _ = cast(scene, uv, n['Kn'], n['T'])
        all_cad, _ = cast(ringscene(SCENE), uv, n['Kn'], n['T'])
        lab = n['native_labels'].ravel()
        pred = np.isfinite(all_hit) & ((~np.isfinite(all_cad)) | (all_hit < all_cad-.002))
        mask_scope = lab != 2
        union = mask_scope & (pred | (lab==1))
        row.update(mask_IoU_visible_proxy=float((mask_scope & pred & (lab==1)).sum()/max(1,union.sum())),
                   mask_outside_N=int((mask_scope & pred & (lab!=1)).sum()),
                   CAD_mask_pixels_excluded_N=int((lab==2).sum()))
        rays.append(row)
        for key, value in dict(native_id=n['native_id'], hit_mm=hit, depth_mm=n['z'],
                CAD_mm=n['CAD'], visible=visible, available=n['available'],
                raw_SDF_mm=df, intersections_N=counts,
                full_image_visible_hit=pred.reshape(n['depth'].shape)).items():
            arrays[cid+'_'+key] = value
        raw = original(cid); centers = raw['P'][raw['F']].mean(1)
        dr = distance(scene, centers) if len(F) else np.full(len(centers), np.inf)
        area = raw['area']
        raw_faces.append(dict(source=cid, original_face_N=len(centers), original_area_mm2=float(area.sum()),
            retained_face_N=int((dr<=.25).sum()),
            area_retention_0p25=float(area[dr<=.25].sum()/area.sum()), distance_mm=stats(dr)))
        arrays[cid+'_original_face_id'] = np.arange(len(centers))
        arrays[cid+'_original_face_distance_mm'] = dr
    result.update(rays=rays, raw_faces=raw_faces, vertices_N=len(P), faces_N=len(F),
                  empty_zero_surface=not len(F))
    if len(F):
        edges = mesh.edges_unique
        graph = coo_matrix((np.ones(2*len(edges)), (np.r_[edges[:,0],edges[:,1]],
                           np.r_[edges[:,1],edges[:,0]])), shape=(len(P),len(P)))
        nc, labels = connected_components(graph, directed=False)
        areas = np.bincount(labels[F[:,0]], weights=mesh.area_faces, minlength=nc)
        result.update(area_mm2=float(mesh.area), components_N=int(nc), bounds_mm=mesh.bounds,
                      largest_component_area_fraction=float(areas.max()/areas.sum()),
                      watertight=bool(mesh.is_watertight), normal_angle_deg=stats(np.degrees(mesh.face_adjacency_angles)))
        centers = P[F].mean(1)
        supported = np.zeros(len(F), bool); visible_any = supported.copy(); conflict = supported.copy()
        for cid in SOURCES:
            n = observed(cid)
            uv, z = vis.project_camera(centers, n['Kn'], n['T'])
            h,w = n['depth'].shape
            ok = np.isfinite(uv).all(1)&(z>0)&(uv[:,0]>=-.5)&(uv[:,0]<w-.5)&(uv[:,1]>=-.5)&(uv[:,1]<h-.5)
            j = np.flatnonzero(ok); ij = np.floor(uv[j]+.5).astype(int)
            cad,_ = cast(ringscene(SCENE), uv[j], n['Kn'], n['T'])
            unblocked = (~np.isfinite(cad)) | (z[j] < cad-.002)
            j=j[unblocked]; ij=ij[unblocked]
            labels2 = n['native_labels'][ij[:,1],ij[:,0]]
            clean = np.load(N0/'frozen_inputs/native'/(cid+'.npz'))['valid'][ij[:,1],ij[:,0]]
            dz = n['depth'][ij[:,1],ij[:,0]]
            visible_any[j] |= labels2!=2
            supported[j] |= clean & (labels2==1) & (abs(z[j]-dz)<=.25)
            conflict[j] |= clean & (labels2==1) & (z[j]<dz-.25)
        categories=np.where(supported,'OBSERVED_NEAR_PROXY',np.where(visible_any,'INFERRED_UNSUPPORTED_PROXY','UNKNOWN_OCCLUDED_OR_UNSEEN'))
        arrays.update(mesh_face_id=np.arange(len(F)), mesh_face_category=categories,
                      mesh_face_free_space_conflict_proxy=conflict)
        result['surface_categories']={c:dict(N=int((categories==c).sum()),area_mm2=float(mesh.area_faces[categories==c].sum()))for c in np.unique(categories)}
        result['support_scope']='three existing CORE observations; also includes non-training sources for single-view diagnostic'
    np.savez_compressed(folder/'evaluation.npz', **arrays)
    table(f'metrics/{tag}_RAYS.csv', rays)
    table(f'metrics/{tag}_RAW_FACES.csv', raw_faces)
    save(f'metrics/{tag}_GEOMETRY.json', result)
    save(f'local_results/{tag}/INDEX.json', dict(tag=tag, files=[asset(x) for x in folder.iterdir() if x.is_file()], geometry=result))
    model.train(was_training)
    torch.cuda.empty_cache()
    return result
