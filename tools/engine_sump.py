"""Oil sump with the induction riser, intake pipes, and the fuel injector servo under it."""
from engine_lib import *
from engine_layout import *

def loft_y(p0, y0, p1, y1):
    """Solid between an (x, z) outline at y0 and another at y1."""
    w = [cq.Wire.makePolygon([V(x, y, z) for x, z in p], close=True) for p, y in ((p0, y0), (p1, y1))]
    return Solid.makeLoft(w, True)

# ---------- sump ----------
TOP = [(-7.9, -4.3), (4.2, -4.3), (5.4, -3.0), (5.4, 3.0), (4.2, 4.3), (-7.9, 4.3)]
BOT = [(-7.9, -3.3), (3.4, -3.3), (4.4, -2.3), (4.4, 2.3), (3.4, 3.3), (-7.9, 3.3)]
RIM = [(-7.9, -4.65), (4.4, -4.65), (5.75, -3.2), (5.75, 3.2), (4.4, 4.65), (-7.9, 4.65)]
sump = loft_y(TOP, -6.2, BOT, -11.3).fuse(loft_y(RIM, -6.0, RIM, -6.28))
sump = sump.fuse(cyl(1.75, (RISER_X, -10.9, 0), (RISER_X, -11.75, 0)))                 # induction riser
sump = sump.fuse(rbox(RISER_X - 1.9, RISER_X + 1.9, -11.95, -11.7, -1.9, 1.9, .1))
for n, p in SUMP_PORT.items():                                                         # runner outlets
    s = 1 if p[2] > 0 else -1
    sump = sump.fuse(cyl(1.05, (p[0], p[1], s * 3.3), p)).cut(cyl(.74, (p[0], p[1], s * 3.6), (p[0], p[1], s * 5.0)))
add('sump', 'case', sump.clean())
for s in (1, -1):
    for x in np.arange(-7.2, 4.3, 1.42):
        add('sump', 'steel', bolt((x, -6.28, s * 4.47), (0, -1, 0), .4, .22))
for x, z in ((4.95, 3.55), (4.95, -3.55), (5.55, 1.2), (5.55, -1.2)):
    add('sump', 'steel', bolt((x, -6.28, z), (0, -1, 0), .4, .22))
add('sump', 'steel', orient(hexprism(.9, .35), (0, -1, 0), (-5.2, -11.3, 0)))          # drain plug
add('sump', 'steel', orient(hexprism(1.1, .4), (0, -1, 0), (2.6, -11.3, 0)))           # suction screen plug

# ---------- intake pipes, one per cylinder (cylinder frame) ----------
for c in CYL:
    s, a = c['s'], SUMP_PORT[c['n']]
    b = local_to_world(c, PORT['intake'])
    def at(f, y, z): return world_to_local(c, (a[0] + f * (b[0] - a[0]), y, s * z))
    path = [world_to_local(c, a), at(.1, -8.15, 7.0), at(.6, -6.9, 10.4), at(1, -5.5, 12.55), at(1, -4.6, 13.05),
            np.array(PORT['intake']) + [0, -.2, 0]]
    key = 'intake_%d' % c['n']
    add(key, 'paint', tube_mesh(path, .78, 20, 8))
    add(key, 'rubber', tube_mesh([path[0], world_to_local(c, a + [0, 0, s * 1.3])], .88, 20, 3))   # hose coupling
    for dz in (.3, 1.0):
        q = world_to_local(c, a + [0, 0, s * dz])
        add(key, 'steel', tube(.93, .86, q - [0, 0, .09], q + [0, 0, .09]))                       # hose clamps
    p = PORT['intake']
    add(key, 'paint', rbox(p[0] - .62, p[0] + .62, p[1] - .2, p[1], p[2] - 1.42, p[2] + 1.42, .08))
    for dz in (-1.12, 1.12):
        add(key, 'steel', bolt((p[0], p[1] - .2, p[2] + dz), (0, -1, 0), .36, .2, False))

# ---------- fuel injector servo: throttle body under the riser ----------
X = RISER_X
servo = fuse(cyl(1.5, (X, -11.95, 0), (X, -16.5, 0)), rbox(X - 1.85, X + 1.85, -12.25, -11.95, -1.85, 1.85, .1),
             rbox(X - 1.85, X + 1.85, -16.8, -16.5, -1.85, 1.85, .1),
             cyl(1.3, (X, -14.1, 1.2), (X, -14.1, 3.3)), cyl(1.42, (X, -14.1, 3.3), (X, -14.1, 3.5)),     # fuel regulator
             cyl(.42, (X, -14.3, -1.2), (X, -14.3, -2.1)))                                               # throttle shaft boss
servo = servo.cut(cyl(1.25, (X, -16.9, 0), (X, -13.0, 0)))
add('servo', 'alu', servo.clean())
add('servo', 'steel', box(X - .12, X + 2.2, -14.55, -14.05, -2.3, -2.1))                # throttle arm
add('servo', 'steel', cyl(.14, (X + 1.9, -14.3, -2.1), (X + 1.9, -14.3, -2.6)))
add('servo', 'brass', orient(fuse(hexprism(.62, .3), cyl(.22, (0, 0, .3), (0, 0, .8))), (-1, 0, 0), (X - 1.3, -13.6, 2.2)))   # fuel inlet
add('servo', 'steel', box(X - .1, X + 1.5, -15.3, -14.9, 3.5, 3.66))                    # mixture arm
