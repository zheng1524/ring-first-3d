"""A fixed source-camera scene. No independent view/azimuth/pose parameters."""
from pathlib import Path
import sys
import numpy as np
from . import real_p0_renderer as base


class SameCameraScene:
    def __init__(self, mesh, K, c2w, image_size, vendor=None):
        try:
            import open3d as o3d
        except ImportError:
            if vendor is None:
                raise
            sys.path.insert(0, str(Path(vendor)))
            import open3d as o3d
        self.o3d = o3d
        self.mesh = mesh
        self.K = np.asarray(K, float).copy()
        self.c2w = np.asarray(c2w, float).copy()
        self.image_size = tuple(image_size)
        self.scene = o3d.t.geometry.RaycastingScene(nthreads=2)
        self.scene.add_triangles(o3d.core.Tensor(np.asarray(mesh.vertices, np.float32)),
                                 o3d.core.Tensor(np.asarray(mesh.faces, np.uint32)))

    def cast(self, uv):
        rays = base.camera_rays(uv, self.K, self.c2w).astype(np.float32)
        return self.scene.cast_rays(self.o3d.core.Tensor(rays))

    def ring_image(self):
        w, h = self.image_size
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        result = self.cast(np.c_[u.ravel(), v.ravel()])
        hit = np.isfinite(result['t_hit'].numpy())
        n = result['primitive_normals'].numpy()
        light = self.c2w[:3, 3] - self.mesh.centroid
        light /= np.linalg.norm(light)
        illumination = np.maximum(n@light, 0)
        shade = .012 + .035*illumination + .035*illumination**18
        image = np.zeros((w*h, 4), np.float32)
        image[hit, :3] = shade[hit, None]
        image[hit, 3] = 1.
        return image.reshape(h, w, 4)

    def draw(self, ax, polyp, polyp_rgb, background, background_rgb, point_size=.8):
        # One combined point call: exactly the same projection, ordering, RGB,
        # size, opacity and scatter method for Polyp and Background.
        points = np.r_[polyp, background]
        colors = np.r_[polyp_rgb, background_rgb]
        uv, z = base.project_camera(points, self.K, self.c2w)
        first_hit = self.cast(uv)['t_hit'].numpy()
        visible = ~np.isfinite(first_hit) | (z <= first_hit+.002)
        image = self.ring_image()
        w, h = self.image_size
        ax.imshow(image, extent=(-.5, w-.5, h-.5, -.5), interpolation='nearest', zorder=2)
        artist, drawn = base.view_camera_rgb(ax, points, colors, self.K, self.c2w,
                                             self.image_size, size=point_size,
                                             visibility=visible)
        artist.set_zorder(3)
        ax.axis('off')
        n = len(polyp)
        return image, drawn, dict(Polyp_points=len(polyp), Background_points=len(background),
                                  Polyp_drawn=int(drawn[:n].sum()), Background_drawn=int(drawn[n:].sum()),
                                  shared_point_artist=True, shared_point_size=point_size,
                                  shared_point_alpha=1., shared_projector='frozen K/c2w pinhole',
                                  independent_observation_rotation=False,
                                  CAD_mesh_vertices=len(self.mesh.vertices), CAD_mesh_faces=len(self.mesh.faces),
                                  CAD_world_bounds_mm=self.mesh.bounds.tolist(),
                                  CAD_opaque_pixels=int((image[:, :, 3]==1).sum()),
                                  CAD_alpha_values=np.unique(image[:, :, 3]).tolist(),
                                  CAD_max_display_RGB=float(image[:, :, :3].max()))

    def scale_bar(self, ax, length_mm=2.5):
        """Perspective scale annotation at Z=0 Ring plane, not a global scale."""
        w, h = self.image_size
        ray = base.camera_rays(np.array([[.08*w, .91*h]]), self.K, self.c2w)[0]
        t = -ray[2]/ray[5]
        if not np.isfinite(t) or t <= 0:
            return None
        start = ray[:3]+t*ray[3:]
        direction = self.c2w[:3, 0].copy()
        direction[2] = 0
        direction /= np.linalg.norm(direction)
        ends = np.array([start, start+length_mm*direction])
        uv, _z = base.project_camera(ends, self.K, self.c2w)
        ax.plot(uv[:, 0], uv[:, 1], color='black', linewidth=2, zorder=5)
        ax.text(uv[0, 0], uv[0, 1]-12, f'{length_mm:g} mm（Ring平面）', fontsize=8,
                bbox=dict(facecolor='white', edgecolor='none', alpha=.8), zorder=5)
        return dict(world_endpoints_mm=ends.tolist(), pixel_endpoints=uv.tolist(),
                    length_mm=length_mm, plane='Ring Z=0 only')
