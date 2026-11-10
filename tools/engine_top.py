"""Rocker box cover, valves, and valve springs (cylinder frame)."""
from engine_lib import *
from engine_layout import *
from engine_head import octagon, prism, B

# ---------- rocker box cover: a pressed octagonal pan held by six screws ----------
def wire(pts, z): return cq.Wire.makePolygon([V(x, y, z) for x, y in pts], close=True)
def pan(extra, z0, dz):
    secs = [(octagon(.3 + extra), z0), (octagon(.5 + extra), 16.2 - dz), (octagon(1.25 + extra), COVER_Z1 - dz)]
    return Solid.makeLoft([wire(p, z) for p, z in secs], True)
F0, F1 = BOX_Z1 + .03, BOX_Z1 + .15
cover = prism(octagon(), F0, F1).fuse(pan(0, F1 - .02, 0)).cut(pan(.09, F0 - .1, .09)).clean()
add('cover', 'paint', cover)
add('cover', 'dark', prism(octagon(), BOX_Z1, F0).cut(prism(octagon(.3), BOX_Z1 - .1, F0 + .1)))   # gasket
for x, y in ((2.6, .85), (2.13, 3.0), (2.13, -1.35)):
    for sx in (1, -1):
        add('cover', 'steel', cyl(.13, (sx * x, y, F1), (sx * x, y, F1 + .1)))

# ---------- valves (built in place, closed) ----------
FACE = ROOF - .02
def valve(v, rh, mat):
    x = VX[v]
    stem = lathe_z([(0, 0), (rh, 0), (rh, .07), (rh - .12, .2), (.36, .5), (.22, .95), (.22, VLEN), (0, VLEN)], FACE)
    key = 'valve_in' if v == 'intake' else 'valve_ex'
    add(key, mat, stem.translate(V(x, 0, 0)))
    top = SEAT_Z + SPRING_LEN
    add(key, 'steel', lathe_z([(.22, 0), (.6, 0), (.72, .1), (.72, .2), (.22, .2)], top).translate(V(x, 0, 0)))
valve('intake', .98, 'chrome')
valve('exhaust', .82, 'exvalve')

# ---------- valve spring (base at the origin, along +Z; the page squeezes it) ----------
turns, n = 5.5, 66
pts = [(.56 * math.cos(2 * math.pi * turns * i / n), .56 * math.sin(2 * math.pi * turns * i / n), SPRING_LEN * i / n) for i in range(n + 1)]
add('spring', 'steel', tube_mesh(pts, .075, 8, 2))
