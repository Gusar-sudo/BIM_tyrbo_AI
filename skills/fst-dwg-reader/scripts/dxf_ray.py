"""Пересечения горизонтали y (или вертикали --vertical x) с линиями DXF в диапазоне.
py dxf_ray.py <dxf> <y> <x0> <x1> [--vertical]  → список (координата, слой, тип)"""
import sys, ezdxf, numpy as np
from ezdxf import path as P
sys.stdout.reconfigure(encoding="utf-8")
src, c, a0, a1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
vert = "--vertical" in sys.argv
doc = ezdxf.readfile(src)
def flat(es, d=0):
    for e in es:
        if e.dxftype() == "INSERT" and d < 6:
            try: yield from flat(e.virtual_entities(), d + 1)
            except Exception: pass
        else: yield e
hits = []
for e in flat(doc.modelspace()):
    if e.dxftype() not in ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "SPLINE", "ELLIPSE", "POLYLINE"): continue
    try: pts = [(q.x, q.y) for q in P.make_path(e).flattening(0.01)]
    except Exception: continue
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if vert: x0, y0, x1, y1 = y0, x0, y1, x1
        if (y0 - c) * (y1 - c) <= 0 and y0 != y1:
            x = x0 + (c - y0) / (y1 - y0) * (x1 - x0)
            if a0 <= x <= a1: hits.append((round(x, 2), e.dxf.layer, e.dxftype()))
for h in sorted(set(hits)): print(h)
