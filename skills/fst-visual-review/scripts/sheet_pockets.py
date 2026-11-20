# -*- coding: utf-8 -*-
# Лист: контуры столбов (probe_pocket.py) — графика узла (серая) и 3D-тело (красное), оси, сетка 10 мм.
# py -P -E sheet_pockets.py <pocket.json> <out.png> [--cols=4] [--lim=80]
import json, io, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Segoe UI"
D = json.load(io.open(sys.argv[1], encoding="utf-8"))
opt = dict(a.lstrip("-").split("=", 1) for a in sys.argv[3:] if "=" in a)
COLS = int(opt.get("cols", 4)); LIM = float(opt.get("lim", 80))
names = [n for n in D if isinstance(D[n], dict)]
rows = int(math.ceil(len(names) / float(COLS)))
fig, axs = plt.subplots(rows, COLS, figsize=(COLS * 5.2, rows * 5.4))
axs = [a for r in (axs if rows > 1 else [axs]) for a in r]
for ax in axs: ax.axis("off")
for ax, n in zip(axs, names):
    r = D[n]; ax.axis("on")
    for s in r.get("nested", []): ax.plot([s[0], s[2]], [s[1], s[3]], color="#9aa3ad", lw=0.6)
    for s in r.get("own", []): ax.plot([s[0], s[2]], [s[1], s[3]], color="#c0392b", lw=1.0)
    ax.axhline(0, color="#1f2933", lw=0.4); ax.axvline(0, color="#1f2933", lw=0.4)
    ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM); ax.set_aspect("equal"); ax.grid(lw=0.25, color="#e5e7eb")
    ax.set_title(n.replace(u" с двухслойным остеклением", u" 2сл"), fontsize=10, loc="left")
fig.suptitle(u"Столбы: графика узла (серое) и 3D-тело (красное), мм от оси импоста", fontsize=14, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(sys.argv[2], dpi=110, facecolor="white")
print("ok", len(names))
