"""Crankshaft, starter ring gear, propeller, camshaft, and the rear gear train."""
from engine_lib import *
from engine_layout import *

# ======================= CRANKSHAFT (crank frame: pin 1 toward +Z) =======================
def cheek(z_a, z_b, x0, x1, ra=1.45, rb=1.45):
    return plate(hull(circle_pts((0, z_a), ra) + circle_pts((0, z_b), rb)), x0, x1 - x0)
def pin(z, x0, x1): return cyl(PIN_R, (x0, 0, z), (x1, 0, z))

crank = [
    cyl(MAIN_R, (5.98, 0, 0), (8.3, 0, 0)), cheek(0, R, 5.28, 5.98, 1.6), pin(R, 5.28, 4.08),
    cheek(R, -R, 3.08, 4.08), pin(-R, 1.88, 3.08), cheek(-R, 0, 1.0, 1.88, 1.45, 1.6),
    cyl(MAIN_R, (-1.0, 0, 0), (1.0, 0, 0)),
    cheek(-R, 0, -1.88, -1.0, 1.45, 1.6), pin(-R, -3.08, -1.88), cheek(-R, R, -4.08, -3.08),
    pin(R, -5.28, -4.08), cheek(R, 0, -5.98, -5.28, 1.45, 1.6),
    cyl(MAIN_R, (-7.05, 0, 0), (-5.98, 0, 0)), cyl(.5, (-7.85, 0, 0), (-7.05, 0, 0)),
    cyl(1.19, (8.3, 0, 0), (11.2, 0, 0)), cone(1.19, 1.45, (11.2, 0, 0), (13.7, 0, 0)),
    cyl(2.75, (13.7, 0, 0), (14.1, 0, 0)),
]
shaft = fuse(*crank).cut(cyl(.6, (9.0, 0, 0), (14.2, 0, 0)))     # hollow front end
for i in range(6):
    p = yz(i * math.pi / 3, 2.375)
    add('crankshaft', 'steel', cyl(.3, p + [14.1, 0, 0], p + [14.55, 0, 0]))   # flange bushings
add('crankshaft', 'polished', shaft)
add('crankgear', 'gear', gear(N_CRANK, GX0, GT, 0.0, MOD, .5))

# Starter ring gear on its dished support, with the alternator belt pulley behind it
ring = plate(gear_pts(5.66, 5.9, 120), 12.2, .5).cut(cyl(5.5, (12.1, 0, 0), (12.8, 0, 0)))
add('ringgear', 'steel', ring)
dish = lathe_x([(1.2, 14.1), (2.9, 14.1), (5.2, 12.45), (5.2, 12.2), (5.55, 12.2), (5.55, 12.7), (5.35, 12.7),
                (3.0, 14.4), (1.2, 14.4)])
pulley = lathe_x([(4.1, 11.5), (4.7, 11.5), (4.7, 11.6), (4.42, 11.75), (4.7, 11.9), (4.7, 12.0), (4.3, 12.0),
                  (4.3, 13.05), (4.1, 13.2)])
support = dish.fuse(pulley)
for i in range(6):
    p = yz(i * math.pi / 3 + math.pi / 6, 3.45)
    support = support.cut(cyl(.42, p + [12.9, 0, 0], p + [14.5, 0, 0]))
add('ringgear', 'alu', support.clean())

# Propeller: two blades, hub, spinner
HUBX = 16.9
spinner = lathe_x([(0, 0)] + [(5.3 * (1 - t ** 2) ** .55, 8.6 * t) for t in np.linspace(0, 1, 16)[:-1]] + [(0, 8.6)], 14.6)
def blade(sign):
    secs = [(4.5, 2.2, 1.6, 45), (8, 4.6, 1.0, 34), (14, 5.4, .72, 24), (21, 5.2, .52, 18), (28, 4.6, .4, 14),
            (34, 3.6, .3, 12), (37.3, 1.8, .2, 11)]
    wires = []
    for r, ch, th, b in secs:
        bb = math.radians(b)
        wires.append(cq.Wire.makeEllipse(ch / 2, th / 2, V(HUBX, r, 0), V(0, 1, 0), V(math.sin(bb), 0, math.cos(bb))))
    s = Solid.makeLoft(wires, False)
    return s if sign > 0 else s.rotate(V(0, 0, 0), V(1, 0, 0), 180)
add('prop', 'prop', blade(1)); add('prop', 'prop', blade(-1))
add('prop', 'prop', cyl(1.5, (HUBX, -4.6, 0), (HUBX, 4.6, 0)))
add('prop', 'white', spinner)
add('prop', 'alu', cyl(5.3, (14.45, 0, 0), (14.6, 0, 0)))

# ======================= CAMSHAFT (cam frame) =======================
def lobe(x, a0, w=.56):
    """Lobe whose peak points along a0 (degrees from +Y toward +Z). Lift follows the page's curve."""
    pts = []
    for i in range(96):
        u = 360 * i / 96 - 180                      # cam degrees from the peak
        rr = CAM_BASE + (LIFT * .5 * (1 + math.cos(math.pi * 2 * u / HALF)) if abs(2 * u) < HALF else 0)
        a = math.radians(a0 + u)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return plate(pts, x - w / 2, w)
cam = [cyl(.45, (-7.3, 0, 0), (7.0, 0, 0)), cyl(.78, (6.3, 0, 0), (7.0, 0, 0)), cyl(.78, (-.5, 0, 0), (.5, 0, 0)),
       cyl(.78, (-7.0, 0, 0), (-6.3, 0, 0)), cyl(.6, (-7.85, 0, 0), (-7.3, 0, 0))]
for x, users in LOBES:
    cam.append(lobe(x, lobe_angle(*users[0])))
add('camshaft', 'steel', fuse(*cam))

# ======================= GEAR TRAIN =======================
aL = math.atan2(IDLER_L[1], IDLER_L[0]); aR = math.atan2(IDLER_R[1], IDLER_R[0])
phL = mesh_phase(N_CRANK, 0.0, N_IDLER, aL)
phR = mesh_phase(N_CRANK, 0.0, N_IDLER, aR)
aC = math.atan2(-IDLER_L[1], CAMY - IDLER_L[0])                 # from the left idler to the cam gear
phC = mesh_phase(N_IDLER, phL, N_CAM, aC)
def holes(g, n, r, rh):
    for i in range(n):
        p = yz(i * 2 * math.pi / n + .3, r)
        g = g.cut(cyl(rh, p + [GX0 - .1, 0, 0], p + [GX0 + GT + .1, 0, 0]))
    return g
add('idler_l', 'gear', holes(gear(N_IDLER, GX0, GT, phL, MOD, .3), 5, .8, .24))
add('idler_r', 'gear', holes(gear(N_IDLER, GX0, GT, phR, MOD, .3), 5, .8, .24))
add('camgear', 'gear', holes(gear(N_CAM, GX0, GT, phC, MOD), 5, .85, .26))
for key in ('idler_l', 'idler_r'):
    add(key, 'polished', cyl(.3, (GX0 - .15, 0, 0), (GX0 + GT + .25, 0, 0)))
