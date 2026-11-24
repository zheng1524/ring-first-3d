"""Single authoritative Ring CAD parameter contract.

ring_mm is the *inner* ring diameter. The torus centerline radius is
ring_mm/2 + wire_radius; wire_radius is the tube radius.
"""
from __future__ import annotations
import math
WIRE_RADIUS_MM = 0.6

def params(ring_mm):
    inner = float(ring_mm)
    if not math.isfinite(inner) or inner <= 0:
        raise ValueError(f'INVALID_RING_INNER_DIAMETER {ring_mm!r}')
    return dict(inner_diameter_mm=inner, centerline_radius_mm=inner/2.0 + WIRE_RADIUS_MM,
                wire_radius_mm=WIRE_RADIUS_MM)

def project_contours(c2w, K, ring_mm, n=256, wire_radius=WIRE_RADIUS_MM):
    """Explicit-keyword CAD projection; never binds an argument positionally."""
    from .camera import torus_contours
    p = params(ring_mm)
    return torus_contours(c2w, K, n=n, ring_radius=p['centerline_radius_mm'],
                          ring_wire=float(wire_radius))
