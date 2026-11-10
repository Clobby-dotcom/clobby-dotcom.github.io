"""Valve train and small cylinder fittings (cylinder frame): rockers, tappets, pushrods, shroud tubes, plugs."""
from engine_lib import *
from engine_layout import *

py, pz = PIV
# ---------- rocker arm (origin on the rocker shaft; the page turns it about X) ----------
TIP = TIPZ - pz                                               # valve tip, relative to the shaft
SOCK = CUP[1] - pz                                            # pushrod cup, relative to the shaft
outline = hull(circle_pts((0, 0), .5) + circle_pts((-VARM, TIP + .25), .26) + circle_pts((ARM, SOCK + .28), .28))
rocker = fuse(plate(outline, -.25, .5), cyl(.5, (-.5, 0, 0), (.5, 0, 0)),
              cyl(.22, (0, -VARM, TIP), (0, -VARM, TIP + .25)))
rocker = rocker.cut(cyl(.314, (-.6, 0, 0), (.6, 0, 0))).clean()
add('rocker', 'steel', rocker)
add('rockershaft', 'polished', cyl(.312, (-2.75, py, pz), (2.75, py, pz)))

# ---------- tappets, pushrods, shroud tubes ----------
for v, s in (('intake', 'in'), ('exhaust', 'ex')):
    x = TX[v]
    tappet = fuse(cyl(.4, (x, CAMY, CAM_BASE), (x, CAMY, CAM_BASE + .14)),
                  cyl(.358, (x, CAMY, CAM_BASE + .1), (x, CAMY, SOCK_Z - .1)))
    add('lifter_' + s, 'polished', tappet.cut(sphere(.2, (x, CAMY, SOCK_Z))))
    a, b = PUSH[v]
    add('pushrod_' + s, 'polished', fuse(cyl(.15, a, b), sphere(.2, a), sphere(.18, b)))
    add('shroud', 'alu', tube(TUBE_R, .33, on_push(v, 4.9), on_push(v, 14.5)))
    for z in (5.32, 14.22):                                   # seals at the case and the head
        add('shroud', 'dark', tube(TUBE_R + .09, TUBE_R, on_push(v, z - .08), on_push(v, z + .08)))

# ---------- spark plugs and the fuel nozzle ----------
def plug(key, seat):
    p, d = seat
    body = fuse(hexprism(.78, .5), cyl(.34, (0, 0, .5), (0, 0, 1.45)), cyl(.42, (0, 0, 1.45), (0, 0, 1.75)))
    add(key, 'steel', orient(body, d, p))
    add(key, 'polished', orient(hexprism(.62, .45).translate(V(0, 0, 1.75)), d, p))    # harness nut
plug('plug_top', TOP_PLUG); plug('plug_bot', BOT_PLUG)
p, d = NOZZLE
add('nozzle', 'brass', orient(fuse(hexprism(.5, .32), cyl(.2, (0, 0, .32), (0, 0, .75))), d, p))

# ---------- rocker box oil drain back to the crankcase ----------
path = [(-.66, -1.95, 14.9), (-.66, -3.2, 14.8), (-.64, -4.3, 13.9), (-.62, -4.62, 12.3), (-.6, -4.66, 9.6),
        (-.5, -4.35, 6.9), (-.4, -4.0, 5.15)]
add('drain', 'alu', tube_mesh(path, .11, 10, 8))
add('drain', 'rubber', tube_mesh(path[4:6], .16, 10, 4))      # hose joint
add('drain', 'steel', orient(hexprism(.36, .3), (0, -1, 0), (-.66, -1.9, 14.9)))
