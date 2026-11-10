"""Starter, alternator, and belt at the front (world frame)."""
from engine_lib import *
from engine_layout import *

# ---------- starter: lower front left, pinion meshing the ring gear ----------
y, z = STARTER
add('starter', 'black', fuse(cyl(1.5, (7.6, y, z), (10.4, y, z)), cyl(1.3, (7.3, y, z), (7.6, y, z))))
add('starter', 'alu', fuse(cone(1.5, 1.0, (10.4, y, z), (11.6, y, z)), cyl(1.0, (11.6, y, z), (12.1, y, z)),
                           rbox(9.9, 10.5, y - .2, y + 2.6, z - 1.5, z + 1.9, .15)))           # nose housing and mount
add('starter', 'steel', plate([(p[0] + y, p[1] + z) for p in gear_pts(.36, .5, 9)], 12.15, .6))
add('starter', 'brass', cyl(.16, (8.2, y - 1.5, z), (8.2, y - 2.0, z)))                       # power stud
# ---------- alternator: front right, belt-driven from the pulley behind the ring gear ----------
y, z = ALT
alt = fuse(cyl(2.3, (8.6, y, z), (11.0, y, z)), cyl(1.0, (11.0, y, z), (11.45, y, z)))
for i in range(12):                                                                           # cooling slots
    q = yz(i * math.pi / 6, 2.3)
    alt = alt.cut(box(8.9, 10.7, y + q[1] - .16, y + q[1] + .16, z + q[2] - .16, z + q[2] + .16))
add('alternator', 'alu', alt.clean())
add('alternator', 'steel', lathe_x([(.3, 11.45), (1.45, 11.45), (1.45, 11.6), (1.17, 11.75), (1.45, 11.9), (1.45, 12.05), (.3, 12.05)]).translate(V(0, y, z)))
add('alternator', 'steel', fuse(box(8.9, 9.3, y + 1.6, -1.0, 3.2, 4.2), box(7.0, 9.3, -1.5, -.9, 3.0, 4.2)))    # bracket to the case
add('alternator', 'steel', box(10.6, 10.8, y - 3.6, y - 1.9, z - 2.9, z - .4))                                   # adjusting link
# ---------- belt ----------
def loop(r_big, r_small): return hull(circle_pts((0, 0), r_big, 72) + circle_pts((y, z), r_small, 36))
add('belt', 'rubber', plate(loop(4.68, 1.43), 11.62, .26).cut(plate(loop(4.4, 1.15), 11.5, .5)))
