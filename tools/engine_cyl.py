"""One cylinder: barrel, piston, connecting rod. Cylinder frame: +Z out along the bore, +Y up."""
from engine_lib import *
from engine_layout import *

# ======================= BARREL =======================
SKIRT_Z, FLANGE_Z1, BARREL_Z1 = 3.7, 6.05, 10.9
FIN_R, WALL_R = 3.23, 2.78
prof = [(BORE_R, SKIRT_Z), (2.72, SKIRT_Z), (2.72, DECK), (WALL_R, DECK), (WALL_R, 6.38)]
z = 6.38
while z < 9.3:                                   # fine cooling fins
    prof += [(FIN_R, z), (FIN_R, z + .06), (WALL_R + .04, z + .075), (WALL_R + .04, z + .15)]
    z += .16
prof += [(WALL_R, z), (WALL_R, BARREL_Z1), (BORE_R, BARREL_Z1)]
barrel = lathe_z(prof)
flange = cq.Workplane('XY', origin=(0, 0, DECK)).polygon(8, 2 * 3.32 / math.cos(math.pi / 8)).extrude(FLANGE_Z1 - DECK).val()
flange = flange.cut(cyl(BORE_R + .05, (0, 0, DECK - .1), (0, 0, FLANGE_Z1 + .1)))
add('barrel', 'paint', barrel)
add('barrel', 'paint', flange)
for i in range(8):                               # hold-down nuts on the case studs
    a = math.pi / 8 + i * math.pi / 4
    add('barrel', 'steel', bolt((3.0 * math.cos(a), 3.0 * math.sin(a), FLANGE_Z1), (0, 0, 1), .5, .3, False))

# ======================= PISTON (pin at the origin) =======================
SKIRT = -1.45
pp = [(0, CROWN), (2.545, CROWN), (2.545, SKIRT), (2.3, SKIRT), (2.3, CROWN - .45), (0, CROWN - .45)]
piston = lathe_z(pp)
for sx in (1, -1):                               # pin bosses
    piston = piston.fuse(cyl(.9, (sx * .62, 0, 0), (sx * 2.32, 0, 0)).fuse(box(min(sx * .62, sx * 2.32), max(sx * .62, sx * 2.32), -.9, .9, 0, CROWN - .4)))
piston = piston.cut(cyl(.562, (-2.6, 0, 0), (2.6, 0, 0)))
add('piston', 'piston', piston.clean())
for zr in (1.62, 1.36, 1.1):                     # two compression rings and an oil ring
    add('piston', 'dark', tube(2.556, 2.4, (0, 0, zr - .045), (0, 0, zr + .045)))
add('piston', 'polished', tube(.562, .34, (-2.2, 0, 0), (2.2, 0, 0)))

# ======================= CONNECTING ROD (big end at the origin, along +Z) =======================
rod = fuse(tube(1.45, PIN_R + .008, (-.5, 0, 0), (.5, 0, 0)),
           rbox(-.5, .5, -1.62, -.95, -.75, .55, .1), rbox(-.5, .5, .95, 1.62, -.75, .55, .1),
           box(-.3, .3, -.55, .55, 1.2, L - .6),
           cq.Workplane('XY', origin=(0, 0, 1.2)).rect(.6, 1.9).workplane(offset=.9).rect(.6, 1.1).loft().val(),
           tube(.82, .562, (-.5, 0, L), (.5, 0, L)))
rod = rod.cut(cyl(PIN_R + .008, (-.6, 0, 0), (.6, 0, 0)))
for sx in (1, -1):                               # I-beam pockets
    rod = rod.cut(box(min(sx * .13, sx * .31), max(sx * .13, sx * .31), -.33, .33, 2.3, L - 1.15))
add('rod', 'steel', rod.clean())
for y in (-1.28, 1.28):                          # cap bolts
    add('rod', 'polished', cyl(.16, (0, y, -.95), (0, y, .75)))
    add('rod', 'polished', orient(hexprism(.42, .28), (0, 0, -1), (0, y, -.75)))
