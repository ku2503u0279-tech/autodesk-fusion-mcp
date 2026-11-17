"""A small software renderer for studio product shots.

No GPU and no external 3D package: a numpy z-buffer rasteriser with smooth
vertex normals, three-point studio lighting, a seamless backdrop floor with a
soft contact shadow, and 2x supersampling. The aim is renders that read like
photographs of a real object: clean gradients, soft shadows, no visible facets.
"""
import math

import numpy as np

from PIL import Image


# ------------------------------------------------------------------ meshes
class Mesh(object):
    """Triangle soup with a material name."""

    def __init__(self, mat="walnut"):
        self.mat = mat
        self.v = []
        self.f = []

    def add(self, verts, faces):
        o = len(self.v)
        self.v.extend([tuple(float(c) for c in p) for p in verts])
        self.f.extend([tuple(int(i) + o for i in fa) for fa in faces])
        return self

    def arrays(self):
        return (np.asarray(self.v, dtype=np.float64).reshape(-1, 3),
                np.asarray(self.f, dtype=np.int64).reshape(-1, 3))

    def moved(self, dx=0.0, dy=0.0, dz=0.0):
        self.v = [(x + dx, y + dy, z + dz) for (x, y, z) in self.v]
        return self


def _signed_area(p):
    s = 0.0
    for i in range(len(p)):
        z0, y0 = p[i]
        z1, y1 = p[(i + 1) % len(p)]
        s += z0 * y1 - z1 * y0
    return s * 0.5


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _inside(p, a, b, c):
    return (_cross(a, b, p) >= -1e-9 and _cross(b, c, p) >= -1e-9
            and _cross(c, a, p) >= -1e-9)


def triangulate(poly):
    """Ear clipping for a simple polygon, returns index triples."""
    idx = list(range(len(poly)))
    if _signed_area(poly) < 0:
        idx.reverse()
    out = []
    guard = 0
    while len(idx) > 3 and guard < 20000:
        guard += 1
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if _cross(a, b, c) <= 1e-9:
                continue
            if any(_inside(poly[o], a, b, c)
                   for o in idx if o not in (i0, i1, i2)):
                continue
            out.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def prism(profile, x0, x1, mat="walnut"):
    """Extrude a closed (z, y) profile along X. No holes."""
    pts = list(profile)
    n = len(pts)
    verts = [(x0, y, z) for (z, y) in pts] + [(x1, y, z) for (z, y) in pts]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j))
        faces.append((i, n + j, n + i))
    for a, b, c in triangulate(pts):
        faces.append((c, b, a))
        faces.append((n + a, n + b, n + c))
    return Mesh(mat).add(verts, faces)


def band(outer, inner, x0, x1, mat="walnut"):
    """Extrude a closed profile that has a closed hole in it.

    `outer` and `inner` must be matched point-for-point, both wound the same
    way, so the extruded wall is a clean ribbon of constant width.
    """
    n = len(outer)
    verts = []
    for x in (x0, x1):
        verts += [(x, y, z) for (z, y) in outer]
        verts += [(x, y, z) for (z, y) in inner]
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        faces += [(o0 + k, o0 + k2, o1 + k2), (o0 + k, o1 + k2, o1 + k)]
        faces += [(i0 + k2, i0 + k, i1 + k), (i0 + k2, i1 + k, i1 + k2)]
        faces += [(o0 + k, i0 + k, i0 + k2), (o0 + k, i0 + k2, o0 + k2)]
        faces += [(o1 + k2, i1 + k2, i1 + k), (o1 + k2, i1 + k, o1 + k)]
    return Mesh(mat).add(verts, faces)


def horseshoe(outer, inner, x0, x1, mat="walnut"):
    """Extrude a C-shaped band: an outer contour and a matching inner one.

    `outer` and `inner` are open polylines over the same parameter, both
    starting at the back foot on the floor and ending at the front foot, so the
    band between them is the whole blade and the two feet close themselves.
    """
    n = len(outer)
    if len(inner) != n:
        raise ValueError("outer/inner must have equal point counts")
    verts = []
    for x in (x0, x1):
        verts += [(x, y, z) for (z, y) in outer]
        verts += [(x, y, z) for (z, y) in inner]
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    faces = []
    for k in range(n - 1):
        k2 = k + 1
        faces += [(o0 + k, o0 + k2, o1 + k2), (o0 + k, o1 + k2, o1 + k)]     # outer wall
        faces += [(i0 + k2, i0 + k, i1 + k), (i0 + k2, i1 + k, i1 + k2)]     # inner wall
        faces += [(o0 + k2, i0 + k2, i0 + k), (o0 + k2, i0 + k, o0 + k)]     # back cap
        faces += [(i1 + k2, o1 + k2, o1 + k), (i1 + k2, o1 + k, i1 + k)]     # front cap
    return Mesh(mat).add(verts, faces)


def slab(x0, x1, z0, z1, y_back, y_front, t, mat="walnut"):
    """A board whose top face tilts from y_back at z0 to y_front at z1."""
    vb = [[x0, y_back, z0], [x1, y_back, z0], [x1, y_front, z1], [x0, y_front, z1]]
    vt = [[x0, y_back - t, z0], [x1, y_back - t, z0],
          [x1, y_front - t, z1], [x0, y_front - t, z1]]
    verts = vb + vt
    faces = [(0, 2, 1), (0, 3, 2),
             (4, 5, 6), (4, 6, 7),
             (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5),
             (2, 3, 7), (2, 7, 6),
             (3, 0, 4), (3, 4, 7)]
    return Mesh(mat).add(verts, faces)


def box(x0, x1, y0, y1, z0, z1, mat="walnut"):
    return slab(x0, x1, z0, z1, y1, y1, y1 - y0, mat=mat)


def tube(x0, x1, y, z, r, mat="metal", seg=48):
    verts = []
    for x in (x0, x1):
        for i in range(seg):
            a = 2 * np.pi * i / seg
            verts.append((x, y + r * np.cos(a), z + r * np.sin(a)))
    faces = []
    for i in range(seg):
        j = (i + 1) % seg
        faces += [(i, j, seg + j), (i, seg + j, seg + i)]
    for i in range(1, seg - 1):
        faces += [(0, i + 1, i), (seg, seg + i, seg + i + 1)]
    return Mesh(mat).add(verts, faces)



# ------------------------------------------------------- chamfer / lofting
def signed_area(loop):
    a = 0.0
    n = len(loop)
    for i in range(n):
        u, v = loop[i]
        w, v2 = loop[(i + 1) % n]
        a += u * v2 - w * v
    return a * 0.5


def inset_loop(loop, c, clamp=3.0):
    """Move every point of a closed loop inward by c, mitred at the corners.

    A chamfer needs the profile held a few millimetres inside the real edge.
    The mitre formula is exact for any corner angle; it is only clamped when a
    corner is so sharp that the offset would fly off to infinity, which can
    happen at the points of a lens-shaped window.
    """
    n = len(loop)
    cw = signed_area(loop) < 0
    out = []
    for i in range(n):
        a, b, d = loop[(i - 1) % n], loop[i], loop[(i + 1) % n]
        n1 = _inward(b, a, cw)
        n2 = _inward(d, b, cw)
        dot = max(-1.0, min(1.0, n1[0] * n2[0] + n1[1] * n2[1]))
        denom = 1.0 + dot
        if denom < 0.22:
            mx, my, ln = n1[0], n1[1], c
        else:
            mx = (n1[0] + n2[0]) / denom
            my = (n1[1] + n2[1]) / denom
            ln = c
            m = (mx * mx + my * my) ** 0.5 or 1.0
            if m * ln > clamp * c:
                mx, my = mx / m, my / m
                ln = clamp * c
            else:
                mx, my, ln = mx * ln, my * ln, 1.0
        out.append((b[0] + mx * ln, b[1] + my * ln))
    return out


def _inward(p, q, cw):
    """Unit normal of edge p->q pointing into the shape."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    ln = (dx * dx + dy * dy) ** 0.5 or 1.0
    dx, dy = dx / ln, dy / ln
    return (dy, -dx) if cw else (-dy, dx)


def _place(plane, a, u, v):
    if plane == "x":          # profile in (z, y), swept along X
        return (a, v, u)
    if plane == "y":          # profile in (x, z), swept along Y
        return (u, a, v)
    return (u, v, a)          # profile in (x, y), swept along Z


def loft(rings, mat="walnut", cap_start=True, cap_end=True):
    """Skin a series of rings, each ring a list of the same number of points.

    This is how every solid here is built: one function, so a chamfer is just
    an extra pair of rings rather than a special case.
    """
    n = len(rings[0])
    m = Mesh(mat)
    verts = []
    for ring in rings:
        if len(ring) != n:
            raise ValueError("all rings must have the same point count")
        verts.extend(ring)
    faces = []
    for r in range(len(rings) - 1):
        o0, o1 = r * n, (r + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((o0 + k, o0 + k2, o1 + k2))
            faces.append((o0 + k, o1 + k2, o1 + k))
    # The caps are triangulated in the plane the rings actually lie in. Using
    # (x, y) for everything silently produced EMPTY caps for a ring swept along
    # X — every point has the same x, so the projection collapsed and the
    # triangulator returned nothing. The result was an open shell with a
    # see-through end, which is what put the black sawtooth along the top of the
    # stacked laminations.
    flat = _flatten(rings[0])
    tris = triangulate(flat)
    if cap_start:
        for a, b, c in tris:
            faces.append((c, b, a))
    if cap_end:
        base = (len(rings) - 1) * n
        for a, b, c in tris:
            faces.append((base + a, base + b, base + c))
    return m.add(verts, faces)


def _flatten(ring):
    """Drop the axis a ring is constant along, keeping the other two in order."""
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    zs = [p[2] for p in ring]
    def span(a):
        return max(a) - min(a)
    if span(xs) <= span(ys) and span(xs) <= span(zs):
        return [(p[2], p[1]) for p in ring]      # swept along X
    if span(zs) <= span(xs) and span(zs) <= span(ys):
        return [(p[0], p[1]) for p in ring]      # swept along Z
    return [(p[0], p[2]) for p in ring]          # swept along Y


def prism_axis(profile, a0, a1, plane="x", mat="walnut", chamfer=0.0):
    """Sweep a closed profile along one axis, optionally chamfering the rims.

    With a chamfer the solid gets four rings: the true profile at each end, and
    an inset copy just inside it. The sloped band between them is the chamfer,
    which is what catches the light along every edge.
    """
    prof = [(float(u), float(v)) for (u, v) in profile]
    if chamfer > 1e-6:
        inner = inset_loop(prof, chamfer)
        stops = ((a0, prof), (a0 + chamfer, inner),
                 (a1 - chamfer, inner), (a1, prof))
    else:
        stops = ((a0, prof), (a1, prof))
    rings = [[_place(plane, a, u, v) for (u, v) in ring] for (a, ring) in stops]
    # keep the winding pointing out of the solid
    if signed_area(prof) > 0 and plane in ("x", "y"):
        rings = [r[::-1] for r in rings]
    return loft(rings, mat=mat)


def deck_outline(x0, x1, z0, z1, r=30.0, steps=8):
    """Plan outline of a deck board: square at the back, drawn round at the front.

    Lives in the geometry module so the renderer and the exporter cannot drift
    apart: a deck that is pictured with round front corners must be cut with
    round front corners.
    """
    r = max(0.0, min(r, (x1 - x0) * 0.5 - 1.0, (z1 - z0) * 0.5 - 1.0))
    pts = [(x0, z0), (x1, z0)]                     # back edge
    for k in range(steps + 1):                     # front-right corner
        a = (math.pi / 2.0) * k / steps
        pts.append((x1 - r + r * math.cos(a), z1 - r + r * math.sin(a)))
    for k in range(1, steps + 1):                  # front edge
        pts.append((x1 - r - (x1 - x0 - 2 * r) * k / steps, z1))
    for k in range(steps + 1):                     # front-left corner
        a = (math.pi / 2.0) * (steps - k) / steps
        pts.append((x0 + r - r * math.cos(a), z1 - r + r * math.sin(a)))
    # the corner arcs start and end on the tangent points, which are also
    # emitted by the edge runs; drop the repeats so the loop has no zero-length
    # segments (those weld into loose edges in an STL)
    out = []
    for q in pts:
        if not out or abs(q[0] - out[-1][0]) > 1e-9 or abs(q[1] - out[-1][1]) > 1e-9:
            out.append(q)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9:
        out.pop()
    return out


def board(outline, y_of_uv, t, mat="ash", chamfer=2.0):
    """A flat-ish board whose top surface is a function of its plan position.

    Used for the deck: the outline is the plan shape, and each point's height
    comes from the tilt, so the board is genuinely level with the blades rather
    than a box rotated to look right.
    """
    o = [(float(u), float(v)) for (u, v) in outline]
    inner = inset_loop(o, chamfer) if chamfer > 1e-6 else o
    rings = []
    for ring, dy in ((o, 0.0), (inner, -chamfer), (inner, -t + chamfer), (o, -t)):
        rings.append([(u, y_of_uv(u, v) + dy, v) for (u, v) in ring])
    if signed_area(o) < 0:
        rings = [r[::-1] for r in rings]
    return loft(rings, mat=mat)



def channel(outer, inner, depth, a0, a1, plane="x", mat="walnut"):
    """Cut a shallow rebate into a face: two walls and a floor.

    Used for the gutter between the deck and the blade's top edge. `outer` and
    `inner` are closed loops in the face's own plane, and the pocket is sunk
    `depth` into the solid from the a1 end.
    """
    n = len(outer)
    if len(inner) != n:
        raise ValueError("outer/inner must match")
    verts = []
    for a in (a1, a1 - depth):
        verts += [_place(plane, a, u, v) for (u, v) in outer]
        verts += [_place(plane, a, u, v) for (u, v) in inner]
    # winding: outer and inner are opposite so the band reads as a surface
    rev = signed_area([(u, v) for (u, v) in outer]) < 0
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        # the floor of the pocket
        faces.append((o1 + k, o1 + k2, i1 + k2))
        faces.append((o1 + k, i1 + k2, i1 + k))
        # the two side walls
        faces.append((o0 + k2, o0 + k, o1 + k))
        faces.append((o0 + k2, o1 + k, o1 + k2))
        faces.append((i0 + k, i0 + k2, i1 + k2))
        faces.append((i0 + k, i1 + k2, i1 + k))
    if rev:
        faces = [tuple(reversed(f)) for f in faces]
    return Mesh(mat).add(verts, faces)



def _resample_loop(loop, n):
    """Redistribute a closed loop to n points, evenly by arc length."""
    m = len(loop)
    seg = [math.hypot(loop[(i + 1) % m][0] - loop[i][0],
                      loop[(i + 1) % m][1] - loop[i][1]) for i in range(m)]
    total = sum(seg) or 1.0
    step = total / float(n)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        target = k * step
        while acc + seg[i] < target and i < m - 1:
            acc += seg[i]
            i += 1
        f = 0.0 if seg[i] < 1e-9 else (target - acc) / seg[i]
        a, b = loop[i], loop[(i + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def loop_pair(outer, inner, a0, a1, plane="x", mat="walnut"):
    """Extrude a ring between two closed loops, leaving the middle open.

    This is how a hole is made: the wall runs round the outside, another wall
    runs round the hole facing inward, and a flat ring joins them at each end.
    It is the same idea as a picture frame, and it is exactly what a routed
    window in a board is.
    """
    inner = _resample_loop(inner, len(outer))
    n = len(outer)
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    verts = []
    for a in (a0, a1):
        verts += [_place(plane, a, u, v) for (u, v) in outer]
        verts += [_place(plane, a, u, v) for (u, v) in inner]
    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        faces += [(o0 + k, o0 + k2, o1 + k2), (o0 + k, o1 + k2, o1 + k)]   # outer wall
        faces += [(i0 + k2, i0 + k, i1 + k), (i0 + k2, i1 + k, i1 + k2)]   # hole wall
        faces += [(o0 + k, i0 + k, i0 + k2), (o0 + k, i0 + k2, o0 + k2)]   # end ring
        faces += [(o1 + k2, i1 + k2, i1 + k), (o1 + k2, i1 + k, o1 + k)]   # far ring
    if signed_area([(u, v) for (u, v) in outer]) > 0:
        faces = [tuple(reversed(f)) for f in faces]
    return Mesh(mat).add(verts, faces)



def _bridge_seam(outer, hole):
    """The closest pair of indices between an outer loop and a hole."""
    best = None
    for i in range(len(outer)):
        for j in range(len(hole)):
            d = ((outer[i][0] - hole[j][0]) ** 2
                 + (outer[i][1] - hole[j][1]) ** 2)
            if best is None or d < best[0]:
                best = (d, i, j)
    return best[1], best[2]


def _bridge_loops(outer, hole):
    """Splice a hole into its outer loop with a single bridge edge.

    The result is one simple polygon, so ordinary ear clipping can triangulate
    an end cap that genuinely has a hole in it. Joining the two loops by index
    instead (the obvious thing) produces a fan of quads that crisscrosses the
    part and seals the opening, which is exactly what was wrong before.
    """
    n, m = len(outer), len(hole)
    best = None
    for i in range(n):
        for j in range(m):
            d = (outer[i][0] - hole[j][0]) ** 2 + (outer[i][1] - hole[j][1]) ** 2
            if best is None or d < best[0]:
                best = (d, i, j)
    _, i, j = best
    return (list(outer[:i + 1]) + list(hole[j:]) + list(hole[:j])
            + list(outer[i + 1:]))


def _earclip(poly):
    """Triangulate a simple polygon by ear clipping. Returns index triples."""
    n = len(poly)
    idx = list(range(n))
    if signed_area(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        made = False
        for k in range(len(idx)):
            a = idx[k - 1]
            b = idx[k]
            c = idx[(k + 1) % len(idx)]
            pa, pb, pc = poly[a], poly[b], poly[c]
            cross = ((pb[0] - pa[0]) * (pc[1] - pa[1])
                     - (pb[1] - pa[1]) * (pc[0] - pa[0]))
            if cross <= 1e-12:
                continue
            bad = False
            for t in idx:
                if t in (a, b, c):
                    continue
                q = poly[t]
                d1 = ((pb[0] - pa[0]) * (q[1] - pa[1])
                      - (pb[1] - pa[1]) * (q[0] - pa[0]))
                d2 = ((pc[0] - pb[0]) * (q[1] - pb[1])
                      - (pc[1] - pb[1]) * (q[0] - pb[0]))
                d3 = ((pa[0] - pc[0]) * (q[1] - pc[1])
                      - (pa[1] - pc[1]) * (q[0] - pc[0]))
                if d1 >= -1e-9 and d2 >= -1e-9 and d3 >= -1e-9:
                    bad = True
                    break
            if bad:
                continue
            tris.append((a, b, c))
            idx.pop(k)
            made = True
            break
        if not made:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def _keyhole(outer_pts, hole_pts):
    """Splice a hole into its outer loop so one simple polygon results.

    Standard keyhole: cut from a vertex of the outer loop to the nearest
    vertex of the hole, walk the whole hole, and come back along the same
    edge. The returned list is a closed polygon with a doubled edge (which
    ear clipping handles, and which is exactly how a hole is represented
    without needing a multi-contour triangulator).
    """
    n, m = len(outer_pts), len(hole_pts)
    best = None
    for i in range(n):
        for j in range(m):
            d = ((outer_pts[i][0] - hole_pts[j][0]) ** 2
                 + (outer_pts[i][1] - hole_pts[j][1]) ** 2)
            if best is None or d < best[0]:
                best = (d, i, j)
    _, i, j = best
    # outer up to and including i, then the complete hole loop starting and
    # ending at j, then the rest of the outer loop
    return ([(k, "o") for k in range(i + 1)]
            + [(k, "h") for k in [(j + t) % m for t in range(m + 1)]]
            + [(k, "o") for k in range(i + 1, n)])


def _triangulate_with_holes(outer_pts, holes):
    """Triangulate a polygon with any number of holes.

    mapbox_earcut takes one flat coordinate list and a ring-end array, so N
    holes is the same call as one: the ring ends just accumulate. Returns index
    triples into `outer_pts + hole0 + hole1 + ...`.
    """
    try:
        import mapbox_earcut as _me
        import numpy as _np
    except Exception:                                   # pragma: no cover
        if len(holes) == 1:
            return _triangulate_keyhole(outer_pts, holes[0])
        raise

    flat = list(outer_pts)
    ends = [len(flat)]
    for h in holes:
        flat.extend(h)
        ends.append(len(flat))
    coords = _np.array(flat, dtype=_np.float64)
    ring_end = _np.array(ends, dtype=_np.uint32)
    tris = _me.triangulate_float64(coords, ring_end)
    return [(int(tris[i]), int(tris[i + 1]), int(tris[i + 2]))
            for i in range(0, len(tris), 3)]


def _triangulate_with_hole(outer_pts, hole_pts):
    """Triangulate a polygon with one hole. Returns index triples into
    outer_pts + hole_pts (outer first, then hole).

    Uses mapbox_earcut, which is a proper earcut implementation and handles the
    hole without a keyhole corridor. The keyhole hand-roll was tried first and
    kept leaving a seam across the opening; a library that exists for exactly
    this job is the right answer.
    """
    try:
        import mapbox_earcut as _me
        import numpy as _np
    except Exception:                                   # pragma: no cover
        return _triangulate_keyhole(outer_pts, hole_pts)

    coords = _np.array(list(outer_pts) + list(hole_pts), dtype=_np.float64)
    n_out = len(outer_pts)
    ring_end = _np.array([n_out, len(coords)], dtype=_np.uint32)
    tris = _me.triangulate_float64(coords, ring_end)
    return [(int(tris[i]), int(tris[i + 1]), int(tris[i + 2]))
            for i in range(0, len(tris), 3)]


def _triangulate_keyhole(outer_pts, hole_pts):
    """Fallback if mapbox_earcut is unavailable: keyhole-corridor ear clip."""
    key = _keyhole(outer_pts, hole_pts)
    pts = [(outer_pts[k] if side == "o" else hole_pts[k]) for (k, side) in key]
    return [tuple(key[t]) for t in ()] or [
        t for t in _earclip_idx(pts)]


def _earclip_idx(pts):
    """Ear clip a simple polygon, returning triples that index `pts`."""
    n = len(pts)
    idx = list(range(n))
    if signed_area(pts) < 0:
        idx.reverse()
    tris, guard = [], 0
    while len(idx) > 3 and guard < 8 * n * n:
        guard += 1
        made = False
        for k in range(len(idx)):
            a, b, c = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            pa, pb, pc = pts[a], pts[b], pts[c]
            cr = ((pb[0] - pa[0]) * (pc[1] - pa[1])
                  - (pb[1] - pa[1]) * (pc[0] - pa[0]))
            if cr <= 1e-12:
                continue
            ok = True
            for t in idx:
                if t in (a, b, c):
                    continue
                q = pts[t]
                d1 = ((pb[0] - pa[0]) * (q[1] - pa[1])
                      - (pb[1] - pa[1]) * (q[0] - pa[0]))
                d2 = ((pc[0] - pb[0]) * (q[1] - pb[1])
                      - (pc[1] - pb[1]) * (q[0] - pb[0]))
                d3 = ((pa[0] - pc[0]) * (q[1] - pc[1])
                      - (pa[1] - pc[1]) * (q[0] - pc[0]))
                if d1 >= -1e-9 and d2 >= -1e-9 and d3 >= -1e-9:
                    ok = False
                    break
            if not ok:
                continue
            tris.append((a, b, c))
            idx.pop(k)
            made = True
            break
        if not made:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris



def _drop_collinear(pts, tol=1e-9):
    """Remove vertices that sit exactly on the straight line between their
    neighbours. earcut does this internally; doing it to the outline too means
    the cap and the skin agree on which vertices exist, so the STL has no
    T-junctions and welds cleanly."""
    out = list(pts)
    changed = True
    while changed and len(out) > 3:
        changed = False
        k = 0
        while k < len(out) and len(out) > 3:
            a = out[k - 1]
            b = out[k]
            c = out[(k + 1) % len(out)]
            cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cr) <= tol * (1.0 + abs(a[0]) + abs(a[1])):
                out.pop(k)
                changed = True
            else:
                k += 1
    return out



def prism_with_hole(outer, hole, a0, a1, plane="x", mat="walnut", chamfer=0.0):
    """A solid extruded from `outer` with a real hole through it."""
    o = _drop_collinear([(float(u), float(v)) for (u, v) in outer])
    i_loop = _drop_collinear([(float(u), float(v)) for (u, v) in hole])
    n, m = len(o), len(i_loop)
    if signed_area(o) < 0:
        o = o[::-1]
    if signed_area(i_loop) * signed_area(o) > 0:
        i_loop = i_loop[::-1]

    if chamfer > 1e-6:
        o_in = inset_loop(o, chamfer)
        stops = ((a0, o), (a0 + chamfer, o_in),
                 (a1 - chamfer, o_in), (a1, o))
    else:
        stops = ((a0, o), (a1, o))

    verts, faces = [], []
    for (a, ring) in stops:                      # ---- outer skin
        verts += [_place(plane, a, u, v) for (u, v) in ring]
    rings = len(stops)
    for r in range(rings - 1):
        b0, b1 = r * n, (r + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((b0 + k, b0 + k2, b1 + k2))
            faces.append((b0 + k, b1 + k2, b1 + k))
    # ---- the wall of the hole
    h0 = len(verts)
    verts += [_place(plane, a0, u, v) for (u, v) in i_loop]
    verts += [_place(plane, a1, u, v) for (u, v) in i_loop]
    for k in range(m):
        k2 = (k + 1) % m
        faces.append((h0 + m + k2, h0 + m + k, h0 + k))
        faces.append((h0 + m + k2, h0 + k, h0 + k2))
    # ---- end caps: one triangulation, reused at both ends.
    # The cap gets its own vertices rather than borrowing the skin's. earcut
    # legitimately drops collinear boundary points, so a shared-vertex cap
    # leaves T-junctions along long straight edges; a cap with its own copied
    # vertices is watertight by position (which is what an STL needs) and has
    # no cracks at all.
    tris = _triangulate_with_hole(o, i_loop)
    cap_src = list(o) + list(i_loop)
    # earcut can hand back the odd zero-area sliver on a long straight edge.
    # Those slivers carry no area but do leave loose edges in the STL, so drop
    # them here rather than in the exporter.
    def _area(t):
        a, b, c = cap_src[t[0]], cap_src[t[1]], cap_src[t[2]]
        return abs((b[0] - a[0]) * (c[1] - a[1])
                   - (b[1] - a[1]) * (c[0] - a[0])) * 0.5
    tris = [t for t in tris if _area(t) > 1e-6]
    for a, flip in ((a0, True), (a1, False)):
        base = len(verts)
        verts += [_place(plane, a, u, v) for (u, v) in cap_src]
        for (x, y, z) in tris:
            q = [base + x, base + y, base + z]
            if flip:
                q = q[::-1]
            faces.append(tuple(q))
    return Mesh(mat).add(verts, faces)


def prism_with_holes(outer, holes, a0, a1, plane="x", mat="walnut", chamfer=0.0):
    """A solid extruded from `outer`, bored by any number of `holes`.

    Same contract as prism_with_hole, but the bore list is a list. This is what
    lets a column carry an array of adjuster holes, or a base plate carry a row
    of pockets, without splitting the part into pieces that only touch.
    """
    o = _drop_collinear([(float(u), float(v)) for (u, v) in outer])
    if signed_area(o) < 0:
        o = o[::-1]
    hs = []
    for h in holes:
        hl = _drop_collinear([(float(u), float(v)) for (u, v) in h])
        if len(hl) < 3:
            continue
        if signed_area(hl) * signed_area(o) > 0:
            hl = hl[::-1]
        hs.append(hl)
    if not hs:
        return prism(o, a0, a1, mat=mat)
    if len(hs) == 1:
        return prism_with_hole(o, hs[0], a0, a1, plane=plane, mat=mat, chamfer=chamfer)

    n = len(o)
    if chamfer > 1e-6:
        o_in = inset_loop(o, chamfer)
        stops = ((a0, o), (a0 + chamfer, o_in),
                 (a1 - chamfer, o_in), (a1, o))
    else:
        stops = ((a0, o), (a1, o))

    verts, faces = [], []
    for (a, ring) in stops:                      # ---- outer skin
        verts += [_place(plane, a, u, v) for (u, v) in ring]
    rings = len(stops)
    for r in range(rings - 1):
        b0, b1 = r * n, (r + 1) * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((b0 + k, b0 + k2, b1 + k2))
            faces.append((b0 + k, b1 + k2, b1 + k))

    for hl in hs:                                # ---- the walls of every bore
        m = len(hl)
        base = len(verts)
        verts += [_place(plane, a0, u, v) for (u, v) in hl]
        verts += [_place(plane, a1, u, v) for (u, v) in hl]
        for k in range(m):
            k2 = (k + 1) % m
            faces.append((base + m + k2, base + m + k, base + k))
            faces.append((base + m + k2, base + k, base + k2))

    cap_src = list(o)
    for hl in hs:
        cap_src += list(hl)
    tris = _triangulate_with_holes(o, hs)

    def _area(t):
        a, b, c = cap_src[t[0]], cap_src[t[1]], cap_src[t[2]]
        return abs((b[0] - a[0]) * (c[1] - a[1])
                   - (b[1] - a[1]) * (c[0] - a[0])) * 0.5
    tris = [t for t in tris if _area(t) > 1e-6]
    for a, flip in ((a0, True), (a1, False)):
        base = len(verts)
        verts += [_place(plane, a, u, v) for (u, v) in cap_src]
        for (x, y, z) in tris:
            q = [base + x, base + y, base + z]
            if flip:
                q = q[::-1]
            faces.append(tuple(q))
    return Mesh(mat).add(verts, faces)


def vertex_normals(v, f):
    n = np.zeros_like(v)
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    fn = np.cross(b - a, c - a)
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    ln = np.linalg.norm(n, axis=1)
    ln[ln < 1e-12] = 1.0
    return n / ln[:, None]


# ---------------------------------------------------------------- camera
class Camera(object):
    def __init__(self, eye, target, up=(0, 1, 0), fov=24.0):
        self.eye = np.asarray(eye, dtype=np.float64)
        self.target = np.asarray(target, dtype=np.float64)
        self.up = np.asarray(up, dtype=np.float64)
        self.fov = fov

    def basis(self):
        f = self.target - self.eye
        f = f / np.linalg.norm(f)
        s = np.cross(f, self.up)
        s = s / np.linalg.norm(s)
        return s, np.cross(s, f), f

    def project(self, p):
        s, u, f = self.basis()
        d = np.asarray(p, dtype=np.float64) - self.eye
        return np.stack([d @ s, d @ u, d @ f], axis=-1)


def orbit(target, dist, az, el):
    az, el = np.radians(az), np.radians(el)
    return (target[0] + dist * np.cos(el) * np.sin(az),
            target[1] + dist * np.sin(el),
            target[2] + dist * np.cos(el) * np.cos(az))


def fit_camera(pts, az, el, w, h, margin=0.94, fov=26.0, target=None):
    """Exact fit: choose the distance so every point lands inside the frame."""
    p = np.asarray(pts, dtype=np.float64)
    if target is None:
        target = (p.min(0) + p.max(0)) / 2.0
    target = np.asarray(target, dtype=np.float64)
    s, u, _ = Camera(orbit(target, 1000.0, az, el), target).basis()
    d = p - target
    xs, ys = d @ s, d @ u
    fpx = 0.5 * min(w, h) / np.tan(np.radians(fov) * 0.5) * (min(w, h) / float(min(w, h)))
    # focal length in pixels for a vertical fov; use the same for both axes
    fpx = 0.5 * h / np.tan(np.radians(fov) * 0.5)
    half_w = 0.5 * w * margin
    half_h = 0.5 * h * margin
    # depth along the view direction, measured from the target
    zs = -d @ (Camera(orbit(target, 1000.0, az, el), target).basis()[2])
    need = np.maximum(np.abs(xs) * fpx / half_w, np.abs(ys) * fpx / half_h) + zs
    dist = float(need.max()) * 1.02
    return Camera(orbit(target, dist, az, el), target, fov=fov)


# ---------------------------------------------------------------- raster
def _raster(v, nrm, fa, cam, W, H, tri_mat):
    sv, uv, fv = cam.project(v).T
    depth = np.maximum(fv, 1e-4)
    fpx = 0.5 * H / np.tan(np.radians(cam.fov) * 0.5)
    px = W / 2.0 + sv / depth * fpx
    py = H / 2.0 - uv / depth * fpx

    zbuf = np.full((H, W), np.inf, dtype=np.float32)
    nbuf = np.zeros((H, W, 3), dtype=np.float32)
    pbuf = np.zeros((H, W, 3), dtype=np.float32)
    ibuf = np.full((H, W), -1, dtype=np.int16)

    tx, ty, tz = px[fa], py[fa], depth[fa]
    tn, tp = nrm[fa].astype(np.float32), v[fa].astype(np.float32)
    for t in np.argsort(-tz.mean(axis=1)):
        _tri(tx[t], ty[t], tz[t], tn[t], tp[t], int(tri_mat[t]),
             zbuf, nbuf, pbuf, ibuf)
    return zbuf, nbuf, pbuf, ibuf, depth.max()


def _tri(ax, ay, az, tn, p3, mid, zbuf, nbuf, pbuf, ibuf):
    H, W = zbuf.shape
    xmin = max(int(np.floor(ax.min())), 0)
    xmax = min(int(np.ceil(ax.max())) + 1, W)
    ymin = max(int(np.floor(ay.min())), 0)
    ymax = min(int(np.ceil(ay.max())) + 1, H)
    if xmin >= xmax or ymin >= ymax:
        return
    area = (ax[1] - ax[0]) * (ay[2] - ay[0]) - (ax[2] - ax[0]) * (ay[1] - ay[0])
    if abs(area) < 1e-9:
        return
    X, Y = np.meshgrid(np.arange(xmin, xmax) + 0.5, np.arange(ymin, ymax) + 0.5)
    l0 = ((ax[1] - X) * (ay[2] - Y) - (ax[2] - X) * (ay[1] - Y)) / area
    l1 = ((ax[2] - X) * (ay[0] - Y) - (ax[0] - X) * (ay[2] - Y)) / area
    l2 = 1.0 - l0 - l1
    inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
    if not inside.any():
        return
    d = l0 * az[0] + l1 * az[1] + l2 * az[2]
    zsub = zbuf[ymin:ymax, xmin:xmax]
    m = inside & (d < zsub)
    if not m.any():
        return
    pw = np.stack([l0, l1, l2], axis=0) / np.maximum(d, 1e-6)[None]
    pw = pw / pw.sum(axis=0)[None]
    zsub[m] = d[m].astype(np.float32)
    nbuf[ymin:ymax, xmin:xmax][m] = (
        pw[:, :, :, None] * tn[:, None, None, :]).sum(0)[m].astype(np.float32)
    pbuf[ymin:ymax, xmin:xmax][m] = (
        pw[:, :, :, None] * p3[:, None, None, :]).sum(0)[m].astype(np.float32)
    ibuf[ymin:ymax, xmin:xmax][m] = mid


# ---------------------------------------------------------------- shading
PALETTE = {
    "walnut": dict(alb=(0.230, 0.140, 0.090), spec=0.36, shin=40.0, metal=0.0, grain=0.070),
    "oak":    dict(alb=(0.560, 0.430, 0.280), spec=0.26, shin=24.0, metal=0.0, grain=0.060),
    "ash":    dict(alb=(0.640, 0.560, 0.430), spec=0.24, shin=20.0, metal=0.0, grain=0.042),
    "black":  dict(alb=(0.045, 0.045, 0.048), spec=0.26, shin=22.0, metal=0.0, grain=0.0),
    "metal":  dict(alb=(0.300, 0.315, 0.335), spec=0.95, shin=60.0, metal=1.0, grain=0.0),
    "felt":   dict(alb=(0.042, 0.045, 0.050), spec=0.02, shin=4.0, metal=0.0, grain=0.0),
    "brass":  dict(alb=(0.330, 0.222, 0.078), spec=0.62, shin=46.0, metal=1.0, grain=0.0),
    "mat":    dict(alb=(0.135, 0.140, 0.150), spec=0.06, shin=12.0, metal=0.0, grain=0.0),
    "graphite": dict(alb=(0.072, 0.075, 0.082), spec=0.10, shin=16.0, metal=0.0, grain=0.0),
    "floor":  dict(alb=(0.830, 0.845, 0.868), spec=0.04, shin=10.0, metal=0.0, grain=0.0),
}

KEY = np.array([0.50, 0.72, 0.48])
FILL = np.array([-0.70, 0.34, -0.18])
RIM = np.array([0.06, 0.26, -0.96])


def _unit(v):
    return v / np.linalg.norm(v)


def shade(pbuf, nbuf, ibuf, mats, cam, bg_top, bg_bot, exposure=1.0,
          vignette=0.16, shadow=None, shadow_ids=(), depth_fade=None):
    H, W = ibuf.shape
    yy = np.linspace(0, 1, H)[:, None, None]
    img = np.repeat(np.array(bg_top)[None, None, :] * (1 - yy)
                    + np.array(bg_bot)[None, None, :] * yy, W, axis=1)

    hit = ibuf >= 0
    if not hit.any():
        return np.clip(img, 0, 1)

    P, N, ids = pbuf[hit], nbuf[hit], ibuf[hit]
    nrm = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    # two-sided: a normal that faces away from the camera is turned around, so
    # a face that happens to be wound the other way still lights correctly
    vdir = P - cam.eye
    flip = (nrm * vdir).sum(1) > 0
    nrm[flip] *= -1.0

    alb = np.zeros_like(nrm)
    spec = np.zeros(len(nrm))
    shin = np.ones(len(nrm))
    metal = np.zeros(len(nrm))
    grain = np.zeros(len(nrm))
    brass = np.zeros(len(nrm))
    for i, name in enumerate(mats):
        sel = ids == i
        if not sel.any():
            continue
        m = PALETTE[name]
        alb[sel] = m["alb"]
        spec[sel] = m["spec"]
        shin[sel] = m["shin"]
        metal[sel] = m["metal"]
        grain[sel] = m["grain"]
        brass[sel] = 1.0 if name == "brass" else 0.0

    L1, L2, L3 = _unit(KEY), _unit(FILL), _unit(RIM)
    V = P - cam.eye
    V /= np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-9)

    d1 = np.clip(nrm @ L1, 0, 1) ** 0.85
    d2 = np.clip(nrm @ L2 * 0.5 + 0.5, 0, 1) ** 1.7
    d3 = np.clip(nrm @ L3 * 0.5 + 0.5, 0, 1) ** 2.0
    sky = np.clip(nrm[:, 1] * 0.5 + 0.5, 0, 1)
    light = 0.86 * d1 + 0.22 * d2 + 0.10 * d3 + 0.19 + 0.11 * sky

    col = alb * light[:, None]

    for L, inten, sh_ in ((L1, 0.90, 1.0), (L2, 0.16, 0.85), (L3, 0.10, 0.7)):
        Hh = L[None, :] - V
        Hh /= np.maximum(np.linalg.norm(Hh, axis=1, keepdims=True), 1e-9)
        sp = np.clip((nrm * Hh).sum(1), 0, 1) ** (shin * sh_)
        col += (spec * inten * sp)[:, None]

    if grain.any():
        # grain runs along the part, so it varies slowly across it; a slow
        # drift keeps the lines from looking printed
        drift = np.sin(P[:, 0] * 0.009 + P[:, 2] * 0.005) * 3.2
        g1 = np.sin(P[:, 2] * 0.075 + drift)
        g2 = np.sin(P[:, 2] * 0.19 + drift * 1.4 + 0.7)
        g3 = np.sin(P[:, 2] * 0.46 + drift * 2.1 + 1.9)
        g = 0.5 + 0.42 * g1 + 0.28 * g2 + 0.13 * g3
        col *= (1.0 + (grain * (g - 0.5))[:, None])

    # metal: a soft studio environment, brighter at the top
    if (metal > 0).any():
        # a dark satin alloy: bright where it turns up to the sky, nearly black
        # underneath. Never white, or it reads as a lamp.
        env = np.clip(nrm[:, 1] * 0.5 + 0.5, 0, 1) ** 1.1
        streak = 0.96 + 0.04 * np.sin(P[:, 0] * 0.35)
        steel = np.array([0.255, 0.272, 0.292])
        gold = np.array([0.520, 0.372, 0.148])
        base = np.where((brass > 0)[:, None], gold[None, :], steel[None, :])
        mc = (base * (0.62 + 0.80 * env[:, None])) * streak[:, None]
        mc += 0.10 * (brass[:, None]) * (env[:, None] ** 4)
        col = np.where((metal > 0)[:, None], mc, col)

    rim = (1.0 - np.clip((nrm * -V).sum(1), 0, 1)) ** 3.4
    col += (0.045 * rim)[:, None] * (1 - metal)[:, None]

    # contact shadow, but only on the floor: the product never shadows itself
    if shadow is not None and shadow_ids:
        sh = shadow[hit]
        onfloor = np.isin(ids, list(shadow_ids))
        k = np.where(onfloor, 1.0 - 0.80 * sh, 1.0)
        col *= k[:, None]

    # the floor melts into the backdrop at the horizon
    if depth_fade is not None and shadow_ids:
        onfloor = np.isin(ids, list(shadow_ids))
        if onfloor.any():
            d = np.linalg.norm(P[onfloor] - cam.eye, axis=1)
            f = np.clip((d - depth_fade[0]) / max(1e-6, depth_fade[1] - depth_fade[0]), 0, 1)
            f = f ** 1.5
            bgc = (np.array(bg_top)[None, :] * 0.35 + np.array(bg_bot)[None, :] * 0.65)
            col[onfloor] = col[onfloor] * (1 - f)[:, None] + bgc * f[:, None]

    col = np.clip(col * exposure, 0, 1)
    col = col * (1.24 - 0.24 * col)
    img[hit] = col

    gy, gx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((gx - W / 2) / (W / 2.0)) ** 2 + ((gy - H / 2) / (H / 2.0)) ** 2)
    img *= (1.0 - vignette * np.clip(r - 0.5, 0, 2) ** 2)[:, :, None]
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- shadow
def _blur(a, r):
    if r <= 0:
        return a
    k = np.ones(2 * r + 1) / (2 * r + 1)
    b = np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 0, a)
    return np.apply_along_axis(lambda m: np.convolve(m, k, mode="same"), 1, b)


def _fill_tri(buf, ax, ay, val):
    h, w = buf.shape
    xmin = max(int(np.floor(ax.min())), 0)
    xmax = min(int(np.ceil(ax.max())) + 1, w)
    ymin = max(int(np.floor(ay.min())), 0)
    ymax = min(int(np.ceil(ay.max())) + 1, h)
    if xmin >= xmax or ymin >= ymax:
        return
    area = (ax[1] - ax[0]) * (ay[2] - ay[0]) - (ax[2] - ax[0]) * (ay[1] - ay[0])
    if abs(area) < 1e-9:
        return
    X, Y = np.meshgrid(np.arange(xmin, xmax) + 0.5, np.arange(ymin, ymax) + 0.5)
    l0 = ((ax[1] - X) * (ay[2] - Y) - (ax[2] - X) * (ay[1] - Y)) / area
    l1 = ((ax[2] - X) * (ay[0] - Y) - (ax[0] - X) * (ay[2] - Y)) / area
    inside = (l0 >= 0) & (l1 >= 0) & ((1 - l0 - l1) >= 0)
    sub = buf[ymin:ymax, xmin:xmax]
    np.maximum(sub, np.where(inside, val, 0.0), out=sub)


def shadow_mask(meshes, cam, W, H, floor_y, res=2, blur=12, strength=1.0):
    """Soft contact shadow: flatten every triangle onto the floor along the key."""
    w, h = max(1, W // res), max(1, H // res)
    fpx = 0.5 * h / np.tan(np.radians(cam.fov) * 0.5)
    L = _unit(KEY)
    mask = np.zeros((h, w), dtype=np.float32)
    for m in meshes:
        v, fa = m.arrays()
        if not len(fa):
            continue
        ok = np.all(v[fa][:, :, 1] > floor_y + 0.05, axis=1)
        sel = fa[ok]
        if not len(sel):
            continue
        p = v.copy()
        t = (p[:, 1] - floor_y) / L[1]
        p[:, 1] = floor_y
        p[:, 0] -= t * L[0]
        p[:, 2] -= t * L[2]
        c = cam.project(p)
        d = np.maximum(c[:, 2], 1e-4)
        x = w / 2.0 + c[:, 0] / d * fpx
        y = h / 2.0 - c[:, 1] / d * fpx
        for k in range(len(sel)):
            _fill_tri(mask, x[sel[k]], y[sel[k]], 1.0)
    mask = np.clip(mask, 0, 1)
    mask = _blur(mask, blur)
    im = Image.fromarray((np.clip(mask * strength, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0


# ---------------------------------------------------------------- API
def backdrop_floor(y=0.0, span=4200.0, mat="floor"):
    """A big quad under the product. It catches the shadow and fades away."""
    m = Mesh(mat)
    m.add([(-span, y, -span), (span, y, -span), (span, y, span), (-span, y, span)],
          [(0, 1, 2), (0, 2, 3)])
    return m


def render(meshes, cam, w=1400, h=900, aa=2,
           bg_top=(0.960, 0.968, 0.978), bg_bot=(0.838, 0.858, 0.892),
           floor=True, floor_y=0.0, shadow=True, shadow_blur=14,
           exposure=1.0, vignette=0.16, grain=0.0, fade=(2400.0, 5200.0)):
    """Render a list of meshes. Returns a PIL image at w x h."""
    W, H = int(w * aa), int(h * aa)
    solids = [m for m in meshes if m is not None and len(m.f)]
    all_meshes = list(solids)
    floor_id = None
    if floor:
        all_meshes.append(backdrop_floor(floor_y))
        floor_id = len(solids)

    allv, allf, mats, tri_mat = [], [], [], []
    off = 0
    for m in all_meshes:
        v, fa = m.arrays()
        allv.append(v)
        allf.append(fa + off)
        mats.append(m.mat)
        tri_mat.append(np.full(len(fa), len(mats) - 1, dtype=np.int16))
        off += len(v)

    v = np.concatenate(allv)
    fa = np.concatenate(allf)
    tri_mat = np.concatenate(tri_mat)
    nrm = vertex_normals(v, fa)
    zbuf, nbuf, pbuf, ibuf, _ = _raster(v, nrm, fa, cam, W, H, tri_mat)

    shm = None
    if shadow and floor_id is not None:
        shm = shadow_mask(solids, cam, W, H, floor_y, blur=shadow_blur)

    img = shade(pbuf, nbuf, ibuf, mats, cam, bg_top, bg_bot,
                exposure=exposure, vignette=vignette, shadow=shm,
                shadow_ids=((floor_id,) if floor_id is not None else ()),
                depth_fade=(np.array(fade) * (W / float(max(w, 1)))) if floor_id is not None else None)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    im = im.resize((w, h), Image.LANCZOS)
    if grain > 0:
        arr = np.asarray(im).astype(np.float32)
        rng = np.random.default_rng(11)
        arr += rng.normal(0, grain * 255, arr.shape)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im


def scene_points(meshes):
    return np.concatenate([m.arrays()[0] for m in meshes if len(m.f)])
