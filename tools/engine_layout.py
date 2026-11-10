"""Layout numbers for the IO-360 study model.

From Lycoming documents: bore 5.125, stroke 4.375, rod length 6.75, journal and pin
diameters (Table of Limits SSP-1776), firing order 1-3-2-4, overall size.
Everything else is scaled from Lycoming's installation drawings and parts catalog
figures, so treat it as approximate.
"""
import math
import numpy as np

R, L = 2.1875, 6.75              # crank throw, rod center to center
BORE_R = 2.5625
MAIN_R, PIN_R = 1.1875, 1.0625   # main and rod journals
DECK = 5.65                      # crank axis to the cylinder pad
CROWN = 1.95                     # piston pin to crown
ROOF = 11.55                     # crank axis to the valve faces
CYL = [dict(n=1, s=1, x=4.68, fire=0, phi=0), dict(n=2, s=-1, x=2.48, fire=360, phi=180),
       dict(n=3, s=1, x=-2.48, fire=180, phi=180), dict(n=4, s=-1, x=-4.68, fire=540, phi=0)]

# Valve train (cylinder frame). Valves are parallel to the bore, side by side.
VX = {'intake': -1.3, 'exhaust': 1.3}
TX = {'intake': -1.1, 'exhaust': 1.1}    # tappets: opposite intake tappets share a lobe
STEM = np.array([0.0, 0.0, 1.0])
VLEN = 3.4
TIPZ = ROOF + VLEN
PIV = np.array([1.35, 15.0])             # rocker shaft (y, z)
ARM, VARM = 1.25, 1.35                   # rocker arms: pushrod side, valve side
CUP = np.array([2.6, 14.8])              # pushrod cup on the rocker (y, z)
CAMY = 4.83                              # camshaft above the crankshaft
CAM_BASE, LIFT, HALF = 0.62, 0.36, 115   # base circle, lobe lift, half duration (crank deg)
SOCK_Z = 2.9                             # tappet socket where the pushrod sits
PUSH = {v: (np.array([TX[v], CAMY, SOCK_Z]), np.array([VX[v], CUP[0], CUP[1]])) for v in VX}
PDIR = {v: (b - a) / np.linalg.norm(b - a) for v, (a, b) in PUSH.items()}
def on_push(v, z):
    a, d = PUSH[v][0], PDIR[v]
    return a + d * ((z - a[2]) / d[2])

# Cylinder head (cylinder frame)
HEAD_Z0, FIN_Z1, BOX_Z1, COVER_Z1 = 9.4, 12.3, 15.3, 16.68   # head start, end of the fins, cover gasket face, cover top
SEAT_Z, SPRING_LEN = 13.3, 1.3                                # valve spring seat and installed length
BOX = dict(x=2.75, y0=-1.95, y1=3.6, ch=1.0, neck=2.3, flare=14.3)   # rocker box outline
PORT = {'intake': np.array([-1.55, -3.9, 13.05]), 'exhaust': np.array([1.55, -3.75, 13.05])}   # port faces, pointing down
TUBE_R = 0.4                                                  # pushrod shroud tube

# Lobes: (station, [(cylinder, valve), ...])
LOBES = [(5.78, [(1, 'exhaust')]), (3.58, [(1, 'intake'), (2, 'intake')]), (1.38, [(2, 'exhaust')]),
         (-1.38, [(3, 'exhaust')]), (-3.58, [(3, 'intake'), (4, 'intake')]), (-5.78, [(4, 'exhaust')])]
def lobe_angle(n, v):
    """Cam-frame angle (from +Y toward +Z) of the lobe peak at crank angle 0."""
    c = CYL[n - 1]; peak = c['fire'] + (450 if v == 'intake' else 270)
    return (90 if c['s'] > 0 else 270) - peak / 2

# Gear train at the rear (simplified): crank gear, two idlers, cam gear
MOD, GX0, GT = 0.1, -7.75, 0.5
N_CRANK, N_IDLER, N_CAM = 15, 30, 30
_d1, _d2 = MOD * (N_CRANK + N_IDLER) / 2, MOD * (N_IDLER + N_CAM) / 2
_y = (_d1 ** 2 - _d2 ** 2 + CAMY ** 2) / (2 * CAMY)
IDLER_L = np.array([_y, -math.sqrt(_d1 ** 2 - _y ** 2)])     # (y, z), meshes crank and cam gears
IDLER_R = np.array([_d1 * math.cos(math.radians(85)), _d1 * math.sin(math.radians(85))])

# Plugs and nozzle (cylinder frame): point on the head, direction pointing out
TOP_PLUG = (np.array([0, 3.1, 12.85]), np.array([0, .77, .64]))
BOT_PLUG = (np.array([0, -3.0, 12.75]), np.array([0, -.77, .64]))
NOZZLE = (np.array([-2.05, 2.3, 12.7]), np.array([-.35, .94, 0]))
for _k in ('TOP_PLUG', 'BOT_PLUG', 'NOZZLE'):
    _p, _d = globals()[_k]; globals()[_k] = (_p, _d / np.linalg.norm(_d))

# Accessories (world)
CASE_X0, CASE_X1, ACC_X0 = -7.9, 7.3, -9.4
MAG = {'left': (0.5, -5.7), 'right': (0.5, 5.7)}     # (y, z)
FILTER_Y = 1.47
STARTER, ALT = (-5.6, -2.9), (-4.2, 5.6)             # (y, z)
DIVIDER = np.array([-2.6, 6.75, 0.0])           # fuel manifold, on top of the case behind the lifting strap

def world_to_local(c, p): return np.array([(p[0] - c['x']) * c['s'], p[1], p[2] * c['s']])
def local_to_world(c, p): return np.array([c['x'] + c['s'] * p[0], p[1], c['s'] * p[2]])

# Sump and induction (world): riser under the sump, one port per cylinder on the sump sides
RISER_X = -0.8
SUMP_PORT = {1: np.array([1.9, -8.3, 4.9]), 3: np.array([-2.9, -8.3, 4.9]),
             2: np.array([1.9, -8.3, -4.9]), 4: np.array([-2.9, -8.3, -4.9])}
MUFFLER = np.array([-5.4, -14.3, 0.0])               # crosswise can under the rear of the sump
