"""Crankcase halves. Each half is built on the +Z side and the left one is mirrored."""
from engine_lib import *
from engine_layout import *

OUTER = [(0, 6.1), (2.2, 6.1), (4.3, 5.35), (4.75, 3.9), (5.5, 3.7), (5.5, -3.7), (4.6, -4.4), (4.4, -6.0), (0, -6.0)]
INNER = [(-.1, 5.8), (2.1, 5.8), (4.05, 5.1), (4.45, 3.6), (5.15, 3.4), (5.15, -3.4), (4.3, -4.1), (4.1, -6.2), (-.1, -6.2)]
WEB = [(0, 5.8), (2.1, 5.8), (4.05, 5.1), (4.45, 3.6), (5.15, 3.4), (5.15, -3.4), (4.3, -4.1), (4.1, -5.2), (0, -5.2)]
BULKHEADS = [(6.1, 7.05), (-.55, .55), (-7.0, -6.05)]

def half(side):
    s = 1 if side == 'right' else -1
    cyls = [c for c in CYL if c['s'] == s]
    def pt(c, p): return np.array([c['x'] + s * p[0], p[1], p[2]])     # cylinder frame to this half, before mirroring
    body = poly_x(OUTER, CASE_X0, CASE_X1)
    # nose: front main bearing and oil seal housing, with the cam front bearing above it
    nose = fuse(cone(3.4, 2.05, (CASE_X1, 0, 0), (10.3, 0, 0)), cyl(2.05, (10.3, 0, 0), (11.0, 0, 0)),
                rbox(CASE_X1 - .4, 9.4, 2.2, 6.1, -2.3, 2.3, .5))
    body = body.fuse(nose.intersect(box(CASE_X1 - .5, 11.5, -7, 7, 0, 6)))
    if side == 'left':                                                     # propeller governor pad
        body = body.fuse(rbox(7.75, 11.1, .9, 4.35, 0, 3.05, .25)).fuse(cyl(.5, (9.25, 4.2, 1.6), (9.25, 6.4, 1.6)))
    body = body.fuse(cyl(2.0, (CASE_X0, CAMY, 0), (CASE_X0 + 1.2, CAMY, 0)).intersect(box(-9, -6, 0, 9, 0, 3)))   # arch over the cam gear
    for c in cyls:                                                         # cylinder pads
        body = body.fuse(cyl(3.4, (c['x'], 0, 4.3), (c['x'], 0, DECK)).intersect(box(CASE_X0, 9, -3.75, 3.75, 4, 6)))
    # hollow it out, then put the bearing webs back
    cavity = fuse(poly_x(INNER, CASE_X0 - .2, 7.05), cyl(1.5, (7.0, 0, 0), (10.6, 0, 0)),
                  cyl(1.72, (CASE_X0 - .2, CAMY, 0), (-7.05, CAMY, 0)))
    body = body.cut(cavity)
    for x0, x1 in BULKHEADS:
        body = body.fuse(poly_x(WEB, x0, x1))
    body = body.fuse(box(-7.0, 7.05, CAMY - 1.0, 5.85, 0, 2.75))          # cam and tappet gallery
    body = body.cut(cyl(MAIN_R + .03, (-8, 0, 0), (11.2, 0, 0))).cut(cyl(.8, (-8, CAMY, 0), (7.06, CAMY, 0)))
    for x, _ in LOBES:                                                     # room for each lobe to turn
        body = body.cut(cyl(1.08, (x - .4, CAMY, 0), (x + .4, CAMY, 0)))
    for c in cyls:
        body = body.cut(cyl(2.8, (c['x'], 0, 2.3), (c['x'], 0, DECK + .1)))
        for v in VX:
            a, b = pt(c, on_push(v, 4.15)), pt(c, on_push(v, 5.25))
            body = body.fuse(cyl(.62, a, b))                               # shroud tube socket
            body = body.cut(cyl(.37, pt(c, (TX[v], CAMY, .3)), pt(c, (TX[v], CAMY, 3.0))))      # tappet bore
            body = body.cut(cyl(.45, pt(c, on_push(v, 2.7)), pt(c, on_push(v, 5.4))))
    # mount ears at the rear
    for y in (4.97, -4.58):
        ear = fuse(cyl(.8, (CASE_X0, y, 6.0), (CASE_X0 + 1.1, y, 6.0)),
                   box(CASE_X0, CASE_X0 + 1.1, min(y, y * .72), max(y, y * .72), 4.4, 6.0))
        body = body.fuse(ear.cut(cyl(.34, (CASE_X0 - .1, y, 6.0), (CASE_X0 + 1.2, y, 6.0))))
    # top spine where the halves bolt together
    body = body.fuse(box(-7.6, 8.9, 5.9, 6.7, 0, .3))
    body = body.clean()
    key = 'case_r' if side == 'right' else 'case_l'
    hardware = []
    for x in np.arange(-7.0, 8.6, 1.3):
        hardware.append(bolt((x, 6.38, .3), (0, 0, 1), .44, .24))
    for c in cyls:                                                         # studs around each pad
        for i in range(8):
            a = math.pi / 8 + i * math.pi / 4
            hardware.append(cyl(.16, (c['x'] + 3.0 * math.cos(a), 3.0 * math.sin(a), DECK - .1), (c['x'] + 3.0 * math.cos(a), 3.0 * math.sin(a), DECK + .75)))
    if side == 'left':
        for x in (8.4, 10.5):
            for y in (1.55, 3.7):
                hardware.append(cyl(.13, (x, y, 3.0), (x, y, 3.6)))
        hardware.append(box(-1.6, 1.6, 6.7, 8.0, .0, .12).cut(cyl(.45, (0, 7.45, -.1), (0, 7.45, .3))))   # lifting strap
    if s < 0:
        body = body.mirror('XY'); hardware = [h.mirror('XY') for h in hardware]
    add(key, 'case', body)
    for h in hardware: add(key, 'steel', h)

half('right'); half('left')
