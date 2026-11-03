def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def clean(v):
    if isinstance(v, dict):
        return {str(k): clean(a) for k, a in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(a) for a in v]
    if hasattr(v, 'tolist'):
        return clean(v.tolist())
    if isinstance(v, Path):
        return str(v)
    if isinstance(v, float) and (not __import__('math').isfinite(v)):
        return None
    return v

def save(p, v):
    p = R / p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(clean(v), ensure_ascii=False, indent=2) + '\n')

def table(p, rows):
    p = R / p
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text('')
        return
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(clean(v), ensure_ascii=False) if isinstance(v, (dict, list, tuple)) else v for k, v in r.items()})

def rows(p):
    return list(csv.DictReader(Path(p).open()))

def asset(p):
    return dict(path=str(p), bytes=Path(p).stat().st_size, sha256=sha(p))

def stats(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return dict(N=len(a), median=float(np.median(a)) if len(a) else None, MAE=float(np.abs(a).mean()) if len(a) else None, p95=float(np.quantile(np.abs(a), 0.95)) if len(a) else None, maximum=float(np.abs(a).max()) if len(a) else None)

@lru_cache(None)
def source(cid):
    c = CC[cid]
    p = np.load(c['pack'])
    K = np.asarray(p['K'])
    T = np.asarray(p['pose'])
    labels = np.asarray(Image.open(c['Mask']))
    rgb = np.asarray(Image.open(c['RGB']).convert('RGB'))
    assert labels.shape == (360, 640) and rgb.shape == (360, 640, 3)
    assert np.allclose(T, c['c2w_mm'], rtol=0, atol=1e-10) and np.allclose(K, c['K_after_resize'], rtol=0, atol=1e-10)
    assert np.array_equal(labels, p['labels'])
    assert np.allclose(np.load(c['camera_file'])['c2w'][c['reference_index']], T, rtol=0, atol=1e-10)
    assert np.allclose(T[:3, :3].T @ T[:3, :3], np.eye(3), atol=1e-10) and np.linalg.det(T[:3, :3]) > 0
    return dict(id=cid, c=c, K=K, T=T, labels=labels, RGB=rgb)

@lru_cache(None)
def native(cid):
    s = source(cid)
    c = s['c']
    p = np.load(c['E1_actual_native']['path'])
    depth = p['depth_mm']
    h, w = depth.shape
    Kn = vis.scaled_intrinsics(s['K'], (640, 360), (w, h))
    stored = next((p[k] for k in ['K_index_native', 'K_index'] if k in p), None)
    assert stored is None or np.allclose(Kn, stored, rtol=0, atol=1e-10)
    nt = next((p[k] for k in ['reference_pose_mm', 'pose'] if k in p), None)
    assert nt is None or np.allclose(nt, s['T'], rtol=0, atol=1e-10)
    labels = cv2.resize(s['labels'], (w, h), interpolation=cv2.INTER_NEAREST)
    rgb = cv2.resize(s['RGB'], (w, h), interpolation=cv2.INTER_AREA)
    valid = (labels == 1) & np.isfinite(depth) & (depth > 0)
    v, u = np.nonzero(valid)
    uv = np.c_[u, v]
    X = unproject(depth[v, u].astype(float), s['T'], uv, Kn)
    return dict(s, depth=depth, Kn=Kn, native_labels=labels, native_RGB=rgb, valid=valid, native_uv=uv, native_id=v * w + u, X=X)

@lru_cache(None)
def original(cid):
    c = CC[cid]
    q = np.load(c['source_points'])
    P = q['points_mm'] if 'points_mm' in q else q['XYZ_mm']
    mesh = trimesh.load(c['mesh'], process=False)
    F = q['original_faces'] if 'original_faces' in q else np.asarray(mesh.faces)
    uv = q['uv'] if 'uv' in q else q['source_uv'] if 'source_uv' in q else q['pixel_uv']
    uv = np.asarray(uv, int)
    s = source(cid)
    z = np.load(c['pack'])['depth_mm']
    assert np.max(abs(unproject(z[uv[:, 1], uv[:, 0]], s['T'], uv, s['K']) - P)) < 1e-06
    assert np.array_equal(F, mesh.faces) and np.max(abs(P - mesh.vertices)) < 1e-05
    return dict(P=P, F=F, uv=uv, area=trimesh.triangles.area(P[F]))

@lru_cache(None)
def ringmesh(scene):
    return trimesh.load(next((c['Ring_CAD']['path'] for c in CC.values() if c['scene_id'] == scene)), process=False)

def mesh_scene(P, F):
    s = o3d.t.geometry.RaycastingScene(nthreads=2)
    if len(F):
        s.add_triangles(o3d.core.Tensor(np.asarray(P, np.float32)), o3d.core.Tensor(np.asarray(F, np.uint32)))
    return s

@lru_cache(None)
def ringscene(scene):
    m = ringmesh(scene)
    return mesh_scene(m.vertices, m.faces)

def cast(scene, uv, K, T):
    result = scene.cast_rays(o3d.core.Tensor(vis.camera_rays(np.asarray(uv), K, T).astype(np.float32)))
    return (result['t_hit'].numpy().astype(float), result['primitive_ids'].numpy().astype(np.int64))

def distance(scene, X):
    return scene.compute_distance(o3d.core.Tensor(np.asarray(X, np.float32))).numpy().astype(float)

def affine_uv(uv, A):
    return np.c_[uv, np.ones(len(uv))] @ np.asarray(A)[:2].T
def scaled_intrinsics(K, source_size, target_size):
    """Pixel-center-preserving scale; neither extrinsic nor focal fit changes."""
    sx, sy = np.asarray(target_size, float) / np.asarray(source_size, float)
    out = np.asarray(K, float).copy()
    out[0, :] *= sx
    out[1, :] *= sy
    out[0, 2] += (sx - 1.0) / 2.0
    out[1, 2] += (sy - 1.0) / 2.0
    return out

def project_camera(points_mm, K, c2w):
    """Frozen pinhole camera, full rotation including roll; camera axial Z mm."""
    camera = (np.asarray(points_mm) - c2w[:3, 3]) @ c2w[:3, :3]
    homogeneous = camera @ K.T
    with np.errstate(divide='ignore', invalid='ignore'):
        uv = homogeneous[:, :2] / homogeneous[:, 2, None]
    return (uv, camera[:, 2])

def camera_rays(uv, K, c2w):
    """Unnormalized world rays: ray parameter equals camera axial Z in mm."""
    camera = np.c_[uv, np.ones(len(uv))] @ np.linalg.inv(K).T
    direction = camera @ c2w[:3, :3].T
    return np.c_[np.broadcast_to(c2w[:3, 3], direction.shape), direction]
def unproject(z, pose, uv, K):
    return np.c_[uv, np.ones(len(uv))] @ np.linalg.inv(K).T * z[:, None] @ pose[:3, :3].T + pose[:3, 3]
