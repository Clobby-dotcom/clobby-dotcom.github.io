"""Cylinder head with its cooling fins, ports, and rocker box (cylinder frame)."""
from engine_lib import *
from engine_layout import *

B = BOX
def octagon(inset=0.0, ymax=None):
    """Rocker box outline as (x, y) points. ymax clips the top off for the neck."""
    x, y0, y1, ch = B['x'] - inset, B['y0'] + inset, B['y1'] - inset, B['ch'] - inset * .6
    if ymax is not None:
        return [(x - ch, y0), (x, y0 + ch), (x, ymax), (-x, ymax), (-x, y0 + ch), (-(x - ch), y0)]
    return [(x - ch, y0), (x, y0 + ch), (x, y1 - ch), (x - ch, y1), (-(x - ch), y1), (-x, y1 - ch), (-x, y0 + ch), (-(x - ch), y0)]
def prism(pts, z0, z1):
    return cq.Workplane('XY', origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0).val()

def slot(v):                                                 # channel a pushrod tube lies in
    r = TUBE_R + .12
    s = cyl(r, (0, 0, 0), (0, 0, 3.8)).fuse(box(-r, r, 0, 2.5, 0, 3.8))
    return orient(s, PDIR[v], on_push(v, HEAD_Z0 - .4))
SLOTS = [slot(v) for v in VX]

# ---------- body: barrel socket, port section (neck), rocker box ----------
body = fuse(cyl(3.0, (0, 0, HEAD_Z0), (0, 0, FIN_Z1)), prism(octagon(ymax=B['neck']), ROOF, B['flare'] + .05),
            prism(octagon(), B['flare'], BOX_Z1))
for v, p in PORT.items():                                    # intake and exhaust ports face down
    body = body.fuse(cyl(.88, (p[0], -1.2, p[2]), p))
    body = body.fuse(rbox(p[0] - .62, p[0] + .62, p[1], p[1] + .3, p[2] - 1.42, p[2] + 1.42, .12))
for p, d in (TOP_PLUG, BOT_PLUG):                            # spark plug bosses
    body = body.fuse(cyl(.55, p - d * 1.6, p))
# rocker box cavity, with the bosses that carry the rocker shaft
cav = fuse(prism(octagon(.22, B['neck'] - .22), SEAT_Z, BOX_Z1 + .1), prism(octagon(.22), B['flare'] + .25, BOX_Z1 + .1))
body = body.cut(cav)
py, pz = PIV
for x0, x1 in ((-2.6, -2.05), (-.5, .5), (2.05, 2.6)):
    body = body.fuse(cyl(.52, (x0, py, pz), (x1, py, pz))).fuse(box(x0, x1, py - .52, py + .52, SEAT_Z - .1, pz))
cuts = [cyl(.312, (-2.9, py, pz), (2.9, py, pz)),            # rocker shaft bore
        cyl(2.79, (0, 0, HEAD_Z0 - .1), (0, 0, 10.9)), cyl(BORE_R, (0, 0, 10.8), (0, 0, ROOF))]
for v, p in PORT.items():
    cuts.append(cyl(.68, (p[0], p[1] - .1, p[2]), (p[0], -2.3, p[2])))
    cuts.append(cyl(TUBE_R + .02, on_push(v, 13.5), on_push(v, 14.75)))          # pushrod tube sockets
for p, d in (TOP_PLUG, BOT_PLUG):
    cuts.append(cyl(.3, p - d * 2.7, p + d * .1))
body = body.cut(*cuts, *SLOTS).clean()
add('head', 'alu', body)
for v, p in PORT.items():                                    # two studs at each port
    for dz in (-1.12, 1.12):
        add('head', 'steel', cyl(.1, (p[0], p[1] + .1, p[2] + dz), (p[0], p[1] - .62, p[2] + dz)))

# ---------- cooling fins, with channels for the two pushrod tubes ----------
hole = cyl(2.9, (0, 0, HEAD_Z0 - .1), (0, 0, FIN_Z1 + .2))
def fin(z, hx, y0, y1, r, t=.07):
    f = cq.Workplane('XY', origin=(0, (y0 + y1) / 2, z)).rect(2 * hx, y1 - y0).extrude(t).edges('|Z').fillet(r).val()
    return f.cut(hole, *SLOTS)
for z in np.arange(HEAD_Z0 + .1, 11.5, .19):
    add('head', 'alu', fin(z, 3.15, -4.3, 4.15, 1.5))
for z in np.arange(11.62, FIN_Z1, .19):
    add('head', 'alu', fin(z, 3.0, -3.45, 3.9, 1.4))
