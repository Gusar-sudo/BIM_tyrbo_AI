"""Картинка окна DXF тонкими линиями (по слоям цветом). py dxf_window_png.py <dxf> x0,y0,x1,y1 <out.png> [--grid=10]"""
import sys, ezdxf, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.stdout.reconfigure(encoding="utf-8")
src, win, out = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], sys.argv[3]
grid = 10
for a in sys.argv[4:]:
    if a.startswith("--grid="): grid = float(a.split("=")[1])
x0, y0, x1, y1 = win
doc = ezdxf.readfile(src)
def flat(es, d=0):
    for e in es:
        if e.dxftype() == "INSERT" and d < 6:
            try: yield from flat(e.virtual_entities(), d + 1)
            except Exception: pass
        else: yield e
cols = {}
pal = ["k", "tab:red", "tab:blue", "tab:green", "tab:orange", "tab:purple", "tab:brown", "tab:cyan", "tab:olive", "tab:pink"]
fig, ax = plt.subplots(figsize=(12, 12 * (y1 - y0) / (x1 - x0)))
n = 0
for e in flat(doc.modelspace()):
    t = e.dxftype()
    try:
        if t in ("LINE", "ARC", "CIRCLE", "LWPOLYLINE", "SPLINE", "ELLIPSE", "POLYLINE"):
            from ezdxf import path as _p
            pts = np.array([(q.x, q.y) for q in _p.make_path(e).flattening(0.02)])
            if len(pts) == 0: continue
            if pts[:, 0].max() < x0 or pts[:, 0].min() > x1 or pts[:, 1].max() < y0 or pts[:, 1].min() > y1: continue
            L = e.dxf.layer; c = cols.setdefault(L, pal[len(cols) % len(pal)])
            ax.plot(pts[:, 0], pts[:, 1], lw=0.4, color=c); n += 1
        elif t in ("MTEXT", "TEXT"):
            p = e.dxf.insert
            if x0 <= p.x <= x1 and y0 <= p.y <= y1:
                ax.text(p.x, p.y, (e.plain_text() if t == "MTEXT" else e.dxf.text)[:40], fontsize=5)
    except Exception:
        pass
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
ax.set_xticks(np.arange(np.ceil(x0 / grid) * grid, x1, grid)); ax.set_yticks(np.arange(np.ceil(y0 / grid) * grid, y1, grid))
ax.tick_params(labelsize=4); ax.grid(lw=0.15)
for L, c in cols.items(): ax.plot([], [], color=c, label=L)
ax.legend(fontsize=5, loc="upper right")
fig.savefig(out, dpi=220, bbox_inches="tight"); print("entities", n, "layers", cols)
