# -*- coding: utf-8 -*-
# Столб целиком: 3D-тело, графика узла и на каждой стороне со стеклом (в т.ч. под углом) — полоса стекла 8 мм
# с торцом по правилу 3 мм и точка отсчёта. py -P -E compose_pocket_angles.py <pocket.json> <items.json> <out.png>
# items.json: [{"type", "title", "sides": [{"ang": градусы направления от оси наружу, "ref": мм, "label": подпись}]}]
import json, io, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
plt.rcParams["font.family"] = "Segoe UI"
D = json.load(io.open(sys.argv[1], encoding="utf-8-sig"))
I = json.load(io.open(sys.argv[2], encoding="utf-8-sig"))
INK, GL, BODY, REAL, OK = "#283040", "#9fd3ef", "#d23c3c", "#9aa3ad", "#16a34a"
cols = 3; rows = int(math.ceil(len(I) / float(cols)))
fig, axs = plt.subplots(rows, cols, figsize=(cols * 6, rows * 6.2), squeeze=False)
for ax in axs.ravel(): ax.axis("off")
for ax, it in zip(axs.ravel(), I):
    r = D[it["type"]]; face = 35.7 if it["type"].startswith(u"М3") else 30.6
    for s in r["nested"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=REAL, lw=0.6)
    for s in r["own"]: ax.plot([s[0], s[2]], [s[1], s[3]], color=BODY, lw=1.3)
    for sd in it["sides"]:
        a = math.radians(sd["ang"]); u = (math.cos(a), math.sin(a)); n = (-u[1], u[0]); e = sd["ref"] + 3.0
        for lo in (-face, face - 8):
            pts = [(u[0] * d + n[0] * l, u[1] * d + n[1] * l) for d, l in ((e, lo), (e + 45, lo), (e + 45, lo + 8), (e, lo + 8))]
            ax.add_patch(Polygon(pts, closed=True, color=GL, alpha=0.6, lw=0))
            p0 = (u[0] * e + n[0] * (lo - 1), u[1] * e + n[1] * (lo - 1)); p1 = (u[0] * e + n[0] * (lo + 9), u[1] * e + n[1] * (lo + 9))
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=OK, lw=2)
        tx = (u[0] * (e + 52), u[1] * (e + 52))
        ax.text(tx[0], tx[1], (u"%s\n%s → %s" % (sd.get("label", u""), (u"%.2f" % sd["ref"]).replace(".", ","), (u"%.2f" % e).replace(".", ","))).strip(),
                fontsize=8.5, color=OK, ha="center", va="center", bbox=dict(fc="white", ec="none", alpha=0.8))
    ax.axis("on"); ax.set_xlim(-115, 115); ax.set_ylim(-115, 115); ax.set_aspect("equal"); ax.grid(lw=0.25, color="#eef0f3")
    ax.tick_params(labelsize=7); ax.set_title(it["title"], fontsize=12, color=INK, loc="left", fontweight="bold")
fig.suptitle(u"Хвосты по столбам: точка отсчёта → торец стекла (мм от оси столба), стекло 8 мм, зелёное — торец по правилу 3 мм", fontsize=14, color=INK, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(sys.argv[3], dpi=100, facecolor="white")
print("ok")
