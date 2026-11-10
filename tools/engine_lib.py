"""Shared CAD helpers for the IO-360 study model (see engine_cad.py)."""
import json, math, sys, os
import numpy as np
import cadquery as cq
import trimesh
from cadquery import Vector as V, Solid

TOL, ATOL = 0.012, 0.3

def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
# ---------- Solid helpers ----------
def vec(p): return V(float(p[0]), float(p[1]), float(p[2]))
def cyl(r, a, b):
    a, b = vec(a), vec(b); d = b - a
    return Solid.makeCylinder(r, d.Length, a, d.normalized())
def tube(ro, ri, a, b): return cyl(ro, a, b).cut(cyl(ri, a, b))
def cone(r1, r2, a, b):
    a, b = vec(a), vec(b); d = b - a
    return Solid.makeCone(r1, r2, d.Length, a, d.normalized())
def box(x0, x1, y0, y1, z0, z1): return Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def rbox(x0, x1, y0, y1, z0, z1, r):
    w = cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0)
    try: w = w.edges().fillet(r)
    except Exception: pass
    return w.val().translate(V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
def sphere(r, c): return Solid.makeSphere(r, vec(c), angleDegrees1=-90, angleDegrees2=90)
def lathe_y(pts): return cq.Workplane('XY').polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
def lathe_z(pts, z0=0.0): return lathe_y(pts).rotate(V(0, 0, 0), V(1, 0, 0), 90).translate(V(0, 0, z0))
def lathe_x(pts, x0=0.0): return lathe_y(pts).rotate(V(0, 0, 0), V(0, 0, 1), -90).translate(V(x0, 0, 0))
def plate(pts, x0, t):
    """Outline drawn in (u, v) = (Y, Z), extruded t along +X from x0."""
    return cq.Workplane('YZ', origin=(x0, 0, 0)).polyline([tuple(map(float, p)) for p in pts]).close().extrude(t).val()
def orient(shape, d, p):
    """Turn a shape built along +Z to point along d, then move its origin to p."""
    d = unit(d); z = np.array([0, 0, 1.0]); ax = np.cross(z, d); s = np.linalg.norm(ax)
    if s > 1e-9: shape = shape.rotate(V(0, 0, 0), vec(ax / s), math.degrees(math.atan2(s, np.dot(z, d))))
    elif d[2] < 0: shape = shape.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    return shape.translate(vec(p))
def hexprism(af, h):   # across-flats, height along +Z
    return cq.Workplane('XY').polygon(6, af / math.cos(math.pi / 6)).extrude(h).val()
def fuse(*shapes):
    out = shapes[0]
    for s in shapes[1:]: out = out.fuse(s)
    return out.clean()

def circle_pts(c, r, n=48, a0=0, a1=2 * math.pi):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
def hull(pts):
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (p[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0]) <= 0: out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]
def gear_pts(r_root, r_tip, teeth):
    pts = []
    for i in range(teeth):
        a = 2 * math.pi * i / teeth; s = 2 * math.pi / teeth
        for f, r in ((0, r_root), (.18, r_root), (.32, r_tip), (.62, r_tip), (.76, r_root)):
            pts.append((r * math.cos(a + f * s), r * math.sin(a + f * s)))
    return pts

# ---------- Tube meshes (pipes, wires, lines) ----------
def catmull(points, per=12):
    P = [np.asarray(p, float) for p in points]; P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2]); return np.array(out)
def tube_mesh(points, r, seg=16, per=12, caps=True):
    C = catmull(points, per); n = len(C)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    a = np.array([1.0, 0, 0]) if abs(T[0][0]) < .9 else np.array([0, 1.0, 0])
    N = [unit(np.cross(T[0], a))]
    for i in range(1, n):
        b = np.cross(T[i - 1], T[i]); nb = np.linalg.norm(b)
        if nb < 1e-9: N.append(N[-1]); continue
        b /= nb; ang = math.acos(max(-1, min(1, np.dot(T[i - 1], T[i]))))
        v = N[-1]; N.append(unit(v * math.cos(ang) + np.cross(b, v) * math.sin(ang) + b * np.dot(b, v) * (1 - math.cos(ang))))
    verts, faces = [], []
    for i in range(n):
        B = np.cross(T[i], N[i])
        for k in range(seg):
            th = 2 * math.pi * k / seg
            verts.append(C[i] + r * (math.cos(th) * N[i] + math.sin(th) * B))
    for i in range(n - 1):
        for k in range(seg):
            a0, a1 = i * seg + k, i * seg + (k + 1) % seg; b0, b1 = a0 + seg, a1 + seg
            faces += [[a0, b0, a1], [a1, b0, b1]]
    m = trimesh.Trimesh(np.array(verts), np.array(faces), process=False)
    if caps:
        for i, flip in ((0, True), (n - 1, False)):
            c = len(m.vertices); ring = [i * seg + k for k in range(seg)]
            cap_v = np.vstack([np.array(verts)[ring], C[i]])
            f = [[seg, (k + 1) % seg, k] if flip else [seg, k, (k + 1) % seg] for k in range(seg)]
            m = trimesh.util.concatenate([m, trimesh.Trimesh(cap_v, np.array(f), process=False)])
    return m

def orient_mesh(m, d, p):
    T = trimesh.geometry.align_vectors([0, 0, 1], unit(d)); T[:3, 3] = p
    return m.copy().apply_transform(T)

# ---------- Tessellation and export ----------
PARTS = {}
def add(part, mat, item):
    PARTS.setdefault(part, {}).setdefault(mat, []).append(item)
def to_mesh(item):
    if isinstance(item, trimesh.Trimesh): return item
    vs, fs, off = [], [], 0
    for face in item.Faces():
        v, t = face.tessellate(TOL, ATOL)
        if not t: continue
        vs.append(np.array([[p.x, p.y, p.z] for p in v])); fs.append(np.array(t) + off); off += len(v)
    return trimesh.Trimesh(np.vstack(vs), np.vstack(fs), process=False)

# ---------- Extra shapes ----------
def gear(n, x0, t, phase=0.0, module=0.1, bore=0.0):
    """Spur gear outline in the YZ plane (angle from +Y toward +Z), a tooth centered on `phase`."""
    r = module * n / 2; tip, root = r + module, r - 1.25 * module
    s = 2 * math.pi / n; pts = []
    for i in range(n):
        a = phase + i * s
        for f, rr in ((-.5, root), (-.3, root), (-.14, tip), (.14, tip), (.3, root)):
            pts.append((rr * math.cos(a + f * s), rr * math.sin(a + f * s)))
    g = plate(pts, x0, t)
    return g.cut(cyl(bore, (x0 - .1, 0, 0), (x0 + t + .1, 0, 0))) if bore else g
def mesh_phase(n_a, phase_a, n_b, alpha):
    """Phase for gear B so its teeth sit in gear A's gaps; alpha is the YZ angle from A's center to B's."""
    return alpha + math.pi - (2 * math.pi / n_b) * (.5 - (alpha - phase_a) * n_a / (2 * math.pi))
def yz(a, r=1.0):
    """Point in the YZ plane at angle a from +Y toward +Z."""
    return np.array([0.0, r * math.cos(a), r * math.sin(a)])
def poly_x(pts_zy, x0, x1):
    """Outline given as (z, y) points, extruded from x0 to x1."""
    return plate([(y, z) for z, y in pts_zy], x0, x1 - x0)
def bolt(p, d, af=.44, h=.26, washer=True):
    """Hex nut with a washer, sitting on point p and facing along d."""
    s = hexprism(af, h)
    if washer: s = s.fuse(cyl(af * .72, (0, 0, -.05), (0, 0, .03)))
    return orient(s, d, p)

def export(out_dir, layout):
    os.makedirs(out_dir, exist_ok=True)
    scene = trimesh.Scene(); total = 0
    for part, mats in PARTS.items():
        count = 0
        for mat, items in mats.items():
            m = trimesh.util.concatenate([to_mesh(i) for i in items])
            scene.add_geometry(m, node_name=f'{part}__{mat}', geom_name=f'{part}__{mat}')
            count += len(m.faces)
        total += count
        print(f'{part:14s} {count:8d} tris')
    print('total', total)
    glb = trimesh.exchange.gltf.export_glb(scene, include_normals=True)
    open(os.path.join(out_dir, 'io360.glb'), 'wb').write(glb)
    json.dump(layout, open(os.path.join(out_dir, 'io360-layout.json'), 'w'), indent=1)
    print('glb bytes', len(glb))
