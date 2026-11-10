"""Accessories: rear housing with magnetos, oil filter, and pumps; starter and alternator at the front (world frame)."""
from engine_lib import *
from engine_layout import *

A0, A1 = ACC_X0, CASE_X0                      # rear face and front face of the accessory housing

# ---------- accessory housing ----------
half = [(0, 6.7), (1.5, 6.55), (2.6, 5.7), (4.4, 4.9), (5.6, 3.6), (5.9, 1.6), (5.9, -1.2), (5.3, -3.6), (4.7, -5.2),
        (4.5, -7.6), (3.6, -8.5)]
outline = half + [(-z, y) for z, y in reversed(half) if z > 0]
housing = poly_x(outline, A0, A1)
pads = [(MAG['left'], 1.95), (MAG['right'], 1.95), ((FILTER_Y, 0), 2.1)]
for (y, z), r in pads:
    housing = housing.fuse(cyl(r, (A0 - .25, y, z), (A0 + .1, y, z)))
housing = housing.fuse(rbox(A0 - .3, A0 + .1, 3.37, 5.77, 1.0, 3.4, .1))            # vacuum pump pad
housing = housing.fuse(rbox(A0 - .3, A0 + .1, -5.1, -2.7, .8, 3.2, .1))             # spare drive pad
add('accessory', 'case', housing.clean())
for z, y in outline:
    if abs(z) > .5 or y < 0: add('accessory', 'steel', bolt((A0, y * .93, z * .93), (-1, 0, 0), .4, .22))
add('accessory', 'alu', rbox(A0 - .42, A0 - .3, -5.0, -2.8, .9, 3.1, .05))          # cover plate on the spare pad
for dy in (-.85, .85):
    for dz in (-.85, .85):
        add('accessory', 'steel', bolt((A0 - .42, -3.9 + dy, 2.0 + dz), (-1, 0, 0), .34, .2, False))

# ---------- magnetos ----------
def magneto(key, y, z):
    add(key, 'alu', rbox(A0 - .65, A0 - .25, y - 1.75, y + 1.75, z - 1.75, z + 1.75, .3))      # mounting flange
    add(key, 'black', cyl(1.55, (A0 - .65, y, z), (A0 - 3.5, y, z)))
    add(key, 'dark', fuse(cyl(1.6, (A0 - 3.5, y, z), (A0 - 3.75, y, z)), cone(1.5, 1.25, (A0 - 3.75, y, z), (A0 - 5.2, y, z))))
    for a in (45, 135, 225, 315):                                                             # the four lead outlets
        q = yz(math.radians(a), .7) + [A0 - 5.2, y, z]
        add(key, 'polished', cyl(.2, q, q + [-.3, 0, 0]))
    for dy in (-1.4, 1.4):
        add(key, 'steel', bolt((A0 - .65, y + dy, z - dy), (-1, 0, 0), .4, .24))
magneto('mag_l', *MAG['left']); magneto('mag_r', *MAG['right'])

# ---------- oil filter, vacuum pump, fuel pump ----------
y = FILTER_Y
add('filter', 'alu', fuse(cyl(2.0, (A0 - .25, y, 0), (A0 - 1.2, y, 0)), rbox(A0 - 1.1, A0 - .3, y - 2.6, y, -1.1, 1.1, .2)))
add('filter', 'filter', fuse(cyl(1.85, (A0 - 1.2, y, 0), (A0 - 5.5, y, 0)), cone(1.85, 1.5, (A0 - 5.5, y, 0), (A0 - 5.8, y, 0))))
add('filter', 'steel', orient(hexprism(1.0, .4), (-1, 0, 0), (A0 - 5.8, y, 0)))
add('vacpump', 'alu', rbox(A0 - .7, A0 - .3, 3.42, 5.72, 1.05, 3.35, .15))
add('vacpump', 'black', fuse(cyl(1.15, (A0 - .7, 4.57, 2.2), (A0 - 3.1, 4.57, 2.2)), cyl(.9, (A0 - 3.1, 4.57, 2.2), (A0 - 3.4, 4.57, 2.2))))
for dz in (-.6, .6):
    add('vacpump', 'brass', cyl(.28, (A0 - 2.2, 4.57, 2.2 + dz), (A0 - 2.2, 6.1, 2.2 + dz)))
fy, fz, fx = -5.45, -1.35, A0 - 1.25
pump = fuse(cyl(.95, (fx, -6.3, fz), (fx, -5.3, fz)), cone(.95, .4, (fx, -5.3, fz), (fx, -4.6, fz)), cyl(1.08, (fx, -5.42, fz), (fx, -5.18, fz)),
            rbox(A0 - .6, A0 - .25, -6.3, -4.9, fz - .9, fz + .9, .1), box(fx, A0 - .6, -6.2, -5.4, fz - .5, fz + .5))
add('fuelpump', 'alu', pump)
for dz, dx in ((-1, 0), (1, 0)):
    add('fuelpump', 'brass', orient(fuse(hexprism(.5, .3), cyl(.2, (0, 0, .3), (0, 0, .7))), (0, 0, dz), (fx, -5.85, fz + dz * .9)))

# ---------- oil filler tube and dipstick, right rear ----------
a, b = np.array([-6.9, -1.8, 5.4]), np.array([-6.9, 6.9, 11.7])
add('dipstick', 'paint', cyl(.55, a, b))
add('dipstick', 'paint', cyl(.75, a + [0, -.3, -.6], a + (b - a) * .07))
add('dipstick', 'brass', orient(fuse(cyl(.72, (0, 0, 0), (0, 0, .5)), box(-.9, .9, -.12, .12, .5, .8)), b - a, b))
