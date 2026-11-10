"""Fuel manifold and injector lines, ignition harness, and a simple exhaust (the exhaust is an airframe part)."""
from engine_lib import *
from engine_layout import *

def W(c, p): return local_to_world(c, p)
# ---------- fuel manifold (flow divider) and the four injector lines ----------
D = DIVIDER
add('divider', 'steel', box(D[0] - .9, D[0] + .9, D[1] - .1, D[1] + .12, -.75, .75))                 # bracket
body = fuse(cyl(.95, D + [0, .12, 0], D + [0, .62, 0]), cyl(1.05, D + [0, .62, 0], D + [0, .78, 0]), cyl(.8, D + [0, .78, 0], D + [0, .95, 0]))
add('divider', 'alu', body)
add('divider', 'brass', orient(fuse(hexprism(.44, .25), cyl(.16, (0, 0, .25), (0, 0, .6))), (-1, 0, 0), D + [-.95, .4, 0]))   # fuel in, from the servo
for c in CYL:
    s = c['s']; p, d = NOZZLE
    tip = W(c, p + d * .78); out = D + [.35 * (1 if c['x'] > D[0] else -1), .45, s * .95]
    add('divider', 'brass', orient(hexprism(.3, .2), (0, 0, s), out - [0, 0, s * .2]))
    path = [out, out + [0, .15, s * .8], [(out[0] + tip[0]) / 2, 6.9, s * 4.2], [tip[0], 5.9, s * 8.0], [tip[0], 4.75, s * 11.2],
            tip + [0, .75, -s * .25], tip]
    add('injlines', 'polished', tube_mesh(path, .065, 8, 10))

# ---------- ignition harness: each magneto fires the top plugs across the engine and the bottom plugs on its own side ----------
for side, sm in (('left', -1), ('right', 1)):
    my, mz = MAG[side]; x0 = ACC_X0 - 5.5
    for i, c in enumerate(CYL):
        s = c['s']; top = s != sm
        p, d = TOP_PLUG if top else BOT_PLUG
        end, pre = W(c, p + d * 2.2), W(c, p + d * 3.1)
        a = yz(math.radians(45 + 90 * i), .7) + [x0, my, mz]
        if top:
            path = [a, a + [-.5, .5, 0], [-13.4, 4.9, sm * 4.6], [-10.6, 7.25, sm * 1.2], [-8.3, 7.1, s * 2.6], [-7.0, 6.5, s * 6.4],
                    [min(c['x'] - 1.0, -5.2), 6.3, s * 9.2], [c['x'] - .25, 6.35, s * 12.6], pre, end]
        else:
            path = [a, a + [-.5, -.5, 0], [-13.6, -2.2, s * 6.9], [-10.5, -4.6, s * 7.6], [-7.6, -5.3, s * 8.4],
                    [c['x'] - 1.2, -5.3, s * 9.0], [c['x'], -5.5, s * 11.4], [c['x'], -6.0, s * 13.7], pre, end]
        add('harness', 'harness', tube_mesh(path, .13, 8, 10))

# ---------- exhaust: a riser from each cylinder into a crosswise muffler ----------
M = MUFFLER
for c in CYL:
    s = c['s']; P = W(c, PORT['exhaust'])
    if c['n'] > 2:      # rear cylinders drop into the muffler ends
        path = [P, [P[0], -6.0, P[2]], [P[0] + .15 * (M[0] - P[0]), -9.5, s * 11.8], [P[0] + .7 * (M[0] - P[0]), -12.8, s * 8.6], [M[0], M[1] + .3, s * 6.0]]
    else:               # front cylinders sweep back along the sump to the muffler's front face
        path = [P, [P[0], -6.0, P[2]], [P[0] - .3, -10.0, s * 12.6], [P[0] + .45 * (-1.3 - P[0]), -13.3, s * 10.7], [-1.3, -14.6, s * 7.5],
                [M[0] + 1.7, M[1] - .6, s * 4.8]]
    key = 'exhaust_%d' % c['n']
    add(key, 'exhaust', tube_mesh([world_to_local(c, q) for q in path], .75, 18, 9))
    p = PORT['exhaust']
    add(key, 'exhaust', rbox(p[0] - .62, p[0] + .62, p[1] - .22, p[1], p[2] - 1.42, p[2] + 1.42, .08))
    for dz in (-1.12, 1.12):
        add(key, 'steel', bolt((p[0], p[1] - .22, p[2] + dz), (0, -1, 0), .36, .2, False))
can = fuse(cyl(2.1, M + [0, 0, -6.0], M + [0, 0, 6.0]), cone(2.1, 1.2, M + [0, 0, 6.0], M + [0, 0, 6.9]), cone(1.2, 2.1, M + [0, 0, -6.9], M + [0, 0, -6.0]))
add('muffler', 'exhaust', can)
add('muffler', 'exhaust', tube(.9, .8, M + [-.6, -1.6, 3.2], M + [-2.2, -5.2, 3.2]))                  # tailpipe
