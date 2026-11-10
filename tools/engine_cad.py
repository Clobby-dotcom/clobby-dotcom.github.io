"""Builds the IO-360 study model as CAD solids and exports it for study/engine.html.

Units are inches. +X is the propeller end, +Y is up, +Z is the right side.
Every part is modeled in the frame the page animates it in:
  - world parts sit where they are on the engine
  - crankshaft parts are in the crank frame (axis along X, pin 1 toward +Z)
  - camshaft parts are in the cam frame (origin on the cam axis)
  - idler gears are centered on their own axis
  - cylinder parts are in a cylinder frame: origin on the crank axis at the cylinder's
    station, +Z out along the bore, +Y up. The page turns the left bank 180 degrees.

Run:  python engine_cad.py <out-dir>     (needs cadquery, trimesh, numpy)
Writes io360.glb (one node per part and material, named "<part>__<material>")
and io360-layout.json (the numbers the page uses to animate it).

Sources and what is approximate: see engine_layout.py.
"""
import sys, importlib
from engine_lib import export
from engine_layout import *

only = sys.argv[2].split(',') if len(sys.argv) > 2 else ['crank', 'case', 'cyl', 'head', 'top', 'train', 'sump', 'acc', 'front', 'ext']
for name in only:
    importlib.import_module('engine_' + name)

layout = dict(
    R=R, L=L, CAMY=CAMY, LIFT=LIFT, HALF=HALF, VX=VX, STEM=STEM.tolist(), VLEN=VLEN, ARM=ARM, RATIO=VARM / ARM,
    pivot=PIV.tolist(), pushDir={v: PDIR[v].tolist() for v in PDIR}, crown=CROWN, roof=ROOF, springSeat=SEAT_Z, springLen=SPRING_LEN, cyl=CYL,
    idlers=[dict(key='idler_l', y=float(IDLER_L[0]), z=float(IDLER_L[1]), ratio=N_CRANK / N_IDLER),
            dict(key='idler_r', y=float(IDLER_R[0]), z=float(IDLER_R[1]), ratio=N_CRANK / N_IDLER)])
export(sys.argv[1] if len(sys.argv) > 1 else '.', layout)
