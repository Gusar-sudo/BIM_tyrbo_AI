# -*- coding: utf-8 -*-
# Листы проверки глазами: на каждый профиль — линии узла (серые), заливка (серо-голубая), контур нового 3D-тела (красный),
# пустоты тела (синие); проблемные из _report.json — рамка оранжевая. По N профилей на лист.
# py -P -E sheet_bodies.py <curves_dir> <body_out_dir> <sheets_dir> [--per=30] [--cols=6]
import json, io, os, sys, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch
plt.rcParams["font.family"] = "Segoe UI"
CD, OD, SD = sys.argv[1:4]
opt = dict(a.lstrip("-").split("=", 1) for a in sys.argv[4:] if "=" in a)
PER = int(opt.get("per", 30)); COLS = int(opt.get("cols", 6))
os.makedirs(SD, exist_ok=True)
rep = dict((r["name"], r) for r in json.load(io.open(os.path.join(OD, "_report.json"), encoding="utf-8")))
names = sorted(rep)


def segs(C):
    out = []
    for g in C["groups"]:
        for c in g["curves"]:
            if c[0] == "L": out.append([(c[1], c[2]), (c[3], c[4])])
            elif c[0] == "A": out.append([(c[1], c[2]), (c[3], c[4]), (c[5], c[6])])
            elif c[0] == "P": out.append([tuple(p) for p in c[1]])
            elif c[0] == "C":
                out.append([(c[1] + c[3] * math.cos(t / 20.0 * 2 * math.pi), c[2] + c[3] * math.sin(t / 20.0 * 2 * math.pi)) for t in range(21)])
    return out


def short(n):
    s = n.replace(u"BIMLIB_Профиль_", u"").replace(u"_ФристайлТехнолоджи", u"")
    return s if len(s) < 46 else s[:44] + u"…"


pages = [names[i:i + PER] for i in range(0, len(names), PER)]
for pi, page in enumerate(pages):
    rows = int(math.ceil(len(page) / float(COLS)))
    fig, axs = plt.subplots(rows, COLS, figsize=(COLS * 3.4, rows * 3.6))
    axs = [a for row in (axs if rows > 1 else [axs]) for a in (row if COLS > 1 else [row])]
    for ax in axs: ax.axis("off")
    for ax, n in zip(axs, page):
        r = rep[n]; bad = r.get("error") or r.get("intersections") or r.get("short_left")
        try:
            C = json.load(io.open(os.path.join(CD, n + ".json"), encoding="utf-8"))
            for s in segs(C):
                xs, ys = zip(*s); ax.plot(xs, ys, color="#9aa3ad", lw=0.35)
            fp = os.path.join(OD, "fills", n + ".json")
            if os.path.exists(fp):
                for rg in json.load(io.open(fp, encoding="utf-8"))["regions"]:
                    v, c = [], []
                    for l in [rg["outer"]] + rg["holes"]:
                        v += [tuple(p) for p in l] + [tuple(l[0])]; c += [MP.MOVETO] + [MP.LINETO] * (len(l) - 1) + [MP.CLOSEPOLY]
                    ax.add_patch(PathPatch(MP(v, c), fc="#a9b8c7", ec="none", alpha=0.85))
            bp = os.path.join(OD, "body", n + ".json")
            if os.path.exists(bp):
                for l in json.load(io.open(bp, encoding="utf-8"))["loops"]:
                    p = l["pts"] + [l["pts"][0]]
                    ax.plot([q[0] for q in p], [q[1] for q in p], color="#c0392b" if l["kind"] == "outer" else "#2563eb", lw=0.6)
            ax.set_aspect("equal"); ax.autoscale_view()
        except Exception as ex:
            ax.text(0.5, 0.5, str(ex)[:60], ha="center", fontsize=7, transform=ax.transAxes)
        ax.set_title(short(n), fontsize=7.5, color="#c2410c" if bad else "#1f2933")
        if bad:
            ax.axis("on"); ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_color("#f59e0b"); sp.set_linewidth(2)
    fig.suptitle(u"Заливка (серо-голубая) и контур 3D-тела (красный — внешний, синий — пустоты) · лист %d из %d" % (pi + 1, len(pages)), fontsize=13, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(os.path.join(SD, u"тела_%02d.png" % (pi + 1)), dpi=110, facecolor="white")
    plt.close(fig)
print("pages", len(pages))
