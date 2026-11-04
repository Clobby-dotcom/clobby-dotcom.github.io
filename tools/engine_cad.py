"""Builds the IO-360 study model as CAD solids and exports it for study/engine.html.

Units are inches. +X is the propeller end, +Y is up, +Z is the right side.
Every part is modeled in the frame the page animates it in:
  - world parts sit where they are on the engine
  - crankshaft parts are in the crank frame (axis along X, throw angle measured from +Z)
  - camshaft parts are in the cam frame (origin on the cam axis)
  - cylinder parts are in a cylinder frame: origin on the crank axis at the cylinder's
    station, +Z out along the bore, +Y up. The page mirrors the left bank by turning it 180°.

Run:  python engine_cad.py <out-dir>
Writes io360.glb (one node per part and material, named "<part>__<material>")
and io360-layout.json (the numbers the page uses to animate it).
"""
import json, math, sys, os
import numpy as np
import cadquery as cq
import trimesh
from cadquery import Vector as V, Solid

TOL, ATOL = 0.012, 0.3

# ---------- Layout (IO-360: 5.125 in bore, 4.375 in stroke) ----------
R, L = 2.1875, 6.75            # crank throw, rod center-to-center
BORE_R = 2.5625
DECK = 4.75                    # crank axis to cylinder pad
CAMY = 3.6                     # cam axis above the crank (gear pitch radii 1.2 + 2.4)
LIFT = 0.45                    # lobe lift
VX = {'intake': 1.0, 'exhaust': -1.0}
STEM = np.array([0.0, 0.75, 0.66]); STEM /= np.linalg.norm(STEM)
VFACE = {'intake': np.array([1.0, 0.4, 11.72]), 'exhaust': np.array([-1.0, 0.4, 11.72])}
VLEN = 4.2
ARM = 1.2                      # rocker arm length on each side of the pivot
CYL = [dict(n=1, s=1, x=4.45, fire=0, phi=0), dict(n=2, s=-1, x=2.45, fire=360, phi=180),
       dict(n=3, s=1, x=-2.45, fire=180, phi=180), dict(n=4, s=-1, x=-4.45, fire=540, phi=0)]
TOP_PLUG = (np.array([0, 3.25, 11.0]), np.array([0, .95, -.3]))
BOT_PLUG = (np.array([0, -3.25, 11.0]), np.array([0, -.95, -.3]))
NOZZLE = (np.array([2.1, 2.5, 10.7]), np.array([.64, .77, 0]))
MAG_POS = {'left': (3.2, -2.8), 'right': (3.2, 2.8)}       # (y, z) on the accessory housing
STARTER_YZ, ALT_YZ = (-6.05, -3.1), (-6.05, 3.1)
DIVIDER = np.array([-1.0, 6.15, 0.0])

def unit(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
for k in ('TOP_PLUG', 'BOT_PLUG', 'NOZZLE'):
    p, d = globals()[k]; globals()[k] = (p, unit(d))

# Rocker geometry: the pivot sits between the valve tip and the pushrod cup, so pushing
# the pushrod outward swings the other end down along the valve stem and opens the valve.
TIP = VFACE['intake'] + STEM * VLEN; TIP[0] = 0
NPERP = np.array([0, -STEM[2], STEM[1]])
PIV = TIP - NPERP * ARM
PUSH_TOP = PIV + np.array([0, ARM, -.15])
PUSH_LOW = np.array([0, CAMY, 2.6])
PDIR = unit(PUSH_TOP - PUSH_LOW)
def on_push(z, lx=0.0):
    p = PUSH_LOW + PDIR * ((z - PUSH_LOW[2]) / PDIR[2]); p[0] = lx; return p

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

# ======================= CRANKCASE =======================
def case_half(s):
    """Right half (s=1) built on +Z; the left half is built the same way and mirrored."""
    bank = [c for c in CYL if c['s'] == s]
    body = rbox(-8.0, 7.6, -4.6, 5.6, 0, 4.5, .6)
    nose = cone(3.4, 2.3, (7.4, 0, 0), (9.1, 0, 0)).cut(box(7, 10, -4, 4, -4, 0))
    shapes = [body, nose]
    for c in bank:
        shapes.append(cyl(3.55, (c['x'], 0, 4.3), (c['x'], 0, DECK)))
        for v, lx in VX.items():   # shroud tube bosses where the pushrods leave the case
            shapes.append(cyl(.55, on_push(4.2, c['x'] + lx), on_push(4.95, c['x'] + lx)))
    shapes.append(rbox(-7.4, 7.0, 5.35, 6.15, 0, .42, .12))      # top parting flange
    shapes.append(rbox(-7.4, 7.0, -4.95, -4.4, 0, .42, .1))      # bottom flange
    solid = fuse(*shapes)
    bolts = [orient(hexprism(.5, .22), (0, 0, 1), (x, 5.78, .42)) for x in np.arange(-6.6, 6.7, 1.65)]
    if s < 0:
        solid = solid.mirror('XY'); bolts = [b.mirror('XY') for b in bolts]
    name = 'case_r' if s > 0 else 'case_l'
    add(name, 'case', solid)
    for b in bolts: add(name, 'steel', b)
case_half(1); case_half(-1)

# ======================= CRANKSHAFT (crank frame) =======================
def web(pin_angle_deg, x0, t, counterweight=True):
    pts = circle_pts((0, 0), 1.55) + circle_pts((0, R), 1.35)
    w = plate(hull(pts), x0, t)
    if counterweight:
        cw = [(0, 0)] + circle_pts((0, 0), 3.05, 40, math.radians(-90 - 62), math.radians(-90 + 62))
        w = w.fuse(plate(hull(cw + circle_pts((0, 0), 1.55)), x0, t))
    return w.rotate(V(0, 0, 0), V(1, 0, 0), -pin_angle_deg)
def flying_web(x0, t):
    return plate(hull(circle_pts((0, R), 1.35) + circle_pts((0, -R), 1.35)), x0, t)
crank = [
    cyl(1.4, (7.6, 0, 0), (10.6, 0, 0)), cyl(1.25, (5.6, 0, 0), (7.6, 0, 0)),
    web(0, 5.1, .5), cyl(1.1, (3.8, 0, R), (5.1, 0, R)), flying_web(3.1, .7), cyl(1.1, (1.8, 0, -R), (3.1, 0, -R)),
    web(180, 1.35, .45), cyl(1.25, (-1.35, 0, 0), (1.35, 0, 0)), web(180, -1.8, .45),
    cyl(1.1, (-3.1, 0, -R), (-1.8, 0, -R)), flying_web(-3.8, .7), cyl(1.1, (-5.1, 0, R), (-3.8, 0, R)),
    web(0, -5.6, .5), cyl(1.25, (-7.6, 0, 0), (-5.6, 0, 0)), cyl(1.0, (-9.6, 0, -0.0), (-7.6, 0, 0)),
]
flange = cyl(3.4, (10.6, 0, 0), (11.2, 0, 0))
for i in range(6):
    a = math.pi / 6 + i * math.pi / 3
    flange = flange.cut(cyl(.26, (10.5, 2.6 * math.sin(a), 2.6 * math.cos(a)), (11.3, 2.6 * math.sin(a), 2.6 * math.cos(a))))
crank.append(flange); crank.append(cyl(1.1, (11.2, 0, 0), (11.9, 0, 0)))
add('crankshaft', 'polished', fuse(*crank))
add('crankgear', 'gear', plate(gear_pts(1.12, 1.32, 24), -9.15, .5).cut(cyl(.95, (-9.3, 0, 0), (-8.5, 0, 0))))

# Starter ring gear and its support, with the alternator belt pulley
ring_teeth = plate(gear_pts(6.1, 6.4, 100), 9.2, .5).cut(cyl(5.75, (9.1, 0, 0), (9.8, 0, 0)))
support = fuse(cyl(5.8, (9.3, 0, 0), (9.6, 0, 0)), cyl(2.1, (9.1, 0, 0), (10.6, 0, 0)), cyl(2.6, (9.85, 0, 0), (10.35, 0, 0)))
support = support.cut(Solid.makeTorus(2.75, .28, V(10.1, 0, 0), V(1, 0, 0))).cut(cyl(1.42, (9.0, 0, 0), (10.7, 0, 0)))
for i in range(6):
    a = i * math.pi / 3
    support = support.cut(cyl(.9, (9.2, 3.9 * math.sin(a), 3.9 * math.cos(a)), (9.7, 3.9 * math.sin(a), 3.9 * math.cos(a))))
add('ringgear', 'steel', ring_teeth); add('ringgear', 'alu', support)

# Propeller and spinner (fixed pitch, 75 in diameter)
spinner = lathe_x([(0, 0)] + [(5.3 * (1 - t ** 2) ** .55, 8.6 * t) for t in np.linspace(0, 1, 16)[:-1]] + [(0, 8.6)], 11.3)
add('prop', 'white', spinner)
def blade(sign):
    secs = [(4.5, 2.2, 1.6, 45), (8, 4.6, 1.0, 34), (14, 5.4, .72, 24), (21, 5.2, .52, 18), (28, 4.6, .4, 14), (34, 3.6, .3, 12), (37.3, 1.8, .2, 11)]
    wires = []
    for r, ch, th, b in secs:
        bb = math.radians(b)
        wires.append(cq.Wire.makeEllipse(ch / 2, th / 2, V(13.6, r, 0), V(0, 1, 0), V(math.sin(bb), 0, math.cos(bb))))
    s = Solid.makeLoft(wires, False)
    return s if sign > 0 else s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
add('prop', 'prop', blade(1)); add('prop', 'prop', blade(-1))

# ======================= CAMSHAFT (cam frame) =======================
def lobe_pts(n=72):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n; c = math.cos(a)
        rr = .85 + LIFT * (max(0.0, c) ** 2.2)
        pts.append((math.sin(a) * rr, c * rr))
    return pts
LOBES = [  # x, cylinder, valve  (opposite cylinders share the middle lobe of each pair)
    (5.45, 1, 'intake'), (3.45, 1, 'exhaust'), (1.45, 2, 'intake'),
    (-1.45, 3, 'intake'), (-3.45, 3, 'exhaust'), (-5.45, 4, 'intake')]
camparts = [cyl(.55, (-9.4, 0, 0), (6.6, 0, 0)), cyl(.85, (6.0, 0, 0), (6.7, 0, 0)), cyl(.85, (-.6, 0, 0), (.6, 0, 0)), cyl(.85, (-8.2, 0, 0), (-7.2, 0, 0))]
for x, n, v in LOBES:
    c = CYL[n - 1]; peak = c['fire'] + (450 if v == 'intake' else 270)
    gamma = (0 if c['s'] > 0 else 180) + peak / 2
    camparts.append(plate(lobe_pts(), x - .31, .62).rotate(V(0, 0, 0), V(1, 0, 0), -gamma))
add('camshaft', 'steel', fuse(*camparts))
camgear = plate(gear_pts(2.32, 2.52, 48), -9.15, .5)
for i in range(5):
    a = i * 2 * math.pi / 5
    camgear = camgear.cut(cyl(.45, (-9.3, 1.45 * math.sin(a), 1.45 * math.cos(a)), (-8.5, 1.45 * math.sin(a), 1.45 * math.cos(a))))
add('camgear', 'gear', camgear)

# ======================= CYLINDER (cylinder frame) =======================
# Barrel: skirt into the case, hold-down flange, fins, threads into the head
bp = [(BORE_R, 3.5), (2.75, 3.5), (2.75, DECK), (3.45, DECK), (3.45, 5.2), (2.85, 5.2)]
z = 5.45
while z + .1 < 10.0:
    bp += [(2.85, z), (3.2, z), (3.2, z + .1), (2.85, z + .1)]; z += .3
bp += [(2.85, 11.0), (BORE_R, 11.0)]
add('barrel', 'paint', lathe_y(bp).rotate(V(0, 0, 0), V(1, 0, 0), 90))
for i in range(8):
    a = math.pi / 8 + i * math.pi / 4
    add('barrel', 'steel', orient(hexprism(.62, .32), (0, 0, 1), (3.12 * math.cos(a), 3.12 * math.sin(a), 5.2)))

# Head: finned, combustion chamber dome, rocker box on top, port and plug bosses
hp = [(0, 10.0), (3.0, 10.0)]
z = 10.3
while z + .14 < 15.0:
    hp += [(3.0, z), (3.4, z), (3.4, z + .14), (3.0, z + .14)]; z += .34
hp += [(3.0, 15.0), (0, 15.0)]
head = lathe_y(hp).rotate(V(0, 0, 0), V(1, 0, 0), 90)
for x in np.arange(-2.4, 2.5, .6):   # cooling fins across the outer end of the head
    head = head.fuse(box(x - .07, x + .07, -3.2, 2.4, 14.9, 15.85).intersect(cyl(3.05, (0, 0, 14.8), (0, 0, 16.0))))
rbox_outer = rbox(-2.5, 2.5, 2.3, 5.95, 11.7, 15.9, .35)
head = head.fuse(rbox_outer)
for p, d in (TOP_PLUG, BOT_PLUG):
    head = head.fuse(cyl(.58, p - d * .9, p + d * .05))
head = head.fuse(cyl(.75, (1.0, -2.6, 12.0), (1.0, -3.75, 12.0)))                     # intake port
head = head.fuse(rbox(-1.9, -.1, -3.95, -2.6, 12.3, 14.1, .15))                       # exhaust port
head = head.fuse(cyl(.38, NOZZLE[0] - NOZZLE[1] * .7, NOZZLE[0] + NOZZLE[1] * .02))   # injector boss
head = head.fuse(cyl(.3, (0, -2.6, 10.4), (0, -3.05, 10.4)))                           # drain fitting
head = head.cut(rbox(-2.2, 2.2, 2.6, 6.1, 12.0, 15.6, .2))                             # rocker well
head = head.cut(cyl(2.86, (0, 0, 9.9), (0, 0, 11.0)))                                  # barrel threads in here
rs = (BORE_R ** 2 + .9 ** 2) / (2 * .9)
head = head.cut(sphere(rs, (0, 0, 11.9 - rs)).intersect(box(-3, 3, -3, 3, 11.0, 12.0)))
add('head', 'paint', head.clean())

cover = rbox(-2.6, 2.6, 5.95, 6.35, 11.6, 16.0, .3)
add('cover', 'chrome', cover)
for x in (-2.15, 2.15):
    for zz in (12.0, 13.8, 15.6):
        add('cover', 'steel', cyl(.15, (x, 6.35, zz), (x, 6.48, zz)))

# Piston (pin at the origin), rings, pin
pp = [(0, 1.95), (2.545, 1.95), (2.545, -1.95), (2.25, -1.95), (2.25, 1.5), (0, 1.5)]
piston = lathe_z(pp)
for zr in (1.62, 1.36, 1.1):
    piston = piston.cut(lathe_z([(2.42, zr - .035), (2.6, zr - .035), (2.6, zr + .035), (2.42, zr + .035)]))
piston = piston.fuse(cyl(.85, (-2.3, 0, 0), (-1.55, 0, 0))).fuse(cyl(.85, (1.55, 0, 0), (2.3, 0, 0)))
piston = piston.cut(cyl(.5, (-2.6, 0, 0), (2.6, 0, 0)))
for v, pz in VFACE.items():
    piston = piston.cut(cyl(1.02, (pz[0], pz[1], 1.89), (pz[0], pz[1], 2.0)))
add('piston', 'piston', piston.clean())
for zr in (1.62, 1.36, 1.1):
    add('piston', 'dark', lathe_z([(2.43, zr - .03), (2.548, zr - .03), (2.548, zr + .03), (2.43, zr + .03)]))
add('piston', 'polished', tube(.5, .3, (-2.25, 0, 0), (2.25, 0, 0)))

# Connecting rod along +Z, big end at the origin
rod = fuse(tube(1.42, 1.1, (-.55, 0, 0), (.55, 0, 0)),
           rbox(-.5, .5, -1.6, -.95, -1.3, .5, .1), rbox(-.5, .5, .95, 1.6, -1.3, .5, .1),
           box(-.42, .42, -.5, .5, 1.0, L - .6),
           tube(.78, .5, (-.5, 0, L), (.5, 0, L)))
rod = rod.cut(box(.14, .5, -.36, .36, 1.4, L - .95)).cut(box(-.5, -.14, -.36, .36, 1.4, L - .95))
add('rod', 'steel', rod.clean())
for y in (-1.27, 1.27):
    add('rod', 'polished', cyl(.17, (0, y, -1.6), (0, y, .4)))
    add('rod', 'polished', orient(hexprism(.42, .3), (0, 0, -1), (0, y, -1.3)))

# Valves (built in place), springs, retainers
for v, face in VFACE.items():
    rh = .98 if v == 'intake' else .82
    vp = lathe_z([(0, 0), (rh, 0), (rh, .07), (rh - .12, .2), (.38, .5), (.18, .95), (.18, VLEN), (0, VLEN)])
    key = 'valve_in' if v == 'intake' else 'valve_ex'
    add(key, 'steel' if v == 'intake' else 'exvalve', orient(vp, STEM, face))
    coil = [(.5 * math.cos(a), .5 * math.sin(a), 2.05 + 1.45 * a / (2 * math.pi * 6.5)) for a in np.linspace(0, 2 * math.pi * 6.5, 160)]
    add(key, 'dark', orient_mesh(tube_mesh(coil, .065, 8, 2), STEM, face))
    ret = lathe_z([(.18, 0), (.62, 0), (.62, .1), (.3, .2), (.18, .2)])
    add(key, 'polished', orient(ret.translate(V(0, 0, 3.5)), STEM, face))
tip = {v: VFACE[v] + STEM * VLEN for v in VFACE}

# Rocker arm about its pivot (origin): a pad over the valve tip, a cup for the pushrod
t_rel = TIP - PIV + np.r_[0, STEM[1:] * .12]
p_rel = PUSH_TOP - PIV
arm = plate(hull(circle_pts((0, 0), .38) + circle_pts((t_rel[1], t_rel[2]), .22) + circle_pts((p_rel[1], p_rel[2]), .24)), -.16, .32)
arm = arm.cut(cyl(.17, (-.3, 0, 0), (.3, 0, 0)))
add('rocker', 'steel', arm)
add('rocker', 'polished', cyl(.17, (-.45, 0, 0), (.45, 0, 0)))
add('rocker', 'polished', sphere(.19, (0, p_rel[1] - .05, p_rel[2])))

# Lifters (in the case), pushrods that slide along their tubes, and the shroud tubes
for v, lx in VX.items():
    sfx = 'in' if v == 'intake' else 'ex'
    add('lifter_' + sfx, 'polished', fuse(cyl(.42, (lx, CAMY, .86), (lx, CAMY, 2.55)), cyl(.46, (lx, CAMY, .86), (lx, CAMY, 1.0))))
    a, b = PUSH_LOW + [lx, 0, .02], PUSH_TOP + [lx, -.2 * PDIR[1], -.2 * PDIR[2]]
    add('pushrod_' + sfx, 'polished', fuse(cyl(.15, a, b), sphere(.2, a), sphere(.18, b)))
    add('shroud', 'paint', tube(.34, .27, on_push(DECK, lx), on_push(11.75, lx)))
    for zz in (DECK + .25, 11.5):
        add('shroud', 'dark', Solid.makeTorus(.36, .06, vec(on_push(zz, lx)), vec(PDIR)))

# Spark plugs (top and bottom) and the injector nozzle
def plug(p, d, key):
    body = fuse(hexprism(.78, .5), cyl(.34, (0, 0, .5), (0, 0, 1.45)), cyl(.42, (0, 0, 1.45), (0, 0, 1.75)))
    add(key, 'steel', orient(body, d, p))
    add(key, 'red', orient(cyl(.3, (0, 0, 1.75), (0, 0, 2.25)), d, p))
plug(*TOP_PLUG, 'plug_top'); plug(*BOT_PLUG, 'plug_bot')
add('nozzle', 'brass', orient(fuse(hexprism(.5, .32), cyl(.2, (0, 0, .32), (0, 0, .75))), NOZZLE[1], NOZZLE[0]))

# Intake pipe (one per cylinder: each starts at the sump), exhaust riser, oil drain tube
def world_to_local(c, p): return np.array([(p[0] - c['x']) * c['s'], p[1], p[2] * c['s']])
for c in CYL:
    wx = c['x'] + c['s'] * VX['intake']
    start = world_to_local(c, (min(max(wx, -6.8), 2.6), -6.9, 4.0 * c['s']))
    path = [start, start + np.array([0, .2, 1.4]), (VX['intake'], -6.4, 8.2), (VX['intake'], -5.0, 11.0), (VX['intake'], -3.75, 12.0)]
    add(f'intake_{c["n"]}', 'paint', tube_mesh(path, .62, 20, 10))
add('exhaust', 'exhaust', tube_mesh([(-1, -3.95, 13.2), (-1, -6.4, 13.8), (-1, -10.3, 11.4), (-1, -12.0, 9.2)], .68, 20, 12))
add('exhaust', 'exhaust', rbox(-1.95, -.05, -4.25, -3.95, 12.25, 14.15, .1))
add('drain', 'alu', tube_mesh([(0, -3.0, 10.4), (0, -3.5, 9.7), (0, -3.5, 5.4), (0, -3.2, DECK)], .2, 12, 8))

# ======================= WORLD PARTS =======================
sump = rbox(-7.8, 3.4, -10.5, -4.4, -4.0, 4.0, .8)
sump = sump.fuse(cyl(.4, (-2.0, -10.5, 0), (-2.0, -10.95, 0)))
add('sump', 'paint', sump)

servo = fuse(rbox(-7.8, -4.8, -13.3, -10.5, -1.6, 1.6, .25), cyl(1.0, (-6.3, -12.0, 1.6), (-6.3, -12.0, 2.4)),
             cyl(1.15, (-6.3, -13.3, 0), (-6.3, -14.3, 0)))
add('servo', 'alu', servo)
add('servo', 'dark', rbox(-5.0, -4.6, -12.4, -11.2, -2.2, -1.6, .05))
add('servo', 'dark', rbox(-7.6, -7.2, -12.4, -11.4, 1.6, 2.0, .05))

div = fuse(cyl(.7, DIVIDER, DIVIDER + np.array([0, .9, 0])), cyl(.5, DIVIDER + np.array([0, .9, 0]), DIVIDER + np.array([0, 1.25, 0])))
add('divider', 'alu', div)

def nozzle_world(c):
    p = NOZZLE[0] + NOZZLE[1] * .75
    return np.array([c['x'] + c['s'] * p[0], p[1], c['s'] * p[2]])
for c in CYL:
    q = nozzle_world(c); s0 = DIVIDER + np.array([.0, .55, .0])
    side = np.sign(q[2])
    path = [s0, s0 + np.array([0, .4, .6 * side]), (q[0] * .6 + s0[0] * .4, 7.2, 3.0 * side), (q[0], 6.2, q[2] - 1.6 * side), q]
    add('injlines', 'polished', tube_mesh(path, .07, 8, 14))
add('injlines', 'polished', tube_mesh([(-6.3, -10.5, -1.0), (-7.3, -8.0, -4.6), (-7.5, -2.0, -5.1), (-7.2, 4.6, -4.8), (-4.0, 6.6, -1.5), DIVIDER + np.array([-.6, .45, 0])], .14, 10, 16))

acc = rbox(-10.0, -8.0, -4.4, 5.4, -4.2, 4.2, .6)
for side, (y, z) in MAG_POS.items():
    acc = acc.fuse(cyl(1.55, (-10.3, y, z), (-10.0, y, z)))
add('accessory', 'paint', acc)

for side, (y, z) in MAG_POS.items():
    key = 'mag_l' if side == 'left' else 'mag_r'
    add(key, 'black', fuse(cyl(1.35, (-13.6, y, z), (-10.3, y, z)), cyl(1.6, (-10.75, y, z), (-10.3, y, z))))
    add(key, 'dark', cyl(1.0, (-14.6, y, z), (-13.6, y, z)))
    add(key, 'polished', cyl(.18, (-12.0, y + 1.3, z), (-12.0, y + 1.75, z)))

add('filter', 'filter', cyl(1.5, (-13.9, .2, 0), (-10.5, .2, 0)))
add('filter', 'dark', cyl(1.1, (-10.5, .2, 0), (-10.0, .2, 0)))
add('fuelpump', 'alu', fuse(cyl(1.05, (-12.3, -2.8, -2.4), (-10.0, -2.8, -2.4)), cyl(.25, (-11.6, -2.8, -3.4), (-11.6, -2.8, -3.9))))
add('vacpump', 'black', fuse(cyl(1.15, (-12.6, -2.8, 2.4), (-10.0, -2.8, 2.4)), cyl(.3, (-12.9, -2.8, 2.4), (-12.6, -2.8, 2.4))))
add('dipstick', 'paint', cyl(.42, (-9.3, 5.2, 2.8), (-9.3, 8.7, 3.4)))
add('dipstick', 'black', fuse(cyl(.62, (-9.3, 8.7, 3.4), (-9.3, 9.2, 3.5)), box(-9.42, -9.18, 9.2, 9.75, 3.0, 4.0)))

sy, sz = STARTER_YZ
add('starter', 'black', fuse(cyl(1.7, (3.8, sy, sz), (7.6, sy, sz)), cone(1.25, .9, (7.6, sy, sz), (8.9, sy, sz))))
add('starter', 'steel', plate([(p[0] + sy, p[1] + sz) for p in gear_pts(.45, .62, 11)], 9.2, .5))
add('starter', 'polished', cyl(.22, (8.9, sy, sz), (9.7, sy, sz)))

ay, az = ALT_YZ
alt = fuse(cyl(2.0, (6.4, ay, az), (8.9, ay, az)), cyl(.3, (8.9, ay, az), (10.4, ay, az)))
for i in range(10):
    a = i * 2 * math.pi / 10
    alt = alt.cut(box(8.55, 8.95, ay + 1.6 * math.sin(a) - .12, ay + 1.6 * math.sin(a) + .12, az + 1.6 * math.cos(a) - .12, az + 1.6 * math.cos(a) + .12))
add('alternator', 'alu', alt)
pulley = cyl(1.1, (9.85, ay, az), (10.35, ay, az)).cut(Solid.makeTorus(1.25, .28, V(10.1, ay, az), V(1, 0, 0)))
add('alternator', 'dark', pulley)
outer = hull(circle_pts((0, 0), 2.86, 64) + circle_pts((ay, az), 1.0, 48))
belt = plate(outer, 9.95, .3)
inner = hull(circle_pts((0, 0), 2.56, 64) + circle_pts((ay, az), .78, 48))
belt = belt.cut(plate(inner, 9.9, .4))
add('belt', 'rubber', belt)

muff = []
for x in (3.45, -3.45):
    muff.append(tube_mesh([(x, -12.0, -9.6), (x, -12.0, 0), (x, -12.0, 9.6)], .9, 20, 4))
add('muffler', 'exhaust', fuse(cyl(2.0, (-4.4, -14.0, 0), (4.4, -14.0, 0)), sphere(2.0, (-4.4, -14.0, 0)), sphere(2.0, (4.4, -14.0, 0))))
for m in muff: add('muffler', 'exhaust', m)
add('muffler', 'exhaust', tube_mesh([(-5.6, -14.6, .6), (-7.6, -15.4, 2.0), (-9.8, -17.0, 3.6)], .8, 20, 10))
add('muffler', 'alu', tube(2.38, 2.2, (-2.8, -14.0, 0), (2.8, -14.0, 0)))
add('muffler', 'rubber', tube_mesh([(0, -11.8, 1.6), (0, -9.6, 3.2), (.6, -8.2, 6.0)], .9, 16, 10))

# Ignition harness: each magneto fires one plug in every cylinder
def plug_world(c, which):
    p, d = TOP_PLUG if which == 'top' else BOT_PLUG
    q = p + d * 2.2
    return np.array([c['x'] + c['s'] * q[0], q[1], c['s'] * q[2]])
for side, (y, z) in MAG_POS.items():
    src = np.array([-14.4, y, z])
    for c in CYL:
        which = 'top' if (c['s'] > 0) == (side == 'right') else 'bot'
        q = plug_world(c, which); sz_ = np.sign(q[2])
        if which == 'top':
            path = [src, (-15.2, y + 1.6, z), (-12.0, 7.4, 4.4 * sz_), (q[0], 7.0, 6.0 * sz_), (q[0], q[1] + 1.6, q[2] - 1.2 * sz_), q]
        else:
            path = [src, (-15.2, y - 1.0, z * 1.4), (-11.5, -1.5, 5.6 * sz_), (-8.0, -5.6, 6.2 * sz_), (q[0], -6.0, 6.8 * sz_), (q[0], q[1] - 1.2, q[2] - 1.0 * sz_), q]
        add('harness', 'harness', tube_mesh(path, .13, 8, 12))

# ======================= EXPORT =======================
out_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
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
layout = dict(R=R, L=L, CAMY=CAMY, LIFT=LIFT, VX=VX, STEM=STEM.tolist(), VLEN=VLEN, ARM=ARM,
              pivot=PIV[1:].tolist(), pushDir=PDIR.tolist(), cyl=CYL, lobes=LOBES)
json.dump(layout, open(os.path.join(out_dir, 'io360-layout.json'), 'w'), indent=1)
print('wrote', os.path.join(out_dir, 'io360.glb'), round(len(glb) / 1e6, 2), 'MB')
